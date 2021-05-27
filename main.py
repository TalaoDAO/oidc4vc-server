"""

if script is launched without Gunicorn, setup environment variables first :
$ export MYCHAIN=talaonet
$ export MYENV=livebox
 NO -> $ export AUTHLIB_INSECURE_TRANSPORT=1
$ python main.py

"""
import os
import time
import json
from flask import Flask, redirect, jsonify, request
from flask_session import Session
from jwcrypto import jwk
from datetime import timedelta

import logging
logging.basicConfig(level=logging.INFO)
import constante
from components import ns, privatekey, directory
from signaturesuite import helpers
from protocol import Document

# Environment variables set in gunicornconf.py  and transfered to environment.py
import environment
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')
if not mychain or not myenv :
    logging.error('environment variables missing')
    logging.error('export MYCHAIN=talaonet, export MYENV=livebox, export AUTHLIB_INSECURE_TRANSPORT=1')
    mychain='talaonet'
    myenv='airbox'
if mychain not in ['mainet', 'ethereum', 'rinkeby', 'talaonet'] :
    logging.error('wrong chain')
    exit()
logging.info('start to init environment')
mode = environment.currentMode(mychain,myenv)
logging.info('end of init')

# Centralized  routes : modules in ./routes
from routes import web_register, web_create_company_cci, web_certificate, web_issuer
from routes import web_data_user, web_skills, web_external, web_issuer_explore
from routes import web_main, web_login, repository, cci_api

# Release
VERSION = "0.9.12"

# Framework Flask and Session setup
app = Flask(__name__)
app.jinja_env.globals['Version'] = VERSION
app.jinja_env.globals['Created'] = time.ctime(os.path.getctime('main.py'))
app.jinja_env.globals['Chain'] = mychain.capitalize()
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_COOKIE_NAME'] = 'talao'
app.config['SESSION_TYPE'] = 'redis' # Redis server side session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=180) # cookie lifetime
app.config['SESSION_FILE_THRESHOLD'] = 100
app.config['SECRET_KEY'] = "OCML3BRawWEUeaxcuKHLpw" + mode.password
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["jpeg", "jpg", "png", "gif"]
sess = Session()
sess.init_app(app)

@app.errorhandler(403)
def page_abort(e):
    """
    we set the 403 status explicitly
    """
    logging.warning('abort 403')
    return redirect(mode.server + 'login/')


# Centralized @route for create identity
app.add_url_rule('/register/identity/',  view_func=web_register.register_identity, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/register/',  view_func=web_register.register, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/register/password/',  view_func=web_register.register_password, methods = [ 'GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/register/code/', view_func=web_register.register_code, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/register/post_code/', view_func=web_register.register_post_code, methods = ['POST', 'GET'], defaults={'mode': mode})

# Centralized @route for create company CCI
app.add_url_rule('/create_company_cci/',  view_func=web_create_company_cci.cci, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/create_company_cci/password/',  view_func=web_create_company_cci.cci_password, methods = [ 'GET','POST'], defaults={'mode': mode})
app.add_url_rule('/create_company_cci/code/', view_func=web_create_company_cci.cci_code, methods = ['GET','POST'], defaults={'mode': mode})
app.add_url_rule('/create_company_cci/post_code/', view_func=web_create_company_cci.cci_post_code, methods = ['GET','POST'], defaults={'mode': mode})

# Centralized @route to display certificates
app.add_url_rule('/certificate/',  view_func=web_certificate.show_certificate, defaults={'mode': mode})
app.add_url_rule('/guest/certificate/',  view_func=web_certificate.show_certificate, defaults={'mode': mode})  # idem previous
app.add_url_rule('/certificate/verify/',  view_func=web_certificate.certificate_verify, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/certificate/issuer_explore/',  view_func=web_certificate.certificate_issuer_explore, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/guest/',  view_func=web_certificate.certificate_issuer_explore, methods = ['GET'], defaults={'mode': mode}) # idem previous

# Centralized route for the Blockchain CV
app.add_url_rule('/resume/', view_func=web_external.resume, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/board/', view_func=web_external.board, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/company/registry/', view_func=web_external.board, methods = ['GET', 'POST'], defaults={'mode': mode}) # same as previous

# Centralized route fo Issuer explore
app.add_url_rule('/user/issuer_explore/', view_func=web_issuer_explore.issuer_explore, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route for login
app.add_url_rule('/logout/',  view_func=web_login.logout, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/forgot_username/',  view_func=web_login.forgot_username, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/forgot_password/',  view_func=web_login.forgot_password, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/forgot_password_token/',  view_func=web_login.forgot_password_token, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/login/authentification/',  view_func=web_login.login_authentification, methods = ['POST'], defaults={'mode': mode})
app.add_url_rule('/login/',  view_func=web_login.login, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/',  view_func=web_login.login, methods = ['GET', 'POST'], defaults={'mode': mode}) # idem previous
app.add_url_rule('/user/two_factor/',  view_func=web_login.two_factor, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/user/update_wallet/',  view_func=web_login.update_wallet, methods = ['GET', 'POST'], defaults={'mode': mode})
#app.add_url_rule('/login_password/',  view_func=web_login.login_password, methods = ['GET', 'POST'])
#app.add_url_rule('/did_auth/',  view_func=web_login.did_auth, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route for user and data main view
app.add_url_rule('/user/',  view_func=web_data_user.user, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/data/',  view_func=web_data_user.data, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/user/advanced/',  view_func=web_data_user.user_advanced, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/user/account/',  view_func=web_data_user.user_account, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/company/',  view_func=web_data_user.the_company, methods = ['GET', 'POST'])
app.add_url_rule('/privacy/',  view_func=web_data_user.privacy, methods = ['GET', 'POST'])
app.add_url_rule('/user/import_identity_key/',  view_func=web_data_user.import_identity_key, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/user/import_identity_key2/',  view_func=web_data_user.import_identity_key, methods = ['GET', 'POST'], defaults={'mode': mode})


# Centralized route issuer for skills
app.add_url_rule('/user/update_skills/',  view_func=web_skills.update_skills, methods = ['GET', 'POST'], defaults={'mode': mode})


# Centralized route for main features

app.add_url_rule('/verifier/',  view_func=web_main.verifier, methods = ['GET', 'POST'])
app.add_url_rule('/getDID/',  view_func=web_main.getDID, methods = ['GET'])
app.add_url_rule('/user/generate_identity/',  view_func=web_main.generate_identity, methods = ['GET', 'POST'],  defaults={'mode' : mode})
app.add_url_rule('/homepage/',  view_func=web_main.homepage, methods = ['GET'])
app.add_url_rule('/user/picture/',  view_func=web_main.picture, methods = ['GET', 'POST'], defaults={'mode' : mode})
app.add_url_rule('/user/success/',  view_func=web_main.success, methods = ['GET'], defaults={'mode' : mode})
app.add_url_rule('/user/update_search_setting/',  view_func=web_main.update_search_setting, methods = ['GET', 'POST'], defaults={'mode' : mode})
app.add_url_rule('/user/update_phone/',  view_func=web_main.update_phone, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/update_password/',  view_func=web_main.update_password, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/signature/',  view_func=web_main.signature, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/report',  view_func=web_main.report, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/tutotial/',  view_func=web_main.tutorial, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/prefetch',  view_func=web_main.prefetch, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/search/',  view_func=web_main.search, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/select_identity/',  view_func=web_main.select_identity, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/issue_certificate/',  view_func=web_main.issue_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/company/issue_reference_credential/',  view_func=web_main.issue_reference_credential, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/update_personal_settings/',  view_func=web_main.update_personal_settings, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/update_company_settings/',  view_func=web_main.update_company_settings, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/store_file/',  view_func=web_main.store_file, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_experience/',  view_func=web_main.add_experience, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_activity/',  view_func=web_main.add_activity, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/presentation/',  view_func=web_main.presentation, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/swap_privacy/',  view_func=web_main.swap_privacy, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_certificate/',  view_func=web_main.remove_certificate, methods = ['GET','POST'], defaults={'mode' : mode})

app.add_url_rule('/user/issue_kyc/',  view_func=web_main.create_kyc, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_experience/',  view_func=web_main.remove_experience, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_education/',  view_func=web_main.remove_education, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/create_company/',  view_func=web_main.create_company, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/create_user/',  view_func=web_main.create_user, methods = ['GET','POST'], defaults={'mode' : mode})

app.add_url_rule('/user/remove_file/',  view_func=web_main.remove_file, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_education/',  view_func=web_main.add_education, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/invit/',  view_func=web_main.invit, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/send_memo/',  view_func=web_main.send_memo, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_partnership/',  view_func=web_main.request_partnership, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_partner/',  view_func=web_main.remove_partner, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/reject_partner/',  view_func=web_main.reject_partner, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/authorize_partner/',  view_func=web_main.authorize_partner, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_alias/',  view_func=web_main.add_alias, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_access/',  view_func=web_main.remove_access, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/import_private_key/',  view_func=web_main.import_private_key, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/import_rsa_key/',  view_func=web_main.import_rsa_key, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_proof_of_identity/',  view_func=web_main.request_proof_of_identity, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_issuer/',  view_func=web_main.add_issuer, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_key/',  view_func=web_main.add_key_for_other, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/delete_identity/',  view_func=web_main.delete_identity, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/uploads/<filename>',  view_func=web_main.send_file, defaults={'mode' : mode})
app.add_url_rule('/fonts/<filename>',  view_func=web_main.send_fonts)
app.add_url_rule('/help/',  view_func=web_main.send_help, methods = ['GET','POST'])
app.add_url_rule('/user/download/',  view_func=web_main.download_file, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/download_rsa_key/',  view_func=web_main.download_rsa_key, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/talao_ca/',  view_func=web_main.ca, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/download_x509/',  view_func=web_main.download_x509, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/download_pkcs12/',  view_func=web_main.download_pkcs12, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/download_QRCode/',  view_func=web_main.download_QRCode, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/typehead/',  view_func=web_main.typehead, methods = ['GET','POST'])
app.add_url_rule('/user/data/',  view_func=web_main.talao_search, methods = ['GET','POST'], defaults={'mode' : mode})


# Centralized route for credential issuer
app.add_url_rule('/company/add_employee/',  view_func=web_issuer.add_employee, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_certificate/',  view_func=web_issuer.request_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_experience_credential/',  view_func=web_issuer.request_experience_credential, methods = ['POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_reference_credential/',  view_func=web_issuer.request_reference_credential, methods = ['POST'], defaults={'mode' : mode})
app.add_url_rule('/company/dashboard/',  view_func=web_issuer.company_dashboard, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/company/issue_credential_workflow/',  view_func=web_issuer.issue_credential_workflow, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/company/add_campaign/',  view_func=web_issuer.add_campaign, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/company/remove_campaign/',  view_func=web_issuer.remove_campaign, methods = ['GET','POST'], defaults={'mode' : mode})


# Centralized route for repository
app.add_url_rule('/repository/authn',  view_func=repository.authn, methods = ['POST'], defaults={'mode' : mode})
app.add_url_rule('/repository/publish',  view_func=repository.publish, methods = ['POST'], defaults={'mode' : mode})
app.add_url_rule('/repository/create',  view_func=repository.create, methods = ['GET'], defaults={'mode' : mode})
app.add_url_rule('/repository/get',  view_func=repository.get, methods = ['POST'], defaults={'mode' : mode})



# centralized route for CCI API
app.add_url_rule('/api/v1/credential',  view_func=cci_api.credential_list, methods = ['GET'], defaults={'mode' : mode})
app.add_url_rule('/api/v1/resolver',  view_func=cci_api.resolver, methods = ['GET'], defaults={'mode' : mode})


# DID API
@app.route('/.well-known/did-configuration.json', methods=['GET']) 
def well_known_did_configuration () :
    document = {
        "@context": "https://identity.foundation/.well-known/did-configuration/v1",
        "linked_dids": [{
  "@context": [
        "https://www.w3.org/2018/credentials/v1",
        {
            "origin": "https://identity.foundation/.well-known/resources/did-configuration/#origin",
            "DomainLinkageCredential": "https://identity.foundation/.well-known/resources/did-configuration/#DomainLinkageCredential",
            "LinkedDomains": "https://identity.foundation/.well-known/resources/did-configuration/#LinkedDomains",
            "linked_dids": "https://identity.foundation/.well-known/resources/did-configuration/#linked_dids"
        }
    ],
  "type": [
    "VerifiableCredential",
    "DomainLinkageCredential"
  ],
  "credentialSubject": {
    "id": "did:web:talao.co",
    "origin": "https://talao.co"
  },
  "issuer": "did:web:talao.co",
  "issuanceDate": "2021-05-02T00:00:00Z",
  "proof": {
    "type": "EcdsaSecp256k1Signature2019",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "did:web:talao.co#key-1",
    "created": "2021-05-12T07:51:17.888Z",
    "jws": "eyJhbGciOiJFUzI1NksiLCJjcml0IjpbImI2NCJdLCJiNjQiOmZhbHNlfQ..Nq3lF-bFOCpZ-kSB8RufLDOwsqaHH77LNzUdTcOCnbJqRGGCqZ3MsnGlBFscl_8QNJ2PRFiAVi5hOHWe0dLjLg"
  },
  "expirationDate": "2026-05-01T00:00:00Z"
    }]}

    return jsonify(document)

@app.route('/.well-known/did.json', methods=['GET'], defaults={'mode' : mode})
def well_known_did (mode) :
    """ did:web
    https://w3c-ccg.github.io/did-method-web/
    https://identity.foundation/.well-known/resources/did-configuration/#LinkedDomains
    """
    address = mode.owner_talao 

    # RSA
    pvk = privatekey.get_key(address, 'rsa_key', mode)
    key = jwk.JWK.from_pem(pvk.encode())
    rsa_public = key.export_public(as_dict=True)
    del rsa_public['kid']
    # secp256k
    pvk = privatekey.get_key(address, 'private_key', mode)
    key = helpers.ethereum_to_jwk256k(pvk)
    ec_public = json.loads(key)
    del ec_public['d']
    del ec_public['alg']
    DidDocument = did_doc(ec_public, rsa_public)
    return jsonify(DidDocument)

def did_doc(ec_public, rsa_public) :
    """
        Build the DID document
    """
    return  {
                "@context":
                    [
                        "https://www.w3.org/ns/did/v1"
                    ],
                "id": "did:web:talao.co",
                "verificationMethod":
                    [
                        {
                        "id": "did:web:talao.co#key-1",
                        "controller" : "did:web:talao.co",
                        "type": "EcdsaSecp256k1VerificationKey2019",
                        "publicKeyJwk": ec_public
                        },
                        {
                        "id": "did:web:talao.co#key-2",
                        "controller" : "did:web:talao.co",
                        "type": "RsaVerificationKey2018",
                        "publicKeyJwk": rsa_public
                        }
                    ],
                "authentication" :
                    [
                    "did:web:talao.co#key-1",
                    "did:web:talao.co#key-2"
                    ],
                "assertionMethod" :
                    [
                    "did:web:talao.co#key-1",
                    "did:web:talao.co#key-2"
                    ],
                "service":
                    [
                        {
                        "id": 'did:web:talao.co#domain-1',
                        "type" : 'LinkedDomains',
                        "serviceEndpoint": "https://talao.co"
                        }
                    ]
            }




# MAIN entry point for test
if __name__ == '__main__':

    # info release
    logging.info('flask serveur init')
    app.run(host = mode.flaskserver, port= mode.port, debug = mode.test)