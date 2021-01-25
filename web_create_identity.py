"""
Just a threading process to create user.

centralized url

app.add_url_rule('/register/',  view_func=web_create_identity.authentification, methods = ['GET', 'POST'])
app.add_url_rule('/register/code/', view_func=web_create_identity.POST_authentification_2, methods = ['POST'])
"""

from flask import request, redirect, render_template, session, flash
import random
import unidecode
import time
from datetime import timedelta, datetime

# dependances
import Talao_message
import createidentity
import sms
from protocol import Claim
import ns
import directory

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
		#session['phone'] = request.form['code'] + request.form['phone']
		session['phone'] = request.form['phone']
		session['search'] = request.form.get('CheckBox')
		try :
			if not sms.check_phone(session['phone'], mode) :
				return render_template("register.html", message='Incorrect phone number.',
												firstname=session['firstname'],
												lastname=session['lastname'],
												email=session['email'])
			else :
				return redirect (mode.server + 'register/password/')
		except :
			return render_template("register.html",message='SMS connexion problem.', )


# register ID with your wallet in Talao Identity
#@app.route('/wc_register/', methods = ['GET', 'POST'])
def wc_register(mode) :
	if request.method == 'GET' :
		session.clear()
		session['is_active'] = True
		message = request.args.get('message', "")
		session['wallet_address']= request.args.get('wallet_address')
		# lets t see if this wallet address is an alias of an Identity
		if ns.get_username_from_wallet(session['wallet_address'], mode) :
			del session['wallet_address']
			flash('This wallet account is already used for an Idcentity.', 'warning')
			return render_template ('login.html')
		print('wallet address = ', session['wallet_address'])
		return render_template('wc_register.html', message=message, wallet_address=session['wallet_address'])
	if request.method == 'POST' :
		session['email'] = request.form['email']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['search'] = request.form.get('CheckBox')
		workspace_contract = createidentity.create_user(session['username'],
											session['email'],
											mode,
											firstname=session['firstname'],
											lastname=session['lastname'],
											wallet=session['wallet_address']
											)[2]
		if not workspace_contract :
			print('Error : createidentity failed')
			return render_template("wc_register.html",message='Connexion problem.', )
		if session['search'] :
			directory.add_user(mode, session['username'], session['firstname']+ ' ' + session['lastname'], None)
			print('Warning : directory updated with firstname and lastname')
		session['is_active'] = False
		return render_template("create3.html", username=session['username'])

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
		sms.send_code(session['phone'], session['code'], mode)
		print('Info : secret code = ', session['code'])
		return render_template("register_code.html")

# route /register/code/
def register_code(mode) :
	if not session.get('is_active') or 'try_number' not in session :
		return redirect(mode.server + 'register/?message=session+expired.')
	mycode = request.form['mycode']
	session['try_number'] +=1
	print('Warning : code received = ', mycode)
	authorized_codes = [session['code'], '123456'] if mode.test else [session['code']]
	if mycode in authorized_codes and datetime.now() < session['code_delay'] and session['try_number'] < 4 :
		print("Warning : call createidentity")
		workspace_contract = createidentity.create_user(session['username'],
											session['email'],
											mode,
											firstname=session['firstname'],
											lastname=session['lastname'],
											phone=session['phone'],
											password=session['password'])[2]
		if not workspace_contract :
			print('Error : createidentity failed')
			return render_template("register.html",message='Connexion problem.', )
		if session['search'] :
			directory.add_user(mode, session['username'], session['firstname']+ ' ' + session['lastname'], None)
			print('Warning : directory updated with firstname and lastname')
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


# route register/post_code/
def register_post_code(mode) :
	return redirect (mode.server + 'login/?username=' + session['username'])
