"""
Pour la cration d'un workspace vierge depuis le webserver
email est gardé uniquement pour l authentification, il n est pas affiché
Pour nameservice on y met "prenom.nom" ou un equivalent
une cle 1 est donnée au Web Relay pour uen délégation de signature


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
from protocol import Identity, addclaim, ownersToContracts, token_transfer, createVaultAccess, ether_transfer, createWorkspace, partnershiprequest, authorizepartnership, addkey
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

def creationworkspacefromscratch(username, _email,mode): 
	
	w3 = mode.w3	
	email =_email.lower()
	
	# open Talao_Identity.csv
	fname = mode.BLOCKCHAIN +"_Talao_Identity.csv"
	identityfile = open(fname, "a")
	writer = csv.writer(identityfile)
	
	# process duration
	time_debut = datetime.now()

	# check email
	if not Talao_backend_transaction.canregister(email,mode) :
		print('email existant dans le backend')
		sys.exit()
	
	# user wallet 
	account = w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530'+email)
	address = account.address
	private_key = account.privateKey.hex()
	
	# deterministic RSA key
	# https://stackoverflow.com/questions/20483504/making-rsa-keys-from-a-password-in-python 
	global salt
	global master_key
	salt = private_key
	master_key = PBKDF2(mode.password, salt, count=10000)  # bigger count = better
	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
	RSA_private = RSA_key.exportKey('PEM')
	RSA_public = RSA_key.publickey().exportKey('PEM')

	# store RSA private key in file ./RSA_key/rinkeby ou ethereum
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+str(address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	fichier = open(filename,"wb")
	fichier.write(RSA_private)
	fichier.close()   

	# new AES key
	AES_key = get_random_bytes(16)	

	# Secret = backend password
	SECRET_key = get_random_bytes(16)
	SECRET = SECRET_key.hex()
	
	# AES key encrypted with RSA key
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted = cipher_rsa.encrypt(AES_key)
	
	# SECRET encrypted with RSA key 
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted = cipher_rsa.encrypt(SECRET_key)
	
	# ether transfer from TalaoGen wallet
	hash1 = ether_transfer(address, mode.ether2transfer,mode)
	balance_avant = w3.eth.getBalance(address)/1000000000000000000
	
	# 100 Talao tokens transfer from TalaoGen wallet
	token_transfer(address,101,mode)
		
	# createVaultAccess call in the token
	createVaultAccess(address,private_key,mode)
	
	# workspace (Decentralized IDentity) setup
	# email is not encrypted !!!! to do..........................
	bemail = bytes(email , 'utf-8')	
	createWorkspace(address, private_key, RSA_public, AES_encrypted, SECRET_encrypted, bemail, mode)
	
	# workspace_contract address to be read in fondation smart contract
	workspace_contract = ownersToContracts(address,mode)
	print('workspace_contract = ',workspace_contract)
	# issuer backend setup
	firstname = ""
	lastname = ""
	backend_Id = Talao_backend_transaction.backend_register(address,workspace_contract,firstname, lastname, email, SECRET,mode)
	
	# user instanciation
	user = Identity(workspace_contract,mode, private_key=private_key,SECRET=SECRET, AES_key=AES_key, backend_Id=backend_Id, rsa_key=RSA_private ) 

	# emails send to user and admin
	status = " createidentity.py"
	Talao_message.messageLog(lastname, firstname, user.username, user.email, status, user.address, user.private_key, user.workspace_contract, user.backend_Id, user.email, user.SECRET, user.AES_key,mode)
	Talao_message.messageUser(lastname, firstname, user.username, user.email, user.address, user.private_key, user.workspace_contract, mode)	

	# management key issued to Web Relay
	addkey(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode, synchronous=True) 
	
	# partnership request to Talao A confirmer l interet de faire ça.
	user.requestPartnership(mode.workspace_contract_talao)	
	# start of Talao task ...........................................to be removed
	fichiercsv = mode.BLOCKCHAIN+'_Talao_Identity.csv'
	csvfile = open(fichiercsv,newline='')
	reader = csv.DictReader(csvfile) 
	for row in reader:
		if row['workspace_contract'] == mode.workspace_contract_talao :
			private_key_talao = row['private_key']			
	csvfile.close()	
	# talao partnership authorization
	authorizepartnership(workspace_contract, workspace_contract_talao, private_key_talao,mode) 
	# end of talao task ...............................................................
	
	# process duration and cost
	time_fin = datetime.now()
	time_delta = time_fin-time_debut
	print('Durée des transactions = ', time_delta)
	balance_apres = w3.eth.getBalance(address)/1000000000000000000
	cost = balance_avant-balance_apres
	print('Cout des transactions =', cost)	

	# update of Talao_Identity.csv
	status = "createidentity.py"
	writer.writerow(( datetime.today(),user.username,lastname, firstname, user.email, status, user.address, private_key, user.workspace_contract, user.backend_Id, user.email, user.SECRET, user.AES_key,cost) )
	identityfile.close()

	print("createidentity is OK")
	return True
