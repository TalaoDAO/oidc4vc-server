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
from protocol import  ownersToContracts, token_transfer, createVaultAccess, ether_transfer, add_key, partnershiprequest, authorize_partnership
import ns
import privatekey
#import ethereum_bridge see later



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
	if not receipt['status'] :
		print('Failed transaction addClaim for email')
		return False

	if mode.test :
		print ('email claim Id = ', claim_id)
		print('email 2 transaction hash = ', transaction_hash)

	return True

def create_user(username, email,mode, creator=None, partner=False, send_email=True):
	email = email.lower()
	# Setup owner Wallet
	account = mode.w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530'+email)
	address = account.address
	private_key = account.privateKey.hex()
	print('user address = ', address)
	print('user private key = ', private_key)

	# create RSA key as derivative from Ethereum private key
	RSA_key, RSA_private, RSA_public = privatekey.create_rsa_key(private_key, mode)

	# store RSA key in file ./RSA_key/rinkeby, talaonet ou ethereum
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+str(address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	try :
		file = open(filename,"wb")
		file.write(RSA_private)
		file.close()
		print('RSA key stored on disk')
	except :
		print('Failed, RSA key not stored on disk')

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

	# Identity setup
	contract = mode.w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
	nonce = mode.w3.eth.getTransactionCount(address)
	txn = contract.functions.createWorkspace(1001,1,1,RSA_public, AES_encrypted , SECRET_encrypted, bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 7500000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if not receipt['status'] :
		print('Failed transaction createWorkspace')
		return None, None, None

	# workspace_contract address to be read in fondation smart contract
	workspace_contract = ownersToContracts(address,mode)
	print('workspace_contract has been setup = ',workspace_contract)

	# add username to register in local nameservice Database with last check
	if ns.username_exist(username, mode) :
		username = username + str(random.randint(1, 100))
	ns.add_identity(username, workspace_contract, email, mode)

	# key 1 issued to Web Relay to act as agent.
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode, synchronous=True)

	# key 5 to Talao be in  White List
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 5, mode, synchronous=True)

	# key 20002 to Talao to Issue Proof of Identity
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 20002 , mode, synchronous=True)

	# Creator
	if creator and creator != mode.owner_talao :
		creator_address = creator
		creator_workspace_contract = ownersToContracts(creator_address, mode)
		creator_rsa_key = privatekey.get_key(creator, 'rsa_key', mode)
		creator_private_key = privatekey.get_key(creator,'private_key', mode)
		# setup partnership
		if partner  :
			# creator requests partnership
			if partnershiprequest(creator_address, creator_workspace_contract, creator_address, creator_workspace_contract, creator_private_key, workspace_contract, creator_rsa_key, mode, synchronous= True) :
				if authorize_partnership(address, workspace_contract, address, workspace_contract, private_key, creator_workspace_contract, RSA_private, mode, synchronous = True) :
					print('partnership request from creator has been accepted by Identity')
				else :
					print('authorize partnership with creator failed')
			else :
				print('creator partnership request failed')
		#add creator as referent
		if add_key(address, workspace_contract, address, workspace_contract, private_key, creator, 20002 , mode, synchronous=True) :
			print('key 20002 issued for creator')
		else :
			print('key 20002 for creator failed')
	else :
		print('no company creator')

	# rewrite privious email with scheme 2 in order to get an encrypted email on Blockchain
	email2(address, workspace_contract, private_key, email, AES_key, mode)

	# emails send to user and admin
	if mode.myenv == 'aws' or True:
		Talao_message.messageLog("no lastname", "no firstname", username, email, "createidentity.py", address, private_key, workspace_contract, "", email, SECRET_key.hex(), AES_key.hex(), mode)
		# By default an email is sent to user
		if send_email :
			Talao_message.messageUser("no lastname", "no fistname", username, email, address, private_key, workspace_contract, mode)

	# store Ethereum private key in keystore
	if not privatekey.add_private_key(private_key, mode) :
		print('add private key in keystore failed')
		return None, None, None
	else :
		print('private key in keystore')

	# synchro with ICO token
	#ethereum_bridge.lock_ico_token(address, private_key)

	print("create identity process is OK and over")
	return address, private_key, workspace_contract
