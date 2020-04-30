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
from protocol import identity, Data, getresolver, getresume, load_register_from_file, address, getEmail, getPrivatekey, contractsToOwners
from protocol import deleteName, deleteDocument, deleteClaim, readProfil, isdid, getdata, destroyWorkspace, addcertificate, canRegister_email, updateName
import environment
import web_create_identity
import web_show_certificate
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


# Centralized @route pour web_create_identity
"""
lacces web permet a un user de creer une identité et de recuperer par email les informations de la cle privée et cle RSA
Par la suite le user peut creer par lui meme une addresse et ethereum et demander le transfert de l identité. 
Si Talao conserve une copie de la cle RSA et une cle de type 1 le user peut continuer a utiliser l acces web.

"""
app.add_url_rule('/talao/register/',  view_func=web_create_identity.authentification)
app.add_url_rule('/talao/register/', view_func=web_create_identity.POST_authentification_1, methods=['POST'])
app.add_url_rule('/talao/register/code/', view_func=web_create_identity.POST_authentification_2, methods=['POST'])
app.add_url_rule('/talao/register/code/', view_func=web_create_identity.POST_authentification_3, methods=['GET'])




# Centralized @route pour certificate
app.add_url_rule('/certificate/<data>',  view_func=web_show_certificate.show_certificate)

fa = FontAwesome(app)

##################################
#gestion du menu de gestion des Alert

def _eventDisplay(workspace_contract) :
	
	if session.get('workspace_contract')  == workspace_contract and 'alertlist' in session : # meme user mais pas meme data
		myalertlist=session['alertlist']
	else :
		user=identity(workspace_contract, mode)
		myalertlist = user.getAlerts()
		session['myalertlist']=myalertlist			
		myalert_html=""
		count=min([5, len(myalertlist)])
	for i in range(0, count) :
		date = myalertlist[i]['date']
		texte=myalertlist[i]['alert']
		doc_id=myalertlist[i]['doc_id']
		event_type=myalertlist[i]['event']
		if doc_id == None :
			href=" "
		else :
			href="href= /data/"+doc_id
		icon='class="fas fa-file-alt text-white"'
		background='class="bg-success icon-circle"'
		
		if event_type == 'DocumentRemoved' or event_type == 'ClaimRemoved' :
			icon='class="fas fa-trash-alt text-white"'
			background='class="bg-warning icon-circle"'
		
		alert= """<a class="d-flex align-items-center dropdown-item" """+href+"""><div class="mr-3">
                                                <div """+background+"""><i """+icon+"""></i></div>
                                            </div><div><span class="small text-gray-500">"""+date+"""</span>
                                             <p>"""+texte+"""</p></div></a>"""
		myalert_html=myalert_html+alert 
	
	return myalert_html

############################################################################################
#         DATA
############################################################################################
@app.route('/talao/api/data/<data>', methods=['GET'])
def data(data) :
	session['data']=data
	if request.args.get('action') == None :
		return redirect(mode.server+'data/'+data)
		#return getdata(data,mode)
	
	elif request.args.get('action') == 'delete' :
		if 'username' in session : 
			username=session['username']
			return render_template('delete1.html', message="", myusername=username)

		else :
			return render_template('delete1.html', message="", myusername="")
	
@app.route('/talao/api/data/delete/', methods=['GET'])
def delete() :	
	if 'username' in session : 
		username = session['username']
		return render_template('delete1.html', message="", myusername=username)
	else :
		return render_template('delete1.html', message="", myusername="")		


@app.route('/data/<dataId>', methods=['GET'])
def data2(dataId) :
	
	workspace_contract = '0x'+dataId.split(':')[3]
	if session.get('workspace_contract') == workspace_contract and 'event' in session :
		myevent = session['event']
	else :	
		myevent = _eventDisplay(workspace_contract)                             
		session['event'] = myevent
		
	mydata= Data(dataId,mode)
			
	mytopic = mydata.topic.capitalize()+' - '+mydata.encrypted.capitalize()
	
	
	myissuer = """<b>Identity</b> : <a class="card-link" href="""+mydata.issuer_endpoint+""">"""+mydata.issuer_id+"""</a><br>
				<b>Name</b> : """+mydata.issuer_name+"""<br>
				<b>Username</b> : """+mydata.issuer_username
	
	myprivacy = """ <b>Privacy</b> : """+mydata.encrypted+"""<br>"""
	
	
	myadvanced = """<b>Data Id</b> : """+mydata.id+"""<br>
				<b>Created</b> : """+mydata.created+"""<br>	
				<b>Expires</b> : """+mydata.expires.capitalize()+"""<br>
				<b>Signature</b> : """+mydata.signature+"""<br>
				<b>Signature Type</b> : """+mydata.signatureType+"""<br>
				<b>Signature Check</b> : """+mydata.signatureCheck+"""<br>
				<b>Transaction Hash</b> : """+mydata.transactionHash+"""<br>					
				<b>Data storage</b> : <a class="card-link" href="""+mydata.datalocation+""">"""+mydata.datalocation+"""</a>"""
	
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
	
	if session.get('picture') == None :
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


#######################################################################################
#                        IDENTITY
##############################################  USER  LOGIN/LOGOUT ####################
@app.route('/login/', methods = ['GET'])
@app.route('/user/login/', methods = ['GET'])
def login() :
		return render_template('login.html')

@app.route('/logout/', methods = ['GET'])
@app.route('/user/logout/', methods = ['GET'])
def logout() :
	if session.get('rememberme') != 'on' :
		session.clear()
	else :
		pass
	return render_template('login.html')


@app.route('/user/', methods = ['GET'])
def user() :
	if request.args.get('option') != None :
		session['rememberme'] = request.args.get('option')
	else :
		pass
	username = request.args['username']	
	if address(username,mode.register) == None :
			mymessage = "Username not found"		
			return render_template('login.html', message=mymessage)	
	else :
		pass
	workspace_contract = address(username, mode.register)	
	if session.get('username') != username :
		user=identity(workspace_contract, mode)
		print(user.__dict__)
		session['username'] = user.username		
		session['address'] = user.address
		session['workspace_contract'] = user.workspace_contract
		session['experience'] = user.getExperience()
		session['personal'] = user.getPersonal()
		session['language'] = user.getLanguage()
		session['event']=_eventDisplay(workspace_contract)	
		if user.picture == None :
			session['picture'] = "anonymous1.png"
		else :
			session['picture'] = user.picture		
						
	thisname = session['personal']['firstname']['data']+ ' '+ session['personal']['lastname']['data']
	#(radio, mylang1, mylang2, mylang3)= session['language']
	
	myevent=session.get('event')
	
	mypersonal = ""
	
	exp = session['experience']	
	myexperience = ''
	for e in range(0,len(exp)) :
		exphtml = """ 
				<b>Company</b> : """+exp[e]['organization']['name']+"""<br>			
				<b>Title</b> : """+exp[e]['title']+"""<br>
				<b>Description</b> : """+exp[e]['description'][:100]+"""...<br>
				<b>My Data</b> : <a class="card-link" href=/data/"""+exp[e]['id']+""">"""+exp[e]['id']+"""</a><hr>"""
				
				
		myexperience = myexperience + exphtml
	
	mypicture = session['picture']
	
	mypersonal = """ 
				<b>Firstname</b> : <a class="card-link" href=/data/"""+session['personal']['firstname']['id']+""">"""+session['personal']['firstname']['data']+"""</a><br>
				<b>Lastname</b> : <a class="card-link" href=/data/"""+session['personal']['lastname']['id']+""">"""+session['personal']['lastname']['data']+"""</a><br>
				<b>Email</b> : <a class="card-link" href=/data/"""+session['personal']['email']['id']+""">"""+session['personal']['email']['data']+"""</a><br>				
				<b>Username</b> : <a class="card-link" href=/username/?username="""+session['username']+""">"""+session['username']+"""</a><br>
				<b>Picture</b> : <a class="card-link" href=/picture/"""+session['picture']+""">"""+session['picture']+"""</a>"""

	myusername = session['username'] 
	
	myeducation = ""
	mylanguages = ""
	myskills = ""
	
	mycontroller = ""
	mypartner = ""
	myclaimissuer = ""
	myaccount = ""
	
	
	return render_template('identity.html',
							personal = mypersonal,
							experience = myexperience,
							education = myeducation,
							languages = mylanguages,
							skills = myskills,
							controller = mycontroller,
							partner = mypartner,
							claimissuer = myclaimissuer,
							event = myevent,
							picturefile = mypicture,
							username = myusername)
	

@app.route('/user/photo/', methods=['POST'])
def photo() :
	username=session['username']
	workspace_contract = address(username, mode.register)	
	user=identity(workspace_contract, mode)
	if 'file' not in request.files:
		print('No file part')
	myfile = request.files['file']
	filename = secure_filename(myfile.filename)
	myfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	user.uploadPicture('./uploads/'+filename)
	print('picture hash = ',user.picture)	
	return redirect(mode.server+'user/?username='+user.username)

@app.route('/user/contact_settings/', methods=['POST'])
def contact_settings() :	
	return redirect(mode.server+'user/?username='+user.username)



@app.route('/user/experience_delete/', methods=['GET'])
def experience_2() :
	username=session['username']
	experienceId=request.args['delete']
	print('experience to delete = ', experienceId)
	user=identity(session['workspace_contract'],mode)
	user.deleteExperience(experienceId)
	session['experience']=user.experience
	return redirect(mode.server+'user/experience/')

	
@app.route('/user/description/', methods=['POST'])
def description() :
	newdescription=request.form.get('description')
	if session['description'] != newdescription :	
		username=session['username']
		user=identity(session['workspace_contract'], mode)
		user.setDescription(newdescription)
		session['description']=newdescription
	return redirect(mode.server+'user/?username='+session['username'])

@app.route('/user/languages/', methods=['GET'])
def languages() :
	print('entree dans languages ')
	username=session['username']
	lang1=request.args.get('lang1')
	lang2=request.args.get('lang2')
	lang3=request.args.get('lang3')
	fluency1=request.args.get('radio1')
	fluency2=request.args.get('radio2')
	fluency3=request.args.get('radio3')
	workspace_contract = address(username, mode.register)	
	user=identity(workspace_contract, mode)
	language=[{"language": lang1,"fluency": fluency1}, {"language": lang2,"fluency": fluency2}, {"language": lang3,"fluency": fluency3}]
	#language= [{"language": 'EN',"fluency": '1'}]
	user.setLanguage(language)
	return redirect(mode.server+'user/?username='+session['username'])

@app.route('/user/user_settings/', methods=['POST'])
def user_settings() :
	username=session['username']
	newfirstname=request.form.get('firstname')
	newlastname=request.form.get('lastname')
	newusername=request.form.get('username')
	newemail=request.form.get('email')
	if session['lastname'] != newlastname or session['firstname'] != newfirstname or session['email'] != newemail :		
		user=identity(session['workspace_contract'], mode)		
		user.setUserSettings(newfirstname, newlastname, newemail)
		session['firstname']=newfirstname
		session['lastname']=newlastname
		session['email']=newemail	
	if session['username'] != newusername :		
		updatename(username, newusername, mode)
		session['username']=newusername	
	return redirect(mode.server+'user/?username='+session['username'])
		
################################################# RESUME and RESOLVER #############################################

# GETresolver with redis session
@app.route('/resolver/api/<did>', methods=['GET'])
@app.route('/talao/resolver/api/<did>', methods=['GET'])
def DID_Document(did) :
	#global lastdidoc
	print('session = ',session)
	workspace_contract='0x'+did.split(':')[3]
	if session.get('lastworkspacefordiddoc')== workspace_contract and session.get('lastdidoc') != None :
		didoc = session['lastdidoc']
		print('deja passe')
	else :		
		print('premier passage')
		session['lastworkspacefordidoc']=workspace_contract
		didoc = getresolver(workspace_contract,did,mode)
		session['lastdidoc']=didoc	
	if didoc == False :
		return {'msg' : 'Identity invalid'}
	return didoc
	
# GETresume Profil idem resume.....
@app.route('/talao/api/profil/<did>', methods=['GET'])
def Company_Profil(did) :
	workspace_contract='0x'+did.split(':')[3]
	if session.get('lastworkspaceforresume')== workspace_contract and session.get('lastresume') != None :
		resume = session['lastresume']
		print('deja passe')
	else :		
		print('premier passage')
		session['lastworkspaceforresume']=workspace_contract
		resume = getresume(workspace_contract,did,mode)
		session['lastresume']=resume	
	if resume == False :
		return {'msg' : 'Identity invalid'}
	return resume

# GETresume	Resume with cache
@app.route('/talao/api/resume/<did>', methods=['GET'])	
@app.route('/resume/<did>', methods=['GET'])
def User_Resume(did) :
	workspace_contract='0x'+did.split(':')[3]
	if session.get('lastworkspaceforresume')== workspace_contract and session.get('lastresume') != None :
		resume = session['lastresume']
		print('deja passe')
	else :		
		print('premier passage')
		session['lastworkspaceforresume']=workspace_contract
		resume = getresume(workspace_contract,did,mode)
		session['lastresume']=resume	
	if resume == False :
		return {'msg' : 'Identity invalid'}
	data=resume	
	return resume
###############################################################################################################

# upload des photos pour certificate
@app.route('/uploads/<filename>')
def send_file(filename):
	UPLOAD_FOLDER='photos'
	return send_from_directory(UPLOAD_FOLDER, filename)
	

# upload des fonts
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
	session['did']=did
	session['endtime']=datetime.now()+timedelta(minutes=3)
	print(session['endtime'])
	return render_template('remove1.html', message="", myusername="")
	
@app.route('/talao/api/did/remove/', methods=['POST'])
def identityRemove_2() :
	if datetime.now() > session['endtime'] :
		mymessage="time out"
		return render_template('remove3.html', message= mymessage)	
	
	username= request.form.get('username')
	if address(username, mode.register) == None :
		mymessage="Your username is not registered"
		return render_template('remove1.html', message=mymessage)
	
	did=session['did']	
	workspace_contract_did='0x'+did.split(':')[3]
	workspace_contract=address(username, mode.register)
	if workspace_contract_did != workspace_contract :
		mymessage = 'Your are not the owner of this Identity, you cannot delete it.'
		return render_template("remove3.html", message = mymessage)
	
	email=getEmail(workspace_contract,mode)
	if email == False :
		mymessage="Your email for authentification is not registered"
		return render_template('remove3.html', message= mymessage)			

	session['username']=username
	# envoi du code secret par email
	code = str(random.randint(100000, 999999))
	print('code secret = ', code)
	session['code']=code
	session['try_number']=0
	Talao_message.messageAuth(email, code)
	mymessage="Code has been sent"
	return render_template("remove2.html", message = mymessage)

# recuperation du code saisi et effacement du did
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
		if private_key == False :
			mymessage = "Talao does not have the private key of this Identity"
			return render_template("remove3.html", message = mymessage)	
		
		# on detruit le workspace et on efface la cle du registre
		destroyWorkspace(workspace_contract, private_key, mode)
		username=session['username']
		deleteName(username,mode)
		mymessage = 'Identity has been removed and data deleted' 
		return render_template("remove3.html", message = mymessage)

	else : # code incorrect
		mymessage = 'This code is incorrect'	
		return render_template("remove2.html", message = mymessage)

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
	
	if address(username, mode.register) == None :
		mymessage="Your username is not registered"
		if 'username' in session :
		 del session['username']
		return render_template('delete1.html', message=mymessage)
	
	workspace_contract=address(username, mode.register)
	data=session['data']
	workspace_contract_data='0x'+data.split(':')[3]
	if workspace_contract_data != workspace_contract :
		if 'username' in  session :
			del session['username']
		mymessage = 'Your are not the owner of this Identity, you cannot delete this data.'
		return render_template("delete3.html", message = mymessage)
	
	email=getEmail(workspace_contract,mode)
	if email == False :
		if 'username' in session :
			del session['username']
		mymessage="Your email for authentification is not registered"
		return render_template('delete3.html', message= mymessage)			

	session['email']=email
	session['username']=username
	# envoi du code secret par email
	code = str(random.randint(100000, 999999))
	print('code secret = ', code)
	session['code']=code
	session['try_number']=0
	Talao_message.messageAuth(email, code)
	mymessage="Code has been sent"
	return render_template("delete2.html", message = mymessage)

# recuperation du code saisi et effacement de la data
@app.route('/talao/api/data/code/', methods=['POST'])
def dataDelete_2() :
	session['try_number'] += 1
	email=session['email']
	mycode = request.form['mycode']	
	data=session['data']
	if session['try_number'] > 3 :
		mymessage = "Too many trials (3 max)"
		return render_template("delete3.html", message = mymessage)
	
	if session.get('code') == None :
		mymessage = "Time out"
		return render_template("delete3.html", message = mymessage)
	
	if mycode == session['code'] : # code correct, on efface 
		workspace_contract='0x'+data.split(':')[3]
		private_key=getPrivatekey(workspace_contract,mode)	
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claimdocId=data.split(':')[5]
		if data.split(':')[4] == 'document' :
			print("effacement de document au prmeier passage")
			deleteDocument(workspace_contract, private_key,claimdocId,mode)
		else :
			print("effacement de claim au premier passage")
			deleteClaim(workspace_contract, private_key, claimdocId,mode)
		mymessage = 'Deletion done' 
		return render_template("delete3.html", message = mymessage)

	else : # code incorrect
		mymessage = 'This code is incorrect'	
		return render_template("delete2.html", message = mymessage)

# sortie et retour vers resume
@app.route('/talao/api/data/code/', methods=['GET'])
def dataDelete_3() :
	data=session['data']
	did = 'did:talao:'+mode.BLOCKCHAIN+':'+data.split(':')[3]
	return redirect(mode.server+'resume/'+did)
	

##################################################
# Onboarding
##################################################
# onboarding
@app.route('/onboarding/<did>')
def	onboarding(did) :
	return { "msg" : "to be done"}


##################################################
# Saisie d un certificat pour entreprise
##################################################

# Formulaire de saisi 
@app.route('/certificate/experience/<did>', methods=['GET'])
def input_certificate(did):

	# recuperation des information sur le user
	workspace_contract='0x'+did.split(':')[3]
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	profil =readProfil(address,mode)
	username=profil['givenName']+' '+profil['familyName']
	myresumelink='http://vault.talao.io:4011/visit/'+workspace_contract
	print(did)
	return render_template("certificaterequest.html",name=username, resumelink= myresumelink, myuser_did=did)

@app.route('/certificate/experience/', methods=['POST']) # pour la demo on ne gere pas le bearer token, on utilise les champs hidden pour cinserver la trace du user di et issuer did
def input_certificate_1():
	#issuer
	workspace_contract_from = request.form['key'] # c est le workspace contract de l issuer
	
	issuer_did='did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract_from[2:]
	secret=request.form['secret'] # c ets le secret de creation du workspace
	if secret != 'talao' :
		mymessage ="secret is incorrect "
		return render_template("certificaterequest_1.html", message = mymessage)
	
	issuer=identity(workspace_contract_from,mode)
	if issuer.islive == False :
		mymessage ="Key is incorrect "
		return render_template("certificaterequest_1.html", message = mymessage)
	
	# user
	userdid = request.form['user_did']
	workspace_contract_to='0x'+userdid.split(':')[3]
	user=identity(workspace_contract_to,mode)
	address_to = user.address
	profil = user.profil
	username=user.username
	user.printIdentity()
	
	certificate=dict()
	certificate={"did_issuer" : issuer_did, 
	"did_user" : request.form['user_did'],
	"topicname" : request.form['topicname'],
	"type" : "experience",	
	"firstname" : profil['givenName'],
	"name" : profil['familyName'],
	"company" : {"name" : "Thales", "manager" : request.form['issuedby'], "managersignature" : "experingsignature.png",
		"companylogo" : "thaleslogo.jpeg", 'manager_email' : "jean.permet@thales.com"},
	"startDate" : request.form['startDate'],
	"endDate" :request.form['endDate'],
	"summary" :  request.form['summary'],
	"skills" : "Optoelectronics			IRST system		CAO/DAO",
	"position" : request.form['position'],
	"score_recommendation" : int(request.form['score1']),
	"score_delivery" : int(request.form['score2']),
	"score_schedule" : int(request.form['score3']),
	"score_communication" : int(request.form['score4'])}
	print(certificate)
	# issue certificate
	(resultat, msg) =addcertificate(issuer.address, issuer.private_key, user.workspace_contract, certificate,mode)
	if resultat == True :
		mymessage = "certification link = "+msg
	else :
		mymessage =msg	
	return render_template("certificaterequest_1.html", message = mymessage)


#####################################################
#   Talao Professional Identity Explorer
#####################################################


@app.route('/resume/')
def resume_home() :
	return render_template("home_resume.html")
		
@app.route('/resume/did/', methods=['GET'])
def resume() :
	did = request.args['did']
	if isdid(did,mode) :
		truedid=did
	else :
		
		if address(did.lower(),mode.register) != None :
			truedid='did:talao:'+mode.BLOCKCHAIN+':'+address(did.lower(), mode.register)[2:]
		else :
			flash('identifier not found')
			return redirect (mode.server+'resume/')
	
	workspace_contract='0x'+truedid.split(':')[3]
	print(workspace_contract)
	return getresume(workspace_contract,truedid,mode)	



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
