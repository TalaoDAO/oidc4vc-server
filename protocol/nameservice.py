"""
le nameservice permet de creer un lien entre un identifiant et un did.
C est un service independant du protocol
le registre du nameservice est gérée par la fondation, il est realisable parcque la fondation a l aces a la liste des workspaces qui ont été cré. 
On peut donc acceder a l enselble des workspaces existant et construire un "registre" en memoire et sur disque

A partir du prenom et du nom on fabrique un username = "prenom.nom", on verifie qu il est unique
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
#from protocol import getEmail
#from .Talao_token_transaction import getEmail

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

###############################################################
#  construction dynamique du registre en memoire et sur disque
# ATTENTION ne faire qu une fois a l initialisation
###############################################################

def buildregister(mode) :
	
	w3 = mode.w3

	# pour choisir l address par defaut du node necessaire a la lecture de l index du smart contract de la fondation
	address = mode.foundation_address
	w3.eth.defaultAccount=address
	
	# lecture de la liste des workspace_contracts dans la fondation
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	contractlist = contract.functions.getContractsIndex().call() 
	contractlist.reverse()
	
	# construction du registre sur la base du username firstname.name
	register = dict()	
	count = 0
	for workspace_contract in contractlist :
		contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		count += 1	
		
		# download de firstname
		firstname = ""
		try :
			firstname_claimId=contract.functions.getClaimIdsByTopic(103105118101110078097109101).call()
		except :
			print ("erreur 1")
			firstname_claimId = []
		if len(firstname_claimId) != 0 :
			claimId = firstname_claimId[-1].hex()
			try :
				firstname = contract.functions.getClaim(claimId).call()[4].decode('utf-8').lower()			
			except :
				firstname = ""
				print('erreur 2', claimId)				
		
		# download de lastname
		lastname = ""
		try : 
			lastname_claimId = contract.functions.getClaimIdsByTopic(102097109105108121078097109101).call()
		except :
			print ("erreur 3")
			lastname_claimId = []			
		if  len(lastname_claimId) != 0 :							
			claimId = lastname_claimId[-1].hex()
			try :
				lastname = contract.functions.getClaim(claimId).call()[4].decode('utf-8').lower()
			except :
				lastname = ""
				print('erreur 4', claimId)
						
		# on verifie que username = "firstname.lastname" n existe pas deja dans le registre sinon, on le modifie
		username = firstname + '.' + lastname		
		if register.get(namehash(username)) is not None :
			newusername = username + str(random.randrange(99999))
		else :
			newusername = username
		
		did = 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]
		
		# on recupere l email
		try :
			a = contract.functions.getClaimIdsByTopic(101109097105108).call()
		except :
			email = None
			a = []	
		if len(a) != 0:
			claimId = a[-1].hex()
			email = contract.functions.getClaim(claimId).call()[4].decode('utf-8')
		else :
			email = None				
		if email is None :
			print ("no email")				
			email = ''			
		
		# calcul du keccak de l address de celui pour qui la cle est emise (publickey)
		contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
		address = contract.functions.contractsToOwners(workspace_contract).call()
		key = mode.w3.soliditySha3(['address'], [address])
		
		register[namehash(newusername)] = { 'username' : newusername, 'email' : email, "publicKey" : key.hex()[2:], 'address' : address, 'workspace_contract' : workspace_contract, 'resolver' : mode.server+'resolver/'+did, 'resume' : mode.server+"talao/resume/"+ did}		
	
	# copie dans le fichier rinkeby/ethereum_register.json du registre (un seul acces au disque)
	print('nombre de workspace =', count)
	try : 
		myfile=open(mode.BLOCKCHAIN+'_register.json', 'w') 
	except IOError :
		print('IOError ; impossible de copier le registre dans le fichier')
		return False
	json.dump(register, myfile)
	myfile.close()
	return True

####################################################
# verifier que l email n'existe pas deja
####################################################
def canRegister_email (email,mode) :
	for a in mode.register  :
		if mode.register[a].get('email') == email :
			return False
	return True 
	
#####################################################	
# DEPRECATED obtenir le workspace_contract depuis un username 
######################################################
def address(username,register) :
	if register.get(namehash(username.lower())) != None :
		return register.get(namehash(username.lower()))['workspace_contract']
	else :
		return None


	
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
def addName(username, address, mode, email=None, workspace_contract=None) :
	
	if workspace_contract is not None :
		resolver = mode.server + 'resolver/did:talao:' + mode.BLOCKCHAIN+':'+ workspace_contract[2:]
		resume = mode.server + 'talao/resume/did:talao:'+ mode.BLOCKCHAIN + ':' + workspace_contract[2:]	
	else :
		resolver = None
		resume = None
	key = mode.w3.soliditySha3(['address'], [address])
	mode.register[namehash(username.lower())] = { 'username' : username,
												'email' : email,
												'publicKey' : key.hex()[2:],
												'address' : address,
												'workspace_contract' : workspace_contract,
												'resolver' : resolver,
												'resume' : resume}	
	print(mode.register[namehash(username.lower())])											
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
