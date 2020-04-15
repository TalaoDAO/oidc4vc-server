
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
from protocol import canRegister_email
import environment

# environment setup
mode=environment.currentMode()
w3=mode.w3
exporting_threads = {}
	
# Multithreading de creatidentity setup   https://stackoverflow.com/questions/24251898/flask-app-update-progress-bar-while-function-runs
class ExportingThread(threading.Thread):
	def __init__(self, firstname, lastname, email, mode):
		self.progress = 0
		super().__init__()
		self.firstname=firstname
		self.lastname=lastname
		self.email=email
		self.mode=mode
	def run(self):
		createidentity.creationworkspacefromscratch(self.firstname, self.lastname, self.email,self.mode)	

# centralized URL dans webserver.py https://flask.palletsprojects.com/en/1.1.x/patterns/lazyloading/
def authentification() :
	session.clear()
	return render_template("create.html",message='')

### recuperation de l email, nom et prenom
def POST_authentification_1() :
	email = request.form['email']
	firstname=request.form['firstname']
	lastname=request.form['lastname']
	# stocké en session
	session['firstname']=request.form['firstname']
	session['lastname']=request.form['lastname']
	session['email']=email
	# check si email disponible
	if canRegister_email(email,mode) == False :
		return render_template("home.html", message = 'Email already used')	
	# envoi du code secret par email
	if session.get('code') == None :
		code = str(random.randint(100000, 999999))
		session['try_number']=1
		session['code']=code
		# envoi message de control du code
		Talao_message.messageAuth(email, str(code))
		print('code secret envoyé= ', code)
	else :
		print("le code a deja ete envoye")
	
	return render_template("create2.html", message = '')

# recuperation du code saisi
def POST_authentification_2() :
	global exporting_threads
	email=session.get('email')
	lastname=session.get('lastname')
	firstname=session.get('firstname')
	mycode = request.form['mycode']
	# on verifie que le user n a pas
	if session.get('code')== False : 
		return "renvoyer au login"
	session['try_number'] +=1
	print('code retourné = ', mycode)
	print (session)
	if mycode == session.get('code') :
		print('code correct')
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(firstname, lastname, email, mode)
		print("appel de createindentty")
		#exporting_threads[thread_id].start()
		mymessage = 'Registation in progress. You will receive an email with details soon.' 
	else :
		if session['try_number'] > 3 :
			mymessage = "Too many trials (3 max)"
			return render_template("create3.html", message = mymessage)

		mymessage = 'This code is incorrect'
		return render_template("create2.html", message = mymessage)

	return render_template("create3.html", message = mymessage)

		
def POST_authentification_3() :
	return redirect(mode.server+'talao/register/')
	
