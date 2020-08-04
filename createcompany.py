"""
Toutes les company sont crées par Talao et signées par Talao

les company ne sont pas enregistrées dans le backend de l issuer

un cle de type 1 et crée pour Talao qui signe les transactions initiales.


"""


import sys
import csv
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Protocol.KDF import PBKDF2
import json
from eth_account.messages import encode_defunct
from Crypto.Cipher import AES
from base64 import b64encode
from datetime import datetime, timedelta
from base64 import b64encode, b64decode


# dependances
from protocol import ether_transfer, ownersToContracts, token_transfer, createVaultAccess, add_key
from Talao_ipfs import ipfs_add, ipfs_get
import constante
#import environment
import ns
import privatekey


# variable pour calcul RSA
master_key = ""
salt = ""



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

def _createWorkspace(address,private_key,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail,mode) :	
	w3 = mode.w3
	
	contract=w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)

	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(address)  

	# Build transaction
	txn=contract.functions.createWorkspace(2001,1,1,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)	
	return hash

# deterministic RSA rand function
def my_rand(n):
    # kluge: use PBKDF2 with count=1 and incrementing salt as deterministic PRNG
    my_rand.counter += 1
    return PBKDF2(master_key, "my_rand:%d" % my_rand.counter, dkLen=n, count=1)


def create_company(email, username, mode) :
	
	w3 = mode.w3
	
	if ns.does_alias_exist(username, mode)  :
		print('username already used')
		return None
	 
	# calcul du temps de process
	#time_debut=datetime.now()
	
	# creation de la wallet	
	account = w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
	address = account.address
	private_key = account.privateKey.hex()
	print('adresse = ', address)
	print('private key = ', private_key)
	
	# création de la cle RSA (bytes) deterministic
	# https://stackoverflow.com/questions/20483504/making-rsa-keys-from-a-password-in-python
	global salt
	global master_key
	salt = private_key
	password = mode.password
	master_key = PBKDF2(password, salt, count=10000)  # bigger count = better
	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
	RSA_private = RSA_key.exportKey('PEM')
	RSA_public = RSA_key.publickey().exportKey('PEM')

	# stockage de la cle privée RSA dans un fichier du repertoire ./RSA_key/rinkeby ou ethereum
	filename = "./RSA_key/" + mode.BLOCKCHAIN + '/'+ str(address) + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	fichier=open(filename,"wb")
	fichier.write(RSA_private)
	fichier.close()   

	# création de la cle AES
	AES_key = get_random_bytes(16)	

	# création du Secret
	SECRET_key = get_random_bytes(16)
	SECRET=SECRET_key.hex()
	print('SECRET = ', SECRET)
	
	# encryption de la cle AES avec la cle RSA
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted=cipher_rsa.encrypt(AES_key)
	
	# encryption du SECRET avec la cle RSA 
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted=cipher_rsa.encrypt(SECRET_key)
	
	# Email 
	bemail = bytes(email , 'utf-8')	
	
	# Transaction pour le transfert de 0.06 ethers depuis le portfeuille TalaoGen
	hash1 = ether_transfer(address, 60,mode)
	print('hash de transfert de 0.06 eth = ',hash1)
	
	# Transaction pour le transfert de 101 tokens Talao depuis le portfeuille TalaoGen
	hash2 = token_transfer(address, 101, mode)
	print('hash de transfert de 101 TALAO = ', hash2)
	
	# Transaction pour l'acces dans le token Talao par createVaultAccess
	hash3=createVaultAccess(address, private_key, mode)
	print('hash du createVaultaccess = ', hash3)
	
	# Transaction pour la creation du workspace :
	bemail = bytes(email , 'utf-8')	
	hash4 =_createWorkspace(address, private_key, RSA_public, AES_encrypted, SECRET_encrypted, bemail, mode)
	print('hash de createWorkspace =', hash4)

	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract = ownersToContracts(address, mode)
	print( 'workspace contract = ', workspace_contract)
	
	# management key (1) issued to Relay 
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode, synchronous=True) 

	# rewrite encrypted email with scheme 2 to differenciate from freedapp email that are not encrypted
	email2(address, workspace_contract, private_key, email, AES_key, mode)
	
	# key 20002 to Talao to Issue Proof of Identity
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 20002 , mode, synchronous=True) 

	# update resolver and create local database
	ns.add_identity(username, workspace_contract, email, mode)
	ns.init_host(username, mode)
	
	# Delay and transaction cost
	#time_fin = datetime.now()
	#time_delta = time_fin-time_debut
	#a = w3.eth.getBalance(address)
	#cost=0.06-a/1000000000000000000	
	
	# update private key.db
	data = { 'created' : datetime.today(),
			'username' : username,
			 'email' : email,
			 'address' : address,
			 'private_key' :private_key,
			 'workspace_contract' : workspace_contract,
			 'secret' : SECRET.hex(),
			 'aes' : AES_key.hex()}
			 
	execution =  privatekey.add_identity(data, mode)
	print('save db = ', execution)


	return address, private_key, workspace_contract
