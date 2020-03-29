"""
piur l authentication cf https://realpython.com/token-based-authentication-with-flask/

pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization

"""



from flask import Flask, jsonify, session, send_from_directory, flash, send_file
from flask import request, redirect, url_for
from flask_api import FlaskAPI, status
from Crypto.Random import get_random_bytes
import json
import ipfshttpclient
from flask_fontawesome import FontAwesome
from flask import render_template
import http.client, urllib.parse
import random
import threading
import time

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
# https://flask.palletsprojects.com/en/1.1.x/quickstart/

# environment setup
mode=environment.currentMode('test', 'rinkeby')
#mode.print_mode()
w3=mode.initProvider()

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

exporting_threads = {}

# Flask setup	
app = FlaskAPI(__name__)
#app = Flask(__name__)
fa = FontAwesome(app)
app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"
tabcode = dict()


#####################################################	
# read contenu du claim stocké sur IPFS
######################################################
def getclaimipfs (claim_id, workspace_contract) :
# @topicname est un str
# return un objet List

	
	# initialisation
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	claimdata=contract.functions.getClaim(claim_id).call()
	print("claimdata = ", claimdata)
	if claimdata[5]!="" :
		data=client.get_json(claimdata[5])
		return data
	else :
		return False
		
		
		
########################### API SERVER ###############################		


#####################################################
#   RESOLVER API
# retourne le DID Document d'un user
#####################################################
#curl http://127.0.0.1:5000/resolver/api/v0/PROJECT-ID \
#    -X POST \
#    -H "Content-Type: application/json" \
#    -d '{"did" : "mydid"}'

@app.route('/resolver/api/v0/<PROJECT_ID>', methods=['POST'])
def did_api(PROJECT_ID) :
	

	if PROJECT_ID !="sandbox" : 							# en attendant une liste des clients
		content = {'Not Authorized': 'nothing to see here'}
		return content, status.HTTP_401_UNAUTHORIZED
	
	else :	
		mydid=request.data.get('did')
		if GETresolver.getresolver(mydid, mode) == False :
			content = {'Bad did': 'nothing to see here'}
			return content, status.HTTP_204_NO_CONTENT
		
		else : 
			return GETresolver.getresolver(mydid,mode)


# autres API
@app.route('/resolver/api/<did>', methods=['GET'])
@app.route('/talao/resolver/api/<did>', methods=['GET'])
def DID_Document(did) :
	return GETresolver.getresolver(did,mode)		

	
#####################################################
#   DATA API
# retourne le contenu  d'une data
#####################################################
#curl http://127.0.0.1:5000/talao/data/api/v0/PROJECT-ID \
#    -X POST \
#    -H "Content-Type: application/json" \
#    -d '{"data" : "mydata"}'
#
# data = 'did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:b34c2a6837a9e89da5ef886d18763fb13a12615814d50a5b73ae403cb547d788'

@app.route('/talao/data/api/v0/<PROJECT_ID>', methods=['POST'])
def data_api(PROJECT_ID) :
	
	if PROJECT_ID !="sandbox" : 							# en attendant une liste des clients
		content = {'Not Authorized': 'nothing to see here'}
		return content, status.HTTP_401_UNAUTHORIZED
	
	else :	
		mydata=request.data.get('data')
	
		if GETdata.getdata(mydata, mode) == False :
			content = {'Bad data': 'nothing to see here'}
			return content, status.HTTP_204_NO_CONTENT
		
		else : 
			return GETdata.getdata(mydata,mode)


# autre API
@app.route('/talao/api/data/<data>', methods=['GET'])
def Data(data) :
	return GETdata.getdata(data,mode)


#####################################################
#    RESUME API
# retourne le resume d'un user à partir de son did 
#####################################################
#curl http://127.0.0.1:5000/talao/resume/api/v0/PROJECT-ID \
#    -X POST \
#    -H "Content-Type: application/json" \
#    -d '{"did" : "mydid"}'

@app.route('/talao/resume/api/v0/<PROJECT_ID>', methods=['POST'])
def resume_api(PROJECT_ID) :
	
	
	if PROJECT_ID !="sandbox" : 							# en attendant une liste des clients
		content = {'Not Authorized': 'nothing to see here'}
		return content, status.HTTP_401_UNAUTHORIZED
	
	else :	
		mydid=request.data.get('did')
		if GETresume.getresume(mydid, mode) == False :
			content = {'Bad did': 'nothing to see here'}
			return content, status.HTTP_204_NO_CONTENT
		
		else : 
			return GETresume.getresume(mydid,mode)
	

#####################################################
#    RESUME NAME API sans authentification
# retourne le resume d'un user à partir de son "nom" du nameservice
# exemple : un Talent laisse son id sur un site de recrutement
# l information accessible ne dispose pas de l email et du telephone
#####################################################
#curl http://127.0.0.1:5000/talao/resume_name/api/v0/PROJECT-ID \
#    -X POST \
#    -H "Content-Type: application/json" \
#    -d '{"name" : "myname"}'

@app.route('/talao/resume_name/api/v0/<PROJECT_ID>', methods=['POST'])
def resume_name_api(PROJECT_ID) :
	
	
	if PROJECT_ID !="sandbox" : 							# en attendant une liste des clients
		content = {'Not Authorized': 'nothing to see here'}
		return content, status.HTTP_401_UNAUTHORIZED
	
	else :	
		myname=request.data.get('name')
		print('myname =',myname)
		myaddress=nameservice.address(myname, mode.register)
		if myaddress == None :
			content = {'Bad name': 'nothing to see here'}
			return content, status.HTTP_204_NO_CONTENT
		else : 
			mydid="did:talao:"+mode.BLOCKCHAIN+":"+myaddress[2:]
			return GETresume.getresume(mydid,mode)

	

#####################################################
#    REQUEST PARNERSHIP
# mise en place d un partneship pour acceder a l information cryptee dont le tel et l email 
# 
# l information accessible ne dispose pas de l email et du telephone
#####################################################
#curl http://127.0.0.1:5000/talao/resume_name/api/v0/PROJECT-ID \
#    -X POST \
#    -H "Content-Type: application/json" \
#    -d '{"name" : "myname"}'
"""
le user laisse on did sur le site de recrutement
le site fait apel a l API pour recuperer son cv
le site demande la mise en place d 'un partenariat
	talao genere un request poyr partnership au talent
	talao envoie un email pour demander l accord au talent
	si oui le parnership est accepté


"""

#autre API pour API explorer
@app.route('/talao/api/profil/<did>', methods=['GET'])
def Company_Profil(did) :
	if Talao_token_transaction.isdid(did,mode) :
		return GETresume.getresume(did,mode)		
	else :
		return {"Erreur" : "False Did"}
	
@app.route('/talao/api/resume/<did>', methods=['GET'])	
@app.route('/resume/<did>', methods=['GET'])
def User_Resume(did) :
	if Talao_token_transaction.isdid(did,mode) :
		return GETresume.getresume(did,mode)		
	else :
		return {"Erreur" : "False Did"}



#######################################################
#   Name Service API
#######################################################
#curl http://127.0.0.1:5000/nameservice/api/v0/PROJECT-ID \
#    -X POST \
#    -H "Content-Type: application/json" \
#    -d '{"name" : "myname"}'

@app.route('/nameservice/api/v0/<PROJECT_ID>', methods=['POST'])
def nameservice_api(PROJECT_ID) :
	
	
	if PROJECT_ID !="sandbox" : 							# en attendant une liste des clients
		content = {'Not Authorized': 'nothing to see here'}
		return content, status.HTTP_401_UNAUTHORIZED
	
	else :	
		myname=request.data.get('name')
		print('myname =',myname)
		myaddress=nameservice.address(myname, mode.register)
		if myaddress == None :
			content = {'Bad name': 'nothing to see here'}
			return content, status.HTTP_204_NO_CONTENT
		
		else : 
			return {"did" : "did:talao:"+mode.BLOCKCHAIN+":"+myaddress[2:]}
	
"""
ne fonctionne pas "timepout"
@app.route('/nameservice/api/rebuild/', methods=['GET'])
def GET_nameservice_rebuild() :
	nameservice.buildregister(mode)
	return {"CODE" : "rebuild done"}
"""
	

@app.route('/nameservice/api/reload/', methods=['GET'])
def GET_nameservice_reload() :
	nameservice.load_register_from_file(mode)
	return {"CODE" : "reload done"}



############################### WEB SERVER ###########################		
		
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
	

	return render_template('certificate2.html', **context)

# upload des photos
@app.route('/uploads/<filename>')
def send_file(filename):
	UPLOAD_FOLDER='photos'
	return send_from_directory(UPLOAD_FOLDER, filename)



#####################################################
#   Talao Professional Identity API Explorer
#####################################################

# HTML
@app.route('/resume/')
def resume_home() :
	return render_template("home_resolver.html")
	
	
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
			return redirect (url_for('resume_home'))
	
	#return GETresume.getresume(truedid,mode)	
	# appel de l API
	print("appel de l api")
	conn = http.client.HTTPConnection(mode.flaskserver+':'+mode.port)
	headers = {'Accept': 'application/json','Content-type': 'application/json'}
	payload = { "did" : truedid}
	data = json.dumps(payload)
	conn.request('POST', '/talao/resume/api/v0/sandbox',data, headers)
	response = conn.getresponse()
	res=response.read()
	return json.loads(res)
	


	

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
	print("entre dans post_authentificate_2")
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
	return redirect(url_for('authentification'))



#######################################################
#   Name Service
#######################################################


# HTML name -> did
@app.route('/nameservice/')
def GET_nameservice_html() :
	return render_template("home_nameservice.html")

@app.route('/nameservice/name/', methods=['POST'])
def DID_nameservice_html_1() :
	name = request.form['name']
	a= nameservice.address(name,mode.register)
	if a == None :
		mymessage='Il n existe pas de did avec cet identifiant' 
	else :
		mymessage="did:talao:rinkeby:"+a[2:]
	return render_template("home_nameservice2.html", message = mymessage, name=name)

@app.route('/nameservice/name/', methods=['GET'])
def POST_nameservice_html_2() :
	return redirect(url_for('GET_nameservice_html'))


#######################################################
#                        MAIN, server launch
#######################################################
# setup du registre nameservice
print('initialisation du serveur')

if __name__ == '__main__':
	
	if mode.env == 'production' or mode.env == 'prod' :
		app.run(host = mode.flaskserver, port= mode.port, debug=True)
	elif mode.env =='test' :
		app.run(debug=True)
	else :
		print("Erreur d'environnement")
