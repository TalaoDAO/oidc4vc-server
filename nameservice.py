"""

le name service permet de creer un lien entre un identifiant et un did.
la donn&e est gérée par la fondation, les données sont stockées sur la blockchain
le regsitre identifiant => did est cnstruit dynamiquement
ex : monidentifiant.TalentConnect est stocké dans la workspace a la creation et par la fondation ou le owner 

1) creer un claim "nameservice" 110097109101115101114118105099101 par le owner ou par la fondation avec la valeur "name" publique
2) creer le registre dynamique "did:name" par la fondation

#  /usr/local/bin/geth --rinkeby --syncmode 'light'  --rpcapi="db,eth,net,web3,personal,web3" --cache=4096 --rpc


Pour faire un call a la fonction getContractIndex qui a un "only owner", il faut passer par une addresse importée en local au node

1) pour importer une private key dans le node
a= w3.geth.personal.importRawKey(foundation_privatekey, 'the-passphrase')

2) pour unlocker le compte dans le node : attention il faut arreter le http, docn enlever --rpc au lancement de geth
a=w3.geth.personal.unlockAccount(address, 'the-passphrase')

# utiliser le provider http (--rpc)  et les api (--rpcapi="db,eth,net,web3,personal,web3") pour l acces
#  /usr/local/bin/geth --rinkeby --syncmode 'light'  --rpcapi="db,eth,net,web3,personal,web3" --cache=4096 --rpc


normalisation:
http://unicode.org/reports/tr46/

"""


from eth_account.messages import encode_defunct
import hashlib
import json
import random

#dependances
import Talao_message
import constante


####################################################
# Nanehash
####################################################
# cf https://docs.ens.domains/dapp-developer-guide/resolving-names

def sha3(key) :
	bkey=bytes(key, 'utf-8')
	m=hashlib.sha3_256()
	m.update(bkey)
	return m.digest().hex()

def namehash(name) :
	bname=bytes(name, 'utf-8')	
	if name == '':
		return '0x00000000000000000000000000000000000'
	else:
		label, _, remainder = name.partition('.')
		a =sha3( namehash(remainder) + sha3(label) )
		return a





#################################################
#  construction dynamique du registre 
#################################################
# le regsitre est un dict {hashname : address}

def buildregister(mode) :

	w3=mode.initProvider()
	
	# pour choisir l address par defaut du node necessaire a la lecture de l index du smart contract de la fondation
	address = mode.foundation_address
	w3.eth.defaultAccount=address
	
	# lecture de la liste des contracts dans la fondation
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	contractlist = contract.functions.getContractsIndex().call() 
	contractlist.reverse()
	
	# construction du registre sur la base des claim firstname et name
	register=dict()	
	for workspace_contract in contractlist :
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		
		# prenom+nom 103105118101110078097109101(firstname) et 102097109105108121078097109101(name)
		lastname=""
		firstname=""
		try :
			firstname_claimId=contract.functions.getClaimIdsByTopic(103105118101110078097109101).call()
		except :
			print ("erreur 1")
			firstname_claimId=[]
		if len(firstname_claimId) != 0 :
			claimId=firstname_claimId[0].hex()
			try :
				firstname = contract.functions.getClaim(claimId).call()[4].decode('utf-8')			
			except :
				firstname=""
				print('erreur 2', claimId)		
		
		try : 
			lastname_claimId = contract.functions.getClaimIdsByTopic(102097109105108121078097109101).call()
		except :
			print ("erreur 3")
			lastname_claimId=[]			
		if  len(lastname_claimId) != 0 :							
			claimId=lastname_claimId[0].hex()
			try :
				lastname = contract.functions.getClaim(claimId).call()[4].decode('utf-8')
			except :
				lastname=""
				print('erreur 4', claimId)
						
		name=firstname+'.'+lastname
		
		if register.get(namehash(name.lower())) != None : 
			mylastname=lastname+str(random.randrange(9999))
			name=firstname+'.'+mylastname
		else :	
			mylastname=lastname
			name=firstname+'.'+lastname
		did = 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]	
		if len(contract.functions.getClaimIdsByTopic(101109097105108).call()) != 0 :
			claimId=contract.functions.getClaimIdsByTopic(101109097105108).call()[0].hex()
			email = contract.functions.getClaim(claimId).call()[4].decode('utf-8')
			
		register[namehash(name.lower())]={ 'firstname' : firstname, 'lastname' : mylastname, 'email_authentification' : email, 'workspace_contract' : workspace_contract, 'resolver' : mode.server+'resolver/api/'+did, 'resume' : mode.server+"talao/api/resume/"+ did}	
		
		
		"""
		# construction du registre sur la base du claim "nameservice" 
		if len(contract.functions.getClaimIdsByTopic(110097109101115101114118105099101).call()) != 0 :
			claimId=contract.functions.getClaimIdsByTopic(110097109101115101114118105099101).call()[0].hex()
			hashname = contract.functions.getClaim(claimId).call()[4].decode('utf-8')
			register[hashname]=workspace_contract
		"""
		
		
		"""
		# construction sur la base de l'email a retirer
		if len(contract.functions.getClaimIdsByTopic(101109097105108).call()) != 0 :
			claimId=contract.functions.getClaimIdsByTopic(101109097105108).call()[0].hex()
			email = contract.functions.getClaim(claimId).call()[4].decode('utf-8')
			register[namehash(email.lower())]=workspace_contract
		"""
	print(register)
	try : 
		myfile=open(mode.BLOCKCHAIN+'_register.json', 'w') 
	except IOError :
		print('IOError ; impossible de stocker le fichier')
		return False

	json.dump(register, myfile)
	myfile.close()
	return True
	
	

#################################################
#  lecture du registre 
#################################################
# le registre est un dict {hashname : address}

def load_register_from_file(mode) :
	
	# Charger le dictionnaire depuis un fichier :
	with open(mode.BLOCKCHAIN+'_register.json', 'r') as myfile: 
		mode.register = json.load(myfile)
	myfile.close()
	return True
	

"""
#################################################
#  setup name 
#################################################
# @name : str
# setup name pour le nameservice
# cela remet a jour le fichier register.json en meme temps
# cf https://docs.ens.domains/dapp-developer-guide/managing-names
# signature cf https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message
# le namehash de name est stocké dans le workpace avec un claim 'nameservice'
	
def setup_address(name, workspace_contract,private_key, mode) :
		
	w3=mode.initProvider()

	issuer = mode.foundation_address	
	data=namehash(name.lower())	
	topicname='nameservice'
	topicvalue= 110097109101115101114118105099101
	ipfshash=""
	
	nonce = w3.eth.getTransactionCount(mode.foundation_address)  	
	
	address=mode.foundation_address
	balance =w3.eth.getBalance(address)/1000000000000000000
	if balance < 0.2 :
		Talao_message.messageAdmin('nameservice', 'balance foundation < 0.2 eth', mode)
	
	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
	#message = encode_defunct(text=msg.hex())
	w3.eth.defaultAccount=mode.foundation_address
	signed_message=w3.eth.sign(mode.foundation_address, data=msg)
	#signed_message = w3.eth.account.sign_message(message, private_key=mode.foundation_private_key)
	#signature=signed_message['signature']	
	signature=signed_message
	
	# build, sign and send avec une addresse dans le node "defaultAccount
	w3.eth.defaultAccount=mode.foundation_address
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	hash1=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).transact({'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce})	
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	
	# register et register.json update
	mode.register[data]=workspace_contract
	try : 
		myfile=open(mode.BLOCKCHAIN+'_register.json', 'w') 
	except IOError :
		print('impossible de stocker le fichier')
		return False
	json.dump(mode.register, myfile)
	myfile.close()
		
	return True
"""

#####################################################	
# obtenir l address depuis un nom
######################################################
def address(name,register) :
	if register.get(namehash(name.lower())) != None :
		return register.get(namehash(name.lower()))['workspace_contract']
	else :
		return None

