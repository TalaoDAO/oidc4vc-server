"""
Just a threading process to create user.

centralized url

app.add_url_rule('/register/',  view_func=web_create_identity.authentification, methods = ['GET', 'POST'])
app.add_url_rule('/register/code/', view_func=web_create_identity.POST_authentification_2, methods = ['POST'])
"""

from flask import request, redirect, render_template, session, flash
#import threading
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


#exporting_threads = {}

"""
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
		if not workspace_contract :
			print('Error : thread to create new Identity failed')
			return
		Claim().relay_add(workspace_contract, 'firstname', self.firstname, 'public', self.mode)
		Claim().relay_add(workspace_contract, 'lastname', self.lastname, 'public', self.mode)
		ns.update_phone(self.username, self.phone, self.mode)
		ns.update_password(self.username, self.password, self.mode)
		if self.search:
			directory.add_user(self.mode, self.username, self.firstname+ ' ' + self.lastname, None)
		return
"""

def synchronous_create_identity(username, firstname, lastname, email, phone, password, search, mode) :
	workspace_contract = createidentity.create_user(username, email, mode, password=password)[2]
	if not workspace_contract :
		print('Error : thread to create new Identity failed')
		return
	Claim().relay_add(workspace_contract, 'firstname', firstname, 'public', mode)
	Claim().relay_add(workspace_contract, 'lastname', lastname, 'public', mode)
	ns.update_phone(username, phone, mode)
	ns.update_password(username, password, mode)
	if search:
		directory.add_user(mode, username, firstname+ ' ' + lastname, None)
	return

# route /register/
def register(mode) :
	if request.method == 'GET' :
		session.clear()
		session['is_active'] = True
		message = request.args.get('message', "")
		return render_template("register.html",message=message, )
	if request.method == 'POST' :
		print('is active dans post ? ',session.get('is_active'))

		session['email'] = request.form['email']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['phone'] = request.form['code'] + request.form['phone']
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
		synchronous_create_identity(session['username'], session['firstname'], session['lastname'], session['email'], session['phone'], session['password'], session['search'], mode)
		"""
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(session['username'], session['firstname'],
		 											   session['lastname'], session['email'],
													   session['phone'], session['password'],
													   session['search'], mode)
		exporting_threads[thread_id].start()
		"""
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
