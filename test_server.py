from flask import Flask, jsonify, session, send_from_directory
from flask import request, redirect, url_for
from flask_api import FlaskAPI
from Crypto.Random import get_random_bytes
import json

import GETdata
import GETresolver
import GETresume
import nameservice
import Talao_message
import createidentity
import constante
import Talao_backend_transaction
import environment
from flask_fontawesome import FontAwesome
from flask import render_template
# https://flask.palletsprojects.com/en/1.1.x/quickstart/

# SETUP
mode=environment.currentMode('test', 'rinkeby')
mode.print_mode()

app = FlaskAPI(__name__)
#app = Flask(__name__)
fa = FontAwesome(app)
app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"
tabcode = dict()


certificate={"firstname" : "Eric",
	"name" : "Planchais",
	"company" : {"name" : "Thales", "manager" : "Jean Charles", "managersignature" : "experingsignature.png",
		"companylogo" : "experinglogo.jpeg"},
	"startDate" : "2019-06-01",
	"endDate" :"2019-08-01",
	"summary" :  "Within the framework of an international consortium (Peugeot, Exagon, Quebec state), development of a new large-dimension hybrid vehicle SUV for the premium automotive segment. Technical, economic and human challenge with the setup of a new production plant in North America",
	"skills" : "Python3		Javascript		Debian",
	"position" : "Interim manager as CTO for hybrid SUV project",
	"score_recommendation" : 2,
	"score_delivery" : 3,
	"score_schedule" : 1,
	"score_communication" : 4}
	

		


#############################################################
#    affichage d'un certificat de type claim
#############################################################
@app.route('/certificate/')
def show_certificate():
	ok="color: rgb(251,211,5); font-size: 10px;"
	ko="color: rgb(0,0,0);font-size: 10px;"
	context=certificate.copy()
	context["manager"]=certificate["company"]["manager"]
	context["managersignature"]=certificate["company"]["managersignature"]
	context["companylogo"]=certificate["company"]["companylogo"]
	
	
	# gestion des star 
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
@app.route('/talao/resolver/api/<did>', methods=['GET'])
def DID_document(did) :
	return GETresolver.getresolver(did,mode)

# HTML
@app.route('/resolver/')
def DID_document_html() :
	return render_template("home_resolver.html")
@app.route('/resolver/did/', methods=['POST'])
def DID_document_html_1() :
	did = request.form['did']
	return GETresolver.getresolver(did,mode)

#####################################################
#   AUTRES API
#####################################################

@app.route('/talao/api/data/<data>', methods=['GET'])
def Data(data) :
	return GETdata.getdata(data, register,mode)

@app.route('/talao/api/resume/<did>', methods=['GET'])
def Resume_resolver(did) :
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
		#(address, eth_p, SECRET, workspace_contract,backend_Id, email, SECRET, AES_key) = createidentity.creationworkspacefromscratch(firstname, name, email)	
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
	
	if mode.env == 'production' :
		app.run(host = mode.IP, port= mode.port, debug=True)
	elif mode.env =='test' :
		app.run(debug=True)
	else :
		print("Erreur d'environnement")
