import json
import constante
from web3.auto import w3
import ipfshttpclient
from eth_account.messages import encode_defunct
import Talao_ipfs
import constante
import json
import datetime
import sys
import isolanguage
import GETresume



def address2did(address1) :
	if w3.isAddress(address1) == False :
		category = False
		controller = None
		did_id= None
	else :
		contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
		address = contract.functions.contractsToOwners(address1).call()
		workspace=contract.functions.ownersToContracts(address1).call()
		if address == '0x0000000000000000000000000000000000000000' and workspace != '0x0000000000000000000000000000000000000000' :
			category = "controller"
			controller = address1
			did_id = 'did:talao:rinkeby:'+workspace[2:]
		if address != '0x0000000000000000000000000000000000000000' and workspace == '0x0000000000000000000000000000000000000000' :
			category = 'did'
			controller=address
			did_id='did:talao:rinkeby:'+address1[2:]
		if address == '0x0000000000000000000000000000000000000000' and workspace == '0x0000000000000000000000000000000000000000' :
			category = 'unknown'
			controller = address1
			did_id ='unknown'
			
	return {"type" : category, "controller" : controller, 'did' : did_id}

#####################################################	
# read Talao document
######################################################
# @_doctype = integer, 40000 = Diploma, 50000 = experience, 60000 certificate
# return dictionnaire

def getdocument(index, workspace_contract) :
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	did="did:talao:"+constante.BLOCKCHAIN+":"+workspace_contract[2:]		
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	doc=contract.functions.getDocument(index).call()
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	data=client.get_json(doc[6].decode('utf-8'))
	doc_type={10000 : "employability", 40000 : "diploma", 50000 : "experience", 60000 : "certificate"}
	document=dict()
	document['@context'] = "https://github.com/TalaoDAO/talao-contracts"
	document["issuer"] = address2did(doc[3])
	document['doctype'] = doc[0]
	document["expires"]= doc[2]
	document["encrypted"] = doc[7]
	document["storage"] = 'https://ipfs.infura.io/ipfs/'+doc[6].decode('utf-8')

	if doc[0]==10000 :  # employabilite
		data=client.get_json(doc[6].decode('utf-8'))['availability']
		document ['data']=data


	if doc[0]== 40000 : #diploma
		data=client.get_json(doc[6].decode('utf-8'))
		del data["recipient"]
		del data["documentType"]
		del data["version"]
		document["data"] = data['diploma']
		document["data"]["organization"]=data["issuer"]["organization"]['name']
	
		
		
	if doc[0] == 50000 or doc[0]==60000 : #experience
		data=client.get_json(doc[6].decode('utf-8'))
		del data["recipient"]	
		del data["documentType"]
		del data["version"]
		new_skills=[]
		for j in range (0, len(data['certificate']['skills'])) :
			new_skills.append(data['certificate']['skills'][j]['name'])
		del data['certificate']['skills']
		data['certificate']['skills']=new_skills
		document["data"]={'organization' : data['issuer']['organization']}
		document["data"]["organization"]['contact']=data['issuer']["responsible"]
		document['data']['experience']=data['certificate']
		document['data']['experience']['ratings' ]=data['certificate']['ratings']
	return document


#####################################################	
# read Talao claim
######################################################
def getclaim (claim_id, workspace_contract) :
# @topicname est un str
# return un objet List
# ajouter le check de validité

	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	claims=[]
	did="did:talao:"+constante.BLOCKCHAIN+":"+workspace_contract[2:]			
	claim=dict()
	
	# initialisation IPFS
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	claimdata=contract.functions.getClaim(claim_id).call()
	topic=constante.topic
	inv_topic=dict(map(reversed, topic.items()))
	topicname=inv_topic[claimdata[0]]
	issuer=claimdata[2]	
	data=claimdata[4]
	
	url=claimdata[5]

	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32'], [bytes(topicname, 'utf-8'), issuer, data, bytes(url, 'utf-8') ])
	message = encode_defunct(text=msg.hex())
	signature=claimdata[3]
	print(signature)
	if signature != b"" :
		signataire=w3.eth.account.recover_message(message, signature=signature)
		if signataire==issuer :
			verification=True
		else :
			verification=False	
	else :
		verification = None
	claim['@context'] = "https://github.com/TalaoDAO/talao-contracts"
	claimt["issuer"] = address2did(issuer)
	claim['topic']=topicname
	if claimdata[5][:1]=="Q" :
		urldata=client.get_json(claimdata[5])
	else :
		urldata=claimdata[5]
		urldata=claimdata[4].decode('utf-8')
	claim['claim'] = {'id': claim_id, 'data' : urldata}
	claim['type']=['Keccak256(topic,issuer,data, url)','ECDSA']
	claim['signature'] = claimdata[3].hex()
	claim['authenticated']=verification
	return claim



########################
#MAIN

data ='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b' # David Houlle


datasplit=data.split(':')
if datasplit[0] != 'did' or len(datasplit) not in [4,6] :
	print('ce n est pas un did')
workspace_contract='0x'+datasplit[3]
if len(datasplit) == 6 :
	if datasplit[4]== 'document' :
		result=getdocument(int(datasplit[5]), workspace_contract)
	if datasplit[4]=='claim' :
		result = getclaim(datasplit[5], workspace_contract)
if len(datasplit) == 4 :
	result=GETresume.getresume(workspace_contract)

print(json.dumps(result, indent=4))


