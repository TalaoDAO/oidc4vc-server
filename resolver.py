import json
import constante
import Talao_token_transaction
import Talao_ipfs
import ipfshttpclient
from web3.auto import w3
import sys



def createClaimId(text) :	
	claimId =''
	for i in range(0, len(text))  :
		a = str(ord(text[i]))
		if int(a) < 100 :
			a='0'+a
		claimId=claimId+a
	return int(claimId)
		
		
def gettopicname(topicid) :
	topic=[
	{'id': 103105118101110078097109101, 'topic' :'firstname'},
	{'id' : 102097109105108121078097109101, 'topic' :'lastname'},
	{'id' : 106111098084105116108101, 'topic' :'jobtitle'},
	{'id' :19111114107115070111114, 'topic' :'worksfor'},
	{'id' : 119111114107076111099097116105111110, 'topic' : 'worklocation'},
	{'id' : 117114108, 'topic' : 'url'},
	{'id' : 101109097105108, 'topic' : 'email'},
	{'id' : 100101115099114105112116105111110, 'topic' : 'description'},
	{'id' : 105109097103101, 'topic' : 'image'}] 		

	for i in range (0,len(topic)) :
		if topic[i]['id']==topicid :
			return topic[i]['topic']
	return False



#############################
# MAIN
#############################

#test
#workspace_contract='0xfafDe7ae75c25d32ec064B804F9D83F24aB14341'
workspace_contract='0xab6d2bAE5ca59E4f5f729b7275786979B17d224b'  # pierre david houlle
#workspace_contract='0xe7Ff2f6c271266DC7b354c1B376B57c9c93F0d65' # compte expterne
#workspace_contract='0x29f880c177cD3017Cf05576576807d1A0dc87417' # TTF



did="did:talao:"+constante.BLOCKCHAIN+":"+workspace_contract[2:]
try : 
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
except:
	print("Addresse erronée")
	sys.exit()

try :
	workspace_information = contract.functions.identityInformation().call()
except :
	print("Cette addresse n'est pas un did Talao")
	sys.exit()
	
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
		"erc725claim" : { "endpoint" : "talao.io/api/did/claim",
					"@context" : "....getclaim.py....",
					"topic" : []},
		"document" : {"endpoint" : "tala.io/aoi/did/document",
					"@context" : "....getdocument.py",
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
	
	
# ERC725 ACTION Keys
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

	
# ERC725 CLAIM Keys
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
# Documents Talao
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
#Claim ERC725
topic=[
	{'id': 103105118101110078097109101, 'topic' :'firstname'},
	{'id' : 102097109105108121078097109101, 'topic' :'lastname'},
	{'id' : 106111098084105116108101, 'topic' :'jobtitle'},
	{'id' :19111114107115070111114, 'topic' :'worksfor'},
	{'id' : 119111114107076111099097116105111110, 'topic' : 'worklocation'},
	{'id' : 117114108, 'topic' : 'url'},
	{'id' : 101109097105108, 'topic' : 'email'},
	{'id' : 100101115099114105112116105111110, 'topic' : 'description'},
	{'id' : 105109097103101, 'topic' : 'image'}] 		

for i in range(0,len(topic)) :
	claimIddata=topic[i]['id']
	claim=contract.functions.getClaimIdsByTopic(claimIddata).call()
	if len(claim) != 0 :
		claimIdvalue=claim[0].hex()
		data = contract.functions.getClaim(claimIdvalue).call()
		did_document['service']['erc725claim']['topic'].append(gettopicname(data[0]))
	
	 
print(json.dumps(did_document, indent=4))

