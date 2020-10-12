import time
from flask import request, session, url_for, Response, abort
from flask import render_template, redirect, jsonify
from werkzeug.security import gen_salt
from authlib.integrations.flask_oauth2 import current_token, client_authenticated
from authlib.oauth2 import OAuth2Error
from models import db, User, OAuth2Client
from oauth2 import authorization, require_oauth
import json


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


#@bp.route('/api/v1/logout')
def oauth_logout():
    check_login()
    del session['id']
    return redirect('/user')


#@bp.route('/api/v1/create_client', methods=('GET', 'POST'))
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


#@bp.route('/api/v1/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()
    # if user log status is not true (Auth server), then to log it in
    if not user:
        return redirect(url_for('website.routes.home', next=request.url))
    if request.method == 'GET':
        try:
            grant = authorization.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            return error.error
        return render_template('authorize.html', user=user, grant=grant)
    if not user and 'username' in request.form:
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
    if request.form['confirm']:
        grant_user = user
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)


#@bp.route('/api/v1/oauth/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()


#@bp.route('/api/v1/api/me')
@require_oauth('profile')
def api_me():
    client_id = current_token.client_id
    client = OAuth2Client.query.filter_by(client_id=client_id).first().__dict__
    print ('client  metadata = ', client['_client_metadata'])
    json_data = request.__dict__.get('data').decode("utf-8")
    dict_data = json.loads(json_data)
    print('data = ', json_data)

    # preparation de la reponse
    content = json.dumps({'User' : 'inconnu', 'msg' : "ok"})
    response = Response(content, status=200, mimetype='application/json')
    return response



#@bp.route('/api/v1/api/me2')
def api_me2():
    with require_oauth.acquire('profile') as token:
        return 'OK me2'
    return 'KO'


""" exempled d'un client

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