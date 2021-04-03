"""
pour l authentication cf https://realpython.com/token-based-authentication-with-flask/
pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization
interace wsgi https://www.bortzmeyer.org/wsgi.html
request : http://blog.luisrei.com/articles/flaskrest.html

"""
import os
from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
#from flask_fontawesome import FontAwesome
from datetime import timedelta, datetime
import json
import secrets
from Crypto.PublicKey import RSA
from authlib.jose import JsonWebEncryption
from urllib.parse import urlencode
from eth_account.messages import defunct_hash_message
import logging
logging.basicConfig(level=logging.INFO)

# dependances
from components import Talao_message, Talao_ipfs, hcode, ns, sms, directory, privatekey
import constante
from protocol import ownersToContracts, contractsToOwners, destroy_workspace, save_image, partnershiprequest, remove_partnership, token_balance
from protocol import Claim, File, Identity, Document, read_profil, get_data_from_token

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
#@app.route('/user/update_wallet/', methods = ['GET', 'POST'])
def update_wallet(mode) :
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
			flash('No identity found', 'danger')
			return redirect (mode.server +'user/')
		if ns.update_wallet(workspace_contract, wallet, mode) :
			if wallet :
				flash('Wallet updated ', 'success')
			else :
				flash('Wallet deleted', 'warning')
		else :
			flash('Update failed', 'danger')
		return redirect (mode.server +'user/')

# walletconnect login
#@app.route('/wc_login/', methods = ['GET', 'POST'])
def wc_login(mode) :
	if request.method == 'GET' :
		# call from JS, the wallet is in a wallectconnect session with the dapp
		# QRmodal rejected by user
		if not request.args.get('wallet_address') or request.args.get('wallet_address') == 'undefined' :
			flash('Scan QR code or log with password', 'warning')
			return redirect (mode.server + 'login/')
		# call from JS, wrong wallet data
		if not mode.w3.isAddress(request.args.get('wallet_address')) :
			flash('This account is not an Ethereum account.', 'warning')
			return render_template('./login/login.html')
		wallet_address = mode.w3.toChecksumAddress(request.args.get('wallet_address'))
		session['workspace_contract'] = ownersToContracts(wallet_address, mode)
		if not session['workspace_contract'] or session['workspace_contract'] == '0x0000000000000000000000000000000000000000':
			# This wallet address is not an Identity owner, lets check if it is an alias (mode workspace = wallet used only for login)
			session['username'] = ns.get_username_from_wallet(wallet_address, mode)
			if not session['username'] :
				# This wallet addresss is not an alias, lest rejest and propose a new registration
				return render_template('./login/wc_reject.html', wallet_address=wallet_address)
			else :
				logging.info('This wallet is an Alias')
				# This wallet is an alias, we look for the workspace_contract attached
				session['workspace_contract'] = ns.get_data_from_username(session['username'], mode)['workspace_contract']
		else :
			logging.info('This wallet is an Owner')
			session['username'] = ns.get_username_from_resolver(session['workspace_contract'], mode)
		# random code to check the wallet signature
		code = secrets.randbelow(99999)
		session['wallet_code'] = str(code)
		src = request.args.get('wallet_logo')
		wallet_name = request.args.get('wallet_name')
		if request.args.get('wallet_logo') == 'undefined' :
			logging.info('wallet name = %s', wallet_name)
			if wallet_name != 'undefined' :
				filename= wallet_name.replace(' ', '').lower()
				src = "/static/img/wallet/" + filename + ".png"
			else :
				src = ""
				wallet_name = ''
		return render_template('./login/wc_confirm.html',
								wallet_address=wallet_address,
								wallet_code=session['wallet_code'],
								wallet_code_hex= '0x' + bytes(str(code), 'utf-8').hex(),
								wallet_name = wallet_name,
								wallet_logo= src)

	if request.method == 'POST' :
		signature = request.form.get('wallet_signature')
		wallet_address = request.form.get('wallet_address')
		message_hash = defunct_hash_message(text=session['wallet_code'])
		try :
			signer = mode.w3.eth.account.recoverHash(message_hash, signature=signature)
		except :
			logging.warning('incorrect signature')
			flash('This account is an Identity but wallet signature is incorrect.', 'danger')
			return render_template('./login/login.html')
		if signer != wallet_address :
			logging.warning('incorrect signer')
			flash('This account is an Identity but wallet signature is incorrect.', 'danger')
			return render_template('./login/login.html')
		del session['wallet_code']
		return redirect(mode.server + 'user/')

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
		flash("Secret code sent by " + support, 'success')
		return render_template("./login/two_factor.html", **session['menu'], consign = session['two_factor']['consign'])
	if request.method == 'POST' :
		code = request.form['code']
		session['two_factor']['try_number'] += 1
		logging.info('code received = %s', code)
		# loop for incorrect code
		if code !=  session['two_factor']['code'] and datetime.now() < session['two_factor']['code_delay'] and session['two_factor']['try_number'] < 4 :
			if session['two_factor']['try_number'] == 2 :
				flash('This code is incorrect, 2 trials left', 'warning')
			if session['two_factor']['try_number'] == 3 :
				flash('This code is incorrect, 1 trial left', 'warning')
			return render_template("./login/two_factor.html", **session['menu'], consign=session['two_factor']['consign'])
		# exit to callback
		if code != session['two_factor']['code'] and datetime.now() < session['two_factor']['code_delay'] :
			two_factor = "True"
		elif datetime.now() > session['two_factor']['code_delay']  :
			two_factor = "False"
			flash("Code expired", "warning")
		elif session['two_factor']['try_number'] > 3 :
			two_factor = "False"
			flash("Too many trials (3 max)", "warning")
		callback = session['two_factor']['callback']
		del session['two_factor']
		return redirect (mode.server + callback + "?two_factor=" + two_factor)

def login_password():
	return render_template('./login/login_password.html')

def login(mode) :
	"""
	@app.route('login/', methods = ['GET', 'POST'])
	mode = mobile_on : we display the original (large) qrcode which provides a list of mobile apps for mobile devices
	mode = mobile_off_qrcode_on : qrcode only for desktop
	mode = password  : display password form
	mode = None : provide a dispaye with qrcode for desktop and password form for smartphone
	"""
	if request.method == 'GET' :
		session.clear()
		#if request.args.get('mode') == 'mobile_on':
		#	logging.info('large QR code for mobile or desktop')
		#	return render_template('./login/login_mobile.html')
		#elif request.args.get('mode') == 'password':
		#	logging.info('password form')
		return render_template('./login/login_password.html')
		#elif request.args.get('mode') == 'mobile_off_qrcode_on' :
		#	logging.info('small QR code for desktop')
		#	return render_template('./login/login_qrcode.html', username=request.args.get('username', ""))
		#else :
		#	logging.info('qrcode for desktop and password for mobile')
		#	return render_template('./login/login.html', username=request.args.get('username', ""))

	if request.method == 'POST' :
		if not session.get('try_number')  :
			session['try_number'] = 1
		session['username_to_log'] = request.form['username']
		if not ns.username_exist(session['username_to_log'], mode)  :
			logging.warning('username does not exist')
			flash('Username not found', "warning")
			session['try_number'] = 1
			return render_template('./login/login.html', username="")

		if not ns.check_password(session['username_to_log'], request.form['password'], mode)  :
			logging.warning('wrong secret code')
			if session['try_number'] == 1 :
				flash('This password is incorrect, 2 trials left', 'warning')
				session['try_number'] += 1
				return render_template('./login/login_password.html', username=session['username_to_log'])

			if session['try_number'] == 2 :
				flash('This password is incorrect, 1 trials left', 'warning')
				session['try_number'] += 1
				return render_template('./login/login_password.html', username=session['username_to_log'])

			flash("Too many trials (3 max)", "warning")
			session['try_number'] = 1
			return render_template('./login/login.html', username="")
		else :
			# secret code to send by email or sms
			session['code'] = str(secrets.randbelow(99999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 180)
			# send code by sms if phone exist else email
			try : 
				session['support'] = send_secret_code(session['username_to_log'], session['code'],mode)
				logging.info('secret code sent = %s', session['code'])
				flash("Secret code sent by " + session['support'], 'success')
				session['try_number'] = 1
			except :
				flash("Connexion problem", 'danger')
				return render_template('./login/login.html', username="")
			return render_template("./login/authentification.html", support=session['support'])


def login_authentification(mode) :
	"""
	verify code from user
	@app.route('/login/authentification/', methods = ['POST'])
	"""
	if not session.get('username_to_log') or not session.get('code') :
		flash("Authentification expired", "warning")
		return render_template('./login/login_password.html')
	code = request.form['code']
	session['try_number'] +=1
	logging.info('code received = %s', code)
	if code == session['code'] and datetime.now() < session['code_delay'] :
		session['username'] = session['username_to_log']
		del session['username_to_log']
		del session['try_number']
		del session['code']
		del session['support']
		return redirect(mode.server + 'user/')
	elif session['code_delay'] < datetime.now() :
		flash("Code expired", "warning")
		return render_template('./login/login_password.html')
	elif session['try_number'] > 3 :
		flash("Too many trials (3 max)", "warning")
		return render_template('./login/login_password.html')
	else :
		if session['try_number'] == 2 :
			flash('This code is incorrect, 2 trials left', 'warning')
		if session['try_number'] == 3 :
			flash('This code is incorrect, 1 trial left', 'warning')
		return render_template("./login/authentification.html", support=session['support'])


def logout(mode) :
	"""
	@app.route('/logout/', methods = ['GET'])
	delete picture, signateure and files before logout, clear session.
	"""
	check_login()
	if request.method == 'GET' :
		return render_template('./login/logout.html')
	try :
		os.remove(mode.uploads_path + session['picture'])
		os.remove(mode.uploads_path + session['signature'])
	except :
		logging.warning('delet picture and signature failed')
	for one_file in session['identity_file'] :
		try :
			os.remove(mode.uploads_path + one_file['filename'])
		except :
			logging.warning('delete file failed')
	session.clear()
	flash('Thank you for your visit', 'success')
	return redirect (mode.server + 'login/')


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
			flash('There is no Identity with this Email' , 'warning')
		else :
			flash('This Email is already used by Identities : ' + ", ".join(username_list) , 'success')
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
			flash("Username not found", "warning")
			return render_template('./login/login.html')
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
			flash("You are going to receive an email to renew your password.", "success")
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
			flash ('Incorrect data', 'danger')
			logging.warning('JWE did not decrypt')
			return render_template('./login/login_password.html')
		payload = json.loads(data['payload'].decode('utf-8'))
		if payload['expired'] < datetime.timestamp(datetime.now()) :
			flash ('Delay expired (3 minutes maximum)', 'danger')
			return render_template('./login/login_password.html')
		session['email_password'] = payload['email']
		session['username_password'] = payload['username']
		return render_template('./login/update_password_external.html')
	if request.method == 'POST' :
		if session['email_password'] != request.form['email'] :
			flash('Incorrect email', 'danger')
			return render_template('./login/update_password_external.html')
		ns.update_password(session['username_password'], request.form['password'], mode)
		flash('Password updated', "success")
		del session['email_password']
		del session['username_password']
		return render_template('./login/login_password.html')
