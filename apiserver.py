"""
piur l authentication cf https://realpython.com/token-based-authentication-with-flask/

pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization

interace wsgi https://www.bortzmeyer.org/wsgi.html


request : http://blog.luisrei.com/articles/flaskrest.html
"""



from flask import Flask, jsonify, send_from_directory, flash, send_file,Response
from flask import request, redirect, url_for
from Crypto.Random import get_random_bytes
import json
import ipfshttpclient
from flask_fontawesome import FontAwesome
import http.client
import random
import threading
import csv

# dependances
import GETdata
import GETresolver
import GETresume
import ADDcertificate
import nameservice
import Talao_message
import createidentity
import constante
import Talao_backend_transaction
import Talao_token_transaction
import environment

# environment setup
mode=environment.currentMode('test', 'rinkeby')
#mode.print_mode()
w3=mode.initProvider()

# threading
exporting_threads = {}

# Flask setup	
app = Flask(__name__)
fa = FontAwesome(app)
app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"


#####################################################
#             tools
#####################################################

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


# pour la recuperation des certificats erc725
def getclaimipfs (claim_id, workspace_contract) :
# @topicname est un str
# return un objet List

	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	claimdata=contract.functions.getClaim(claim_id).call()

	if claimdata[5]!="" :
		data=client.get_json(claimdata[5])
		return data
	else :
		return False

#####################################################
#   Obtention d'un Bearer token 0AUTH
#####################################################
#
#
@app.route('/api/v0/token', methods=['GET'])
def auth() :
	key=request.json.get("key") # request.json parceque content type is application/json
	secret=request.json.get("secret")
	if key==None or secret==None :
		content=json.dumps({"msg" : "key and secret needed"}) # content est un json
		resp = Response(content, status=401, mimetype='application/json')
		return resp	
	fichiercsv=mode.BLOCKCHAIN+'_Talao_Identity.csv'
	csvfile = open(fichiercsv,newline='')
	reader = csv.DictReader(csvfile) 
	for row in reader:
		if row['workspace_contract'] == key and row['password'] == secret :
			name= row["name"]
			token=Talao_backend_transaction. encode_auth_token(key, 0, 5)
			csvfile.close()	
			content=json.dumps({"token" : token.hex(), 'name' : name}) # content est un json
			resp = Response(content, status=200, mimetype='application/json')
			return resp
	csvfile.close()
	content=json.dumps({"MSG" : "key or secret error"}) # content est un json
	resp = Response(content, status=401, mimetype='application/json')
	return resp

#####################################################
#   emission d'un certificat d experience ERC725
#####################################################
# curl http://127.0.0.1:3000/certificate/api/v0  -X POST -H "Content-Type: application/json, Authorization : Bearer token" -d 'certificate'
# prevoir l envoie d un message avce le lien

@app.route('/certificate/api/v0', methods=['POST'])
def issueCertificate() :  
	
	# valider la request
	if request.method != 'POST':
		content=json.dumps({"msg" : "bad request"}) # content est un json
		resp = Response(content, status=401, mimetype='application/json')
		return resp		
	auth = request.headers.get("Authorization")
	if auth == None :
		content=json.dumps({"msg" : "authorization_header_missing"}) # content est un json
		resp = Response(content, status=401, mimetype='application/json')
		return resp		       
	parts = auth.split()
	if parts[0].lower() != 'bearer':
		content=json.dumps({"msg" : "invalid_heade description Authorization header must start with Bearer"}) # content est un json
		resp = Response(content, status=401, mimetype='application/json')
		return resp		
	elif len(parts) == 1:
		content=json.dumps({"msg" : "token not found"}) # content est un json
		resp = Response(content, status=401, mimetype='application/json')
		return resp			
	elif len(parts) > 2:
		content=json.dumps({"msg" : "Authorization header must be Bearer token"}) # content est un json
		resp = Response(content, status=401, mimetype='application/json')
		return resp	  

	token = parts[1]	
	certificate=request.json
			
	# verifier la validité du bearer token
	userid, code, msg =Talao_backend_transaction.decode_auth_token(bytes.fromhex(token))
	if userid==False :
		content=json.dumps({"msg" : msg}) # content est un json
		resp = Response(content, status=code, mimetype='application/json')
		return resp		
		
	# valider le user
	did_user = certificate.get('did_user')	
	if did_user == None :
		content=json.dumps({"msg" : "user not defined in the certificate"}) # content est un json
		resp = Response(content, status=400, mimetype='application/json')
		return resp		
	if not Talao_token_transaction.isdid(did_user,mode) :
		content=json.dumps({"msg" : "invalid did for user"}) # content est un json
		resp = Response(content, status=401, mimetype='application/json')
		return resp			
	workspace_contract_to = '0x'+did_user.split(':')[3]	

	# valider l issuer
	did_issuer = certificate.get('did_issuer')
	
	if did_issuer == None :
		content=json.dumps({"msg" : "no did for issuer"}) # content est un json
		resp = Response(content, status=401, mimetype='application/json')
		return resp	
	if not Talao_token_transaction.isdid(did_issuer,mode) :
		content=json.dumps({"msg" : "invalid did for issuer"}) # content est un json
		resp = Response(content, status=401, mimetype='application/json')
		return resp		
	workspace_contract_from ='0x'+did_issuer.split(':')[3]	
	fichiercsv=mode.BLOCKCHAIN+'_Talao_Identity.csv'
	csvfile = open(fichiercsv,newline='')
	reader = csv.DictReader(csvfile) 
	search = False
	for row in reader :
		if row['workspace_contract'] == workspace_contract_from :
			name= row.get('name')
			address_from=row.get('ethereum_address')
			private_key_from=row.get('private_key')
			search = True
	csvfile.close()
	if search == False :
		content=json.dumps({"msg" : user+" has no professional identity"}) # content est un json
		resp = Response(content, status=400, mimetype='application/json')
		return resp			
		
	# emission du certificat	
	resultat, link = ADDcertificate.addcertificate(address_from, private_key_from, workspace_contract_to, certificate,mode)
	code = 200
	if resultat == False :
		code = 401
		link = "Error, no certificate created"
	content=json.dumps({"link" : link}) # content est un json
	resp = Response(content, status=code, mimetype='application/json')
	return resp	
	

#####################################################
#   RESOLVER API
# retourne le DID Document d'un user
#####################################################
#curl http://127.0.0.1:3000/resolver/api/v0  -X GET -H "Content-Type: application/json" -d '{"did" : "mydid"}'
#
@app.route('/resolver/api/v0', methods=['GET'])
def did_api() :	
		mydid=request.json.get('did')
		if mydid == None :
			content=json.dumps({"msg" : "no did"}) # content est un json
			resp = Response(content, status=401, mimetype='application/json')
			return resp	

		if not Talao_token_transaction.isdid(mydid,mode) :
			content=json.dumps({"msg" : "invalid did"}) # content est un json
			resp = Response(content, status=401, mimetype='application/json')
			return resp			

		if GETresolver.getresolver(mydid, mode) == False :
			content=json.dumps({"msg" : "invalid did"}) # content est un json
			resp = Response(content, status=401, mimetype='application/json')
			return resp	
		else : 
			did_document=GETresolver.getresolver(mydid,mode)
			content=json.dumps(did_document) # content est un json
			resp = Response(content, status=200, mimetype='application/json')
			return resp		

	
#####################################################
#   DATA API
# retourne le contenu  d'une data publique
#####################################################
#curl http://127.0.0.1:3000/talao/data/api/v0  -X GET -H "Content-Type: application/json" -d '{"data" : "mydata"}'
#
# data = 'did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:b34c2a6837a9e89da5ef886d18763fb13a12615814d50a5b73ae403cb547d788'

@app.route('/talao/data/api/v0', methods=['GET'])
def data_api() :
		mydata=request.json.get('data')
		if mydata == None :
			content=json.dumps({"msg" : "JSON has no data"}) # content est un json
			resp = Response(content, status=401, mimetype='application/json')
			return resp
		
		if len(mydata.split(':'))<4 :
			content=json.dumps({"msg" : "did incorrect"}) # content est un json
			resp = Response(content, status=401, mimetype='application/json')
			return resp	
			
		if GETdata.getdata(mydata, mode) == False :
			content=json.dumps({"msg" : "no data"}) # content est un json
			resp = Response(content, status=401, mimetype='application/json')
			return resp				
		else : 
			data = GETdata.getdata(mydata,mode)
			content=json.dumps(data) # content est un json
			resp = Response(content, status=200, mimetype='application/json')
			return resp	


#####################################################
#    RESUME API
# retourne le resume d'un user à partir de son did 
#####################################################
#curl http://127.0.0.1:3000/resume/api/v0  -X GET -H "Content-Type: application/json" -d '{"did" : "mydid"}'

@app.route('/resume/api/v0', methods=['GET'])
def resume_api() :
	
		mydid=request.json.get('did')
		
		if mydid == None :
			content=json.dumps({"msg" : "no did"}) # content est un json
			resp = Response(content, status=401, mimetype='application/json')
			return resp	

		if not Talao_token_transaction.isdid(mydid,mode) :
			content=json.dumps({"msg" : "invalid did"}) # content est un json
			resp = Response(content, status=401, mimetype='application/json')
			return resp	
			
		if GETresume.getresume(mydid, mode) == False :
			content=json.dumps({"msg" : "did incorrect"}) # content est un json
			resp = Response(content, status=401, mimetype='application/json')
			return resp			
		
		else : 
			resume = GETresume.getresume(mydid,mode)
			content=json.dumps(resume) # content est un json
			resp = Response(content, status=200, mimetype='application/json')
			return resp	
		
#####################################################
#    RESUME NAME API sans authentification
# retourne le resume d'un user à partir de son "nom" du nameservice
# exemple : un Talent laisse son id sur un site de recrutement
# l information accessible ne dispose pas de l email et du telephone
#####################################################
# curl http://127.0.0.1:3000/resume_by_name/api/v0  -X GET -H "Content-Type: application/json" -d '{"name" : "myname"}'

@app.route('/resume_by_name/api/v0', methods=['GET'])
def resume_name_api() :
	
	myname=request.json.get('name')
	myaddress=nameservice.address(myname, mode.register)
	if myaddress == None :
		content=json.dumps({"msg" : "name not found"}) # content est un json
		resp = Response(content, status=401, mimetype='application/json')
		return resp	
	else : 
		mydid="did:talao:"+mode.BLOCKCHAIN+":"+myaddress[2:]
		resume = GETresume.getresume(mydid,mode)
		content=json.dumps(resume) # content est un json
		resp = Response(content, status=200, mimetype='application/json')
		return resp		

#####################################################
#    REQUEST PARTNERSHIP
# mise en place d un partneship pour acceder a l information cryptee dont le tel et l email 
# 
# l information accessible ne dispose pas de l email et du telephone
#####################################################

"""
le user laisse on did sur le site de recrutement
le site fait apel a l API pour recuperer son cv
le site demande la mise en place d 'un partenariat
	talao genere un request poyr partnership au talent
	talao envoie un email pour demander l accord au talent
	si oui le parnership est accepté


"""


#######################################################
#   Name Service API
#######################################################
# curl http://127.0.0.1:3000/nameservice/api/v0  -X GET -H "Content-Type: application/json" -d '{"name" : "myname"}'

@app.route('/nameservice/api/v0', methods=['GET'])
def nameservice_api() :
		
	myname=request.json.get('name')
	myaddress=nameservice.address(myname, mode.register)
	if myaddress == None :
		content=json.dumps({"msg" : "name not found"}) # content est un json
		resp = Response(content, status=400, mimetype='application/json')
		return resp			
	else : 
		content=json.dumps({"did" : "did:talao:"+mode.BLOCKCHAIN+":"+myaddress[2:]}) # content est un json
		resp = Response(content, status=200, mimetype='application/json')
		return resp		


#######################################################
#                        MAIN, server launch
#######################################################
# setup du registre nameservice
print('initialisation du serveur')


if __name__ == '__main__':
	
	if mode.env == 'production' or mode.env == 'prod' :
		app.run(host = mode.flaskserver, port= mode.port, debug=True)
	elif mode.env =='test' :
		app.run(host=mode.flaskserver, port =mode.apiport, debug=True)
	else :
		print("Erreur d'environnement")

