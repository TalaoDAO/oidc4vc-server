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
import constante
#from protocol import getEmail
from .Talao_token_transaction import getUsername, getEmail

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
	
	w3=mode.w3
	
	# pour choisir l address par defaut du node necessaire a la lecture de l index du smart contract de la fondation
	address = mode.foundation_address
	w3.eth.defaultAccount=address
	
	# lecture de la liste des contracts dans la fondation
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	contractlist = contract.functions.getContractsIndex().call() 
	contractlist.reverse()
	
	# construction du registre sur la base du username firstname.name
	register=dict()	
	
	for workspace_contract in contractlist :
		
		# on regarde d abord dans l identité
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		username =getUsername(workspace_contract,mode)
		if username != None:
			print("username de l identité = ", username)		
			did = 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]
			email=getEmail(workspace_contract, mode)
			if email == None :
				print ("no email")				
				email=''
			register[namehash(username)]={ 'username' : username, 'email_authentification' : email, 'workspace_contract' : workspace_contract, 'resolver' : mode.server+'resolver/api/'+did, 'resume' : mode.server+"talao/api/resume/"+ did}	
	
		else :		
			# download de firstname
			firstname=""
			try :
				firstname_claimId=contract.functions.getClaimIdsByTopic(103105118101110078097109101).call()
			except :
				print ("erreur 1")
				firstname_claimId=[]
			if len(firstname_claimId) != 0 :
				claimId=firstname_claimId[0].hex()
				try :
					firstname = contract.functions.getClaim(claimId).call()[4].decode('utf-8').lower()			
				except :
					firstname=""
					print('erreur 2', claimId)				
			# download de lastname
			lastname=""
			try : 
				lastname_claimId = contract.functions.getClaimIdsByTopic(102097109105108121078097109101).call()
			except :
				print ("erreur 3")
				lastname_claimId=[]			
			if  len(lastname_claimId) != 0 :							
				claimId=lastname_claimId[0].hex()
				try :
					lastname = contract.functions.getClaim(claimId).call()[4].decode('utf-8').lower()
				except :
					lastname=""
					print('erreur 4', claimId)
						
			# on verifie que username = "firstname.lastname" n existe pas deja dans le registre sinon, on le modifie
			username=firstname+'.'+lastname		
			if register.get(namehash(username)) != None :
				newusername=username+str(random.randrange(99999))
			else :
				newusername=username
			print("username = ", newusername)		
			did = 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]
			email=getEmail(workspace_contract, mode)
			if email == None :
				print ("no email")				
				email=''			
			register[namehash(newusername)]={ 'username' : newusername, 'email_authentification' : email, 'workspace_contract' : workspace_contract, 'resolver' : mode.server+'resolver/api/'+did, 'resume' : mode.server+"talao/api/resume/"+ did}		
	
	# copie dans le fichier rinkeby/ethereum_register.json du registre
	try : 
		myfile=open(mode.BLOCKCHAIN+'_register.json', 'w') 
	except IOError :
		print('IOError ; impossible de copier le registre dans le fichier')
		return False
	json.dump(register, myfile)
	myfile.close()
	return True
	

####################################################
#    can register email
####################################################

def canRegister_email (email,mode) :
	search = False
	for a in mode.register  :
		if mode.register[a].get('email_authentification') == email :
			return False
	return True 
	
#####################################################	
# obtenir l address depuis un nom
######################################################
def address(name,register) :
	if register.get(namehash(name.lower())) != None :
		return register.get(namehash(name.lower()))['workspace_contract']
	else :
		return None
	

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
	

#################################################
#  ajoute une address du registre
#################################################
# le registre est un dict {hashname : workspace_contract}

def addName(username, email, workspace_contract,mode) :
	
	did='did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]
	mode.register[namehash(username.lower())]={ 'username' : username, 'email_authentification' : email, 'workspace_contract' : workspace_contract, 'resolver' : mode.server+'resolver/api/'+did, 'resume' : mode.server+"talao/api/resume/"+ did}	
	try : 
		myfile=open(mode.BLOCKCHAIN+'_register.json', 'w') 
	except IOError :
		print('IOError ; impossible de stocker le fichier')
		return False
	json.dump(mode.register, myfile)
	myfile.close()
	return True


#################################################
#  efface une address du registre
#################################################
# le registre est un dict {hashname : workspace_contract}

def deleteName(name, mode) :
	
	del mode.register[namehash(name.lower())]
	try : 
		myfile=open(mode.BLOCKCHAIN+'_register.json', 'w') 
	except IOError :
		print('IOError ; impossible de stocker le fichier')
		return False
	json.dump(mode.register, myfile)
	myfile.close()
	return True




