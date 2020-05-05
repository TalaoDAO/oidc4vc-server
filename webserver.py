"""
pour l authentication cf https://realpython.com/token-based-authentication-with-flask/

pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization

interace wsgi https://www.bortzmeyer.org/wsgi.html

import ipfshttpclient

request : http://blog.luisrei.com/articles/flaskrest.html
"""
import os
from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template
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
from protocol import Identity, Data, getresolver, getresume, load_register_from_file, address, getEmail, getPrivatekey, contractsToOwners, data_from_publickey
from protocol import deleteName, deleteDocument, deleteClaim, readProfil, isdid, getdata, destroyWorkspace, addcertificate, canRegister_email, updateName, addkey, addName, delete_key
import environment
import web_create_identity
import web_certificate
import hcode

# environment setup
mode=environment.currentMode()
w3=mode.w3

UPLOAD_FOLDER = './uploads'

# Flask and Session setup	
app = FlaskAPI(__name__)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'redis'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)
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



""" gestion du menu de gestion des Events  """
def event_display(eventlist) :
			
	event_html = ""
	index = 0
	for key in sorted(eventlist, reverse=True) :
		index += 1
		date= key
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

#                                <p>""" + texte + """</p>

############################################################################################
#         DATA
############################################################################################
""" on ne gere aucune information des data en session """


@app.route('/data/<dataId>', methods=['GET'])
def data2(dataId) :
	
	workspace_contract = '0x'+dataId.split(':')[3]
	if session.get('workspace_contract') == workspace_contract and 'event' in session :
		myevent = session['event']
	else :	
		myevent = event_display(workspace_contract)                             
		session['event'] = myevent
		
	mydata = Data(dataId,mode)
			
	mytopic = mydata.topic.capitalize() + ' - ' + mydata.encrypted.capitalize()
	
	
	myissuer = """<b>Identity</b> : <a class = "card-link" href = """+mydata.issuer_endpoint+""">"""+mydata.issuer_id+"""</a><br>
				<b>Type</b> : """ + mydata.issuer_type + """<br>				
				<b>Name</b> : """ + mydata.issuer_name + """<br>
				<b>Username</b> : """ + mydata.issuer_username
	
	myprivacy = """ <b>Privacy</b> : """ + mydata.encrypted + """<br>"""
	
	
	myadvanced = """<b>Data Id</b> : """ + mydata.id + """<br>
				<b>Created</b> : """ + mydata.created + """<br>	
				<b>Expires</b> : """ + mydata.expires.capitalize() + """<br>
				<b>Signature</b> : """ + mydata.signature + """<br>
				<b>Signature Type</b> : """ + mydata.signatureType + """<br>
				<b>Signature Check</b> : """ + mydata.signatureCheck + """<br>
				<b>Transaction Hash</b> : """ + mydata.transactionHash + """<br>					
				<b>Data storage</b> : <a class="card-link" href=""" + mydata.datalocation + """>""" + mydata.datalocation + """</a>"""
	
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
				<b>Skills</b> : """+mydata.value['skills']+"""<br>
				<b>Certificate</b> : """+mydata.value['certificate_link']
	
	
	elif mydata.topic.capitalize() == "Education" :
		print('mydatatopic = ', mydata.topic)
		return 'work in progress'
	elif mydata.topic.capitalize() == "Employability" :
		print('mydatatopic = ', mydata.topic)
		return 'work in progress'		
	else :
		mytitle = 'Profil'
		mysummary = ''		
		myvalue = """<b>"""+mydata.topic.capitalize()+"""</b> : """+mydata.value
	
	if session.get('picture') is None :
		mypicture = 'anonymous1.jpeg'
	else :
		mypicture = session['picture']
			
	mydelete_link = "/talao/api/data/delete/"
	
	myusername = mydata.issuer_username
	session['username'] = myusername
		
	return render_template('data.html',
							topic = mytopic,
							issuer = myissuer,
							title = mytitle,
							summary = mysummary,
							value = myvalue,
							privacy = myprivacy,
							advanced = myadvanced,
							delete_link = mydelete_link,
							event = myevent,
							picturefile = mypicture,
							username = myusername)

# 70 39 04 06#
# tel 0172260470
#######################################################################################
#                        IDENTITY
#######################################################################################
@app.route('/login/', methods = ['GET'])
#@app.route('/user/login/', methods = ['GET'])
def login() :
		return render_template('login.html')

@app.route('/logout/', methods = ['GET'])
#@app.route('/user/logout/', methods = ['GET'])
def logout() :
	if session.get('rememberme') != 'on' :
		session.clear()
	else :
		pass
	return render_template('login.html')

""" fonction principale d'affichage de l identité """
@app.route('/user/', methods = ['GET'])
def user() :
	if request.args.get('option') is not None :
		session['rememberme'] = request.args.get('option')
	else :
		pass
	username = request.args['username']	
	if address(username,mode.register) is None :
			my_message = "Username not found"		
			return render_template('login.html', message=my_message)	
	else :
		pass
	workspace_contract = address(username, mode.register)	
	if session.get('username') != username or 'personal' not in session :
		print('premiere instanciation du user')
		user = Identity(workspace_contract, mode)
		session['username'] = user.username		
		session['address'] = user.address
		session['workspace_contract'] = user.workspace_contract
		session['experience'] = user.experience
		session['personal'] = user.personal
		session['contact'] = user.contact
		session['language'] = user.language
		session['events']=  user.eventslist
		session['controller'] = user.managementkeys
		session['issuer'] = user.claimkeys
		session['partner'] = user.partners
		session['education'] = user.education
		session['did'] = user.did
		session['eth'] = user.eth
		if user.picture is None :
			session['picture'] = "anonymous1.png"
		else :
			session['picture'] = user.picture		
	#this_name = session['personal']['firstname']['data']+ ' '+ session['personal']['lastname']['data']
	#(radio, mylang1, mylang2, mylang3)= session['language']
	
	my_event = session.get('events')
	my_picture = session['picture']
	my_username = session['username'] 
	my_event_html, my_counter =  event_display(session['events'])
	controller_list = session['controller']
	issuer_list = session['issuer']
	experience_list = session['experience']
	partners_list = session['partner']		
	education_list = session['education']
	
	my_experience = ''
	for experience in experience_list :
		exp_html = """<hr> 
				<b>Company</b> : """+experience['organization']['name']+"""<br>			
				<b>Title</b> : """+experience['title']+"""<br>
				<b>Description</b> : """+experience['description'][:100]+"""...<br>
				<p>
					<a class="text-secondary" href="#remove">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove"></i>
					</a>
					<a class="text-secondary" href=/data/"""+experience['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
		my_experience = my_experience + exp_html
	
	my_personal = """ 
				<b>Firstname</b> : <a class="card-link" href=/data/"""+session['personal']['firstname']['id']+""">"""+session['personal']['firstname']['data']+"""</a><br>
				<b>Lastname</b> : <a class="card-link" href=/data/"""+session['personal']['lastname']['id']+""">"""+session['personal']['lastname']['data']+"""</a><br>
				<b>Authentification Email</b> : <a class="card-link" href=/data/"""+session['personal']['email']['id']+""">"""+session['personal']['email']['data']+"""</a><br>				
				<b>Username</b> : <a class="card-link" href=/username/?username="""+session['username']+""">"""+session['username']+"""</a><br>
				<b>Picture</b> : <a class="card-link" href=/picture/"""+session['picture']+""">"""+session['picture']+"""</a>"""	
	
	if session['contact'] is None :
		my_contact =  """ <a class="card-link" href="">Add Contact</a>"""
	else :
		my_contact = """
					<b>Contact Email</b> : """ + session['contact']['data']['email'] + """</a><br>						
					<b>Contact Phone</b> : """ + session['contact']['data']['phone'] + """</a><br>				
					<b>Contact Twitter</b> : """ + session['contact']['data']['twitter'] + """</a><br>				
					<a class="card-link" href=/data/""" + session['contact']['id'] + """>Delete or Update</a>"""				
	
	
	my_education = ""
	for education in education_list :
		edu_html = """<hr> 
				<b>Organization</b> : """+education['data']['organization']+"""<br>			
				<b>Title</b> : """+education['data']['studyType']+"""<br>
				<b>Start Date</b> : """+education['data']['startDate']+"""<br>
				<b>End Date</b> : """+education['data']['endDate']+"""<br>				
				<p>
					<a class="text-secondary" href="#remove">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove"></i>
					</a>
					<a class="text-secondary" href=/data/"""+education['id'] + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
		my_education = my_education + edu_html
	
	my_advanced = """
					<b>Workspace Contract</b> : """ + session['workspace_contract'] + """<br>						
					<b>Address</b> : """ + session['address'] + """<br>				
					<b>DID</b> : """ + session['did']			
	
	my_languages = ""
	
	my_skills = ""

	my_controller = ''
	for controller in controller_list :
		print(controller)
		controller_html = """<hr>
				<p>""" + controller['username'] + """
					<a class="text-secondary" href="/user/remove_controller/?controller_username="""+controller['username']+"""&amp;controller_address="""+controller['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">    </i>
					</a>
					<a class="text-secondary" href="#explore">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
		my_controller = my_controller + controller_html
		
	my_partner = ""
	for partner in partners_list :
		partner_html = """<hr>
				<p>""" + partner['username'] + """
					<a class="text-secondary" href="#remove">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove"></i>
					</a>
					<a class="text-secondary" href="#explore">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
		my_partner = my_partner + partner_html
		
	my_claim_issuer = ""
	for issuer in issuer_list :
		issuer_html = """<hr>
				<p>""" + issuer['username'] + """
					<a class="text-secondary" href="#remove">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove"></i>
					</a>
					<a class="text-secondary" href="#explore">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""
		my_claim_issuer = my_claim_issuer + issuer_html
	
	my_account = """<b>Balance ETH</b> : """ + str(session['eth'])				

	
	return render_template('identity.html',
							personal=my_personal,
							contact=my_contact,
							experience=my_experience,
							education=my_education,
							languages=my_languages,
							skills=my_skills,
							controller=my_controller,
							partner=my_partner,
							claimissuer=my_claim_issuer,
							advanced=my_advanced,
							event=my_event_html,
							counter=my_counter,
							account=my_account,
							picturefile=my_picture,
							username=my_username)	

# picture helper
@app.route('/user/photo/', methods=['POST'])
def photo() :
	username = session['username']
	workspace_contract = address(username, mode.register)	
	user = Identity(workspace_contract, mode)
	if 'file' not in request.files:
		print('No file part')
	myfile = request.files['file']
	filename = secure_filename(myfile.filename)
	myfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	user.uploadPicture('./uploads/' + filename)
	print('picture hash = ',user.picture)	
	return redirect(mode.server + 'user/?username=' + user.username)

@app.route('/user/contact_settings/', methods=['POST'])
def contact_settings() :	
	return redirect(mode.server + 'user/?username=' + user.username)

# partnership request
@app.route('/user/partnership/', methods=['GET'])
def partnership() :	
	return render_template('parnership_request.html')
@app.route('/user/partnership/', methods=['POST'])
def partnership_1() :
	return render_template('parnership_request.html')


# add controller
@app.route('/user/add_controller/', methods=['GET'])
def add_controller() :	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	return render_template('add_controller.html', picturefile=my_picture, event=my_event_html, counter=my_counter)
@app.route('/user/add_controller/', methods=['POST'])
def add_controller_1_() :	
	controller_name = request.form['controller_name']
	controller_wallet = request.form['controller_wallet']
	workspace_contract_from = mode.relay_workspace_contract
	address_from = mode.relay_address	
	private_key_from = mode.relay_private_key
	address_to = session['address']
	workspace_contract_to = session['workspace_contract']
	address_partner = controller_wallet
	purpose = 1 
	addkey(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, address_partner, purpose, mode, synchronous=False) 
	addName(controller_name, controller_wallet, mode)
	username = session['username']
	# update controller list in session
	contract = mode.w3.eth.contract(workspace_contract_to, abi=constante.workspace_ABI)
	key_list = contract.functions.getKeysByPurpose(1).call()
	controller_keys = []
	for i in key_list :
		key = contract.functions.getKey(i).call()
		key_Id = mode.w3.soliditySha3(['string', 'string'], [key[2].hex(), 'MANAGEMENT']).hex()
		controller = data_from_publickey(key[2].hex(), mode)
		if controller is None : 
			controller = {'workspace_contract' : 'unknown' , 'username' : 'unknown'}
		controller_keys.append({"address": address_to, 	"publickey": key[2].hex(), "workspace_contract" : controller['workspace_contract'] , 'username' : controller['username'] } )
	session['controller'] = controller_keys
	return redirect (mode.server +'user/?username=' + username)

# remove controller
@app.route('/user/remove_controller/', methods=['GET'])
def remove_controller() :	
	controller_username = request.args['controller_username']
	controller_address : request.args['controller_address']
	session['controller_address_to_remove'] = request.args['controller_address']
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	return render_template('remove_controller.html', picturefile=my_picture, event=my_event_html, counter=my_counter, controller_name=controller_username)
@app.route('/user/remove_controller/', methods=['POST'])
def remove_controller_1_() :	
	workspace_contract_to = session['workspace_contract']
	address_to = session['address']
	address_partner = session['controller_address_to_remove']
	purpose = 1
	address_from = mode.relay_address
	workspace_contract_from = mode.relay_workspace_contract
	private_key_from = mode.relay_private_key
	delete_key(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, address_partner, purpose, mode,  synchhronous=False) 
	# update controller list in session
	contract = mode.w3.eth.contract(workspace_contract_from, abi=constante.workspace_ABI)
	key_list = contract.functions.getKeysByPurpose(1).call()
	controller_keys = []
	for i in key_list :
		key = contract.functions.getKey(i).call()
		key_Id = mode.w3.soliditySha3(['string', 'string'], [key[2].hex(), 'MANAGEMENT']).hex()
		controller = data_from_publickey(key[2].hex(), mode)
		if controller is None : 
			controller = {'address' : 'unknown', 'workspace_contract' : 'unknown' , 'username' : 'unknown'}
		controller_keys.append({"address": address_from, 	"publickey": key[2].hex(), "workspace_contract" : controller['workspace_contract'] , 'username' : controller['username'] } )
	session['controller'] = controller_keys
	username = session['username']
	return redirect (mode.server +'user/?username=' + username)



@app.route('/user/experience_delete/', methods=['GET'])
def experience_2() :
	username = session['username']
	experienceId = request.args['delete']
	print('experience to delete = ', experienceId)
	user = Identity(session['workspace_contract'],mode)
	user.deleteExperience(experienceId)
	session['experience'] = user.experience
	return redirect(mode.server + 'user/experience/')
	
@app.route('/user/description/', methods=['POST'])
def description() :
	newdescription=request.form.get('description')
	if session['description'] != newdescription :	
		username = session['username']
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

@app.route('/user/user_settings/', methods=['POST'])
def user_settings() :
	username = session['username']
	newfirstname = request.form.get('firstname')
	newlastname = request.form.get('lastname')
	newusername = request.form.get('username')
	newemail = request.form.get('email')
	if session['lastname'] != newlastname or session['firstname'] != newfirstname or session['email'] != newemail :		
		user = Identity(session['workspace_contract'], mode)		
		user.setUserSettings(newfirstname, newlastname, newemail)
		session['firstname'] = newfirstname
		session['lastname'] = newlastname
		session['email'] = newemail	
	if session['username'] != newusername :		
		updatename(username, newusername, mode)
		session['username'] = newusername	
	return redirect(mode.server+'user/?username='+session['username'])


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
	if address(username, mode.register) == None :
		mymessage="Your username is not registered"
		return render_template('remove1.html', message=mymessage)
	
	did=session['did']	
	workspace_contract_did='0x'+did.split(':')[3]
	workspace_contract=address(username, mode.register)
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
	

##################################################
# Create data
##################################################
@app.route('/talao/api/data/create/', methods=['GET'])
def dataCreate_1() :
	print (request.form['value'])
	return render_template('create1.html', message="", myusername="")
	
	
@app.route('/talao/api/data/create/', methods=['POST'])
def dataCreate_2() :
	username= request.form.get('username')
	print("username = ", username)
	data=session['data']
	return {"msg" : "work in progress...."} # a retirer
	

##################################################
# Delete data
##################################################			
@app.route('/talao/api/data/', methods=['POST'])
def dataDelete_1() :
	username= request.form['username']
	data=session['data']
	workspace_contract='0x'+data.split(':')[3]
	if 'username' in session and session['username'] == username and address(username,mode.register) == workspace_contract : # on efface sans passer par l'ecran de saisie de code 
		private_key=getPrivatekey(workspace_contract,mode)
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claimdocId=data.split(':')[5]
		if data.split(':')[4] == 'document' :
			print("effacement de document au prmeier passage")
			deleteDocument(workspace_contract, private_key,claimdocId,mode)
		else :
			deletClaim(workspace_contract, private_key, claimdocId,mode)
			print("effacement de document au premier passage")
		mymessage = 'Deletion done' 
		return render_template("delete3.html", message = mymessage)
	
	if address(username, mode.register) is None :
		mymessage = "Your username is not registered"
		if 'username' in session :
		 del session['username']
		return render_template('delete1.html', message=mymessage)
	
	workspace_contract = address(username, mode.register)
	data=session['data']
	workspace_contract_data = '0x'+data.split(':')[3]
	if workspace_contract_data != workspace_contract :
		if 'username' in  session :
			del session['username']
		mymessage = 'Your are not the owner of this Identity, you cannot delete this data.'
		return render_template("delete3.html", message = mymessage)
	
	email = getEmail(workspace_contract,mode)
	if not email :
		if 'username' in session :
			del session['username']
		mymessage = "Your email for authentification is not registered"
		return render_template('delete3.html', message= mymessage)			

	session['email'] = email
	session['username'] = username
	# envoi du code secret par email
	code = str(random.randint(100000, 999999))
	print('code secret = ', code)
	session['code'] = code
	session['try_number'] = 0
	Talao_message.messageAuth(email, code)
	mymessage = "Code has been sent"
	return render_template("delete2.html", message=mymessage)

# recuperation du code saisi et effacement de la data
@app.route('/talao/api/data/code/', methods=['POST'])
def dataDelete_2() :
	session['try_number'] += 1
	email = session['email']
	mycode = request.form['mycode']	
	data = session['data']
	if session['try_number'] > 3 :
		mymessage = "Too many trials (3 max)"
		return render_template("delete3.html", message = mymessage)
	
	if session.get('code') is None :
		mymessage = "Time out"
		return render_template("delete3.html", message = mymessage)
	
	# wrong code, delete
	if mycode == session['code'] : 
		workspace_contract='0x'+data.split(':')[3]
		private_key = getPrivatekey(workspace_contract,mode)	
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claimdocId = data.split(':')[5]
		if data.split(':')[4] == 'document' :
			print("effacement de document au prmeier passage")
			deleteDocument(workspace_contract, private_key,claimdocId,mode)
		else :
			print("effacement de claim au premier passage")
			deleteClaim(workspace_contract, private_key, claimdocId,mode)
		mymessage = 'Deletion done' 
		return render_template("delete3.html", message = mymessage)

	else :
		mymessage = 'This code is incorrect'	
		return render_template("delete2.html", message = mymessage)

# exit and return to resume
@app.route('/talao/api/data/code/', methods=['GET'])
def dataDelete_3() :
	data=session['data']
	did = 'did:talao:'+mode.BLOCKCHAIN+':'+data.split(':')[3]
	return redirect(mode.server+'resume/'+did)
	


#########################################################################
#   version JSON : RESUME + RESOLVER + DATA
#########################################################################

""" ecran d accueil pour la saisie du username """
@app.route('/resume/')
def resume_home() :
	return render_template("home_resume.html")

""" affichage du resume au format json """		
@app.route('/resume/did/', methods=['GET'])
def resume() :
	did = request.args['did']
	if isdid(did,mode) :
		truedid=did
	else :
		
		if address(did.lower(),mode.register) is not None :
			truedid='did:talao:'+mode.BLOCKCHAIN+':'+address(did.lower(), mode.register)[2:]
		else :
			flash('identifier not found')
			return redirect (mode.server+'resume/')
	
	workspace_contract='0x'+truedid.split(':')[3]
	print(workspace_contract)
	return getresume(workspace_contract,truedid,mode)	

""" affichage du did au format json """
# GETresolver with redis session
@app.route('/resolver/<did>', methods=['GET'])
#@app.route('/talao/resolver/api/<did>', methods=['GET'])
def DID_Document(did) :
	workspace_contract='0x'+did.split(':')[3]
	if session.get('lastworkspacefordiddoc')== workspace_contract and session.get('lastdidoc') is not None :
		didoc = session['lastdidoc']
		print('deja passe')
	else :		
		session['lastworkspacefordidoc']=workspace_contract
		didoc = getresolver(workspace_contract,did,mode)
		session['lastdidoc']=didoc	
	if not didoc :
		return {'msg' : 'Identity invalid'}
	return didoc
	
# GETresume Profil idem resume.....
@app.route('/talao/profil/<did>', methods=['GET'])
def Company_Profil(did) :
	workspace_contract='0x'+did.split(':')[3]
	if session.get('lastworkspaceforresume')== workspace_contract and session.get('lastresume') != None :
		resume = session['lastresume']
	else :		
		session['lastworkspaceforresume']=workspace_contract
		resume = getresume(workspace_contract,did,mode)
		session['lastresume']=resume	
	if not resume :
		return {'msg' : 'Identity invalid'}
	return resume

# GETresume	Resume with cache
@app.route('/talao/resume/<did>', methods=['GET'])	
#@app.route('/resume/<did>', methods=['GET'])
def User_Resume(did) :
	workspace_contract='0x'+did.split(':')[3]
	if session.get('lastworkspaceforresume')== workspace_contract and session.get('lastresume') != None :
		resume = session['lastresume']
	else :		
		session['lastworkspaceforresume']=workspace_contract
		resume = getresume(workspace_contract,did,mode)
		session['lastresume']=resume	
	if not resume :
		return {'msg' : 'Identity invalid'}
	data = resume	
	return resume

""" affichage des Data au format JsON """
@app.route('/talao/data/<data>', methods=['GET'])
def data(data) :
	session['data'] = data
	return getdata(data, mode)
	

#######################################################
#                        MAIN, server launch
#######################################################
# setup du registre nameservice

print('initialisation du serveur')


if __name__ == '__main__':
	
	if mode.myenv == 'production' or mode.myenv == 'prod' :
		app.run(host = mode.flaskserver, port= mode.port, debug=True)
	elif mode.myenv =='test' :
		app.run(host='127.0.0.1', port =4000, debug=True)
	else :
		print("Erreur d'environnement")
