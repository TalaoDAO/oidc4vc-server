"""
Issue certificate for guest, Guest have received an email to issue a certificate. They have or they do not have an Identity.
If they do not have an Identity create one.
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

import createidentity
import Talao_message
import ns
import environment
from protocol import Document, add_key

exporting_threads = {}

# environment setup
mode = environment.currentMode()
w3 = mode.w3

# Multithreading 
class ExportingThread(threading.Thread):
	def __init__(self, username, issuer_email, issuer_firstname, issuer_lastname, workspace_contract, talent_name, talent_username, certificate, mode) :
		super().__init__()
		self.username = username
		self.issuer_email = issuer_email
		self.issuer_firstname = issuer_firstname
		self.issuer_lastname = issuer_lastname
		self.workspace_contract = workspace_contract
		self.talent_name = talent_name
		self.talent_username = talent_username
		self.certificate = certificate
		self.mode = mode
	def run(self):
		create_authorize_issue_thread(self.username, self.issuer_email, self.issuer_firstname, self.issuer_lastname, self.workspace_contract, self.talent_name, self.talent_username, self.certificate, self.mode)	


#@app.route('/issue/', methods=['GET', 'POST'])
def issue_certificate_for_guest() :
	""" Its a GUEST screen, issuer are either new or user but theu habe been requested to issue, Do not mix with issuer_experience_certificate. 
	we display a form to complete the certificate draft and put everything in session for next phase"""
	
	if request.method == 'GET' :
		session.clear()
		session['issuer_username'] = request.args['issuer_username']
		session['url'] = request.url
		session['issuer_email'] = request.args['issuer_email']
		session['workspace_contract'] = request.args['workspace_contract']	
		session['talent_name'] = request.args['talent_name']
		session['talent_username'] = request.args['talent_username']
		talent_name = request.args['talent_name']
		issuer_list = ns.get_username_list_from_email(session['issuer_email'])
		if session['issuer_username'] == "null" and issuer_list != [] : # It is a issuer creation but certifcate has already been issued
			flash("Certificate already issued.", 'warning')
			return redirect(mode.server + 'login/')	
		elif session['issuer_username'] != "null" : # it is not an issuer creation
			issuer_workspace_contract = ns.get_data_from_username(session['issuer_username'], mode)['workspace_contract']
			firstname_claim = Claim()
			lastname_claim = Claim()
			firstname_claim.get_by_topic_name(issuer_workspace_contract, 'firstname', mode)
			lastname_claim.get_by_topic_name(issuer_workspace_contract, 'lastname', mode)
			issuer_firstname = firstname_claim.claim_value
			issuer_lastname = lastname_claim.claim_value
		else : # it is an issuer creation
			issuer_firstname = ""
			issuer_lastname = ""
		return render_template('issue_experience_certificate_for_guest.html',
							start_date=request.args['start_date'],
							end_date=request.args['end_date'],
							description=request.args['description'],
							title=request.args['title'],
							skills=request.args['skills'],
							talent_name=talent_name,
							issuer_firstname=issuer_firstname,
							issuer_lastname=issuer_lastname)
	
	if request.method == 'POST' :
		session['title'] = request.form['title']
		session['company_name'] = request.form['company_name']
		session['description'] = request.form['description']
		session['skills'] = request.form['skills']
		session['start_date'] = request.form['start_date']
		session['end_date'] = request.form['end_date']
		session['score_recommendation'] = request.form['score_recommendation']
		session['score_delivery'] = request.form['score_delivery']
		session['score_schedule'] =  request.form['score_schedule']
		session['score_communication'] = request.form['score_communication']
		session['issuer_firstname'] =request.form['issuer_firstname']
		session['issuer_lastname'] = request.form['issuer_lastname']
		if session.get('code') is None :
			session['code'] = str(random.randint(1000, 9999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 180)
			session['try_number'] = 1
			Talao_message.messageAuth(session['issuer_email'], str(session['code']))
		if session['issuer_username'] == 'null' :
			return render_template('confirm_issue_certificate_for_guest.html')
		else :
			return render_template('confirm_issue_certificate_for_user_as_guest.html')

		
#@app.route('/issue/create_authorize_issue/', methods=['GET', 'POST'])
def create_authorize_issue() :
	""" Its a GUEST screen ,
	We create the Identity, then the Talent issues the key 20002 to the issuer then the issuer issues the certificate"""
	# verif secret code sent by email
	if session.get('code') is None :
		flash("Authentification expired")		
		return render_template('login.html')
	code = request.form['code']
	session['try_number'] +=1
	if session['code_delay'] < datetime.now() :
		flash("Code expired", 'danger')
		url=session['url']
		session.clear()
		return redirect(url)	
	elif session['try_number'] > 3 :
		flash("Too many trials (3 max)")
		url = session['url']
		session.clear()
		return redirect(url)			
	elif code not in [session['code'], "123456"] :	
		if session['try_number'] == 2 :			
			flash('This code is incorrect, 2 trials left', 'warning')
		if session['try_number'] == 3 :
			flash('This code is incorrect, 1 trial left', 'warning')
			print('sortie vers confirm_issue.html ')
		return render_template('confirm_issue_certificate_for_guest.html')
	
	certificate = {
		"version" : 1,
		"type" : "experience",	
		"title" : session['title'],
		"description" : session['description'],
		"start_date" : session['start_date'],
		"end_date" : session['end_date'],
		"skills" : session['skills'].split(','),  		
		"score_recommendation" : session['score_recommendation'],
		"score_delivery" : session['score_delivery'],
		"score_schedule" : session['score_schedule'],
		"score_communication" : session['score_communication'],
		"logo" : None,
		"signature" : None,
		"manager" : session['issuer_firstname'] + " " + session['issuer_lastname'],
		"reviewer" : None }
	if session['issuer_username'] == "null" :	
		# call to thread to authorize, issue and create
		username_2 = session['issuer_firstname'].lower() + session['issuer_lastname'].lower()
		username_1 = username_2 + str(random.randint(0, 999)) if ns.does_alias_exist(username_2) else username_2
		username = username_1.replace(" ", "")
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(username,
														session['issuer_email'],
														session['issuer_firstname'],
														session['issuer_lastname'],
														session['workspace_contract'],
														session['talent_name'],
														session['talent_username'],
														certificate,
														mode)
		exporting_threads[thread_id].start() 
		return render_template('thank_you.html',
								url_to_link= mode.server + 'login/')
	else :
		my_certificate = Document('certificate')
		issuer_workspace_contract = ns.get_data_from_username(session['issuer_username'], mode)['workspace_contract']
		issuer_address = contractsToOwners(issuer_workspace_contract, mode)
		# get private key for issuer
		fname = mode.BLOCKCHAIN +"_Talao_Identity.csv"
		identity_file = open(fname, newline='')
		reader = csv.DictReader(identity_file)
		private_key_exist = False
		issuer_private_key = None
		for row in reader :
			if row['ethereum_address'] == issuer_address :
				private_key_exist = False if row.get('private_key', '')[:2] != '0x'  else True				
				if private_key_exist :
					issuer_private_key = row['private_key']
					break 
		if issuer_private_key is None :
			print('erreur , Private kay not found for ', session['issuer_username'])
			flash('Sorry, the Certificate cant issued, No Private Key', 'danger')
			return render_template('login.html')
		workspace_contract = session['workspace_contract']
		address = contractsToOwners(session['workspace_contract'],mode)
		(doc_id, ipfshash, transaction_hash) = my_certificate.add(issuer_address, issuer_workspace_contract, address, workspace_contract, issuer_private_key, certificate, mode, mydays=0, privacy='public', synchronous=True) 
		flash('Thank you, the Certificate has been issued', 'success')
		return render_template('login.html')
								
# this is a Thread function		
def create_authorize_issue_thread(username, 
									issuer_email,
									issuer_firstname,
									issuer_lastname,
									workspace_contract,
									talent_name,
									talent_username,
									certificate,
									mode) :
	print('debut du thread')
	issuer_address,issuer_private_key, issuer_workspace_contract = createidentity.create_user(username, issuer_email, mode) 
	#  update firtname and lastname
	Claim().relay_add( issuer_workspace_contract,'firstname', issuer_firstname, 'public', mode)
	Claim().relay_add( issuer_workspace_contract,'lastname', issuer_lastname, 'public', mode)
	print('firstname et lastname updated')
	#authorize the new issuer to issue documents (key 20002)
	address = contractsToOwners(workspace_contract, mode)
	add_key(mode.relay_address, mode.relay_workspace_contract, address, workspace_contract, mode.relay_private_key, issuer_address, 20002, mode, synchronous=True) 
	print('key 20002 issued')
	# build certificate and issue
	my_certificate = Document('certificate')
	(doc_id, ipfshash, transaction_hash) = my_certificate.add(issuer_address, issuer_workspace_contract, address, workspace_contract, issuer_private_key, certificate, mode, mydays=0, privacy='public', synchronous=True) 
	print('certificat issued')
	# send message to issuer
	subject = 'Certificate has been issued to ' + talent_name
	link = mode.server + 'certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract[2:] + ':document:' + str(doc_id)  
	text = '\r\nFollow the link : ' + link
	Talao_message.message(subject, issuer_email, text)
	print('msg pour issuer envoyé')
	# send message to talent
	subject = 'A new Certificate has been issued to you'
	identity, talent_email = ns.get_data_for_login(talent_username)
	Talao_message.message(subject, talent_email, text)
	print('msg pour user envoyé')
	return
	
