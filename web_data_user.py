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
from flask_fontawesome import FontAwesome
from datetime import timedelta, datetime
import time
import json
import random
from Crypto.PublicKey import RSA
from authlib.jose import JsonWebEncryption
from urllib.parse import urlencode
from eth_account.messages import defunct_hash_message

# dependances
import Talao_message
import Talao_ipfs
import constante
from protocol import ownersToContracts, contractsToOwners, destroy_workspace, save_image, partnershiprequest, remove_partnership, token_balance
from protocol import Claim, File, Identity, Document, read_profil, get_data_from_token
import hcode
import ns
import sms
import vpi
import directory
import privatekey

def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if session.get('username') is None :
		abort(403)
	else :
		return session['username']


def send_secret_code (username, code, mode) :
	data = ns.get_data_from_username(username, mode)
	if data == dict() :
		return None
	if not data['phone'] :
		subject = 'Talao : Email authentification  '
		Talao_message.messageHTML(subject, data['email'], 'code_auth', {'code' : code}, mode)
		print('Warning : code sent by email')
		return 'email'
	else :
		print('Warning : code sent by sms')
		sms.send_code(data['phone'], code, mode)
	return 'sms'


# Starter with 3 options, login and logout
#@app.route('/starter/', methods = ['GET', 'POST'])
def starter(mode) :
		if request.method == 'GET' :
			return render_template('starter.html')
		else :
			start = request.form['start']
			if start == 'user' :
				return redirect(mode.server + 'login/')
			elif start == 'quick' :
				return redirect(mode.server + 'register/')
			else :
				return redirect(mode.server + 'starter/') # tobe done

# update wallet in Talao Identity
#@app.route('/user/update_wallet/', methods = ['GET', 'POST'])
def update_wallet(mode) :
	check_login()
	if request.method == 'GET' :
		return render_template('update_wallet.html', **session['menu'])
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
		# call from JS, QRmodal rejected by user
		if not request.args.get('wallet_address') or request.args.get('wallet_address') == 'undefined' :
			flash('Scan QR code or log with password', 'warning')
			return redirect (mode.server + 'login/')
		session['wallet_address'] = mode.w3.toChecksumAddress(request.args.get('wallet_address'))
		workspace_contract = ownersToContracts(session['wallet_address'], mode)
		if not workspace_contract :
			# This wallet address is not an Identity owner, lets t see if this wallet address is an alias of an Identiti
			session['wallet_username'] = ns.get_username_from_wallet(session['wallet_address'], mode)
			if not session['wallet_username'] :
				# This wallet addresss is not an alias
				return render_template('wc_reject.html', wallet_address=session['wallet_address'])
		else :
			# this wallet addrress is an identity owner
			session['wallet_username'] = ns.get_username_from_resolver(workspace_contract, mode)
			if not session['wallet_username'] :
				return render_template('wc_reject.html', wallet_address=session['wallet_address'])
		code = random.randint(10000, 99999)
		session['wallet_code'] = str(code)
		src = request.args.get('wallet_logo')
		if request.args.get('wallet_logo') == 'undefined' :
			filename= request.args.get('wallet_name').replace(' ', '').lower()
			src = "/static/img/wallet/" + filename + ".png"
		return render_template('wc_confirm.html', 
								wallet_address=session['wallet_address'],
								wallet_code=session['wallet_code'],
								wallet_code_hex= '0x' + bytes(str(code), 'utf-8').hex(),
								wallet_name = request.args.get('wallet_name'),
								wallet_logo= src)

	if request.method == 'POST' :
		signature = request.form.get('wallet_signature')
		message_hash = defunct_hash_message(text=session['wallet_code'])
		try :
			signer = mode.w3.eth.account.recoverHash(message_hash, signature=signature)
		except :
			print('Warning : incorrect signature')
			flash('Incorrect wallet signature. This wallet does not sign correctly personal messages.', 'danger')
			return render_template('login.html')
		if signer != session['wallet_address'] :
			print('Warning : incorrect signature')
			flash('Incorrect wallet signature. This wallet does not sign correctly personal messages.', 'danger')
			return render_template('login.html')
		session['username'] = session['wallet_username']
		return redirect(mode.server + 'user/')


# two factor checking function
#@app.route('/user/two_factor/', methods=['GET', 'POST'])
""" this route has to be used as a function to check code before signing a certificate
CF issue certificate in main.py to see how to use it with redirect and callback """
def two_factor(mode) :
	check_login()
	if request.method == 'GET' :
		session['two_factor'] = {'callback' : request.args.get('callback'),
								'code' : str(random.randint(10000, 99999)),
								'code_delay' : datetime.now() + timedelta(seconds= 180),
								'try_number': 1,
								'consign' : None}
		# send code by sms if phone exist else email
		support = send_secret_code(session['username'], session['two_factor']['code'],mode)
		session['two_factor']['consign'] = "Check your phone for SMS." if support == 'sms' else "Check your email."
		print('Info : secret code sent = ', session['two_factor']['code'], 'by ', support)
		flash("Secret code sent by " + support, 'success')
		return render_template("two_factor.html", **session['menu'], consign = session['two_factor']['consign'])
	if request.method == 'POST' :
		code = request.form['code']
		session['two_factor']['try_number'] += 1
		print('Warning : code received = ', code)
		authorized_codes = [session['two_factor']['code'], '123456'] if mode.test else [session['two_factor']['code']]
		# loop for incorrect code
		if code not in authorized_codes and datetime.now() < session['two_factor']['code_delay'] and session['two_factor']['try_number'] < 4 :
			if session['two_factor']['try_number'] == 2 :
				flash('This code is incorrect, 2 trials left', 'warning')
			if session['two_factor']['try_number'] == 3 :
				flash('This code is incorrect, 1 trial left', 'warning')
			return render_template("two_factor.html", **session['menu'], consign=session['two_factor']['consign'])
		# exit to callback
		if code in authorized_codes and datetime.now() < session['two_factor']['code_delay'] :
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


#@app.route('login/', methods = ['GET', 'POST'])
def login(mode) :
	"""
	mode = mobile_on : we display the original (large) qrcode which provides a list of mobile apps for mobile devices
	mode = mobile_off_qrcode_on : qrcode only for desktop
	mode = password  : display password form
	mode = None : provide a dispaye with qrcode for deskytop and password form for smartphone
	"""
	if request.method == 'GET' :
		session.clear()
		if request.args.get('mode') == 'mobile_on':
			print('login_mobile.html')
			return render_template('login_mobile.html')
		elif request.args.get('mode') == 'password':
			print('login_password.html')
			return render_template('login_password.html')
		elif request.args.get('mode') == 'mobile_off_qrcode_on' :
			print('login_qrcode.html')
			return render_template('login_qrcode.html', username=request.args.get('username', ""))
		else :
			print('login.html')
			return render_template('login.html', username=request.args.get('username', ""))

	if request.method == 'POST' :
		print('passage par post')
		if session.get('try_number') is None :
			session['try_number'] = 1
		session['username_to_log'] = request.form['username']
		if not ns.username_exist(session['username_to_log'], mode)  :
			flash('Username not found', "warning")
			session['try_number'] = 1
			return render_template('login.html', username="")
		if not ns.check_password(session['username_to_log'], request.form['password'], mode)  :
			session['try_number'] +=1
			if session['try_number'] == 2 :
				flash('This password is incorrect, 2 trials left', 'warning')
				return render_template('login.html', username=session['username_to_log'])
			elif session['try_number'] == 3 :
				flash('This password is incorrect, 1 trial left', 'warning')
				return render_template('login.html', username=session['username_to_log'])
			else :
				flash("Too many trials (3 max)", "warning")
				session['try_number'] = 1
				return render_template('login.html', username="")
		else :
			# secret code to send by email or sms
			session['code'] = str(random.randint(10000, 99999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 180)
			# send code by sms if phone exist else email
			session['support'] = send_secret_code(session['username_to_log'], session['code'],mode)
			if session['support'] is None :
				flash("Problem to send secret code", 'warning')
				return redirect(mode.server + 'login/')
			else :
				print('Warning : secret code sent = ', session['code'])
				flash("Secret code sent by " + session['support'], 'success')
				session['try_number'] = 1
				return render_template("authentification.html", support=session['support'])

# recuperation du code saisi
#@app.route('/login/authentification/', methods = ['POST'])
def login_authentification(mode) :
	if session.get('username_to_log') is None or session.get('code') is None :
		flash("Authentification expired", "warning")
		return render_template('login.html')
	code = request.form['code']
	session['try_number'] +=1
	print('Warning : code received = ', code)
	authorized_codes = [session['code'], '123456'] if mode.test else [session['code']]
	if code in authorized_codes and datetime.now() < session['code_delay'] :
		session['username'] = session['username_to_log']
		del session['username_to_log']
		del session['try_number']
		del session['code']
		del session['support']
		return redirect(mode.server + 'user/')
	elif session['code_delay'] < datetime.now() :
		flash("Code expired", "warning")
		return redirect(mode.server + 'user/')
	elif session['try_number'] > 3 :
		flash("Too many trials (3 max)", "warning")
		return render_template("authentification.html")
	else :
		if session['try_number'] == 2 :
			flash('This code is incorrect, 2 trials left', 'warning')
		if session['try_number'] == 3 :
			flash('This code is incorrect, 1 trial left', 'warning')
		return render_template("authentification.html", support=session['support'])


# logout
#@app.route('/logout/', methods = ['GET'])
def logout(mode) :
	if not session.get('logout') :
		print('appel de logout')
		session['logout'] = 'on'
		return render_template('logout.html')
	# delete picture, signateure and files before logout, clear session.
	check_login()
	try :
		os.remove(mode.uploads_path + session['picture'])
		os.remove(mode.uploads_path + session['signature'])
	except :
		print('Error : effacement picture/signature erreur')
	for one_file in session['identity_file'] :
		try :
			os.remove(mode.uploads_path + one_file['filename'])
		except :
			print('Error : effacement file error')
	session.clear()
	flash('Thank you for your visit', 'success')
	return redirect (mode.server + 'login/')


# mentions legales
#@app.route('/company')
def company() :
	return render_template('company.html')


# protetion des données personelles
#@app.route('/privacy')
def privacy() :
	return render_template('privacy.html')

# forgot username
""" @app.route('/forgot_username/', methods = ['GET', 'POST'])
This function is called from the starter and login view.
"""
def forgot_username(mode) :
	if request.method == 'GET' :
		return render_template('forgot_username.html')
	if request.method == 'POST' :
		username_list = ns.get_username_list_from_email(request.form['email'], mode)
		if username_list == [] :
			flash('There is no Identity with this Email' , 'warning')
		else :
			flash('This Email is already used by Identities : ' + ", ".join(username_list) , 'success')
		return render_template('login.html', name="")

# forgot password
""" @app.route('/forgot_password/', methods = ['GET', 'POST'])
This function is called from the starter and login view.
build JWE to store timestamp, username and email, we use Talao RSA key
"""
def forgot_password(mode) :
	if request.method == 'GET' :
		return render_template('forgot_password_init.html')
	if request.method == 'POST' :
		username = request.form.get('username')
		if not ns.username_exist(username, mode) :
			flash("Username not found", "warning")
			return render_template('login.html')
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
		link = mode.server + 'forgot_password_2/?'+ urlencode({'token'  : token.decode('utf-8')}, doseq=True)
		subject = "Renew your password"
		if Talao_message.messageHTML(subject, email, 'forgot_password', {'link': link}, mode):
			flash("You are going to receive an email to renew your password.", "success")
		return render_template('login.html')

# forgot password 2
""" @app.route('/forgot_password_2/', methods = ['GET', 'POST'])
This function is called from email to decode token and reset password.
"""
def forgot_password_2(mode) :
	if request.method == 'GET' :
		token = request.args.get('token')
		key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
		jwe = JsonWebEncryption()
		try :
			data = jwe.deserialize_compact(token, key)
		except :
			flash ('Incorrect data', 'danger')
			return render_template('login.html')
		payload = json.loads(data['payload'].decode('utf-8'))
		if payload['expired'] < datetime.timestamp(datetime.now()) :
			flash ('Delay expired (3 minutes maximum)', 'danger')
			return render_template('login.html')
		session['email_password'] = payload['email']
		session['username_password'] = payload['username']
		return render_template('update_password_external.html')
	if request.method == 'POST' :
		if session['email_password'] != request.form['email'] :
			flash('Incorrect email', 'danger')
			return render_template('update_password_external.html')
		ns.update_password(session['username_password'], request.form['password'], mode)
		flash('Password updated', "success")
		del session['email_password']
		del session['username_password']
		return render_template('login.html')



#@app.route('/use_my_own_address/', methods = ['GET', 'POST'])
def use_my_own_address(mode) :
	flash("Feature not available yet.", "warning")
	return redirect(mode.server + 'user/')

############################################################################################
#		 DATA
############################################################################################
""" on ne gere aucune information des data en session """
#@app.route('/data/', methods=['GET'])
def data(mode) :
	check_login()
	dataId = request.args['dataId']
	workspace_contract = '0x' + dataId.split(':')[3]
	support = dataId.split(':')[4]
	if support == 'document' :
		doc_id = int(dataId.split(':')[5])
		my_topic = dataId.split(':')[6]
		my_data = Document(my_topic)
		exist = my_data.relay_get(workspace_contract, doc_id, mode)
		if not exist :
			print('Error data in webserver.py, Class instance needed')
			return redirect(mode.server + 'user/')
		expires = my_data.expires
		my_topic = my_data.topic.capitalize()
	if support == 'claim' :
		claim_id = dataId.split(':')[5]
		my_data = Claim()
		my_data.get_by_id(session.get('workspace_contract'), session.get('private_key_value'), workspace_contract, claim_id, mode)
		expires = 'Unlimited'
		my_topic = 'Personal'
	myvisibility = my_data.privacy

	# issuer
	issuer_name = my_data.issuer.get('name', 'Unknown') if my_data.issuer['category'] == 2001 else my_data.issuer['firstname'] + ' ' +my_data.issuer['lastname']
	issuer_username = ns.get_username_from_resolver(my_data.issuer['workspace_contract'], mode)
	issuer_username = 'Unknown' if not issuer_username  else issuer_username
	issuer_type = 'Company' if my_data.issuer['category'] == 2001 else 'Person'

	myissuer = """
				<span>
				<b>Issuer</b><a class="text-secondary" href=/user/issuer_explore/?issuer_username="""+ issuer_username + """ >
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i></a>
				<li><b>Name</b> : """ + issuer_name + """<br></li>
				<li><b>Username</b> : """ + issuer_username +"""<br></li>
				<li><b>Type</b> : """ + issuer_type + """<br></li>
				"""
	# for audit
	if support == 'document' :
		myissuer= myissuer + """
				<li><b>IP Address</b> : """ + my_data.request_remote_addr + """<br></li>
				<li><b>Issuer Agent</b> : """ + my_data.request_remote_user_agent.get('string', 'None') + """<br></li>
				<li><b>Issuer Browser</b> : """ + my_data.request_remote_user_agent.get('browser', 'None') + """<br></li>
				<li><b>Issuer Platform</b> : """ + my_data.request_remote_user_agent.get('platform', 'None') + """<br></li>"""

	if my_data.issuer['workspace_contract'] == session.get('workspace_contract') or my_data.issuer['workspace_contract'] == mode.relay_workspace_contract :
		myissuer = myissuer + """
				 <a class="text-warning">Self Declaration</a>
				</span>"""
	else :
		myissuer = myissuer + "<br>Issuer fiability : " + str(vpi.check_proof_of_identity(session.get('workspace_contract'), my_data.issuer['workspace_contract'], mode)*100)+'%'


	# advanced """
	(location, link) = (my_data.data_location, my_data.data_location)
	if mode.BLOCKCHAIN == 'rinkeby' :
		transaction_hash = """<a class = "card-link" href = https://rinkeby.etherscan.io/tx/ """ + my_data.transaction_hash + """>"""+ my_data.transaction_hash + """</a>"""
	elif mode.BLOCKCHAIN == 'ethereum' :
		transaction_hash = """<a class = "card-link" href = https://etherscan.io/tx/ """ + my_data.transaction_hash + """>"""+ my_data.transaction_hash + """</a>"""
	elif mode.BLOCKCHAIN == 'talaonet' :
		transaction_hash = my_data.transaction_hash
	else :
		print('Error : blockchain problem')
		transaction_hash = my_data.transaction_hash = ""

	if support == 'document' :
		myadvanced = """
				<b>Advanced</b>
				<li><b>Document Id</b> : """ + dataId + """<br></li>
				<li><b>Doc Id</b> : """ + str(doc_id) + """<br></li>
				<li><b>Privacy</b> : """ + myvisibility.capitalize() + """<br></li>
				<li><b>Created</b> : """ + my_data.created + """<br></li>
				<li><b>Expires</b> : """ + expires + """<br></li>
				<li><b>Transaction Hash</b> : """ + transaction_hash + """<br></li>
				<li><b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a></li>
				<li><b>Cryptography</b> : AES-128 AEX Mode, key = 'public_ipfs_key_'<br></li>"""
	# if support is an ERC725 Claim
	else :
		(location, link) = (mode.BLOCKCHAIN, "") if myvisibility == 'public' else (my_data.data_location, my_data.data_location)
		myadvanced = """
				<b>Advanced</b>
				<li><b>Claim Id</b> : """ + str(claim_id) + """<br></li>
				<li><b>Topic</b> : """ + str(my_data.topicname) + """<br></li>
				<li><b>Privacy</b> : """ + myvisibility + """<br></li>
				<li><b>Created</b> : """ + my_data.created + """<br></li>
				<li><b>Expires</b> : """ + expires + """<br></li>
				<li><b>Transaction Hash</b> : """ +transaction_hash + """<br></li>
				<li><b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a></li>"""


	my_verif =  myadvanced + "<hr>" + myissuer
	return render_template('data_check.html', **session['menu'], verif=my_verif)


#######################################################################################
#						USER
#######################################################################################

""" fonction principale d'affichage de l identité """
#@app.route('/user/', methods = ['GET'])
def user(mode) :
	check_login()
	if not session.get('uploaded', False) :
		print('Warning : start first instanciation user')
		if mode.test :
			user = Identity(ns.get_data_from_username(session['username'],mode)['workspace_contract'], mode, authenticated=True)
		else :
			try :
				user = Identity(ns.get_data_from_username(session['username'],mode)['workspace_contract'], mode, authenticated=True)
			except :
				flash('session aborted', 'warning')
				return render_template('login.html')
		print('Warning : end of first intanciation')

		# clean up for resume
		user_dict = user.__dict__.copy()
		del user_dict['aes']
		del user_dict['rsa_key_value']
		del user_dict['private_key_value']
		del user_dict['secret']
		del user_dict['partners']

		# init session
		session['resume'] = user_dict
		session['uploaded'] = True
		session['type'] = user.type
		session['address'] = user.address
		session['workspace_contract'] = user.workspace_contract
		session['issuer'] = user.issuer_keys
		session['whitelist'] = user.white_keys
		session['partner'] = user.partners
		session['did'] = user.did
		session['eth'] = user.eth
		session['token'] = user.token
		session['rsa_key'] = user.rsa_key
		session['rsa_key_value'] = user.rsa_key_value
		session['rsa_filename'] =  session['address'] + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
		session['private_key'] = user.private_key
		session['private_key_value'] = user.private_key_value
		session['relay_activated'] = user.relay_activated
		session['personal'] = user.personal
		session['identity_file'] = user.identity_file
		session['name'] = user.name
		session['secret'] = user.secret
		session['picture'] = user.picture
		session['signature'] = user.signature
		session['test'] = mode.test
		session['skills'] = user.skills
		session['certificate'] = user.certificate

		phone =  ns.get_data_from_username(session['username'], mode).get('phone')
		session['phone'] = phone if phone else ""

		if user.type == 'person' :
			session['experience'] = user.experience
			session['education'] = user.education
			session['kyc'] = user.kyc
			session['profil_title'] = user.profil_title
			session['menu'] = {'picturefile' : user.picture,
								'username' : session['username'],
								'name' : user.name,
								'private_key_value' : user.private_key_value,
								'rsa_filename': session['rsa_filename'],
								'profil_title' : session['profil_title'],
								'clipboard' : mode.server  + "resume/?workspace_contract=" + session['workspace_contract']}
		if user.type == 'company' :
			session['kbis'] = user.kbis
			session['profil_title'] = ""
			session['menu'] = {'picturefile' : user.picture,
								'username' : session['username'],
								'name' : user.name,
								'private_key_value' : user.private_key_value,
								'rsa_filename': session['rsa_filename'],
								'profil_title' : session['profil_title'],
								'clipboard' : mode.server  + "board/?workspace_contract=" + session['workspace_contract']}


		# welcome message
		message = ""
		if not session['private_key'] :
			message = message + 'Private key not found. You cannot issue claims.'
		if not session['rsa_key'] :
			message = message + 'Rsa key not found. You cannot encrypt data.'
		if message != "" :
			flash(message, 'warning')

		# ask update password messsage
		#if ns.must_renew_password(session['username'], mode) :
		#	return render_template('ask_update_password.html', **session['menu'])

		#Homepage
		if user.type == 'person' :
			return render_template('homepage.html', **session['menu'])


##### debut page resume a mettre dans une @route '/resume'

	# account
	my_account = """ <b>ETH</b> : """ + str(session['eth'])+"""<br>
					<b>token TALAO</b> : """ + str(session['token'])
	if session['username'] == 'talao' :
		relay_eth = mode.w3.eth.getBalance(mode.relay_address)/1000000000000000000
		relay_token = float(token_balance(mode.relay_address,mode))
		talaogen_eth = mode.w3.eth.getBalance(mode.Talaogen_public_key)/1000000000000000000
		talaogen_token = float(token_balance(mode.Talaogen_public_key, mode))
		total_deposit, vault_deposit = get_data_from_token(mode)
		my_account = my_account + """<br><br>
					<b>Relay ETH</b> : """ + str(relay_eth) + """<br>
					<b>Relay token Talao</b> : """ + str(relay_token) + """<br><br>
					<b>Talao Gen ETH</b> : """ + str(talaogen_eth) + """<br>
					<b>Talao Gen token Talao</b> : """ + str(talaogen_token) + """<br><br>
					<b>Vault Deposit</b> : """ + str(vault_deposit/10**18) + """ TALAO <br>
					<b>Total Deposit</b> : """ + str(total_deposit/10**18) + """ TALAO<br>
					<b>Nb Identities</b> : """ + str(int(total_deposit/vault_deposit))

	# advanced
	relay = 'Activated' if session['relay_activated'] else 'Not Activated'
	relay_rsa_key = 'Yes' if session['rsa_key']  else 'No'
	relay_private_key = 'Yes' if session['private_key'] else 'No'
	path = """https://rinkeby.etherscan.io/address/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/address/"""
	my_advanced = """
					<b>Blockchain</b> : """ + mode.BLOCKCHAIN.capitalize() + """<br>
					<b>Worskpace Contract</b> : <a class = "card-link" href = """ + path + session['workspace_contract'] + """>"""+ session['workspace_contract'] + """</a><br>
					<b>Owner Wallet Address</b> : <a class = "card-link" href = """ + path + session['address'] + """>"""+ session['address'] + """</a><br>"""
	if session['username'] != 'talao' :
		if relay == 'Activated' :
			my_advanced = my_advanced + """ <hr><b>Relay Status : </b>""" + relay + """<br>"""
		else :
			my_advanced = my_advanced + """ <hr><b>Relay Status : </b>""" + relay + """<a class ="text-warning" >You cannot store data.</a><br>"""

		if relay_rsa_key == 'Yes' :
			my_advanced = my_advanced + """<b>RSA Key</b> : """ + relay_rsa_key + """<br>"""
		else :
			my_advanced = my_advanced +"""<b>RSA Key</b> : """ + relay_rsa_key + """<br><a class ="text-warning" >You cannot store and access private and secret data.</a><br>"""

		if relay_private_key == 'Yes' :
			my_advanced = my_advanced + """<b>Private Key</b> : """ + relay_private_key +"""<br>"""
		else :
			my_advanced = my_advanced + """<b>Private Key</b> : """ + relay_private_key + """<br><a class="text-warning" >You cannot issue certificates for others.</a><br>"""


	my_advanced = my_advanced + "<hr>" + my_account +  "<hr>"

	# Partners
	if session['partner'] == [] :
		my_partner = """<a class="text-info">No Partners available</a>"""
	else :
		my_partner = ""
		for partner in session['partner'] :
			#partner_username = ns.get_username_from_resolver(partner['workspace_contract'])
			#partner_username = 'Unknown' if partner_username is None else partner_username
			if partner['authorized'] == 'Pending' :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner['username'] + """">"""+ partner['username'] + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
					<a class="text-secondary" href="/user/reject_partner/?partner_username=""" + partner['username'] +"""&amp;partner_workspace_contract=""" + partner['workspace_contract']+"""">
						<i data-toggle="tooltip" class="fa fa-thumbs-o-down" title="Reject this Partnership.">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/authorize_partner/?partner_username=""" + partner['username'] + """&amp;partner_workspace_contract=""" + partner['workspace_contract']+ """">
						<i data-toggle="tooltip" class="fa fa-thumbs-o-up" title="Authorize this Parnership."></i>
					</a>
				</spn>"""
			elif partner['authorized'] == 'Removed' :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner['username'] + """">"""+ partner['username'] + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
				</spn>"""
			else :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner['username'] + """">"""+ partner['username'] + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
					<a class="text-secondary" href="/user/remove_partner/?partner_username=""" + partner['username'] +"""&amp;partner_workspace_contract=""" + partner['workspace_contract']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove this Partnership.">&nbsp&nbsp&nbsp</i>
				</spn>"""
			my_partner = my_partner + partner_html + """<br>"""


	# Issuer for document, they have an ERC725 key 20002
	if session['issuer'] == [] :
		my_issuer = """  <a class="text-info">No Referents available</a>"""
	else :
		my_issuer = ""
		for one_issuer in session['issuer'] :
			issuer_username = ns.get_username_from_resolver(one_issuer['workspace_contract'], mode)
			issuer_username = 'Unknown' if issuer_username is None else issuer_username
			issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_issuer/?issuer_username="""+ issuer_username +"""&amp;issuer_address=""" + one_issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span>"""
			my_issuer = my_issuer + issuer_html + """<br>"""


	# whitelist
	if session['whitelist'] == [] :
		my_white_issuer = """  <a class="text-info">No Whitelist available</a>"""
	else :
		my_white_issuer = ""
		for issuer in session['whitelist'] :
			issuer_username = ns.get_username_from_resolver(issuer['workspace_contract'], mode)
			issuer_username = 'Unknown' if issuer_username is None else issuer_username
			issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_white_issuer/?issuer_username="""+issuer_username +"""&amp;issuer_address="""+issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span>"""
			my_white_issuer = my_white_issuer + issuer_html + """<br>"""


	# files
	if session['identity_file'] == [] :
		my_file = """<a class="text-info">No Files available</a>"""
	else :
		my_file = ""
		for one_file in session['identity_file'] :
			file_html = """
				<b>File Name</b> : """+one_file['filename']+ """ ( """+ one_file['privacy'] + """ ) <br>
				<b>Created</b> : """+ one_file['created'] + """<br>
				<p>
					<a class="text-secondary" href="/user/remove_file/?file_id=""" + one_file['id'] + """&filename="""+one_file['filename'] +"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>

					<a class="text-secondary" href=/user/download/?filename=""" + one_file['filename'] + """>
						<i data-toggle="tooltip" class="fa fa-download" title="Download"></i>
					</a>
				</p>"""
			my_file = my_file + file_html

	# skills
	if session['skills'] is None or session['skills'].get('id') is None :
		my_skills =  """<a class="text-info">No data available</a>"""
	else :
		my_skills = ""
		for skill in session['skills']['description'] :
			skill_html = skill['skill_name'] + """ (""" + skill['skill_level'] + """)""" + """<br>"""
			my_skills = my_skills + skill_html
		my_skills = my_skills + """
				<p>
					<a class="text-secondary" href=/data/?dataId="""+ session['skills']['id'] + """:skills>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""



####################################################################################################
	# specific to person
####################################################################################################
	if session['type'] == 'person' :
		# experience
		my_experience = ""
		if len (session['experience']) == 0:
			my_experience = my_experience + """<a class="text-info">No Experience available</a>"""
		else :
			for experience in sorted(session['experience'], key= lambda d: time.strptime(d['start_date'], "%Y-%m-%d"), reverse=True) :
				exp_html = """
				<b>Company</b> : """+experience['company']['name']+"""<br>
				<b>Title</b> : """+experience['title']+"""<br>
				<b>Start Date</b> : """+experience['start_date']+"""<br>
					<b>End Date</b> : """+experience['end_date']+"""<br>
				<b>Description</b> : """+experience['description'][:100]+"""...<br>
				<p>
					<a class="text-secondary" href="/user/remove_experience/?experience_id=""" + experience['id'] + """&experience_title="""+ experience['title'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>

					<a class="text-secondary" href=/data/?dataId="""+ experience['id'] + """:experience>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""
				my_experience = my_experience + exp_html + "<hr>"

		# education
		my_education = ""
		if len (session['education']) == 0:
			my_education = my_education + """<a class="text-info">No Education available</a>"""
		else :
			for education in session['education'] :
				edu_html = """
				<b>Organization</b> : """+education['organization']['name']+"""<br>
				<b>Title</b> : """+education['title'] + """<br>
				<b>Start Date</b> : """+education['start_date']+"""<br>
				<b>End Date</b> : """+education['end_date']+"""<br>
				<p>
					<a class="text-secondary" href="/user/remove_education/?education_id=""" + education['id'] + """&education_title="""+ education['title'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href=/data/?dataId="""+ education['id'] + """:education>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""
				my_education = my_education + edu_html	+ "<hr>"

		# personal
		Topic = {'firstname' : 'Firstname',
				'lastname' : 'Lastname',
				'about' : 'About',
				'profil_title' : 'Title',
				'birthdate' : 'Birth Date',
				'contact_email' : 'Contact Email',
				'contact_phone' : 'Contact Phone',
				'postal_address' : 'Postal Address',
				'education' : 'Education'}
		my_personal = ""
		for topicname in session['personal'].keys() :
			if session['personal'][topicname]['claim_value'] :
				topicname_value = session['personal'][topicname]['claim_value']
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':claim:' + session['personal'][topicname]['claim_id']
				topicname_privacy = ' (' + session['personal'][topicname]['privacy'] + ')'
				my_personal = my_personal + """
				<span><b>""" + Topic[topicname] + """</b> : """+ topicname_value + topicname_privacy +"""
					<a class="text-secondary" href=/data/?dataId=""" + topicname_id + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span><br>"""

		# kyc
		my_kyc = """
			<b>Authentification Key (ECDSA/ES256K)</b> : """+ session['address'] +"""<br><hr>"""

		if not session['kyc'] :
			my_kyc = my_kyc + """<a class="text-warning">No other proof of identity available.</a>"""

		else :
			kyc = session['kyc'][-1]
			kyc_html = """
				<b>Identity checking method</b> : """+ kyc.get('identification', 'Electronic Check') + """<br>
				<b>Firstname</b> : """+ kyc.get('given_name', '') +"""<br>
				<b>Lastname</b> : """+ kyc.get('family_name', '') +"""<br>
				<b>Birth Date</b> : """+ kyc.get('birthdate', '') +"""<br>
				<b>Gender</b> : """+ kyc.get('gender', ' ').capitalize() +"""<br>
				<b>Phone</b> : """ + kyc.get('phone', '') + """<br>
				<b>Email</b>  : """ + kyc.get('email', '') + """<br>
				<b>Address</b>  : """ + kyc.get('address', '') + """<br>
				<p>
					<a class="text-secondary" href="/user/remove_kyc/?kyc_id=""" + kyc['id'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href=/data/?dataId="""+ kyc['id'] + """:kyc>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""
			my_kyc = my_kyc + kyc_html

		# Alias
		if session['username'] != ns.get_username_from_resolver(session['workspace_contract'], mode) :
			display_alias = False
			my_access = ""
		else :
			display_alias = True
			my_access = ""
			access_list = ns.get_alias_list(session['workspace_contract'], mode)
			for access in access_list :
				if access['username'] == session['username'] :
					access_html = """
					<span>""" + session['username'] + """ (logged)
					</span>"""
				else :
					access_html = """
					<span>""" + access['username'] + """ : """ +  access['email'] +"""
						<a class="text-secondary" href="/user/remove_access/?username_to_remove="""+ access['username']+"""">
							<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">	</i>
						</a>
					</span>"""
				my_access = my_access + access_html + """<br>"""

		# certificates
		my_certificates = ""
		if len(session['certificate']) == 0:
			my_certificates = my_certificates + """<a class="text-info">No Certificates available</a>"""
		else :
			for counter, certificate in enumerate(session['certificate'],1) :
				issuer_username = ns.get_username_from_resolver(certificate['issuer']['workspace_contract'], mode)
				issuer_username = 'Unknown' if not issuer_username else issuer_username
				if certificate['issuer']['category'] == 2001 : # company
					issuer_name = certificate['issuer']['name']
					#issuer_type = 'Company'
				elif  certificate['issuer']['category'] == 1001 :
					issuer_name = certificate['issuer']['firstname'] + ' ' + certificate['issuer']['lastname']
					#issuer_type = 'Person'
				else :
					pass
				# <b>Title</b> : """ + certificate.get('title', 'None')+"""<br>
				cert_html = """<hr>
							<b>Referent Name</b> : """ + issuer_name +"""<br>
							<b>Certificate Type</b> : """ + certificate['type'].capitalize()+"""<br>
							<b>Title</b> : """ + certificate.get('title', 'None')+"""<br>
							<b>Description</b> : """ + certificate['description'][:100]+"""...<br>

							<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """>Display Certificate</a><br>
							<p>
							<a class="text-secondary" href="/user/remove_certificate/?certificate_id=""" + certificate['id'] + """&certificate_title="""+ certificate.get('title', "None") + """">
							<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
							</a>
							<a class="text-secondary" href=/data/?dataId=""" + certificate['id'] + """:certificate>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check">&nbsp&nbsp&nbsp</i>
							</a>
							<a class="text-secondary" onclick="copyToClipboard('#p"""+ str(counter) + """')">
							<i data-toggle="tooltip" class="fa fa-clipboard" title="Copy Certificate Link"></i>
							</a>
							</p>
							<p hidden id="p""" + str(counter) + """" >""" + mode.server  + """guest/certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """</p>"""
				my_certificates = my_certificates + cert_html

		return render_template('person_identity.html',
							**session['menu'],
							display_alias = display_alias,
							personal=my_personal,
							kyc=my_kyc,
							experience=my_experience,
							education=my_education,
							skills=my_skills,
							certificates=my_certificates,
							access=my_access,
							partner=my_partner,
							issuer=my_issuer,
							whitelist=my_white_issuer,
							advanced=my_advanced,
							digitalvault= my_file,
							nb_certificates=len(session['certificate'])
							)
	# specific to company
	if session['type'] == 'company' :
		# Manager
		if session['username'] != ns.get_username_from_resolver(session['workspace_contract'], mode) :
			display_manager = False
			my_access = ""
		else :
			display_manager = True
			my_access_start = """<a href="/user/add_manager/">Add a Manager</a><hr> """
			my_access = ""
			access_list = ns.get_manager_list(session['workspace_contract'], mode)
			for access in access_list :
				if access['username'] == session['username'] :
					access_html = """
					<span>""" + session['username'] + """ (logged)
					</span>"""
				else :
					access_html = """
					<span>""" + access['username'] + """ : """ +  access['email'] +"""
					<a class="text-secondary" href="/user/remove_access/?username_to_remove="""+ access['username']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">	</i>
					</a>
					</span>"""
				my_access = my_access + access_html + """<br>"""
			my_access = my_access_start + my_access

		# API
		credentials = ns.get_credentials(session['username'], mode)
		if not len (credentials) :
			my_api = """<a class="text-info">Contact relay@talao.io to get your API credentials.</a>"""
		else :
			my_api = """ <div style="height:200px;overflow:auto;overflow-x: hidden;">"""
			for cred in credentials :
				my_api = my_api + """
				<b>client_id</b> : """+ cred['client_id'] +"""<br>
				<b>client_secret</b> : """+ cred['client_secret'] + """<br>
				<b>client_uri</b> : """+ cred['client_uri'] + """<br>
				<b>redirect_uri</b> : """+ cred['redirect_uris'][0] + """<br>
				<b>scope</b> : """+ cred['scope'] + """<br>
				<b>grant_types</b> : """+ " ".join(cred['grant_types']) + """<br><hr> """
			my_api = my_api + """</div>"""
		# kbis
		if len (session['kbis']) == 0:
			my_kbis = """<a href="/user/request_proof_of_identity/">Request a Proof of Identity</a><hr>
					<a class="text-danger">No Proof of Identity available</a>"""
		else :
			my_kbis = ""
			for kbis in session['kbis'] :
				kbis_html = """
				<b>Name</b> : """+ kbis['name'] +"""<br>
				<b>SIREN</b> : """+ kbis.get('siren', '') +"""<br>
				<b>Creation</b> : """+ kbis['date'] + """<br>
				<b>Capital</b> : """+ kbis['capital']+"""<br>
				<b>Address</b> : """+ kbis['address']+"""<br>

					<a class="text-secondary" href="/user/remove_kbis/?kbis_id=""" + kbis['id'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href=/data/?dataId="""+ kbis['id'] + """:kbis>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				"""
				my_kbis = my_kbis + kbis_html

		# company settings
		my_personal = """<a href="/user/picture/">Change Logo</a><br>
						<a href="/user/signature/">Change Signature</a><br>"""
		for topicname in session['personal'].keys() :
			if session['personal'][topicname]['claim_value'] :
				topicname_value = session['personal'][topicname]['claim_value']
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':claim:' + session['personal'][topicname]['claim_id']
				topicname_privacy = ' (' + session['personal'][topicname]['privacy'] + ')'
				my_personal = my_personal + """
				<span><b>""" + topicname + """</b> : """+ topicname_value + topicname_privacy +"""
					<a class="text-secondary" href=/data/?dataId=""" + topicname_id + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span><br>"""
		my_personal = my_personal + """<a href="/user/update_company_settings/">Update Company Data</a>"""

		# certificates
		if  not len (session['certificate']) :
			my_certificates =  """<a class="text-info">No Certificates available</a>"""
		else :
			my_certificates = """<div  style="height:300px;overflow:auto;overflow-x: hidden;">"""
			for counter, certificate in enumerate(session['certificate'],1) :
				issuer_username = ns.get_username_from_resolver(certificate['issuer']['workspace_contract'], mode)
				issuer_username = 'Unknown' if issuer_username is None else issuer_username
				if certificate['issuer']['category'] == 2001 :
					issuer_name = certificate['issuer']['name']
				else :
					issuer_name = certificate['issuer']['firstname'] + ' ' + certificate['issuer']['lastname']
				if certificate['type'] == 'agreement' :
					if not issuer_name :
						issuer_name = 'unknown'
					cert_html = """<hr>
								<b>Referent Name</b> : """ + issuer_name +"""<br>
								<b>Certificate Type</b> : """ + certificate.get('type','').capitalize()+"""<br>
								<b>Title</b> : """ + certificate.get('title',"").capitalize()+"""<br>
								<b>Registration number</b> : """ + certificate.get('registration_number',"").capitalize()+"""<br>
								<b>Description</b> : " """ + certificate['description'][:100]+"""..."<br>

								<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """>Display Certificate</a><br>
								<p>
								<a class="text-secondary" href="/user/remove_certificate/?certificate_id=""" + certificate['id'] + """&certificate_title=""" + certificate['type'].capitalize()+ """">
								<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
								</a>

								<a class="text-secondary" href=/data/?dataId=""" + certificate['id'] + """:certificate>
								<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check">&nbsp&nbsp&nbsp</i>
								</a>
								<a class="text-secondary" onclick="copyToClipboard('#p"""+ str(counter) + """')">
								<i data-toggle="tooltip" class="fa fa-clipboard" title="Copy Certificate Link"></i>
								</a>
								</p>
								<p hidden id="p""" + str(counter) +"""" >""" + mode.server  + """guest/certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """</p>"""

				elif certificate['type'] ==  "reference" :
					cert_html = """<hr>
								<b>Referent Name</b> : """ + issuer_name +"""<br>
								<b>Certificate Type</b> : """ + certificate.get('type', 'Unknown').capitalize()+"""<br>
								<b>Title</b> : """ + certificate.get('title', 'Unknown').capitalize()+"""<br>
								<b>Description</b> : " """ + certificate.get('description', 'Unknown')[:100]+"""..."<br>
								<b>Budget</b> : """ + certificate.get('budget', 'Unknown') + """<br>
								<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """>Display Certificate</a><br>
								<p>
								<a class="text-secondary" href="/user/remove_certificate/?certificate_id=""" + certificate['id'] + """&certificate_title=""" + certificate.get('type', 'Unknown').capitalize()+ """">
								<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
								</a>

								<a class="text-secondary" href=/data/?dataId=""" + certificate['id'] + """:certificate>
								<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check">&nbsp&nbsp&nbsp</i>
								</a>

								<a class="text-secondary" onclick="copyToClipboard('#p"""+ str(counter) + """')">
								<i data-toggle="tooltip" class="fa fa-clipboard" title="Copy Certificate Link"></i>
								</a>
								</p>
								<p hidden id="p""" + str(counter) +"""" >""" + mode.server  + """guest/certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """</p>"""
				else :
					cert_html =""
					print('Error : incorrect certificate type : ' + certificate.get('type', 'Unknown'))
				my_certificates = my_certificates + cert_html
			my_certificates = my_certificates + """</div>"""

		return render_template('company_identity.html',
							**session['menu'],
							manager=my_access,
							display_manager= display_manager,
							personal=my_personal,
							skills=my_skills,
							kbis=my_kbis,
							issuer=my_issuer,
							partner=my_partner,
							certificates=my_certificates,
							api=my_api,
							whitelist=my_white_issuer,
							advanced=my_advanced,
							digitalvault=my_file)


def user_advanced(mode) :
	check_login()

	# account
	my_account = """ <b>ETH</b> : """ + str(session['eth'])+"""<br>
					<b>token TALAO</b> : """ + str(session['token'])
	if session['username'] == 'talao' :
		relay_eth = mode.w3.eth.getBalance(mode.relay_address)/1000000000000000000
		relay_token = float(token_balance(mode.relay_address,mode))
		talaogen_eth = mode.w3.eth.getBalance(mode.Talaogen_public_key)/1000000000000000000
		talaogen_token = float(token_balance(mode.Talaogen_public_key, mode))
		my_account = my_account + """<br><br>
					<b>Relay ETH</b> : """ + str(relay_eth) + """<br>
					<b>Relay token Talao</b> : """ + str(relay_token) + """<br><br>
					<b>Talao Gen ETH</b> : """ + str(talaogen_eth) + """<br>
					<b>Talao Gen token Talao</b> : """ + str(talaogen_token)

	# Alias
	if session['username'] != ns.get_username_from_resolver(session['workspace_contract'], mode) :
		#display_alias = False
		my_access = ""
	else :
		display_alias = True
		my_access = ""
		access_list = ns.get_alias_list(session['workspace_contract'], mode)
		for access in access_list :
			if access['username'] == session['username'] :
				access_html = """
				<span>""" + session['username'] + """ (logged)
				</span>"""
			else :
				access_html = """
				<span>""" + access['username'] + """ : """ +  access['email'] +"""
						<a class="text-secondary" href="/user/remove_access/?username_to_remove="""+ access['username']+"""">
							<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">	</i>
						</a>
					</span>"""
			my_access = my_access + access_html + """<br>"""

	# Advanced

	relay = 'Activated' if session['relay_activated'] else 'Not Activated'
	relay_rsa_key = 'Yes' if session['rsa_key']  else 'No'
	relay_private_key = 'Yes' if session['private_key'] else 'No'
	path = """https://rinkeby.etherscan.io/address/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/address/"""
	my_advanced = """
					<b>Blockchain</b> : """ + mode.BLOCKCHAIN.capitalize() + """<br>
					<b>Worskpace Contract</b> : <a class = "card-link" href = """ + path + session['workspace_contract'] + """>"""+ session['workspace_contract'] + """</a><br>
					<b>Owner Wallet Address</b> : <a class = "card-link" href = """ + path + session['address'] + """>"""+ session['address'] + """</a><br>"""
	if session['username'] != 'talao' :
		if relay == 'Activated' :
			my_advanced = my_advanced + """ <hr><b>Relay Status : </b>""" + relay + """<br>"""
		else :
			my_advanced = my_advanced + """ <hr><b>Relay Status : </b>""" + relay + """<a class ="text-warning" >You cannot store data.</a><br>"""

		if relay_rsa_key == 'Yes' :
			my_advanced = my_advanced + """<b>RSA Key</b> : """ + relay_rsa_key + """<br>"""
		else :
			my_advanced = my_advanced +"""<b>RSA Key</b> : """ + relay_rsa_key + """<br><a class ="text-warning" >You cannot store and access private and secret data.</a><br>"""

		if relay_private_key == 'Yes' :
			my_advanced = my_advanced + """<b>Private Key</b> : """ + relay_private_key +"""<br>"""
		else :
			my_advanced = my_advanced + """<b>Private Key</b> : """ + relay_private_key + """<br><a class="text-warning" >You cannot issue certificates for others.</a><br>"""
	my_advanced = my_advanced + "<hr>" + my_account

	# Partners
	if session['partner'] == [] :
		my_partner = """<a class="text-info">No Partners available</a>"""
	else :
		my_partner = ""
		for partner in session['partner'] :
			#partner_username = ns.get_username_from_resolver(partner['workspace_contract'])
			#partner_username = 'Unknown' if partner_username is None else partner_username
			partner_username = partner['username']
			if partner['authorized'] == 'Pending' :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner_username + """">"""+ partner_username + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
					<a class="text-secondary" href="/user/reject_partner/?partner_username=""" + partner_username+"""&amp;partner_workspace_contract=""" + partner['workspace_contract']+"""">
						<i data-toggle="tooltip" class="fa fa-thumbs-o-down" title="Reject this Partnership.">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/authorize_partner/?partner_username=""" + partner_username + """&amp;partner_workspace_contract=""" + partner['workspace_contract']+ """">
						<i data-toggle="tooltip" class="fa fa-thumbs-o-up" title="Authorize this Parnership."></i>
					</a>
				</spn>"""
			elif partner['authorized'] == 'Removed' :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner_username + """">"""+ partner_username + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
				</spn>"""
			else :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner_username + """">"""+ partner_username + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
					<a class="text-secondary" href="/user/remove_partner/?partner_username=""" + partner_username +"""&amp;partner_workspace_contract=""" + partner['workspace_contract']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove this Partnership.">&nbsp&nbsp&nbsp</i>
				</spn>"""
			my_partner = my_partner + partner_html + """<br>"""


	# Issuer for document, they have an ERC725 key 20002
	if session['issuer'] == [] :
		my_issuer = """  <a class="text-info">No Referents available</a>"""
	else :
		my_issuer = ""
		for one_issuer in session['issuer'] :
			issuer_username = ns.get_username_from_resolver(one_issuer['workspace_contract'], mode)
			issuer_username = 'Unknown' if issuer_username is None else issuer_username
			issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_issuer/?issuer_username="""+issuer_username +"""&amp;issuer_address="""+one_issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span>"""
			my_issuer = my_issuer + issuer_html + """<br>"""


	# whitelist
	if session['whitelist'] == [] :
		my_white_issuer = """  <a class="text-info">No Whitelist available</a>"""
	else :
		my_white_issuer = ""
		for issuer in session['whitelist'] :
			issuer_username = ns.get_username_from_resolver(issuer['workspace_contract'], mode)
			issuer_username = 'Unknown' if issuer_username is None else issuer_username
			issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_white_issuer/?issuer_username="""+issuer_username +"""&amp;issuer_address="""+issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span>"""
			my_white_issuer = my_white_issuer + issuer_html + """<br>"""

	return render_template('advanced.html',
							**session['menu'],
							access=my_access,
							partner=my_partner,
							issuer=my_issuer,
							whitelist=my_white_issuer,
							advanced=my_advanced)

# account settings
def user_account(mode) :
	check_login()
	if directory.search_user(mode, session):
		checkBox = "checked"
	else:
		checkBox = ""
	if request.args.get('success') == 'true' :
		if session['type'] == 'person' :
			flash('Picture has been updated', 'success')
		else :
			flash('Logo has been updated', 'success')
	return render_template('account.html',
							**session['menu'],
							checkBox = checkBox)
