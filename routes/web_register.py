"""
Just a process to a centralized basic create user from password and username

"""
from flask import request, redirect, render_template, session, flash, abort, jsonify, Response, flash
import random
import json
import didkit
from flask_babel import _
from datetime import  datetime, timedelta
import uuid

import requests
from datetime import timedelta, datetime
import logging
logging.basicConfig(level=logging.INFO)

from factory import createidentity, createcompany
from components import sms, directory, ns, company

#PRESENTATION_DELAY = timedelta(seconds= 10*60)

DID = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'

CREDENTIAL_TOPIC = ['experience', 'training', 'recommendation', 'work', 'salary', 'vacation', 'internship', 'relocation', 'end_of_work', 'hiring']


def init_app(app, red, mode) :
	app.add_url_rule('/register/identity',  view_func= register_identity, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register',  view_func=register_user, methods = ['GET', 'POST'], defaults={'mode': mode}) # idem below
	app.add_url_rule('/register/user',  view_func=register_user, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register/company',  view_func=register_company, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register/password',  view_func=register_password, methods = [ 'GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register/qrcode',  view_func=register_qrcode, methods = [ 'GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register/credible/user',  view_func=register_credible_user, methods = [ 'GET', 'POST'], defaults={'mode': mode, 'red' : red})

	app.add_url_rule('/register/code', view_func=register_code, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register/post_code', view_func=register_post_code, methods = ['POST', 'GET'], defaults={'mode': mode})
	app.add_url_rule('/register/credible_endpoint/<id>', view_func=register_credible_endpoint, methods = ['POST', 'GET'], defaults={'mode': mode, 'red' : red})
	app.add_url_rule('/register/stream',  view_func=register_stream,  defaults={'red' : red})
	app.add_url_rule('/register/error',  view_func=register_error)
	app.add_url_rule('/register/create_for_credible',  view_func=register_create_for_credible, methods = ['POST', 'GET'], defaults={'mode': mode})

	return



def register_company(mode) :
	""" create company
	# route /register/company
	"""
	if request.method == 'GET' :
		return render_template('register/company_register.html')
	if request.method == 'POST' :
		credentials_supported = list()
		for topic in CREDENTIAL_TOPIC :
			if request.form.get(topic) :
				credentials_supported.append(request.form[topic])
		username = request.form['company_name'].lower()
		siren = request.form['siren']
		if ns.username_exist(username, mode)   :
			username = username + str(random.randint(1, 100))
		if request.form['promo'] in ["TEST"] :
			promo = 50
		else :
			promo = 10
		workspace_contract =  createcompany.create_company(request.form['contact_email'],username, None, mode, siren=request.form['siren'])[2]
		if workspace_contract :
			directory.add_user(mode, request.form['company_name'], username, siren)
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
			personal['picture'] = 'QmXKeAgNZhLibNjYJFHCiXFvGhqsqNV2sJCggzGxnxyhJ5'
			personal['signature'] = 'QmPZxzrmh29sNcgrT7hyrrP6BWyahLwYUvzbuf5vUFxw91'
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
			return render_template('register/company_end_of_registration.html', campaign_code=campaign_code)
		else :
			flash(_('Company registration failed'), 'danger')
			return redirect(mode.server + 'register/company')


def register_user(mode) :
	if request.method == 'GET' :
		#session.clear()
		session['is_active'] = True
		return render_template("/register/user_register.html")
	if request.method == 'POST' :
		session['email'] = request.form['email']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['phone'] = request.form['phone']
		session['search_directory'] = request.form.get('CGU')
		message = ""
		if not request.form.get('CGU') :
			message = _('Accept the service conditions to move next step.')
			phone = session['phone']
		if not sms.check_phone(session['phone'], mode) :
			message = _('Incorrect phone number.')
			phone = ''
		if message :
			flash(message, 'warning')
			return render_template("/register/user_register.html",
									firstname=session['firstname'],
									lastname=session['lastname'],
									email=session['email'],
									phone=phone)
		return redirect (mode.server + 'register/identity')

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
					flash(_('DID resolution has been rejected by Universal Resolver.'), 'warning')
					return render_template("/register/register_identity.html")
			else  :
				r = requests.get('https://dev.uniresolver.io/1.0/identifiers/' + session['did'])
				if r.status_code != 200 :
					flash(_('DID resolution has been rejected by Universal Resolver.'), 'warning')
					return render_template("/register/register_identity.html")
		else :
			session['did'] = request.form['did_selected']
		return redirect (mode.server + 'register/password')


# route /register/password/
def register_password(mode):
	if not session.get('is_active') :
		flash(_('Session expired'), 'warning')
		return redirect(mode.server + 'register')
	if request.method == 'GET' :
		if request.args.get('did') :
			session['did'] = request.args['did']
			return render_template("/register/register_password_credible.html")
		return render_template("/register/register_password.html")
	if request.method == 'POST' :
		session['password'] = request.form['password']
		if not session.get('code_sent') :
			session['code'] = str(random.randint(100000, 999999))
			session['code_sent'] = True
			session['code_delay'] = datetime.now() + timedelta(seconds= 180)
			session['try_number'] = 0
			if sms.send_code(session['phone'], session['code'], mode) :
				logging.info('secret code sent = %s', session['code'])
			else :
				logging.error('sms connexion probleme register_password')
				flash(_('SMS failed.'), 'warning')
				return render_template("user_register.html" )
		return render_template("/register/register_code.html")


# route /register/code/
def register_code(mode) :
	if not session.get('is_active') or 'try_number' not in session :
		flash(_('Session expired'), 'warning')
		return redirect(mode.server + 'register')
	session['try_number'] +=1
	logging.info('code received = %s', request.form.get('mycode'))
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
			flash(_('Transaction failed.'), 'warning')
			return render_template("/register/user_register.html" )

		directory.add_user(mode, session['username'], session['firstname'] + ' ' + session['lastname'], None)
		# success exit
		return render_template("/register/end_of_registration.html", username=session['username'])
	elif session['try_number'] == 3 :
		session['is_active'] = False
		flash(_("Code is incorrect. Too many trials."), 'warning')
		message = _("Registration failed")
		return render_template("/register/registration_error.html")
	elif datetime.now() > session['code_delay'] :
		session['is_active'] = False
		flash(_('Code expired'), 'warning')
		return render_template("/register/registration_error.html")
	else :
		if session['try_number'] == 1 :
			message = _('Code is incorrect, 2 trials left.')
		if session['try_number'] == 2 :
			message = _('Code is incorrect, last trial.')
		flash(message, 'warning')
		return render_template("/register/register_code.html")


# route register/post_code
def register_post_code(mode) :
	if request.form.get('wallet') == 'ok' :
		return redirect (mode.server + 'login/VerifiablePresentationRequest')
	try :
		username = session['username']
		session.clear()
		return redirect (mode.server + 'login?username=' + username)
	except :
		return redirect (mode.server + 'login')


##############################################################################


def register_qrcode(mode) :
	if request.method == 'GET' :
		id = str(uuid.uuid1())
		url = mode.server + 'register/credible_endpoint/' + id
		return render_template("/register/register_credible_qrcode.html", url=url, id=id)


def register_credible_endpoint(id,red, mode):
    if request.method == 'GET':  
        challenge = str(uuid.uuid1())
        did_auth_request = {
            "type": "VerifiablePresentationRequest",
            "query": [{"type": 'DIDAuth'}],
            "challenge": challenge,
            "domain" : mode.server}    
        return jsonify(did_auth_request)
    if request.method == 'POST':
        presentation = json.loads(request.form['presentation'])
        # FIXME pb de version et voir comment on gere le challenge
        # FIXME challenge = presentation['proof']['challenge']
        # FIXME domain = presentation['proof']['domain']
        try :
            email = presentation['verifiableCredential']['credentialSubject']['email']   
        except :
            data = json.dumps({ "id" : id, "data" : 'wrong_vc'})
            red.publish('register_credible', data)
            return jsonify('wrong_vc')
        if ns.get_workspace_contract_from_did(presentation['holder'], mode) :
            data = json.dumps({ "id" : id, "data" : 'already_registered'})
            red.publish('register_credible', data)
            return jsonify('already_registered')
        session_data = json.dumps({"id" : id, "email" : email , "did" : presentation['holder']})
        red.set(id, session_data )
        data = json.dumps({ "id" : id, "data" : 'ok'})
        red.publish('register_credible', data)
        return jsonify('ok')


def register_credible_user(red, mode) :
	if request.method == 'GET' :
		id = request.args['id']
		session_data = json.loads(red.get(id).decode())
		red.delete(id)
		session['did'] = session_data['did']
		session['email'] = session_data['email']
		session['is_active'] = True
		return render_template("/register/register_credible_user.html")
	if request.method == 'POST' :
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['search_directory'] = request.form.get('CGU')
		message = ""
		if not request.form.get('CGU') :
			message = _('Accept the service conditions to move next step.')
		if message :
			flash(message, 'warning')
			return render_template("/register/register_credible_user.html",
									firstname=session['firstname'],
									lastname=session['lastname'],
									email=session['email'])
		return redirect (mode.server + 'register/create_for_credible')

# event push to browser
def register_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('register_credible')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)


def register_create_for_credible(mode) :
	if not createidentity.create_user(session['username'],
										session['email'],
										mode,
										did=session['did'],
										firstname=session['firstname'],
										lastname=session['lastname'],
										password='identity')[2] :
		logging.error('createidentity failed')
		flash(_('Transaction failed.'), 'warning')
		return render_template("/register/user_register.html" )
	directory.add_user(mode, session['username'], session['firstname'] + ' ' + session['lastname'], None)
	# success exit
	return render_template("/register/end_of_registration.html", username=session['username'], wallet="ok")


def register_error() :
	if request.args['message'] == 'already_registered' :
		message = _("This identity is already registered.")
	elif request.args['message'] == 'wrong_vc' :
		message = _("This credential is not accepted.")
	return render_template("/register/registration_error.html", message=message)

