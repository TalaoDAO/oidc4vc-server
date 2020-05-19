"""
pour l authentication cf https://realpython.com/token-based-authentication-with-flask/

pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization

interace wsgi https://www.bortzmeyer.org/wsgi.html

import ipfshttpclient

request : http://blog.luisrei.com/articles/flaskrest.html
"""
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
from protocol import username_and_email_list, deleteName, username_to_data, getUsername
from protocol import createdocument, savepictureProfile
import environment
import hcode
# Centralized  route
import web_create_identity
import web_certificate
import web_guest

# environment setup
mode=environment.currentMode()
w3=mode.w3

UPLOAD_FOLDER = './uploads'

# Flask and Session setup	
app = FlaskAPI(__name__)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'redis'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=100)
app.config['SESSION_FILE_THRESHOLD'] = 100  
app.config['SECRET_KEY'] = "OCML3BRawWEUeaxcuKHLpw"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Session(app)

fa = FontAwesome(app)


# Centralized @route pour web_create_identity
"""
lacces web permet a un user de creer une identité et de recuperer par email les informations de la cle privée et cle RSA
Par la suite le user peut creer par lui meme une addresse et ethereum et demander le transfert de l identité. 
Si Talao conserve une copie de la cle RSA et une cle de type 1 le user peut continuer a utiliser l acces web.

"""
app.add_url_rule('/talao/register/',  view_func=web_create_identity.authentification)
app.add_url_rule('/talao/register/', view_func=web_create_identity.POST_authentification_1, methods = ['POST'])
app.add_url_rule('/talao/register/code/', view_func=web_create_identity.POST_authentification_2, methods = ['POST'])
app.add_url_rule('/talao/register/code/', view_func=web_create_identity.POST_authentification_3, methods = ['GET'])


"""
Permet de creer un certificat et de l afficher
"""
# Centralized @route pour certificate
app.add_url_rule('/certificate/<data>',  view_func=web_certificate.show_certificate)
app.add_url_rule('/certificate/experience/<did>',  view_func=web_certificate.input_certificate, methods = ['GET'])
app.add_url_rule('/certificate/experience/',  view_func=web_certificate.input_certificate_1, methods = ['POST'])
app.add_url_rule('/certificate/verify/<dataId>',  view_func=web_certificate.certificate_verify, methods = ['GET'])


"""
Gestion des access anonyme 
"""
# centralized route for Guest
app.add_url_rule('/guest/',  view_func=web_guest.guest , methods = ['GET'])
app.add_url_rule('/guest_data/<dataId>',  view_func=web_guest.guest_data, methods = ['GET'])
app.add_url_rule('/talent-connect/',  view_func=web_guest.anonymous, methods = ['GET', 'POST'])
app.add_url_rule('/guest/issuer_explore/',  view_func=web_guest.guest_issuer_explore, methods = ['GET'])



def check_login(username) :
	if username is None or session.get('username_logged') is None or username != session.get('username_logged') :
		print('session aborted = ', session)
		session.clear()
		abort(403, description="Authentification required")
	else :
		return username

""" gestion du menu de gestion des Events  """
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
				return redirect(mode.server + 'talao/register/')
			elif start == 'advanced' :
				return redirect(mode.server + 'starter/')
			else :
				pass

@app.route('/login/', methods = ['GET', 'POST'])
#@app.route('/user/login/', methods = ['GET'])
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
def data2(dataId) :
	username = check_login(session.get('username'))
	mypicture = 'anonymous1.jpeg' if session.get('picture') is None else session['picture']		
	my_event_html, my_counter =  event_display(session['events'])
				
	mydata = Data(dataId,mode)		
	mytopic = mydata.topic.capitalize()
	myvisibility = mydata.encrypted.capitalize()
	issuer_is_white = False
	for issuer in session['whitelist'] :
		if issuer['username'] == mydata.issuer_username :
			issuer_is_white = True 		
	if mydata.issuer_username == session['username']:					
		myissuer = """
				<span>
				<b>Name</b> : """ + mydata.issuer_name + """<br>
				<b>Username</b> : """ + mydata.issuer_username +"""<br>
				</span>"""
	elif issuer_is_white :					
		myissuer = """
				<span>
				<b>Name</b> : """ + mydata.issuer_name + """<br>
				<b>Username</b> : """ + mydata.issuer_username +"""<br>
				<b>Type</b> : """ + mydata.issuer_type + """<br>
				<a class="text-secondary" href=/user/issuer_explore/?issuer_username="""+mydata.issuer_username+""" >
					<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
				</a><br>
				  <a class="text-info">This issuer is in my White List</a>			
				</span>"""		
	else :	
		myissuer = """
				<span>
				<b>Name</b> : """ + mydata.issuer_name + """<br>
				<b>Username</b> : """ + mydata.issuer_username +"""<br>
				<b>Type</b> : """ + mydata.issuer_type + """<br>				
					<a class="text-secondary" href=/user/issuer_explore/?issuer_username="""+mydata.issuer_username+""" >
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a><br>
					<a class="text-warning">This issuer is not in my Whitelist</a>
				</span>"""
		
	myprivacy = """ <b>Privacy</b> : """ + mydata.encrypted + """<br>"""
	
	path = """https://rinkeby.etherscan.io/tx/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/tx/"""

	myadvanced = """
		<!--		<b>Data Id</b> : """ + mydata.id + """<br>  -->
				<b>Created</b> : """ + mydata.created + """<br>	
				<b>Expires</b> : """ + mydata.expires + """<br>
				<b>Transaction Hash</b> : <a class = "card-link" href = """ + path + mydata.transaction_hash + """>"""+ mydata.transaction_hash + """</a><br>					
				<b>Data storage</b> : <a class="card-link" href=""" + mydata.data_location + """>""" + mydata.data_location + """</a>"""
	
	
	""" topic = Experience """
	if mydata.topic.capitalize() == "Experience"  :
		mytitle = mydata.value['position']
		mysummary = mydata.value['summary']		
		myvalue = """ 
				<b>Title</b> : """+mydata.value['position']+"""<br>
				<b>Company</b> : """+mydata.value['company']['name']+"""<br>
				<b>Manager</b> : """+mydata.value['company']['manager']+"""<br>
				<b>Manager Email</b> : """+mydata.value['company']['manager_email']+"""<br>
				<b>Start Date</b> : """+mydata.value['startDate']+"""<br>		
				<b>End Date</b> : """+mydata.value['endDate']+"""<br>
				<b>Skills</b> : """+ " ".join(mydata.value['skills'])
				
	elif mydata.topic.capitalize() == "Education" :
		return 'work in progress'
	
	elif mydata.topic.capitalize() == "Employability" :
		return 'work in progress'		
	
	elif mydata.topic.capitalize() == "Certificate" :
		mytitle = mydata.value['position']
		mysummary = mydata.value['summary']		
		print(mydata.value)
		myvalue = """ 
				<b>Title</b> : """ + mydata.value['position'] + """<br>
				<b>Company</b> : """ + mydata.value['company']['name'] + """<br>
				<b>Manager</b> : """+ mydata.value['company'].get('manager', 'Unknown') + """<br>
				<b>Manager Email</b> : """+ mydata.value['company'].get('manager_email', 'Unknown') + """<br>
				<b>Start Date</b> : """+ mydata.value['startDate'] + """<br>		
				<b>End Date</b> : """+ mydata.value['endDate'] + """<br>
				<b>Skills</b> : """+ mydata.value['skills'] 
	else :
		mytitle = 'Profil'
		mysummary = ''		
		myvalue = """<b>"""+mydata.topic.capitalize()+"""</b> : """+mydata.value

			
	mydelete_link = "/talao/api/data/delete/"
	
	myusername = mydata.issuer_username
		
	return render_template('data.html',
							topic = mytopic,
							visibility = myvisibility,
							issuer = myissuer,
							title = mytitle,
							summary = mysummary,
							value = myvalue,
							privacy = myprivacy,
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
		session['controller'] = user.managementkeys
		session['issuer'] = user.claimkeys
		session['whitelist'] = user.whitekeys
		session['partner'] = user.partners
		session['did'] = user.did
		session['eth'] = user.eth
		session['token'] = user.token
		session['rsa_key'] = user.rsa_key
		session['web_relay_authorized'] = user.web_relay_authorized
		session['personal'] = user.personal
		session['name'] = user.name
		
		if user.type == 'person' :
			session['experience'] = user.experience
			session['certificate'] = user.certificate
			session['contact'] = user.contact
			session['language'] = user.language
			session['education'] = user.education	
			session['picture'] = "anonymous1.png" if user.picture is None else user.picture
			
			#this_name = session['personal']['firstname']['data']+ ' '+ session['personal']['lastname']['data']
			#(radio, mylang1, mylang2, mylang3)= session['language']
		
		if user.type == 'company' :
			pass
	
	my_type = session['type']
	my_eth = session['eth']
	my_token = session['token']
	my_event = session['events']
	my_username = session['username'] 
	my_event_html, my_counter =  event_display(session['events'])
	controller_list = session['controller']
	issuer_list = session['issuer']
	white_list = session['whitelist']
	partners_list = session['partner']		
	web_relay_authorized = 'Yes' if session['web_relay_authorized'] else 'No'
	rsa_key = 'No' if session['rsa_key'] is None else 'Yes'
	my_name = session['name']
	
	if session['type'] == 'person' :	
		my_picture = session['picture']
		experience_list = session['experience']
		certificate_list = session['certificate']
		education_list = session['education']
	if session['type'] == 'company' :
		pass
	
	# advanced
	my_controller = ""
	my_controller_start =  """ <li> <a class="card-link" href="">Add Key</a></li>"""
	for controller in controller_list :
		controller_html = """
				<li>""" + controller['username'] + """
					<a class="text-secondary" href="/user/remove_controller/?controller_username="""+controller['username']+"""&amp;controller_address="""+controller['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="#explore">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</li>"""	
		my_controller = my_controller + controller_html 
	my_controller = my_controller_start + my_controller
	path = """https://rinkeby.etherscan.io/address/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/address/"""	
	my_advanced = """
					<b>Ethereum Chain</b> : """ + mode.BLOCKCHAIN + """<br>	
					<b>Authentification Email</b> : """ + getEmail(session['workspace_contract'], mode) + """<br>
					<b>Worskpace Contract</b> : <a class = "card-link" href = """ + path + session['workspace_contract'] + """>"""+ session['workspace_contract'] + """</a><br>					
					<b>Owner Wallet Address</b> : <a class = "card-link" href = """ + path + session['address'] + """>"""+ session['address'] + """</a><br>					
					<b>Decentralized IDentifier</b> : """ + session['did'] + """<br>	
					<b>RSA Key</b> : """ + rsa_key + """<br>
					<div><b>Management Keys :</b>""" + my_controller+"""</div>"""
	
	
	# access/username
	my_access_start = """<a href="/user/add_access/">Add a Username</a><hr> """
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
	
	# partner
	if web_relay_authorized == 'Yes' and rsa_key == 'Yes'  :
		my_partner_start = """<a href="">Request a Partnership</a><hr> """
	else :
		my_partner_start = ""				
	my_partner = ""
	for partner in partners_list :
		partner_html = """
				<span>""" + partner['username'] + """
					<a class="text-secondary" href="#remove">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + partner['username'] + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</apn>"""	
		my_partner = my_partner + partner_html + """<br>"""
	my_partner = my_partner_start + my_partner 	
	
	
	# issuer	
	if web_relay_authorized == 'Yes':
		my_issuer_start = """<a href="/user/add_issuer/">Authorize an Issuer</a><hr> """
	else :
		my_issuer_start = ""	
	my_claim_issuer = ""		
	for issuer in issuer_list :
		issuer_html = """
				<span>""" + issuer['username'] + """
					<a class="text-secondary" href="/user/remove_issuer/?issuer_username="""+issuer['username']+"""&amp;issuer_address="""+issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer['username'] + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span>"""
		my_claim_issuer = my_claim_issuer + issuer_html + """<br>"""
	my_claim_issuer = my_issuer_start + my_claim_issuer
	
	
	# whitelist	
	if web_relay_authorized == 'Yes':
		my_white_start = """<a href="/user/add_white_issuer/">Add a new Issuer</a><hr> """
	else :
		my_white_start = ""	
	my_white_issuer = ""		
	for issuer in white_list :
		issuer_html = """
				<span>""" + issuer['username'] + """
					<a class="text-secondary" href="/user/remove_white_issuer/?issuer_username="""+issuer['username']+"""&amp;issuer_address="""+issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer['username'] + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span>"""
		my_white_issuer = my_white_issuer + issuer_html + """<br>"""
	my_white_issuer = my_white_start + my_white_issuer
	
	
	
	
	
	
	# account
	my_account = """
					<b>Balance ETH</b> : """ + str(my_eth)+"""<br>				
					<b>Balance TALAO</b> : """ + str(my_token)	
####################################################################################################
	# specific to person
####################################################################################################	
	if my_type == 'person' :
	
	# experience
		my_experience = ''
		for experience in experience_list :
			exp_html = """<hr> 
				<b>Company</b> : """+experience['organization']['name']+"""<br>			
				<b>Title</b> : """+experience['title']+"""<br>
				<b>Description</b> : """+experience['description'][:100]+"""...<br>
				<p>
					<a class="text-secondary" href="/user/remove_experience/?experience_id=""" + experience['id'] + """&experience_title="""+ experience['title'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					
					<a class="text-secondary" href=/data/"""+experience['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
			my_experience = my_experience + exp_html
	
		# personal
		my_personal_start = """<a href="/user/picture/">Change Picture</a>"""
		my_personal = """ 
				<span><b>Firstname</b> : """+session['personal']['firstname']['data']+"""				
					
					
					<a class="text-secondary" href=/data/"""+session['personal']['firstname']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Lastname</b> : """+session['personal']['lastname']['data']+"""
					
					<a class="text-secondary" href=/data/"""+session['personal']['lastname']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				"""
		my_personal = my_personal + my_personal_start
		
		# contact
		if session['contact'] is None :
			my_contact =  """ <a class="card-link" href="">Add Contact</a>"""
		else :
			my_contact = """<span>
					<b>Contact Email</b> : """ + session['contact']['data']['email'] + """<br>						
					<b>Contact Phone</b> : """ + session['contact']['data']['phone'] + """<br>				
					<b>Contact Twitter</b> : """ + session['contact']['data']['twitter'] + """<br>				
						
						<a class="text-secondary" href=/data/"""+session['contact']['id'] + """>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
						</a>
					</span>"""	
	
		# education
		my_education = ""
		for education in education_list :
			edu_html = """<hr> 
				<b>Organization</b> : """+education['data']['organization']+"""<br>			
				<b>Title</b> : """+education['data']['studyType']+"""<br>
				<b>Start Date</b> : """+education['data']['startDate']+"""<br>
				<b>End Date</b> : """+education['data']['endDate']+"""<br>				
				<p>
					
					<a class="text-secondary" href=/data/"""+education['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
			my_education = my_education + edu_html
							
		# languages
		my_languages = ""
	
		# skills
		my_skills = ""
		
		# certificates
		my_certificates = ""
		for certificate in certificate_list :
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
							name=my_name,
							personal=my_personal,
							contact=my_contact,
							experience=my_experience,
							education=my_education,
							languages=my_languages,
							skills=my_skills,
							certificates=my_certificates,
							access=my_access,
							partner=my_partner,
							claimissuer=my_claim_issuer,
							whitelist=my_white_issuer,
							advanced=my_advanced,
							event=my_event_html,
							counter=my_counter,
							account=my_account,
							picturefile=my_picture,
							username=my_username)	

####################################################################################################
	# specific to company
####################################################################################################	

	else :
		# personal
		my_personal = """ 
				<span><b>Name</b> : """+session['personal']['name']['data'] + """				
					
					<a class="text-secondary" href=/data/"""+session['personal']['name']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Website</b> : """+session['personal']['website']['data']+"""
					
					<a class="text-secondary" href=/data/"""+session['personal']['website']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Contact</b> : """+session['personal']['contact']['data']+"""
					
					<a class="text-secondary" href=/data/"""+session['personal']['contact']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Email</b> : """+session['personal']['email']['data']+"""
					
					<a class="text-secondary" href=/data/"""+session['personal']['email']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>"""
		
		return render_template('company_identity.html',
							access=my_access,
							name = my_name,
							personal=my_personal,
							partner=my_partner,
							claimissuer=my_claim_issuer,
							whitelist=my_white_issuer,
							advanced=my_advanced,
							event=my_event_html,
							account=my_account,
							counter=my_counter,
							username=my_username)	
		
		
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
		if 'file' not in request.files :
			print('No file ')
		myfile = request.files['file']
		filename = secure_filename(myfile.filename)
		myfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		picturefile = UPLOAD_FOLDER + '/' + filename
		savepictureProfile(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, picturefile, mode, synchronous = False)	
		print('picture file = ',picturefile)
		session['picture'] = filename			
		return redirect(mode.server + 'user/?username=' + username)

# a faire
@app.route('/user/contact_settings/', methods=['POST'])
def contact_settings() :	
	return redirect(mode.server + 'user/?username=' + user.username)



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
	my_picture = session['picture'] if session['type'] == 'person' else ""  
	
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
					
					<a class="text-secondary" href=/data/""" + issuer.personal['firstname']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Lastname</b> : """+ issuer.personal['lastname']['data']+"""
					
					<a class="text-secondary" href=/data/""" + issuer.personal['lastname']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Picture</b>  	
					
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
		
		# personal
		issuer_personal = """ 
				<span><b>Name</b> : """ + issuer.personal['name']['data'] + """				
					
					<a class="text-secondary" href=/data/"""+ issuer.personal['name']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Website</b> : """+ issuer.personal['website']['data']+"""
					
					<a class="text-secondary" href=/data/"""+ issuer.personal['website']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Contact</b> : """+ issuer.personal['contact']['data']+"""
					
					<a class="text-secondary" href=/data/"""+ issuer.personal['contact']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>
				
				<span><b>Email</b> : """+ issuer.personal['email']['data']+"""
					
					<a class="text-secondary" href=/data/""" + issuer.personal['email']['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>"""
		
		return render_template('company_issuer_identity.html',
							issuer_name=issuer_name,
							name=my_name,
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
		experience = {"documentType":55000,
						"version":2,
						"recipient": {"givenName": "",
									"familyName": "",
									"title": "",
									"email": "",
									"ethereum_account": session['address'],
									"ethereum_contract": session['workspace_contract']
									},
						"issuer": {"organization": {"email": request.form['contact_email'],
													'name' : request.form['company_name'],
													"url":"",
													"image":"",
													"ethereum_account":"",
													"ethereum_contract":""},
									"responsible":{"name": request.form['contact_name'],
													"title":"",
													"image":""},
									"partner":{"name":"",
												"text":""}
									},												
						"certificate":{"title": request.form['title'],
										"description": request.form['description'],
										"from": request.form['from'],
										"to": request.form['to'],
										"skills": request.form['skills'].split(' '),
										"ratings":[]
										}
					}
		encrypted = False if request.form['privacy'] == 'public' else True							
		doc_id = createdocument(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, 55000, experience, 0, encrypted, mode, synchronous=True) 
		# add experience in session
		new_experience = {'id' : 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':document:'+str(doc_id),
						'title' : experience['certificate']['title'],
						'description' : experience['certificate']['description'],
						'from' : experience['certificate']['from'],
						'to' : experience['certificate']['to'],
						'organization' : {"name" : experience['issuer']['organization']['name'], 
										"contact_name" : experience['issuer']['responsible']["name"],
										"contact_email" : experience["issuer"]["organization"]["email"]
										},
						"certification_link" : "",
						'skills' : experience['certificate']['skills']
						}	
		
		session['experience'].append(new_experience)			
		flash('New experience added')
		return redirect(mode.server + 'user/?username=' + username)
@app.route('/user/remove_experience/', methods=['GET', 'POST'])
def remove_experience() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['experience_to_remove'] = request.args['experience_id']
		session['experience_title'] = request.args['experience_title']
		print(session['experience_to_remove'])
		print(session['experience_title'])
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_experience.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, experience_title=session['experience_title'])
	elif request.method == 'POST' :	
		session['experience'] = [experience for experience in session['experience'] if experience['id'] != session['experience_to_remove']]
		Id = session['experience_to_remove'].split(':')[5]
		if session['experience_to_remove'].split(':')[4] == 'document' :
			deleteDocument(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, Id, mode)
		else :
			deleteClaim(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, Id, mode)
		del session['experience_to_remove']
		del session['experience_title']
		flash('The experience has been removed')
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
		flash('Invit sent to friend')
		return redirect(mode.server + 'user/?username=' + username)




# request partnership to be completed
@app.route('/user/request_partnership/', methods=['GET', 'POST'])
def resquest_partnership() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('request_partnership.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	else :
		partner_username = request.form['issuer_username']
		if partner_username == 'new' :
			return render_template('request_partnership_new.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
		else :
			return redirect(mode.server + 'user/?username=' + username)




# request certificatet to be completed with email
@app.route('/user/request_certificate/', methods=['GET', 'POST'])
def request_certificate() :	
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('request_certificate.html', picturefile=my_picture, event=my_event_html, counter=my_counter)
	else :
		issuer_username = request.form['issuer_username']
		certificate_type = request.form['certificate_type']
		if issuer_username == 'new' :
			return render_template('request_certificate_new_issuer.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
		else :
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
	flash('Certificate Request sent to '+issuer_email)
	return redirect(mode.server + 'user/?username=' + username)



# add Username
@app.route('/user/add_access/', methods=['GET', 'POST'])
def add_access() :	
	username = check_login(session.get('username'))	
	if request.method == 'GET' :		
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('add_access.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	else :
		workspace_contract = session['workspace_contract']
		address = session['address']
		access_username = request.form['access_username']
		access_email = request.form['access_email']
		addName(access_username, address, mode, workspace_contract=workspace_contract, email=access_email)
		flash('Username added for '+access_username)
		return redirect (mode.server +'user/?username=' + username)
# remove Username
@app.route('/user/remove_access/', methods=['GET'])
def remove_access() :	
	username = check_login(session.get('username'))	
	username_to_remove = request.args['username_to_remove']
	deleteName(username_to_remove, mode)
	flash('Username removed for '+username_to_remove)
	return redirect (mode.server +'user/?username=' + username)




# add issuer
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
		issuer_address = username_to_data(issuer_username,mode)['address']
		addkey(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 3, mode, synchronous=True) 
		# update issuer list in session
		issuer_key = mode.w3.soliditySha3(['address'], [issuer_address])
		contract = mode.w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
		issuer_workspace_contract = ownersToContracts(issuer_address, mode)
		session['issuer'].append({"address": issuer_address, "publickey": issuer_key.hex()[2:], "workspace_contract" : issuer_workspace_contract , 'username' : issuer_username } )	
		flash(issuer_username + ' has been added as Issuer')
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
		delete_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.realy_private_key_from, session['issuer_address_to_remove'], 3, mode) 
		session['issuer'] = [ issuer for issuer in session['issuer'] if issuer['address'] != session['issuer_address_to_remove']]
		flash('The Issuer '+session['issuer_username_to_remove']+ '  has been removed')
		del session['issuer_username_to_remove']
		del session['issuer_address_to_remove']
		return redirect (mode.server +'user/?username=' + username)






# add white issuer
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
		issuer_address = username_to_data(issuer_username,mode)['address']
		addkey(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 5, mode, synchronous=True) 
		# update issuer list in session
		issuer_key = mode.w3.soliditySha3(['address'], [issuer_address])
		contract = mode.w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
		issuer_workspace_contract = ownersToContracts(issuer_address, mode)
		session['whitelist'].append({"address": issuer_address, "publickey": issuer_key.hex()[2:], "workspace_contract" : issuer_workspace_contract , 'username' : issuer_username } )	
		flash(issuer_username + ' has been added as Issuer in your White List')
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
		flash('The Issuer '+session['issuer_username_to_remove']+ '  has been removed')
		del session['issuer_username_to_remove']
		del session['issuer_address_to_remove']
		return redirect (mode.server +'user/?username=' + username)




	
@app.route('/user/description/', methods=['POST'])
def description() :
	username = check_login(session.get('username'))	
	newdescription=request.form.get('description')
	if session['description'] != newdescription :	
		user = Identity(session['workspace_contract'], mode)
		user.setDescription(newdescription)
		session['description'] = newdescription
	return redirect(mode.server + 'user/?username=' + session['username'])

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
	
# TEST database
@app.route('/database/')
def database() :
	return mode.register

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
	
	email=getEmail(workspace_contract,mode)
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
