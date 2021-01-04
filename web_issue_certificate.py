"""
Issue certificate for guest, Guest have received an email to issue a certificate. They have or they do not have an Identity.
If they do not have an Identity we create one.
"""


import os
from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
from flask_fontawesome import FontAwesome
from datetime import timedelta, datetime
import json
import random
import threading
import csv
import unidecode
from authlib.jose import jwt
from Crypto.PublicKey import RSA

import createidentity
import createcompany
import Talao_message
import ns
import privatekey
from protocol import Document, add_key, Claim, contractsToOwners, get_image, read_profil, get_category
import sms

exporting_threads = {}

class IssueRequest() :
	def __init__(self,remote_addr, remote_user, user_agent) :
		self.remote_addr = remote_addr
		self.remote_user = remote_user
		self.user_agent = user_agent

# Multithreading
class ExportingThread(threading.Thread):
	def __init__(self, issuer_type, issuer_email, issuer_firstname, issuer_lastname, workspace_contract, talent_name, talent_username, certificate, company_name, mode, request) :
		super().__init__()
		self.issuer_type = issuer_type
		self.issuer_email = issuer_email
		self.issuer_firstname = issuer_firstname
		self.issuer_lastname = issuer_lastname
		self.workspace_contract = workspace_contract
		self.talent_name = talent_name
		self.talent_username = talent_username
		self.certificate = certificate
		self.company_name = company_name
		self.mode = mode
		self.request = request
	def run(self):
		create_authorize_issue_thread(self.issuer_type,
										self.issuer_email,
										self.issuer_firstname,
										self.issuer_lastname,
										self.workspace_contract,
										self.talent_name,
										self.talent_username,
										self.certificate,
										self.company_name,
										self.mode,
										self.request)

def send_secret_code (username, code, mode) :
	data = ns.get_data_from_username(username, mode)
	if data == dict() :
		return None
	if not data['phone'] :
		subject = 'Talao : Email authentification  '
		Talao_message.messageHTML(subject, data['email'], 'code_auth', {'code' : code}, mode)
		print('Warning : secret code sent by email')
		return 'email'
	else :
		print('Warning : secret code sent by SMS')
		sms.send_code(data['phone'], code,mode)
	return 'sms'

#@app.route('/issue/logout/', methods = ['GET'])
def issue_logout(mode) :
	session.clear()
	flash('Thank you for your visit', 'success')
	return render_template('login.html')

#@app.route('/issue/', methods=['GET', 'POST'])
def issue_certificate_for_guest(mode) :
	""" MAIN GUEST view, issuer are either new or user but they have been requested to issue, Do not mix with issuer_experience_certificate.
	we display a form to complete the certificate draft and put everything in session for next phase
	this route is a hub to dispatcg according to certificate type"""

	if request.method == 'GET' :
		session.clear()
		# test if url is fine and decode JWT with Talao public RSA key
		try :
			btoken = bytes(request.args.get('token'), 'utf-8')
			private_rsa_key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
			RSA_KEY = RSA.import_key(private_rsa_key)
			public_rsa_key = RSA_KEY.publickey().export_key('PEM').decode('utf-8')
			token = jwt.decode(btoken, public_rsa_key)
		except :
			flash("Link error, Check the url", 'warning')
			print('Error : decode JWT in /issue/')
			return render_template('login.html')

		# issuer call is clean (token ok)
		session['certificate_type'] = token['certificate_type']
		session['url'] = request.url

		session['issuer_email'] = token['issuer_email']
		session['issuer_username'] = token['issuer_username']
		session['issuer_workspace_contract'] = token['issuer_workspace_contract']
		session['issuer_name'] = token['issuer_name']
		session['issuer_type'] = token['issuer_type']

		session['user_username'] = token['user_username']
		session['user_name'] = token['user_name']
		session['user_workspace_contract'] = token['user_workspace_contract']

		# complete user profil
		user_profil,category = read_profil(session['user_workspace_contract'], mode, 'light')
		if category == 1001 : # person
			session['user_postal_address'] = None
			session['user_siren'] = None
		else :
			session['user_siren'] = user_profil['siren']
			session['user_postal_address'] = user_profil['postal_address']

		# complete issuer profil
		if session['issuer_type'] == 'person' :
			session['issuer_logo'] = None
			session['issuer_siren'] = None
			session['issuer_postal_address'] = None
			if session['issuer_username']  :
				issuer_profil = read_profil(session['issuer_workspace_contract'], mode, 'light')[0]
				session['issuer_title'] == issuer_profil['issuer_title']
				session['issuer_firstname'] = issuer_profil['firstname']
				session['issuer_lastname'] = issuer_profil['lastname']
				session['issuer_picture'] = get_image(session['issuer_workspace_contract'], 'picture', mode)
			else : # issuer is an unknown person
				session['issuer_firstname'] = None
				session['issuer_lastname'] = None
				session['issuer_picture'] = None
				session['issuer_title'] = None

		else : # session['issuer_type'] == 'company' :
			session['issuer_firstname'] = None
			session['issuer_lastname'] = None
			session['issuer_picture'] = None
			session['issuer_title'] = None
			if session['issuer_username'] :
				issuer_profil = read_profil(session['issuer_workspace_contract'], mode, 'light')[0]
				session['issuer_logo'] = get_image(session['issuer_workspace_contract'], 'logo', mode)
				session['issuer_signature'] = get_image(session['issuer_workspace_contract'], 'signature', mode)
				session['issuer_siren'] = issuer_profil['siren']
				session['issuer_postal_address'] = issuer_profil['postal_address']
			else : # issuer is an unknown company
				session['issuer_logo'] = None
				session['issuer_signature'] = None
				session['issuer_siren'] = None
				session['issuer_postal_address'] = None

		# Dispatch starts here
		if session['certificate_type'] == 'experience' :
			return render_template('issue_experience_certificate_for_guest.html',
									start_date = token['start_date'],
									end_date = token['end_date'],
									description=token['description'],
									title=token['title'],
									skills=token['skills'],
									talent_name=session['user_name'],
									issuer_name=session['issuer_name'],
									issuer_firstname=session['issuer_firstname'] if session['issuer_firstname'] else "",
									issuer_lastname=session['issuer_lastname'] if session['issuer_lastname'] else "",
									company_name=session['issuer_name'] if session['issuer_lastname'] else "")

		elif session['certificate_type'] == 'recommendation' :
			return render_template('issue_recommendation_certificate_for_guest.html',
									talent_name = session['user_name'],
									issuer_firstname=session['issuer_firstname'] if session['issuer_firstname'] else "",
									issuer_lastname=session['issuer_lastname'] if session['issuer_lastname'] else "")

		elif session['certificate_type'] == 'agreement' :
			return render_template('issue_agreement_certificate_for_guest.html',
									description=token['description'],
									title=token['title'],
									service_product_group = token['service_product_group'],
									valid_until=token['valid_until'],
									date_of_issue=token['date_of_issue'],
									location=token['location'],
									standard=token['standard'],
									registration_number=token['registration_number'],
									issuer_firstname=session['issuer_firstname'] if session['issuer_firstname'] else "",
									issuer_lastname=session['issuer_lastname'] if session['issuer_lastname'] else "")

		elif session['certificate_type'] == 'reference' :
			return render_template('issue_reference_certificate_for_guest.html',
									start_date = token['start_date'],
									end_date = token['end_date'],
									description=token['description'],
									title=token['title'],
									competencies=token['competencies'],
									project_location = token['project_location'],
									project_staff=token['project_staff'],
									project_budget=token['project_budget'],
									issuer_firstname=session['issuer_firstname'] if session['issuer_firstname'] else "",
									issuer_lastname=session['issuer_lastname'] if session['issuer_lastname'] else "")

		else :
			flash("Certificate type not available yet", 'warning')
			print("Certificate type not available yet", 'warning')
			return render_template('login.html')

	if request.method == 'POST' :
		if not session['issuer_username'] :
			session['issuer_firstname'] = request.form.get('issuer_firstname')
			session['issuer_lastname'] = request.form.get('issuer_lastname')
			session['issuer_name'] = request.form.get('company_name')

		# Dispatch starts here
		if session['certificate_type'] == 'experience' :
			session['certificate'] = {
			'version' : 1,
			'type' : 'experience',
			'title' : request.form['title'],
			'description' : request.form['description'],
			'skills' : request.form['skills'],
			'start_date' : request.form['start_date'],
			'end_date' : request.form['end_date'],
			'score_recommendation' : request.form['score_recommendation'],
			'score_delivery' : request.form['score_delivery'],
			'score_schedule' :  request.form['score_schedule'],
			'score_communication' : request.form['score_communication'],
			"logo" : session['issuer_logo'],
			"signature" : session['issuer_signature'],
			"manager" : request.form.get('manager'),
			"reviewer" :  request.form['reviewer']
			}

		elif session['certificate_type'] == 'recommendation' :
			session['certificate'] = {
			'version' : 1,
			'type' : 'recommendation',
			'description' : request.form['description'],
			"logo" : session['issuer_logo'],
			"picture" : session['issuer_picture'],
			"issued_by"  : {
							"name" : session['issuer_name'],
							"postal_address" : session['issuer_postal_address'],
							"siren" : session['issuer_siren'],
							"logo" : session['issuer_logo'],
							"signature" : session['issuer_signature'],
        					"manager" : request.form.get('manager'),
							},
    		"issued_to"  : {
							"name" : session['user_name'],
							"postal_address" : session['user_postal_address'],
							"siren" : session['user_siren'],
							"logo" : None,
							"signature" : None,
							}
			}
			if get_category(session['user_workspace_contract'], mode) == 1001 and session['issuer_firstname']:
				firstname = Claim()
				firstname.get_by_topic_name(None, None,session['user_workspace_contract'],'firstname', mode)
				talent_firstname = firstname.claim_value
				relationship = request.form['relationship']
				if relationship == "1" :
					relationship_msg = session['issuer_firstname'] +   ' managed ' + talent_firstname + ' directly.'
				elif relationship == "2" :
					relationship_msg = session['issuer_firstname'] + ' reported directly to ' + talent_firstname + '.'
				elif relationship == "3" :
					relationship_msg = session['issuer_firstname'] + ' worked with ' + talent_firstname + ' in the same company.'
				elif relationship == "4" :
					relationship_msg = talent_firstname + ' was a client of ' + session['issuer_firstname'] + '.'
				elif relationship == "5" :
					relationship_msg = session['issuer_firstname'] + ' was a client of ' + talent_firstname + '.'
				elif relationship == "6" :
					relationship_msg = session['issuer_firstname'] + ' studied  together.'
				else :
					relationship_msg = talent_firstname + ' is a friend of ' + session['issuer_firstname'] + '.'
			else  :
				relationship_msg = ""
			session['certificate']['relationship'] = relationship_msg


		elif session['certificate_type'] == 'reference' :
			session['certificate'] = {
			'version' : 1,
			'type' : 'reference',
			'start_date' : request.form['start_date'],
			'end_date' : request.form['end_date'],
			'description' : request.form['description'],
			'title' : request.form['title'],
			'competencies' : request.form['competencies'],
			'location' : request.form['project_location'],
			'staff' : request.form['project_staff'],
			'budget' : request.form['project_budget'],
			'score_recommendation' : request.form['score_recommendation'],
			'score_delivery' : request.form['score_delivery'],
			'score_schedule' :  request.form['score_schedule'],
			'score_communication' : request.form['score_communication'],
			'score_budget' : request.form['score_budget'],
			'issued_by'  : {
							"name" : session['issuer_name'],
							"postal_address" : session['issuer_postal_address'],
							"siren" : session['issuer_siren'],
							"logo" : session['issuer_logo'],
							"signature" : session['issuer_signature'],
        					"manager" : request.form.get('manager'),
							},
    		"issued_to"  : {
							"name" : session['user_name'],
							"postal_address" : session['user_postal_address'],
							"siren" : session['user_siren'],
							"logo" : None,
							"signature" : None,
							}
			}

		elif session['certificate_type'] == 'agreement' :
			session['certificate'] = {
			'version' : 1,
			'type' : 'agreement',
			'description' : request.form['description'],
			'title' : request.form['title'],
			'service_product_group' : request.form['service_product_group'],
			'valid_until' : request.form['valid_until'],
			'date_of_issue' : request.form['date_of_issue'],
			'location' : request.form['location'],
			'standard' : request.form['standard'],
			'registration_number' : request.form['registration_number'],
			"issued_by"  : {
							"name" : session['issuer_name'],
							"postal_address" : session['issuer_postal_address'],
							"siren" : session['issuer_siren'],
							"logo" : session['issuer_logo'],
							"signature" : session['issuer_signature'],
        					"manager" : request.form.get('manager'),
							},
    		"issued_to"  : {
							"name" : session['user_name'],
							"postal_address" : session['user_postal_address'],
							"siren" : session['user_siren'],
							"logo" : None,
							"signature" : None,
							}
			}

		else :
			flash("Session aborted", 'warning')
			print('Error : unknown certificate type')
			return render_template('login.html')

		if not session.get('code') :
			session['code'] = str(random.randint(10000, 99999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 240)
			session['try_number'] = 1

		# ask for code confirmation
		print('Warning : secret code sent = ', session['code'])
		if not session['issuer_username'] :
			flash("Secret Code already sent by email", 'success')
			Talao_message.messageHTML('Talao : Email authentification  ', session['issuer_email'], 'code_auth', {'code' : session['code']}, mode)
			return render_template('confirm_issue_certificate_for_guest.html')
		else :
			support = send_secret_code(session['issuer_username'], session['code'], mode)
			flash("Secret Code already sent by " + support, 'success')
			return render_template('confirm_issue_certificate_for_user_as_guest.html', support=support)

#@app.route('/issue/create_authorize_issue/', methods=['GET', 'POST'])
def create_authorize_issue(mode) :
	""" Its a GUEST screen ,
	After confirmation view
	We create the Identity for issuer (and eventually for company), then the Talent issues the key 20002 to the issuer then the issuer issues the certificate"""

	# setup a local copy of request to pass it as an argument
	my_request = IssueRequest(request.remote_addr, request.remote_user, request.user_agent)

	# verif secret code sent by email
	if session.get('code') is None :
		flash("Authentification expired")
		return render_template('login.html')

	code = request.form['code']
	authorized_codes = [session['code'], '123456'] if mode.test else [session['code']]
	session['try_number'] +=1
	if session['code_delay'] < datetime.now() :
		flash("Code expired", 'danger')
		url=session['url']
		session.clear()
		return redirect(url)
	elif session['try_number'] > 3 :
		flash("Too many trials (3 max)", "danger")
		url = session['url']
		session.clear()
		return redirect(url)
	elif code not in authorized_codes :
		if session['try_number'] == 2 :
			flash('This code is incorrect, 2 trials left', 'warning')
		elif session['try_number'] == 3 :
			flash('This code is incorrect, 1 trial left', 'warning')
		return render_template('confirm_issue_certificate_for_guest.html')

	# New user and company, call to thread to authorize, issue and create
	if not session['issuer_username'] :
		#issuer_username = ns.build_username(session['issuer_firstname'], session['issuer_lastname'], mode)
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(session['issuer_type'],
														session['issuer_email'],
														session['issuer_firstname'],
														session['issuer_lastname'],
														session['user_workspace_contract'],
														session['user_name'],
														session['user_username'],
														session['certificate'],
														session['issuer_name'],
														mode,
														my_request)
		exporting_threads[thread_id].start()
		return render_template('thank_you.html', url_to_link= mode.server + 'login/')

	# "Old" user, issue certificate straight
	else :
		my_certificate = Document('certificate')
		issuer_workspace_contract = session['issuer_workspace_contract']
		issuer_address = contractsToOwners(issuer_workspace_contract, mode)

		# get private key for issuer
		issuer_private_key = privatekey.get_key(issuer_address,'private_key', mode)
		if not issuer_private_key  :
			print('Error : private key not found for ', session['issuer_username'])
			flash('Sorry, the Certificate cant be issued, no Private Key found', 'warning')
			return render_template('login.html')
		workspace_contract = session['user_workspace_contract']
		address = contractsToOwners(session['user_workspace_contract'],mode)
		doc_id = my_certificate.add(issuer_address, issuer_workspace_contract, address, workspace_contract, issuer_private_key, session['certificate'], mode, mydays=0, privacy='public', synchronous=True, request=my_request)[0]

		# message to issuer
		flash('Thank you, the Certificate has been issued', 'success')

		# Email to issuer
		subject = 'Certificate has been issued to ' + session['user_name']
		link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract[2:] + ':document:' + str(doc_id)
		Talao_message.messageHTML(subject, session['issuer_email'], 'certificate_issued_issuer', {'name' : session['user_name'], 'link':link}, mode)
		print('Success : msg to issuer sent')

		# Email to talent
		subject = 'A new Certificate has been issued to you'
		talent_email = ns.get_data_from_username(session['user_username'], mode)['email']
		Talao_message.messageHTML(subject, talent_email, 'certificate_issued', {'username' : session['user_username'], 'link': link}, mode)
		print('Success : msg to user sent')

		return render_template('login.html')

# this is a Thread function to create Identity and issue certificates
def create_authorize_issue_thread(issuer_type,
									issuer_email,
									issuer_firstname,
									issuer_lastname,
									workspace_contract,
									talent_name,
									talent_username,
									certificate,
									company_name,
									mode,
									request) :

	# create user identity
	print('Warning : call create identity for user')
	issuer_username = ns.build_username(issuer_firstname, issuer_lastname, mode)
	issuer_address,issuer_private_key, issuer_workspace_contract = createidentity.create_user(issuer_username, issuer_email, mode, firstname=issuer_firstname, lastname=issuer_lastname,is_thread=False)
	if not issuer_workspace_contract  :
		print('Error : create new identity failed')
		return

	# create company identity if company is the issuer and company does not exist
	if issuer_type == 'company' :
		if not ns.username_exist(company_name.lower(), mode) :
			print('Warning : call create identity for company')
			company_address, company_private_key, company_workspace_contract = createcompany.create_company(issuer_email, company_name.lower(), mode, name=company_name, is_thread=False)
			if not issuer_workspace_contract  :
				print('Error : create new identity failed')
				return

			#authorize the new company to issue documents (ERC725 key 20002)
			address = contractsToOwners(workspace_contract, mode)
			add_key(mode.relay_address, mode.relay_workspace_contract, address, workspace_contract, mode.relay_private_key, company_address, 20002, mode)
			print('Success : key 20002 issued to company')

			# build certificate and company issues certificate
			my_certificate = Document('certificate')
			doc_id = my_certificate.add(company_address, company_workspace_contract, address, workspace_contract, company_private_key, certificate, mode, mydays=0, privacy='public', request=request)[0]
			print('Success : certificate issued by company')

			# send message to company 
			subject = 'A new certificate has been issued to ' + talent_name
			link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract[2:] + ':document:' + str(doc_id)
			Talao_message.messageHTML(subject, issuer_email, 'certificate_issued_issuer', {'name' : talent_name, 'link': link}, mode)
			print('Success : msg to issuer sent')

		else :
			print('Warning : company already exist, cannot issue certificate')
			return

	else : # issuer is a person

		#authorize the new issuer to issue documents (ERC725 key 20002)
		address = contractsToOwners(workspace_contract, mode)
		add_key(mode.relay_address, mode.relay_workspace_contract, address, workspace_contract, mode.relay_private_key, issuer_address, 20002, mode)
		print('Success : key 20002 issued')

		# build certificate and issue
		my_certificate = Document('certificate')
		doc_id = my_certificate.add(issuer_address, issuer_workspace_contract, address, workspace_contract, issuer_private_key, certificate, mode, mydays=0, privacy='public', request=request)[0]
		print('Success : certificate issued')

		# send message to issuer
		subject = 'A new certificate has been issued to ' + talent_name
		link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract[2:] + ':document:' + str(doc_id)
		Talao_message.messageHTML(subject, issuer_email, 'certificate_issued_issuer', {'name' : talent_name, 'link': link}, mode)
		print('Success : msg to issuer sent')

	# send message to user/company
	subject = 'A new Certificate has been issued to you'
	talent_email = ns.get_data_from_username(talent_username, mode)['email']
	Talao_message.messageHTML(subject, talent_email, 'certificate_issued', {'username' : talent_username, 'link': link}, mode)
	print('Success : msg to user sent')
	print('Success : end of issue certificate')
	return
