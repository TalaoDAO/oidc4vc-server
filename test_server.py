#import http.client, urllib.parse
from flask import Flask, jsonify
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

from flask import render_template

# https://flask.palletsprojects.com/en/1.1.x/quickstart/

app = FlaskAPI(__name__)
#app = Flask(__name__)

code = ""
email = ""

@app.route('/talao/api/<data>', methods=['GET'])
def Main(data) :
	return GETdata.getdata(data, register)

	
@app.route('/talao/api/resolver/<did>', methods=['GET'])
def DID_document(did) :
	return GETresolver.getresolver(did)

@app.route('/talao/api/data/<data>', methods=['GET'])
def Data(data) :
	return GETdata.getdata(data, register)

@app.route('/talao/api/resume/<did>', methods=['GET'])
def Resume(did) :
	return GETresume.getresume(did)


@app.route('/talao/talent_connect/<data>', methods=['GET'])
def talentconnect(data) :
	return GETdata.getdata(data, register)

#####################################################
#### Création d'une identité online##################
#####################################################

@app.route('/talao/auth/')
def authentification() :
	return render_template("home.html")

### recuperation de l email
@app.route('/talao/auth/', methods=['POST'])
def POST_authentification_1() :
	global email
	global code
	email = request.form['email']
	if register.get(email) != None :
		return  {'message' : 'Email deja utilisé'}
	code = get_random_bytes(3).hex()
	Talao_message.messageAuth(email, code)
	return render_template("home2.html")

# recuperation du code
@app.route('/talao/auth/code/', methods=['POST'])
def POST_authentification_2() :
	global email
	mycode = request.form['mycode']
	mycode = code  # a retirer ensuite
	if mycode == code :
		(address, eth_p, SECRET, workspace_contract,backend_Id, email, SECRET, AES_key) = createidentity.creationworkspacefromscratch("", "", email)	
		return { "address" : address, "did" : "did:talao:rinkeby:"+workspace_contract[2:], "authentification" : email }
	else :
		return { 'message' : 'Code incorect'}



#######################################################
#name service
#######################################################
@app.route('/talao/api/nameservice/<name>', methods=['GET'])
def GET_nameservice(name) :
	a= register.get(name)
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
register=nameservice.buildregister()


if __name__ == '__main__':
	#app.run(host = "192.168.0.34", port= 5000, debug=True)
    app.run(debug=True)
