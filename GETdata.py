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

	# a voir pour l'affichage de doc[0] ?
	#doc_type={10000 : "employability", 40000 : "diploma", 50000 : "experience", 60000 : "certificate"}	
	
	# determination de l addresse du workspace
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	
	# calcul du did
	did="did:talao:"+mode.BLOCKCHAIN+":"+workspace_contract[2:]		
	
	# download du doc
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	doc=contract.functions.getDocument(index).call()
	
	# issuer
	issuer = doc[3]

	# category
	identityinformation = contract.functions.identityInformation().call()[1]	
	if identityinformation==1001 :
		category="individual"
	else :
		category = "company"	
			
	# determination du profil de l issuer
	(issuerprofile, x)=GETresume.readProfil(whatisthisaddress(issuer,mode)["owner"], whatisthisaddress(issuer,mode)["workspace"],mode)	

	# mise en forme de la reponse de la fonction
	#document={'id' : None, 'value' :None}
	document=dict()
	document['@context']='https://github.com/TalaoDAO/talao-contracts'
	document["id"]="did:talao:rinkeby:"+workspace_contract[2:]+":document:"+str(index)
	document['endpoint']=mode.server+'data/'+document['id']
	document["methods"]=["GET"]
	document['value'] = {"issuer" : {'id' : "did:talao:rinkeby:"+whatisthisaddress(issuer,mode)["workspace"][2:],
									'endpoint' : mode.server+'resume/did:talao:rinkeby:'+whatisthisaddress(issuer,mode)["workspace"][2:],
									'value' : issuerprofile},	
						'doctype': doc[0],
						'doctypeversion' : doc[1],
						"expires" : doc[2],
						"encrypted" : doc[7],
						"datalocation" : 'https://ipfs.infura.io/ipfs/'+doc[6].decode('utf-8'),						
						"signature" : True,
						'signature_check' : True}
	
	return document




#####################################################	
# read Talao claim
######################################################
def getclaim (claim_id, workspace_contract,mode) :
# @claim_id : str, identifiant d un claim
# return un dictionnaire
# ajouter le check de validité

	w3=mode.initProvider()

	# setup variable
	claims=[]
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
	inv_topic=dict(map(reversed, constante.topic.items()))
	topicname=inv_topic[claimdata[0]]
	issuer=claimdata[2]	
	data=claimdata[4]
	url=claimdata[5]
	
	# identification de la category de l'issuer du claim
	contract=w3.eth.contract(whatisthisaddress(issuer,mode)["workspace"],abi=constante.workspace_ABI)
	identityinformation = contract.functions.identityInformation().call()[1]
	if identityinformation==1001 :
		category="person"
	else :
		category = "company"	
		
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
	claim['@context'] = 'https://github.com/ethereum/EIPs/issues/735'
	claim["id"]="did:talao:rinkeby:"+workspace_contract[2:]+":claim:"+claim_id
	claim['endpoint']=mode.server+'talao/api/data/'+claim['id']
	claim["methods"]=["GET"]
	claim["value"]={"issuer" :{'id' : "did:talao:rinkeby:"+whatisthisaddress(issuer,mode)["workspace"][2:],
					'endpoint' : mode.server+"resume/did:talao:rinkeby:"+whatisthisaddress(issuer,mode)["workspace"][2:],
					'value' : issuerprofile}}	
	claim['value']['topic']=topicname
	if claimdata[5][:1]=="Q" :
		data=client.get_json(claimdata[5])
	else :
		url=claimdata[5]
		data=claimdata[4].decode('utf-8')
	claim['value']['data']=data
	if claimdata[5]=="" :
		claim['value']['data']=None
	else :
		claim['value']['datalocation']='https://ipfs.infura.io/ipfs/'+claimdata[5]
	claim['value']['signaturetype']=['Keccak256(topic,issuer,data, url)','ECDSA']
	claim['value']['signature'] = signature
	claim['value']['signature_check']=verification
	
	
	return claim


##############################################
#   MAIN
##############################################
# @data = email ou did ou document ou claim

#   A refaire !!!!!!

def getdata(data, register,mode) :
	w3=mode.initProvider()

	datasplit=data.split('@')
	datasplit2=data.split(':')
	# si data est un email
	if len(datasplit) == 2 :
		if len(datasplit[1].split('.')) == 1 :
			return data+' n est pas un email correct'
		# recherche d'un did dans le regsitre nameservice
		workspace_contract= register.get(data,mode)
		if workspace_contract== None :
			return 'Il n existe pas de workspace pour '+data
		else :
			did='did:talao:rinkeby:'+workspace_contract[2:]
			result=GETresume.getresume(did,mode)
			return result
			
	# si data n'est pas un did
	if datasplit2[0] != 'did' or len(datasplit2) not in [4,6] :
		return data+' n est pas un identifiant'

	# determination de l'addresse du workspace
	workspace_contract='0x'+datasplit2[3]

	# si data est un identifiant de document
	if len(datasplit2) == 6 and datasplit2[4]== 'document' :
		result=getdocument(int(datasplit2[5]), workspace_contract,mode)

	# si data est un identfiant de claim
	if len(datasplit2) == 6 and datasplit2[4]== 'claim' :	
		result = getclaim(datasplit2[5], workspace_contract,mode)	

	# si data est un did	
	if len(datasplit2) == 4  :
		result=GETresume.getresume(data,mode)

	return result


