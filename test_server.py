#import http.client, urllib.parse
from flask import Flask, jsonify, session
from flask import request
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

from flask import render_template

# https://flask.palletsprojects.com/en/1.1.x/quickstart/

app = FlaskAPI(__name__)
#app = Flask(__name__)
app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"
tabcode = dict()






@app.route('/talao/api/<data>', methods=['GET'])
def Main(data) :
	return GETdata.getdata(data, register)

#####################################################
#   RESOLVER
#####################################################

# API
@app.route('/talao/api/resolver/<did>', methods=['GET'])
def DID_document(did) :
	return GETresolver.getresolver(did)

# version html
@app.route('/resolver/')
def DID_document_html() :
	return render_template("home_resolver.html")
@app.route('/resolver/did/', methods=['POST'])
def DID_document_html_1() :
	did = request.form['did']
	return GETresolver.getresolver(did)

#####################################################
#   AUTRES API
#####################################################


@app.route('/talao/api/data/<data>', methods=['GET'])
def Data(data) :
	return GETdata.getdata(data, register)

@app.route('/talao/api/resume/<did>', methods=['GET'])
def Resume_resolver(did) :
	return GETresume.getresume(did)

#####################################################
#   Talent Connect
#####################################################
# @data = did

# API
@app.route('/talent_connect/api/<data>', methods=['GET'])
def talentconnect(data) :
	return GETdata.getdata(data, register)

#####################################################
#   CREATION IDENTITE ONLINE (html) pour le site talao.io
#####################################################
"""
le user reçoit par email les informations concernant son identité
Talao dispose d'une copie de la clé
"""

@app.route('/talao/auth/')
def authentification() :
	return render_template("home.html")

### recuperation de l email
@app.route('/talao/auth/', methods=['POST'])
def POST_authentification_1() :
	global tabcode
	email = request.form['email']
	if register.get(email) != None :
		return  {'message' : 'Email deja utilisé'}
	code = get_random_bytes(3).hex()
	tabcode[email]=code
	session['email']=email
	Talao_message.messageAuth(email, code)
	return render_template("home2.html")

# recuperation du code
@app.route('/talao/auth/code/', methods=['POST'])
def POST_authentification_2() :
	email=session.get('email')
	mycode = request.form['mycode']
	if mycode == tabcode[email] :
		#(address, eth_p, SECRET, workspace_contract,backend_Id, email, SECRET, AES_key) = createidentity.creationworkspacefromscratch("", "", email)	
		return { 'code juste' : tabcode[email] }
	else :
		return { 'ERROR' : 'false code'}



#######################################################
#name service
#######################################################

# API
@app.route('/nameservice/api/<name>', methods=['GET'])
def GET_nameservice(name) :
	a= nameservice.address(name)
	if a== None :
		return {"ERR" : "601"}
	else :
		return {"did" : "did:talao:rinkeby:"+a[2:]}

@app.route('/nameservice/api/reload/', methods=['GET'])
def GET_nameservice_reload() :
	nameservice.buildregister()
	return "relaod done"


# version html 
@app.route('/nameservice/')
def GET_nameservice_html() :
	return render_template("home_nameservice.html")
@app.route('/nameservice/name/', methods=['POST'])
def DID_nameservice_html_1() :
	name = request.form['name']
	a= nameservice.address(name,register)
	if a == None :
		return {'Il n existe pas de did avec cet identifiant' :0}
	else :
		return {"did" : "did:talao:rinkeby:"+a[2:]}



	
"""
from flask import Flask
from flask import request
from flask import render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/', methods=['POST'])
def text_box():
    text = request.form['text']
    processed_text = text.upper()
    return render_template("bienvenue.html" , message = processed_text )

if __name__ == '__main__':
    app.run()


@app.route('/api/v1.0/profil', methods=['GET'])
def get_profil():
	address=request.data.get("address")
	return jsonify(Talao_token_transaction.readProfil(address))

@app.route('/api/v1.0/experience', methods=['GET'])
def get_experience():
	address=request.data.get("address")	
	index=Talao_token_transaction.getDocumentIndex(address, 50000)
	return jsonify(Talao_token_transaction.getDocument(address,50000, index-1))

@app.route('/api/v1.0/diploma', methods=['GET'])
def get_diploma():
	address=request.data.get("address")
	index=Talao_token_transaction.getDocumentIndex(address, 40000)
	return jsonify(Talao_token_transaction.getDocument(address,40000, index-1))

@app.route('/api/v1.0/skill', methods=['GET'])
def get_skill():
	address=request.data.get("address")
	index=Talao_token_transaction.getDocumentIndex(address, 50000)
	i=0
	_skills=[]
	while i < index :
		_skills.extend(Talao_token_transaction.getDocument(address,50000, i)['certificate']['skills'])
		i=i+1
	return jsonify({'skills': _skills})
"""

# setup du registre nameservice
print('debut de la creation du registre')
register={"pierre" : "0x4"}
#register=nameservice.buildregister()
print('initialisation du serveur')

if __name__ == '__main__':
	#app.run(host = "192.168.0.34", port= 5000, debug=True)
    app.run(debug=True)
