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
import redis

import requests
from datetime import timedelta, datetime
import logging
logging.basicConfig(level=logging.INFO)

from factory import createidentity, createcompany
from components import sms, directory, ns, company, privatekey
from signaturesuite import vc_signature

red = redis.StrictRedis()


CREDENTIAL_TOPIC = ['experience', 'training', 'recommendation', 'work', 'salary', 'vacation', 'internship', 'relocation', 'end_of_work', 'hiring']


def init_app(app, mode) :
	app.add_url_rule('/register/identity',  view_func= register_identity, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register',  view_func=register_user, methods = ['GET', 'POST'], defaults={'mode': mode}) # idem below
	app.add_url_rule('/register/user',  view_func=register_user, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register/company',  view_func=register_company, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register/password',  view_func=register_password, methods = [ 'GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register/code', view_func=register_code, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/register/post_code', view_func=register_post_code, methods = ['POST', 'GET'], defaults={'mode': mode})
	app.add_url_rule('/register/credible_endpoint', view_func=register_credible_endpoint, methods = ['POST', 'GET'], defaults={'mode': mode})
	app.add_url_rule('/register/stream',  view_func=register_stream)
	app.add_url_rule('/register/error',  view_func=register_error)
	app.add_url_rule('/register/create_for_credible',  view_func=register_create_for_credible, methods = ['POST', 'GET'], defaults={'mode': mode})

	return


def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if not session.get('workspace_contract') and not session.get('username') :
		logging.warning('Check login failed, call abort 403')
		abort(403)
	else :
		return True


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
		if request.form['did'] == "credible" :
			url = mode.server + "register/credible_endpoint"
			return render_template("/register/register_credible_qrcode.html", url=url)
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



def register_credible_endpoint(mode):
    credential = {
    "@context": ["https://www.w3.org/2018/credentials/v1"],
        "id": "",
        "type": ["VerifiableCredential"],
        "issuer": "",
        "issuanceDate": "",
        "credentialSubject" : {}
	}
    if request.method == 'GET':   
        return jsonify({
            "type": "CredentialOffer",
            "credentialPreview": credential,
			"expires" : (datetime.now() + timedelta(seconds= 10*60)).replace(microsecond=0).isoformat() + "Z"
        	})
    elif request.method == 'POST':
        if ns.get_workspace_contract_from_did(request.form['subject_id'], mode) :
            data = json.dumps({ "did" : 'registered'})
            red.publish('register_credible', data)
            return jsonify('registered')
        pvk = privatekey.get_key(mode.owner_talao, 'private_key', mode)
        credential["issuer"] = 'did:web:talao.co'
        credential['id'] = "urn:uuid:" + str(uuid.uuid1())
        credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        credential['credentialSubject']['id'] = request.form['subject_id']
        signed_credential = vc_signature.sign(credential, pvk, 'did:web:talao.co')
        data = json.dumps({ "did" : request.form['subject_id']})
        red.publish('register_credible', data)
        return Response(signed_credential, content_type = 'application/ld+json')


# event push to browser
def register_stream():
    def event_stream():
        pubsub = red.pubsub()
        pubsub.subscribe('register_credible')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(), headers=headers)


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

def register_create_for_credible(mode) :
	if not createidentity.create_user(session['username'],
										session['email'],
										mode,
										did=request.args['did'],
										firstname=session['firstname'],
										lastname=session['lastname'],
										phone=session['phone'],
										password='identity')[2] :
		logging.error('createidentity failed')
		flash(_('Transaction failed.'), 'warning')
		return render_template("/register/user_register.html" )
	directory.add_user(mode, session['username'], session['firstname'] + ' ' + session['lastname'], None)
	# success exit
	return render_template("/register/end_of_registration.html", username=session['username'])


def register_error() :
	message = _("This Identity is already registered")
	return render_template("/register/registration_error.html", message=message)


# route register/post_code
def register_post_code(mode) :
	try :
		username = session['username']
		session.clear()
		return redirect (mode.server + 'login?username=' + username)
	except :
		return redirect (mode.server + 'login')