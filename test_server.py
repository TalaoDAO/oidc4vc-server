from flask import Flask, jsonify, session, send_from_directory, flash
from flask import request, redirect, url_for
from flask_api import FlaskAPI
from Crypto.Random import get_random_bytes
import json
import ipfshttpclient
from flask_fontawesome import FontAwesome
from flask import render_template

import GETdata
import GETresolver
import GETresume
import nameservice
import Talao_message
import createidentity
import constante
import Talao_backend_transaction
import environment
# https://flask.palletsprojects.com/en/1.1.x/quickstart/

# SETUP
mode=environment.currentMode('test', 'rinkeby')
#mode.print_mode()
w3=mode.initProvider()
	
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
	print(claimdata)
	if claimdata[5]!="" :
		data=client.get_json(claimdata[5])
		return data
	else :
		return False
		
#############################################################
#    affichage d'un certificat de type claim
#############################################################
#data='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:b34c2a6837a9e89da5ef886d18763fb13a12615814d50a5b73ae403cb547d788'


@app.route('/certificate/<data>', methods=['GET'])
def show_certificate(data):
	
	claimId=data.split(':')[5]
	print(claimId)
	workspace_contract= '0x'+data.split(':')[3]
	print(workspace_contract)
	certificate=getclaimipfs(claimId, workspace_contract)
	
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
	print(json.dumps(context))

	return render_template('certificate.html', **context)

# upload des photos
@app.route('/uploads/<filename>')
def send_file(filename):
	UPLOAD_FOLDER='photos'
	return send_from_directory(UPLOAD_FOLDER, filename)



######################################################
@app.route('/talao/api/<data>', methods=['GET'])
def Main(data) :
	return GETdata.getdata(data, register,mode)

#####################################################
#   RESOLVER
#####################################################

# API
@app.route('/resolver/api/<did>', methods=['GET'])
@app.route('/talao/resolver/api/<did>', methods=['GET'])
def DID_Document(did) :
	return GETresolver.getresolver(did,mode)

#####################################################
#   Talao Professional Identity Explorer
#####################################################

# HTML
@app.route('/resume/')
def resume_home() :
	return render_template("home_resolver.html")
	
	
@app.route('/resume/did/', methods=['GET'])
def resume() :
	did = request.args['did']
	print(did)
	if did[:3] == 'did' :
		truedid=did
	else :
		print('nameservice = ', nameservice.address(did,register))
		if nameservice.address(did,register) != None :
			truedid='did:talao:'+mode.BLOCKCHAIN+':'+nameservice.address(did, register)[2:]
		else :
			flash('Identifier not found')
			return redirect (url_for('resume_home'))
	
	return GETresume.getresume(truedid,mode)	

	
	
#####################################################
#   AUTRES API
#####################################################

@app.route('/talao/api/data/<data>', methods=['GET'])
def Data(data) :
	return GETdata.getdata(data, register,mode)

"""
@app.route('/talao/api/resume/<did>', methods=['GET'])
def Resume_resolver(did) :
	return redirect(url_for('Resume'))
"""	

@app.route('/talao/api/profil/<did>', methods=['GET'])
def Company_Profil(did) :
	return GETresume.getresume(did, mode)
	
@app.route('/talao/api/resume/<did>', methods=['GET'])	
@app.route('/resume/<did>', methods=['GET'])
def User_Resume(did) :
	return GETresume.getresume(did,mode)
	

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
	#print('name = ', request.args['name'])
	return render_template("home.html",message='')

### recuperation de l email
@app.route('/talao/register/', methods=['POST'])
def POST_authentification_1() :
	global tabcode
	
	# verification de l email dans le backend
	email = request.form['email']
	print('email =' ,email)
	firstname=request.form['firstname']
	lastname=request.form['lastname']
	session['firstname']=request.form['firstname']
	session['lastname']=request.form['lastname']
	session['email']=email
	check_backend=Talao_backend_transaction.canregister(email,mode)
	print('check backend =',check_backend) 
	if check_backend == False :
		return render_template("home.html", message = 'Email already in Backend')
	
	# envoi du code secret par email
	code = get_random_bytes(3).hex()
	print('code secret = ', code)
	tabcode[email]=code
		
	# envoi message de control du code
	Talao_message.messageAuth(email, code)
	print('message envoyé à ', email)
	print('name = ', request.form['lastname'])
	print('firstname =', request.form['firstname'])

	return render_template("home2.html", message = '')

# recuperation du code saisi
@app.route('/talao/register/code/', methods=['POST'])
def POST_authentification_2() :
	email=session.get('email')
	lastname=session.get('lastname')
	firstname=session.get('firstname')
	mycode = request.form['mycode']
	print(firstname, '  ', lastname, '   ', email)
	print('code retourné = ', mycode)
	if mycode == tabcode[email] :
		print('appel de createidentity avec firtsname = ', firstname, ' name = ', lastname, ' email = ', email)
		(address, eth_p, SECRET, workspace_contract,backend_Id, email, SECRET, AES_key) = createidentity.creationworkspacefromscratch(firstname, name, email,mode)	
		mymessage = 'Your professional Identity will be available within a couple of minutes. You will receive your Cryptographic keyys to connect through my.Freedapp http://vault.talao.io:4011/' 
	else :
		mymessage = 'Error code'
	return render_template("home3.html", message = mymessage)

@app.route('/talao/register/code/', methods=['GET'])
def POST_authentification_3() :
	return redirect(url_for('authentification'))


#######################################################
#   Name Service
#######################################################

# API
@app.route('/nameservice/api/<name>', methods=['GET'])
def GET_nameservice(name) :
	a= nameservice.address(name,mode)
	if a== None :
		return {"CODE" : "601"}
	else :
		return {"did" : "did:talao:rinkeby:"+a[2:]}

@app.route('/nameservice/api/reload/', methods=['GET'])
def GET_nameservice_reload() :
	nameservice.buildregister(mode)
	return {"CODE" : "reload done"}


# HTML name -> did
@app.route('/nameservice/')
def GET_nameservice_html() :
	return render_template("home_nameservice.html")

@app.route('/nameservice/name/', methods=['POST'])
def DID_nameservice_html_1() :
	name = request.form['name']
	a= nameservice.address(name,register)
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
print('chargement du registre')
register=nameservice.readregister(mode)
print('initialisation du serveur')

if __name__ == '__main__':
	
	if mode.env == 'production' or mode.env == 'prod' :
		app.run(host = mode.flaskserver, port= mode.port, debug=True)
	elif mode.env =='test' :
		app.run(debug=True)
	else :
		print("Erreur d'environnement")
