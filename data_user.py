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
#import http.client
#import random
#import csv
from datetime import timedelta, datetime
import json
#from werkzeug.utils import secure_filename

# dependances
#import Talao_message
import constante
from protocol import ownersToContracts, contractsToOwners, destroyWorkspace, save_image, partnershiprequest, remove_partnership, token_balance
#from protocol import delete_key, has_key_purpose, add_key
from protocol import Claim, File, Identity, Document, read_profil
import environment
import hcode
import ns



"""
# Centralized  route
import web_create_identity
import web_certificate
import talent_connect
#import web_guest
"""

# environment setup
mode = environment.currentMode()
w3 = mode.w3

def check_login(username) :
	if username is None or session.get('username_logged') is None or username != session.get('username_logged') :
		print('session aborted = ', session)
		session.clear()
		abort(403, description="Authentification required")
	else :
		return username



# gestion du menu de gestion des Events  """
def event_display(eventlist) :
	event_html = ""
	index = 0
	for key in sorted(eventlist, reverse=True) :
		index += 1
		date= key.strftime("%y/%m/%d")
		texte = eventlist[key]['alert']
		doc_id = eventlist[key]['doc_id']
		event_type = eventlist[key]['event']
		if doc_id is None :
			href = " "
		else :
			href = "href= /data/"+doc_id
		icon = 'class="fas fa-file-alt text-white"'
		background = 'class="bg-success icon-circle"'
		
		if event_type == 'DocumentRemoved' or event_type == 'ClaimRemoved' :
			icon = 'class="fas fa-trash-alt text-white"'
			background = 'class="bg-warning icon-circle"'	
		thisevent = """<a class="d-flex align-items-center dropdown-item" """ + href + """>
							<div class="mr-3"> <div """ + background + """><i """ + icon + """></i></div></div>
							<div>
								<span class="small text-gray-500">""" + date + """</span><br>
								<div class = "text-truncate">
                                <span>""" + texte + """</span></div>
                            </div>
                        </a>"""	
		event_html = event_html + thisevent 
	return event_html, index


############################################################################################
#         DATA 
############################################################################################
""" on ne gere aucune information des data en session """


#@app.route('/data/<dataId>', methods=['GET'])
def data(dataId) :
	username = check_login(session.get('username'))
	mypicture = 'anonymous1.jpeg' if session.get('picture') is None else session['picture']		
	my_event_html, my_counter =  event_display(session['events'])
	workspace_contract = '0x' + dataId.split(':')[3]
	support = dataId.split(':')[4]
	
	if support == 'document' : 
		doc_id = int(dataId.split(':')[5])			
		my_topic = dataId.split(':')[6]
		if my_topic in [ 'experience', 'certificate', 'kbis', 'kyc', 'education'] :
			my_data = Document(my_topic)
			exist = my_data.relay_get(workspace_contract, doc_id, mode) 	
		else :
			print('Error data in webserver.py, Class instance needed')	
			return
			
		#ID = 'did:talao:' + mode.BLOCKCHAIN+':'+ my_data.identity['workspace_contract'][2:]+':document:'+ str(my_data.doc_id)
		expires = my_data.expires
		my_topic = my_data.topic.capitalize()
	
	if support == 'claim' :
		claim_id = dataId.split(':')[5]
		my_data = Claim()
		my_data.get_by_id(workspace_contract, claim_id, mode) 
		#ID = 'did:talao:' + mode.BLOCKCHAIN+':'+ my_data.identity['workspace_contract'][2:]+':claim:'+ claim_id
		expires = 'Unlimited'
		my_topic = 'Personal'
		
	myvisibility = my_data.privacy
	issuer_is_white = False
	for issuer in session['whitelist'] :
		if issuer['workspace_contract'] == my_data.issuer['workspace_contract'] :
			issuer_is_white = True 		
	
	
	# issuer
	issuer_name = my_data.issuer['name'] if my_data.issuer['category'] == 2001 else my_data.issuer['firstname'] + ' ' +my_data.issuer['lastname']
	issuer_username = ns.get_username_from_resolver(my_data.issuer['workspace_contract'])
	issuer_username = 'Unknown' if issuer_username is None else issuer_username 
	issuer_type = 'Company' if my_data.issuer['category'] == 2001 else 'Person'
	
	myissuer = """
				<span>
				<b>Issuer</b>
				<li><b>Name</b> : """ + issuer_name + """<br></li>
				<li><b>Username</b> : """ + issuer_username +"""<br></li>
				<li><b>Type</b> : """ + issuer_type + """<br></li>"""
	
	if my_data.issuer['workspace_contract'] == session['workspace_contract'] :					
		myissuer = myissuer + """
				 <a class="text-warning">Sel Declaration</a>	
				</span>"""
	
	elif issuer_is_white :					
		myissuer = myissuer + """
				<a class="text-secondary" href=/user/issuer_explore/?issuer_username="""+ issuer_username +""" >
					<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
				</a><br>
				  <a class="text-info">This issuer is in my White List</a>			
				</span>"""		
	else :	
		myissuer = myissuer + """				
					<a class="text-secondary" href=/user/issuer_explore/?issuer_username="""+ issuer_username + """ >
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a><br>
					<a class="text-warning">This issuer is not in my White List</a>
				</span>"""
	
	
	# advanced """
	(location, link) = (my_data.data_location, my_data.data_location)
	path = """https://rinkeby.etherscan.io/tx/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/tx/"""	
	if support == 'document' :
		myadvanced = """
				<b>Advanced</b>
				<li><b>Document Id</b> : """ + str(doc_id) + """<br></li>
				<li><b>Privacy</b> : """ + myvisibility + """<br></li>
				<li><b>Created</b> : """ + my_data.created + """<br></li>	
				<li><b>Expires</b> : """ + expires + """<br></li>
				<li><b>Transaction Hash</b> : <a class = "card-link" href = """ + path + my_data.transaction_hash + """>"""+ my_data.transaction_hash + """</a><br></li>	
				<li><b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a></li>"""
	else :
		(location, link) = (mode.BLOCKCHAIN, "") if myvisibility == 'public' else (my_data.data_location, my_data.data_location)
		path = """https://rinkeby.etherscan.io/tx/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/tx/"""	
		myadvanced = """
				<b>Advanced</b>		
				<li><b>Claim Id</b> : """ + str(claim_id) + """<br></li>
				<li><b>Topic</b> : """ + str(my_data.topicname) + """<br></li>				
				<li><b>Privacy</b> : """ + myvisibility + """<br></li>
				<li><b>Created</b> : """ + my_data.created + """<br></li>	
				<li><b>Expires</b> : """ + expires + """<br></li>
				<li><b>Transaction Hash</b> : <a class = "card-link" href = """ + path + my_data.transaction_hash + """>"""+ my_data.transaction_hash + """</a><br></li>	
				<li><b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a></li>"""
		
	
	# value
	if my_topic.lower() == "experience"  :
		mytitle = my_data.title
		mysummary = my_data.description	
		myvalue = """ 
				<b>Data Content</b>
				<li><b>Title</b> : """+my_data.title + """<br></li>
				<li><b>Company Name</b> : """+my_data.company['name']+"""<br></li>
				<li><b>Contact Name</b> : """+my_data.company['contact_name']+"""<br></li>
				<li><b>Contact Email</b> : """+my_data.company['contact_email']+"""<br></li>
				<li><b>Contact Phone</b> : """+my_data.company['contact_phone']+"""<br></li>
				<li><b>Start Date</b> : """+my_data.start_date + """<br></li>		
				<li><b>End Date</b> : """+my_data.end_date+"""<br></li>
				<li><b>Skills</b> : """+ " ".join(my_data.skills)+"""</li>"""
				
	elif my_topic.lower() == "education" :
		mytitle = my_data.title
		mysummary = my_data.description	
		myvalue = """ 
				<b>Data Content</b>
				<li><b>Title</b> : """+my_data.title + """<br>
				<li><b>Organiation Name</b> : """+my_data.organization['name']+"""<br></li>
				<li><b>Contact Name</b> : """+my_data.organization['contact_name']+"""<br></li>
				<li><b>Contact Email</b> : """+my_data.organization['contact_email']+"""<br></li>
				<li><b>Contact Phone</b> : """+my_data.organization['contact_phone']+"""<br></li>
				<li><b>Start Date</b> : """+my_data.start_date + """<br></li>		
				<li><b>End Date</b> : """+my_data.end_date+"""<br></li>
				<li><b>Skills</b> : """+ " ".join(my_data.skills) +"""<br></li>
				<li><b>Diploma Link</b> : """+  my_data.certificate_link+"""</li>"""
	
	
	elif my_topic.lower() == "certificate" :
		
		mytitle = my_data.title
		mysummary = my_data.description	
		profil,category  = read_profil(my_data.issuer['workspace_contract'], mode, 'full')	
		issuer_name = "Unknown" if profil['name'] is None else profil['name']

		myvalue = """ 
				<b>Data Content</b>
				<li><b>Title</b> : """ + my_data.title + """<br></li>
				<li><b>Company Name</b> : """ + issuer_name + """<br></li>
				<li><b>Start Date</b> : """+ my_data.start_date + """<br></li>		
				<li><b>End Date</b> : """+ my_data.end_date + """<br></li>
				<li><b>Skills</b> : """+ "".join(my_data.skills) + """<br></li>
				<li><b>Delivery Quality</b> : """+ my_data.score_delivery + """<br></li>
				<li><b>Schedule Respect</b> : """+ my_data.score_schedule + """<br></li>
				<li><b>Communication Skill</b> : """+ my_data.score_communication + """<br></li>
				<li><b>Recommendation</b> : """+ my_data.score_recommendation + """<br></li>
				<li><b>Manager</b> : """+ my_data.manager+"""</li>"""

				
				

	elif my_topic.lower() == "kbis" :
		mytitle = "Kbis validated"
		mysummary = ""		
		myvalue = """ 
				<b>Data Content</b>
				<li><b>Name</b> : """ + my_data.name+ """<br></li>
				<li><b>Siret</b> : """ + my_data.siret + """<br></li>
				<li><b>Created</b> : """+ my_data.date + """<br></li>
				<li><b>Address</b> : """+ my_data.address + """<br></li>
				<li><b>Legal Form</b> : """+ my_data.legal_form + """<br></li>
				<li><b>Capital</b> : """+ my_data.capital + """<br></li>		
				<li><b>Naf</b> : """+ my_data.naf + """<br></li>	
				<li><b>Activity</b> : """+ my_data.activity+"""</li>""" 



	elif my_topic.lower() == "kyc" :
		mytitle = "ID validated by Talao"
		mysummary = ""		
		myvalue = """ 
				<b>Data Content</b>
				<li><b>Firstname</b> : """+ my_data.firstname + """<br></li>
				<li><b>Lastname</b> : """ + my_data.lastname + """<br></li>
				<li><b>Sex</b> : """+ my_data.sex + """<br></li>
				<li><b>Nationality</b> : """+ my_data.nationality + """<br></li>		
				<li><b>Birth Date</b> : """+ my_data.birthdate + """<br></li>
				<li><b>Date of Issue</b> : """+ my_data.date_of_issue + """<br></li>
				<li><b>Date of Expiration/b> : """+ my_data.date_of_expiration + """<br></li>
				<li><b>Authority</b> : """+ my_data.authority + """<br></li>
				<li><b>Country</b> : """+ my_data.country+"""</li>"""
			
				 

	elif my_topic.lower() == 'personal' :
		mytitle = 'Profil'
		mysummary = ''		
		myvalue = """<b>Data</b> : """+ my_data.claim_value 

	else :
		print('erreur my_topic dans data de webserver.py')
		return
			
	mydelete_link = "/talao/api/data/delete/"
	
	call_from = "/user/?username="+username
	my_verif = "<hr>" + myvalue + "<hr>" + myissuer +"<hr>" + myadvanced
	
	return render_template('data_check.html',
							event = my_event_html,
							counter = my_counter,
							picturefile = mypicture,
							name = session['name'],
							username = username,
							call_from=call_from,
							verif=my_verif,
							)
		
	"""return render_template('data.html',
							topic = my_topic,
							visibility = myvisibility,
							issuer = myissuer,
							title = mytitle,
							summary = mysummary,
							value = myvalue,
							advanced = myadvanced,
							delete_link = mydelete_link,
							event = my_event_html,
							counter = my_counter,
							picturefile = mypicture,
							name = session['name'],
							username = username)"""



#######################################################################################
#                        USER
#######################################################################################


""" fonction principale d'affichage de l identité """
#@app.route('/user/', methods = ['GET'])
def user() :
	username = check_login(request.args.get('username'))
	if session.get('uploaded') is None :
		print('start first instanciation user')		
		user = Identity(ns.get_data_from_username(username,mode)['workspace_contract'], mode, authenticated=True)
		print('end')
		""" clean up for resume  """
		user_dict = user.__dict__.copy()
		del user_dict['mode']
		del user_dict['aes']
		del user_dict['eventslist']
		del user_dict['partners']
		session['resume'] = user_dict
		
	
		session['uploaded'] = True
		session['type'] = user.type
		session['username'] = username	
		session['address'] = user.address
		session['workspace_contract'] = user.workspace_contract
		session['events']=  user.eventslist
		#session['controller'] = user.managementkeys
		session['issuer'] = user.issuer_keys
		session['whitelist'] = user.white_keys
		session['partner'] = user.partners
		session['did'] = user.did
		session['eth'] = user.eth
		session['token'] = user.token
		session['rsa_key'] = user.rsa_key
		session['private_key'] = user.private_key
		session['private_key_value'] = user.private_key_value
		session['relay_activated'] = user.relay_activated
		session['personal'] = user.personal
		session['identity_file'] = user.identity_file
		session['name'] = user.name
		session['picture'] = "anonymous1.png" if user.picture is None else user.picture
		session['signature'] = "picasso.jpg" if user.signature is None else user.signature
		print('dans user  ', session['picture'])
		session['secret'] = user.secret
		
		if user.type == 'person' :
			session['experience'] = user.experience
			session['certificate'] = user.certificate
			#session['language'] = user.language
			session['education'] = user.education	
			session['kyc'] = user.kyc
			#(radio, mylang1, mylang2, mylang3)= session['language']
			session['profil_title'] = user.profil_title	
		
		if user.type == 'company' :
			session['kbis'] = user.kbis
	
	my_event_html, my_counter =  event_display(session['events'])
	#controller_list = session['controller']
	relay = 'Activated' if session['relay_activated'] else 'Not Activated'
	
	
	
	
	# advanced
	relay_rsa_key = 'Yes' if session['rsa_key']  else 'No'
	relay_private_key = 'Yes' if session['private_key'] else 'No'
	path = """https://rinkeby.etherscan.io/address/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/address/"""	
	my_advanced = """
					<b>Ethereum Chain</b> : """ + mode.BLOCKCHAIN + """<br>	
					<b>Authentification Email</b> : """ + "to be done " + """<br>
					<b>Worskpace Contract</b> : <a class = "card-link" href = """ + path + session['workspace_contract'] + """>"""+ session['workspace_contract'] + """</a><br>					
					<b>Owner Wallet Address</b> : <a class = "card-link" href = """ + path + session['address'] + """>"""+ session['address'] + """</a><br>"""					
	
	if session['username'] != 'talao' :
		my_advanced = my_advanced + """				
					<hr><b>Relay Status : </b>""" + relay + """<br>
					<b>RSA Key</b> : """ + relay_rsa_key + """<br>
					<b>Private Key</b> : """ + relay_private_key +"""<hr>"""
	
	if session['type'] == 'person' :
		my_advanced = my_advanced + """<a href="/user/data_analysis/">Data Analysis</a>"""
	
	# TEST only
	if session['username'] != 'talao' :
		my_advanced = my_advanced + """<hr><br><a href="/user/test/">Test Only</a>"""

	
	
	
	# Partners
	if session['partner'] == [] :
		my_partner = """<a class="text-warning">No partner available</a>"""
	else :
		my_partner = ""	 
		for partner in session['partner'] :
			partner_username = ns.get_username_from_resolver(partner['workspace_contract'])
			partner_username = 'Unknown' if partner_username is None else partner_username
			if partner['authorized'] == 'Pending' :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner_username + """">"""+ partner_username + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )  
					<a class="text-secondary" href="/user/parner_reject/?partner_username=""" + partner_username+"""&amp;partner_workspace_contract=""" + partner['workspace_contract']+"""">
						<i data-toggle="tooltip" class="fa fa-thumbs-o-down" title="Reject">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/partner_authorize/?partner_username=""" + partner_username + """">
						<i data-toggle="tooltip" class="fa fa-thumbs-o-up" title="Authorize"></i>
					</a>
				</spn>"""	
			elif partner['authorized'] == 'Removed' :
				partner_html = ""		
			else :			
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner_username + """">"""+ partner_username + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )  
					<a class="text-secondary" href="/user/partner_remove/?partner_username=""" + partner_username +"""&amp;partner_workspace_contract=""" + partner['workspace_contract']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					
				</spn>"""
			my_partner = my_partner + partner_html + """<br>"""
	
	
	# Issuer for document, they have an ERC725 key 20002	
	if session['issuer'] == [] :
		my_issuer = """  <a class="text-warning">No data available</a>"""
	else :
		my_issuer = ""		
		for one_issuer in session['issuer'] :
			issuer_username = ns.get_username_from_resolver(one_issuer['workspace_contract'])
			issuer_username = 'Unknown' if issuer_username is None else issuer_username
			issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_issuer/?issuer_username="""+issuer_username +"""&amp;issuer_address="""+one_issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span>"""
			my_issuer = my_issuer + issuer_html + """<br>"""
	

	# whitelist	
	if session['whitelist'] == [] :
		my_white_issuer = """  <a class="text-warning">No data available</a>"""
	else :
		my_white_issuer = ""		
		for issuer in session['whitelist'] :
			issuer_username = ns.get_username_from_resolver(issuer['workspace_contract'])
			issuer_username = 'Unknown' if issuer_username is None else issuer_username
			issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_white_issuer/?issuer_username="""+issuer_username +"""&amp;issuer_address="""+issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span>"""
			my_white_issuer = my_white_issuer + issuer_html + """<br>"""
	

	# account	
	my_account = """ <b>ETH</b> : """ + str(session['eth'])+"""<br>				
					<b>token TALAO</b> : """ + str(session['token'])
	if session['username'] == 'talao' :
		relay_eth = mode.w3.eth.getBalance(mode.relay_address)/1000000000000000000
		relay_token = float(token_balance(mode.relay_address,mode))	
		talaogen_eth = mode.w3.eth.getBalance(mode.Talaogen_public_key)/1000000000000000000
		talaogen_token = float(token_balance(mode.Talaogen_public_key, mode))
		my_account = my_account + """<br><br> 
					<b>Relay ETH</b> : """ + str(relay_eth) + """<br>
					<b>Relay token Talao</b> : """ + str(relay_token) + """<br><br>
					<b>Talao Gen ETH</b> : """ + str(talaogen_eth) + """<br>
					<b>Talao Gen token Talao</b> : """ + str(talaogen_token)
					
	
	# file
	my_file = """<a href="/user/store_file/">Store Data</a><hr>"""
	for one_file in session['identity_file'] :
		file_html = """
				<b>File Name</b> : """+one_file['filename']+ """ ( """+ one_file['privacy'] + """ ) <br>			
				<b>Created</b> : """+ one_file['created'] + """<br>
				<p>
					<a class="text-secondary" href="/user/remove_experience/?experience_id=""" + one_file['id'] + """&experience_title="""+ one_file['filename'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					
					<a class="text-secondary" href=/user/download/""" + one_file['id'] + """>
						<i data-toggle="tooltip" class="fa fa-download" title="Download"></i>
					</a>
				</p>"""	
		my_file = my_file + file_html + """<br>"""
	
						
####################################################################################################
	# specific to person
####################################################################################################	
	if session['type'] == 'person' :
	
	# experience
	
		my_experience = """<a href="/user/add_experience/">Add Experience</a><hr>"""
		
		if len (session['experience']) == 0:
			my_experience = """<a class="text-danger">No Data Available</a>"""
		else :
			for experience in session['experience'] :
				exp_html = """
				<b>Company</b> : """+experience['company']['name']+"""<br>			
				<b>Title</b> : """+experience['title']+"""<br>
				<b>Description</b> : """+experience['description'][:100]+"""...<br>
				<p>
					<a class="text-secondary" href="/user/remove_experience/?experience_id=""" + experience['id'] + """&experience_title="""+ experience['title'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					
					<a class="text-secondary" href=/data/"""+ experience['id'] + """:experience>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""	
				my_experience = my_experience + exp_html + "<hr>"
			
			
		# education
		my_education = """<a href="/user/add_education/">Add Education</a><hr>"""
		if len (session['education']) == 0:
			my_education = my_education + """<a class="text-danger">No Data Available</a>"""
		else :
			for education in session['education'] :
				edu_html = """
				<b>Organization</b> : """+education['organization']['name']+"""<br>			
				<b>Title</b> : """+education['title'] + """<br>
				<b>Start Date</b> : """+education['start_date']+"""<br>
				<b>End Date</b> : """+education['end_date']+"""<br>				
				<p>		
					<a class="text-secondary" href="/user/remove_education/?education_id=""" + education['id'] + """&education_title="""+ education['title'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href=/data/"""+ education['id'] + """:education>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""	
				my_education = my_education + edu_html	+ "<hr>"
	
	
		# personal
		
		Topic = {'firstname' : 'Firstname',
				'lastname' : 'Lastname',
				'about' : 'About',
				'profil_title' : 'Title',
				'birthdate' : 'Birth Date',
				'contact_email' : 'Contact Email',
				'contact_phone' : 'Contact Phone',
				'postal_address' : 'Postal Address',
				'education' : 'Education'}							
		my_personal = """<a href="/user/picture/">Change Picture</a><br>
						<a href="/user/signature/">Change Signature</a><br>"""
		for topicname in session['personal'].keys() :
			if session['personal'][topicname]['claim_value'] is not None :
				topicname_value = session['personal'][topicname]['claim_value']
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':claim:' + session['personal'][topicname]['claim_id']
				topicname_privacy = ' (' + session['personal'][topicname]['privacy'] + ')'
				my_personal = my_personal + """ 
				<span><b>""" + Topic[topicname] + """</b> : """+ topicname_value + topicname_privacy +"""								
					<a class="text-secondary" href=/data/""" + topicname_id + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span><br>"""				
		my_personal = my_personal + """<a href="/user/update_personal_settings/">Update Data</a>"""
	
	
		
		# kyc
		if len (session['kyc']) == 0:
			my_kyc = """<a href="/user/request_proof_of_identity/">Request a Proof of Identity</a><hr>
					<a class="text-danger">No Proof of Identity available</a>"""
		else :	
			my_kyc = ""
			for kyc in session['kyc'] :
				kyc_html = """<hr> 
				<b>Firstname</b> : """+ kyc['firstname'] +"""<br>				
				<b>Lastname</b> : """+ kyc['lastname'] +"""<br>				
				<b>Birth Date</b> : """+ kyc['birthdate'] +"""<br>				
				
				<b>Sex</b> : """+ kyc['sex'] +"""<br>			
				<b>Nationality</b> : """+ kyc['nationality'] + """<br>
				<b>Date of Issue</b> : """+ kyc['date_of_issue']+"""<br>
				<b>Date of Expiration</b> : """+ kyc['date_of_expiration']+"""<br>
				<b>Authority</b> : """+ kyc['authority']+"""<br>
				<b>Country</b> : """+ kyc['country']+"""<br>				
				<b>Id</b> : """+ kyc['id']+"""<br>				
				<p>		
					<a class="text-secondary" href="/user/remove_education/?experience_id=""" + kyc['id'] + """&experience_title="""+ kyc['firstname'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href=/data/"""+ kyc['id'] + """:kyc>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""	
				my_kyc = my_kyc + kyc_html		
	
	
		# Alias
		if session['username'] != ns.get_username_from_resolver(session['workspace_contract']) :
			display_alias = False
			my_access = ""
		else :
			display_alias = True
			my_access_start = """<a href="/user/add_alias/">Add an Alias</a><hr> """
			my_access = ""
			access_list = ns.get_alias_list(session['workspace_contract'])
			for access in access_list :
				if access['username'] == session['username'] :
					access_html = """
					<span>""" + session['username'] + """ (logged)					
					</span>"""
				else :
					access_html = """
					<span>""" + access['username'] + """ : """ +  access['email'] +"""
						<a class="text-secondary" href="/user/remove_access/?username_to_remove="""+ access['username']+"""">
							<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">    </i>
						</a>
					</span>"""	
				my_access = my_access + access_html + """<br>""" 
			my_access = my_access_start + my_access
		
							
		# languages
		my_languages = ""
	
		# skills
		my_skills = ""
		
		# certificates
		if len (session['certificate']) == 0:
			my_certificates = """<a class="text-danger">No Data Available</a>"""
		else :
			my_certificates = ""
			for certificate in session['certificate'] :
				organization_name = ns.get_username_from_resolver(certificate['issuer']['workspace_contract'])
				organization_name = 'Unknon' if organization_name is None else organization_name
				cert_html = """<hr> 
				<b>Company</b> : """ + organization_name +"""<br>			
				<b>Title</b> : """ + certificate['title']+"""<br>
				<b>Description</b> : """ + certificate['description'][:100]+"""...<br>

				<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """&call_from=user>Display Certificate</a><br>
				<p>
					<a class="text-secondary" href="/user/remove_certificate/?certificate_id=""" + certificate['id'] + """&certificate_title="""+ certificate['title'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					
					
					<a class="text-secondary" href=/data/""" + certificate['id'] + """:certificate> 
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""	
				my_certificates = my_certificates + cert_html
	
		
		return render_template('person_identity.html',
							name=session['name'],
							display_alias = display_alias,
							profil_title=session['profil_title'],
							personal=my_personal,
							kyc=my_kyc,
							experience=my_experience,
							education=my_education,
							languages=my_languages,
							skills=my_skills,
							certificates=my_certificates,
							access=my_access,
							partner=my_partner,
							issuer=my_issuer, 
							whitelist=my_white_issuer,
							advanced=my_advanced,
							event=my_event_html,
							counter=my_counter,
							account=my_account,
							picturefile=session['picture'],
							digitalvault= my_file,
							username=session['username'])	

####################################################################################################
	# specific to company
####################################################################################################	

	else :
		
		# Manager
		
		if session['username'] != ns.get_username_from_resolver(session['workspace_contract']) :
			display_manager = False
			my_access = ""
		else :
			display_manager = True
			my_access_start = """<a href="/user/add_manager/">Add a Manager</a><hr> """
			my_access = ""
			access_list = ns.get_manager_list(session['workspace_contract'])
			for access in access_list :
				if access['username'] == session['username'] :
					access_html = """
					<span>""" + session['username'] + """ (logged)					
					</span>"""
				else :
					access_html = """
					<span>""" + access['username'] + """ : """ +  access['email'] +"""
					<a class="text-secondary" href="/user/remove_access/?username_to_remove="""+ access['username']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">    </i>
					</a>
					</span>"""	
				my_access = my_access + access_html + """<br>""" 
			my_access = my_access_start + my_access
		
		
		# API
		my_api = """ 
				<b>Login</b> : """+ session['workspace_contract'] +"""<br>				
				<b>Secret</b> : """+ session['secret'] + """<br>
				<b>Client White List</b> : to completed <br>	
				<br><a href="/user/api_whitelist/">Add client to your White List for APIs</a>"""		
				
		
		# kbis
		if len (session['kbis']) == 0:
			my_kbis = """<a href="/user/request_proof_of_identity/">Request a Proof of Identity</a><hr>
					<a class="text-danger">No Proof of Identity available</a>"""
		else :	
			my_kbis = ""
			for kbis in session['kbis'] :
				kbis_html = """
				<b>Name</b> : """+ kbis['name'] +"""<br>				
				<b>Siret</b> : """+ kbis['siret'] +"""<br>			
				<b>Creation</b> : """+ kbis['date'] + """<br>
				<b>Capital</b> : """+ kbis['capital']+"""<br>
				<b>Address</b> : """+ kbis['address']+"""<br>				
				<p>		
					<a class="text-secondary" href="/user/remove_education/?experience_id=""" + kbis['id'] + """&experience_title="""+ kbis['name'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href=/data/"""+ kbis['id'] + """:kbis>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
				my_kbis = my_kbis + kbis_html		
	
		
		# company settings
		my_personal = """<a href="/user/picture/">Change Logo</a><br>"""
		for topicname in session['personal'].keys() :
			if session['personal'][topicname]['claim_value'] is not None :
				topicname_value = session['personal'][topicname]['claim_value']
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':claim:' + session['personal'][topicname]['claim_id']
				topicname_privacy = ' (' + session['personal'][topicname]['privacy'] + ')'
				my_personal = my_personal + """ 
				<span><b>""" + topicname + """</b> : """+ topicname_value + topicname_privacy +"""								
					<a class="text-secondary" href=/data/""" + topicname_id + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>"""				
		my_personal = my_personal + """<a href="/user/update_company_settings/">Update Company Data</a>"""
		
		
		return render_template('company_identity.html',
							manager=my_access,
							display_manager= display_manager,
							name = session['name'],
							personal=my_personal,
							kbis=my_kbis,
							partner=my_partner,
							api=my_api,
							whitelist=my_white_issuer,
							advanced=my_advanced,
							event=my_event_html,
							account=my_account,
							counter=my_counter,
							picturefile=session['picture'],
							digitalvault=my_file,
							username=session['username'])	
		
		
###########################  END OF USER #####################################	
