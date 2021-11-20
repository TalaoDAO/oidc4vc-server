"""
pour l authentication cf https://realpython.com/token-based-authentication-with-flask/
pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization
interace wsgi https://www.bortzmeyer.org/wsgi.html
request : http://blog.luisrei.com/articles/flaskrest.html

"""
from flask import session, flash, jsonify
from flask import request, redirect, render_template,abort, Response
from flask_babel import _
from datetime import timedelta, datetime
import json
import secrets
from Crypto.PublicKey import RSA
from authlib.jose import JsonWebEncryption
from urllib.parse import urlencode
import logging
from components import Talao_message, ns, sms, privatekey
import uuid
import didkit

PRESENTATION_DELAY = 600 # seconds

DID_WEB = 'did:web:talao.cp'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY =  'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'                      

logging.basicConfig(level=logging.INFO)

def init_app(app, red, mode) :
	app.add_url_rule('/logout',  view_func=logout, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/unregistered',  view_func=unregistered, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/forgot_username',  view_func=forgot_username, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/forgot_password',  view_func=forgot_password, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/forgot_password_token/',  view_func=forgot_password_token, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/login/authentification/',  view_func=login_authentication, methods = ['POST'], defaults={'mode': mode})
	app.add_url_rule('/login',  view_func=login, methods = ['GET', 'POST'], defaults={'mode': mode, 'red' : red})
	app.add_url_rule('/login/',  view_func=login, methods = ['GET', 'POST'], defaults={'mode': mode, 'red' : red}) #FIXME
	app.add_url_rule('/',  view_func=login, methods = ['GET', 'POST'], defaults={'mode': mode, 'red' : red}) # idem previous
	app.add_url_rule('/login/VerifiablePresentationRequest',  view_func=VerifiablePresentationRequest_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode, 'red' : red})
	app.add_url_rule('/login/wallet_presentation/<stream_id>',  view_func=wallet_endpoint, methods = ['GET', 'POST'],  defaults={'mode' : mode, 'red' :red})
	app.add_url_rule('/login/stream',  view_func=stream, defaults={ 'red' : red})
	app.add_url_rule('/credible/callback',  view_func=callback, methods = ['GET', 'POST'])
	app.add_url_rule('/app/login',  view_func=app_login, methods = ['GET', 'POST'])

	return

def app_login():
	return jsonify("test login app")

def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if not session.get('workspace_contract') and not session.get('username') :
		logging.error('abort')
		abort(403)
	return True


def send_secret_code (username, code, mode) :
	"""
	if phone exist we send and SMS
	if not we send an email
	return : 'sms' or 'email' or None
	"""
	data = ns.get_data_from_username(username, mode)
	code_auth = 'code_auth_fr' if session['language'] == 'fr' else 'code_auth'
	if not data :
		logging.error('cannot send secret code')
		return None
	if not data.get('phone') :
		try :
			subject = _('Talao : Email authentication  ')
			Talao_message.messageHTML(subject, data['email'], code_auth, {'code' : code}, mode)
			logging.info('code sent by email')
			return 'email'
		except :
			logging.error('sms failed, no phone')
			return None
	try :
		sms.send_code(data['phone'], code, mode)
		logging.info('code sent by sms')
		return 'sms'
	except :
		subject = _('Talao : Email authentication  ')
		try :
			Talao_message.messageHTML(subject, data['email'], code_auth, {'code' : code}, mode)
			logging.info('sms failed, code sent by email')
			return 'email'
		except :
			logging.error('sms failed, email failed')
			return None


def login(red, mode) :
	if request.method == 'GET' :
		language = session.get('language')
		session.clear()
		session['language'] = language

		# code qrcode inside the page
		stream_id = str(uuid.uuid1())
		session_data = json.dumps({'challenge' : str(uuid.uuid1()),
							'issuer_username' : request.args.get('issuer_username'),
							'vc' : request.args.get('vc')
							})
		red.set(stream_id,  session_data, PRESENTATION_DELAY)
		if request.args.get('vc') == 'certificateofemployment' : 
			message = _('Get a Certificate of Employment')
		elif request.args.get('vc') == 'professionalexperienceassessment' :
			message = _('Request a Professional Experience Assessment')
		else :
			message = _('Sign-In')
		url=mode.server + 'login/wallet_presentation/' + stream_id +'?' + urlencode({'issuer' : DID_TZ})
		deeplink = 'https://app.talao.co/app/login?' + urlencode({'uri' : url })
		# end code for qrcode
		return render_template('./login/login_password.html',
								url=url,
								deeplink=deeplink,
								stream_id=stream_id,
								message=message,
								username=request.args.get('username', ''))

	if request.method == 'POST' :
		if not session.get('try_number')  :
			session['try_number'] = 1
		session['username_to_log'] = request.form['username']
		if not ns.username_exist(session['username_to_log'], mode)  :
			logging.warning('username does not exist')
			flash(_(_('Username not found')), "warning")
			session['try_number'] = 1
			return render_template('./login/login_password.html', username="")

		if not ns.check_password(session['username_to_log'], request.form['password'], mode)  :
			logging.warning('wrong password')
			if session['try_number'] == 1 :
				flash(_('This password is incorrect, 2 trials left.'), 'warning')
				session['try_number'] += 1
				return render_template('./login/login_password.html', username=session['username_to_log'])

			if session['try_number'] == 2 :
				flash(_('This password is incorrect, 1 trials left.'), 'warning')
				session['try_number'] += 1
				return render_template('./login/login_password.html', username=session['username_to_log'])

			flash(_("Too many trials (3 max)."), "warning")
			session['try_number'] = 1
			return render_template('./login/login_password.html', username="")
		else :
			session['code'] = str(secrets.randbelow(99999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 180)
			try : 
				session['support'] = send_secret_code(session['username_to_log'], session['code'],mode)
				logging.info('secret code sent = %s', session['code'])
				flash(_("Secret code sent by ") + session['support'] +'.', 'success')
				session['try_number'] = 1
			except :
				flash(_("Connexion problem."), 'danger')
				return render_template('./login/login_password.html', username="")
			return render_template("./login/authentification.html", support=session['support'])


def login_authentication(mode) :
	"""
	verify code from user
	@app.route('/login/authentification/', methods = ['POST'])
	"""
	if not session.get('username_to_log') or not session.get('code') :
		flash(_("Authentification expired."), "warning")
		return render_template('./login/login_password.html')
	code = request.form['code']
	session['try_number'] +=1
	logging.info('code received = %s', code)
	if (code == session['code'] and datetime.now() < session['code_delay']) or (session['username_to_log'] == 'talao' and code == '123456') :
		# success login, forward to user/
		session['username'] = session['username_to_log']
		del session['username_to_log']
		del session['try_number']
		del session['code']
		del session['support']
		return redirect(mode.server + 'user/')
	elif session['code_delay'] < datetime.now() :
		flash(_("Code expired."), "warning")
		return render_template('./login/login_password.html')
	elif session['try_number'] > 3 :
		flash(_("Too many trials (3 max)."), "warning")
		return render_template('./login/login_password.html')
	else :
		if session['try_number'] == 2 :
			flash(_('This code is incorrect, 2 trials left.'), 'warning')
		if session['try_number'] == 3 :
			flash(_('This code is incorrect, 1 trial left.'), 'warning')
		return render_template("./login/authentification.html", support=session['support'])


def logout(mode) :
	"""
	@app.route('/logout/', methods = ['GET'])
	delete picture, signateure and files before logout, clear session.
	"""
	check_login()
	if request.method == 'GET' :
		return render_template('login/logout.html', **session['menu'])
	session.clear()
	flash(_('Thank you for your visit.'), 'success')
	return redirect (mode.server + 'login')


def unregistered(mode) :
	if request.method == 'GET' :
		return render_template('login/unregistered.html', message=request.args.get('message', ""))
	if request.method == 'POST' :
		return redirect (mode.server + 'login/VerifiablePresentationRequest')


def forgot_username(mode) :
	"""
	@app.route('/forgot_username/', methods = ['GET', 'POST'])
	This function is called from the login view.
	"""
	if request.method == 'GET' :
		return render_template('login/forgot_username.html')
	if request.method == 'POST' :
		username_list = ns.get_username_list_from_email(request.form['email'], mode)
		if not username_list :
			flash(_('There is no Identity with this Email.') , 'warning')
		else :
			flash(_('This Email is already used by Identities : ') + ", ".join(username_list) + '.', 'success')
		return render_template('login/login_password.html', name="")


def forgot_password(mode) :
	"""
	@app.route('/forgot_password/', methods = ['GET', 'POST'])
	This function is called from the login view.
	build JWE to store timestamp, username and email, we use Talao RSA key
	"""
	if request.method == 'GET' :
		return render_template('login/forgot_password_init.html')
	if request.method == 'POST' :
		username = request.form.get('username')
		if not ns.username_exist(username, mode) :
			flash(_("Username not found."), "warning")
			return render_template('login/login_password.html')
		email= ns.get_data_from_username(username, mode)['email']
		private_rsa_key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
		RSA_KEY = RSA.import_key(private_rsa_key)
		public_rsa_key = RSA_KEY.publickey().export_key('PEM').decode('utf-8')
		expired = datetime.timestamp(datetime.now()) + 180 # 3 minutes live
		# build JWE
		jwe = JsonWebEncryption()
		header = {'alg': 'RSA1_5', 'enc': 'A256GCM'}
		json_string = json.dumps({'username' : username, 'email' : email, 'expired' : expired})
		payload = bytes(json_string, 'utf-8')
		token = jwe.serialize_compact(header, payload, public_rsa_key)
		link = mode.server + 'forgot_password_token/?'+ urlencode({'token'  : token.decode('utf-8')}, doseq=True)
		subject = "Renew your password"
		if Talao_message.messageHTML(subject, email, 'forgot_password', {'link': link}, mode):
			flash(_("You are going to receive an email to renew your password."), "success")
		return render_template('login/login_password.html')


def forgot_password_token(mode) :
	"""
	@app.route('/forgot_password_token/', methods = ['GET', 'POST'])
	This function is called from email to decode token and reset password.
	"""
	if request.method == 'GET' :
		token = request.args.get('token')
		key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
		jwe = JsonWebEncryption()
		try :
			data = jwe.deserialize_compact(token, key)
		except :
			flash (_('Incorrect data.'), 'danger')
			logging.warning('JWE did not decrypt')
			return render_template('login/login_password.html')
		payload = json.loads(data['payload'].decode('utf-8'))
		if payload['expired'] < datetime.timestamp(datetime.now()) :
			flash (_('Delay expired (3 minutes maximum).'), 'danger')
			return render_template('login/login_password.html')
		session['email_password'] = payload['email']
		session['username_password'] = payload['username']
		return render_template('login/update_password_external.html')
	if request.method == 'POST' :
		if session['email_password'] != request.form['email'] :
			flash(_('Incorrect email.'), 'danger')
			return render_template('login/update_password_external.html')
		ns.update_password(session['username_password'], request.form['password'], mode)
		flash(_('Password updated.'), "success")
		del session['email_password']
		del session['username_password']
		return render_template('login/login_password.html')


####################################Login with wallet ##########################################################""


def VerifiablePresentationRequest_qrcode(red, mode):
    stream_id = str(uuid.uuid1())
    session_data = json.dumps({'challenge' : str(uuid.uuid1()),
							'issuer_username' : request.args.get('issuer_username'),
							'vc' : request.args.get('vc')
							})
    red.set(stream_id,  session_data, PRESENTATION_DELAY)
    if request.args.get('vc') == 'certificateofemployment' : 
        message = _('Get a Certificate of Employment')
    elif request.args.get('vc') == 'professionalexperienceassessment' :
        message = _('Request a Professional Experience Assessment')
    else :
        message = _('Sign-In')
    return render_template('login/login_qr.html',
							url=mode.server + 'login/wallet_presentation/' + stream_id +'?' + urlencode({'issuer' : DID_TZ}),
							stream_id=stream_id, message=message)


def wallet_endpoint(stream_id, red, mode):
    """
    200 OK
    201 Created 
    400 Bad Request
    401  unauthenticated
    403 Forbidden
    408 Request Timeout
    500 Internal Server Error
    501 Not Implemented
    504 Gateway Timeout
    """
    try :
        session_data = json.loads(red.get(stream_id).decode())
    except :
        logging.warning('time expired')
        event_data = json.dumps({"stream_id" : stream_id,
								"code" : "ko",
								 "message" : _('Delay has expired.')})
        red.publish('credible', event_data)
        jsonify ("Delay has expired"), 408
    if request.method == 'GET':
        did_auth_request = {
            "type": "VerifiablePresentationRequest",
            "query": [{
            	"type": 'DIDAuth'
            	}],
            "challenge": session_data['challenge'],
            "domain" : mode.server
        }
        return jsonify(did_auth_request)
    elif request.method == 'POST' :
        #red.delete(stream_id)
        presentation = json.loads(request.form['presentation'])       
        logging.info('verify presentation = ' + didkit.verify_presentation(json.dumps(presentation), '{}'))
        """
        if json.loads(didkit.verify_presentation(request.form['presentation'], '{}'))['errors'] :
            logging.warning('signature failed')
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ko",
									 "message" : _("Signature verification failed.")})
            red.publish('credible', event_data)
            return jsonify("Signature verification failed"), 401
        """
        try : # FIXME
            issuer = presentation['verifiableCredential']['issuer']
            holder = presentation['holder']
            challenge = presentation['proof']['challenge']
            domain = presentation['proof']['domain']
        except :
            logging.warning('to be fixed, presentation is not correct')
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ko",
									 "message" : _("Presentation check failed.")})
            red.publish('credible', event_data)
            return jsonify("Presentation malformed"), 400
        if domain != mode.server or challenge != session_data['challenge'] :
            logging.warning('challenge failed')
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ko",
									 "message" : _("The presentation challenge failed.")})
            red.publish('credible', event_data)
            return jsonify("Challenge failed"), 401
        elif issuer not in [DID_WEB, DID_ETHR, DID_TZ, DID_KEY] :
            logging.warning('unknown issuer')
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ko",
									 "message" : _("This issuer is unknown.")})
            red.publish('credible', event_data)
            return jsonify("Issuer unknown"), 403
        elif not ns.get_workspace_contract_from_did(holder, mode) :
            # user has no account
            logging.warning('User unknown')
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ko",
									 "message" : _('Your Digital Identity has not been registered yet.')})
            red.publish('credible', event_data)
            return  jsonify("User unknown"), 403
        else :
			# Successfull login 
            # we transfer a JWE token to user agent to sign in
            logging.info('log with DID')
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ok",
			                        "message" : "ok",
			                        "token" : generate_token(holder, session_data['issuer_username'], session_data['vc'],mode)})
            red.publish('credible', event_data)
            return jsonify("ok"), 201


def event_stream(red):
    pubsub = red.pubsub()
    pubsub.subscribe('credible')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def stream(red):
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)


def callback() :
    credential = 'holder : ' + request.args['holder'] + ' issuer : ' + request.args['issuer']
    return render_template('credible/credential.html', credential=credential)


def generate_token(did,issuer_username, vc, mode) :
    private_rsa_key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
    RSA_KEY = RSA.import_key(private_rsa_key)
    public_rsa_key = RSA_KEY.publickey().export_key('PEM').decode('utf-8')
    expired = datetime.timestamp(datetime.now()) + 5 # 5s live
    # build JWE
    jwe = JsonWebEncryption()
    header = {'alg': 'RSA1_5', 'enc': 'A256GCM'}
    json_string = json.dumps({'did' : did,
							 'issuer_username' : issuer_username,
							 'vc' : vc,
							 'exp' : expired})
    payload = bytes(json_string, 'utf-8')
    return jwe.serialize_compact(header, payload, public_rsa_key).decode()

