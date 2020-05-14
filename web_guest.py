
import os
from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort
from flask_session import Session
from flask_api import FlaskAPI, status
import ipfshttpclient
from flask_fontawesome import FontAwesome
import http.client
import random
import csv
from datetime import timedelta, datetime
import json
from werkzeug.utils import secure_filename

# dependances
import Talao_message
import constante
from protocol import Identity, Data
from protocol import getresolver, getresume, load_register_from_file, getEmail, getPrivatekey, data_from_publickey
from protocol import ownersToContracts, contractsToOwners, readProfil, isdid
from protocol import deleteName, deleteDocument, deleteClaim, getdata, destroyWorkspace, addcertificate, canRegister_email, updateName, addkey, addName, delete_key
from protocol import username_and_email_list, deleteName, username_to_data
import environment
import web_create_identity
import web_certificate
import hcode

# environment setup
mode=environment.currentMode()
w3=mode.w3




def anonymous() :
	if request.method == 'GET' :
		return render_template('anonymous.html')
	else : 
		talent_name = request.form['username']
		return redirect(mode.server + 'guest/?username=' + talent_name)

#######################################################################################
#                        IDENTITY for GUEST
#######################################################################################


""" fonction principale d'affichage de l identité """
#@app.route('/guest/', methods = ['GET'])
def guest() :
	username = request.args.get('username')
	#workspace_contract = username_to_data(username, mode)['workspace_contract']	
	if username != session.get('username') :
		session.clear()
	if session.get('uploaded') is None :
		print('user first instanciation in guest')
		user = Identity(workspace_contract, mode)
		session['uploaded'] = True
		session['username'] = user.username		
		session['address'] = user.address
		session['workspace_contract'] = user.workspace_contract
		session['experience'] = user.experience
		session['personal'] = user.personal
		session['name'] = user.name
		session['contact'] = user.contact
		session['language'] = user.language
		session['education'] = user.education
		session['did'] = user.did
		if user.picture is None :
			session['picture'] = "anonymous1.png"
		else :
			session['picture'] = user.picture		
	#this_name = session['personal']['firstname']['data']+ ' '+ session['personal']['lastname']['data']
	#(radio, mylang1, mylang2, mylang3)= session['language']
	
	his_name = session['name']
	his_picture = session['picture']
	his_username = session['username'] 
	his_experience_list = session['experience']
	his_education_list = session['education']
	
	
	# experience
	his_experience = ''
	for experience in his_experience_list :
		exp_html = """<hr> 
				<b>Company</b> : """+experience['organization']['name']+"""<br>			
				<b>Title</b> : """+experience['title']+"""<br>
				<b>Description</b> : """+experience['description'][:100]+"""...<br>
				<p>
					
					<a class="text-secondary" href=/guest_data/"""+experience['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
		his_experience = his_experience + exp_html
	
	# personal
	his_personal = """ 
				<span><b>Firstname</b> : """+session['personal']['firstname']['data']+"""				
					
					<a class="text-secondary" href=/guest_data/"""+session['personal']['firstname']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Lastname</b> : """+session['personal']['lastname']['data']+"""
					
					<a class="text-secondary" href=/guest_data/"""+session['personal']['lastname']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
							
				<span><b>Username</b> : """+session['username']+"""
					
					<a class="text-secondary" href=/guest_data/"""+session['username'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Picture</b>  	
					
					<a class="text-secondary" href=/guest_data/"""+session['picture'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span>"""
	
	# contact
	if session['contact'] is None :
		his_contact =  ""
	else :
		his_contact = """<span>
					<b>Contact Email</b> : """ + session['contact']['data']['email'] + """<br>						
					<b>Contact Phone</b> : """ + session['contact']['data']['phone'] + """<br>				
					<b>Contact Twitter</b> : """ + session['contact']['data']['twitter'] + """<br>				
						
						<a class="text-secondary" href=/data/"""+session['contact']['id'] + """>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
						</a>
					</span>"""	
	
	# education
	his_education = ""
	for education in his_education_list :
		edu_html = """<hr> 
				<b>Organization</b> : """+education['data']['organization']+"""<br>			
				<b>Title</b> : """+education['data']['studyType']+"""<br>
				<b>Start Date</b> : """+education['data']['startDate']+"""<br>
				<b>End Date</b> : """+education['data']['endDate']+"""<br>				
				<p>
					
					<a class="text-secondary" href=/guest_data/"""+education['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
		his_education = his_education + edu_html
	
	# advanced
	his_advanced = """
					<b>Ethereum Chain</b> : """ + mode.BLOCKCHAIN + """<br>										
					<b>Username</b> : """ + session['username'] + """<br>										
					<b>DID</b> : """ + session['did'] 				
							
	# languages
	his_languages = ""
	
	# skills
	his_skills = ""
	
	
	his_services = ""
	
	
	# certificates
	his_certificates = ""
	
	
	return render_template('guest.html',
							name=his_name,
							personal=his_personal,
							contact=his_contact,
							experience=his_experience,
							education=his_education,
							languages=his_languages,
							skills=his_skills,
							services=his_services,
							advanced=his_advanced,
							certificate=his_certificates,			
							picturefile=his_picture,
							username=his_username)	


############################################################################################
#         DATA for GUEST
############################################################################################
""" on ne gere aucune information des data en session """


#@app.route('/guest_data/<dataId>', methods=['GET'])
def guest_data(dataId) :
	workspace_contract = '0x'+dataId.split(':')[3]
	if session.get('workspace_contract') != workspace_contract or 'events' not in session :
		print('dans guest_data2 de webserver.py error')	
	his_data = Data(dataId, mode)
			
	his_topic = his_data.topic.capitalize()
	
	his_visibility = his_data.encrypted.capitalize()
	
	his_issuer = """
				<span>
				<b>Name</b> : """ + his_data.issuer_name + """<br>
				<b>Username</b> : """ + his_data.issuer_username +"""<br>
				<b>Type</b> : """ + his_data.issuer_type + """<br>				
					<a class="text-secondary" href=/guest/issuer_explore/?issuer_username="""+his_data.issuer_username+""" >
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span>"""
	
	his_privacy = """ <b>Privacy</b> : """ + his_data.encrypted + """<br>"""
	
	
	if his_data.data_location == 'rinkeby' :
		path = """https://rinkeby.etherscan.io/tx/"""
	else :
		path = """https://etherscan.io/tx/"""
	his_advanced = """
		<!--		<b>Data Id</b> : """ + his_data.id + """<br>  -->
				<b>Created</b> : """ + his_data.created + """<br>	
				<b>Expires</b> : """ + his_data.expires + """<br>
				<b>Signature</b> : """ + his_data.signature + """<br>
				<b>Signature Check</b> : """ + his_data.signature_check + """<br>
				<b>Transaction Hash</b> : <a class = "card-link" href = """ + path + his_data.transaction_hash + """>"""+ his_data.transaction_hash + """</a><br>					
				<b>Data storage</b> : <a class="card-link" href=""" + his_data.data_location + """>""" + his_data.data_location + """</a>"""
	
	
	""" topic = Experience """
	if his_data.topic.capitalize() == "Experience"  :
		his_title = his_data.value['position']
		his_summary = his_data.value['summary']		
		his_value = """ 
				<b>Title</b> : """+his_data.value['position'] + """<br>
				<b>Company</b> : """+his_data.value['company']['name'] + """<br>
				<b>Manager</b> : """+his_data.value['company'].get('manager', 'Unknown') + """<br>
				<b>Manager Email</b> : """+his_data.value['company'].get('manager_email', 'Unknown') + """<br>
				<b>Start Date</b> : """+his_data.value['startDate'] + """<br>		
				<b>End Date</b> : """+his_data.value['endDate'] + """<br>
				<b>Skills</b> : """+his_data.value['skills'] + """<br>
				<b>Certificate</b> : """ + his_data.value['certificate_link']
	elif his_data.topic.capitalize() == "Education" :
		print('mydatatopic = ', his_data.topic)
		return 'work in progress'
	elif his_data.topic.capitalize() == "Employability" :
		print('mydatatopic = ', his_data.topic)
		return 'work in progress'		
	elif his_data.topic.capitalize() == "Certificate" :
		his_title = his_data.value['position']
		his_summary = his_data.value['summary']		
		his_value = """ 
				<b>Title</b> : """+his_data.value['position'] + """<br>
				<b>Company</b> : """+his_data.value['company']['name'] + """<br>
				<b>Manager</b> : """+his_data.value['company'].get('manager', 'Unknown') + """<br>
				<b>Manager Email</b> : """+his_data.value['company'].get('manager_email', 'Unknown') + """<br>
				<b>Start Date</b> : """+his_data.value['startDate'] + """<br>		
				<b>End Date</b> : """+his_data.value['endDate'] + """<br>
				<b>Skills</b> : """+his_data.value['skills'] + """<br>
				<b>Certificate</b> : """ + his_data.value['certificate_link']
	else :
		his_title = 'Profil'
		his_summary = ''		
		his_value = """<b>"""+his_data.topic.capitalize()+"""</b> : """+his_data.value
		
	if session.get('picture') is None :
		his_picture = 'anonymous1.jpeg'
	else :
		his_picture = session['picture']
			
	
	his_username = session['username']
	print('username =', his_username)	
	return render_template('guest_data.html',
							topic = his_topic,
							visibility = his_visibility,
							title = his_title,
							summary = his_summary,
							issuer=his_issuer,
							value = his_value,
							privacy = his_privacy,
							advanced = his_advanced,
							picturefile = his_picture,
							username = his_username)




# guest issuer explore On ne met rien en session
#@app.route('/guest/issuer_explore/', methods=['GET'])
def guest_issuer_explore() :
	issuer_username = request.args['issuer_username']
	issuer_workspace_contract = username_to_data(issuer_username, mode)['workspace_contract']
	issuer = Identity(issuer_workspace_contract, mode)
	# do something common
	issuer_name = issuer.name
	
	# advanced
	issuer_advanced = """
					<b>Ethereum Chain</b> : """ + mode.BLOCKCHAIN + """<br>										
					<b>Username</b> : """ + issuer_username + """<br>										
					<b>DID</b> : """ + issuer.did 				
	
	
	
	
	if issuer.type == 'person' :
		# do something specifc

		
		issuer_picture = "anonymous1.png" if issuer.picture is None else issuer.picture

		# personal
		issuer_personal = """ 
				<span><b>Firstname</b> : """+ issuer.personal['firstname']['data']+"""				
					
					<a class="text-secondary" href=/guest_data/""" + issuer.personal['firstname']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Lastname</b> : """+ issuer.personal['lastname']['data']+"""
					
					<a class="text-secondary" href=/guest_data/""" + issuer.personal['lastname']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Picture</b>  	
					
					<a class="text-secondary" href=/guest_data/"""+ issuer_picture + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span>"""
		
		
		
		
		
		return render_template('guest_person_issuer_identity.html',
							issuer_name=issuer_name,
							advanced=issuer_advanced,
							personal=issuer_personal,
							issuer_picturefile=issuer_picture)
	
	
	if issuer.type == 'company' :
		# do something specific
		
		# personal
		issuer_personal = """ 
				<span><b>Name</b> : """ + issuer.personal['name']['data'] + """				
					
					<a class="text-secondary" href=/guest_data/"""+ issuer.personal['name']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Website</b> : """+ issuer.personal['website']['data']+"""
					
					<a class="text-secondary" href=/guest_data/"""+ issuer.personal['website']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Contact</b> : """+ issuer.personal['contact']['data']+"""
					
					<a class="text-secondary" href=/guest_data/"""+ issuer.personal['contact']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Email</b> : """+ issuer.personal['email']['data']+"""
					
					<a class="text-secondary" href=/guest_data/""" + issuer.personal['email']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>"""
		
		return render_template('guest_company_issuer_identity.html',
							issuer_name=issuer_name,
							advanced=issuer_advanced,
							personal=issuer_personal)


