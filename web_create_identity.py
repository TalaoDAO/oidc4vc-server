
"""	
#####################################################
#   CREATION IDENTITE ONLINE (html) pour le site talao.io
#####################################################

le user reçoit par email les informations concernant son identité
Talao dispose d'une copie de la clé
On test si l email existe dans le registre

centralized url https://flask.palletsprojects.com/en/1.1.x/patterns/lazyloading/
"""

from flask import request, redirect, render_template, session
#from flask_api import FlaskAPI
import threading
import random

# dependances
import Talao_message
import createidentity
from protocol import canRegister_email, address
import environment

# environment setup
mode = environment.currentMode()
w3 = mode.w3
exporting_threads = {}
	
# Multithreading creatidentity setup   https://stackoverflow.com/questions/24251898/flask-app-update-progress-bar-while-function-runs
class ExportingThread(threading.Thread):
	def __init__(self, username, email, mode):
		super().__init__()
		self.username = username
		self.email = email
		self.mode = mode
	def run(self):
		createidentity.creationworkspacefromscratch(self.username, self.email,self.mode)	

# centralized URL in webserver.py https://flask.palletsprojects.com/en/1.1.x/patterns/lazyloading/
def authentification() :
	session.clear()
	return render_template("create.html",message='')

### recuperation de l email et username
def POST_authentification_1() :
	email = request.form['email']
	username = request.form['username']
	session['username'] = username
	session['email'] = email
	# check if email and username available
	if not canRegister_email(email,mode) :
		return render_template("create.html", message = 'Email already used')	
	if address(username, mode.register) is not None :	
		return render_template("create.html", message = 'Username already used')	
	# secret code sent by email
	if session.get('code') is None :
		code = str(random.randint(100000, 999999))
		session['try_number'] = 1
		session['code'] = code
		Talao_message.messageAuth(email, str(code))
		print('secret code = ', code)
	else :
		print("secret code already sent")
	
	return render_template("create2.html", message = '')

# recuperation du code saisi
def POST_authentification_2() :
	global exporting_threads
	email = session.get('email')
	username = session.get('username')
	mycode = request.form['mycode']
	# 
	if not session.get('code') : 
		return "renvoyer au login"
	session['try_number'] +=1
	print('code retourné = ', mycode)
	print (session)
	if mycode == session.get('code') :
		print('code correct')
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(username, email, mode)
		print("appel de createindentty")
		#TEST a retirer exporting_threads[thread_id].start() pour les Tests
		mymessage = 'Registation in progress. You will receive an email with details soon.' 
	else :
		if session['try_number'] > 3 :
			mymessage = "Too many trials (3 max)"
			return render_template("create3.html", message=mymessage)

		mymessage = 'This code is incorrect'
		return render_template("create2.html", message=mymessage)

	return render_template("create3.html", message=mymessage)

		
def POST_authentification_3() :
	return redirect(mode.server+'talao/register/')
	
