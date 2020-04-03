"""
piur l authentication cf https://realpython.com/token-based-authentication-with-flask/

pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization

interace wsgi https://www.bortzmeyer.org/wsgi.html


request : http://blog.luisrei.com/articles/flaskrest.html
"""



from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template
from flask_api import FlaskAPI, status
#import json
import ipfshttpclient
from flask_fontawesome import FontAwesome
import http.client
import threading

# dependances
import GETdata
import GETresolver
import GETresume
import nameservice
import Talao_message
import createidentity
import constante
import Talao_backend_transaction
import Talao_token_transaction
import environment

# environment setup
mode=environment.currentMode('test', 'rinkeby')
w3=mode.initProvider()

# Flask setup	
app = FlaskAPI(__name__)
fa = FontAwesome(app)
app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"
tabcode = dict()

# thread
exporting_threads = {}

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
		for _ in range(10):
			time.sleep(1)
			self.progress += 10

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
	return GETresolver.getresolver(did,mode)		

# GETdata
@app.route('/talao/api/data/<data>', methods=['GET'])
def Data(data) :
	return GETdata.getdata(data,mode)
	
# GETresume Profil
@app.route('/talao/api/profil/<did>', methods=['GET'])
def Company_Profil(did) :
	return GETresume.getresume(did,mode)		

# GETresume	Resume
@app.route('/talao/api/resume/<did>', methods=['GET'])	
@app.route('/resume/<did>', methods=['GET'])
def User_Resume(did) :
	return GETresume.getresume(did,mode)		

# Nameservice
@app.route('/nameservice/api/reload/', methods=['GET'])
def GET_nameservice_reload() :
	nameservice.load_register_from_file(mode)
	return {"CODE" : "reload done"}

# upload des photos
@app.route('/uploads/<filename>')
def send_file(filename):
	UPLOAD_FOLDER='photos'
	return send_from_directory(UPLOAD_FOLDER, filename)

##################################################
# Saisie d un certificat pour entreprise
##################################################

@app.route('/certificate/experience/<did>', methods=['GET'])
def input_certificate(did):

	workspace_contract='0x'+did.split(':')[3]
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	profil =Talao_token_transaction.readProfil(address,mode)
	username=profil['givenName']+' '+profil['familyName']
	myresumelink='http://vault.talao.io:4011/visit/'+workspace_contract
	print(did)
	return render_template("certificaterequest.html",name=username, resumelink= myresumelink, myuser_did=did)

@app.route('/certificate/experience/', methods=['POST']) # pour la demo on ne gere pas le bearer token, on utilise les champs hidden pour cinserver la trace du user di et issuer did
def input_certificate_1():
	certificate=dict()
	key=request.form['key'] # c est le workspace contract de l issuer
	issuer_did='did:talao:'+mode.BLOCKCHAIN+':'+key[2:]
	secret=request.form['secret']
	userdid = request.form['user_did']
	workspace_contract='0x'+userdid.split(':')[3]
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	profil =Talao_token_transaction.readProfil(address,mode)
	
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
	username= certificate['firstname']+' '+certificate['name']
	mymessage ="Your professional certificate has been issued to "+ username+ '. An email has been sent too'
	print(certificate)
	# ajouter ADDcertificate ici
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
#   Talao Professional Identity API Explorer
#####################################################


@app.route('/resume/')
def resume_home() :
	return render_template("home_resume.html")
		
@app.route('/resume/did/', methods=['GET'])
def resume() :
	did = request.args['did']
	if Talao_token_transaction.isdid(did,mode) :
		truedid=did
	else :

		if nameservice.address(did.lower(),mode.register) != None :
			truedid='did:talao:'+mode.BLOCKCHAIN+':'+nameservice.address(did.lower(), mode.register)[2:]
		else :
			flash('Name/Email not found')
			return redirect (mode.server+'resume/')
	
	return GETresume.getresume(truedid,mode)	


	
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
	return render_template("home.html",message='')

### recuperation de l email, nom et prenom
@app.route('/talao/register/', methods=['POST'])
def POST_authentification_1() :
	global tabcode
	email = request.form['email']
	firstname=request.form['firstname']
	lastname=request.form['lastname']
	# stocké en session
	session['firstname']=request.form['firstname']
	session['lastname']=request.form['lastname']
	session['email']=email
	# check de l'email dans le backend
	check_backend=Talao_backend_transaction.canregister(email,mode) 
	if check_backend == False :
		return render_template("home.html", message = 'Email already in Backend')
	
	# envoi du code secret par email
	if tabcode.get(email) == None :
		code = get_random_bytes(3).hex()
		print('code secret = ', code)
		tabcode[email]=code
		# envoi message de control du code
		Talao_message.messageAuth(email, code)
		print('message envoyé à ', email)
	else :
		print("le code a deja ete envoye")
	
	return render_template("home2.html", message = '')

# recuperation du code saisi
@app.route('/talao/register/code/', methods=['POST'])
def POST_authentification_2() :
	global tabcode
	global exporting_threads
	email=session.get('email')
	lastname=session.get('lastname')
	firstname=session.get('firstname')
	mycode = request.form['mycode']
	print('code retourné = ', mycode)
	if mycode == tabcode[email] :
		print('code correct')
		thread_id = random.randint(0, 10000)
		exporting_threads[thread_id] = ExportingThread(firstname, lastname, email, mode)
		print("appel de createindentty")
		exporting_threads[thread_id].start()
		mymessage = 'Registation in progress........ You will receive an email with your Cryptographic keys to connect soon' 
	else :
		mymessage = 'Error code'
	
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
