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
			print('Thread to create new Identity failed')
			return
		claim = Claim()
		claim.relay_add(workspace_contract,'name', self.name, 'public', self.mode)
		claim = Claim()
		claim.relay_add(workspace_contract,'siren', self.siren, 'public', self.mode)
		ns.update_password(self.username, self.password, self.mode)
		directory.add_user(self.mode, self.name, self.username, self.siren)
		return

# route /create_company_ext
def authentification_company(mode) :
	session.clear()
	if request.method == 'GET' :
		try:
			referer = request.environ['HTTP_REFERER']
		except KeyError:
			referer = None
		whitelist = ['http://127.0.0.1:5000/profile', 'masociete.com', 'http://127.0.0.1:4000']
		if referer in whitelist:
			return render_template("create_company/create_company_ext.html",message='')
		else:
			flash('Incorrect referer, you do not have access to this page', 'warning')
			return redirect("/login")
	if request.method == 'POST' :
		session['email'] = request.form['email']
		session['name'] = request.form['name']
		company_username = request.form['name'].lower()
		if ns.username_exist(company_username, mode)   :
			company_username = company_username + str(random.randint(1, 100))
		session['username'] = company_username
		session['siren'] = request.form['siren']
		return render_template("create_company/create_company_ext_password.html")

# route /create_company_ext/password
def authentification_password_company(mode):
	session['password'] = request.form['password']
	session['code'] = str(random.randint(10000, 99999))
	session['code_delay'] = datetime.now() + timedelta(seconds= 180)
	session['try_number'] = 1
	sent = Talao_message.messageAuth(session['email'], session['code'], mode)
	print("Message sent ? " + str(sent))
	#Talao_message.messageAuth(email, str(code), mode)
	print('secret code = ', session['code'])
	return render_template("create_company/create_company_ext_code.html", message = '')

# route /create_company_ext/authentification/
def POST_authentification_2_company(mode) :
	global exporting_threads
	mycode = request.form['mycode']
	if not session.get('code') :
		flash('Registration error', 'warning')
		return redirect(mode.server + 'login/')
	session['try_number'] +=1
	print('code retourné = ', mycode)
	authorized_codes = [session['code'], '123456'] if mode.test else [session['code']]
	if mycode in authorized_codes and datetime.now() < session['code_delay'] and session['try_number'] < 4 :
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(session['username'], session['name'],
		 											   session['email'], session['password'],
													   session['siren'], mode)
		print("appel de createidentity")
		exporting_threads[thread_id].start()
		return render_template("create3.html", message='Registation in progress. You will receive an email with your credentials soon.')
	elif session['try_number'] > 3 :
		return render_template("create3.html", message="Too many trials (3 max)")
	elif datetime.now() > session['code_delay'] :
		return render_template("create3.html", message="Code expired")
	else :
		return render_template("create_company/create_company_ext_code.html", message='This code is incorrect')
