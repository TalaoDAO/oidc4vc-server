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
import user_search


exporting_threads = {}

# Multithreading creatidentity setup
class ExportingThread(threading.Thread):
	def __init__(self, username, firstname, lastname, email, phone, mode):
		super().__init__()
		self.username = username
		self.firstname = firstname
		self.lastname = lastname
		self.email = email
		self.phone = phone
		self.mode = mode
	def run(self):
		workspace_contract = createidentity.create_user(self.username, self.email, self.mode)[2]
		if workspace_contract is None :
			print('Thread to create new Identity failed')
			return
		claim = Claim()
		claim.relay_add(workspace_contract, 'firstname', self.firstname, 'public', self.mode)
		claim = Claim()
		claim.relay_add(workspace_contract, 'lastname', self.lastname, 'public', self.mode)
		ns.update_phone(self.username, self.phone, self.mode)
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
		user_search.add_user(session['firstname'] + ' ' + session['lastname'], session['username'])
		if not sms.check_phone(session['phone'], mode) :
			return render_template("create.html",message='Incorrect phone number')
		else :
			session['code'] = str(random.randint(10000, 99999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 180)
			session['try_number'] = 1
			sms.send_code(session['phone'], session['code'], mode)
			#Talao_message.messageAuth(email, str(code), mode)
			print('secret code = ', session['code'])
			return render_template("create2.html", message = '')

# route /register/authentification/
def POST_authentification_2(mode) :
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
		exporting_threads[thread_id] = ExportingThread(session['username'], session['firstname'], session['lastname'], session['email'], session['phone'], mode)
		print("appel de createidentity")
		exporting_threads[thread_id].start()
		return render_template("create3.html", message='Registation in progress. You will receive an email with your credentials soon.')
	elif session['try_number'] > 3 :
		return render_template("create3.html", message="Too many trials (3 max)")
	elif datetime.now() > session['code_delay'] :
		return render_template("create3.html", message="Code expired")
	else :
		return render_template("create2.html", message='This code is incorrect')
