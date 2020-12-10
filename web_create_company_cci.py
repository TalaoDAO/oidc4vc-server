"""
Just a threading process to create user.

centralized url

app.add_url_rule('/register/',  view_func=web_create_identity.authentification, methods = ['GET', 'POST'])
app.add_url_rule('/register/code/', view_func=web_create_identity.POST_authentification_2, methods = ['POST'])
"""

from flask import request, redirect, render_template, session, flash
import threading
import random
import unidecode
from datetime import timedelta, datetime

# dependances
import Talao_message
import createcompany
from protocol import Claim
import ns
import directory


exporting_threads = {}

# Multithreading creatidentity setup
class ExportingThread(threading.Thread):
	def __init__(self, username, name, email, password, siren, mode):
		super().__init__()
		self.username = username
		self.name = name
		self.email = email
		self.siren = siren
		self.password = password
		self.mode = mode
	def run(self):
		workspace_contract = createcompany.create_company(self.email, self.username, self.mode)[2]
		if workspace_contract is None :
			print('Warning : CCI Thread to create new Identity failed')
			return
		claim = Claim()
		claim.relay_add(workspace_contract,'name', self.name, 'public', self.mode)
		claim = Claim()
		claim.relay_add(workspace_contract,'siren', self.siren, 'public', self.mode)
		ns.update_password(self.username, self.password, self.mode)
		directory.add_user(self.mode, self.username, self.name, self.siren)
		return

# route /create_company_cci
def authentification_company(mode) :
	session.clear()
	if request.method == 'GET' :
		whitelist = ['http://127.0.0.1:5000/profile', 'http://masociete.co/', 'http://127.0.0.1:4000/', mode.server+'create_company_cci/']
		if request.referrer in whitelist:
			return render_template("CCI/create_company_cci.html",message='')
		else:
			flash('Incorrect referrer, you do not have access to this page', 'warning')
			print('Error : CCI incorrect referrer')
			return redirect("/starter")
	if request.method == 'POST' :
		session['email'] = request.form['email']
		session['name'] = request.form['name']
		company_username = request.form['name'].lower()
		if ns.username_exist(company_username, mode)   :
			company_username = company_username + str(random.randint(1, 100))
		session['username'] = company_username
		session['siren'] = request.form['siren']
		return render_template("CCI/create_company_cci_password.html")

# route /create_company_cci/password
def authentification_password_company(mode):
	session['password'] = request.form['password']
	session['code'] = str(random.randint(10000, 99999))
	session['code_delay'] = datetime.now() + timedelta(seconds= 180)
	session['try_number'] = 1
	Talao_message.messageAuth(session['email'], session['code'], mode)
	print("Warning : code sent =" + session['code'])
	return render_template("CCI/create_company_cci_code.html", message_class='text-info', message = '')

# route /create_company_cci/authentification/
def POST_authentification_2_company(mode) :
	global exporting_threads
	mycode = request.form['mycode']
	if not session.get('code') :
		return redirect(mode.server + 'login/')
	session['try_number'] +=1
	print('Warning : returned code = ', mycode)
	authorized_codes = [session['code'], '123456'] if mode.test else [session['code']]
	if mycode in authorized_codes and datetime.now() < session['code_delay'] and session['try_number'] < 4 :
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(session['username'], session['name'], session['email'], session['password'],session['siren'], mode)
		print("Info : call of createidentity")
		exporting_threads[thread_id].start()
		return render_template("create3.html", message_class="text-info", message="Création de l'Identité en cours. Vous allez reçevoir un email avec votre code d'accès.")
	elif session['try_number'] > 3 :
		return render_template("create4.html", message_class ="text-danger", message="Nombre d'essais maximum atteint (3 max)")
	elif datetime.now() > session['code_delay'] :
		return render_template("create4.html", message_class ="text-danger", message="Code expiré")
	else :
		if session['try_number'] == 2 :
			message = 'Code is incorrect, 2 trials left'
		if session['try_number'] == 3 :
			message = 'Code is incorrect, last trial'
		return render_template("CCI/create_company_cci_code.html", message_class='text-danger', message=message)
