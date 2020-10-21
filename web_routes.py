

"""
External routes for Oauth clients
flow available :
'password'
    curl -u ${client_id}:${client_secret} -XPOST http://127.0.0.1:3000/api/v1/oauth/token -F grant_type=password -F username=${username} -F password=valid -F scope=profile
    curl -H "Authorization: Bearer ${access_token}" http://127.0.0.1:3000/api/v1/api/me

'client_credentials' Celui que l on utilise
    curl -u pyD3s4TGQL6j1B4w1Dz522g3:6elzYVTLDxbBUKUIKdPT2FZ6keOf8zTqGO2RrnuBfTSDPElY -XPOST http://127.0.0.1:5000/api/v1/oauth/token -F grant_type=client_credentials -F scope=profile

    curl -H "Authorization: Bearer jPEFgk8tuql278BEi0tHqGD3sMmVbJTi2Cj7EbuKtB" http://127.0.0.1:5000/api/v1/api/me

'authorization_code' : celui de France Connect (avec en plus OpenId option)
    open http://127.0.0.1:3000/api/v1/oauth/authorize?response_type=code&client_id=${client_id}&scope=profile
    After granting the authorization, you should be redirected to `${redirect_uri}/?code=${code}`

    curl -u ${client_id}:${client_secret} -XPOST http://127.0.0.1:5000/oauth/token -F grant_type=authorization_code -F scope=profile -F code=${code}

    curl -H "Authorization: Bearer ${access_token}" http://127.0.0.1:3000/api/v1/api/me
"""




import os
import time
from flask import request, session, url_for, Response, abort, flash
from flask import render_template, redirect, jsonify
from werkzeug.security import gen_salt
from authlib.integrations.flask_oauth2 import current_token, client_authenticated
from authlib.oauth2 import OAuth2Error, OAuth2Request
from models import db, User, OAuth2Client
from oauth2 import authorization, require_oauth
import json
import ns
import environment
import constante
from protocol import read_profil, Identity, Talao_token_transaction
from urllib.parse import urlencode, parse_qs, urlparse
import createidentity




def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if session.get('username') is None :
		abort(403)
	else :
		return session['username']

def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None

def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


#@bp.route('/api/v1', methods=('GET', 'POST'))
def home():
    check_login()
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session['id'] = user.id
        # if user is not just to log in, but need to head back to the auth page, then go for it
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect('/api/v1')
    user = current_user()
    if user:
        clients = OAuth2Client.query.filter_by(user_id=user.id).all()
    else:
        clients = []
    return render_template('/oauth/home.html', user=user, clients=clients)


#@bp.route('/api/v1/oauth_logout')
def oauth_logout():
    check_login()
    del session['id']
    return redirect('/user')

""" login pour les utilisateurs qui viennent d'une application cliente par OAuth2
Le login doit etre de type two factor

"""
#@bp.route('/api/v1/oauth_login')
def oauth_login(mode):
    if request.method == 'GET' :
        session['url'] = request.args.get('next')
        return render_template('/oauth/oauth_login.html')
    if request.method  == 'POST' :
        url = session['url']
        username = request.form.get('username')
        if not ns.username_exist(username, mode)  :
            flash('Username not found', "warning")
            return redirect(url)
        if not ns.check_password(username, request.form['password'].lower(), mode)  :
            flash('Wrong password', "warning")
            return redirect(url)
        # if secret code wrong redirect to url
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session['id'] = user.id
        print('User logged in Talao.co')
        session['username']=username
    return redirect(url)


#@bp.route('/api/v1/create_client', methods=('GET', 'POST'))
""" gestion des grant client 
"""
def create_client():
    check_login()
    user = current_user()
    if not user:
        return redirect('/api/v1')
    if request.method == 'GET':
        return render_template('/oauth/create_client.html')

    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=user.id,
    )
    form = request.form
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"]
    }
    client.set_client_metadata(client_metadata)
    if form['token_endpoint_auth_method'] == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)
    db.session.add(client)
    db.session.commit()
    return redirect('/api/v1')

#@bp.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    check_login()
    return authorization.create_endpoint_response('revocation')

#@bp.route('/api/v1/oauth/token', methods=['POST'])
def issue_token():
    print('request reçue dans /token = ', request.__dict__)
    response = authorization.create_token_response()
    print(response)
    return response




# AUTHORIZATION CODE endpoint
#@bp.route('/api/v1/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()
    # if user log status is not true (Auth server), then to log it in
    if not user:
        return redirect(url_for('oauth_login', next=request.url))
    if request.method == 'GET':
        try:
            grant = authorization.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            return error.error
        #return render_template('/oauth/authorize.html', user=user, grant=grant)
        profile_check = "checked" if "profile" in grant.request.scope else  "disabled"
        resume_check = "checked" if "profile" in grant.request.scope else "disabled"
        proof_of_identity_check = "checked" if "proof_of_identity" in grant.request.scope else "disabled"
        email_check = "checked" if "email" in grant.request.scope else "disabled"
        phone_check = "checked" if "phone" in grant.request.scope else "disabled"
        certificate_check = "checked" if "certificate" in grant.request.scope else "disabled"
        return render_template('/oauth/oauth_authorize.html', user=user,
                                                            grant=grant,
                                                            profile_check=profile_check,
                                                            resume_check=resume_check,
                                                            proof_of_identity_check=proof_of_identity_check,
                                                            email_check=email_check,
                                                            phone_check=phone_check,
                                                            certificate_check=certificate_check)
    # POST
    if not user and 'username' in request.form:
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
    if 'reject' in request.form :
        grant_user = None
        return authorization.create_authorization_response(grant_user=grant_user)
    # obtain query string as dictionary
    query_dict = parse_qs(request.query_string.decode("utf-8"))
    # customize scope for this request
    my_scope = ""
    for scope in ["profile", "email", "phone", "resume", "proof_of_identity"] :
        if request.form.get(scope) == "on" :
            my_scope = my_scope + scope + " "
    query_dict["scope"] = my_scope
    # We here setup a custom Oauth2Request as we have change the scope in the query_dict
    req = OAuth2Request("POST", request.base_url + "?" + urlencode(query_dict, doseq=True))
    return authorization.create_authorization_response(grant_user=user, request=req)


#  User Info Endpoint
#route('/api/v1/user_info')
@require_oauth('profile')
def user_info(mode):
    #client_id = current_token.client_id
    #client = OAuth2Client.query.filter_by(client_id=client_id).first().__dict__
    user_id = current_token.user_id
    user = User.query.get(user_id)
    #print ('client  metadata = ', client['_client_metadata'])
    #json_data = request.__dict__.get('data').decode("utf-8")
    #dict_data = json.loads(json_data)
    #print('data recu dans routes.py = ', json_data)
    username = user.username
    if username is None :
        workspace_contract = None
        print('something is wrong in userinfo')
        content=json.dumps({"msg" : "invalid username"}) # content est un json
        response = Response(content, status=401, mimetype='application/json')
        return response
    workspace_contract = ns.get_data_from_username(username, mode)['workspace_contract']
    user_info = dict()
    profile = read_profil(workspace_contract, mode, 'full')[0]
    user_info['sub'] = 'did:talao:' + mode.BLOCKCHAIN +':' + workspace_contract[2:]
    user_info['given_name'] = profile.get('firstname')
    user_info['family_name'] = profile.get('lastname')
    user_info['gender'] = profile.get('gender')
    if 'email' in current_token.scope :
        user_info['email']= profile.get('contact_email') if profile.get('contact_email') != 'private' else None
    if 'phone' in current_token.scope :
        user_info['phone']= profile.get('contact_phone') if profile.get('contact_phone') != 'private' else None
    if 'birthdate' in current_token.scope :
        user_info['birthdate'] = profile.get('birthdate') if profile.get('birthdate') != 'private' else None
    if 'certificate' in current_token.scope :
        user_info['certificate'] = True
        # issue a 20002 key
    if 'resume' in current_token.scope :
        user = Identity(workspace_contract, mode)
        user_dict = user.__dict__
        del user_dict['mode']
        del user_dict['partners']
        user_info['resume'] = user_dict 
    # preparation de la reponse
    content = json.dumps(user_info)
    response = Response(content, status=200, mimetype='application/json')
    return response


# Client credential endpoint

#@route('/api/v1/create')
@require_oauth(None)
def oauth_create(mode):
    # creation d'une identité"
    # status 900 : Ok
    # status 910 : Failed, client has no identity
    # status 920 : Failed, creation identity
    # status 930 : Failed, request incorrect
    client_id = current_token.client_id
    client = OAuth2Client.query.filter_by(client_id=client_id).first().__dict__
    client_metadata = json.loads(client['_client_metadata'])
    client_username = client_metadata['client_name']
    #user_id = current_token.user_id
    #user = User.query.get(user_id)
    #user_workspace_contract = ns.get_data_from_username(user.username, mode)['workspace_contract']
    json_data = request.__dict__.get('data').decode("utf-8")
    data = json.loads(json_data)
    client_workspace_contract = ns.get_data_from_username(client_username, mode).get('workspace_contract')
    if data.get('email') is None or data.get('firstname') is None or data.get('lastname')is None :
        response_dict = {'status' : '930','msg' : 'Incorect request', **data}
    # Test de la doc
    elif client_id == 'aslAD3wmxbEvybv3ntnZR0Tf' :
        response_dict = {'status' : '900','did' : 'did:talao:talaonet:__TEST__', **data}
    # le client n a pas d identite
    elif client_workspace_contract is None :
        response_dict = {'status' : '910','msg' : 'le client n a pas d identite', **data}
    # cas normal
    else :
        identity_username = ns.build_username(data.get('firstname'), data.get('lastname'), mode)
        client_address = Talao_token_transaction.contractsToOwners(client_workspace_contract, mode)
        identity_workspace_contract = createidentity.create_user(identity_username, data.get('email'), mode, creator=client_address)[2]
        # echec de createidentity
        if identity_workspace_contract is None :
            response_dict = {'status' : '920','msg' : 'echec creation identite', **data}
        else :
            response_dict = {'status' : '900','did' : 'did:talao:' + mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:], **data}
    content = json.dumps(response_dict)
    response = Response(content, status=200, mimetype='application/json')
    return response




""" exempled d'un client python

import requests
import json
import shutil


def send_dict() :
	headers = {'Content-Type': 'application/json',
				'Authorization': 'Bearer  K2jJkgpWFFS3PNXHbWLpyE2m7DcX9GejxEuDjhMExP'}
	data = {'name' : 'pierre', 'data' : 125}
	response = requests.post('http://127.0.0.1:3000/api/v1/api/me', data=json.dumps(data), headers=headers)
	return response.json()

print(send_dict())
"""