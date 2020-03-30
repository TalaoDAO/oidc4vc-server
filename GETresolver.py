"""
Le Resolver permet d'avoir acces au DID document

cf le standard https://www.w3.org/TR/did-core/

"""

import json
import constante
import Talao_token_transaction
import Talao_ipfs
import ipfshttpclient
import nameservice




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


########################################################################
#                    RESOLVER
########################################################################
# retourne un dict
# Add an ECDSA ERC 725 key for initial owner with MANAGER purpose
# newWorkspace.addKey(keccak256(abi.encodePacked(msg.sender)), 1, 1);
# w3.soliditySha3(['address'], [address])



def getresolver(did,mode) :
	

	w3=mode.initProvider()
	
	# test de validité du did
	if Talao_token_transaction.isdid(did,mode) :
		workspace_contract='0x'+did.split(':')[3]
	else :	
		return False
	
	# recuperation de l'address du owner
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()

	# calcul du keccak
	owner_publicKeyHex=w3.soliditySha3(['address'], [address])

	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)

	# initialisation du Dict corespondant au DID Document
	workspace_information=contract.functions.identityInformation().call()
	cat={1001 : "user", 2001 : "company", 3001 : "unknown", 4001 : "unknoown", 5001 : "unknown"}
	
	
	
	# structure du DID Document
	did_document={
	"@context": "DID Document see https://w3c.github.io/did-core/",
	"id": did,
	"category" : cat[workspace_information[1]],
	"controller" : address,
	"authentication" : [{"type": "Secp256k1SignatureVerificationKey2018",
						"controller" : address,
						"EthereumKey": address},
						{"type": "RsaVerificationKey2018",
						"controller" : address,
						"publicKeyPem": workspace_information[4].decode('utf_8')}			
						
						
						],
	"publicKey": [],
	"encryption" : [],
	"service" : {}}


########################################################################################
#                     INDIVIDUAL
########################################################################################	
	if workspace_information[1] == 1001 :
		
		did_document["service"]['resume_viewer'] = { "endpoint" : mode.WORKSPACE_LINK+workspace_contract,
				"@context" : "https://talao.io/",
				"description" : "have a look at my resume"}

		did_document["service"]["resume"] = { "endpoint" : mode.server+"talao/api/resume/"+ did,
				"@context" : "https://talao.io",
				"description" : "check and verify my resume"}
				
		did_document["service"]["messagebox"]  = { "endpoint" : "to be done....",
				"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/identity/Identity.sol",
				"description" : "send me a message"}
	
		did_document["service"]["digitalvault"]  = { "endpoint" : "to be done....",
				"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/identity/Identity.sol",
				"description" : "send me private document"}
					
		did_document["service"]["requestparnership"]= {"endpoint" : "to be done",
					"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/access/Partnership.sol",
					"description" : "Let's partner together and exchange private data"}
	
		did_document["service"]["transfercrypto"] = {"endpoint" : "to be done",
					"@context" : "eth and TALAO token",
					"description" : "My Ethereum account"}	
	




########################################################################################
#                     COMPANY et les autres...................
########################################################################################	
	else : 
		
		
		did_document["service"]["publicdata"] = { "endpoint" : mode.server+"talao/api/profil/"+ did,
				"@context" : "https://talao.io",
				"description" : "check and verify Company data"}
				
		did_document["service"]["messagebox"]  = { "endpoint" : "to be done....",
				"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/identity/Identity.sol",
				"description" : "send us a message"}
	
		did_document["service"]["digitalvault"]  = { "endpoint" : "to be done....",
				"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/identity/Identity.sol",
				"description" : "send us private documents"}
					
		did_document["service"]["requestparnership"]= {"endpoint" : "to be done",
					"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/access/Partnership.sol",
					"description" : "Let's partner together and exchange private data"}
	
		did_document["service"]["transfercrypto"] = {"endpoint" : "to be done",
					"@context" : "eth and TALAO token",
					"description" : "Our Ethereum account"}	
	
		
	
	# MANAGEMENT keys
	data = contract.functions.getKeysByPurpose(1).call()
	for i in range(0, len(data)) :
		key=contract.functions.getKey(data[i]).call()
		keyId=w3.soliditySha3(['string', 'string'], [key[2].hex(), 'MANAGEMENT']).hex()
		if key[2].hex() == owner_publicKeyHex.hex()[2:] :
			key_controller = address
		else :
			key_controller = 'unknown'
		did_document["publicKey"].append({"id": keyId,
		"type": ["Secp256k1SignatureVerificationKey2018", "ERC725ManagementKey"],
		"controller" : key_controller,
		"publicKeyHex": key[2].hex()})
	
	# ACTION Keys
	data = contract.functions.getKeysByPurpose(2).call()
	for i in range(0, len(data)) :
		key=contract.functions.getKey(data[i]).call()
		keyId=w3.soliditySha3(['string', 'string'], [key[2].hex(), 'ACTION']).hex()
		if key[2].hex() == owner_publicKeyHex.hex()[2:] :
			key_controller = address
		else :
			key_controller = 'unknown'
		did_document["publicKey"].append({"id": keyId,
		"type": ["Secp256k1SignatureVerificationKey2018", "ERC725ActionKey"],
		"controller" : key_controller,
		"publicKeyHex": key[2].hex()})
		did_document.append({"authentication": { "id" : KeyId,
		"type": "Secp256k1SignatureAuthentication2018",
		"controller" : key_controller,
		"publicKey": key[2].hex()}})
	
	# CLAIM Keys
	data = contract.functions.getKeysByPurpose(3).call()
	for i in range(0, len(data)) :
		key=contract.functions.getKey(data[i]).call()
		keyId=w3.soliditySha3(['string', 'string'], [key[2].hex(), 'CLAIM']).hex()
		if key[2].hex() == owner_publicKeyHex.hex()[2:] :
			key_controller = address
		else :
			key_controller = 'unknown'
		did_document["publicKey"].append({"id": keyId,
		"type": ["Secp256k1SignatureVerificationKey2018", "ERC725ClaimKey"],
		"controller" : key_controller,
		"publicKeyHex": key[2].hex()})
	
	# ENCRYPTION Keys
	data = contract.functions.getKeysByPurpose(4).call()
	for i in range(0, len(data)) :
		key=contract.functions.getKey(data[i]).call()
		keyId=w3.soliditySha3(['string', 'string'], [key[2].hex(), 'MANAGEMENT']).hex()
		if key[2].hex() == owner_publicKeyHex.hex()[2:] :
			key_controller = address
		else :
			key_controller = 'unknown'
		did_document["publicKey"].append({"id": keyId,
		"type": ["Secp256k1SignatureVerificationKey2018", "ERC725EncryptionKey"],
		"controller" : key_controller,
		"publicKeyHex": key[2].hex()})
		did_document.append({"encryption": {
		"type": "Secp256k1SignatureEncryption2018",
		"controller" : key_controller,
		"publicKey": ""	}})

	 
	return did_document

