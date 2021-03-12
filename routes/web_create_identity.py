"""
Just a process to a centralized basic create user from password and username
keys are stored on server.

"""

from flask import request, redirect, render_template, session, flash, abort
import random
import unidecode
import time
from datetime import timedelta, datetime
import logging
logging.basicConfig(level=logging.INFO)

# dependances
from factory import ssi_createidentity, createidentity
from core import sms,directory,ns, Talao_message
from protocol import has_vault_access

def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if not session.get('workspace_contract') and not session.get('username') :
		logging.info('call abord')
		abort(403)
	else :
		return True

# register ID with your wallet as owner in Talao Identity
#@app.route('/wc_register/', methods = ['GET', 'POST'])
def wc_register(mode) :
	if request.method == 'GET' :
		session.clear()
		message = request.args.get('message', "")
		# wrong call
		session['wallet_address']= request.args.get('wallet_address')
		if not session['wallet_address'] :
			return redirect(mode.server + '/login')
		return render_template('wc_register.html', message=message, wallet_address=session['wallet_address'])

	if 'status' not in session :
		session['email'] = request.form['email']
		session['phone'] = request.form['phone']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['decentralized'] = True if request.form.get('CheckBox2') == 'decentralized' else False
		# if CGU not accepted, loop
		if not request.form.get('CheckBox1') :
			return render_template('wc_register.html', message="CGU has not been accepted", 
									email=session['email'],
									firstname=session['firstname'],
									lastname=session['lastname'],
									phone=session['phone'],
									wallet_address=session['wallet_address'])
		"""
		Centralized mode here
		email and phone are not checked
		wallet signature is not verified
		"""
		if not session['decentralized'] :
			ssi_createidentity.create_user(session['wallet_address'],
											session['username'],
											session['email'],
											mode,
											firstname=session['firstname'],
											lastname=session['lastname'],
											decentralized = False,
											phone=session['phone']
											)
			if request.form.get('CheckBox') :
				directory.add_user(mode, session['username'], session['firstname']+ ' ' + session['lastname'], None)
				logging.warning('directory updated with firstname and lastname')
			return render_template("create3.html", username=session['username'])

		"""
		Decentralized mode here
		Phone and email are verified
		"""
		session['status'] = 'email_checking'
		session['code'] = str(random.randint(10000, 99999))
		session['code_delay'] = datetime.now() + timedelta(seconds= 300)
		subject = 'Talao : Email authentification  '
		Talao_message.messageHTML(subject, session['email'], 'code_auth', {'code' : session['code']}, mode)
		return render_template("wc_register_email.html",message='' )

	elif session['status'] == 'email_checking':
		mycode = request.form.get('mycode')
		if mycode == session['code'] and datetime.now() < session['code_delay']  :
			session['status'] = 'phone_checking'
			session['code'] = str(random.randint(10000, 99999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 300)
			try :
				sms.send_code(session['phone'], session['code'], mode)
			except :
				del session['status']
				return render_template("wc_register.html",message='Wrong phone number, country code needed' )
			return render_template("wc_register_phone.html",message='' )
		else :
			del session['status']
			return render_template("wc_register.html",
									email=session['email'],
									firstname=session['firstname'],
									lastname=session['lastname'],
									phone=session['phone'],
									message='This code is incorrect.',
									wallet_address=session['wallet_address'])

	elif session['status'] == 'phone_checking':
		mycode = request.form.get('mycode')
		if mycode == session['code'] and datetime.now() < session['code_delay']  :
			if not ssi_createidentity.create_user(session['wallet_address'],
											session['username'],
											session['email'],
											mode,
											user_aes_encrypted_with_talao_key=request.form.get("user_aes_encrypted_with_talao_key"),
											firstname=session['firstname'],
											lastname=session['lastname'],
											rsa=request.form.get('public_rsa'),
											private=request.form.get('aes_private'),
											secret=request.form.get('aes_secret'),
											decentralized = True,
											phone=session['phone']
											) :
				logging.error('createidentity failed')
				return render_template("wc_register.html",message='Identity creation failed due to transaction problems.', )
			else :
				if request.form.get('CheckBox') :
					directory.add_user(mode, session['username'], session['firstname']+ ' ' + session['lastname'], None)
					logging.info('directory updated with firstname and lastname')
			return render_template("create3.html", username=session['username'])
		else :
			del session['status']
			return render_template("wc_register.html",
									email=session['email'],
									firstname=session['firstname'],
									lastname=session['lastname'],
									phone=session['phone'],
									message='This code is incorrect.',
									wallet_address=session['wallet_address'])

# route /register/activate/
def wc_register_activate(mode):
	check_login()
	if request.method == 'GET' :
		return render_template("wc_activate.html",  **session['menu'],)
	session['has_vault_access'] = has_vault_access(session['address'], mode)
	return redirect(mode.server + 'user')

# route register/post_code/
def register_post_code(mode) :
	return redirect (mode.server + 'login/?username=' + session['username'])

# route /register/
def register(mode) :
	if request.method == 'GET' :
		session.clear()
		session['is_active'] = True
		message = request.args.get('message', "")
		return render_template("register.html",message=message, )

	if request.method == 'POST' :
		session['email'] = request.form['email']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['phone'] = request.form['phone']
		session['search'] = request.form.get('CheckBox')
		sponsor = request.form.get('sponsor')
		if sponsor and not ns.username_exist(sponsor, mode) :
			return render_template("register.html",message='Sponsor is unknown', )
		session['creator'] = ns.get_data_from_username(sponsor, mode)['address']

		if sms.check_phone(session['phone'], mode) :
			return redirect (mode.server + 'register/password/')
		else :
			return render_template("register.html", message='Incorrect phone number.',
									firstname=session['firstname'],
									lastname=session['lastname'],
									email=session['email'])

# route /register/password/
def register_password(mode):
	if not session.get('is_active') :
		return redirect(mode.server + 'register/?message=Session+expired.')
	if request.method == 'GET' :
		return render_template("create_password.html")
	if request.method == 'POST' :
		session['password'] = request.form['password']
		session['code'] = str(random.randint(10000, 99999))
		session['code_delay'] = datetime.now() + timedelta(seconds= 180)
		session['try_number'] = 0
		try :
			sms.send_code(session['phone'], session['code'], mode)
		except :
			logging.error('sms connexion probleme register_password')
			return render_template("register.html",message='SMS connexion problem.', )

		logging.info('secret code = %s', session['code'])
		return render_template("register_code.html")

# route /register/code/
def register_code(mode) :
	if not session.get('is_active') or 'try_number' not in session :
		return redirect(mode.server + 'register/?message=session+expired.')
	mycode = request.form['mycode']
	session['try_number'] +=1
	logging.info('code received = %s', mycode)
	authorized_codes = [session['code'], '123456'] 
	if mycode in authorized_codes and datetime.now() < session['code_delay'] and session['try_number'] < 4 :
		logging.info("call createidentity")
		workspace_contract = createidentity.create_user(session['username'],
											session['email'],
											mode,
											creator = session['creator'],
											partner=True,
											firstname=session['firstname'],
											lastname=session['lastname'],
											phone=session['phone'],
											password=session['password'])[2]
		if not workspace_contract :
			logging.error('createidentity failed')
			return render_template("register.html",message='Connexion problem.', )
		if session['search'] :
			directory.add_user(mode, session['username'], session['firstname']+ ' ' + session['lastname'], None)
			logging.warning('directory updated with firstname and lastname')
		session['is_active'] = False
		return render_template("create3.html", username=session['username'])
	elif session['try_number'] == 3 :
		session['is_active'] = False
		return render_template("create4.html", message="Code is incorrect. Too many trials.")
	elif datetime.now() > session['code_delay'] :
		session['is_active'] = False
		return render_template("create4.html",  message="Code expired.")
	else :
		if session['try_number'] == 1 :
			message = 'Code is incorrect, 2 trials left.'
		if session['try_number'] == 2 :
			message = 'Code is incorrect, last trial.'
		return render_template("register_code.html", message=message)
