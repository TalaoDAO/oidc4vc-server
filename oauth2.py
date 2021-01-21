from authlib.integrations.flask_oauth2 import (
    AuthorizationServer, ResourceProtector)
from authlib.integrations.sqla_oauth2 import (
    create_query_client_func,
    create_save_token_func,
    create_bearer_token_validator,
    create_revocation_endpoint,
)

from authlib.oauth2.rfc6749 import grants # ajout
from authlib.oauth2.rfc6749.grants import (
    AuthorizationCodeGrant as _AuthorizationCodeGrant,
)
from authlib.oidc.core.grants import (
    OpenIDCode as _OpenIDCode,
    OpenIDImplicitGrant as _OpenIDImplicitGrant,
    OpenIDHybridGrant as _OpenIDHybridGrant,
)
from authlib.oidc.core import UserInfo
from werkzeug.security import gen_salt
from models import db, User
from models import OAuth2Client, OAuth2AuthorizationCode, OAuth2Token
from authlib.jose import jwk
from Crypto.PublicKey import RSA
import time
import datetime

from protocol import Document, get_category
import ns
import environment
import privatekey
import os
import constante

# Environment setup
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')
mode = environment.currentMode(mychain,myenv)


# API Server has its own identity
api_server_address = '0xEE09654eEdaA79429F8D216fa51a129db0f72250' # = owner_talao

# JWT configuration with JWK, JWT is signed with Talao RSA key, 
filename = './RSA_key/talaonet/' + api_server_address + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
try :
	fp = open(filename,"r")
	private_rsa_key = fp.read()
	fp.close()
except :
    print('RSA private key of API Server not found')


# Generate JWK from rsa key
JWK = jwk.dumps(private_rsa_key)


# set up 'kid' in the JWK header 
JWK['kid'] = 'Talao public RSA key'
JWT_CONFIG = {
    'key':  JWK,
    'alg': 'RS256',
    'iss': 'did:talao:' + mode.BLOCKCHAIN + ':' + api_server_address[2:],
    'exp': 3600,
}

def exists_nonce(nonce, req):
    exists = OAuth2AuthorizationCode.query.filter_by(
        client_id=req.client_id, nonce=nonce
    ).first()
    return bool(exists)

# for JWT generation only, we use the kyc data 
def generate_user_info(user, scope):
    user_workspace_contract = ns.get_data_from_username(user.username, mode).get('workspace_contract')
    user_info = UserInfo(sub='did:talao:' + mode.BLOCKCHAIN +':' + user_workspace_contract[2:])
    category  = get_category(user_workspace_contract, mode,)
    if category == 2001 : #  company
        return user_info
    # get KYC
    contract = mode.w3.eth.contract(user_workspace_contract,abi = constante.workspace_ABI)
    kyc_list = list()
    for doc_id in contract.functions.getDocuments().call() :
        if contract.functions.getDocument(doc_id).call()[0] == 15000 :
            kyc_list.append(doc_id)
    if kyc_list :
        kyc = Document('kyc')
        kyc.relay_get(user_workspace_contract, kyc_list[-1], mode, loading='light')
        kyc_dict = kyc.__dict__
        if 'profile' in scope :
            user_info['given_name'] = kyc_dict.get('given_name', '')
            user_info['family_name'] = kyc_dict.get('family_name', '')
            user_info['gender'] = kyc_dict.get('gender', '')
        if 'email' in scope :
            user_info['email']= kyc_dict.get('email', '')
            user_info['email_verified'] = True if user_info['email'] else False
        if 'phone' in scope or 'phone_number' in scope :
            user_info['phone_number']= kyc_dict.get('phone', '')
            user_info['phone_number_verified'] = True if user_info['phone_number'] else False
        if 'birthdate' in scope :
            user_info['birthdate'] = kyc_dict.get('birthdate', '')
        if 'address' in scope :
            user_info['address'] = kyc_dict.get('address', '')
        updated_at = time.mktime(datetime.datetime.strptime(kyc_dict.get('created', 0), "%Y-%m-%d %H:%M:%S").timetuple())
        user_info['updated_at'] = updated_at
    return user_info



def create_authorization_code(client, grant_user, request):
    code = gen_salt(48)
    nonce = request.data.get('nonce')
    item = OAuth2AuthorizationCode(
        code=code,
        client_id=client.client_id,
        redirect_uri=request.redirect_uri,
        scope=request.scope,
        user_id=grant_user.id,
        nonce=nonce,
    )
    db.session.add(item)
    db.session.commit()
    return code

class AuthorizationCodeGrant(_AuthorizationCodeGrant):
    def create_authorization_code(self, client, grant_user, request):
        return create_authorization_code(client, grant_user, request)

    def parse_authorization_code(self, code, client):
        item = OAuth2AuthorizationCode.query.filter_by(
            code=code, client_id=client.client_id).first()
        if item and not item.is_expired():
            return item

    def delete_authorization_code(self, authorization_code):
        db.session.delete(authorization_code)
        db.session.commit()

    def authenticate_user(self, authorization_code):
        return User.query.get(authorization_code.user_id)


class OpenIDCode(_OpenIDCode):
    def exists_nonce(self, nonce, request):
        return exists_nonce(nonce, request)
    
    def get_audiences(self, request):
        """Parse `aud` value for id_token, default value is client id. Developers
        MAY rewrite this method to provide a customized audience value.
        """
        return ['did:talao:' + mode.BLOCKCHAIN + ':' + api_server_address[2:]]
    
    def get_jwt_config(self, grant):
        return JWT_CONFIG

    def generate_user_info(self, user, scope):
        return generate_user_info(user, scope)

"""
class ImplicitGrant(_OpenIDImplicitGrant):
    def exists_nonce(self, nonce, request):
        return exists_nonce(nonce, request)

    def get_jwt_config(self, grant):
        return JWT_CONFIG

    def generate_user_info(self, user, scope):
        return generate_user_info(user, scope)
"""


#ajout
class RefreshTokenGrant(grants.RefreshTokenGrant):
    def authenticate_refresh_token(self, refresh_token):
        token = OAuth2Token.query.filter_by(refresh_token=refresh_token).first()
        if token and token.is_refresh_token_active():
            return token

    def authenticate_user(self, credential):
        return User.query.get(credential.user_id)

    def revoke_old_credential(self, credential):
        credential.revoked = True
        db.session.add(credential)
        db.session.commit()

"""
class HybridGrant(_OpenIDHybridGrant):
    def create_authorization_code(self, client, grant_user, request):
        return create_authorization_code(client, grant_user, request)

    def exists_nonce(self, nonce, request):
        return exists_nonce(nonce, request)

    def get_jwt_config(self):
       return JWT_CONFIG

    def generate_user_info(self, user, scope):
        return generate_user_info(user, scope)

"""

authorization = AuthorizationServer()
require_oauth = ResourceProtector()


def config_oauth(app):
    query_client = create_query_client_func(db.session, OAuth2Client)
    save_token = create_save_token_func(db.session, OAuth2Token)
    authorization.init_app(
        app,
        query_client=query_client,
        save_token=save_token
    )

    # support all openid grants
    authorization.register_grant(AuthorizationCodeGrant, [
        OpenIDCode(require_nonce=True),
    ])
    #authorization.register_grant(ImplicitGrant)
    #authorization.register_grant(HybridGrant)
    authorization.register_grant(grants.ClientCredentialsGrant)
    authorization.register_grant(RefreshTokenGrant)
    #authorization.register_grant(PasswordGrant)

    # protect resource
    bearer_cls = create_bearer_token_validator(db.session, OAuth2Token)
    require_oauth.register_token_validator(bearer_cls())

    # support revocation
    revocation_cls = create_revocation_endpoint(db.session, OAuth2Token)
    authorization.register_endpoint(revocation_cls)

