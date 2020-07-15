"""
pour l authentication cf https://realpython.com/token-based-authentication-with-flask/

pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization

interace wsgi https://www.bortzmeyer.org/wsgi.html

import ipfshttpclient

request : http://blog.luisrei.com/articles/flaskrest.html
"""
import os
from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
from flask_fontawesome import FontAwesome
from datetime import timedelta, datetime
import json
import random
import time
import unidecode

# dependances
import Talao_message
import constante
from protocol import ownersToContracts, contractsToOwners, destroyWorkspace, save_image, partnershiprequest, remove_partnership, token_balance, Document
from protocol import Claim, File, Identity, Document, read_profil
import environment
import hcode
import ns




# environment setup
mode = environment.currentMode()
w3 = mode.w3

def check_login() :
	username = session.get('username_logged')
	if username is None  :
		flash('session aborted', 'warning')
	return username

# route user/update_skills/
def update_skills() :
	username = check_login()
	if username is None :
		return redirect(mode.server + 'login/')		
	
	if request.method == 'GET' :		
		my_picture = session['picture']	
		if session['skills'] is not None :
			skills = session['skills']['description']
		
			#description = [{'skill_code' : 'consulting' ,'skill_name' : 'consulting', 'skill_level' : 'intermediate', 'skill_domain' : 'industry'},] 	
			skills_row = ""
			for counter, skill in enumerate(skills, 0) :
				skill_level = 'Intermed.' if skill['skill_level'] == 'Intermediate' else skill['skill_level'] 
				form_row = """
					<div class="form-row">
						  <div class="col-3 col-sm-3 col-lg-3 col-xl-3">
                       
                            <div class="form-group">
								<p> """ + skill['skill_name'] + """</p>
							</div>
                         </div>
                           <div class="col-3 col-sm-3 col-lg-3 col-xl-3">
                         
                             <div class="form-group">
								<p>""" + skill['skill_domain'] + """</p>
							</div>
                         </div>
                           <div class="col-3 col-sm-3 col-lg-3 col-xl-3">
                         
                            <div class="form-group">
								<p> """ + skill_level + """</p>
							</div>	
                         </div>
                           <div class="col-3 col-sm-3 col-lg-3 col-xl-3">
                        
                              <div class="form-group">
								<button title="Delete first if you want to update." class="btn btn-secondary btn-sm" name="choice" value=""" + str(counter) + """ type="submit">Delete</button></div>
								</div>
                     </div>"""
				skills_row = form_row + skills_row									
		else :
			skills_row = ""
			
		return render_template('update_skills.html', picturefile=my_picture, username=username, skills_row=skills_row)
	
	if request.method == 'POST' :
	
		# session[skills'] =  {'version' : 1,   description: [{'skill_code' : 'consulting' ,'skill_name' : 'consulting', 'skill_level' : 'intermediate', 'skill_domain' : 'industry'},] 	
		
		# add a skill
		if request.form['choice'] == 'add' :
			skill_code = unidecode.unidecode(request.form['skill_name'].lower())
			skill_code = skill_code.replace(" ", "")
			skill_code = skill_code.replace("-", "")
			skill = {'skill_code' : skill_code,
									'skill_name' : request.form['skill_name'].capitalize(),
									'skill_level' : request.form['skill_level'],
									'skill_domain' : request.form['skill_domain']}
			if session['skills'] is None  :
				session['skills'] = dict()
				session['skills']['description'] = []
				session['skills']['version'] = 1
			
			else :
				pass
				
			for one_skill in session['skills']['description'] :
				if one_skill['skill_code'] == skill_code :
					flash('Skill alreday added', 'warning')
					return redirect(mode.server + 'user/update_skills/')
			if skill_code == "" :
				return redirect(mode.server + 'user/update_skills/')	
			
			session['skills']['description'].append(skill)												
			return redirect(mode.server + 'user/update_skills/')
		
		# update the skill document
		elif request.form['choice'] == 'update' :
			# case update before add first time
			if session['skills'] is None :
				return redirect( mode.server + 'user/')
			# update first time
			elif session['skills'].get('doc_id') is None :
				my_skills = Document('skills')
				data = {'version' : session['skills']['version'],  'description' : session['skills']['description']}
				(doc_id, ipfshash, transaction_hash) = my_skills.relay_add(session['workspace_contract'], data, mode)
				session['skills']['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] +':document:' + str(doc_id)  
				
			# standard update
			else :
				my_skills = Document('skills')
				data = {'version' : session['skills']['version'], 'description' : session['skills']['description']}
				(doc_id, ipfshash, transaction_hash) = my_skills.relay_update(session['workspace_contract'], session['skills']['doc_id'], data, mode)
				session['skills']['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] +':document:' + str(doc_id)  
			flash('Your skills have been updated', 'success')	
			return redirect( mode.server + 'user/')
		
		# delete the skill 	
		else :
			counter = request.form['choice']
			print(' skill to delete =', session['skills']['description'][int(counter)] )
			del session['skills']['description'][int(counter)]
			return redirect (mode.server + 'user/update_skills/')
			
def update_skills_from_elsewhere(skill_list) :
	for skill in skill_list :
		skill_code = unidecode.unidecode(request.form['skill_name'].lower())
		skill_code = skill_code.replace(" ", "")
		skill_code = skill_code.replace("-", "")
		skill = {'skill_code' : skill_code,
				'skill_name' : skill.capitalize(),
				'skill_level' : 'Intermediate',
				'skill_domain' : ''}
		if session['skills'] is None  :
			session ['skills'] = dict()
			session['skills']['description'] =[]
			session['skills']['version'] = 1
			
		found == False	
		for one_skill in session['skills']['description'] :
			if one_skill['skill_code'] == skill_code :
				found == True
				break
		if found == True :
			session['skills']['description'].append(skill)	
		if session['skills'].get('doc_id') is None :
			my_skills = Document('skills')
			data = {'version' : session['skills']['version'], 'description' : session['skills']['description']}
			(doc_id, ipfshash, transaction_hash) =my_skills.relay_add(session['workspace_contract'], data, mode, mydays=0) 
		else :
			my_skills = Document('skills')
			data = {'version' : session['skills']['version'],  'description' : session['skills']['description']}
			(doc_id, ipfshash, transaction_hash) = my_skills.relay_update(session['workspace_contract'], session['skills']['doc_id'], data, mode, mydays=0)													
	return execution
		
