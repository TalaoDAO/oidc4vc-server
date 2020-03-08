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
import getworkspacelist


##############################################
# detrmination de la nauter de l addresse
##############################################
# @thisaddress, address
# return dictionnaire

def whatisthisaddress(thisaddress) :

	# est ce une addresse Ethereum ?
	if w3.isAddress(thisaddress) == False :
		category = False
		owner = None
		workspace= None	
	else :
		
		# test sur la nature de thisaddress
		contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
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


def getdocument(index, workspace_contract) :
	
	# a voir pour l'affichage de doc[0] ?
	#doc_type={10000 : "employability", 40000 : "diploma", 50000 : "experience", 60000 : "certificate"}	
	
	# determination de l addresse du workspace
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	
	# calcul du did
	did="did:talao:"+constante.BLOCKCHAIN+":"+workspace_contract[2:]		
	
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
	issuerprofile=GETresume.readProfil(whatisthisaddress(issuer)["owner"], whatisthisaddress(issuer)["workspace"])	

	# mise en forme de la reponse de la fonction
	document=dict()
	document['@context'] = "https://github.com/TalaoDAO/talao-contracts"
	document["id"]="did:talao:rinkeby:"+workspace_contract[2:]+":document:"+str(index)
	document["issuer"] = {'id' : "did:talao:rinkeby:"+whatisthisaddress(issuer)["workspace"][2:], 'value' : issuerprofile}	
	document['doctype'] = doc[0]
	document['doctypeversion'] = doc[1]
	document["expires"]= doc[2]
	document["encrypted"] = doc[7]
	document["storage"] = 'https://ipfs.infura.io/ipfs/'+doc[6].decode('utf-8')
	
	return document




#####################################################	
# read Talao claim
######################################################
def getclaim (claim_id, workspace_contract) :
# @claim_id : str, identifiant d un claim
# return un dictionnaire
# ajouter le check de validité

	# setup variable
	claims=[]
	claim=dict()

	# determination de l address du owner
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	
	# calcul du did
	did="did:talao:"+constante.BLOCKCHAIN+":"+workspace_contract[2:]			
	
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
	contract=w3.eth.contract(whatisthisaddress(issuer)["workspace"],abi=constante.workspace_ABI)
	identityinformation = contract.functions.identityInformation().call()[1]
	if identityinformation==1001 :
		category="person"
	else :
		category = "company"	
		
	# determination du profil de l issuer
	issuerprofile=GETresume.readProfil(whatisthisaddress(issuer)["owner"], whatisthisaddress(issuer)["workspace"])

	# verification de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32'], [bytes(topicname, 'utf-8'), issuer, data, bytes(url, 'utf-8') ])
	message = encode_defunct(text=msg.hex())
	signature=claimdata[3]
	if signature != b"" :
		signataire=w3.eth.account.recover_message(message, signature=signature)
		if signataire==issuer :
			verification=True
		else :
			verification=False	
	else :
		verification = None
	
	# mise en forme de la reponse
	claim['@context'] = "https://github.com/TalaoDAO/talao-contracts"
	claim["id"]="did:talao:rinkeby:"+workspace_contract[2:]+":claim:"+claim_id
	claim["issuer"] = {'id' : "did:talao:rinkeby:"+whatisthisaddress(issuer)["workspace"][2:],  'value' : issuerprofile}	
	claim['topic']=topicname
	if claimdata[5][:1]=="Q" :
		urldata=client.get_json(claimdata[5])
	else :
		urldata=claimdata[5]
		urldata=claimdata[4].decode('utf-8')
	claim['signaturetype']=['Keccak256(topic,issuer,data, url)','ECDSA']
	claim['signature'] = claimdata[3].hex()
	claim['authenticated']=verification
	claim['url']=claimdata[5]
	
	return claim


##############################################
#   MAIN
##############################################

# données des test
#data ='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:document:10' # David Houlle
#data='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:b34c2a6837a9e89da5ef886d18763fb13a12615814d50a5b73ae403cb547d788'
#data='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b' # david houlle
#data= 'did:talao:rinkeby:29f880c177cD3017Cf05576576807d1A0dc87417' # TTF
#data = 'did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:b34c2a6837a9e89da5ef886d18763fb13a12615814d50a5b73ae403cb547d788'
#data = 'thierry.XX@gmail.com'
#data='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:document:7' # david houlle skil value


data=input('entrez email ou did =')
datasplit=data.split('@')
datasplit2=data.split(':')

# si data est un email
if len(datasplit) == 2 :	
	# recherche d'un did avec cet email
	workspace_contract=getworkspacelist.email2contract(data)
	if workspace_contract== False :
		print('Il n existe pas de workspace pour cet email')
		sys.exit()
	else :
		result=GETresume.getresume(workspace_contract)

# si data n'est pas un did
if datasplit2[0] != 'did' or len(datasplit2) not in [4,6] :
	print('ce n est pas un identifiant')
	sys.exit()

# determination de l'addresse du workspace
workspace_contract='0x'+datasplit2[3]

# si data est un identifiant de document
if len(datasplit2) == 6 and datasplit2[4]== 'document' :
	result=getdocument(int(datasplit2[5]), workspace_contract)

# si data est un identfiant de claim
if len(datasplit2) == 6 and datasplit2[4]== 'claim' :	
	result = getclaim(datasplit2[5], workspace_contract)	

# si data est un did	
if len(datasplit2) == 4  :
	result=GETresume.getresume(workspace_contract)

print(json.dumps(result, indent=4))


