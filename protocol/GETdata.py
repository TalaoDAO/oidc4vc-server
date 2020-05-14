import ipfshttpclient
from eth_account.messages import encode_defunct
import json
import datetime
import sys
from datetime import datetime
#dependances
import isolanguage
import Talao_ipfs
import constante
import constante

from .ADDdocument import getdocument

##############################################
# detrmination de la nature de l addresse
##############################################
# @thisaddress, address
# return dictionnaire

def whatisthisaddress(thisaddress,mode) :

	w3=mode.w3

	# est ce une addresse Ethereum ?
	if w3.isAddress(thisaddress) == False :
		category = False
		owner = None
		workspace= None	
	else :
		
		# test sur la nature de thisaddress
		contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
		address = contract.functions.contractsToOwners(thisaddress).call()
		workspace=contract.functions.ownersToContracts(thisaddress).call()
		
		# thisaddress est un owner
		if address == '0x0000000000000000000000000000000000000000' and workspace != '0x0000000000000000000000000000000000000000' :
			category = "owner"
			owner = thisaddress
			workspace=workspace
			
		# thisaddress est un workspace
		if address != '0x0000000000000000000000000000000000000000' and workspace == '0x0000000000000000000000000000000000000000' :
			category = 'workspace'
			owner=address
			workspace=thisaddress
		
		# thisaddressn est une addresse ethereum standard
		if address == '0x0000000000000000000000000000000000000000' and workspace == '0x0000000000000000000000000000000000000000' :
			category = 'unknown'
			owner = None
			workspace = None
			
	return {"type" : category, "owner" : owner, 'workspace' : workspace}




#########################################################################################
# return profil comme dictionnaire {'givenName' ; 'Jean', 'familyName' ; 'Pascal'.....
###########################################################################################
# return un couple (dict dictionaire,int category)
# ATTENTION on retire l email du profil pour individual

def readProfil (address, workspace_contract, mode) :

	w3 = mode.w3

	# setup constante
	givenName = 103105118101110078097109101 # = firstname
	familyName = 102097109105108121078097109101 # = lastname
	jobTitle = 106111098084105116108101
	worksFor = 119111114107115070111114
	workLocation = 119111114107076111099097116105111110
	url = 117114108
	email = 101109097105108
	description = 100101115099114105112116105111110
	SIRET = 83073082069084	
	adresse = 97100100114101115115
	contact = 99111110116097099116

	# initialisation de la reponse
	profil = dict()
		
	# determination de la category
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	category = contract.functions.identityInformation().call()[1]	
	
	# si profil d un individu, on retire email
	if category == 1001 : 
		topicvalue = [givenName, familyName, jobTitle, worksFor, workLocation, url,  description]
		topicname = ['firstname', 'lastname', 'jobtitle', 'company', 'location', 'url', 'description']
		for i in range (0, len(topicvalue)) :
			claim = contract.functions.getClaimIdsByTopic(topicvalue[i]).call()
			if len(claim) != 0 :
				claimId = claim[0].hex()
				data = contract.functions.getClaim(claimId).call()
				if data[4].decode('utf-8') == "" or data[4].decode('utf-8')==" " :
					profil[topicname[i]] = None
				else :
					profil[topicname[i]] = data[4].decode('utf-8')			
			else :
				profil[topicname[i]] = None		
	
	# si profil d'une company
	else :
		topicvalue = [givenName,url,email,contact, adresse]
		topicname = ['name', 'website', 'email', 'contact','address']
		for i in range (0, len(topicvalue)) :
			claim = contract.functions.getClaimIdsByTopic(topicvalue[i]).call()
			if len(claim) != 0 :
				claimId = claim[0].hex()
				data = contract.functions.getClaim(claimId).call()
				if data[4].decode('utf-8') == "" or data[4].decode('utf-8')==" " :
					profil[topicname[i]] = None
				else :
					profil[topicname[i]] = data[4].decode('utf-8')										
			else :
				profil[topicname[i]] = None			
	
	return profil,category 

#####################################################	
# read Talao document
######################################################
# @index : int, identifiant du document
# return dictionnaire


def getdoc(index, workspace_contract,mode) :
	
	w3 = mode.w3
	document = dict()
	
	# determination de l addresse du workspace
	contract = w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	
	# calcul du did
	did = "did:talao:" + mode.BLOCKCHAIN + ":" + workspace_contract[2:]		
	
	# download du doc
	contract = w3.eth.contract(workspace_contract,abi = constante.workspace_ABI)

	try :
		doc = contract.functions.getDocument(index).call()
	except :
		return False
	
	
	# topic
	if doc[0] == 60000 or doc[0] == 50000 :
		topic = "experience"
	elif doc[0] == 40000 :
		topic = "education"
	elif doc[0] == 10000 :
		topic ="employability"
	elif doc[0] == 15000 :
		topic ="contact"	
	else :
		topic = "unknown"

	# value
	if topic == "education" :
		ipfs_hash=doc[6].decode('utf-8')
		education=Talao_ipfs.IPFS_get(ipfs_hash)	
		value = {"organization" : { 'name' :education["issuer"]["organization"]["name"],
									'contact_name' : "Unknown",
									'contact_email' : "Unknown"},
				"to" : education["diploma"]["to"], 
				"from" : education["diploma"]["from"],
				"title" : education["diploma"]["title"],
				'skilss' : "Unknown",
				"description" : education["diploma"]["description"],
				"certificate_link" : education["diploma"]["link"]}
	
	
	elif topic == "experience" :
		ipfs_hash=doc[6].decode('utf-8')
		experience=Talao_ipfs.IPFS_get(ipfs_hash)
		value = {'position' : experience['certificate']['title'],
				'summary' : experience['certificate']['description'],
				'startDate' : experience['certificate']['from'],
				'endDate' : experience['certificate']['to'],
				'company' : {"name" : "Unknown", 
								"manager" : experience['issuer']['responsible']["name"],
								"manager_email" : experience["issuer"]["organization"]["email"]},
				'skills' : "Unknown",
				"certificate_link" : "No"	}
	
	elif topic == 'contact' :
		""" getdocument avec data cryptee  """
		value = getdocument(workspace_contract, '0x0', workspace_contract, index, mode)
	
	else :
		topic = "unknown"
		value = {}
		
	# issuer
	issuer = doc[3]
			
	# determination du profil de l issuer
	(issuerprofile, identityinformation) = readProfil(whatisthisaddress(issuer,mode)["owner"], whatisthisaddress(issuer,mode)["workspace"],mode)	
	if identityinformation == 1001 :
		category="person"
		path="resume"
	else :
		category = "company"	
		path = "profil"

	# calcul de la date
	if doc[2] == 0 :
		date = 'Unlimited'
	else :			
		date=datetime.fromtimestamp(doc[2]).strftime("%y/%m/%d")
	if doc[7]== False :
		encrypted = 'Public'
	else :
		encrypted = 'Private'	
		
	# mise en forme de la reponse globale		
	document["id"]="did:talao:rinkeby:"+workspace_contract[2:]+":document:"+str(index)
	document['endpoint']=mode.server+'talao/api/data/'+document['id']
	document['data'] = {"issuer" : {'id' : "did:talao:rinkeby:"+whatisthisaddress(issuer,mode)["workspace"][2:],
									'endpoint' : mode.server+'talao/'+path+'/did:talao:'+mode.BLOCKCHAIN+':'+whatisthisaddress(issuer,mode)["workspace"][2:],
									'data' : issuerprofile,
									'type' : category},
						"topic": topic,
						"value" : value,	
						"expires" : date,
						"encrypted" : encrypted,
						"location" : 'https://ipfs.infura.io/ipfs/'+doc[6].decode('utf-8'),						
						"signaturetype" : "Secp256k1SignatureVerificationKey2018, AES128 MODE-EAX",
						"signature" : 'Unknown',
						"signature_check" : 'Undone'}
	return document


#####################################################	
# read Talao claim
######################################################
def getclaim (claim_id, workspace_contract,mode) :
# @claim_id : str, identifiant d un claim
# return un dictionnaire
# ajouter le check de validité

	w3 = mode.w3
	claim = dict()

	# determination de l address du owner
	contract = w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	
	# calcul du did
	did = "did:talao:"+mode.BLOCKCHAIN+":"+workspace_contract[2:]			
	
	# initialisation IPFS
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	
	# download du claim
	contract = w3.eth.contract(workspace_contract,abi = constante.workspace_ABI)
	claimdata = contract.functions.getClaim(claim_id).call()
	if claimdata[0] == 0 and claimdata[1] == 0:
		print( 'claim n existe pas ')
		return False
	
	inv_topic = dict(map(reversed, constante.topic.items()))
	topicname = inv_topic.get(claimdata[0])
	if topicname is None :
		topicname = 'certificate'
	issuer = claimdata[2]	
	data = claimdata[4]
	url = claimdata[5]
	
	# identification de la category de l'issuer du claim
	contract = w3.eth.contract(whatisthisaddress(issuer,mode)["workspace"],abi = constante.workspace_ABI)
	identityinformation = contract.functions.identityInformation().call()[1]
	
	if identityinformation == 1001 :
		category = "person"
		path = "resume"
	elif identityinformation == 2001 :
		category = "company"
		if topicname == 'url' :
			topicname = 'website'
		elif topicname == 'firstname' :
			topicname = 'name'	
		path = "profil"
	else :
		print ('erreur de category')
		return False
		
	# determination du profil de l issuer
	(issuerprofile,X) = readProfil(whatisthisaddress(issuer,mode)["owner"], whatisthisaddress(issuer,mode)["workspace"],mode)

	# verification de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32'], [bytes(topicname, 'utf-8'), issuer, data, bytes(url, 'utf-8') ])
	message = encode_defunct(text=msg.hex())
	signature = claimdata[3]
	if signature != b"" :
		signataire = w3.eth.account.recover_message(message, signature=signature)
		signature = claimdata[3].hex()
		verification = 'Right' if signataire == issuer else 'False' 	
	else :
		signature = 'Unknown'
		verification = 'Undone'
	
	# calcul de la date
	date = 'Unlimited'
	
	# mise en forme de la reponse
	claim["id"] = "did:talao:rinkeby:"+workspace_contract[2:]+":claim:"+claim_id
	claim['endpoint'] = mode.server+'talao/api/data/'+claim['id']
	claim["data"] = {"issuer" :{'id' : "did:talao:rinkeby:"+whatisthisaddress(issuer,mode)["workspace"][2:],
					'endpoint' : mode.server+"talao/"+path+"/did:talao:"+mode.BLOCKCHAIN+":"+whatisthisaddress(issuer,mode)["workspace"][2:],
					'data' : issuerprofile,
					'type' : category}}

	claim['data']['topic'] = topicname	
	
	if claimdata[5][:1] == "Q" : # les datas sont sur IPFS
		claim['data']['value'] = client.get_json(claimdata[5])
		claim['data']['location'] = 'https://ipfs.infura.io/ipfs/'+claimdata[5]
		if 	topicname == 'certificate' :
			claim['data']['value']['certificate_link'] = claim_id
		else :
			claim['data']['value'].get('certificate_link', 'No') 
	else :		
		claim['data']['value'] = claimdata[4].decode('utf-8')
		claim['data']['location'] = mode.BLOCKCHAIN # a corriger pour ne pas avoir de pb du lien dans webserver.py

	claim['data']['expires'] = date
	claim['data']['encrypted'] = 'Public'
	claim['data']['signaturetype'] = 'Keccak256(topic,issuer,data, url) ECDSA'
	claim['data']['signature'] = signature
	claim['data']['signature_check'] = verification
	
	return claim


##############################################
# @data = did ou document ou claim
# did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b'
# did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim;56879abc
#  
def getdata(data, mode) :
	w3 = mode.w3
	datasplit = data.split(':')
	workspace_contract = '0x' + datasplit[3]
	if datasplit[4]== 'document' :
		return getdoc(int(datasplit[5]), workspace_contract, mode)
	if datasplit[4]== 'claim' :	
		return getclaim(datasplit[5], workspace_contract, mode)



