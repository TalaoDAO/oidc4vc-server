import json
import constante
import ipfshttpclient
from eth_account.messages import encode_defunct
import Talao_ipfs
import constante
import json
import datetime
import sys
import isolanguage
import GETresume
import nameservice




##############################################
# detrmination de la nauter de l addresse
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


#####################################################	
# read Talao document
######################################################
# @index : int, identifiant du document
# return dictionnaire


def getdocument(index, workspace_contract,mode) :
	
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
	(issuerprofile, x)=GETresume.readProfil(whatisthisaddress(issuer,mode)["owner"], whatisthisaddress(issuer,mode)["workspace"],mode)	

	# mise en forme de la reponse de la fonction
	
	document["id"]="did:talao:rinkeby:"+workspace_contract[2:]+":document:"+str(index)
	document['endpoint']=mode.server+'data/'+document['id']
	document['data'] = {"issuer" : {'id' : "did:talao:rinkeby:"+whatisthisaddress(issuer,mode)["workspace"][2:],
									'endpoint' : mode.server+'talao/api/'+path+'/did:talao:'+mode.BLOCKCHAIN+':'+whatisthisaddress(issuer,mode)["workspace"][2:],
									'data' : issuerprofile},
						"topic": topic,
						"value" : value,	
						"expires" : doc[2],
						"encrypted" : doc[7],
						"datalocation" : 'https://ipfs.infura.io/ipfs/'+doc[6].decode('utf-8'),						
						"signaturetype" : "Secp256k1SignatureVerificationKey2018",
						"signature" : True,
						'signature_check' : True,
						"validity_check" : True}
	
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
	(issuerprofile,X)=GETresume.readProfil(whatisthisaddress(issuer,mode)["owner"], whatisthisaddress(issuer,mode)["workspace"],mode)

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
	
	# mise en forme de la reponse
	claim["id"]="did:talao:rinkeby:"+workspace_contract[2:]+":claim:"+claim_id
	claim['endpoint']=mode.server+'talao/api/data/'+claim['id']
	claim["data"]={"issuer" :{'id' : "did:talao:rinkeby:"+whatisthisaddress(issuer,mode)["workspace"][2:],
					'endpoint' : mode.server+"talao/api/"+path+"/did:talao:"+mode.BLOCKCHAIN+":"+whatisthisaddress(issuer,mode)["workspace"][2:],
					'data' : issuerprofile}}	
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
	claim['data']['expires']=0
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

	# si data est un identifiant de document
	if len(datasplit) == 6 and datasplit[4]== 'document' :
		result=getdocument(int(datasplit[5]), workspace_contract,mode)

	# si data est un identfiant de claim
	elif len(datasplit) == 6 and datasplit[4]== 'claim' :	
		result = getclaim(datasplit[5], workspace_contract,mode)	
	
	else :
		result = False
	return result
"""
	# si data est un did	
	if len(datasplit) == 4  :
		result=GETresume.getresume(data,mode)
"""		
	


