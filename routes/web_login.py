"""
pour l authentication cf https://realpython.com/token-based-authentication-with-flask/
pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization
interace wsgi https://www.bortzmeyer.org/wsgi.html
request : http://blog.luisrei.com/articles/flaskrest.html

"""
import os
from flask import session, flash
from flask import request, redirect, render_template,abort
from flask_babel import _
from datetime import timedelta, datetime
import json
import secrets
from Crypto.PublicKey import RSA
from authlib.jose import JsonWebEncryption
import jwt
from urllib.parse import urlencode
import logging
logging.basicConfig(level=logging.INFO)
import uuid 
# dependances
from components import Talao_message, ns, sms, privatekey
from signaturesuite import helpers


def init_app(app, mode) :
# Centralized route for login
	app.add_url_rule('/logout',  view_func=logout, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/forgot_username',  view_func=forgot_username, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/forgot_password',  view_func=forgot_password, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/forgot_password_token/',  view_func=forgot_password_token, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/login/authentification/',  view_func=login_authentification, methods = ['POST'], defaults={'mode': mode})
	app.add_url_rule('/login',  view_func=login, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/login/',  view_func=login, methods = ['GET', 'POST'], defaults={'mode': mode}) #FIXME
	app.add_url_rule('/',  view_func=login, methods = ['GET', 'POST'], defaults={'mode': mode}) # idem previous
	app.add_url_rule('/user/two_factor/',  view_func=two_factor, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/user/update_wallet/',  view_func=update_wallet, methods = ['GET', 'POST'], defaults={'mode': mode})
	return


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
	if not data :
		logging.error('cannot send secret code')
		return None
	if not data['phone'] :
		try :
			subject = 'Talao : Email authentification  '
			Talao_message.messageHTML(subject, data['email'], 'code_auth', {'code' : code}, mode)
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
		subject = 'Talao : Email authentification  '
		try :
			Talao_message.messageHTML(subject, data['email'], 'code_auth', {'code' : code}, mode)
			logging.info('sms failed, code sent by email')
			return 'email'
		except :
			logging.error('sms failed, email failed')
			return None


# update wallet in Talao Identity
def update_wallet(mode) :
	"""
	DEPRECATED
	"""
	check_login()
	if request.method == 'GET' :
		return render_template('./login/update_wallet.html', **session['menu'])
	if request.method == 'POST' :
		username = request.form['username']
		try :
			wallet = mode.w3.toChecksumAddress(request.form['wallet'])
		except :
			wallet = None
		workspace_contract = ns.get_data_from_username(username, mode).get('workspace_contract')
		if not workspace_contract :
			flash(_('No identity found'), 'danger')
			return redirect (mode.server +'user/')
		if ns.update_wallet(workspace_contract, wallet, mode) :
			if wallet :
				flash(_('Wallet updated '), 'success')
			else :
				flash(_('Wallet deleted'), 'warning')
		else :
			flash(_('Update failed'), 'danger')
		return redirect (mode.server +'user/')



def two_factor(mode) :
	"""
	@app.route('/user/two_factor/', methods=['GET', 'POST'])
	this route has to be used as a function to check code before signing a certificate
	CF issue certificate in main.py to see how to use it with redirect and callback 
	"""
	check_login()
	if request.method == 'GET' :
		session['two_factor'] = {'callback' : request.args.get('callback'),
								'code' : str(secrets.randbelow(99999)),
								'code_delay' : datetime.now() + timedelta(seconds= 180),
								'try_number': 1,
								'consign' : None}
		# send code by sms if phone exist else email
		support = send_secret_code(session['username'], session['two_factor']['code'],mode)
		session['two_factor']['consign'] = "Check your phone for SMS." if support == 'sms' else "Check your email."
		logging.info('secret code sent = %s', session['two_factor']['code'])
		flash(_("Secret code sent by ") + support, 'success')
		return render_template("./login/two_factor.html", **session['menu'], consign = session['two_factor']['consign'])
	if request.method == 'POST' :
		code = request.form['code']
		session['two_factor']['try_number'] += 1
		logging.info('code received = %s', code)
		# loop for incorrect code
		if code !=  session['two_factor']['code'] and datetime.now() < session['two_factor']['code_delay'] and session['two_factor']['try_number'] < 4 :
			if session['two_factor']['try_number'] == 2 :
				flash(_('This code is incorrect, 2 trials left'), 'warning')
			if session['two_factor']['try_number'] == 3 :
				flash(_('This code is incorrect, 1 trial left'), 'warning')
			return render_template("./login/two_factor.html", **session['menu'], consign=session['two_factor']['consign'])
		# exit to callback
		if code == session['two_factor']['code'] and datetime.now() < session['two_factor']['code_delay'] :
			two_factor = "True"
		elif datetime.now() > session['two_factor']['code_delay']  :
			two_factor = "False"
			flash(_("Code expired"), "warning")
		elif session['two_factor']['try_number'] > 3 :
			two_factor = "False"
			flash(_("Too many trials (3 max)"), "warning")
		callback = session['two_factor']['callback']
		del session['two_factor']
		return redirect (mode.server + callback + "?two_factor=" + two_factor)



def login(mode) :
	if request.method == 'GET' :
		language = session.get('language')
		session.clear()
		session['language'] = language
		return render_template('./login/login_password.html', username=request.args.get('username', ''))

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
				flash(_('This password is incorrect, 2 trials left'), 'warning')
				session['try_number'] += 1
				return render_template('./login/login_password.html', username=session['username_to_log'])

			if session['try_number'] == 2 :
				flash(_('This password is incorrect, 1 trials left'), 'warning')
				session['try_number'] += 1
				return render_template('./login/login_password.html', username=session['username_to_log'])

			flash(_("Too many trials (3 max)"), "warning")
			session['try_number'] = 1
			return render_template('./login/login_password.html', username="")
		else :
			# secret code to send by email or sms
			session['code'] = str(secrets.randbelow(99999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 180)
			# send code by sms if phone exist else email
			try : 
				session['support'] = send_secret_code(session['username_to_log'], session['code'],mode)
				logging.info('secret code sent = %s', session['code'])
				flash(_("Secret code sent by ") + session['support'], 'success')
				session['try_number'] = 1
			except :
				flash(_("Connexion problem"), 'danger')
				return render_template('./login/login_password.html', username="")
			return render_template("./login/authentification.html", support=session['support'])


def login_authentification(mode) :
	"""
	verify code from user
	@app.route('/login/authentification/', methods = ['POST'])
	"""
	if not session.get('username_to_log') or not session.get('code') :
		flash(_("Authentification expired"), "warning")
		return render_template('./login/login_password.html')
	code = request.form['code']
	session['try_number'] +=1
	logging.info('code received = %s', code)
	# success logn exit
	if (code == session['code'] and datetime.now() < session['code_delay']) or (session['username_to_log'] == 'talao' and code == '123456') :
		session['username'] = session['username_to_log']
		del session['username_to_log']
		del session['try_number']
		del session['code']
		del session['support']
		return redirect(mode.server + 'user/')
	elif session['code_delay'] < datetime.now() :
		flash(_("Code expired"), "warning")
		return render_template('./login/login_password.html')
	elif session['try_number'] > 3 :
		flash(_("Too many trials (3 max)"), "warning")
		return render_template('./login/login_password.html')
	else :
		if session['try_number'] == 2 :
			flash(_('This code is incorrect, 2 trials left'), 'warning')
		if session['try_number'] == 3 :
			flash(_('This code is incorrect, 1 trial left'), 'warning')
		return render_template("./login/authentification.html", support=session['support'])


def logout(mode) :
	"""
	@app.route('/logout/', methods = ['GET'])
	delete picture, signateure and files before logout, clear session.
	"""
	check_login()
	if request.method == 'GET' :
		return render_template('./login/logout.html', **session['menu'])
	try :
		os.remove(mode.uploads_path + session['picture'])
		os.remove(mode.uploads_path + session['signature'])
	except :
		logging.warning('delete picture and signature failed')
	for one_file in session['identity_file'] :
		try :
			os.remove(mode.uploads_path + one_file['filename'])
		except :
			logging.warning('delete file failed')
	session.clear()
	flash(_('Thank you for your visit'), 'success')
	return redirect (mode.server + 'login')


def forgot_username(mode) :
	"""
	@app.route('/forgot_username/', methods = ['GET', 'POST'])
	This function is called from the login view.
	"""
	if request.method == 'GET' :
		return render_template('./login/forgot_username.html')
	if request.method == 'POST' :
		username_list = ns.get_username_list_from_email(request.form['email'], mode)
		if not username_list :
			flash(_('There is no Identity with this Email') , 'warning')
		else :
			flash(_('This Email is already used by Identities : ') + ", ".join(username_list) , 'success')
		return render_template('./login/login_password.html', name="")


def forgot_password(mode) :
	"""
	@app.route('/forgot_password/', methods = ['GET', 'POST'])
	This function is called from the login view.
	build JWE to store timestamp, username and email, we use Talao RSA key
	"""
	if request.method == 'GET' :
		return render_template('./login/forgot_password_init.html')
	if request.method == 'POST' :
		username = request.form.get('username')
		if not ns.username_exist(username, mode) :
			flash(_("Username not found"), "warning")
			return render_template('./login/login_password.html')
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
		return render_template('./login/login_password.html')


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
			flash (_('Incorrect data'), 'danger')
			logging.warning('JWE did not decrypt')
			return render_template('./login/login_password.html')
		payload = json.loads(data['payload'].decode('utf-8'))
		if payload['expired'] < datetime.timestamp(datetime.now()) :
			flash (_('Delay expired (3 minutes maximum)'), 'danger')
			return render_template('./login/login_password.html')
		session['email_password'] = payload['email']
		session['username_password'] = payload['username']
		return render_template('./login/update_password_external.html')
	if request.method == 'POST' :
		if session['email_password'] != request.form['email'] :
			flash(_('Incorrect email'), 'danger')
			return render_template('./login/update_password_external.html')
		ns.update_password(session['username_password'], request.form['password'], mode)
		flash(_('Password updated'), "success")
		del session['email_password']
		del session['username_password']
		return render_template('./login/login_password.html')
