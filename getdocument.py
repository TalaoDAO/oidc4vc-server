import json
import constante
from web3.auto import w3
import ipfshttpclient

#####################################################	
# read Talao experience/diploma/certificate/employabilite
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
	if doc[0]==10000 :
		data=client.get_json(doc[6].decode('utf-8'))['availability']
	if doc[0]== 40000 :
		data=client.get_json(doc[6].decode('utf-8'))
		del data["recipient"]
		del data["documentType"]
		del data["version"]
	if doc[0] == 50000 or doc[0]==60000 :
		data=client.get_json(doc[6].decode('utf-8'))
		del data["recipient"]	
		del data["documentType"]
		del data["version"]
		new_skills=[]
		for j in range (0, len(data['certificate']['skills'])) :
			new_skills.append(data['certificate']['skills'][j]['name'])
		del data['certificate']['skills']
		data['certificate']['skills']=new_skills
	document=dict()
	document["did"] = did
	document["controller"] = address
	document["issuer"] = doc[3]
	document["document"]={"type" : doc_type[doc[0]],
		'@context' : "https://talao.io/did/document_documentation",
		"expires" : doc[2],
		"data" : data,
		'encrypted' : doc[7]}
	document['authenticated']=True
	return document

# test	
workspace_contract='0xab6d2bAE5ca59E4f5f729b7275786979B17d224b'  # pierre david houlle
#workspace_contract='0x2164c21e2ca79FD205700597A7Cc3A3867E226F1'

print (json.dumps(getdocument(8, workspace_contract), indent=4))
