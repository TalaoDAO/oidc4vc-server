"""
Pour la cration d'un workspace vierge depuis le webserver
email est gardé uniquement pour l authentification, il n est pas affiché
Pour nameservice on y met "prenom.nom"


mise en place d'un partenariat avec Talao

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
import random

# import des fonctions custom
import Talao_backend_transaction
import Talao_message
import Talao_ipfs
import constante
import environment
from protocol import identity, addclaim, ownersToContracts, token_transfer, createVaultAccess, ether_transfer, createWorkspace, partnershiprequest, authorizepartnership
from protocol import addName, namehash

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

def creationworkspacefromscratch(firstname, lastname, _email,mode): 
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
	master_key = PBKDF2(mode.password, salt, count=10000)  # bigger count = better
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
	hash1=ether_transfer(address, mode.ether2transfer,mode)
	balance_avant=w3.eth.getBalance(address)/1000000000000000000
	
	# Transaction pour le transfert de 100 tokens Talao depuis le portfeuille TalaoGen
	token_transfer(address,100,mode)
		
	# Transaction pour l'acces dans le token Talao par createVaultAccess
	createVaultAccess(address,private_key,mode)
	
	# Transaction pour la creation du workspace :
	##### email non crypté !!!!
	bemail=bytes(email , 'utf-8')	
	createWorkspace(address,private_key,RSA_public,AES_encrypted,SECRET_encrypted,bemail,mode)
	
	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract=ownersToContracts(address,mode)
	
	# Transaction pour la creation du compte sur le backend HTTP POST
	backend_Id = Talao_backend_transaction.backend_register(address,workspace_contract,firstname, lastname, email, SECRET,mode)
	
	# update du user
	user=identity(workspace_contract,mode, SECRET=SECRET, AES_key=AES_key, private_key=private_key, backend_Id=backend_Id, email=email) 
	user.setFirstname(firstname)
	user.setLastname(lastname)
	user.setUsername(firstname.lower()+'.'+lastname.lower())	
	user.addToRegister()
	
	# envoi du message a l admin et au user
	status="webserver"
	Talao_message.messageLog(user.lastname, user.firstname, user.username, user.email,status,user.address, user.private_key, user.workspace_contract, user.backend_Id, user.email, user.SECRET, user.AES_key,mode)
	Talao_message.messageUser(user.lastname, user.firstname, user.username, user.email,user.address, user.private_key, user.workspace_contract, mode)
	
	# envoi d'un request partnership à Talao
	user.requestPartnership(mode.workspace_contract_talao)
	
	################################################ debut intervention de Talao ########################################
	# lecture de la private_key_talao
	fichiercsv=mode.BLOCKCHAIN+'_Talao_Identity.csv'
	csvfile = open(fichiercsv,newline='')
	reader = csv.DictReader(csvfile) 
	for row in reader:
		if row['workspace_contract'] == mode.workspace_contract_talao :
			private_key_talao= row['private_key']			
	csvfile.close()	
	# authorize request de Talao
	authorizepartnership(workspace_contract, workspace_contract_talao, private_key_talao,mode) 
	################################################ fin intervention de Talao ##########################################
	
	# calcul de la duree de transaction et du cout
	time_fin=datetime.now()
	time_delta=time_fin-time_debut
	print('Durée des transactions = ', time_delta)
	balance_apres=w3.eth.getBalance(address)/1000000000000000000
	cost=balance_avant-balance_apres
	print('Cout des transactions =', cost)	

	# mise a jour du fichier archive Talao_Identity.csv
	status="webserver"
	writer.writerow(( datetime.today(),user.username,user.lastname, user.firstname, user.email,status,user.address, user.private_key, user.workspace_contract, user.backend_Id, user.email, user.SECRET, user.AES_key,cost) )
	identityfile.close()

	print("createidentity is OK")
	user.printIdentity()
	return user
