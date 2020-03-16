
from web3.auto import w3
import constante
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import Talao_token_transaction
import csv
import http.client, urllib.parse
import json
import sys
import datetime
import jwt

#from urllib.parse import urlencode



###################################################################
# creation du freelance sur le back end
###################################################################

def backend_register (eth_a, workspace, first_name, last_name, email, password,mode) :
	
	w3=mode.initProvider()

	conn = http.client.HTTPConnection(mode.ISSUER)
	if mode.BLOCKCHAIN == 'ethereum' :
		conn = http.client.HTTPSConnection(mode.ISSUER)
	headers = {'Accept': 'application/json','Content-type': 'application/json'}
	payload = {"user": { "ethereum_account": eth_a , "ethereum_contract": workspace ,"first_name" : first_name ,"last_name" : last_name ,"email" : email ,"password" : password}}
	data = json.dumps(payload)
	conn.request('POST', '/register',data, headers)
	response = conn.getresponse()

	res=response.read()
	a= json.loads(res)
	return a['user']['id']


###################################################################
#  verifier si l email existe deja sur le back end 
# le password est celui qui fonctionne sur le back end
###################################################################

def canregister(email) :

	w3=mode.initProvider()

	conn = http.client.HTTPConnection(mode.ISSUER)
	if mode.BLOCKCHAIN == 'ethereum' :
		conn = http.client.HTTPSConnection(mode.ISSUER)
	headers = {'Accept': 'application/json','Content-type': 'application/json'}
	payload = {'user':{'email': email }}
	data = json.dumps(payload)
	conn.request('POST', '/user_available_email',data, headers)
	response = conn.getresponse()
	res=response.read()
	return json.loads(res)['available']



###################################################################
# login sur le back end
###################################################################

def login (email, password,mode) :

	w3=mode.initProvider()

	conn = http.client.HTTPConnection(mode.ISSUER)
	if mode.BLOCKCHAIN == 'ethereum' :
		conn = http.client.HTTPSConnection(mode.ISSUER)
	headers = {'Accept': 'application/json','Content-type': 'application/json'}
	payload = {"email" : email ,"password" : password}
	data = json.dumps(payload)
	conn.request('POST', '/login',data, headers)
	response = conn.getresponse()
	res=response.read()
	return json.loads(res)['token']



###################################################################
# creation d une experience sur le backend
###################################################################

def createExperience (email, password, experience) :

	w3=mode.initProvider()

	token=login(email, password,mode)
	
	conn = http.client.HTTPConnection(mode.ISSUER)
	if mode.BLOCKCHAIN == 'ethereum' :
		conn = http.client.HTTPSConnection(mode.ISSUER)
		
	headers = {'Accept': 'application/json','Content-type': 'application/json',  'Authorization':'Bearer '+token}
	payload = experience
# JSON => { 'experience':{'title': 'Nouveau Test depuis Talaogen', 'description': 'Nouvelle Aucune', 'from': '2002-02-02', 'to': '2003-02-02', 'location': '', 'remote': True, 'organization_name': 'Talao','skills': [] }}
	data = json.dumps(payload)
	conn.request('POST', '/experiences',data, headers)

	response= conn.getresponse()
	print(response.status, response.reason)
	res=response.read()
	#print(json.loads(res))	
	conn.close()
	return


###################################################################
# creation d un skill sur le backend
###################################################################
# retourne un dict

def createSkill (email, password, skillname, mode) :

	w3=mode.initProvider()

	token=login(email, password,mode)
	conn = http.client.HTTPConnection(mode.ISSUER)
	if mode.BLOCKCHAIN == 'ethereum' :
		conn = http.client.HTTPSConnection(mode.ISSUER)
	headers = {'Accept': 'application/json','Content-type': 'application/json',  'Authorization':'Bearer '+token}
	payload = {"skill": {"name": skillname}}
	data = json.dumps(payload)
	conn.request('POST', '/skills',data, headers)
	response= conn.getresponse()
	res=response.read()
	conn.close()
	a=json.loads(res)
	if "err" in a :
		a= {"skill"  : "ERROR"} # cf guillaume pour trouver la cause
	return a["skill"]
	
	

###################################################################
# recuperation d'un skill 
###################################################################
# retourne un dict

def getSkill (email, password, skillname, mode) :
	w3=mode.initProvider()

	token=login(email, password,mode)
	conn = http.client.HTTPConnection(mode.ISSUER)
	if mode.BLOCKCHAIN == 'ethereum' :
		conn = http.client.HTTPSConnection(mode.ISSUER)
	headers = {'Accept': 'application/json','Content-type': 'application/json',  'Authorization':'Bearer '+token}
	payload = {}
	data = json.dumps(payload)
	conn.request('GET', '/skills',data, headers)
	response= conn.getresponse()
	res=response.read()
	conn.close()
	skillarray=json.loads(res)["skills"]	
	for i in range (0, len(skillarray)) :
		if skillarray[i]["name"].lower()==skillname.lower() :
			return skillarray[i]
	return createSkill(email, password, skillname, mode)		


###################################################################
#  Get d une experience sur le backend
###################################################################

def getExperience (email, password,experience, mode) :

	w3=mode.initProvider()

	token=login(email, password,mode)
	headers = {'Accept': 'application/json','Content-type': 'application/json',  'Authorization':'Bearer '+token}
	payload = {"Id" : experience }
	data = json.dumps(payload)
	conn.request('GET', '/experiences',data, headers)
	response= conn.getresponse()
	res=response.read()
	return json.loads(res)


###################################################################
#  Bearer Token 
###################################################################

def encode_auth_token(user_id,mode):
	w3=mode.initProvider()

	try:
		payload = {'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=5),'iat': datetime.datetime.utcnow(),'sub': user_id}
		return jwt.encode(
            payload,
            'TALAO',
            algorithm='HS256')
	except Exception as e:
		return e

def decode_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token,'TALAO')
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'




