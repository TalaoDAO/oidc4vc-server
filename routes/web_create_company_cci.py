"""
Just a threading process to create user.

centralized url

app.add_url_rule('/register/',  view_func=web_create_identity.authentification, methods = ['GET', 'POST'])
app.add_url_rule('/register/code/', view_func=web_create_identity.POST_authentification_2, methods = ['POST'])
"""

from flask import request, redirect, render_template, session, flash
import random
import unidecode
from datetime import timedelta, datetime

# dependances
from components import Talao_message, ns, directory
from factory import createcompany

# route /create_company_cci/
def cci(mode) :
	session.clear()
	print('referrer = ', request.referrer)
	if request.method == 'GET' :
		whitelist = ['http://127.0.0.1:5000/profile',
					'http://masociete.co/',
					'http://127.0.0.1:4000/',
					mode.server + 'create_company_cci/',
					mode.server + 'create_company_cci/password/',
					mode.server + 'create_company_cci/code/',]
		if request.referrer in whitelist:
			return render_template("CCI/create_company_cci.html",message='')
		else:
			#flash('Incorrect referrer, you do not have access to this page', 'warning')
			print('Error : CCI incorrect referrer')
			return redirect('/register/')
	if request.method == 'POST' :
		session['email'] = request.form['email']
		session['name'] = request.form['name']
		session['username'] = request.form['name'].lower()
		if ns.username_exist(session['username'], mode)   :
			session['username'] = session['username'] + str(random.randint(1, 100))
		session['siren'] = request.form['siren']
		return render_template("CCI/create_company_cci_password.html")

# route /create_company_cci/password/
def cci_password(mode):
	if not session.get('email') :
		return redirect(mode.server + 'create_company_cci/')
	session['password'] = request.form['password']
	session['code'] = str(random.randint(10000, 99999))
	session['code_delay'] = datetime.now() + timedelta(seconds= 180)
	session['try_number'] = 0
	subject = 'Talao : Email authentification  '
	Talao_message.messageHTML(subject, session['email'], 'code_auth', {'code' : session['code']}, mode)
	print("Warning : code sent =" + session['code'])
	return render_template("CCI/create_company_cci_code.html", message_class='text-info', message = '')

# route /create_company_cci/code/
def cci_code(mode) :
	if not session.get('code') :
		return redirect(mode.server + 'create_company_cci/')
	mycode = request.form['mycode']
	session['try_number'] +=1
	print('Warning : returned code = ', mycode)
	authorized_codes = [session['code'], '123456'] if mode.test else [session['code']]
	if mycode in authorized_codes and datetime.now() < session['code_delay'] and session['try_number'] < 4 :
		print("Info : call of createidentity")
		workspace_contract = createcompany.create_company(session['email'], session['username'], mode, password=session['password'], name=session['name'], siren=session['siren'])[2]
		if workspace_contract :
			directory.add_user(mode, session['name'], session['username'], session['siren'])
			return render_template("CCI/create3_cci.html", username=session['username'])
		else :
			return render_template("CCI/create4_cci.html", message_class ="text-danger", message="Echec du déploiement de l'Identité.")
	elif session['try_number'] == 3 :
		return render_template("CCI/create4_cci.html", message="Nombre d'essais maximum atteint (3 max)")
	elif datetime.now() > session['code_delay'] :
		return render_template("CCI/create4_cci.html", message="Code expiré")
	else :
		if session['try_number'] == 1 :
			message = 'Code incorrect, encore 2 essais'
		if session['try_number'] == 2 :
			message = 'Code incorrect, dernier essai'
		return render_template("CCI/create_company_cci_code.html", message_class='text-danger', message=message)

# route /create_company_cci/post_code/
def cci_post_code(mode) :
	if not 'username' in session :
		return redirect(mode.server + 'create_company_cci/')
	if request.method == 'POST' :
		return redirect (mode.server + 'login/?username=' + session['username'])
