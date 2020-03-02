import datetime
import json
from datetime import datetime
import constante
import Talao_token_transaction
import Talao_ipfs
import ipfshttpclient
from web3.auto import w3
import sys

"""
[50000, 1, 0, '0xe7Ff2f6c271266DC7b354c1B376B57c9c93F0d65', b"j\x1e'@\xc8\xf3#\xcd\xfe%\xd7\xa8XyM\xce\xb6.\xca/^\x9a\xafn\x90\xe5\xd9\xc1\xf4\xc5\xcd\xcd", 1, b'QmeztGJRx2sKXGkw4fSMWWWwrP3Ww9bwn9NpCf6G9H1TeG', False, 0]
"""



#####################################################	
# read Talao experience or diploma
######################################################
# @_doctype = integer, 40000 = Diploma, 50000 = experience, 60000 certificate
# return dictionnaire

def getdocument(index, workspace_contract) :
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	did="did:talao:"+constante.BLOCKCHAIN+":"+workspace_contract[2:]		
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	doc=contract.functions.getDocument(index).call()
	doctype={10000 : "employability", 40000 : "diploma", 50000 : "experience", 60000 : "certificate"}
	document=dict()
	document["did"] = did
	document["issuer"] = doc[3]
	document["document"]={"type" : doctype[doc[0]], '@context' : "https://talao.io/did/document_documentation", "expires" : doc[2],"location" : 'IPFS', "data" : doc[6].decode('utf-8'), 'encrypted' : doc[7]}
	return document
	
workspace_contract='0xab6d2bAE5ca59E4f5f729b7275786979B17d224b'  # pierre david houlle

print (json.dumps(getdocument(8, workspace_contract), indent=4))
