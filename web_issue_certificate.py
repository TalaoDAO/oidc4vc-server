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

import createidentity
import Talao_message
import ns
import privatekey
from protocol import Document, add_key, Claim, contractsToOwners, get_image, read_profil
import sms

exporting_threads = {}

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

def send_secret_code (username, code, mode) :
	data = ns.get_data_from_username(username, mode)
	if data == dict() :
		return None
	if data['phone'] is None :	
		Talao_message.messageAuth(data['email'], code, mode)
		print('envoi du code par email')
		return 'email'
	else :
		print('envoi du code par sms')
		sms.send_code(data['phone'], code,mode)
	return 'sms'

#@app.route('/issue/logout/', methods = ['GET'])
def issue_logout(mode) :
	session.clear()
	flash('Thank you for your visit', 'success')
	return render_template('login.html')

#@app.route('/issue/', methods=['GET', 'POST'])
def issue_certificate_for_guest(mode) :
	""" Its a the MAIN GUEST view, issuer are either new or user but they have been requested to issue, Do not mix with issuer_experience_certificate. 
	we display a form to complete the certificate draft and put everything in session for next phase
	this route is a hub to dispatcg according to certificate type"""
	
	if request.method == 'GET' :
		session.clear()
		# test if url is fine
		try :
			session['certificate_type'] = request.args['certificate_type']
			session['issuer_email'] = request.args['issuer_email']
			session['url'] = request.url
			session['issuer_username'] = request.args['issuer_username']
			session['issuer_workspace_contract'] = request.args['issuer_workspace_contract']	
			session['talent_username'] = request.args['talent_username']
			session['talent_name'] = request.args['talent_name']
			session['talent_workspace_contract'] = request.args['talent_workspace_contract']
		
		except :
			flash("Link error, Check the url", 'warning')
			return redirect(mode.server + 'login/')	
		
		# test if certificate has already been issued (we only test if the issuer exists.....to be changed later)
		issuer_list = ns.get_username_list_from_email(session['issuer_email'], mode)
		if session['issuer_username'] == "new" and issuer_list != [] : 
			flash("Certificate already issued.", 'warning')
			return redirect(mode.server + 'login/')	
		
		# Dispatch starts here
		if session['certificate_type'] == 'experience' :
			if session['issuer_username'] != 'new' :
				print('workspace_contract = ', session['issuer_workspace_contract'])
				session['issuer_logo'] = get_image(session['issuer_workspace_contract'], 'logo', mode) 
				session['issuer_signature'] = get_image(session['issuer_workspace_contract'], 'signature', mode) 
				print ('logo = ', session['issuer_logo'], 'signature = ', session['issuer_signature'])
			else :
				session['issuer_logo'] = None
				session['issuer_signature'] = None
			personal = get_issuer_personal(mode)
			return render_template('issue_experience_certificate_for_guest.html',
						start_date = request.args['start_date'],
						end_date = request.args['end_date'],
						description=request.args['description'],
						title=request.args['title'],
						skills=request.args['skills'],
						talent_name=session['talent_name'],
						**personal)
		
		elif session['certificate_type'] == 'recommendation' :
			if session['issuer_username'] != 'new' :
				session['issuer_picture'] = get_image(session['issuer_workspace_contract'], 'picture', mode)
				title_claim = Claim()
				title_claim.get_by_topic_name(None, None,session['issuer_workspace_contract'],'profil_title', mode)
				session['issuer_title'] = title_claim.claim_value
			else :
				session['issuer_title'] = None
				session['issuer_picture'] = None
			personal = get_issuer_personal(mode)
			return render_template('issue_recommendation_for_guest.html',
									talent_name = session['talent_name'],
									**personal)
		
		else :
			flash("Certififcate type not available yet", 'warning')
			return redirect(mode.server + 'login/')	
	
	
	if request.method == 'POST' :
		# Dispatch starts here
		if session['certificate_type'] == 'experience' :	
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
		
		elif session['certificate_type'] == 'recommendation' :	
			session['description'] = request.form['description']
			session['issuer_firstname'] =request.form['issuer_firstname']
			session['issuer_lastname'] = request.form['issuer_lastname']
			firstname_claim = Claim()
			firstname_claim.get_by_topic_name(None, None,session['talent_workspace_contract'],'firstname', mode)
			talent_firstname = firstname_claim.claim_value
			relationship = request.form['relationship']
			if relationship == "1" :	
				session['relationship'] = session['issuer_firstname'] +   ' managed ' + talent_firstname + ' directly.'
			elif relationship == "2" :
				session['relationship'] = session['issuer_firstname'] + ' reported directly to ' + talent_firstname + '.'
			elif relationship == "3" :
				session['relationship'] = session['issuer_firstname'] + ' worked with ' + talent_firstname + ' in the same company.'
			elif relationship == "4" :
				session['relationship'] = talent_firstname + ' was a client of ' + session['issuer_firstname'] + '.'
			elif relationship == "5" :
				session['relationship'] = session['issuer_firstname'] + ' was a client of ' + talent_firstname + '.'
			elif relationship == "6" :
				session['relationship'] = session['issuer_firstname'] + ' studied  together.'
			else :
				session['relationship'] = talent_firstname + ' is a friend of ' + session['issuer_firstname'] + '.'			
			
		else :
			flash("Session aborted", 'warning')
			return redirect(mode.server + 'login/')	
		
		if session.get('code') is None :
			session['code'] = str(random.randint(10000, 99999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 180)
			session['try_number'] = 1
		
		if session['issuer_username'] == 'new' :
			Talao_message.messageAuth(session['issuer_email'], str(session['code']), mode)
			return render_template('confirm_issue_certificate_for_guest.html')
		else :
			support = send_secret_code(session['issuer_username'], session['code'], mode)
			if support is None :
				flash("Session aborted", 'warning')
				print('support is None dans web_issue_certificate') 
				return render_template('login.html')
			else :
				print('secret code sent = ', session['code'])
				flash("Secret Code already sent by " + support, 'success')
			return render_template('confirm_issue_certificate_for_user_as_guest.html', support=support)		
				
def get_issuer_personal(mode) :				
		 # it is not an issuer creation
		if session['issuer_username'] != "new" :
			firstname_claim = Claim()
			lastname_claim = Claim()
			firstname_claim.get_by_topic_name(None, None, session['issuer_workspace_contract'],'firstname', mode)
			lastname_claim.get_by_topic_name(None, None, session['issuer_workspace_contract'], 'lastname', mode)
			issuer_firstname = firstname_claim.claim_value
			issuer_lastname = lastname_claim.claim_value
		 # it is an issuer creation
		else :
			issuer_firstname = ""
			issuer_lastname = ""
		print('issuer_firstname = ', issuer_firstname)
		return {'issuer_firstname' : issuer_firstname,
				'issuer_lastname' : issuer_lastname}
	
				
		
#@app.route('/issue/create_authorize_issue/', methods=['GET', 'POST'])
def create_authorize_issue(mode) :
	""" Its a GUEST screen ,
	After confirmation view
	We create the Identity, then the Talent issues the key 20002 to the issuer then the issuer issues the certificate"""
	
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
	
	
	# Code if fine we can dispatch
	if session['certificate_type'] == 'experience' :
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
			"logo" : session['issuer_logo'],
			"signature" : session['issuer_signature'],
			"manager" : session['issuer_firstname'] + " " + session['issuer_lastname'],
			"reviewer" : None }
		
	elif session['certificate_type'] == 'recommendation' :
		certificate = {	"version" : 1,
			"type" : "recommendation",	
			"description" : session['description'],
			"relationship" : session['relationship'],
			"picture" : session['issuer_picture'],
			"title" : session['issuer_title'],
			}	
		
	# New user, call to thread to authorize, issue and create	
	if session['issuer_username'] == "new" :	
		issuer_username = ns.build_username(session['issuer_firstname'], session['issuer_lastname'], mode) 
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(issuer_username,
														session['issuer_email'],
														session['issuer_firstname'],
														session['issuer_lastname'],
														session['talent_workspace_contract'],
														session['talent_name'],
														session['talent_username'],
														certificate,
														mode)
		exporting_threads[thread_id].start() 
		return render_template('thank_you.html',
								url_to_link= mode.server + 'login/')
	# "Old" user, issue certificate straight
	else :
		my_certificate = Document('certificate')
		issuer_workspace_contract = session['issuer_workspace_contract']
		issuer_address = contractsToOwners(issuer_workspace_contract, mode)
		# get private key for issuer
		issuer_private_key = privatekey.get_key(issuer_address,'private_key', mode) 					
		if issuer_private_key is None :
			print('erreur , Private kay not found for ', session['issuer_username'])
			flash('Sorry, the Certificate cant be issued, no Private Key found', 'warning')
			return render_template('login.html')
		workspace_contract = session['talent_workspace_contract']
		address = contractsToOwners(session['talent_workspace_contract'],mode)
		doc_id = my_certificate.add(issuer_address, issuer_workspace_contract, address, workspace_contract, issuer_private_key, certificate, mode, mydays=0, privacy='public', synchronous=True)[0] 
		# message to issuer
		flash('Thank you, the Certificate has been issued', 'success')
		# Email to issuer
		subject = 'Certificate has been issued to ' + session['talent_name']
		link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract[2:] + ':document:' + str(doc_id)  
		text = 'Hello,\r\nFollow the link to see the Certificate : ' + link
		Talao_message.message(subject, session['issuer_email'], text, mode)
		if mode.test :
			print('msg pour issuer envoyé')
		# Email to talent
		subject = 'A new Certificate has been issued to you'
		talent_email = ns.get_data_from_username(session['talent_username'], mode)['email']
		Talao_message.message(subject, talent_email, text, mode)
		if mode.test :
			print('message pour Talent envoyé')
		return render_template('login.html')
								
# this is a Thread function to create Identity and issue certificates		
def create_authorize_issue_thread(username, 
									issuer_email,
									issuer_firstname,
									issuer_lastname,
									workspace_contract,
									talent_name,
									talent_username,
									certificate,
									mode) :
	if mode.test :
		print('debut thread ')
	issuer_address,issuer_private_key, issuer_workspace_contract = createidentity.create_user(username, issuer_email, mode) 
	if issuer_workspace_contract is None :
		print('Thread to create new identity failed')
		return
	#  update firtname and lastname
	Claim().relay_add( issuer_workspace_contract,'firstname', issuer_firstname, 'public', mode)
	Claim().relay_add( issuer_workspace_contract,'lastname', issuer_lastname, 'public', mode)
	if mode.test :
		print('firstname, lastname updated')
	#authorize the new issuer to issue documents (ERC725 key 20002)
	address = contractsToOwners(workspace_contract, mode)
	add_key(mode.relay_address, mode.relay_workspace_contract, address, workspace_contract, mode.relay_private_key, issuer_address, 20002, mode, synchronous=True) 
	if mode.test :
		print('key 20002 issued')
	# build certificate and issue
	my_certificate = Document('certificate')
	doc_id = my_certificate.add(issuer_address, issuer_workspace_contract, address, workspace_contract, issuer_private_key, certificate, mode, mydays=0, privacy='public', synchronous=True)[0]
	if mode.test :
		print('certificat issued')
	# send message to issuer
	subject = 'A new certificate has been issued to ' + talent_name
	link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract[2:] + ':document:' + str(doc_id)  
	text = 'Hello,\r\nFollow the link to see the Certificate : ' + link
	Talao_message.message(subject, issuer_email, text, mode)
	if mode.test :
		print('msg pour issuer envoyé')
	# send message to talent
	subject = 'A new Certificate has been issued to you'
	talent_email = ns.get_data_from_username(talent_username, mode)['email']
	Talao_message.message(subject, talent_email, text, mode)
	if mode.test :
		print('msg pour user envoyé')
	return
	
	
