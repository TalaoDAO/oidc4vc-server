"""
Pour la cration d'un workspace vierge depuis une page html

"""
import sys
import csv
from Crypto.Protocol.KDF import PBKDF2
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import http.client
import json
from datetime import datetime

# import des fonctions custom
import Talao_token_transaction
import Talao_backend_transaction
import Talao_message
import Talao_ipfs
import nameservice
import constante
import addclaim

password = "suc2cane"
master_key = ""
salt = ""


# deterministic RSA rand function
def my_rand(n):
    # kluge: use PBKDF2 with count=1 and incrementing salt as deterministic PRNG
    my_rand.counter += 1
    return PBKDF2(master_key, "my_rand:%d" % my_rand.counter, dkLen=n, count=1)



############################################
# Creation d'un workspace from scratch
############################################

def creationworkspacefromscratch(firstname, name, _email,mode): 
	w3=mode.initProvider()
	
	email=_email.lower()
	
	# Ouverture du fichier d'archive Talao_Identity.csv
	fname= mode.BLOCKCHAIN +"_Talao_Identity.csv"
	identityfile = open(fname, "a")
	writer = csv.writer(identityfile)
	
	# calcul du temps de process
	time_debut=datetime.now()

	# check de l email
	if Talao_backend_transaction.canregister(email,mode) == False :
		print('email existant dans le backend')
		sys.exit()
	
	# creation de la wallet	
	account = w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530'+email)
	address=account.address
	private_key=account.privateKey.hex()
	
	# création de la cle RSA (bytes) aleatoire, des cle public et privées
	#RSA_key = RSA.generate(2048)
	#RSA_private = RSA_key.exportKey('PEM')
	#RSA_public = RSA_key.publickey().exportKey('PEM')

	# création de la cle RSA (bytes) deterministic
	# https://stackoverflow.com/questions/20483504/making-rsa-keys-from-a-password-in-python
	global salt
	global master_key
	salt = private_key
	master_key = PBKDF2(password, salt, count=10000)  # bigger count = better
	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
	RSA_private = RSA_key.exportKey('PEM')
	RSA_public = RSA_key.publickey().exportKey('PEM')

	# stockage de la cle privée RSA dans un fichier du repertoire ./RSA_key/rinkeby ou ethereum
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+str(address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	fichier=open(filename,"wb")
	fichier.write(RSA_private)
	fichier.close()   

	# création de la cle AES
	AES_key = get_random_bytes(16)	

	# création du Secret
	SECRET_key = get_random_bytes(16)
	SECRET=SECRET_key.hex()
	
	# encryption de la cle AES avec la cle RSA
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted=cipher_rsa.encrypt(AES_key)
	
	# encryption du SECRET avec la cle RSA 
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted=cipher_rsa.encrypt(SECRET_key)
	
	# Transaction pour le transfert des ethers depuis le portfeuille TalaoGen
	hash1=Talao_token_transaction.ether_transfer(address, mode.ether2transfer,mode)
	balance_avant=w3.eth.getBalance(address)/1000000000000000000
	print('balance avant', balance_avant)
	
	# Transaction pour le transfert de 100 tokens Talao depuis le portfeuille TalaoGen
	hash2=Talao_token_transaction.token_transfer(address,100,mode)
	
	
	# Transaction pour l'acces dans le token Talao par createVaultAccess
	hash3=Talao_token_transaction.createVaultAccess(address,private_key,mode)
	
	
	# Transaction pour la creation du workspace :
##### email non crypté !!!!
	bemail=bytes(email , 'utf-8')	
	hash4=Talao_token_transaction.createWorkspace(address,private_key,RSA_public,AES_encrypted,SECRET_encrypted,bemail,mode)

	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract=Talao_token_transaction.ownersToContracts(address,mode)
	
	# Transaction pour la creation du compte sur le backend HTTP POST
	backend_Id = Talao_backend_transaction.backend_register(address,workspace_contract,firstname, name, email, SECRET,mode)

	# ajout de l email dans register en memoire et dans le fichier
	mode.register[nameservice.namehash(email)]=workspace_contract
	try : 
		myfile=open(mode.BLOCKCHAIN+'_register.json', 'w') 
	except IOError :
		print('impossible de stocker le fichier')
		return False
	json.dump(mode.register, myfile)
	myfile.close()
	
	# envoi du message de log
	status="from website /talao/register/"
	Talao_message.messageLog(name, firstname, email,status,address, private_key, workspace_contract, backend_Id, email, SECRET, AES_key,mode)
	
	# envoi du message user
	Talao_message.messageUser(name, firstname, email,address, private_key, workspace_contract, mode)
	
	# ajout du nom et prenom
	#givenName = 103105118101110078097109101
	#familyName = 102097109105108121078097109101
	addclaim.addClaim(workspace_contract, address,private_key, "familyName", address, name, "",mode)
	addclaim.addClaim(workspace_contract, address,private_key, "givenName", address, firstname, "",mode)
	
	#ajout d'un cle 3 a la fondation
	owner_foundation = mode.foundation_address	       
	#envoyer la transaction sur le contrat
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token . Ici le owner
	nonce = w3.eth.getTransactionCount(address)  
	# calcul du keccak
	_key=w3.soliditySha3(['address'], [owner_foundation])
	# Build transaction
	txn = contract.functions.addKey(_key, 3, 1).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	#sign transaction
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1)		
	
	
	#ajout d'un cle 3 a Talao
	owner_talao = mode.owner_talao	       
	#envoyer la transaction sur le contrat
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token . Ici le owner
	nonce = w3.eth.getTransactionCount(address)  
	# calcul du keccak
	_key=w3.soliditySha3(['address'], [owner_talao])
	# Build transaction
	txn = contract.functions.addKey(_key, 3, 1).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	#sign transaction
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1)		
	
	
	# calcul de la duree de transaction et du cout
	time_fin=datetime.now()
	time_delta=time_fin-time_debut
	print('Durée des transactions = ', time_delta)
	balance_apres=w3.eth.getBalance(address)/1000000000000000000
	cost=balance_avant-balance_apres
	print('Cout des transactions =', cost)	


	# mise a jour du fichier archive Talao_Identity.csv
	status="website /talao/register/"
	writer.writerow(( datetime.today(),name, firstname, email,status,address, private_key, workspace_contract, backend_Id, email, SECRET, AES_key,cost) )
	identityfile.close()

	print("createidentity is OK")
	return address, private_key, SECRET, workspace_contract,backend_Id, email, SECRET, AES_key
