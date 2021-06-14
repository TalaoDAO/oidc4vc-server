"""
Just a process to a centralized basic create user from password and username

"""
from flask import request, redirect, render_template, session, flash, abort
import random
import json
import didkit
import requests
from datetime import timedelta, datetime
import logging
logging.basicConfig(level=logging.INFO)

from factory import createidentity, createcompany
from components import sms, directory, ns, company


CREDENTIAL_TOPIC = ['experience', 'training', 'recommendation', 'work', 'salary', 'vacation', 'internship', 'relocation', 'end_of_work', 'hiring']


def init_app(app, mode) :
	app.add_url_rule('/hrid/register',  view_func=hrid_register_user, methods = ['GET', 'POST'], defaults={'mode': mode}) # idem below
	app.add_url_rule('/hrid/register/user',  view_func=hrid_register_user, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/hrid/register/company',  view_func=hrid_register_company, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/hrid/register/password',  view_func=hrid_register_password, methods = [ 'GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/hrid/register/code', view_func=hrid_register_code, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/hrid/register/post_code', view_func=hrid_register_post_code, methods = ['POST', 'GET'], defaults={'mode': mode})
	return


def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if not session.get('workspace_contract') and not session.get('username') :
		logging.warning('Check login failed, call abort 403')
		abort(403)
	else :
		return True


def hrid_register_company(mode) :
	if request.method == 'GET' :
		return render_template('hrid/company_register_fr.html')
	if request.method == 'POST' :
		credentials_supported = list()
		credentials_supported_dict = dict()
		for topic in CREDENTIAL_TOPIC :
			if request.form.get(topic) :
				credentials_supported.append(request.form[topic])
				credentials_supported_dict[topic] = request.form[topic]
		if not request.form.get('CheckBox') :
			message = "Acceptez les conditions générales d'utilisation (CGU) pour continuer."
		if not sms.check_phone(request.form['contact_phone'], mode) :
			message = 'Numéro de téléphone incorrect.'
		if message :
			return render_template("/hrid/company_register_fr.html",
									company_name=request.form['company_name'],
									contact_name=request.form['contact_name'],
									contact_email=request.form['contact_email'],
									siren=request.form['siren'],
									contact_phone=request.form['contact_phone'],
									postal_address=request.form['postal_address'],
									website=request.form['website'],
									**credentials_supported_dict,
									message=message)

		username = request.form['company_name'].lower()
		if ns.username_exist(username, mode)   :
			username = username + str(random.randint(1, 100))
		if request.form['promo'] in ["TEST"] :
			promo = 50
		else :
			promo = 10
		workspace_contract =  createcompany.create_company(request.form['contact_email'],username, None, mode)[2]
		if workspace_contract :
			directory.add_user(mode, request.form['company_name'], username, request.form['siren'])
			filename = mode.db_path + 'company.json'
			personal = json.load(open(filename, 'r'))
			personal['contact_name']['claim_value'] = request.form['contact_name']
			personal['name']['claim_value'] = request.form['company_name']
			personal['contact_email']['claim_value'] = request.form['contact_email']
			personal['contact_phone']['claim_value'] = request.form['contact_phone']
			personal['website']['claim_value'] = request.form['website']
			personal['siren']['claim_value'] = request.form['siren']
			personal['postal_address']['claim_value'] = request.form['postal_address']
			personal['credentials_supported'] = credentials_supported
			personal['credential_counter'] = 0
			personal['credential_acquired'] = promo
			ns.update_personal(workspace_contract, json.dumps(personal, ensure_ascii=False), mode)
			# init first campaign
			new_campaign = company.Campaign(session['username'], mode)
			data = {'description' : request.form['description'],
					'nb_subject' : 0,
					'startDate' : '',
					'endDate' : '',
					'credentials_supported' : credentials_supported}
			campaign_code = "camp" +  str(random.randint(100, 999))
			new_campaign.add(campaign_code  , json.dumps(data, ensure_ascii=False))
			return render_template('hrid/company_end_of_registration_fr.html', campaign_code=campaign_code)
		else :
			flash('Echec de la création du compte', 'danger')
			return redirect(mode.server + 'hrid/register/company')


def hrid_register_user(mode) :
	if request.method == 'GET' :
		session.clear()
		session['is_active'] = True
		message = request.args.get('message', "")
		return render_template("/hrid/user_register_fr.html",message=message, myenv=mode.server)

	if request.method == 'POST' :
		session['email'] = request.form['email']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['phone'] = request.form['phone']
		session['did'] = request.form['did']
		if not request.form.get('CheckBox') :
			return render_template("/hrid/user_register_fr.html",
									message="Acceptez les conditions générales d'utilisation (CGU) pour continuer.",
									firstname=session['firstname'],
									lastname=session['lastname'],
									email=session['email'])
		if sms.check_phone(session['phone'], mode) :
			return redirect (mode.server + 'hrid/register/password')

		else :
			return render_template("/hrid/user_register_fr.html",
									message='Numéro de téléphone incorrect.',
									firstname=session['firstname'],
									lastname=session['lastname'],
									email=session['email'])


def hrid_register_password(mode):
	if not session.get('is_active') :
		return redirect(mode.server + 'hrid/register?message=Session+expirée.')
	if request.method == 'GET' :
		return render_template("/hrid/register_password_fr.html")
	if request.method == 'POST' :
		session['password'] = request.form['password']
		session['code'] = str(random.randint(100000, 999999))
		session['code_delay'] = datetime.now() + timedelta(seconds= 180)
		session['try_number'] = 0
		try :
			sms.send_code(session['phone'], session['code'], mode)
		except :
			logging.error('sms connexion probleme register_password')
			return render_template("hrid/user_register_fr.html",message='SMS connexion problem.', )
		logging.info('secret code = %s', session['code'])
		return render_template("/hrid/register_code_fr.html")


# route /register/code/
def hrid_register_code(mode) :
	if not session.get('is_active') or 'try_number' not in session :
		return redirect(mode.server + 'register?message=Session+expirée.')
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
			return render_template("/hrid/register_fr.html",message='Echec de connexion.', )

		directory.add_user(mode, session['username'], session['firstname'] + ' ' + session['lastname'], None)
		ns.update_phone(session['username'], session['phone'], mode)
		return render_template("/hrid/end_of_registration_fr.html", username=session['username'])

	elif session['try_number'] == 3 :
		session['is_active'] = False
		return render_template("/hrid/registration_error_fr.html", message="Code incorrect. Nombre maximum de tentatives atteint.")
	elif datetime.now() > session['code_delay'] :
		session['is_active'] = False
		return render_template("/hrid/registration_error_fr.html",  message="Code expiré.")
	else :
		if session['try_number'] == 1 :
			message = 'Code incorrect, encore 2 essais.'
		if session['try_number'] == 2 :
			message = 'Code incorrect, dernier essai.'
		return render_template("/hrid/register_code_fr.html", message=message)


# route register/post_code
def hrid_register_post_code(mode) :
	try :
		username = session['username']
		session.clear()
		return redirect (mode.server + 'login?username=' + username)
	except :
		return redirect (mode.server + 'login')