"""
piur l authentication cf https://realpython.com/token-based-authentication-with-flask/

pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization

interace wsgi https://www.bortzmeyer.org/wsgi.html


request : http://blog.luisrei.com/articles/flaskrest.html
"""



from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template
from flask_api import FlaskAPI, status
import ipfshttpclient
from flask_fontawesome import FontAwesome
import http.client
import threading
import random
import csv
from datetime import timedelta, datetime
import json

# dependances
import Talao_message
import createidentity
import constante
from protocol import identity, getresolver, getresume, load_register_from_file, address, getEmail, getPrivatekey, contractsToOwners
from protocol import deleteName, deleteDocument, deleteClaim, readProfil, isdid, getdata, destroyWorkspace, addcertificate, canRegister_email
import environment

# environment setup
mode=environment.currentMode('test', 'rinkeby')
w3=mode.w3

# Flask setup	
app = FlaskAPI(__name__)
fa = FontAwesome(app)
app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"

# thread
exporting_threads = {}
lastresume=dict()
lastdidoc=dict()

#####################################################	
# tools
######################################################

# Multithreading de creatidentity setup   https://stackoverflow.com/questions/24251898/flask-app-update-progress-bar-while-function-runs
class ExportingThread(threading.Thread):
	def __init__(self, firstname, lastname, email, mode):
		self.progress = 0
		super().__init__()
		self.firstname=firstname
		self.lastname=lastname
		self.email=email
		self.mode=mode
	def run(self):
		createidentity.creationworkspacefromscratch(self.firstname, self.lastname, self.email,self.mode)
		

def getclaimipfs (claim_id, workspace_contract) :
# @topicname est un str
# return un objet List
	
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	claimdata=contract.functions.getClaim(claim_id).call()
	print("claimdata = ", claimdata)
	if claimdata[5]!="" :
		data=client.get_json(claimdata[5])
		return data
	else :
		return False

# GETresolver
@app.route('/resolver/api/<did>', methods=['GET'])
@app.route('/talao/resolver/api/<did>', methods=['GET'])
def DID_Document(did) :
	global lastdidoc
	print('session = ',session)
	workspace_contract='0x'+did.split(':')[3]
	if session.get('lastworkspacefordiddoc')== workspace_contract :
		didoc = lastdidoc
		print('deja passe')
	else :		
		print('premier passage')
		session['lastworkspacefordidoc']=workspace_contract
		didoc = getresolver(workspace_contract,did,mode)
		lastdidoc=didoc	
	if didoc == False :
		return {'msg' : 'Identity invalid'}
	return didoc

		
# GETresume Profil
@app.route('/talao/api/profil/<did>', methods=['GET'])
def Company_Profil(did) :
	workspace_contract='0x'+did.split(':')[3]
	resume=getresume(workspace_contract,did,mode)
	if resume == False :
		return {'msg' : 'Identity invalid'}
	return resume


# GETresume	Resume
@app.route('/talao/api/resume/<did>', methods=['GET'])	
@app.route('/resume/<did>', methods=['GET'])
def User_Resume(did) :
	global lastresume
	print('session = ',session)
	workspace_contract='0x'+did.split(':')[3]
	if session.get('lastworkspaceforresume')== workspace_contract :
		resume = lastresume
		print('deja passe')
	else :		
		print('premier passage')
		session['lastworkspaceforresume']=workspace_contract
		resume = getresume(workspace_contract,did,mode)
		lastresume=resume	
	if resume == False :
		return {'msg' : 'Identity invalid'}
	return resume
	

# Nameservice
@app.route('/nameservice/api/reload/', methods=['GET'])
def GET_nameservice_reload() :
	load_register_from_file(mode)
	return {"CODE" : "reload done"}

# upload des photos
@app.route('/uploads/<filename>')
def send_file(filename):
	UPLOAD_FOLDER='photos'
	return send_from_directory(UPLOAD_FOLDER, filename)
	
# database
@app.route('/database/')
def database() :
	return mode.register


##################################################
# GETdata avec option Delete/Create
##################################################
@app.route('/talao/api/data/<data>', methods=['GET'])
def data(data) :
	session['data']=data
	if request.args.get('action') == None :
		return getdata(data,mode)
	
	elif request.args.get('action') == 'delete' :
		if 'username' in session : 
			username=session['username']
			return render_template('delete1.html', message="", myusername=username)

		else :
			return render_template('delete1.html', message="", myusername="")
	
	elif request.args.get('action') == 'create' :
		return render_template('create1.html', message="", myusername="")


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
			removeClaim(workspace_contract, private_key, claimdocId,mode)
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
			removeClaim(workspace_contract, private_key, claimdocId,mode)
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



		
#############################################################
#    affichage d'un certificat de type claim
#############################################################
#data='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:b34c2a6837a9e89da5ef886d18763fb13a12615814d50a5b73ae403cb547d788'
#data="did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:abf370997a7b240f56c62b8b33cc8976f9808d3889f3eed865c79e4622d90af4"
                

@app.route('/certificate/<data>', methods=['GET'])
def show_certificate(data):
	
	#data="did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:abf370997a7b240f56c62b8b33cc8976f9808d3889f3eed865c79e4622d90af4"

	claimId=data.split(':')[5]
	workspace_contract= '0x'+data.split(':')[3]
	certificate=getclaimipfs(claimId, workspace_contract)
	
	if certificate == False :
		return {"ERROR" : "No Certificate"}
	
	ok="color: rgb(251,211,5); font-size: 10px;"
	ko="color: rgb(0,0,0);font-size: 10px;"
	context=certificate.copy()
	context["manager"]=certificate["company"]["manager"]
	context["managersignature"]=certificate["company"]["managersignature"]
	context["companylogo"]=certificate["company"]["companylogo"]
	
	
	# gestion des "fa-star" 
	score=[]
	score.append(certificate["score_recommendation"])
	score.append(certificate["score_delivery"])
	score.append(certificate["score_schedule"])
	score.append(certificate["score_communication"])
	for q in range(0,4) :
		for i in range(0,score[q]) :
			context["star"+str(q)+str(i)]=ok
		for i in range(score[q],5) :
			context ["star"+str(q)+str(i)]=ko

	return render_template('certificate.html', **context)



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


	
#####################################################
#   CREATION IDENTITE ONLINE (html) pour le site talao.io
#####################################################
"""
le user reçoit par email les informations concernant son identité
Talao dispose d'une copie de la clé
On test si l email existe dans le back end
"""

@app.route('/talao/register/')
def authentification() :
	session.clear()
	return render_template("home.html",message='')

### recuperation de l email, nom et prenom
@app.route('/talao/register/', methods=['POST'])
def POST_authentification_1() :
	email = request.form['email']
	firstname=request.form['firstname']
	lastname=request.form['lastname']
	# stocké en session
	session['firstname']=request.form['firstname']
	session['lastname']=request.form['lastname']
	session['email']=email
	# check si email disponible
	if canRegister_email(email,mode) == False :
		return render_template("home.html", message = 'Email already used')	
	# envoi du code secret par email
	if session.get('code') == None :
		code = str(random.randint(100000, 999999))
		session['try_number']=1
		session['code']=code
		# envoi message de control du code
		Talao_message.messageAuth(email, str(code))
		print('code secret envoyé= ', code)
	else :
		print("le code a deja ete envoye")
	
	return render_template("home2.html", message = '')

# recuperation du code saisi
@app.route('/talao/register/code/', methods=['POST'])
def POST_authentification_2() :
	global exporting_threads
	email=session.get('email')
	lastname=session.get('lastname')
	firstname=session.get('firstname')
	mycode = request.form['mycode']
	session['try_number'] +=1
	print('code retourné = ', mycode)
	print (session)
	if mycode == session.get('code') :
		print('code correct')
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(firstname, lastname, email, mode)
		print("appel de createindentty")
		#exporting_threads[thread_id].start()
		mymessage = 'Registation in progress. You will receive an email with details soon.' 
	else :
		if session['try_number'] > 3 :
			mymessage = "Too many trials (3 max)"
			return render_template("home3.html", message = mymessage)

		mymessage = 'Error code'
		return render_template("home2.html", message = mymessage)

	return render_template("home3.html", message = mymessage)

		
@app.route('/talao/register/code/', methods=['GET'])
def POST_authentification_3() :
	return redirect(mode.server+'talao/register/')
	


#######################################################
#                        MAIN, server launch
#######################################################
# setup du registre nameservice

print('initialisation du serveur')


if __name__ == '__main__':
	
	if mode.env == 'production' or mode.env == 'prod' :
		app.run(host = mode.flaskserver, port= mode.port, debug=True)
	elif mode.env =='test' :
		app.run(host='127.0.0.1', port =4000, debug=True)
	else :
		print("Erreur d'environnement")
