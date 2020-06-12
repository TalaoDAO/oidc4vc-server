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
#import Talao_backend_transaction
import Talao_message
#import Talao_ipfs
import constante
import environment
from protocol import  ownersToContracts, token_transfer, createVaultAccess, ether_transfer, add_key
from protocol import addName

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

def creationworkspacefromscratch(username, email,mode): 
	
	w3 = mode.w3	
	email = email.lower()
	
	# open Talao_Identity.csv
	fname = mode.BLOCKCHAIN +"_Talao_Identity.csv"
	identityfile = open(fname, "a")
	writer = csv.writer(identityfile)
	
	# process duration
	time_debut = datetime.now()

	# check email
	#if not Talao_backend_transaction.canregister(email,mode) :
	#	print('email existant dans le backend')
	#	sys.exit()
	
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

	# new AES key , shared with partnership
	AES_key = get_random_bytes(16)	

	# Secret 
	SECRET_key = get_random_bytes(16)
	#SECRET = SECRET_key.hex()
	
	# AES key encrypted with RSA key
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted = cipher_rsa.encrypt(AES_key)
	
	# SECRET encrypted with RSA key 
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted = cipher_rsa.encrypt(SECRET_key)
	
	# Email encrypted with RSA Key
	bemail = bytes(email , 'utf-8')	
	email_encrypted = cipher_rsa.encrypt(bemail)
	print('email encrypted =' ,email_encrypted)
	
	# ether transfer from TalaoGen wallet
	hash1 = ether_transfer(address, mode.ether2transfer,mode)
	balance_avant = w3.eth.getBalance(address)/1000000000000000000
	
	# 101 Talao tokens transfer from TalaoGen wallet
	token_transfer(address,101,mode)
		
	# createVaultAccess call in the token
	createVaultAccess(address,private_key,mode)
	
	# workspace (Decentralized IDentity) setup
	contract = w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
	nonce = w3.eth.getTransactionCount(address)  
	txn = contract.functions.createWorkspace(1001,1,1,RSA_public, AES_encrypted , SECRET_encrypted, email_encrypted).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = w3.eth.account.signTransaction(txn,private_key)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)	
	
	# workspace_contract address to be read in fondation smart contract
	workspace_contract = ownersToContracts(address,mode)
	print('workspace_contract = ',workspace_contract)
	# issuer backend setup
	firstname = ""
	lastname = ""

	# management key(1) issued to Web Relay to act as agent.
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode, synchronous=True) 
	# rewrite email with scheme 2 to differenciate from freedapp email that are not encrypted
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address)  
	txn = contract.functions.addClaim(101109097105108,2,address, '', email_encrypted, "" ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = w3.eth.account.signTransaction(txn,private_key)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	email_transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
		
	# add username to register
	addName(username, address, workspace_contract, email, mode) 
	
	# emails send to user and admin
	status = " createidentity.py"
	Talao_message.messageLog(lastname, firstname, username, email, status, address, private_key, workspace_contract, "", email, SECRET_key.hex(), AES_key.hex(), mode)
	Talao_message.messageUser(lastname, firstname, username, email, address, private_key, workspace_contract, mode)	
	
	# process duration and cost
	time_fin = datetime.now()
	time_delta = time_fin-time_debut
	print('Durée des transactions = ', time_delta)
	balance_apres = w3.eth.getBalance(address)/1000000000000000000
	cost = balance_avant-balance_apres
	print('Cout des transactions =', cost)	

	# update of Talao_Identity.csv
	status = "createidentity.py, email crypté"
	writer.writerow(( datetime.today(),username,lastname, firstname, email, status, address, private_key, workspace_contract, "", email, SECRET_key.hex(), AES_key.hex(), cost) )
	identityfile.close()

	print("createidentity is OK")
	return True
