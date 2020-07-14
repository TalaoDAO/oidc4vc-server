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
import json
import random
from Crypto.Cipher import AES
from base64 import b64encode
from eth_account.messages import encode_defunct
from datetime import datetime, timedelta
from base64 import b64encode, b64decode

# import des fonctions custom
import Talao_message
from Talao_ipfs import ipfs_add, ipfs_get
import constante
import environment
from protocol import  ownersToContracts, token_transfer, createVaultAccess, ether_transfer, add_key
import ns
import privatekey

master_key = ""
salt = ""
Identity_store = 5

# deterministic RSA rand function
def my_rand(n):
    # kluge: use PBKDF2 with count=1 and incrementing salt as deterministic PRNG
    my_rand.counter += 1
    return PBKDF2(master_key, "my_rand:%d" % my_rand.counter, dkLen=n, count=1)


def email2(address, workspace_contract, private_key, email, AES_key, mode) :
	""" This function signs a claim with sheme 2 and an encrypted email with secret key. email  topicvalue = 101109097105108 """
	w3 = mode.w3
		
	# coder les datas
	bytesdatajson = bytes(json.dumps({'email' : email}), 'utf-8') # dict -> json(str) -> bytes
	header = b"header"
	cipher = AES.new(AES_key, AES.MODE_EAX) #https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html
	cipher.update(header)
	ciphertext, tag = cipher.encrypt_and_digest(bytesdatajson)
	json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
	json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, header, ciphertext, tag] ]
	dict_data = dict(zip(json_k, json_v))
	
	ipfs_hash = ipfs_add(dict_data)
	
	print('ipfs_hash email2 = ', ipfs_hash)	
	nonce = w3.eth.getTransactionCount(address)  
	
	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes('email', 'utf-8'), address, bytes(email, 'utf-8'), bytes(ipfs_hash, 'utf-8')])
	
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=private_key)
	signature = signed_message['signature']
	
	claim_id = w3.solidityKeccak(['address', 'uint256'], [address, 101109097105108]).hex()
	
	#transaction
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	txn = contract.functions.addClaim(101109097105108, 2, 	address, signature, bytes('secret', 'utf-8'),ipfs_hash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = w3.eth.account.signTransaction(txn,private_key)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	
	print ('email claim Id = ', claim_id)
	print('email 2 transaction hash = ', transaction_hash)
	
	return 

def create_user(username, email,mode): 
	
	w3 = mode.w3	
	email = email.lower()
	
	if ns.does_alias_exist(username)  :
		print('username already used')
		return None
	
	
	# process duration
	time_debut = datetime.now()
	
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
	txn = contract.functions.createWorkspace(1001,1,1,RSA_public, AES_encrypted , SECRET_encrypted, bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = w3.eth.account.signTransaction(txn,private_key)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)	
	
	# workspace_contract address to be read in fondation smart contract
	workspace_contract = ownersToContracts(address,mode)
	print('workspace_contract = ',workspace_contract)	

	# key(1) issued to Web Relay to act as agent.
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode, synchronous=True) 
	
	# key 5 to Talao as White List
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 5, mode, synchronous=True) 

	# rewrite email with scheme 2 to differenciate from freedapp email that are not encrypted
	email2(address, workspace_contract, private_key, email, AES_key, mode)
		
	# add username to register
	ns.add_identity(username, workspace_contract, email, mode)
	
	# emails send to user and admin
	status = " createidentity.py"
	Talao_message.messageLog("no lastname", "no firstname", username, email, status, address, private_key, workspace_contract, "", email, SECRET_key.hex(), AES_key.hex(), mode)
	Talao_message.messageUser("no lastname", "no fistname", username, email, address, private_key, workspace_contract, mode)	
	
	# process duration and cost
	time_fin = datetime.now()
	time_delta = time_fin-time_debut
	print('Durée des transactions = ', time_delta)
	balance_apres = w3.eth.getBalance(address)/1000000000000000000
	cost = balance_avant-balance_apres
	print('Cout des transactions =', cost)	

	# update private key.db
	data = { 'created' : datetime.today(),
			'username' : username,
			 'email' : email,
			 'address' : address,
			 'private_key' :private_key,
			 'workspace_contract' : workspace_contract,
			 'secret' : SECRET_key.hex(),
			 'aes' : AES_key.hex()}
			 
	execution =  privatekey.add_identity(data)
	print('save db = ', execution)
	print("createidentity is OK")
	return address, private_key, workspace_contract
