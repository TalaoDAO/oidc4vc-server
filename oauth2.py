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
from protocol import read_profil
import ns
import environment

import os

# Environment setup
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')
mode = environment.currentMode(mychain,myenv)


# API Server has its own identity
api_server_address = '0xEE09654eEdaA79429F8D216fa51a129db0f72250' # = owner_talao

# JWT configuration with JWK, JWT is signed with Talao RSA key, the public rsa key is sent with the JWT
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
print('JWK = ', JWK)
JWT_CONFIG = {
    'key':  JWK,
    'alg': 'RS256',
    'iss': 'https://talao.co',
    'exp': 3600,
}

def exists_nonce(nonce, req):
    exists = OAuth2AuthorizationCode.query.filter_by(
        client_id=req.client_id, nonce=nonce
    ).first()
    return bool(exists)

# for JWT generation only
def generate_user_info(user, scope):
    user_workspace_contract = ns.get_data_from_username(user.username, mode).get('workspace_contract')
    user_info = UserInfo(sub='did:talao:' + mode.BLOCKCHAIN +':' + user_workspace_contract[2:])
    profile, category  = read_profil(user_workspace_contract, mode, 'full')
    if category == 2001 : #  company
        return user_info
    if 'profile' in scope :
        user_info['given_name'] = profile.get('firstname')
        user_info['family_name'] = profile.get('lastname')
        user_info['gender'] = profile.get('gender')
    if 'email' in scope :
        user_info['email']= profile.get('contact_email') if profile.get('contact_email') != 'private' else None
    if 'phone' in scope :
        user_info['phone']= profile.get('contact_phone') if profile.get('contact_phone') != 'private' else None
    if 'birthdate' in scope :
        user_info['birthdate'] = profile.get('birthdate') if profile.get('birthdate') != 'private' else None
    if 'address' in scope :
        user_info['address'] = profile.get('postal_address') if profile.get('postal_address') != 'private' else None
    if 'about' in scope :
        user_info['about'] = profile.get('about') if profile.get('about') != 'private' else None
    if 'website' in scope :
        user_info['website'] = profile.get('website') if profile.get('website') != 'private' else None
    if 'proof_of_identity' in scope :
        user_info['proof_of_identity'] = 'Not implemented yet'
    if 'resume' in scope :
        user_info['resume'] = 'Not implemented yet'
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

