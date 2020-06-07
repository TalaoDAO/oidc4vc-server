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
#from protocol import getresolver, getresume, load_register_from_file, getPrivatekey, data_from_publickey
from protocol import ownersToContracts, contractsToOwners
from protocol import destroyWorkspace, canRegister_email, updateName
from protocol import delete_key, has_key_purpose, addkey
from protocol import username_and_email_list, deleteName, username_to_data, getUsername, addName
from protocol import savepictureProfile, partnershiprequest, remove_partnership
from protocol import Experience, Claim, Education, File, Identity, Certificate, Kbis, Kyc
import environment
import hcode
# Centralized  route
import web_create_identity
import web_certificate
import talent_connect
#import web_guest

# environment setup
mode=environment.currentMode()
w3=mode.w3

UPLOAD_FOLDER = './uploads'

# Flask and Session setup	
#app = FlaskAPI(__name__)
app = Flask(__name__)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'redis'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=100)
app.config['SESSION_FILE_THRESHOLD'] = 100  
app.config['SECRET_KEY'] = "OCML3BRawWEUeaxcuKHLpw"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Session(app)

fa = FontAwesome(app)


# Centralized @route for web_create_identity
app.add_url_rule('/register/',  view_func=web_create_identity.authentification, methods = ['GET', 'POST'])
app.add_url_rule('/register/code/', view_func=web_create_identity.POST_authentification_2, methods = ['POST'])

# Centralized @route to display certificates
app.add_url_rule('/certificate/<data>',  view_func=web_certificate.show_certificate)
app.add_url_rule('/certificate/verify/<dataId>',  view_func=web_certificate.certificate_verify, methods = ['GET'])

# Centralized @route to APIs
app.add_url_rule('/api/v1/talent-connect/',  view_func=talent_connect.get, methods = ['GET'])
app.add_url_rule('/api/talent-connect/',  view_func=talent_connect.get, methods = ['GET'])
app.add_url_rule('/talent-connect/',  view_func=talent_connect.get, methods = ['GET'])


def check_login(username) :
	if username is None or session.get('username_logged') is None or username != session.get('username_logged') :
		print('session aborted = ', session)
		session.clear()
		abort(403, description="Authentification required")
	else :
		return username


def is_username_in_list(my_list, username) :
	new_list = [user for user in my_list if user['username'] == username]
	if len(new_list) != 0 :
		return True
	else :
		return False


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

"""
def analysis(data) :
	for e in data['experience'] :
		
"""


# Starter with 3 options, login and logout
@app.route('/starter/', methods = ['GET', 'POST'])
def starter() :
		if request.method == 'GET' :
			return render_template('starter.html')
		else :
			start = request.form['start']
			if start == 'user' :
				return redirect(mode.server + 'login/')
			elif start == 'quick' :
				return redirect(mode.server + 'register/')
			elif start == 'advanced' :
				return redirect(mode.server + 'starter/') # tobe done
			else :
				pass

@app.route('/login/', methods = ['GET', 'POST'])
def login() :
	session.clear()
	if request.method == 'GET' :
		return render_template('login.html')		
	if request.method == 'POST' :
		session['username_to_log'] = request.form['username']
		if username_to_data(session['username_to_log'], mode) is None :
			flash('Username not found')		
			return render_template('login.html')
		email_to_log = username_to_data(session['username_to_log'], mode)['email']
		# secret code to send by email
		if session.get('code') is None :
			session['code'] = str(random.randint(100000, 999999))
			session['try_number'] = 1
			Talao_message.messageAuth(email_to_log, str(session['code']))
			print('secret code sent = ', session['code'])
			flash('Secret Code sent')
		else :
			print("secret code already sent")
			flash("Secret Code already sent")
		return render_template("login_2.html")

# recuperation du code saisi
@app.route('/login/authentification/', methods = ['POST'])
def login_2() :
	if session.get('username_to_log') is None or session.get('code') is None :
		flash("Authentification expired")		
		return render_template('login.html')
	code = request.form['code']
	session['try_number'] +=1
	print('code retourné = ', code)
	
	if code == session['code'] or code == "123456": # pour les tests
		session['username_logged'] = session['username_to_log']
		del session['username_to_log']
		del session['try_number']
		del session['code'] 
		return redirect(mode.server + 'user/?username=' + session['username_logged'])		
	
	elif session['try_number'] > 3 :
		flash("Too many trials (3 max)")
		return render_template("login.html")
		
	else :	
		if session['try_number'] == 2 :			
			flash('This code is incorrect, 2 trials left')
		if session['try_number'] == 3 :
			flash('This code is incorrect, 1 trial left')
		return render_template("login_2.html")	
	
# logout
@app.route('/logout/', methods = ['GET'])
def logout() :
	session.clear()
	return render_template('login.html')

############################################################################################
#         DATA for USER
############################################################################################
""" on ne gere aucune information des data en session """


@app.route('/data/<dataId>', methods=['GET'])
def data(dataId) :
	username = check_login(session.get('username'))
	mypicture = 'anonymous1.jpeg' if session.get('picture') is None else session['picture']		
	my_event_html, my_counter =  event_display(session['events'])
	workspace_contract = '0x' + dataId.split(':')[3]
	support = dataId.split(':')[4]
		
	if support == 'document' : 
		doc_id = int(dataId.split(':')[5])			
		my_topic = dataId.split(':')[6]
		if my_topic == 'experience' :
			my_data = Experience()
			my_data.relay_get_experience(workspace_contract, doc_id, mode) 
		if my_topic == 'education' :
			my_data = Education()
			my_data.relay_get_education(workspace_contract, doc_id, mode) 
		if my_topic == 'kyc' :
			my_data = Kyc()
			my_data.relay_get_kyc(workspace_contract, doc_id, mode) 	
		if my_topic == 'kbis' :
			my_data = Kbis()
			print(my_data.__dict__)
			my_data.relay_get_kbis(workspace_contract, doc_id, mode) 	
		else :
			print('Error data in webserver.py, Class instance needed')	
			return
			
		ID = 'did:talao:' + mode.BLOCKCHAIN+':'+ my_data.identity['workspace_contract'][2:]+':document:'+ str(my_data.doc_id)
		expires = my_data.expires
		my_topic = my_data.topic.capitalize()
	
	if support == 'claim' :
		claim_id = dataId.split(':')[5]
		my_data = Claim()
		my_data.get_by_id(workspace_contract, claim_id, mode) 
		print(my_data.__dict__)
		ID = 'did:talao:' + mode.BLOCKCHAIN+':'+ my_data.identity['workspace_contract'][2:]+':claim:'+ claim_id
		expires = 'Unlimited'
		my_topic = 'Personal'
		
	myvisibility = my_data.privacy
	issuer_is_white = False
	for issuer in session['whitelist'] :
		if issuer['username'] == my_data.issuer['username'] :
			issuer_is_white = True 		
	
	
	# issuer
	issuer_name = my_data.issuer['name'] if my_data.issuer['type'] == 'Company' else my_data.issuer['firstname'] + ' ' +my_data.issuer['lastname']
	if my_data.issuer['username'] == session['username']:					
		myissuer = """
				<span>
				<b>Name</b> : """ + issuer_name + """<br>
				<b>Username</b> : """ + my_data.issuer['username'] +"""<br>
				</span>"""
	
	elif issuer_is_white :					
		myissuer = """
				<span>
				<b>Name</b> : """ + issuer_name + """<br>
				<b>Username</b> : """ + my_data.issuer['username'] +"""<br>
				<b>Type</b> : """ + my_data.issuer['type'] + """<br>
				<a class="text-secondary" href=/user/issuer_explore/?issuer_username="""+my_data.issuer['username']+""" >
					<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
				</a><br>
				  <a class="text-info">This issuer is in my White List</a>			
				</span>"""		
	else :	
		myissuer = """
				<span>
				<b>Name</b> : """ + issuer_name + """<br>
				<b>Username</b> : """ + my_data.issuer['username'] +"""<br>
				<b>Type</b> : """ + my_data.issuer['type'] + """<br>				
					<a class="text-secondary" href=/user/issuer_explore/?issuer_username="""+my_data.issuer['username'] + """ >
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a><br>
					<a class="text-warning">This issuer is not in my White List</a>
				</span>"""
	
	
	# advanced """
	(location, link) = (mode.BLOCKCHAIN, "") if myvisibility == 'public' else (my_data.data_location, my_data.data_location)
	path = """https://rinkeby.etherscan.io/tx/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/tx/"""	
	if support == 'document' :
		myadvanced = """
				<b>Document Id</b> : """ + str(doc_id) + """<br>
				<b>Privacy</b> : """ + myvisibility + """<br>
				<b>Created</b> : """ + my_data.created + """<br>	
				<b>Expires</b> : """ + expires + """<br>
				<b>Transaction Hash</b> : <a class = "card-link" href = """ + path + my_data.transaction_hash + """>"""+ my_data.transaction_hash + """</a><br>	
				<b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a>"""
	else :
		myadvanced = """
				<b>Claim Id</b> : """ + str(claim_id) + """<br>
				<b>Topic</b> : """ + str(my_data.topic_value) + """<br>				
				<b>Privacy</b> : """ + myvisibility + """<br>
				<b>Created</b> : """ + my_data.created + """<br>	
				<b>Expires</b> : """ + expires + """<br>
				<b>Transaction Hash</b> : <a class = "card-link" href = """ + path + my_data.transaction_hash + """>"""+ my_data.transaction_hash + """</a><br>	
				<b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a>"""
		
	
	# value
	if my_topic == "Experience"  :
		mytitle = my_data.title
		mysummary = my_data.description	
		myvalue = """ 
				<b>Title</b> : """+my_data.title + """<br>
				<b>Company Name</b> : """+my_data.company['name']+"""<br>
				<b>Contact Name</b> : """+my_data.company['contact_name']+"""<br>
				<b>Contact Email</b> : """+my_data.company['contact_email']+"""<br>
				<b>Contact Phone</b> : """+my_data.company['contact_phone']+"""<br>
				<b>Start Date</b> : """+my_data.start_date + """<br>		
				<b>End Date</b> : """+my_data.end_date+"""<br>
				<b>Skills</b> : """+ " ".join(my_data.skills)
				
	elif my_topic == "Education" :
		mytitle = my_data.title
		mysummary = my_data.description	
		myvalue = """ 
				<b>Title</b> : """+my_data.title + """<br>
				<b>Organiation Name</b> : """+my_data.organization['name']+"""<br>
				<b>Contact Name</b> : """+my_data.organization['contact_name']+"""<br>
				<b>Contact Email</b> : """+my_data.organization['contact_email']+"""<br>
				<b>Contact Phone</b> : """+my_data.organization['contact_phone']+"""<br>
				<b>Start Date</b> : """+my_data.start_date + """<br>		
				<b>End Date</b> : """+my_data.end_date+"""<br>
				<b>Skills</b> : """+ " ".join(my_data.skills) +"""<br>
				<b>Diploma Link</b> : """+  my_data.certificate_link
	
	
	elif my_topic == "Certificate" :
		mytitle = my_data.title
		mysummary = my_data.description		
		myvalue = """ 
				<b>Title</b> : """ + my_data.title + """<br>
				<b>Company Name</b> : """ + my_data.company['name'] + """<br>
				<b>Contact Name</b> : """+ my_data.company['contact_name'] + """<br>
				<b>Contact Email</b> : """+ my_data.company['contact_email'] + """<br>
				<b>Start Date</b> : """+ my_data.start_date + """<br>		
				<b>End Date</b> : """+ my_data.end_date + """<br>
				<b>Skills</b> : """+ my_data.skills 

	elif my_topic == "Kbis" :
		mytitle = "Kbis validated"
		mysummary = ""		
		myvalue = """ 
				<b>Name</b> : """ + my_data.name+ """<br>
				<b>Siret</b> : """ + my_data.siret + """<br>
				<b>Created</b> : """+ my_data.date + """<br>
				<b>Address</b> : """+ my_data.address + """<br>	
				<b>Legal Form</b> : """+ my_data.legal_form + """<br>
				<b>Capital</b> : """+ my_data.capital + """<br>		
				<b>Naf</b> : """+ my_data.naf + """<br>	
				<b>Activity</b> : """+ my_data.activity 


	elif my_topic == "kyc" :
		mytitle = "ID validated"
		mysummary = ""		
		myvalue = """ 
				<b>Firstname</b> : """+ my_data.firstname + """<br>
				<b>Lastname</b> : """ + my_data.lastname + """<br>
				<b>Sex</b> : """+ my_data.sex + """<br>
				<b>Nationality</b> : """+ my_data.nationality + """<br>		
				<b>Birth Date</b> : """+ my_data.birthdate + """<br>
				<b>Date of Issue</b> : """+ my_data.date_of_issue 

	elif my_topic == 'Personal' :
		mytitle = 'Profil'
		mysummary = ''		
		myvalue = """<b>Data</b> : """+ my_data.claim_value 

	else :
		print('erreur my_topic dans data de webserver.py')
		return
			
	mydelete_link = "/talao/api/data/delete/"
	
	myusername = my_data.issuer['username']
		
	return render_template('data.html',
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
							username = myusername)



#######################################################################################
#                        IDENTITY
#######################################################################################


""" fonction principale d'affichage de l identité """
@app.route('/user/', methods = ['GET'])
def user() :
	username = check_login(request.args.get('username'))
	
	if session.get('uploaded') is None :
		print('first instanciation user')		
		user = Identity(username_to_data(username,mode)['workspace_contract'], mode, authenticated=True)
		
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
		session['relay_activated'] = user.relay_activated
		session['personal'] = user.personal
		session['identity_file'] = user.identity_file
		session['name'] = user.name
		session['picture'] = "anonymous1.png" if user.picture is None else user.picture
		session['workspace_email'] = user.email
		session['secret'] = user.secret
		
		if user.type == 'person' :
			session['experience'] = user.experience
			session['certificate'] = user.certificate
			#session['language'] = user.language
			session['education'] = user.education	
			session['kyc'] = user.kyc
			#(radio, mylang1, mylang2, mylang3)= session['language']	
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
					<b>Owner Wallet Address</b> : <a class = "card-link" href = """ + path + session['address'] + """>"""+ session['address'] + """</a><br>					
					<b>Relay Status : </b>""" + relay + """<br>
					<b>RSA Key</b> : """ + relay_rsa_key + """<br>
					<b>Private Key</b> : """ + relay_private_key
	my_advanced = my_advanced + """<hr><a href="">Delete Identity</a>"""
	if session['private_key'] :
		my_advanced = my_advanced + """<br><a href="">Transfer Ownership</a>"""

	
	
	# Partners
	if relay == 'Activated' and session['rsa_key']   :
		my_partner_start = """<a href="/user/request_partnership/">Request a Partnership</a><hr> """
	else :
		my_partner_start = ""				
	my_partner = ""
	for partner in session['partner'] :
		partner_username = getUsername(partner['workspace_contract'], mode)
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
	my_partner = my_partner_start + my_partner 	
	
	
	
	# Issuer for document, they have an ERC725 key 20002	
	if relay == 'Activated':
		my_issuer_start = """<a href="/user/add_issuer/">Authorize an Issuer</a><hr> """
	else :
		my_issuer_start = ""	
	my_issuer = ""		
	for issuer in session['issuer'] :
		issuer_username = getUsername(issuer['workspace_contract'], mode)
		issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_issuer/?issuer_username="""+issuer_username +"""&amp;issuer_address="""+issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span>"""
		my_issuer = my_issuer + issuer_html + """<br>"""
	my_issuer = my_issuer_start + my_issuer
	
	
	

	# whitelist	
	if relay  == 'Activated':
		my_white_start = """<a href="/user/add_white_issuer/">Add a new Issuer</a><hr> """
	else :
		my_white_start = ""	
	my_white_issuer = ""		
	for issuer in session['whitelist'] :
		issuer_username = getUsername(issuer['workspace_contract'], mode)
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
	my_white_issuer = my_white_start + my_white_issuer
	


	# account
	my_account = """ <b>Balance ETH</b> : """ + str(session['eth'])+"""<br>				
					<b>Balance TALAO</b> : """ + str(session['token'])
	
	
	
	# file
	my_file = """<a href="/user/store_file/">Store Data</a>"""
	for one_file in session['identity_file'] :
		file_html = """<hr> 
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
		my_file = my_file + file_html
	
						
####################################################################################################
	# specific to person
####################################################################################################	
	if session['type'] == 'person' :
	
	# experience
		my_experience = ''
		for experience in session['experience'] :
			exp_html = """<hr> 
				<b>Company</b> : """+experience['company']['name']+"""<br>			
				<b>Title</b> : """+experience['title']+"""<br>
				<b>Description</b> : """+experience['description'][:100]+"""...<br>
				<p>
					<a class="text-secondary" href="/user/remove_experience/?experience_id=""" + experience['id'] + """&experience_title="""+ experience['title'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					
					<a class="text-secondary" href=/data/"""+ experience['id'] + """:experience>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
			my_experience = my_experience + exp_html
			
			
		# education
		my_education = ""
		for education in session['education'] :
			edu_html = """<hr> 
				<b>Organization</b> : """+education['organization']['name']+"""<br>			
				<b>Title</b> : """+education['title'] + """<br>
				<b>Start Date</b> : """+education['start_date']+"""<br>
				<b>End Date</b> : """+education['end_date']+"""<br>				
				<p>		
					<a class="text-secondary" href="/user/remove_education/?experience_id=""" + education['id'] + """&experience_title="""+ education['title'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href=/data/"""+ education['id'] + """:education>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
			my_education = my_education + edu_html		
	
	
		# personal
		my_personal = """<a href="/user/picture/">Change Picture</a><br>"""
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
					<a class="text-secondary" href=/data/"""+ kyc['id'] + """:kbis>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
				my_kyc = my_kyc + kyc_html		
	
	
		# alias
		my_access_start = """<a href="/user/add_access/">Add an Alias</a><hr> """
		my_access = ""
		access_list = username_and_email_list(session['workspace_contract'], mode)
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
		my_certificates = ""
		for certificate in session['certificate'] :
			cert_html = """<hr> 
				<b>Company</b> : """ + certificate['organization']['name']+"""<br>			
				<b>Title</b> : """ + certificate['title']+"""<br>
				<b></b><a href= """ + mode.server +  """certificate/did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:claim:""" + certificate['certificate_link'] + """>Display Certificate</a><br>
				<p>
					<a class="text-secondary" href="#remove">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					
					<a class="text-secondary" href=/data/""" + certificate['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
			my_certificates = my_certificates + cert_html
	
		
		return render_template('person_identity.html',
							name=session['name'],
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
		
		# username, cf NameService which is a stand alone tool.
		my_access_start = """<a href="/user/add_access/">Add a Manager</a><hr> """
		my_access = ""
		access_list = username_and_email_list(session['workspace_contract'], mode)
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
				<b>Password</b> : """+ session['secret']			
				
		
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
		my_personal = """<a href="/user/picture/">Change Picture</a><br>"""
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
		my_personal = my_personal + """<a href="/user/update_company_settings/">Update Data</a>"""
		
		
		return render_template('company_identity.html',
							access=my_access,
							name = session['name'],
							personal=my_personal,
							kbis=my_kbis,
							partner=my_partner,
							api=my_api,
							issuer=my_issuer,
							whitelist=my_white_issuer,
							advanced=my_advanced,
							event=my_event_html,
							account=my_account,
							counter=my_counter,
							picturefile=session['picture'],
							digitalvault=my_file,
							username=session['username'])	
		
		
###########################  END OF IDENTITY #####################################	

# picture
@app.route('/user/picture/', methods=['GET', 'POST'])
def photo() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('picture.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		if 'image' not in request.files :
			print('No file ')
		myfile = request.files['image']
		filename = secure_filename(myfile.filename)
		myfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		picturefile = UPLOAD_FOLDER + '/' + filename
		savepictureProfile(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, picturefile, mode, synchronous = False)	
		print('picture file = ',picturefile)
		session['picture'] = filename			
		return redirect(mode.server + 'user/?username=' + username)

@app.route('/faq/', methods=['GET'])
def faq() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('faq.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)

# issuer explore On ne met rien en session
@app.route('/user/issuer_explore/', methods=['GET'])
def issuer_explore() :
	username = check_login(session.get('username'))	
	issuer_username = request.args['issuer_username']
	issuer_workspace_contract = username_to_data(issuer_username, mode)['workspace_contract']
	
	issuer = Identity(issuer_workspace_contract, mode)
	
	# do something common
	my_event_html, my_counter =  event_display(session['events'])
	my_name = session['name']
	issuer_name = issuer.name
	my_picture = session['picture'] 
	
	# advanced
	path = """https://rinkeby.etherscan.io/address/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/address/"""	
	issuer_advanced = """
					<b>Ethereum Chain</b> : """ + mode.BLOCKCHAIN + """<br>										
					<b>Username</b> : """ + issuer_username + """<br>										
					<b>Worskpace Contract</b> : <a class = "card-link" href = """ + path + issuer.workspace_contract + """>"""+ issuer.workspace_contract + """</a><br>					
					<b>Owner Wallet Address</b> : <a class = "card-link" href = """ + path + issuer.address + """>"""+ issuer.address + """</a>"""					

	
	if issuer.type == 'person' :
		# do something specifc	
		issuer_picture = "anonymous1.png" if issuer.picture is None else issuer.picture
	
		# personal
		issuer_personal = """ <span><b>Username : </b> : """ + getUsername(issuer.workspace_contract, mode)+"""<br>"""			
		for topic_name in issuer.personal.keys() : 
			if issuer.personal[topic_name]['claim_value'] is not None :
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer.workspace_contract[2:] + ':claim:' + issuer.personal[topic_name]['claim_id']
				issuer_personal = issuer_personal + """ 
				<span><b>"""+ key +"""</b> : """+ issuer.personal[topic_name]['claim_value']+"""				
					
					<a class="text-secondary" href=/data/""" + topicname_id + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>"""				
		issuer_personal = issuer_personal +	"""	<span><b>Picture</b>  	
					<a class="text-secondary" href=/data/"""+ issuer_picture + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span>"""

		# experience
		issuer_experience = ''
		for experience in issuer.experience :
			exp_html = """<hr> 
				<b>Company</b> : """+experience['organization']['name']+"""<br>			
				<b>Title</b> : """+experience['title']+"""<br>
				<b>Description</b> : """+experience['description'][:100]+"""...<br>
				<p>
					
					
					<a class="text-secondary" href=/data/"""+experience['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
			issuer_experience = issuer_experience + exp_html
		
		# certificates
		issuer_certificates = ""
		for certificate in issuer.certificate :
			cert_html = """<hr> 
				<b>Company</b> : """ + certificate['organization']['name']+"""<br>			
				<b>Title</b> : """ + certificate['title']+"""<br>
				<b></b><a href= """ + mode.server +  """certificate/did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer.workspace_contract[2:] + """:claim:""" + certificate['certificate_link'] + """>Display Certificate</a><br>
				<p>
					<a class="text-secondary" href=/data/""" + certificate['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
			issuer_certificates = issuer_certificates + cert_html
		
		return render_template('person_issuer_identity.html',
							issuer_name=issuer_name,
							username=username,
							name=my_name,
							advanced=issuer_advanced,
							personal=issuer_personal,
							experience=issuer_experience,
							certificates=issuer_certificates,
							event=my_event_html,
							counter=my_counter,
							picturefile = my_picture,
							issuer_picturefile=issuer_picture)
	
	
	if issuer.type == 'company' :
		# do something specific
		
		# kbis
		kbis_list = issuer.kbis
		if len (kbis_list) == 0:
			my_kbis = """<a href="/user/request_proof_of_identity/">Request a Proof of Identity</a><hr>
					<a class="text-danger">No Proof of Identity available</a>"""
		else :	
			my_kbis = ""
			for kbis in kbis_list :
				kbis_html = """
				<b>Name</b> : """+ kbis['name'] +"""<br>				
				<b>Siret</b> : """+ kbis['siret'] +"""<br>			
				<b>Creation</b> : """+ kbis['date'] + """<br>
				<b>Capital</b> : """+ kbis['capital']+"""<br>
				<b>Address</b> : """+ kbis['address']+"""<br>				
				<p>		
					
					<a class="text-secondary" href=/data/"""+ kbis['id'] + """:kbis>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
				my_kbis = my_kbis + kbis_html		
		
		# personal
		issuer_personal = """ <span><b>Username : </b> : """ + getUsername(issuer.workspace_contract, mode)	+ """<br>"""		
		for topic_name in issuer.personal.keys() :
			if issuer.personal[topic_name]['claim_value'] is not None :
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer.workspace_contract[2:] + ':claim:' + issuer.personal[topic_name]['claim_id']
				issuer_personal = issuer_personal + """ 
				<span><b>"""+ topic_name +"""</b> : """+ issuer.personal[topic_name]['claim_value']+"""				
					
					<a class="text-secondary" href=/data/""" + topicname_id + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>"""
					
					
		return render_template('company_issuer_identity.html',
							issuer_name=issuer_name,
							name=my_name,
							kbis=my_kbis,
							advanced=issuer_advanced,
							personal=issuer_personal,
							event=my_event_html,
							counter=my_counter,
							picturefile=my_picture)



# search
@app.route('/user/search/', methods=['GET', 'POST'])
def search() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('search.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	else :
		username_to_search = request.form['username_to_search']
		return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + username_to_search)
		
		
		
# issue certificate for companies
@app.route('/user/issue_certificate/', methods=['GET', 'POST'])
def issue_certificate():
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('issue_certificate.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		talent_username = request.form['talent_username']
		data  = username_to_data(talent_username, mode)
		if data is None :
			flash('Username not found', 'warning')
			return redirect(mode.server + 'user/?username=' + username)		
		# tester si on a le droit d emettre un cerrtificate
		if not has_key_purpose(data['workspace_contract'], session['address'],20002, mode) : 
			flash('Company is not authorized to issue', 'warning')
			return redirect(mode.server + 'user/?username=' + username)	
		session['talent_to_issue_certificate'] = talent_username
		if request.form['certificate_type'] == 'experience' :
			return render_template("issue_experience_certificate.html", picturefile=my_picture, event=my_event, counter=my_counter, username=username, name=talent_username)	
		else :
			flash('This certificate is not implemented yet !', 'warning')
			return redirect(mode.server + 'user/?username=' + username)	
@app.route('/user/issuer_experience_certificate/', methods=['POST'])
def issue_experience_certificate():
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	my_certificate = {
					"type" : "experience",	
					"title" : request.form['title'],
					"description" : request.form['description'],
					"start_date" : request.form['start_date'],
					"end_date" : request.form['end_date'],
					"skills" : request.form['skills'],  		
					"score_recommendation" : request.form['score_recommendation'],
					"score_delivery" : request.form['score_delivery'],
					"score_schedule" : request.form['score_schedule'],
					"score_communication" : request.form['score_communication'],
					"logo" : session['picture'],
					"signature" : "permet.png",
					"manager" : request.form['manager'],}
	certificate = Certificate()
	print(my_certificate)
	del session['talent_to_issue_certificate']
	flash('Certificate has been issued', 'success')
	return redirect(mode.server + 'user/?username=' + username)		
	









# personalsettings
@app.route('/user/update_personal_settings/', methods=['GET', 'POST'])
def update_personal_settings() :	
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		privacy=dict()
		for topicname in session['personal'].keys() :
			if session['personal'][topicname]['privacy']=='secret' :
				(p1,p2,p3) = ("", "", "selected") 
			if session['personal'][topicname]['privacy']=='private' :
				(p1,p2,p3) = ("", "selected", "") 
			if session['personal'][topicname]['privacy']=='public' :
				(p1,p2,p3) = ("selected", "", "") 
			if session['personal'][topicname]['privacy'] is None :
				(p1,p2,p3) = ("", "", "") 
			
			privacy[topicname] = """
					<optgroup """ +  """ label="Select">
					<option """+ p1 + """ value="public">Public</option>
					<option """ + p2 +""" value="private">Private</option>
					<option """ + p3 + """ value="secret">Secret</option>
					</opgroup>"""
					
		return render_template('update_personal_settings.html',
								picturefile=my_picture,
								event=my_event_html,
								counter=my_counter,
								username=username,
								firstname=session['personal']['firstname']['claim_value'],
								firstname_privacy=privacy['firstname'],
								lastname=session['personal']['lastname']['claim_value'],
								lastname_privacy=privacy['lastname'],
								contact_email=session['personal']['contact_email']['claim_value'],
								contact_email_privacy=privacy['contact_email'],
								contact_phone=session['personal']['contact_phone']['claim_value'],
								contact_phone_privacy=privacy['contact_phone'],
								birthdate=session['personal']['birthdate']['claim_value'],
								birthdate_privacy=privacy['birthdate'],
								postal_address=session['personal']['postal_address']['claim_value'],
								postal_address_privacy=privacy['postal_address']
								)
	if request.method == 'POST' :
		form_privacy = dict()
		form_value = dict()
		form_privacy['firstname'] = request.form['firstname_select']
		form_privacy['lastname'] = request.form['lastname_select']
		form_privacy['contact_phone'] = request.form['contact_phone_select']
		form_privacy['contact_email'] = request.form['contact_email_select']
		form_privacy['birthdate'] = request.form['birthdate_select']
		form_privacy['postal_address'] = request.form['postal_address_select']

		change = False	
		for topicname in session['personal'].keys() :
			form_value[topicname] = None if request.form[topicname] in ['None', '', ' '] else request.form[topicname]

			if 	form_value[topicname] != session['personal'][topicname]['claim_value'] or session['personal'][topicname]['privacy'] != form_privacy[topicname] :
				print(form_value[topicname])
				print(form_privacy[topicname])
				print('passage')
				(claim_id,a,b) = Claim().relay_add( session['workspace_contract'],topicname, form_value[topicname], form_privacy[topicname], mode)
				change = True
				session['personal'][topicname]['claim_value'] = form_value[topicname]
				session['personal'][topicname]['privacy'] = form_privacy[topicname]
				session['personal'][topicname]['claim_id'] = claim_id[2:]
			
		if change :
			flash('personal has been updated', 'success')
		return redirect(mode.server + 'user/?username=' + username)


# company settings
@app.route('/user/update_company_settings/', methods=['GET', 'POST'])
def update_company_settings() :	
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		privacy=dict()
		for topicname in session['personal'].keys() :
		#for topicname in ['name', 'contact_name', 'contact_email', 'contact_phone', 'website'] :
			if session['personal'][topicname]['privacy']=='secret' :
				(p1,p2,p3) = ("", "", "selected") 
			if session['personal'][topicname]['privacy']=='private' :
				(p1,p2,p3) = ("", "selected", "") 
			if session['personal'][topicname]['privacy']=='public' :
				(p1,p2,p3) = ("selected", "", "") 
			if session['personal'][topicname]['privacy'] is None :
				(p1,p2,p3) = ("", "", "") 
			
			privacy[topicname] = """
					<optgroup """ +  """ label="Select">
					<option """+ p1 + """ value="public">Public</option>
					<option """ + p2 +""" value="private">Private</option>
					<option """ + p3 + """ value="secret">Secret</option>
					</opgroup>"""
					
		return render_template('update_company_settings.html',
								picturefile=my_picture,
								event=my_event_html,
								counter=my_counter,
								username=username,
								name=session['personal']['name']['claim_value'],
								name_privacy=privacy['name'],
								contact_name=session['personal']['contact_name']['claim_value'],
								contact_name_privacy=privacy['contact_name'],
								contact_email=session['personal']['contact_email']['claim_value'],
								contact_email_privacy=privacy['contact_email'],
								contact_phone=session['personal']['contact_phone']['claim_value'],
								contact_phone_privacy=privacy['contact_phone'],
								website=session['personal']['website']['claim_value'],
								website_privacy=privacy['website'],
								)
	if request.method == 'POST' :
		form_privacy = dict()
		form_value = dict()
		form_privacy['name'] = request.form['name_select']
		form_privacy['contact_name'] = request.form['contact_name_select']
		form_privacy['contact_phone'] = request.form['contact_phone_select']
		form_privacy['contact_email'] = request.form['contact_email_select']
		form_privacy['website'] = request.form['website_select']

		change = False	
		for topicname in session['personal'].keys() :
		#for topicname in ['name', 'contact_name', 'contact_email', 'contact_phone', 'website'] :
			form_value[topicname] = None if request.form[topicname] in ['None', '', ' '] else request.form[topicname]

			if 	form_value[topicname] != session['personal'][topicname]['claim_value'] or session['personal'][topicname]['privacy'] != form_privacy[topicname] :
				(claim_id,a,b) = Claim().relay_add( session['workspace_contract'],topicname, form_value[topicname], form_privacy[topicname], mode)
				change = True
				session['personal'][topicname]['claim_value'] = form_value[topicname]
				session['personal'][topicname]['privacy'] = form_privacy[topicname]
				session['personal'][topicname]['claim_id'] = claim_id[2:]			
		if change :
			flash('Company Settings has been updated', 'success')
		return redirect(mode.server + 'user/?username=' + username)


# diigitalvault
@app.route('/user/store_file/', methods=['GET', 'POST'])
def store_file() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('store_file.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		if 'file' not in request.files :
			print('No file ')
			return
		myfile = request.files['file']
		filename = secure_filename(myfile.filename)
		myfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		privacy = request.form['privacy']
		user_file = File()
		(doc_id, ipfs_hash, transaction_hash) =user_file.add(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, filename, privacy, mode)
		new_file = {'id' : 'did:talao:'+ mode.BLOCKCHAIN+':'+ session['workspace_contract'][2:]+':document:'+ str(doc_id),
									'filename' : filename,
									'doc_id' : doc_id,
									'created' : str(datetime.utcnow()),
									'privacy' : privacy,
									'doctype' : "",
									'issuer' : mode.relay_address,
									'transaction_hash' : transaction_hash
									}	
		session['identity_file'].append(new_file)				
		flash(filename + ' uploaded', "success")
		return redirect(mode.server + 'user/?username=' + username)


# add experience
@app.route('/user/add_experience/', methods=['GET', 'POST'])
def add_experience() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('add_experience.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		my_experience = Experience()
		experience = dict()
		experience['company'] = {'contact_email' : request.form['contact_email'],
								'name' : request.form['company_name'],
								'contact_name' : request.form['contact_name'],
								'contact_phone' : request.form['contact_phone']}
		experience['title'] = request.form['title']
		experience['description'] = request.form['description']
		experience['start_date'] = request.form['from']
		experience['end_date'] = request.form['to']
		experience['skills'] = request.form['skills'].split(' ')  		
		privacy = request.form['privacy']
		(doc_id, ipfshash, transaction_hash) = my_experience.relay_add(session['workspace_contract'], experience, mode, privacy=privacy)		
		# add experience in session
		experience['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':document:'+str(doc_id)
		experience['doc_id'] = doc_id
		session['experience'].append(experience)			
		flash('New experience added', 'success')
		return redirect(mode.server + 'user/?username=' + username)
@app.route('/user/remove_experience/', methods=['GET', 'POST'])
def remove_experience() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['experience_to_remove'] = request.args['experience_id']
		session['experience_title'] = request.args['experience_title']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_experience.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, experience_title=session['experience_title'])
	elif request.method == 'POST' :	
		session['experience'] = [experience for experience in session['experience'] if experience['id'] != session['experience_to_remove']]
		Id = session['experience_to_remove'].split(':')[5]
		my_experience = Experience()
		my_experience.relay_delete(session['workspace_contract'], int(Id), mode)
		del session['experience_to_remove']
		del session['experience_title']
		flash('The experience has been removed', 'success')
		return redirect (mode.server +'user/?username=' + username)


# add education
@app.route('/user/add_education/', methods=['GET', 'POST'])
def add_education() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('add_education.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		my_education = Education()
		education  = dict()
		education['organization'] = {'contact_email' : request.form['contact_email'],
								'name' : request.form['company_name'],
								'contact_name' : request.form['contact_name'],
								'contact_phone' : request.form['contact_phone']}
		education['title'] = request.form['title']
		education['description'] = request.form['description']
		education['start_date'] = request.form['from']
		education['end_date'] = request.form['to']
		education['skills'] = request.form['skills'].split(' ')
		education['certificate_link'] = request.form['certificate_link']  		
		privacy = request.form['privacy']
		(doc_id, ipfshash, transaction_hash) = my_education.relay_add(session['workspace_contract'], education, mode, privacy=privacy)		
		# add experience in session
		education['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':document:'+str(doc_id)
		education['doc_id'] = doc_id
		session['experience'].append(education)			
		flash('New Education added', 'success')
		return redirect(mode.server + 'user/?username=' + username)
@app.route('/user/remove_education/', methods=['GET', 'POST'])
def remove_education() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['education_to_remove'] = request.args['education_id']
		session['education_title'] = request.args['education_title']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_education.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, experience_title=session['education_title'])
	elif request.method == 'POST' :	
		session['experience'] = [experience for experience in session['experience'] if experience['id'] != session['education_to_remove']]
		Id = session['education_to_remove'].split(':')[5]
		my_education = Education()
		my_education.relay_delete(session['workspace_contract'], int(Id), mode)
		del session['education_to_remove']
		del session['education_title']
		flash('The Education has been removed', 'success')
		return redirect (mode.server +'user/?username=' + username)

# invit friend
@app.route('/user/invit_friend/', methods=['GET', 'POST'])
def invit_friend() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('invit_friend.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	else :
		friend__email = request.form['friend_email']
		friend_memo = request.form['friend_memo']
		# something to do		
		flash('Invit sent to friend', 'success')
		return redirect(mode.server + 'user/?username=' + username)




# request partnership
@app.route('/user/request_partnership/', methods=['GET', 'POST'])
def resquest_partnership() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('request_partnership.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		partner_username = request.form['partner_username']
		if partner_username == 'new' :
			return render_template('request_partnership_new.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
		if is_username_in_list(session['partner'], partner_username) :
			flash(partner_username + ' is already a partner')
			return redirect(mode.server + 'user/?username=' + username)
		partner_workspace_contract = username_to_data(partner_username, mode)['workspace_contract']
		partner_address = username_to_data(partner_username, mode)['address']
		partner_publickey = username_to_data(partner_username, mode)['publicKey']
		
		filename = "./RSA_key/" + mode.BLOCKCHAIN + '/' + session['address'] + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
		try :
			fp = open(filename,"r")
			rsa_key = fp.read()	
			fp.close()   
		except IOError :
			print('RSA key not found')	
		res = partnershiprequest(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, partner_workspace_contract, rsa_key, mode, synchronous= True)
		if res  :
			session['partner'].append({"address": partner_address,
								"publickey": partner_publickey,
								 "workspace_contract" : partner_workspace_contract,
								  'username' : partner_username,
								  'authorized' : 'Authorized',
								  })
			flash('We have send a request to ' + partner_username, 'success')
		else :
			flash('Request to ' + partner_username + ' failed', 'danger')
		return redirect(mode.server + 'user/?username=' + username)
# remove partnership to be completed
@app.route('/user/remove_partner/', methods=['GET', 'POST'])
def remove_partner() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['partner_username_to_remove'] = request.args['partner_username']
		session['partner_workspace_contract_to_remove'] = request.args['partner_workspace_contract']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_partner.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, partner_name=session['partner_username_to_remove'])
	if request.method == 'POST' :
		remove_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_remove'], mode, synchronous= True)
		session['partner'] = [ partner for partner in session['partner'] if partner['workspace_contract'] != session['partner_workspace_contract_to_remove']]
		flash('The partnership with '+session['partner_username_to_remove']+ '  has been removed', 'success')
		print('partner w =', session['partner_workspace_contract_to_remove'])
		del session['partner_username_to_remove']
		del session['partner_workspace_contract_to_remove']
		return redirect (mode.server +'user/?username=' + username)



# request certificatet to be completed with email
@app.route('/user/request_certificate/', methods=['GET', 'POST'])
def request_certificate() :	
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('request_certificate.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	else :
		issuer_username = request.form['issuer_username']
		certificate_type = request.form['certificate_type']
		if issuer_username == 'new' :
			return render_template('request_certificate_new_issuer.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
		else :
			# something to do
			return redirect(mode.server + 'user/?username=' + username)
@app.route('/user/request_certificate_new_issuer/', methods=['POST'])
def request_certificate_new_issuer() :
	username = check_login(session.get('username'))	
	choice = request.form['choice']
	if choice == 'cancel' :
		return redirect(mode.server + 'user/?username=' + username)
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	project_description = request.form['project_description']
	issuer_type = request.form['type']
	issuer_memo = request.form['issuer_memo']
	issuer_email = request.form['issuer_email']
	# to do send  email
	flash('Certificate Request sent to '+issuer_email, 'success')
	return redirect(mode.server + 'user/?username=' + username)



# add Alias/Username
@app.route('/user/add_access/', methods=['GET', 'POST'])
def add_access() :	
	username = check_login(session.get('username'))	
	if request.method == 'GET' :		
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('add_access.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		if username_to_data(request.form['access_username'],mode) is not None :
			flash('Username already used' , 'warning')
			return redirect (mode.server +'user/?username=' + username)
		addName(request.form['access_username'], session['address'], session['workspace_contract'], request.form['access_email'], mode)
		flash('Username added for '+ request.form['access_username'] , 'success')
		return redirect (mode.server +'user/?username=' + username)
# remove Username
@app.route('/user/remove_access/', methods=['GET'])
def remove_access() :	
	username = check_login(session.get('username'))	
	username_to_remove = request.args['username_to_remove']
	deleteName(username_to_remove, mode)
	flash('Username removed for '+username_to_remove, 'success')
	return redirect (mode.server +'user/?username=' + username)




# request proof of Identity
@app.route('/user/request_proof_of_identity/', methods=['GET', 'POST'])
def request_proof_of_identity() :	
	username = check_login(session.get('username'))	
	if request.method == 'GET' :				
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		session['request_code'] = str(random.randint(100000, 999999))
		return render_template('request_proof_of_identity.html', picturefile=my_picture, event=my_event_html, code= session['request_code'], counter=my_counter, username=username)
	elif request.method == 'POST' :
		message = 'username = '+ session['username'] + ' secret code = ' + session['request_code'] + 'workspce_contract = ' + session['workspace_contract']
		subject = 'Request for Proof of Identity'
		Talao_message.messageAdmin (subject, message, mode)
		flash(' Your request has been registered, we are waiting for your email', 'success')
		return redirect (mode.server +'user/?username=' + username)	


# add Issuer, they have an ERC725 key with purpose 20002 (or 1) to issue Document (Experience, Certificate)
@app.route('/user/add_issuer/', methods=['GET', 'POST'])
def add_issuer() :	
	username = check_login(session.get('username'))	
	if request.method == 'GET' :				
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('add_issuer.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	elif request.method == 'POST' :
		issuer_username = request.form['issuer_username']
		if is_username_in_list(session['issuer'], issuer_username) :
			flash(issuer_username + ' is already authorized', 'warning')
			return redirect (mode.server +'user/?username=' + username)	
		issuer_address = username_to_data(issuer_username,mode)['address']
		addkey(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 20002, mode, synchronous=True) 
		# update issuer list in session
		issuer_key = mode.w3.soliditySha3(['address'], [issuer_address])
		contract = mode.w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
		issuer_workspace_contract = ownersToContracts(issuer_address, mode)
		session['issuer'].append(username_to_data(issuer_username, mode))	
		flash(issuer_username + ' has been added as Issuer', 'success')
		return redirect (mode.server +'user/?username=' + username)	
# remove issuer
@app.route('/user/remove_issuer/', methods=['GET', 'POST'])
def remove_issuer() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['issuer_username_to_remove'] = request.args['issuer_username']
		session['issuer_address_to_remove'] = request.args['issuer_address']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_issuer.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, issuer_name=session['issuer_username_to_remove'])
	elif request.method == 'POST' :
		address_partner = session['issuer_address_to_remove']
		delete_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['issuer_address_to_remove'], 20002, mode) 
		session['issuer'] = [ issuer for issuer in session['issuer'] if issuer['address'] != session['issuer_address_to_remove']]
		flash('The Issuer '+session['issuer_username_to_remove']+ '  has been removed', 'success')
		del session['issuer_username_to_remove']
		del session['issuer_address_to_remove']
		return redirect (mode.server +'user/?username=' + username)






# add  White Issuer or WhiteList They all have an ERC725 key with purpose 5
@app.route('/user/add_white_issuer/', methods=['GET', 'POST'])
def add_white_issuer() :	
	username = check_login(session.get('username'))	
	if request.method == 'GET' :				
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('add_white_issuer.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	elif request.method == 'POST' :
		issuer_username = request.form['white_issuer_username']
		if is_username_in_list(session['whitelist'], issuer_username) :
				flash(issuer_username + ' is already in White List', 'warning')
				return redirect(mode.server + 'user/?username=' + username)
		issuer_address = username_to_data(issuer_username,mode)['address']
		addkey(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 5, mode, synchronous=True) 
		# update issuer list in session
		issuer_key = mode.w3.soliditySha3(['address'], [issuer_address])
		contract = mode.w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
		issuer_workspace_contract = ownersToContracts(issuer_address, mode)
		session['whitelist'].append(username_to_data(issuer_username, mode))	
		flash(issuer_username + ' has been added as Issuer in your White List', 'success')
		return redirect (mode.server +'user/?username=' + username)	
# remove white issuer
@app.route('/user/remove_white_issuer/', methods=['GET', 'POST'])
def remove_white_issuer() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['issuer_username_to_remove'] = request.args['issuer_username']
		session['issuer_address_to_remove'] = request.args['issuer_address']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_white_issuer.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, issuer_name=session['issuer_username_to_remove'])
	elif request.method == 'POST' :
		address_partner = session['issuer_address_to_remove']
		delete_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['issuer_address_to_remove'], 5, mode) 
		session['whitelist'] = [ issuer for issuer in session['whitelist'] if issuer['address'] != session['issuer_address_to_remove']]
		flash('The Issuer '+session['issuer_username_to_remove']+ '  has been removed from your White list', 'success')
		del session['issuer_username_to_remove']
		del session['issuer_address_to_remove']
		return redirect (mode.server +'user/?username=' + username)


""""
@app.route('/user/description/', methods=['POST'])
def description() :
	username = check_login(session.get('username'))	
	newdescription=request.form.get('description')
	if session['description'] != newdescription :	
		user = Identity(session['workspace_contract'], mode)
		user.setDescription(newdescription)
		session['description'] = newdescription
	return redirect(mode.server + 'user/?username=' + session['username'])
"""

@app.route('/user/languages/', methods=['GET'])
def languages() :
	print('entree dans languages ')
	username = session['username']
	lang1 = request.args.get('lang1')
	lang2 = request.args.get('lang2')
	lang3 = request.args.get('lang3')
	fluency1 = request.args.get('radio1')
	fluency2 = request.args.get('radio2')
	fluency3 = request.args.get('radio3')
	workspace_contract = address(username, mode.register)	
	user = Identity(workspace_contract, mode)
	language = [{"language": lang1,"fluency": fluency1}, {"language": lang2,"fluency": fluency2}, {"language": lang3,"fluency": fluency3}]
	#language= [{"language": 'EN',"fluency": '1'}]
	user.setLanguage(language)
	return redirect(mode.server + 'user/?username=' + session['username'])


# photos upload for certificates
@app.route('/uploads/<filename>')
def send_file(filename):
	UPLOAD_FOLDER = 'photos'
	return send_from_directory(UPLOAD_FOLDER, filename)
	
# fonts upload
@app.route('/fonts/<filename>')
def send_fonts(filename):
	UPLOAD_FOLDER='templates/assets/fonts'
	return send_from_directory(UPLOAD_FOLDER, filename)		


##################################################
# Remove Identity
##################################################
@app.route('/talao/api/did/remove/<did>', methods=['GET'])
def identityRemove_1(did) :
	session['did'] = did
	session['endtime'] = datetime.now() + timedelta(minutes=3)
	print(session['endtime'])
	return render_template('remove1.html', message="", myusername="")
	
@app.route('/talao/api/did/remove/', methods=['POST'])
def identityRemove_2() :
	if datetime.now() > session['endtime'] :
		mymessage="time out"
		return render_template('remove3.html', message=mymessage)	
	
	username= request.form.get('username')
	if username_to_data(username, mode)['workspace_contract']is None :
		mymessage="Your username is not registered"
		return render_template('remove1.html', message=mymessage)
	
	did=session['did']	
	workspace_contract_did='0x'+did.split(':')[3]
	workspace_contract = username_to_data(username, mode)['workspace_contract']
	if workspace_contract_did != workspace_contract :
		mymessage = 'Your are not the owner of this Identity, you cannot delete it.'
		return render_template("remove3.html", message=mymessage)
	
	email = uername_to_data(username, mode)['email']
	if email == False :
		mymessage="Your email for authentification is not registered"
		return render_template('remove3.html', message=mymessage)			
	session['username'] = username
	# secret code is sent by email
	code = str(random.randint(100000, 999999))
	print('code secret = ', code)
	session['code'] = code
	session['try_number'] = 0
	Talao_message.messageAuth(email, code)
	mymessage="Code has been sent"
	return render_template("remove2.html", message=mymessage)


@app.route('/talao/api/did/remove/code/', methods=['POST'])
def identityRemove_3() :
	if 'username' not in session :
		mymessage="session is over"
		return render_template('remove3.html', message= mymessage)	
	
	if datetime.now() > session['endtime'] :
		mymessage="time out"
		return render_template('remove3.html', message= mymessage)	
	
	session['try_number'] += 1
	if session['try_number'] > 3 :
		mymessage = "Too many trials (3 max)"
		return render_template("remove3.html", message = mymessage)
	
	mycode = request.form['mycode']	
	if mycode == session['code'] :
		did=session['did']
		workspace_contract='0x'+did.split(':')[3]
		private_key=getPrivatekey(workspace_contract,mode)
		if not private_key :
			mymessage = "Talao does not have the private key of this Identity"
			return render_template("remove3.html", message=mymessage)	
		
		# on detruit le workspace et on efface la cle du registre
		destroyWorkspace(workspace_contract, private_key, mode)
		username=session['username']
		deleteName(username,mode)
		mymessage = 'Identity has been removed and data deleted' 
		return render_template("remove3.html", message=mymessage)

	else : # code incorrect
		mymessage = 'This code is incorrect'	
		return render_template("remove2.html", message=mymessage)

# sortie et retour vers resolver
@app.route('/talao/api/did/remove/code/', methods=['GET'])
def identityRemove_4() :
	did=session['did']
	session.clear()
	return redirect(mode.server+'resume/')
	






#######################################################
#                        MAIN, server launch
#######################################################
# setup du registre nameservice

print('initialisation du serveur')


if __name__ == '__main__':
	app.run(host = mode.flaskserver, port= mode.port, debug = mode.debug)
