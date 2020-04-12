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

	w3=mode.initProvider()

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

	w3=mode.initProvider()

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
	profil=dict()
		
	# determination de la category
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	category = contract.functions.identityInformation().call()[1]	
	
	# si profil d un individu, on retire email
	if category ==1001 : 
		topicvalue =[givenName, familyName, jobTitle, worksFor, workLocation, url,  description]
		topicname =['firstname', 'lastname', 'jobtitle', 'company', 'location', 'url', 'description']
		for i in range (0, len(topicvalue)) :
			claim=contract.functions.getClaimIdsByTopic(topicvalue[i]).call()
			if len(claim) != 0 :
				claimId=claim[0].hex()
				data = contract.functions.getClaim(claimId).call()
				if data[4].decode('utf-8') == "" or data[4].decode('utf-8')==" " :
					profil[topicname[i]]=None
				else :
					profil[topicname[i]]=data[4].decode('utf-8')			
			else :
				profil[topicname[i]]=None		
	
	# si profil d une company
	else :
		topicvalue =[givenName,url,email,contact, adresse]
		topicname =['name', 'website', 'email', 'contact','address']
		for i in range (0, len(topicvalue)) :
			claim=contract.functions.getClaimIdsByTopic(topicvalue[i]).call()
			if len(claim) != 0 :
				claimId=claim[0].hex()
				data = contract.functions.getClaim(claimId).call()
				if data[4].decode('utf-8') == "" or data[4].decode('utf-8')==" " :
					profil[topicname[i]]=None
				else :
					profil[topicname[i]]=data[4].decode('utf-8')										
			else :
				profil[topicname[i]]=None			
	
	return profil,category 


#####################################################	
# read Talao document
######################################################
# @index : int, identifiant du document
# return dictionnaire


def getdoc(index, workspace_contract,mode) :
	
	w3=mode.initProvider()
	document=dict()
	
	# determination de l addresse du workspace
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	
	# calcul du did
	did="did:talao:"+mode.BLOCKCHAIN+":"+workspace_contract[2:]		
	
	# download du doc
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)

	try :
		doc=contract.functions.getDocument(index).call()
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
		value = {"organization" : education["issuer"]["organization"]["name"],
		"endDate" : education["diploma"]["to"], 
		"startDate" : education["diploma"]["from"],
		"studyType" : education["diploma"]["title"],
		"area" : education["diploma"]["description"],
		"certificate_link" : education["diploma"]["link"]}
	elif topic == "experience" :
		ipfs_hash=doc[6].decode('utf-8')
		experience=Talao_ipfs.IPFS_get(ipfs_hash)
		value = {'title' : experience['certificate']['title'],
		'description' : experience['certificate']['description'],
		'from' : experience['certificate']['from'],
		'to' : experience['certificate']['to'],
		'organization' : {"name" : None, 
				"contact_name" : experience['issuer']['responsible']["name"],
				"contact_email" : experience["issuer"]["organization"]["email"]},
		"certification_link" : None	}
	elif topic == 'contact' :
		value=getdocument(workspace_contract, '0x0', workspace_contract, index, mode)
	
	else :
		topic = "unknown"
		value = {}
		
	# issuer
	issuer = doc[3]

	# category
	identityinformation = contract.functions.identityInformation().call()[1]	
	if identityinformation==1001 :
		category="individual"
		path="resume"
	else :
		category = "company"	
		path= "profil"
			
	# determination du profil de l issuer
	(issuerprofile, x)=readProfil(whatisthisaddress(issuer,mode)["owner"], whatisthisaddress(issuer,mode)["workspace"],mode)	

	# calcul de la date
	if doc[2]== 0 :
		date = 'unlimited'
	else :			
		date=datetime.fromtimestamp(doc[2])
		
	# mise en forme de la reponse de la fonction		
	document["id"]="did:talao:rinkeby:"+workspace_contract[2:]+":document:"+str(index)
	document['endpoint']=mode.server+'talao/api/data/'+document['id']
	document['data'] = {"issuer" : {'id' : "did:talao:rinkeby:"+whatisthisaddress(issuer,mode)["workspace"][2:],
									'endpoint' : mode.server+'talao/api/'+path+'/did:talao:'+mode.BLOCKCHAIN+':'+whatisthisaddress(issuer,mode)["workspace"][2:],
									'data' : issuerprofile},
						"topic": topic,
						"value" : value,	
						"expires" : date,
						"encrypted" : doc[7],
						"datalocation" : 'https://ipfs.infura.io/ipfs/'+doc[6].decode('utf-8'),						
						"signaturetype" : "Secp256k1SignatureVerificationKey2018, AES128 MODE-EAX",
						"signature" : True,
						'signature_check' : True,
						"validity_check" : True}
	document['action']={'Delete' : mode.server+'talao/api/data/'+document['id']+'?action=delete'}	
	return document




#####################################################	
# read Talao claim
######################################################
def getclaim (claim_id, workspace_contract,mode) :
# @claim_id : str, identifiant d un claim
# return un dictionnaire
# ajouter le check de validité

	w3=mode.initProvider()
	claim=dict()

	# determination de l address du owner
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	
	# calcul du did
	did="did:talao:"+mode.BLOCKCHAIN+":"+workspace_contract[2:]			
	
	# initialisation IPFS
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	
	# doownload du claim
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	claimdata=contract.functions.getClaim(claim_id).call()
	if claimdata[0] == 0 and claimdata[1] == 0:
		return False
	
	inv_topic=dict(map(reversed, constante.topic.items()))
	topicname=inv_topic.get(claimdata[0])
	if topicname==None :
		topicname ='experience'
	issuer=claimdata[2]	
	data=claimdata[4]
	url=claimdata[5]
	
	# identification de la category de l'issuer du claim
	contract=w3.eth.contract(whatisthisaddress(issuer,mode)["workspace"],abi=constante.workspace_ABI)
	identityinformation = contract.functions.identityInformation().call()[1]
	if identityinformation==1001 :
		category="person"
		path= "resume"
	else :
		category = "company"	
		path="profil"
		
	# determination du profil de l issuer
	(issuerprofile,X)=readProfil(whatisthisaddress(issuer,mode)["owner"], whatisthisaddress(issuer,mode)["workspace"],mode)

	# verification de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32'], [bytes(topicname, 'utf-8'), issuer, data, bytes(url, 'utf-8') ])
	message = encode_defunct(text=msg.hex())
	signature=claimdata[3]
	if signature != b"" :
		signataire=w3.eth.account.recover_message(message, signature=signature)
		signature=claimdata[3].hex()
		if signataire==issuer :
			verification=True
		else :
			verification=False	
	else :
		signature= None
		verification = False
	
	# calcul de la date
	date = 'unlimited'
	
	# mise en forme de la reponse
	claim["id"]="did:talao:rinkeby:"+workspace_contract[2:]+":claim:"+claim_id
	claim['endpoint']=mode.server+'talao/api/data/'+claim['id']
	claim["data"]={"issuer" :{'id' : "did:talao:rinkeby:"+whatisthisaddress(issuer,mode)["workspace"][2:],
					'endpoint' : mode.server+"talao/api/"+path+"/did:talao:"+mode.BLOCKCHAIN+":"+whatisthisaddress(issuer,mode)["workspace"][2:],
					'data' : issuerprofile}}
	claim['action']={'delete' : mode.server+'talao/api/data/'+claim['id']+'?action=delete'}				
	
	if topicname == 'lastname' :
		claim['data']['topic']='profil'
	else :
		claim['data']['topic']=topicname
	if claimdata[5][:1]=="Q" :
		data=client.get_json(claimdata[5])
	else :
		url=claimdata[5]
		data=claimdata[4].decode('utf-8')
	claim['data']['value']=data
	if claimdata[5]=="" :
		claim['data']['value']=None
	else :
		claim['data']['location']='https://ipfs.infura.io/ipfs/'+claimdata[5]
	if topicname == 'lastname' :
		claim['data']['value']=issuerprofile
	claim['data']['expires']=date
	claim['data']['encrypted']=False
	claim['data']['signaturetype']=['Keccak256(topic,issuer,data, url)','ECDSA']
	claim['data']['signature'] = signature
	claim['data']['signature_check']=verification
	claim['data']['validity_check']=True
	
	
	return claim


##############################################
#   MAIN
##############################################
# @data = did ou document ou claim
# did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b'
# did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim;56879abc
#  

def getdata(data,mode) :
	
	w3=mode.initProvider()
	datasplit=data.split(':')
	workspace_contract='0x'+datasplit[3]
	
	# work in progress
	if datasplit[5]=='0' :
		result = {"msg" : "work to be done !!!!!"}
	
	# si data est un identifiant de document
	elif len(datasplit) == 6 and datasplit[4]== 'document' :
		result=getdoc(int(datasplit[5]), workspace_contract,mode)

	# si data est un identfiant de claim
	elif len(datasplit) == 6 and datasplit[4]== 'claim' :	
		result = getclaim(datasplit[5], workspace_contract,mode)	
	
	else :
		result = {"msg" : "error in GETdata"}
	
	return result



