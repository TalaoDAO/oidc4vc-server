"""
test
Main script to start web server through Gunicorn
Arguments of main.py are in gunicornconf.py (global variables) :
$ gunicorn -c gunicornconf.py  --reload wsgi:app

if script is launched without Gunicorn, setup environment variables first :
$ export MYCHAIN=talaonet
$ export MYENV=livebox
$ export WEB3_INFURA_PROJECT_ID=f2be8a3bf04d4a528eb416566f7b5ad6
$ export AUTHLIB_INSECURE_TRANSPORT=1
$ python main.py

Many views are inside this script, others are in web_modules.py. See Centralized routes.

"""
from Crypto.PublicKey import RSA
import sys
import os
import os.path, time
from flask import Flask, session, send_from_directory, flash, jsonify, render_template_string
from flask import request, redirect, render_template,abort, Response, abort
from flask_session import Session
from flask_fontawesome import FontAwesome
import random
import csv
from datetime import timedelta, datetime
import json
from werkzeug.utils import secure_filename
import threading
import copy
import urllib.parse
import unidecode
from eth_keys import keys
from eth_utils import decode_hex
import redis
import requests
from Crypto.PublicKey import RSA
from models import db
from oauth2 import config_oauth



# dependances
import Talao_message
import Talao_ipfs
import createcompany
import createidentity
import constante
from protocol import ownersToContracts, contractsToOwners, save_image, partnershiprequest, remove_partnership, get_image, authorize_partnership, reject_partnership, destroy_workspace
from protocol import delete_key, has_key_purpose, add_key
from protocol import Claim, File, Identity, Document, read_profil
import environment
import hcode
import ns
import analysis
import history
import privatekey
import sms
import QRCode
import user_search

# Centralized  routes
import web_create_identity
import web_certificate
import web_data_user
import web_issue_certificate
import web_skills
import web_CV_blockchain
import web_oauth
import web_issuer_explore

# Environment variables set in gunicornconf.py  and transfered to environment.py
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')

# Environment setup
print('Start to init environment')
mode = environment.currentMode(mychain,myenv)
print('End of init')

# Global variable
exporting_threads = {}

# Constants
FONTS_FOLDER='templates/assets/fonts'
RSA_FOLDER = './RSA_key/' + mode.BLOCKCHAIN
VERSION = "0.13.4"

# Flask and Session setup
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
app.config['RSA_FOLDER'] = RSA_FOLDER
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["jpeg", "jpg", "png", "gif"]

oauth_config = {
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + mode.db_path + '/db.sqlite',
    'OAUTH2_TOKEN_EXPIRES_IN' : {
        'authorization_code': 3000,
        'implicit': 3000,
        'password': 3000,
        'client_credentials': 3000
        }
    }
app.config.update(oauth_config)
sess = Session()
sess.init_app(app)

db.init_app(app)
config_oauth(app)


# bootstrap font managment  -> recheck if needed !!!!!
fa = FontAwesome(app)

# info release
print(__file__, " created: %s" % time.ctime(os.path.getctime(__file__)))

# Centralized @route for create identity
app.add_url_rule('/register/',  view_func=web_create_identity.authentification, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/register/code/', view_func=web_create_identity.POST_authentification_2, methods = ['POST'], defaults={'mode': mode})

# Centralized @route to display certificates
app.add_url_rule('/certificate/',  view_func=web_certificate.show_certificate, defaults={'mode': mode})
app.add_url_rule('/guest/certificate/',  view_func=web_certificate.show_certificate, defaults={'mode': mode})  # idem previous
app.add_url_rule('/certificate/verify/',  view_func=web_certificate.certificate_verify, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/certificate/issuer_explore/',  view_func=web_certificate.certificate_issuer_explore, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/guest/',  view_func=web_certificate.certificate_issuer_explore, methods = ['GET'], defaults={'mode': mode}) # idem previous
app.add_url_rule('/certificate/data/',  view_func=web_certificate.certificate_data, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/certificate/certificate_data_analysis/',  view_func=web_certificate.certificate_data_analysis, methods = ['GET'], defaults={'mode': mode})

# Main routes (Endpointd) for OAuth Authorization Server
app.add_url_rule('/api/v1', view_func=web_oauth.home, methods = ['GET', 'POST'])
app.add_url_rule('/api/v1/oauth_logout', view_func=web_oauth.oauth_logout, methods = ['GET', 'POST'])
app.add_url_rule('/api/v1/oauth_login', view_func=web_oauth.oauth_login, methods = ['GET', 'POST'], defaults ={'mode' : mode})
app.add_url_rule('/api/v1/create_client', view_func=web_oauth.create_client, methods = ['GET', 'POST'])
app.add_url_rule('/api/v1/authorize', view_func=web_oauth.authorize, methods = ['GET', 'POST'], defaults={'mode' : mode})
app.add_url_rule('/api/v1/oauth/token', view_func=web_oauth.issue_token, methods = ['POST'])
app.add_url_rule('/api/v1/oauth_revoke', view_func=web_oauth.revoke_token, methods = ['GET', 'POST'])

app.add_url_rule('/api/v1/create', view_func=web_oauth.oauth_create, methods = ['GET', 'POST'], defaults={'mode' : mode})
app.add_url_rule('/api/v1/user_info', view_func=web_oauth.user_info, methods = ['GET', 'POST'], defaults={'mode' : mode})
app.add_url_rule('/api/v1/request_partnership', view_func=web_oauth.oauth_request_partnership, methods = ['GET', 'POST'], defaults={'mode' : mode})
app.add_url_rule('/api/v1/issue', view_func=web_oauth.oauth_issue, methods = ['GET', 'POST'], defaults={'mode' : mode})

# Centralized route for the Blockchain CV
app.add_url_rule('/resume/', view_func=web_CV_blockchain.resume, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route fo Issuer explore
app.add_url_rule('/user/issuer_explore/', view_func=web_issuer_explore.issuer_explore, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route for user, data, login
app.add_url_rule('/user/',  view_func=web_data_user.user, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/data/',  view_func=web_data_user.data, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/logout/',  view_func=web_data_user.logout, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/forgot_username/',  view_func=web_data_user.forgot_username, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/forgot_password/',  view_func=web_data_user.forgot_password, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/login/authentification/',  view_func=web_data_user.login_authentification, methods = ['POST'], defaults={'mode': mode})
app.add_url_rule('/login/',  view_func=web_data_user.login, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/',  view_func=web_data_user.login, methods = ['GET', 'POST'], defaults={'mode': mode}) # idem previous
app.add_url_rule('/starter/',  view_func=web_data_user.starter, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/use_my_own_address/',  view_func=web_data_user.use_my_own_address, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/user/advanced/',  view_func=web_data_user.user_advanced, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/user/account/',  view_func=web_data_user.user_account, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/company/',  view_func=web_data_user.company, methods = ['GET', 'POST'])
app.add_url_rule('/privacy/',  view_func=web_data_user.privacy, methods = ['GET', 'POST'])


# Centralized route issuer for issue certificate for guest
app.add_url_rule('/issue/',  view_func=web_issue_certificate.issue_certificate_for_guest, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/issue/create_authorize_issue/',  view_func=web_issue_certificate.create_authorize_issue, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/issue/logout/',  view_func=web_issue_certificate.issue_logout, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route issuer for skills
app.add_url_rule('/user/update_skills/',  view_func=web_skills.update_skills, methods = ['GET', 'POST'], defaults={'mode': mode})

# Check if session is active and access is fine. To be used for all routes, excetp external call
def check_login() :
    """ check if the user is correctly logged. This function is called everytime a user function is called """
    if session.get('username') is None :
        abort(403)
    else :
        return session['username']

# helper
def is_username_in_list(my_list, username) :
    for user in my_list :
        if user['username'] == username :
            return True
    return False
# helper
def is_username_in_list_for_partnership(partner_list, username) :
    for partner in partner_list :
        if partner['username'] == username and partner['authorized'] not in ['Removed',"Unknown", "Rejected"]:
            return True
    return False

#HomePage
@app.route('/homepage/', methods=['GET'])
def homepage() :
    check_login()
    if request.method == 'GET' :
        return render_template('homepage.html', **session['menu'])

# picture
""" This is to download the user picture or company logo to the uploads folder """
@app.route('/user/picture/', methods=['GET', 'POST'])
def picture() :
    check_login()
    if request.method == 'GET' :
        if request.args.get('badtype') == 'true' :
            flash('Only "JPEG", "JPG", "PNG" files accepted', 'warning')
        return render_template('picture.html',**session['menu'])
    if request.method == 'POST' :
        myfile = request.files['croppedImage']
        filename = "profile_pic.jpg"
        myfile.save(os.path.join(mode.uploads_path, filename))
        picturefile = mode.uploads_path  + filename
        session['picture'] = save_image(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, picturefile, 'picture',mode, synchronous = False)
        Talao_ipfs.get_picture(session['picture'], mode.uploads_path+ '/' + session['picture'])
        session['menu']['picturefile'] = session['picture']
        return redirect(mode.server + 'user/')

@app.route('/user/success/', methods=['GET'])
def success() :
    check_login()
    if request.method == 'GET' :
        if session['type'] == 'person' :
            flash('Picture has been updated', 'success')
        else :
            flash('Logo has been updated', 'success')
        return redirect(mode.server + 'user/')


@app.route('/user/update_phone/', methods=['GET', 'POST'])
def update_phone() :
    check_login()
    if request.method == 'GET' :
        return render_template('update_phone.html', **session['menu'], phone=session['phone'])
    if request.method == 'POST' :
        _phone = request.form['phone']
        code = request.form['code']
        phone = code + _phone
        if _phone == "" :
            flash('Your phone number has been deleted.', 'success')
            ns.update_phone(session['username'], None, mode)
            session['phone'] = ""
        elif sms.check_phone(phone, mode) :
            ns.update_phone(session['username'], phone, mode)
            session['phone'] = phone
            flash('Your phone number has been updated.', 'success')
        else :
            flash('Incorrect phone number.', 'warning')
        return redirect(mode.server + 'user/')

@app.route('/user/update_password/', methods=['GET', 'POST'])
def update_password() :
    check_login()
    if request.method == 'GET' :
        return render_template('update_password.html', **session['menu'])
    if request.method == 'POST' :
        current_password = request.form['current_password']
        new_password = request.form['password']
        if not ns.check_password(session['username'],current_password, mode) :
            flash ('Wrong password', 'warning')
            return render_template('update_password.html', **session['menu'])
        ns.update_password(session['username'], new_password, mode)
        flash ('Password updated', 'success')
        return redirect(mode.server + 'user/')

# signature
@app.route('/user/signature/', methods=['GET', 'POST'])
def signature() :
    check_login()
    my_signature = session['signature']
    if request.method == 'GET' :
        if request.args.get('badtype') == 'true' :
            flash('Only "JPEG", "JPG", "PNG" files accepted', 'warning')
        return render_template('signature.html', **session['menu'], signaturefile=my_signature)
    if request.method == 'POST' :
        myfile = request.files['croppedImage']
        filename = "signature.png"
        myfile.save(os.path.join(mode.uploads_path, filename))
        signaturefile = mode.uploads_path + '/' + filename
        session['signature'] = save_image(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, signaturefile, 'signature', mode, synchronous = False)
        Talao_ipfs.get_picture(session['signature'], mode.uploads_path+ '/' + session['signature'])
        flash('Your signature has been updated', 'success')
        return redirect(mode.server + 'user/')


# Dashboard, Analysis, history
@app.route('/user/data_analysis/', methods=['GET'])
def data_analysis() :
    check_login()
    if request.method == 'GET' :
        if request.args.get('user') == 'issuer_explore' :
            my_analysis = analysis.dashboard(session['issuer_explore']['workspace_contract'],session['issuer_explore'], mode)
            history_string = history.history_html(session['issuer_explore']['workspace_contract'],15, mode)
        else :
            my_analysis = analysis.dashboard(session['workspace_contract'],session['resume'], mode)
            history_string = history.history_html(session['workspace_contract'],15, mode)

        return render_template('dashboard.html', **session['menu'],    history=history_string,    **my_analysis)

# Test only
@app.route('/user/test/', methods=['GET'])
def test() :
    check_login()
    return render_template('test.html', **session['menu'],test=json.dumps(session['resume'], indent=4))

# search
@app.route('/user/search/', methods=['GET', 'POST'])
def search() :
    check_login()
    if request.method == 'GET' :
        return render_template('search.html', **session['menu'])
    if request.method == 'POST' :
        username_to_search = request.form['username_to_search'].lower()
        if username_to_search == session['username'] :
            flash('Here you are !', 'success')
            return redirect(mode.server + 'user/')
        if not ns.username_exist(username_to_search, mode) :
            print('test username_exist')
            flash('Username not found', "warning")
            return redirect(mode.server + 'user/')
        else :
            return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + username_to_search)

# issue certificate
@app.route('/user/issue_certificate/', methods=['GET', 'POST'])
def issue_certificate():
    check_login()
    if not session['private_key'] :
        flash('Relay does not have your Private Key to issue a Certificate', 'warning')
        return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])
    if request.method == 'GET' :
        goback= request.args['goback']
        return render_template('issue_certificate.html',
                                **session['menu'],
                                issuer_username=session['issuer_username'],
                                goback = goback)
    if request.method == 'POST' :
        if request.form['certificate_type'] == 'experience' :
            if len(session['username'].split('.')) == 2 :
                # look for signature of manager
                manager_username = session['username'].split('.')[0]
                manager_workspace_contract = ns.get_data_from_username(manager_username, mode)['workspace_contract']
                session['certificate_signature'] = get_image(manager_workspace_contract, 'signature', mode)
                # look for firstname, lasname and name of manager
                firstname_claim = Claim()
                lastname_claim = Claim()
                firstname_claim.get_by_topic_name(None, None, manager_workspace_contract, 'firstname', mode)
                lastname_claim.get_by_topic_name(None, None, manager_workspace_contract, 'lastname', mode)
                session['certificate_signatory'] = firstname_claim.claim_value + ' ' + lastname_claim.claim_value
            elif session['type'] == 'company' :
                session['certificate_signature'] = session['signature']
                session['certificate_signatory'] = 'Director'
            else :
                session['certificate_signature'] = session['signature']
                session['certificate_signatory'] = session['name']

            return render_template("issue_experience_certificate.html",
                                    **session['menu'],
                                    manager_name=session['certificate_signatory'],
                                    issuer_username=session['issuer_username'],
                                    talent_name=session['issuer_explore']['name'] )
        elif request.form['certificate_type'] == 'skill' :
            issuer_explore_username = ns.get_username_from_resolver(session['issuer_explore']['workspace_contract'], mode)
            return render_template("create_skill_certificate.html",
                                    **session['menu'],
                                    identity_username=issuer_explore_username )
        else :
            flash('This certificate is not implemented yet !', 'warning')
            return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])

@app.route('/user/issuer_experience_certificate/', methods=['POST'])
def issue_experience_certificate():
    """ The signature is the manager's signature except if the issuer is the company """
    check_login()
    certificate = {
                    "version" : 1,
                    "type" : "experience",
                    "title" : request.form['title'],
                    "description" : request.form['description'],
                    "start_date" : request.form['start_date'],
                    "end_date" : request.form['end_date'],
                    "skills" : request.form['skills'].split(','),
                    "score_recommendation" : request.form['score_recommendation'],
                    "score_delivery" : request.form['score_delivery'],
                    "score_schedule" : request.form['score_schedule'],
                    "score_communication" : request.form['score_communication'],
                    "logo" : session['picture'],
                    "signature" : session['certificate_signature'],
                    "manager" : session['certificate_signatory'],
                    "reviewer" : request.form['reviewer_name']}
    workspace_contract_to = ns.get_data_from_username(session['issuer_username'], mode)['workspace_contract']
    address_to = contractsToOwners(workspace_contract_to, mode)
    my_certificate = Document('certificate')
    execution = my_certificate.add(session['address'],
                        session['workspace_contract'],
                        address_to,
                        workspace_contract_to,
                        session['private_key_value'],
                        certificate,
                        mode,
                        mydays=0,
                        privacy='public',
                         synchronous=True)[0]
    if execution is None :
        flash('Operation failed ', 'danger')
    else :
        flash('Certificate has been issued', 'success')
    del session['certificate_signature']
    del session['certificate_signatory']
    return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])


# issue recommendation for person
@app.route('/user/issue_recommendation/', methods=['GET', 'POST'])
def issue_recommendation():
    check_login()
    if request.method == 'GET' :
        session['talent_to_issue_certificate_username'] = session['issuer_username']
        return render_template('issue_recommendation.html',**session['menu'], issuer_username=request.args['issuer_username'], issuer_name = request.args['issuer_name'])
    if request.method == 'POST' :
        issuer_username = session['talent_to_issue_certificate_username']
        recommendation = {    "version" : 1,
                    "type" : "recommendation",
                    "description" : request.form['description'],
                    "relationship" : request.form['relationship']}
        workspace_contract_to = ns.get_data_from_username(session['talent_to_issue_certificate_username'], mode)['workspace_contract']
        address_to = contractsToOwners(workspace_contract_to, mode)
        my_recommendation = Document('certificate')
        execution = my_recommendation.add(session['address'], session['workspace_contract'], address_to, workspace_contract_to, session['private_key_value'], recommendation, mode, mydays=0, privacy='public', synchronous=True)
        if execution[0] is None :
            flash('Operation failed ', 'danger')
        else :
            flash('Certificate has been issued', 'success')
        del session['talent_to_issue_certificate_username']
        return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + issuer_username)


# personal settings
@app.route('/user/update_personal_settings/', methods=['GET', 'POST'])
def update_personal_settings() :
    check_login()
    personal = copy.deepcopy(session['personal'])
    convert(personal)
    if request.method == 'GET' :
        privacy=dict()
        for topicname in session['personal'].keys() :
            if session['personal'][topicname]['privacy']=='secret' :
                (p1,p2,p3) = ("", "", "selected")
            if session['personal'][topicname]['privacy']=='private' :
                (p1,p2,p3) = ("", "selected", "")
            if session['personal'][topicname]['privacy']=='public' :
                (p1,p2,p3) = ("selected", "", "")
            if session['personal'][topicname]['privacy'] is None :
                (p1,p2,p3) = ("", "", "")
            privacy[topicname] = """
                    <optgroup>
                    <option """+ p1 + """ value="public">Public</option>
                    <option """ + p2 +""" value="private">Private</option>
                    <option """ + p3 + """ value="secret">Secret</option>
                    </opgroup>"""
        return render_template('update_personal_settings.html',
                                **session['menu'],
                                firstname=personal['firstname']['claim_value'],
                                lastname=personal['lastname']['claim_value'],
                                about=personal['about']['claim_value'],
                                education=personal['education']['claim_value'],
                                contact_email=personal['contact_email']['claim_value'],
                                contact_email_privacy=privacy['contact_email'],
                                contact_phone=personal['contact_phone']['claim_value'],
                                contact_phone_privacy=privacy['contact_phone'],
                                birthdate=personal['birthdate']['claim_value'],
                                birthdate_privacy=privacy['birthdate'],
                                postal_address=personal['postal_address']['claim_value'],
                                postal_address_privacy=privacy['postal_address']
                                )
    if request.method == 'POST' :
        form_privacy = dict()
        form_value = dict()
        form_privacy['contact_phone'] = request.form['contact_phone_select']
        form_privacy['contact_email'] = request.form['contact_email_select']
        form_privacy['birthdate'] = request.form['birthdate_select']
        form_privacy['postal_address'] = request.form['postal_address_select']
        form_privacy['firstname'] = 'public'
        form_privacy['lastname'] = 'public'
        form_privacy['about'] = 'public'
        form_privacy['profil_title'] = 'public'
        form_privacy['education'] = 'public'
        change = False
        for topicname in session['personal'].keys() :
            form_value[topicname] = None if request.form[topicname] in ['None', '', ' '] else request.form[topicname]
            if     form_value[topicname] != session['personal'][topicname]['claim_value'] or session['personal'][topicname]['privacy'] != form_privacy[topicname] :
                if form_value[topicname] is not None :
                    claim_id = Claim().relay_add( session['workspace_contract'],topicname, form_value[topicname], form_privacy[topicname], mode)[0]
                    if claim_id is None :
                        flash('Update impossible (RSA not found ?)', 'danger')
                        return redirect(mode.server + 'user/')
                    change = True
                    session['personal'][topicname]['claim_value'] = form_value[topicname]
                    session['personal'][topicname]['privacy'] = form_privacy[topicname]
                    session['personal'][topicname]['claim_id'] = claim_id[2:]
        if change :
            flash('Personal has been updated', 'success')
        return redirect(mode.server + 'user/')

def convert(obj):
    if type(obj) == list:
        for x in obj:
            convert(x)
    elif type(obj) == dict:
        for k, v in obj.items():
            if v is None:
                obj[k] = ''
            else :
                convert(v)
    return True

# company settings
@app.route('/user/update_company_settings/', methods=['GET', 'POST'])
def update_company_settings() :
    check_login()
    personal = copy.deepcopy(session['personal'])
    convert(personal)
    if request.method == 'GET' :
        privacy=dict()
        for topicname in session['personal'].keys() :
            if session['personal'][topicname]['privacy']=='secret' :
                (p1,p2,p3) = ("", "", "selected")
            if session['personal'][topicname]['privacy']=='private' :
                (p1,p2,p3) = ("", "selected", "")
            if session['personal'][topicname]['privacy']=='public' :
                (p1,p2,p3) = ("selected", "", "")
            if session['personal'][topicname]['privacy'] is None :
                (p1,p2,p3) = ("", "", "")
            privacy[topicname] = """
                    <optgroup """ +  """ label="Select">
                    <option """+ p1 + """ value="public">Public</option>
                    <option """ + p2 +""" value="private">Private</option>
                    <option """ + p3 + """ value="secret">Secret</option>
                    </opgroup>"""

        return render_template('update_company_settings.html',
                                **session['menu'],
                                contact_name=personal['contact_name']['claim_value'],
                                contact_name_privacy=privacy['contact_name'],
                                contact_email=personal['contact_email']['claim_value'],
                                contact_email_privacy=privacy['contact_email'],
                                contact_phone=personal['contact_phone']['claim_value'],
                                contact_phone_privacy=privacy['contact_phone'],
                                website=personal['website']['claim_value'],
                                about=personal['about']['claim_value']
                                )
    if request.method == 'POST' :
        form_privacy = dict()
        form_value = dict()
        form_privacy['contact_name'] = request.form['contact_name_select']
        form_privacy['contact_phone'] = request.form['contact_phone_select']
        form_privacy['contact_email'] = request.form['contact_email_select']
        form_privacy['name'] = 'public'
        form_privacy['website'] = 'public'
        form_privacy['about'] = 'public'
        change = False
        for topicname in session['personal'].keys() :
            form_value[topicname] = None if request.form[topicname] in ['None', '', ' '] else request.form[topicname]
            if     form_value[topicname] != session['personal'][topicname]['claim_value'] or session['personal'][topicname]['privacy'] != form_privacy[topicname] :
                if form_value[topicname] is not None :
                    claim_id = Claim().relay_add( session['workspace_contract'],topicname, form_value[topicname], form_privacy[topicname], mode)[0]
                    change = True
                    session['personal'][topicname]['claim_value'] = form_value[topicname]
                    session['personal'][topicname]['privacy'] = form_privacy[topicname]
                    session['personal'][topicname]['claim_id'] = claim_id[2:]
        if change :
            session['menu']['name'] = session['personal']['name']['claim_value']
            flash('Company Settings has been updated', 'success')
        return redirect(mode.server + 'user/')


# digital vault
@app.route('/user/store_file/', methods=['GET', 'POST'])
def store_file() :
    check_login()
    if request.method == 'GET' :
        return render_template('store_file.html', **session['menu'])
    if request.method == 'POST' :
        myfile = request.files['file']
        filename = secure_filename(myfile.filename)
        myfile.save(os.path.join(mode.uploads_path, filename))
        privacy = request.form['privacy']
        user_file = File()
        data = user_file.add(mode.relay_address,
                             mode.relay_workspace_contract,
                             session['address'],
                             session['workspace_contract'],
                             mode.relay_private_key,
                             filename,
                             privacy,
                            mode)
        if data[0] is None :
            flash('Transaction failed', "danger")
        else :
            new_file = {'id' : 'did:talao:'+ mode.BLOCKCHAIN+':'+ session['workspace_contract'][2:]+':document:'+ str(data[0]),
                                    'filename' : filename,
                                    'doc_id' : data[0],
                                    'created' : str(datetime.utcnow()),
                                    'privacy' : privacy,
                                    'doctype' : "",
                                    'issuer' : mode.relay_address,
                                    'transaction_hash' : data[2]
                                    }
            session['identity_file'].append(new_file)
            flash('File ' + filename + ' has been uploaded.', "success")
        return redirect(mode.server + 'user/')

# create company (Talao only)
@app.route('/user/create_company/', methods=['GET', 'POST'])
def create_company() :
    check_login()
    if request.method == 'GET' :
        return render_template('create_company.html', **session['menu'])
    if request.method == 'POST' :
        company_email = request.form['email']
        company_username = request.form['name'].lower()
        if ns.username_exist(company_username, mode)   :
            company_username = company_username + str(random.randint(1, 100))
        workspace_contract = createcompany.create_company(company_email, company_username, mode)[2]
        if workspace_contract is not None :
            claim=Claim()
            claim.relay_add(workspace_contract, 'name', request.form['name'], 'public', mode)
            flash(company_username + ' has been created as company', 'success')
        else :
            flash('Company Creation failed', 'danger')
        return redirect(mode.server + 'user/')

# create a user/identity
@app.route('/user/create_person/', methods=['GET', 'POST'])
def create_person() :
    check_login()
    if request.method == 'GET' :
        return render_template('create_identity.html', **session['menu'])
    if request.method == 'POST' :
        person_email = request.form['email']
        person_firstname = request.form['firstname']
        person_lastname = request.form['lastname']
        person_username = ns.build_username(person_firstname, person_lastname, mode)
        workspace_contract = createidentity.create_user(person_username, person_email, mode, creator=session['address'])[2]
        if workspace_contract is not None :
            claim=Claim()
            claim.relay_add(workspace_contract, 'firstname', person_firstname, 'public', mode)
            claim=Claim()
            claim.relay_add(workspace_contract, 'lastname', person_lastname, 'public', mode)
            flash('New Identity = ' + person_username + ' has been created.', 'success')
        else :
            flash('Identity Creation failed', 'danger')
        return redirect(mode.server + 'user/')

# add experience
@app.route('/user/add_experience/', methods=['GET', 'POST'])
def add_experience() :
	check_login()
	if request.method == 'GET' :
		return render_template('add_experience.html',**session['menu'])
	if request.method == 'POST' :
		my_experience = Document('experience')
		experience = dict()
		experience['company'] = {'contact_email' : request.form['contact_email'],
								'name' : request.form['company_name'],
								'contact_name' : request.form['contact_name'],
								'contact_phone' : request.form['contact_phone']}
		experience['title'] = request.form['title']
		experience['description'] = request.form['description']
		experience['start_date'] = request.form['from']
		experience['end_date'] = request.form['to']
		experience['skills'] = request.form['skills'].split(', ')
		privacy = 'public'
		# issue experience document
		doc_id_exp = my_experience.relay_add(session['workspace_contract'], experience, mode, privacy=privacy)[0]
		if doc_id_exp is None :
			flash('Transaction failed', 'danger')
		else :
			if experience['skills']!= [''] :
				# add skills  in document skill
				for skill in experience['skills'] :
					skill_code = unidecode.unidecode(skill.lower())
					skill_code = skill_code.replace(" ", "")
					skill_code = skill_code.replace("-", "")
					my_skill = {'skill_code' : skill_code,
									'skill_name' : skill.capitalize(),
									'skill_level' : "Intermediate",
									'skill_domain' : ""}
					if session['skills'] is None  :
						session['skills'] = dict()
						session['skills']['description'] = []
						session['skills']['version'] = 1
					for one_skill in session['skills']['description'] :
						if one_skill['skill_code'] == skill_code :
							pass
						else :
							session['skills']['description'].append(my_skill)
							break
				# update skills
				my_skills = Document('skills')
				skill_data = {'version' : session['skills']['version'],  'description' : session['skills']['description']}
				# issue new skill document
				data = my_skills.relay_add(session['workspace_contract'], skill_data, mode)
				if data[0] is None :
					flash('Transaction to add skill failed', 'danger')
					return redirect( mode.server + 'user/')
				doc_id = data[0]
				session['skills']['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] +':document:' + str(doc_id)

			# add experience in current session
			experience['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':document:'+str(doc_id_exp)
			experience['doc_id'] = doc_id_exp
			experience['created'] = str(datetime.now())
			experience['issuer'] = {'workspace_contract' : mode.relay_workspace_contract, 'category' : 2001}
			session['experience'].append(experience)
			flash('New experience added', 'success')
		return redirect(mode.server + 'user/')

# issue kyc (Talao only)
@app.route('/user/issue_kyc/', methods=['GET', 'POST'])
def create_kyc() :
    check_login()
    if request.method == 'GET' :
        return render_template('issue_kyc.html', **session['menu'])
    if request.method == 'POST' :
        my_kyc = dict()
        kyc_username = request.form['username'].lower()
        kyc_workspace_contract = ns.get_data_from_username(kyc_username,mode).get('workspace_contract')
        if kyc_workspace_contract is None :
            flash(kyc_username + ' does not exist ', 'danger')
            return redirect(mode.server + 'user/')
        my_kyc['firstname'] = request.form['firstname']
        my_kyc['lastname'] = request.form['lastname']
        my_kyc['birthdate'] = request.form['birthdate']
        my_kyc['authority'] = request.form['authority']
        my_kyc['card_id'] = request.form['card_id']
        my_kyc['nationality'] = request.form['nationality']
        my_kyc['date_of_issue'] = request.form['date_of_issue']
        my_kyc['date_of_expiration'] = request.form['date_of_expiration']
        my_kyc['sex'] = request.form['sex']
        my_kyc['country'] = request.form['country']
        kyc_workspace_contract = ns.get_data_from_username(kyc_username, mode)['workspace_contract']
        kyc = Document('kyc')
        data = kyc.talao_add(kyc_workspace_contract, my_kyc, mode)[0]
        if data is None :
            flash('Transaction failed', 'danger')
        else :
            flash('New kyc added for '+ kyc_username, 'success')
            text =     "\r\nYour Proof of Identity has been issued by Talao.\r\nCheck your Identity on " + mode.server + 'login/'
            subject = 'Your proof of Identity'
            kyc_email = ns.get_data_from_username(kyc_username, mode)['email']
            Talao_message.message(subject, kyc_email, text, mode)
        return redirect(mode.server + 'user/')


# Create skill certificate
@app.route('/user/create_skill_certificate/', methods=['GET', 'POST'])
def create_skill_certificate() :
    check_login()
    if request.method == 'GET' :
        return render_template('create_skill_certificate.html', **session['menu'])
    if request.method == 'POST' :
        identity_username = request.form['identity_username'].lower()
        certificate = {
                    "version" : 1,
                    "type" : "skill",
                    "title" : request.form['title'],
                    "description" : request.form['description'],
                    "start_date" : "",
                    "end_date" : request.form['date'],
                    "skills" : "",
                    "score_recommendation" : "",
                    "score_delivery" : "",
                    "score_schedule" : "",
                    "score_communication" : "",
                    "logo" : session['picture'],
                    "signature" : session['signature'],
                    "manager" : "Director",
                    "reviewer" : ""}
        workspace_contract_to = ns.get_data_from_username(identity_username, mode)['workspace_contract']
        #address_to = contractsToOwners(workspace_contract_to, mode)
        my_certificate = Document('certificate')
        doc_id = my_certificate.talao_add(workspace_contract_to, certificate, mode)[0]
        #execution = my_certificate.add(session['address'],
        #                session['workspace_contract'],
        #                address_to,
        #                workspace_contract_to,
        #                session['private_key_value'],
        #                certificate,
        #                mode,
        #                mydays=0,
        #                privacy='public',
        #                 synchronous=True)
        if doc_id is None :
            flash('Operation failed ', 'danger')
        else :
            flash('Certificate has been issued', 'success')
            link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract_to[2:] + ':document:' + str(doc_id)
            text =     "\r\nYour Skill Certificate has been issued by Talao.\r\n"
            text = text + '\r\nFollow the link to see the Certificate : ' + link
            subject = 'Your skill certificate'
            identity_email = ns.get_data_from_username(identity_username, mode)['email']
            Talao_message.message(subject, identity_email, text, mode)
        return redirect(mode.server + 'user/')

# remove kyc
@app.route('/user/remove_kyc/', methods=['GET', 'POST'])
def remove_kyc() :
    check_login()
    if request.method == 'GET' :
        session['kyc_to_remove'] = request.args['kyc_id']
        return render_template('remove_kyc.html', **session['menu'])
    if request.method == 'POST' :
        session['kyc'] = [kyc for kyc in session['kyc'] if kyc['id'] != session['kyc_to_remove']]
        doc_id = session['kyc_to_remove'].split(':')[5]
        my_kyc = Document('kyc')
        if session['private_key'] :
            my_kyc.delete(session['workspace_contract'], session['private_key_value'], int(doc_id), mode)
            for counter,kyc in enumerate(session['kyc'], 0) :
                if kyc['doc_id'] == doc_id :
                    del session['kyc'][counter]
                    break
            del session['kyc_to_remove']
            flash('The Proof of Identity has been removed', 'success')
        else :
            flash('You cannot remove theis Proof of Identy (No Private Key found)', 'warning')
        return redirect (mode.server +'user/')



# create kbis (Talao only)
@app.route('/user/issue_kbis/', methods=['GET', 'POST'])
def issue_kbis() :
    check_login()
    if request.method == 'GET' :
        return render_template('issue_kbis.html', **session['menu'])
    if request.method == 'POST' :
        kbis = Document('kbis')
        my_kbis = dict()
        kbis_username = request.form['username']
        kbis_workspace_contract = ns.get_data_from_username(kbis_username,mode).get('workspace_contract')
        if kbis_workspace_contract is None :
            flash(kbis_username + ' does not exist ', 'danger')
            return redirect(mode.server + 'user/')
        my_kbis['name'] = request.form['name']
        my_kbis['date'] = request.form['date']
        my_kbis['legal_form'] = request.form['legal_form']
        my_kbis['capital'] = request.form['capital']
        my_kbis['naf'] = request.form['naf']
        my_kbis['activity'] = request.form['activity']
        my_kbis['address'] = request.form['address']
        my_kbis['ceo'] = request.form['ceo']
        my_kbis['siret'] = request.form['siret']
        my_kbis['managing_director'] = request.form['managing_director']
        data = kbis.talao_add(kbis_workspace_contract, my_kbis, mode)[0]
        if data is None :
            flash('Transaction failed', 'danger')
        else :
            flash('New kbis added for '+ kbis_username, 'success')
        return redirect(mode.server + 'user/')


# remove kbis
@app.route('/user/remove_kbis/', methods=['GET', 'POST'])
def remove_kbis() :
    check_login()
    if request.method == 'GET' :
        session['kbis_to_remove'] = request.args['kbis_id']
        return render_template('remove_kbis.html', **session['menu'])
    if request.method == 'POST' :
        session['kbis'] = [kbis for kbis in session['kbis'] if kbis['id'] != session['kbis_to_remove']]
        doc_id = session['kbis_to_remove'].split(':')[5]
        my_kbis = Document('kbis')
        if session['private_key'] :
            my_kbis.delete(session['workspace_contract'], session['private_key_value'], int(doc_id), mode)
            for counter,kbis in enumerate(session['kbis'], 0) :
                if kbis['doc_id'] == doc_id :
                    del session['kbis'][counter]
                    break
            del session['kbis_to_remove']
            flash('The Proof of Identity has been removed', 'success')
        else :
            flash('You cannot remove this Proof of Identy (No Private Key found)', 'warning')
        return redirect (mode.server +'user/')

@app.route('/user/remove_experience/', methods=['GET', 'POST'])
def remove_experience() :
    check_login()
    if request.method == 'GET' :
        session['experience_to_remove'] = request.args['experience_id']
        session['experience_title'] = request.args['experience_title']
        return render_template('remove_experience.html', **session['menu'], experience_title=session['experience_title'])
    elif request.method == 'POST' :
        session['experience'] = [experience for experience in session['experience'] if experience['id'] != session['experience_to_remove']]
        Id = session['experience_to_remove'].split(':')[5]
        my_experience = Document('experience')
        data = my_experience.relay_delete(session['workspace_contract'], int(Id), mode)
        if data is None :
            flash('Transaction failed', 'danger')
        else :
            del session['experience_to_remove']
            del session['experience_title']
            flash('The experience has been removed', 'success')
        return redirect (mode.server +'user/')


@app.route('/user/remove_certificate/', methods=['GET', 'POST'])
def remove_certificate() :
    check_login()
    if request.method == 'GET' :
        session['certificate_to_remove'] = request.args['certificate_id']
        session['certificate_title'] = request.args['certificate_title']
        return render_template('remove_certificate.html', **session['menu'], certificate_title=session['certificate_title'])
    elif request.method == 'POST' :
        session['certificate'] = [certificate for certificate in session['certificate'] if certificate['id'] != session['certificate_to_remove']]
        Id = session['certificate_to_remove'].split(':')[5]
        my_experience = Document('certificate')
        data = my_experience.relay_delete(session['workspace_contract'], int(Id), mode)
        if data is None :
            flash('Transaction failed', 'danger')
        else :
            del session['certificate_to_remove']
            del session['certificate_title']
            flash('The certificate has been removed', 'success')
        return redirect (mode.server +'user/')


@app.route('/user/remove_file/', methods=['GET', 'POST'])
def remove_file() :
    check_login()
    if request.method == 'GET' :
        session['file_id_to_remove'] = request.args['file_id']
        session['filename_to_remove'] = request.args['filename']
        return render_template('remove_file.html', **session['menu'],filename=session['filename_to_remove'])
    elif request.method == 'POST' :
        session['identity_file'] = [one_file for one_file in session['identity_file'] if one_file['id'] != session['file_id_to_remove']]
        Id = session['file_id_to_remove'].split(':')[5]
        my_file = File()
        data = my_file.relay_delete(session['workspace_contract'], int(Id), mode)
        if data is None :
            flash('Transaction failed', 'danger')
        else :
            del session['file_id_to_remove']
            del session['filename_to_remove']
            flash('The file has been deleted', 'success')
        return redirect (mode.server +'user/')

# add education
@app.route('/user/add_education/', methods=['GET', 'POST'])
def add_education() :
    check_login()
    if request.method == 'GET' :
        return render_template('add_education.html', **session['menu'])
    if request.method == 'POST' :
        my_education = Document('education')
        education  = dict()
        education['organization'] = {'contact_email' : request.form['contact_email'],
                                'name' : request.form['company_name'],
                                'contact_name' : request.form['contact_name'],
                                'contact_phone' : request.form['contact_phone']}
        education['title'] = request.form['title']
        education['description'] = request.form['description']
        education['start_date'] = request.form['from']
        education['end_date'] = request.form['to']
        education['skills'] = request.form['skills'].split(',')
        education['certificate_link'] = request.form['certificate_link']
        privacy = 'public'
        doc_id = my_education.relay_add(session['workspace_contract'], education, mode, privacy=privacy)[0]
        if doc_id is None :
            flash('Transaction failed', 'danger')
        else :
            # add experience in session
            education['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':document:'+str(doc_id)
            education['doc_id'] = doc_id
            education['created'] = str(datetime.now())
            education['issuer'] = {'workspace_contract' : mode.relay_workspace_contract, 'category' : 2001}
            session['education'].append(education)
            flash('New Education added', 'success')
        return redirect(mode.server + 'user/')

@app.route('/user/remove_education/', methods=['GET', 'POST'])
def remove_education() :
    check_login()
    if request.method == 'GET' :
        session['education_to_remove'] = request.args['education_id']
        session['education_title'] = request.args['education_title']
        return render_template('remove_education.html', **session['menu'], education_title=session['education_title'])
    elif request.method == 'POST' :
        session['education'] = [education for education in session['education'] if education['id'] != session['education_to_remove']]
        doc_id = session['education_to_remove'].split(':')[5]
        my_education = Document('education')
        data = my_education.relay_delete(session['workspace_contract'], int(doc_id), mode)
        if data is None :
            flash('Transaction failed', 'danger')
        else :
            for counter,edu in enumerate(session['education'], 0) :
                if edu['doc_id'] == doc_id :
                    del session['education'][counter]
                    break
            del session['education_to_remove']
            del session['education_title']
            flash('The Education has been removed', 'success')
        return redirect (mode.server +'user/')

# invit
@app.route('/user/invit/', methods=['GET', 'POST'])
def invit() :
    check_login()
    if request.method == 'GET' :
        return render_template('invit.html', **session['menu'])
    if request.method == 'POST' :
        talent_email = request.form['email']
        memo = request.form['memo']
        username_list = ns.get_username_list_from_email(talent_email, mode)
        if username_list != [] :
            msg = 'This email is already used by Identity(ies) : ' + ", ".join(username_list) + ' . Use the Search Bar.'
            flash(msg , 'warning')
            return redirect(mode.server + 'user/')
        link = mode.server + 'register/'
        if memo in [None, "", " " ] :
            memo = "hello,"
        msg = "".join([memo,
                        "\r\n\r\nYou can follow this link to register through the Talao platform.\r\n\r\nYour Identity will be tamper proof.\r\n\r\nFollow this link to proceed : ",
                        link])
        subject = 'You have received an invitation from '+ session['name']
        execution = Talao_message.message(subject, talent_email, msg, mode)
        if execution :
            flash('Your invit has been sent', 'success')
        else :
            flash('Your invit has not been sent', 'danger')
        return redirect(mode.server + 'user/')

# send memo by email
@app.route('/user/send_memo/', methods=['GET', 'POST'])
def send_memo() :
    check_login()
    if request.method == 'GET' :
        session['memo_username'] = request.args['issuer_username']
        return render_template('send_memo.html', **session['menu'], memo_username=session['memo_username'])
    if request.method == 'POST' :
        # email to issuer
        subject = "You have received a memo from " + session['name'] +"."
        text = request.form['memo']
        memo_email = ns.get_data_from_username(session['memo_username'], mode)['email']
        Talao_message.message(subject, memo_email, text, mode)
        # message to user
        flash("Your memo has been sent to " + session['memo_username'], 'success')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['memo_username'])

# request partnership
@app.route('/user/request_partnership/', methods=['GET', 'POST'])
def resquest_partnership() :
    check_login()
    if request.method == 'GET' :
        session['partner_username'] = request.args['issuer_username']
        return render_template('request_partnership.html', **session['menu'], partner_username=session['partner_username'])
    if request.method == 'POST' :
        partner_workspace_contract = ns.get_data_from_username(session['partner_username'], mode)['workspace_contract']
        partner_address = contractsToOwners(partner_workspace_contract, mode)
        partner_publickey = mode.w3.solidityKeccak(['address'], [partner_address]).hex()
        if not session['rsa_key'] :
            flash('Request Partnership to ' + session['partner_username'] + ' is not available (RSA key not found)', 'warning')
            return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['partner_username'])
        #relay signs the transaction"
        if  partnershiprequest(mode.relay_address,
                                 mode.relay_workspace_contract,
                                 session['address'],
                                 session['workspace_contract'],
                                 mode.relay_private_key,
                                 partner_workspace_contract,
                                 session['rsa_key_value'],
                                 mode,
                                 synchronous= True) :
            # add partnership in current session
            session['partner'].append({"address": partner_address,
                                "publickey": partner_publickey,
                                 "workspace_contract" : partner_workspace_contract,
                                  'username' : session['partner_username'],
                                  'authorized' : 'Authorized',
                                  'status' : "Pending"
                                  })
            # add partner in the issuer list if not already in
            if not is_username_in_list(session['issuer'], session['partner_username']) :
                if not add_key(mode.relay_address,
                             mode.relay_workspace_contract,
                             session['address'],
                             session['workspace_contract'],
                             mode.relay_private_key,
                             partner_address,
                             20002,
                             mode,
                             synchronous=True) :
                    flash('transaction for add issuer failed', 'danger')
                else :
                    session['issuer'].append(ns.get_data_from_username(session['partner_username'], mode))
            # user message
            flash('You have send a Request for Partnership to ' + session['partner_username'], 'success')
            # partner email
            subject = session['name'] + " souhaite accéder aux données privées de votre Identité Talao"
            text = "\r\n".join(['',
                    'Vous pouvez accepter ou refuser sa demande en allant sur ' + mode.server,
                    """Dans votre menu, choisissez l'option 'Advanced', puis l'option 'Partner List'.""",
                    'Acceptez ou refusez sa demande en cliquant sur un des icons.',
                    '',
                    'Des informations complémentaires sur ' + session['name'] + ' sont disponibles ici ' + session['menu']['clipboard']])
            partner_email = ns.get_data_from_username(session['partner_username'], mode)['email']
            Talao_message.message(subject, partner_email, text, mode)
        else :
            flash('Request to ' + session['partner_username'] + ' failed', 'danger')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['issuer_username'])

# remove partnership
@app.route('/user/remove_partner/', methods=['GET', 'POST'])
def remove_partner() :
    check_login()
    if request.method == 'GET' :
        session['partner_username_to_remove'] = request.args['partner_username']
        session['partner_workspace_contract_to_remove'] = request.args['partner_workspace_contract']
        return render_template('remove_partner.html', **session['menu'], partner_name=session['partner_username_to_remove'])
    if request.method == 'POST' :
        res = remove_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_remove'], mode)
        if not res :
            flash ('Partnership removal has failed')
        else :
            # remove partneship in current session
            session['partner'] = [ partner for partner in session['partner'] if partner['workspace_contract'] != session['partner_workspace_contract_to_remove']]
            flash('The partnership with '+session['partner_username_to_remove']+ '  has been removed', 'success')
        del session['partner_username_to_remove']
        del session['partner_workspace_contract_to_remove']
        return redirect (mode.server +'user/')

# reject partnership
@app.route('/user/reject_partner/', methods=['GET', 'POST'])
def reject_partner() :
    check_login()
    if request.method == 'GET' :
        session['partner_username_to_reject'] = request.args['partner_username']
        session['partner_workspace_contract_to_reject'] = request.args['partner_workspace_contract']
        return render_template('reject_partner.html', **session['menu'], partner_name=session['partner_username_to_reject'])
    if request.method == 'POST' :
        res = reject_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_reject'], mode)
        if not res :
            flash ('Partnership rejection has failed')
        else :
            # remove partnership in current session
            session['partner'] = [ partner for partner in session['partner'] if partner['workspace_contract'] != session['partner_workspace_contract_to_reject']]
            # message to user
            flash('The Partnership with '+session['partner_username_to_reject']+ '  has been rejected', 'success')
            # email to partner
            subject = "Your Request for Partnership has been rejected by " + session['name']
            text = ""
            partner_email = ns.get_data_from_username(session['partner_username_to_reject'], mode)['email']
            Talao_message.message(subject, partner_email, text, mode)
        del session['partner_username_to_reject']
        del session['partner_workspace_contract_to_reject']
        return redirect (mode.server +'user/')

# authorize partnership
@app.route('/user/authorize_partner/', methods=['GET', 'POST'])
def authorize_partner() :
    check_login()
    if request.method == 'GET' :
        session['partner_username_to_authorize'] = request.args['partner_username']
        session['partner_workspace_contract_to_authorize'] = request.args['partner_workspace_contract']
        return render_template('authorize_partner.html', **session['menu'], partner_name=session['partner_username_to_authorize'])
    if request.method == 'POST' :
        if not session['rsa_key'] :
            flash('Request a Partnership to ' + session['partner_username'] + ' is impossible (RSA key not found)', 'warning')
            del session['partner_username_to_authorize']
            del session['partner_workspace_contract_to_authorize']
            return redirect (mode.server +'user/')
        res= authorize_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_authorize'], session['rsa_key_value'], mode)
        if not res :
            flash ('Partnership authorize has failed', 'danger')
        else :
            flash('The partnership with '+session['partner_username_to_authorize']+ '  has been authorized', 'success')
            # update partnership in current session
            for partner in session['partner'] :
                if partner['workspace_contract'] == session['partner_workspace_contract_to_authorize'] :
                    partner['authorized'] = "Authorized"
                    break
        del session['partner_username_to_authorize']
        del session['partner_workspace_contract_to_authorize']
        return redirect (mode.server +'user/')


# request certificate to be completed with email
@app.route('/user/request_certificate/', methods=['GET', 'POST'])
def request_certificate() :
    """ The request comes from the Search Bar or from Menu"""
    check_login()
    if request.method == 'GET' :
        session['certificate_issuer_username'] = request.args.get('issuer_username')
        # The call comes from Menu, we ask for email
        if session['certificate_issuer_username'] is None :
            display_email = True
            # always recommendation option displayed
            reco = True
        # the call comes from search bar (issuer_explore view)
        else :
            display_email = False
            if session['issuer_explore']['type'] == 'person' :
                # one displays the recommendation option
                reco = True
            else :
                reco = False
            # Check if issuer has private key
            issuer_address = session['issuer_explore']['address']
            if privatekey.get_key(issuer_address, 'private_key', mode) is None :
                flash('Sorry, this Referent cannot issue Certificates.', 'warning')
                return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['certificate_issuer_username'])
        return render_template('request_certificate.html', **session['menu'], display_email=display_email, reco=reco)
    if request.method == 'POST' :
        # From Menu, if issuer does not exist, he has to be created
        if session.get('certificate_issuer_username') is None :
            session['issuer_email'] = request.form['issuer_email']
            # One checks if the issuer exists
            username_list = ns.get_username_list_from_email(request.form['issuer_email'], mode)
            if username_list != [] :
                msg = 'This email is already used by Identity(ies) : ' + ", ".join(username_list) + ' . Use the Search Bar.'
                flash(msg , 'warning')
                return redirect(mode.server + 'user/')
        # From Search Bar, issuer exist
        else :
            session['issuer_email'] = ns.get_data_from_username(session['certificate_issuer_username'], mode)['email']
        if request.form['certificate_type'] == 'experience' :
            return render_template('request_experience_certificate.html', **session['menu'])
        elif request.form['certificate_type'] == 'recommendation' :
            return render_template('request_recommendation_certificate.html', **session['menu'])

@app.route('/user/request_recommendation_certificate/', methods=['POST'])
def request_recommendation_certificate() :
    """ With this view one sends an email with link to the Referent"""
    check_login()
    memo = request.form.get('memo')
    issuer_username = 'new' if session.get('certificate_issuer_username') is None else session['certificate_issuer_username']
    issuer_workspace_contract = 'new' if session.get('certificate_issuer_username') is None else session['issuer_explore']['workspace_contract']
    issuer_name = 'new' if session.get('certificate_issuer_username') is None else session['issuer_explore']['name']

    # email to Referent/issuer
    parameters = {'issuer_email' : session['issuer_email'],
                    'issuer_username' : issuer_username,
                    'issuer_workspace_contract' : issuer_workspace_contract,
                    'issuer_name' : issuer_name,
                    'certificate_type' : 'recommendation',
                    'talent_name' : session['name'],
                    'talent_username' : session['username'],
                    'talent_workspace_contract' : session['workspace_contract']
                    }
    link = urllib.parse.urlencode(parameters)
    url = mode.server + 'issue/?' + link
    if memo == "" or memo is None :
        memo = "Hello,"
    text = "".join([memo,
                    "\r\n\r\nYou can follow this link to issue a certificate to ",
                    session['name'],
                    " through the Talao platform.\r\n\r\nThis certificate will be stored on a Blockchain decentralized network. Data will be tamper proof and owned by Talent.\r\n\r\nFollow this link to proceed : ",
                    url])
    subject = 'You have received a request for recommendation from '+ session['name']
    Talao_message.message(subject, session['issuer_email'], text, mode)
    # message to user vue
    flash('Your request for Recommendation has been sent.', 'success')
    # email to user/Talent
    subject = "Your request for certificate has been sent."
    text = "".join(["Dear ",
                    session['personal']['firstname']['claim_value'],",",
                    "\r\n\r\nYou will receive an email when your Referent connects."])
    user_email = ns.get_data_from_username(session['username'], mode)['email']
    Talao_message.message(subject, user_email, text, mode)
    del session['issuer_email']
    if session.get('certificate_issuer_username') is not None :
        del session['certificate_issuer_username']
        return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + issuer_username)
    return redirect(mode.server + 'user/')

@app.route('/user/request_experience_certificate/', methods=['POST'])
def request_experience_certificate() :
    """ This is to send the email with link """
    check_login()
    # email to Referent/issuer
    memo = request.form.get('memo')
    issuer_username = 'new' if session.get('certificate_issuer_username') is None else session.get('certificate_issuer_username')
    issuer_workspace_contract = 'new' if session.get('certificate_issuer_username') is None else session['issuer_explore']['workspace_contract']
    issuer_name = 'new' if session.get('certificate_issuer_username') is None else session['issuer_explore']['name']
    parameters = {'issuer_email' : session['issuer_email'],
            'certificate_type' : 'experience',
            'title' : request.form['title'],
             'description' : request.form['description'],
             'skills' :request.form['skills'],
             'end_date' :  request.form['end_date'],
             'start_date' : request.form['start_date'],
             'talent_name' : session['name'],
             'talent_username' : session['username'],
             'talent_workspace_contract' : session['workspace_contract'],
             'issuer_username' : issuer_username,
             'issuer_workspace_contract' : issuer_workspace_contract,
             'issuer_name' : issuer_name}

    link = urllib.parse.urlencode(parameters)
    url = mode.server + 'issue/?' + link
    if memo == "" or memo is None :
        memo = "Hello,"
    text = "".join([memo,
                    "\r\n\r\nYou can follow this link to issue a certificate to ",
                     session['name'],
                     " through the Talao platform.\r\n\r\nThis certificate will be stored on a Blockchain decentralized network. Data will be tamper proof and owned by Talent.\r\n\r\nFollow this link to proceed : ", url])
    subject = 'You have received a request for certification from '+ session['name']
    Talao_message.message(subject, session['issuer_email'], text, mode)
    # email to user/Talent
    subject = "Your request for certificate has been sent."
    text = "".join(["Dear ",
                    session['personal']['firstname']['claim_value'],",",
                    "\r\n\r\nYou will receive an email when your Referent connects."])
    user_email = ns.get_data_from_username(session['username'], mode)['email']
    Talao_message.message(subject, user_email, text, mode)
    # message to user/Talent
    flash('Your request for an Experience Certificate has been sent.', 'success')
    del session['issuer_email']
    if session.get('certificate_issuer_username') is not None :
        del session['certificate_issuer_username']
        return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + issuer_username)
    else :
        return redirect(mode.server + 'user/')

# add alias (Username)
@app.route('/user/add_alias/', methods=['GET', 'POST'])
def add_alias() :
    check_login()
    if request.method == 'GET' :
        return render_template('add_alias.html', **session['menu'])
    if request.method == 'POST' :
        if ns.username_exist(request.form['access_username'],mode) :
            flash('Username already used' , 'warning')
        else :
            alias_username = request.form['access_username']
            ns.add_alias(alias_username, session['username'], request.form['access_email'], mode)
            flash('Alias added for '+ alias_username , 'success')
        return redirect (mode.server +'user/')

# remove alias
@app.route('/user/remove_access/', methods=['GET'])
def remove_access() :
    check_login()
    username_to_remove = request.args['username_to_remove']
    manalias_name,s,host_name = username_to_remove.partition('.')
    if host_name != "" :
        execution = ns.remove_manager(manalias_name, host_name, mode)
    else :
        execution = ns.remove_alias(manalias_name, mode)
    if execution :
        flash(username_to_remove + ' has been removed', 'success')
    else :
        flash('Operation failed', 'danger')
    return redirect (mode.server +'user/')

# Import private key
@app.route('/user/import_private_key/', methods=['GET', 'POST'])
def import_private_key() :
    check_login()
    if request.method == 'GET' :
        return render_template('import_private_key.html', **session['menu'])
    if request.method == 'POST' :
        data = {'username' : session['username'],
                'address' : session['address'],
                'created' : str(datetime.today()),
                'private_key' : request.form['private_key'],
                'workspace_contract' : session['workspace_contract'],
                'email' : ns.get_data_from_username(session['username'], mode)['email'],
                'secret' : None,
                'aes' : None}
        priv_key_bytes = decode_hex(request.form['private_key'])
        priv_key = keys.PrivateKey(priv_key_bytes)
        pub_key = priv_key.public_key
        address = pub_key.to_checksum_address()
        if address != session['address'] :
            flash('Wrong Private Key', 'warning')
            return redirect (mode.server +'user/')
        session['private_key'] = True
        session['private_key_value'] = request.form['private_key']
        privatekey.add_identity(data, mode)
        flash('Private Key has been imported',  'success')
        return redirect (mode.server +'user/')

# Import rsa key
@app.route('/user/import_rsa_key/', methods=['GET', 'POST'])
def import_rsa_key() :
    check_login()
    if request.method == 'GET' :
        return render_template('import_rsa_key.html', **session['menu'])
    if request.method == 'POST' :
        if 'file' not in request.files :
            flash('no file', "warning")
            return redirect(mode.server + 'user/')
        myfile = request.files['file']
        filename = secure_filename(myfile.filename)
        myfile.save(os.path.join(app.config['RSA_FOLDER'], filename))
        filename = "./RSA_key/"+mode.BLOCKCHAIN + '/' + filename
        try :
            f = open(filename,'r')
            key = RSA.import_key(f.read())
            RSA_public = key.publickey().exportKey('PEM')
        except :
            flash('RSA key is not found', 'danger')
            return redirect (mode.server +'user/')
        contract = mode.w3.eth.contract(session['workspace_contract'],abi=constante.workspace_ABI)
        identity_key = contract.functions.identityInformation().call()[4]
        if RSA_public == identity_key :
            session['rsa_key'] = True
            session['rsa_key_value'] = key.exportKey('PEM')
            flash('RSA Key has been uploaded',  'success')
        else :
            flash('RSA key is not correct', 'danger')
        return redirect (mode.server +'user/')


# add manager
@app.route('/user/add_manager/', methods=['GET', 'POST'])
def add_manager() :
    check_login()
    if request.method == 'GET' :
        return render_template('add_manager.html', **session['menu'])
    if request.method == 'POST' :
        if not ns.username_exist(request.form['manager_username'].lower(),mode)  :
            flash('Username not found' , 'warning')
        else :
            manager_username = request.form['manager_username']
            ns.add_manager(manager_username, manager_username, session['username'], request.form['manager_email'], mode)
            flash('Manager added for '+ manager_username.lower() , 'success')
        return redirect (mode.server +'user/')


# request proof of Identity
@app.route('/user/request_proof_of_identity/', methods=['GET', 'POST'])
def request_proof_of_identity() :
    check_login()
    if request.method == 'GET' :
        return render_template('request_proof_of_identity.html', **session['menu'])
    elif request.method == 'POST' :
        id_file = request.files['id_file']
        selfie_file = request.files['selfie_file']

        id_file_name = secure_filename(id_file.filename)
        selfie_file_name = secure_filename(selfie_file.filename)

        id_file.save(os.path.join('./uploads/proof_of_identity', session['username'] + "_ID." + id_file_name))
        selfie_file.save(os.path.join('./uploads/proof_of_identity', session['username'] + "_selfie." + selfie_file_name))

        # email to user/Talent
        subject = "Your request for a proof of Identity has been sent."
        text = " You will receive an email soon."
        user_email = ns.get_data_from_username(session['username'], mode)['email']
        Talao_message.message(subject, user_email, text, mode)
        # email with files to Admin
        message = 'Request for proof of identity for ' + session['username'] + '\r\nEmail = ' + request.form.get('email', 'off') + '\r\nPhone = ' + request.form.get('phone', 'off')
        filename_list = [session['username'] + "_ID." + id_file_name, session['username'] + "_selfie." + selfie_file_name]
        Talao_message.message_file([mode.admin], message, 'files for proof of Identity', filename_list, '/home/thierry/Talao/uploads/proof_of_identity/', mode)
        # message to user
        flash(' Thank you, we will check your documents soon.', 'success')
        return redirect (mode.server +'user/')

# add Issuer, they have an ERC725 key with purpose 20002 (or 1) to issue Document (Experience, Certificate)
@app.route('/user/add_issuer/', methods=['GET', 'POST'])
def add_issuer() :
    check_login()
    if request.method == 'GET' :
        session['referent_username'] = request.args['issuer_username']
        if session['referent_username'] == session['username' ] :
            flash('You cannot be the Referent of yourself.', 'warning')
            return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['referent_username'])
        return render_template('add_referent.html', **session['menu'], referent_username=session['referent_username'])
    elif request.method == 'POST' :
        issuer_workspace_contract = ns.get_data_from_username(session['referent_username'],mode)['workspace_contract']
        issuer_address = contractsToOwners(issuer_workspace_contract, mode)
        if not add_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 20002, mode, synchronous=True) :
            flash('transaction failed', 'danger')
        else :
            # update issuer list in session
            #issuer_key = mode.w3.soliditySha3(['address'], [issuer_address])
            #contract = mode.w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
            issuer_workspace_contract = ownersToContracts(issuer_address, mode)
            session['issuer'].append(ns.get_data_from_username(session['referent_username'], mode))
            # email to issuer
            if session['issuer_explore']['category'] == 2001 :
                subject = "Your company has been chosen by " + session['name'] + " as a Referent."
            else :
                subject = "You have been chosen by " + session['name'] + " as a Referent."
            text = " You can now issue Certficates to " + session['name'] + ". Go to " + mode.server +"login/ to proceed."
            issuer_email = ns.get_data_from_username(session['referent_username'], mode)['email']
            Talao_message.message(subject, issuer_email, text, mode)
            # message to user
            flash(session['referent_username'] + ' has been added as a Referent. An email has been sent too.', 'success')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['referent_username'])

# remove issuer
@app.route('/user/remove_issuer/', methods=['GET', 'POST'])
def remove_issuer() :
    check_login()
    if request.method == 'GET' :
        session['issuer_username_to_remove'] = request.args['issuer_username']
        session['issuer_address_to_remove'] = request.args['issuer_address']
        return render_template('remove_issuer.html', **session['menu'],issuer_name=session['issuer_username_to_remove'])
    elif request.method == 'POST' :
        #address_partner = session['issuer_address_to_remove']
        if not delete_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['issuer_address_to_remove'], 20002, mode) :
            flash ('transaction failed', 'danger')
        else :
            session['issuer'] = [ issuer for issuer in session['issuer'] if issuer['address'] != session['issuer_address_to_remove']]
            flash('The Issuer '+session['issuer_username_to_remove']+ '  has been removed', 'success')
        del session['issuer_username_to_remove']
        del session['issuer_address_to_remove']
        return redirect (mode.server +'user/')


# add  White Issuer or WhiteList They all have an ERC725 key with purpose 5
@app.route('/user/add_white_issuer/', methods=['GET', 'POST'])
def add_white_issuer() :
    check_login()
    if request.method == 'GET' :
        session['whitelist_username'] = request.args['issuer_username']
        return render_template('add_white_issuer.html', **session['menu'], whitelist_username=session['whitelist_username'])
    elif request.method == 'POST' :
        issuer_workspace_contract = ns.get_data_from_username(session['whitelist_username'],mode)['workspace_contract']
        issuer_address = contractsToOwners(issuer_workspace_contract, mode)
        if not add_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 5, mode, synchronous=True) :
            flash('transaction failed', 'danger')
        else :
            # update issuer list in session
            #issuer_key = mode.w3.soliditySha3(['address'], [issuer_address])
            #contract = mode.w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
            issuer_workspace_contract = ownersToContracts(issuer_address, mode)
            session['whitelist'].append(ns.get_data_from_username(session['whitelist_username'], mode))
            flash(session['whitelist_username'] + ' has been added as Issuer in your White List', 'success')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['referent_username'])

# remove white issuer
@app.route('/user/remove_white_issuer/', methods=['GET', 'POST'])
def remove_white_issuer() :
    check_login()
    if request.method == 'GET' :
        session['issuer_username_to_remove'] = request.args['issuer_username']
        session['issuer_address_to_remove'] = request.args['issuer_address']
        return render_template('remove_white_issuer.html', **session['menu'], issuer_name=session['issuer_username_to_remove'])
    elif request.method == 'POST' :
        #address_partner = session['issuer_address_to_remove']
        if not delete_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['issuer_address_to_remove'], 5, mode) :
            flash('transaction failed', 'danger')
        else :
            session['whitelist'] = [ issuer for issuer in session['whitelist'] if issuer['address'] != session['issuer_address_to_remove']]
            flash('The Issuer '+session['issuer_username_to_remove']+ '  has been removed from your White list', 'success')
        del session['issuer_username_to_remove']
        del session['issuer_address_to_remove']
        return redirect (mode.server +'user/')


# delete user identity
@app.route('/user/delete_identity/', methods=['GET', 'POST'])
def delete_identity() :
    check_login()
    if request.method == 'GET' :
        if not session['private_key'] :
            flash('Identity deletion is not possible as there is no private key', 'danger')
            return redirect (mode.server +'user/')
        else :
            return render_template('delete_identity.html', **session['menu'])
    elif request.method == 'POST' :
        if not ns.check_password(session['username'], request.form['password'], mode) :
            flash('Wrong password', 'danger')
            return redirect (mode.server +'user/')
        else :
            destroy_workspace(session['workspace_contract'], session['private_key_value'], mode)
            ns.delete_identity(session['username'], mode)
            flash('Your Identity has been deleted from Blockchain', 'success')
            return redirect (mode.server +'login/')


# photos upload for certificates
@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(mode.uploads_path, filename)

# fonts upload
@app.route('/fonts/<filename>')
def send_fonts(filename):
    return send_from_directory(FONTS_FOLDER, filename)

@app.route('/user/download/', methods=['GET', 'POST'])
def download():
    filename = request.args['filename']
    return send_from_directory(mode.uploads_path,
                               filename, as_attachment=True)

@app.route('/user/download_rsa_key/', methods=['GET', 'POST'])
def download_rsa_key():
    filename = request.args['filename']
    return send_from_directory(app.config['RSA_FOLDER'],
                               filename, as_attachment=True)


@app.route('/user/download_QRCode/', methods=['GET', 'POST'])
def download_QRCode():
    QRCode.get_QRCode(mode,  mode.server + "resume/?workspace_contract=" + session['workspace_contract'])
    filename = 'External_CV_QRCode.png'
    return send_from_directory(mode.uploads_path,
                               filename, as_attachment=True)

@app.route('/user/typehead/', methods=['GET', 'POST'])
def typehead() :
    return render_template('typehead.html')

# To manage the navbar search field. !!!! The json file is uploaded once
@app.route('/user/data/', methods=['GET', 'POST'])
def talao_search() :
    print('Upload prefetch file')
    filename = request.args['filename']
    return send_from_directory(mode.uploads_path,
                               filename, as_attachment=True)

# This is the DID proof
@app.route('/did/', methods=['GET'])
def did_check () :
    html = """<!DOCTYPE html>
        <html lang="en">
            <body>
                <h1>Talao</h1>
                <h2>https://talao.co and https://talao.io</h2>
                <h2>Our Decentralized IDentifiers are : </h2>
                <p>
                    <li><b>did:talao:talaonet:4562DB03D8b84C5B10FfCDBa6a7A509FF0Cdcc68</b></li>
                    <li><b>did:talao:rinkeby:fafDe7ae75c25d32ec064B804F9D83F24aB14341</b></li>
                </p>
            </body>
        </html>"""
    return render_template_string(html)

# This is to call the DID proof
@app.route('/call_did/', methods=['GET'])
def call_did_check () :
    link = request.args['website']+'/did/'
    return redirect (link)



#######################################################
#                        MAIN, server launch
#######################################################
# setup du registre nameservice

print('initialisation du serveur')


if __name__ == '__main__':
    app.run(host = mode.flaskserver, port= mode.port, debug = mode.test)
