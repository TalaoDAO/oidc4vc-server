import datetime
import json
from datetime import datetime
import constante
import Talao_token_transaction
import Talao_ipfs
import ipfshttpclient
from web3.auto import w3
import sys

# return claim 

def getclaim (topicname, workspace_contract) :
# @topicname est un str
# return un array
 
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	claims=[]
	did="did:talao:"+constante.BLOCKCHAIN+":"+workspace_contract[2:]		
	topic=constante.topic	
	claimIdvalue=topic.get(topicname)
	if claimIdvalue == None :
		return None 
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	data = contract.functions.getClaimIdsByTopic(claimIdvalue).call()
	for i in range(0,len(data)) :
		
		claimdata=contract.functions.getClaim(data[i]).call()
		issuer=claimdata[2]
		if issuer == address :
			issuer='owner'
		claim=dict()
		claim["did"] = did
		claim['@context'] = "https://talao.io/did/claim_documentation"
		claim["issuer"] = issuer
		claim['claim'] = {'id': data[i].hex(), topicname : claimdata[4].decode('utf-8'), 'url' : claimdata[5]}
		claim['type']='Keccak256(topic,issuer,data)'
		claim['signature'] = claimdata[3].hex()
		claims.append(claim)
	return claims


print (json.dumps(getclaim('email', '0x29f880c177cD3017Cf05576576807d1A0dc87417'), indent=4))
