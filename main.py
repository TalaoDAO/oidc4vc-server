"""
Main script to start web server through Gunicorn
Arguments of main.py are in gunicornconf.py (global variables) :
$ gunicorn -c gunicornconf.py  --reload wsgi:app

if script is launched without Gunicorn, setup environment variables first :
$ export MYCHAIN=talaonet
$ export MYENV=livebox
 NO -> $ export AUTHLIB_INSECURE_TRANSPORT=1
$ python main.py

"""
import sys
import os
import time
import json
from flask import Flask, redirect, jsonify, request
from flask_session import Session
from jwcrypto import jwk
#from flask_fontawesome import FontAwesome
from datetime import timedelta

import logging
logging.basicConfig(level=logging.INFO)

from components import ns, privatekey
from signaturesuite import helpers
from protocol import ownersToContracts

# Environment variables set in gunicornconf.py  and transfered to environment.py
import environment
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')
if not mychain or not myenv :
    logging.error('environment variables missing')
    logging.error('export MYCHAIN=talaonet, export MYENV=livebox, export AUTHLIB_INSECURE_TRANSPORT=1')
    exit()
if mychain not in ['mainet', 'ethereum', 'rinkeby', 'talaonet'] :
    logging.error('wrong chain')
    exit()
logging.info('start to init environment')
mode = environment.currentMode(mychain,myenv)
logging.info('end of init')

# Centralized  routes : modules in ./routes
from routes import web_create_identity, web_create_company_cci, web_certificate, web_workflow
from routes import web_data_user, web_issue_certificate, web_skills, web_CV_blockchain, web_issuer_explore
from routes import web_main, web_login

# Release
VERSION = "0.8.7"

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

# bootstrap font managment  -> recheck if needed !!!!!
#fa = FontAwesome(app)

@app.errorhandler(403)
def page_abort(e):
    """
    we set the 403 status explicitly
    """
    logging.warning('abort 403')
    return redirect(mode.server + 'login/')

# Centralized @route for create identity
app.add_url_rule('/register/',  view_func=web_create_identity.register, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/register/password/',  view_func=web_create_identity.register_password, methods = [ 'GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/register/code/', view_func=web_create_identity.register_code, methods = ['GET', 'POST'], defaults={'mode': mode})

app.add_url_rule('/register/post_code/', view_func=web_create_identity.register_post_code, methods = ['POST', 'GET'], defaults={'mode': mode})
app.add_url_rule('/wc_register/',  view_func=web_create_identity.wc_register, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/wc_register_activate/',  view_func=web_create_identity.wc_register_activate, methods = ['GET', 'POST'], defaults={'mode': mode})

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
#app.add_url_rule('/certificate/data/',  view_func=web_certificate.certificate_data, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/certificate/certificate_data_analysis/',  view_func=web_certificate.certificate_data_analysis, methods = ['GET'], defaults={'mode': mode})

# Centralized route for the Blockchain CV
app.add_url_rule('/resume/', view_func=web_CV_blockchain.resume, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/board/', view_func=web_CV_blockchain.board, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route fo Issuer explore
app.add_url_rule('/user/issuer_explore/', view_func=web_issuer_explore.issuer_explore, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route for login
#app.add_url_rule('/wc_login/',  view_func=web_login.wc_login, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/logout/',  view_func=web_login.logout, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/forgot_username/',  view_func=web_login.forgot_username, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/forgot_password/',  view_func=web_login.forgot_password, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/forgot_password_token/',  view_func=web_login.forgot_password_token, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/login/authentification/',  view_func=web_login.login_authentification, methods = ['POST'], defaults={'mode': mode})
app.add_url_rule('/login/',  view_func=web_login.login, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/',  view_func=web_login.login, methods = ['GET', 'POST'], defaults={'mode': mode}) # idem previous
app.add_url_rule('/user/two_factor/',  view_func=web_login.two_factor, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/user/update_wallet/',  view_func=web_login.update_wallet, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/login_password/',  view_func=web_login.login_password, methods = ['GET', 'POST'])

# Centralized route for user and data main view
app.add_url_rule('/user/',  view_func=web_data_user.user, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/data/',  view_func=web_data_user.data, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/user/advanced/',  view_func=web_data_user.user_advanced, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/user/account/',  view_func=web_data_user.user_account, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/company/',  view_func=web_data_user.the_company, methods = ['GET', 'POST'])
app.add_url_rule('/privacy/',  view_func=web_data_user.privacy, methods = ['GET', 'POST'])

# Centralized route issuer for issue certificate for guest
app.add_url_rule('/issue/',  view_func=web_issue_certificate.issue_certificate_for_guest, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/issue/create_authorize_issue/',  view_func=web_issue_certificate.create_authorize_issue, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/issue/logout/',  view_func=web_issue_certificate.issue_logout, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route issuer for skills
app.add_url_rule('/user/update_skills/',  view_func=web_skills.update_skills, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route for main features
app.add_url_rule('/homepage/',  view_func=web_main.homepage, methods = ['GET'])
app.add_url_rule('/user/picture/',  view_func=web_main.picture, methods = ['GET', 'POST'], defaults={'mode' : mode})
app.add_url_rule('/user/success/',  view_func=web_main.success, methods = ['GET'], defaults={'mode' : mode})
app.add_url_rule('/user/update_search_setting/',  view_func=web_main.update_search_setting, methods = ['GET', 'POST'], defaults={'mode' : mode})
app.add_url_rule('/user/update_phone/',  view_func=web_main.update_phone, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/update_password/',  view_func=web_main.update_password, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/signature/',  view_func=web_main.signature, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/report',  view_func=web_main.report, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/data_analysis/',  view_func=web_main.data_analysis, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/tutotial/',  view_func=web_main.tutorial, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/prefetch',  view_func=web_main.prefetch, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/search/',  view_func=web_main.search, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/select_identity/',  view_func=web_main.select_identity, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/issue_certificate/',  view_func=web_main.issue_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/issuer_experience_certificate/',  view_func=web_main.issue_experience_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/issue_recommendation/',  view_func=web_main.issue_recommendation, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/company/issue_reference_credential/',  view_func=web_main.issue_reference_credential, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/update_personal_settings/',  view_func=web_main.update_personal_settings, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/update_company_settings/',  view_func=web_main.update_company_settings, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/store_file/',  view_func=web_main.store_file, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/create_person/',  view_func=web_main.create_person, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_experience/',  view_func=web_main.add_experience, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/issue_kyc/',  view_func=web_main.create_kyc, methods = ['GET','POST'], defaults={'mode' : mode})
#app.add_url_rule('/user/issue_skill_certificate/',  view_func=web_main.issue_skill_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_kyc/',  view_func=web_main.remove_kyc, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/issue_kbis/',  view_func=web_main.issue_kbis, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_kbis/',  view_func=web_main.remove_kbis, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_experience/',  view_func=web_main.remove_experience, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/create_company/',  view_func=web_main.create_company, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_certificate/',  view_func=web_main.remove_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_file/',  view_func=web_main.remove_file, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_education/',  view_func=web_main.add_education, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/invit/',  view_func=web_main.invit, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/send_memo/',  view_func=web_main.send_memo, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_partnership/',  view_func=web_main.request_partnership, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_partner/',  view_func=web_main.remove_partner, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/reject_partner/',  view_func=web_main.reject_partner, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/authorize_partner/',  view_func=web_main.authorize_partner, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_recommendation_certificate/',  view_func=web_main.request_recommendation_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_agreement_certificate/',  view_func=web_main.request_agreement_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_reference_certificate/',  view_func=web_main.request_reference_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_alias/',  view_func=web_main.add_alias, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_access/',  view_func=web_main.remove_access, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/import_private_key/',  view_func=web_main.import_private_key, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/import_rsa_key/',  view_func=web_main.import_rsa_key, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_proof_of_identity/',  view_func=web_main.request_proof_of_identity, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_issuer/',  view_func=web_main.add_issuer, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_key/',  view_func=web_main.add_key_for_other, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/remove_issuer/',  view_func=web_main.remove_issuer, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/add_white_issuer/',  view_func=web_main.add_white_issuer, methods = ['GET','POST'], defaults={'mode' : mode})
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

# Centralized route for credential workflow
app.add_url_rule('/company/add_employee/',  view_func=web_workflow.add_employee, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_certificate/',  view_func=web_workflow.request_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/user/request_experience_certificate/',  view_func=web_workflow.request_experience_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/company/dashboard/',  view_func=web_workflow.company_dashboard, methods = ['GET','POST'], defaults={'mode' : mode})
app.add_url_rule('/company/issue_credential_workflow/',  view_func=web_workflow.issue_credential_workflow, methods = ['GET','POST'], defaults={'mode' : mode})


@app.route('/.well-known/did.json', methods=['GET'], defaults={'mode' : mode})
def wellknown (mode) :
    return redirect('/talao/did.json')

@app.route('/<username>/did.json', methods=['GET'], defaults={'mode' : mode})
def web(username, mode) :
    address = ns.get_data_from_username(username, mode).get('address')
    if address :
        pvk = privatekey.get_key(address, 'rsa_key', mode)
        key = jwk.JWK.from_pem(pvk.encode())
        rsa_public = key.export_public(as_dict=True)
        del rsa_public['kid']

        pvk = privatekey.get_key(address, 'private_key', mode)
        key = helpers.ethereum_to_jwk256k(pvk)
        ec_public = json.loads(key)
        del ec_public['d']

        DIDdocument = did_document(username, ec_public, rsa_public)
    else :
        DIDdocument = {'result' : 'No DID found'}
    return jsonify (DIDdocument)

def did_document(username, ec_public, rsa_public) :
    if username == 'talao' :
        id = "did:web:talao.co"
    else :
        id =  "did:web:talao.co:" + username
    return {
                "@context":
                    [
                        "https://www.w3.org/ns/did/v1",
                        {
                            "@base": id
                        }
                    ],
                "id": id,
                "verificationMethod":
                    [
                        {
                        "id": id + "#key-1",
                        "type": "JsonWebKey2020",
                        "publicKeyJwk": ec_public
                        },
                        {
                        "id": id + "#key-2",
                        "type": "JsonWebKey2020",
                        "publicKeyJwk": rsa_public
                        }
                    ],
                "authentication" :
                    [
                    id + "#key-1",
                    id + "#key-2"
                    ],
                "assertionmethod" :
                    [
                    id + "#key-1",
                    id + "#key-2"
                    ]
            }

# MAIN entry point for test
if __name__ == '__main__':

    # info release
    logging.info('flask serveur init')
    app.run(host = mode.flaskserver, port= mode.port, debug = mode.test)