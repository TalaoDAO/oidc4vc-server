import json
import constante
import Talao_token_transaction
import Talao_ipfs
import ipfshttpclient
import nameservice

from web3 import Web3
my_provider = Web3.IPCProvider('/home/thierry/.ethereum/rinkeby/geth.ipc')
w3 = Web3(my_provider)
	



########################################################################
#                    RESOLVER
########################################################################
# retourne un dict
# https://www.w3.org/TR/did-core/
# Add an ECDSA ERC 725 key for initial owner with MANAGER purpose
# newWorkspace.addKey(keccak256(abi.encodePacked(msg.sender)), 1, 1);
# w3.soliditySha3(['address'], [address])



def getresolver(did) :

	workspace_contract='0x'+did[18:]
	
	# recuperation de l'address du owner
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()

	# calcul du keccak
	owner_publicKeyHex=w3.soliditySha3(['address'], [address])

	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)

	# initialisation du Dict corespondant au DID Document
	workspace_information=contract.functions.identityInformation().call()
	cat={1001 : "user", 2001 : "company", 3001 : "unknown", 4001 : "unknoown", 5001 : "unknown"}
	
	# to be done
	(auth_email, auth_phone, auth_website) = nameservice.getauth(workspace_contract)
	
	
	# structure du DID Document
	did_document={
	"@context": "DID Document see https://w3c.github.io/did-core/",
	"id": did,
	"category" : cat[workspace_information[1]],
	"controller" : address,
	"authentication" : [{"type": "RsaVerificationKey2018",
						"controller" : address,
						"publicKeyPem": workspace_information[4].decode('utf_8')},
						{"type": "EmailAuthentication",
						"controller" : address,
						"email": auth_email},
						{"type": "SMSAuthentication, WhatsAppAuthentication, TelegramAuthentication",
						"controller" : address,
						"phone": auth_phone},
						{"type": "DNSAuthentication",
						"controller" : address,
						"website": auth_website}
						
						],
	"publicKey": [],
	"encryption" : [],
	"service" : {}}


########################################################################################
#                     INDIVIDUAL
########################################################################################	
	if workspace_information[1] == 1001 :
		
		did_document["service"]['freedapp'] = { "endpoint" : "http://vault.talao.io:4011/visit/"+workspace_contract,
				"method" : "GET",
				"@context" : "https://talao.io/",
				"description" : "have a look at my resume"}

		did_document["service"]["resume"] = { "endpoint" : "http://127.0.0.1:5000/talao/api/resume/"+ did,
				"method" : "GET",
				"@context" : "https://talao.io",
				"description" : "check and verify my resume"}
				
		did_document["service"]["messagebox"]  = { "endpoint" : "to be done....",
				"method" : "POST",
				"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/identity/Identity.sol",
				"description" : "send me a message"}
	
		did_document["service"]["digitalvault"]  = { "endpoint" : "to be done....",
				"method" : "POST",
				"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/identity/Identity.sol",
				"description" : "send me private document"}
					
		did_document["service"]["requestparnership"]= {"endpoint" : "to be done",
					"method" : "POST",
					"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/access/Partnership.sol",
					"description" : "Let's partner together and exchange private data"}
	
		did_document["service"]["transfercrypto"] = {"endpoint" : "to be done",
					"method" : "POST",
					"@context" : "eth and TALAO token",
					"description" : "My Ethereum account"}	
	




########################################################################################
#                     COMPANY et les autres...................
########################################################################################	
	else : 
		
		did_document["service"]["publicdata"] = { "endpoint" : "http://127.0.0.1:5000/talao/api/resume/"+ did,
				"method" : "GET",
				"@context" : "https://talao.io",
				"description" : "check and verify our Company data"}
				
		did_document["service"]["messagebox"]  = { "endpoint" : "to be done....",
				"method" : "POST",
				"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/identity/Identity.sol",
				"description" : "send us a message"}
	
		did_document["service"]["digitalvault"]  = { "endpoint" : "to be done....",
				"method" : "POST",
				"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/identity/Identity.sol",
				"description" : "send us private documents"}
					
		did_document["service"]["requestparnership"]= {"endpoint" : "to be done",
					"method" : "POST",
					"@context" : "https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/access/Partnership.sol",
					"description" : "Let's partner together and exchange private data"}
	
		did_document["service"]["transfercrypto"] = {"endpoint" : "to be done",
					"method" : "POST",
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

