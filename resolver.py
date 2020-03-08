import json
import constante
import Talao_token_transaction
import Talao_ipfs
import ipfshttpclient
from web3.auto import w3


#############################
# resolver
#############################
# retourne un dict

#test
# workspace_contract='0xfafDe7ae75c25d32ec064B804F9D83F24aB14341'
# workspace_contract='0xab6d2bAE5ca59E4f5f729b7275786979B17d224b'  # pierre david houlle
# workspace_contract='0xe7Ff2f6c271266DC7b354c1B376B57c9c93F0d65' # compte expterne
# workspace_contract='0x29f880c177cD3017Cf05576576807d1A0dc87417' # TTF
# workspace_contract='0x2164c21e2ca79FD205700597A7Cc3A3867E226F1'
# workspace_contract='0x6FD4Cb70c7894fd84AF0708aa12636CCfEf99Ecb'
# did:talao:rinkeby:6FD4Cb70c7894fd84AF0708aa12636CCfEf99Ecb
# did:talao:ethereum:6FD4Cb70c7894fd84AF0708aa12636CCfEf99Ecb


def resolver(did) :
	
	workspace_contract=did[18:]
#	did did:talao:"+constante.BLOCKCHAIN+":"+workspace_contract[2:]



	try : 
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	except:
		return "Addresse erronée"

	try :
		workspace_information = contract.functions.identityInformation().call()
	except :
		return "Cette addresse n'est pas un did Talao ou pb de synchro avec Geth"
	
	# recuperation de l'address du owner
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()

	# calcul du keccak
	owner_publicKeyHex=w3.soliditySha3(['address'], [address])

	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)

	# initialisation du Dict corespondant au DID Document
	# https://www.w3.org/TR/did-core/
	workspace_information=contract.functions.identityInformation().call()
	cat={1001 : "user", 2001 : "company", 3001 : "unknown", 4001 : "unknoown", 5001 : "unknown"}

	did_document={
	"@context": "https://w3id.org/did/v1",
	"id": did,
	"category" : cat[workspace_information[1]],
	"controller" : address,
	"authentication" : [{"type": "RsaVerificationKey2018",
		"controller" : address,
		"publicKeyPem": workspace_information[4].decode('utf_8')}],
	"publicKey": [],
	"encryption" : [],
	"service" : {
		"erc725claim" : { "endpoint" : "to do....",
					"@context" : "utilisez getclaim.py pour acceder au claim",
					"topic" : []},
		"document" : {"endpoint" : "to do....",
					"@context" : "utilisez getdocument.py pour acceder au document",
					"diploma" : [],
					"experience" : [],
					"certificate" : [],
					"employability" : []}
		}
}

	# Add an ECDSA ERC 725 key for initial owner with MANAGER purpose
	#        newWorkspace.addKey(keccak256(abi.encodePacked(msg.sender)), 1, 1);
	# w3.soliditySha3(['address'], [address])

	# recherche des publicKey
	
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

	# SERVICES
	
	# liste des Documents Talao
	experience=[]
	diploma =[]
	certificate=[]
	employability=[]
	docindex=contract.functions.getDocuments().call()
	for i in docindex :
		doc=contract.functions.getDocument(i).call()
		if doc[0] == 10000 :
			employability.append(i)
		if doc[0]==40000:
			diploma.append(i)
		if doc[0] == 50000 :
			experience.append(i)
		if doc[0] == 60000 :
			certificate.append(i)
	did_document["service"]["document"]["experience"]=experience
	did_document["service"]["document"]["diploma"]=diploma
	did_document["service"]["document"]["employability"]=employability
	did_document["service"]["document"]["certificate"]=certificate

	# liste des Claim ERC725
	topic=constante.topic
	inv_topic={}
	for key, value in topic.items() :
		inv_topic[value]=key
	# pour chaque topic
	for i in topic.values() :
		claim=contract.functions.getClaimIdsByTopic(i).call()
		new_claim=[]
		if len(claim) != 0 :
			for j in range(0,len(claim)) :
				claimIdvalue=claim[j].hex()		
				new_claim.append(claimIdvalue)			
				data = contract.functions.getClaim(claimIdvalue).call()
				if { inv_topic[data[0]] :  list(set(new_claim)) } not in did_document['service']['erc725claim']['topic'] :
					did_document['service']['erc725claim']['topic'].append( { inv_topic[data[0]] :  list(set(new_claim)) } ) 
		
	 
	return did_document

