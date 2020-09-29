"""
Pour la cration d'un workspace vierge Identity) depuis le webserver :
Creation d' un wallet pour le owner
Creation des cle de cyryptage : 1 RSA (asymetric) , et 2 cle symetriques 
L email est gardé uniquement pour l authentification, il est crypté dans l identité
Pour la base SQL (nameservice) on y met "prenom.nom" ou un equivalent
une cle 1 (ERC725) est donnée au Web Relay pour uen délégation de signature
un cle 20002 est donné a Talao pour emettre des documents et e particulier le proof of identity
une cle 5 est donnée a Talao pour etre ddans al whitelist
La cle privée de l identité est sauvergaée dans private.key.db

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
from protocol import  ownersToContracts, token_transfer, createVaultAccess, ether_transfer, add_key
import ns
import privatekey

# Gloval variables for RSA algo
master_key = ""
salt = ""
#Identity_store = 5

# deterministic rand function for RSA setup
def my_rand(n):
    """ use of kluge: use PBKDF2 with count=1 and incrementing salt as deterministic PRNG """
    my_rand.counter += 1
    return PBKDF2(master_key, "my_rand:%d" % my_rand.counter, dkLen=n, count=1)

def email2(address, workspace_contract, private_key, email, AES_key, mode) :
	""" This function signs a claim with sheme #2 and store an encrypted email with secret key (topicvalue = 101109097105108 """
	
	
	# encrypts email cf algo https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html
	bytesdatajson = bytes(json.dumps({'email' : email}), 'utf-8') # dict -> json(str) -> bytes
	header = b"header"
	cipher = AES.new(AES_key, AES.MODE_EAX) 
	cipher.update(header)
	ciphertext, tag = cipher.encrypt_and_digest(bytesdatajson)
	json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
	json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, header, ciphertext, tag] ]
	dict_data = dict(zip(json_k, json_v))

	# store email on IPFS
	ipfs_hash = ipfs_add(dict_data,mode)
	if mode.test :
		print('ipfs_hash email2 = ', ipfs_hash)	
	
	# Signature
	nonce = mode.w3.eth.getTransactionCount(address)  
	msg = mode.w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes('email', 'utf-8'), address, bytes(email, 'utf-8'), bytes(ipfs_hash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = mode.w3.eth.account.sign_message(message, private_key=private_key)
	signature = signed_message['signature']
	claim_id = mode.w3.solidityKeccak(['address', 'uint256'], [address, 101109097105108]).hex()
	
	# Transaction
	contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	txn = contract.functions.addClaim(101109097105108, 2, 	address, signature, bytes('secret', 'utf-8'),ipfs_hash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if receipt['status'] == 0 :
		print('Failed transaction addClaim for email')
		return False	
	
	if mode.test :
		print ('email claim Id = ', claim_id)
		print('email 2 transaction hash = ', transaction_hash)
	
	return True

def create_user(username, email,mode): 
	""" Create Identity """
	
	email = email.lower()
	
	if ns.does_alias_exist(username,mode)  :
		print('username already used')
		return None, None, None
	
	# Setup owner Wallet 
	account = mode.w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530'+email)
	address = account.address
	private_key = account.privateKey.hex()
	if mode.test :
		print('user address = ', address)
		print('user private key = ', private_key)
	
	# deterministic RSA key https://stackoverflow.com/questions/20483504/making-rsa-keys-from-a-password-in-python 
	global salt
	global master_key
	salt = private_key
	master_key = PBKDF2(mode.password, salt, count=10000)  # bigger count = better
	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
	RSA_private = RSA_key.exportKey('PEM')
	RSA_public = RSA_key.publickey().exportKey('PEM')

	# store RSA key in file ./RSA_key/rinkeby, talaonet ou ethereum
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+str(address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	fichier = open(filename,"wb")
	fichier.write(RSA_private)
	fichier.close()   

	# Keys for encryption
	# Setup a key (symetric) named 'AES' to encrypt private data and to be shared with partnership
	AES_key = get_random_bytes(16)	
	# Setup another key named 'SECRET' (symetric) to encrypt secret data
	SECRET_key = get_random_bytes(16)
	
	# AES key encrypted with RSA key
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted = cipher_rsa.encrypt(AES_key)
	
	# SECRET encrypted with RSA key 
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted = cipher_rsa.encrypt(SECRET_key)
	
	# Email encrypted with RSA Key
	bemail = bytes(email , 'utf-8')	
	
	# Ether transfer from TalaoGen wallet
	hash = ether_transfer(address, mode.ether2transfer,mode)
	if mode.test :
		print('ether transfer hash ', hash)

	# Talao tokens transfer from TalaoGen wallet
	hash = token_transfer(address,mode.talao_to_transfer,mode)
	if mode.test :
		print('token transfer hash ', hash)
		
	# CreateVaultAccess call in the token to declare the identity within the Talao Token smart contract
	hash = createVaultAccess(address,private_key,mode)
	if mode.test :
		print('create vault acces hash ', hash)

	# Identity setup , Identity is named "Workspace"
	contract = mode.w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
	nonce = mode.w3.eth.getTransactionCount(address)  
	txn = contract.functions.createWorkspace(1001,1,1,RSA_public, AES_encrypted , SECRET_encrypted, bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 7500000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)	
	if receipt['status'] == 0 :
		print('Failed transaction createWprkspace')
		return None, None, None

	# workspace_contract address to be read in fondation smart contract
	workspace_contract = ownersToContracts(address,mode)
	if mode.test :
		print('workspace_contract has been setup = ',workspace_contract)	

	#ERC725 keys
	# key 1 issued to Web Relay to act as agent.
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode, synchronous=True) 
	# key 5 to Talao as White List
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 5, mode, synchronous=True) 
	# key 20002 to Talao to Issue Proof of Identity
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 20002 , mode, synchronous=True) 

	# rewrite email with scheme 2 to be encrypted
	email2(address, workspace_contract, private_key, email, AES_key, mode)
		
	# add username to register sql database
	ns.add_identity(username, workspace_contract, email, mode)
	
	# emails send to user and admin
	status = " createidentity.py"
	#Talao_message.messageLog("no lastname", "no firstname", username, email, status, address, private_key, workspace_contract, "", email, SECRET_key.hex(), AES_key.hex(), mode)
	#Talao_message.messageUser("no lastname", "no fistname", username, email, address, private_key, workspace_contract, mode)	
	
	# update private key.db
	data = { 'created' : datetime.today(),
			'username' : username,
			 'email' : email,
			 'address' : address,
			 'private_key' :private_key,
			 'workspace_contract' : workspace_contract,
			 'secret' : SECRET_key.hex(),
			 'aes' : AES_key.hex()}
			 
	if not privatekey.add_identity(data, mode) :
		print('update private key failed')
		return None, None, None

	if mode.test :
		print("createidentity is OK")
	return address, private_key, workspace_contract
