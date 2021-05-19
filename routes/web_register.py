"""
Just a process to a centralized basic create user from password and username

"""
from flask import request, redirect, render_template, session, flash, abort
import random
import requests
import json
from datetime import timedelta, datetime
import logging
logging.basicConfig(level=logging.INFO)

from factory import createidentity
from components import sms,directory,ns

def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if not session.get('workspace_contract') and not session.get('username') :
		logging.warning('Check login failed, call abort 403')
		abort(403)
	else :
		return True


# route /register/
def register(mode) :
	if request.method == 'GET' :
		session.clear()
		session['is_active'] = True
		message = request.args.get('message', "")
		return render_template("/register/register.html",message=message, )
	if request.method == 'POST' :
		session['email'] = request.form['email']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['phone'] = request.form['phone']
		session['search_directory'] = request.form.get('CheckBox')
		if sms.check_phone(session['phone'], mode) :
			return redirect (mode.server + 'register/identity/')
		else :
			return render_template("/register/register.html",
									message='Incorrect phone number.',
									firstname=session['firstname'],
									lastname=session['lastname'],
									email=session['email'])


def register_identity(mode) :
	""" FIXME si le did est perso, voir ce que l'on fait de la cle qui est en  localstorage
	"""
	if request.method == 'GET' :
		session['server'] = mode.server
		return render_template("/register/register_identity.html")
	if request.method == 'POST' :
		if request.form['did'] == "own" :
			session['did'] = request.form['own_did']
			if session['did'].split(':')[1]  == 'tz' :
				try :
					didkit.resolveDID(session['did'],'{}')
				except :
					flash('DID resolution has been rejected by Universal Resolver.', 'warning')
					return render_template("/register/register_identity.html")
			else  :
				r = requests.get('https://dev.uniresolver.io/1.0/identifiers/' + session['did'])
				if r.status_code != 200 :
					flash('DID resolution has been rejected by Universal Resolver.', 'warning')
					return render_template("/register/register_identity.html")
		else :
			session['did'] = request.form['did']
		return redirect (mode.server + 'register/password/')


# route /register/password/
def register_password(mode):
	if not session.get('is_active') :
		return redirect(mode.server + 'register/?message=Session+expired.')
	if request.method == 'GET' :
		return render_template("/register/register_password.html")
	if request.method == 'POST' :
		session['password'] = request.form['password']
		session['code'] = str(random.randint(100000, 999999))
		session['code_delay'] = datetime.now() + timedelta(seconds= 180)
		session['try_number'] = 0
		try :
			sms.send_code(session['phone'], session['code'], mode)
		except :
			logging.error('sms connexion probleme register_password')
			return render_template("register.html",message='SMS connexion problem.', )
		logging.info('secret code = %s', session['code'])
		return render_template("/register/register_code.html")


# route /register/code/
def register_code(mode) :
	if not session.get('is_active') or 'try_number' not in session :
		return redirect(mode.server + 'register/?message=Session+expired.')
	session['try_number'] +=1
	logging.info('code received = %s', request.form['mycode'])
	if request.form['mycode'] == session['code'] and datetime.now() < session['code_delay'] and session['try_number'] < 4 :

		if not createidentity.create_user(session['username'],
										session['email'],
										mode,
										did=session['did'],
										firstname=session['firstname'],
										lastname=session['lastname'],
										phone=session['phone'],
										password=session['password'])[2] :
			logging.error('createidentity failed')
			return render_template("/register/register.html",message='Connexion problem.', )

		if session['search_directory'] :
			directory.add_user(mode, session['username'], session['firstname'] + ' ' + session['lastname'], None)
			logging.warning('directory updated with firstname and lastname')
		# success exit
		return render_template("/register/end_of_registration.html", username=session['username'])
	elif session['try_number'] == 3 :
		session['is_active'] = False
		return render_template("/register/registration_error.html", message="Code is incorrect. Too many trials.")
	elif datetime.now() > session['code_delay'] :
		session['is_active'] = False
		return render_template("/register/registration_error.html",  message="Code expired.")
	else :
		if session['try_number'] == 1 :
			message = 'Code is incorrect, 2 trials left.'
		if session['try_number'] == 2 :
			message = 'Code is incorrect, last trial.'
		return render_template("/register/register_code.html", message=message)


# route register/post_code/
def register_post_code(mode) :
	try :
		username = session['username']
		session.clear()
		return redirect (mode.server + 'login/?username=' + username)
	except :
		return redirect (mode.server + 'login/')