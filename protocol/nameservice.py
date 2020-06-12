"""
le nameservice permet de creer un lien entre un identifiant et un did.
C est un service independant du protocol
le registre du nameservice est gérée par la fondation, il est realisable parcque la fondation a l aces a la liste des workspaces qui ont été cré. 
On peut donc acceder a l enselble des workspaces existant et construire un "registre" en memoire et sur disque


on calcul un namehash du username sur le principe du name service de Ethereum https://docs.ens.domains/dapp-developer-guide/resolving-names
registre = { namehash :{ 'username' : username, 'email_authentification' : email, 'workspace_contract' : workspace_contract, 'resolver' : mode.server+'resolver/api/'+did, 'resume' : mode.server+"talao/api/resume/"+ did}}		

le nameservice est utilisé pour simplifier l acces au service en evitant l utilisation du "did". 
Mais seul le 'did' est unique et immuable alors que l on peut créer plusieurs 'username', les effacer, etc


"""


from eth_account.messages import encode_defunct
import hashlib
import json
import random

#dependances
import constante


####################################################
# Namehash
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

	
#####################################################	
# obtenir l address depuis un username 
######################################################
def username_to_data(username,mode) :
	if mode.register.get(namehash(username.lower())) != None :
		return mode.register.get(namehash(username.lower()))
	else :
		return None
	
#####################################################	
# obtenir le workspace_contract depuis un pubicKeyHex
######################################################
def workspaceFromPublickeyhex(publickeyhex,mode) :
	
	#return [access for access in mode.register if access.get('publicKey') == publickeyhex]  
	for a in mode.register  :
		if mode.register[a].get('publicKey') == publickeyhex :
			return  {'workspace_contract' : mode.register[a].get('workspace_contract'), 'username' : mode.register[a].get('username')}
	return None

	
	
#####################################################	
# obtenir des datas depuis un pubicKeyHex
######################################################
def data_from_publickey(publickeyhex,mode) :
	for a in mode.register  :
		if mode.register[a].get('publicKey') == publickeyhex :
			return  {'address' : mode.register[a].get('address'), 'workspace_contract' : mode.register[a].get('workspace_contract'), 'username' : mode.register[a].get('username')}
	return None
		
#####################################################	
# obtenir le username depuis le workspace_contract
######################################################
def getUsername(workspace_contract,mode) :
	for a in mode.register  :
		if mode.register[a].get('workspace_contract') == workspace_contract :
			return  mode.register[a].get('username')
	return None

		
#####################################################	
# obtenir le username et email depuis le workspace_contract
######################################################
def username_and_email_list(workspace_contract, mode) :
	this_list=[]
	for access in mode.register  :
		if mode.register[access].get('workspace_contract') == workspace_contract :
			this_list.append({'username' : mode.register[access].get('username'), 'email' : mode.register[access].get('email')})
	return this_list
	
#################################################
#  upload du registre en memoire 
#################################################
def load_register_from_file(mode) :
	
	# Charger le dictionnaire depuis un fichier :
	with open(mode.BLOCKCHAIN+'_register.json', 'r') as myfile: 
		mode.register = json.load(myfile)
	myfile.close()
	return True
	
#################################################
#  ajoute un username au registre memoire et disque
#################################################
def addName(username, address, workspace_contract, email, mode) :
	
	key = mode.w3.soliditySha3(['address'], [address])
	mode.register[namehash(username.lower())] = { 'username' : username,
												'email' : email,
												'publicKey' : key.hex()[2:],
												'address' : address,
												'workspace_contract' : workspace_contract,
												}	
	try : 
		myfile = open(mode.BLOCKCHAIN+'_register.json', 'w') 
	except IOError :
		print('IOError ; impossible de stocker le fichier')
		return False
	json.dump(mode.register, myfile)
	myfile.close()
	return True

#################################################
#  efface un username du registre memoire et disque
#################################################
def deleteName(username, mode) :
	
	del mode.register[namehash(username.lower())]
	try : 
		myfile = open(mode.BLOCKCHAIN+'_register.json', 'w') 
	except IOError :
		print('IOError ; impossible de stocker le fichier')
		return False
	json.dump(mode.register, myfile)
	myfile.close()
	return True

#################################################
#  update un username du registre memoire et disque
#################################################
def updateName(username, newusername, mode) :
	
	if mode.register.get(namehash(username.lower())) is None :
		print ('username does not exist')
		return False	
	address = mode.register.get(namehash(username.lower()))['address']
	contract = mode.w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
	workspace_contract = contract.functions.ownersToContracts(address).call()
	if workspace_contract != '0x0000000000000000000000000000000000000000' :
		# get email
		contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		try :
			a = contract.functions.getClaimIdsByTopic(101109097105108).call()
		except :			
			return False
		if len(a) != 0:
			claimId = a[-1].hex()
			email = contract.functions.getClaim(claimId).call()[4].decode('utf-8')
			print('email = ', email)
		else :
			return False
	else :
		email = 'Unknown'	
	# calcul du keccak (publickey)
	key = mode.w3.soliditySha3(['address'], [address])			
	# effacement de l ancien username 
	del mode.register[namehash(username.lower())]
	did = 'did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract[2:]
	mode.register[namehash(newusername.lower())] = { 'username' : newusername, 'email' : email, 'publicKey': key.hex()[2:],'address' : address, 'workspace_contract' : workspace_contract, 'resolver' : mode.server+'resolver/'+did, 'resume' : mode.server+"talao/resume/"+ did}	
	try : 
		myfile = open(mode.BLOCKCHAIN+'_register.json', 'w') 
	except IOError :
		print('IOError ; impossible de stocker le fichier')
		return False
	json.dump(mode.register, myfile)
	print('register ok')
	myfile.close()
	return True
