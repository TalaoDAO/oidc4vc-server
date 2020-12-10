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
import createidentity
import sms
from protocol import Claim
import ns
import directory


exporting_threads = {}

# Multithreading creatidentity setup
class ExportingThread(threading.Thread):
	def __init__(self, username, firstname, lastname, email, phone, password, search, mode):
		super().__init__()
		self.username = username
		self.firstname = firstname
		self.lastname = lastname
		self.email = email
		self.phone = phone
		self.password = password
		self.search = search
		self.mode = mode
		self.password = password
	def run(self):
		workspace_contract = createidentity.create_user(self.username, self.email, self.mode, password=self.password)[2]
		if workspace_contract is None :
			print('Error : thread to create new Identity failed')
			return
		claim = Claim()
		claim.relay_add(workspace_contract, 'firstname', self.firstname, 'public', self.mode)
		claim = Claim()
		claim.relay_add(workspace_contract, 'lastname', self.lastname, 'public', self.mode)
		ns.update_phone(self.username, self.phone, self.mode)
		ns.update_password(self.username, self.password, self.mode)
		if self.search:
			directory.add_user(self.mode, self.username, self.firstname+ ' ' + self.lastname, None)
		return

# route /register/
def authentification(mode) :
	session.clear()
	if request.method == 'GET' :
		return render_template("create.html",message='')
	if request.method == 'POST' :
		session['email'] = request.form['email']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['phone'] = request.form['code'] + request.form['phone']
		try:
			if request.form["CheckBox"] == "on":
				session['search'] = True
		except:
			session['search'] = False
		if not sms.check_phone(session['phone'], mode) :
			return render_template("create.html", message_class='text-danger', message='Incorrect phone number')
		else :
			return render_template("create_password.html")

# route /register/password
def authentification_password(mode):
	session['password'] = request.form['password']
	session['code'] = str(random.randint(10000, 99999))
	session['code_delay'] = datetime.now() + timedelta(seconds= 180)
	session['try_number'] = 1
	sms.send_code(session['phone'], session['code'], mode)
	#Talao_message.messageAuth(email, str(code), mode)
	print('secret code = ', session['code'])
	return render_template("create2.html", message = '')

# route /register/authentification/
def POST_authentification_2(mode) :
	mycode = request.form['mycode']
	if not session.get('code') :
		flash('Registration error', 'warning')
		return redirect(mode.server + 'login/')
	session['try_number'] +=1
	print('Warning : code received = ', mycode)
	authorized_codes = [session['code'], '123456'] if mode.test else [session['code']]
	if mycode in authorized_codes and datetime.now() < session['code_delay'] and session['try_number'] < 4 :
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(session['username'], session['firstname'],
		 											   session['lastname'], session['email'],
													   session['phone'], session['password'],
													   session['search'], mode)
		print("Warning : call createidentity")
		exporting_threads[thread_id].start()
		return render_template("create3.html", message_class='text-info', message='Registation in progress. You will receive an email with your credentials soon.')
	elif session['try_number'] > 3 :
		return render_template("create4.html", message_class='text-danger', message="Too many trials (3 max)")
	elif datetime.now() > session['code_delay'] :
		return render_template("create4.html", message_class='text-danger', message="Code expired")
	else :
		if session['try_number'] == 2 :
			message = 'Code is incorrect, 2 trials left'
		if session['try_number'] == 3 :
			message = 'Code is incorrect, last trial'
		return render_template("create2.html", message_class='text-danger', message=message)

#@app.route('/register/update_password/', methods=['GET'])
def register_update_password(mode) :
	global exporting_threads
	thread_id = str(random.randint(0,10000 ))
	exporting_threads[thread_id] = ExportingThread(session['username'], session['firstname'], session['lastname'], session['email'], session['phone'], request.form['password'], session['search'], mode)
	print("Warning : appel de createidentity")
	exporting_threads[thread_id].start()
	session.clear()
	return render_template("create3.html", message_class='text-info', message='Registation in progress. You will receive an email with your credentials soon.')
