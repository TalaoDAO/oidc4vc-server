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
import threading

# import des fonctions custom
import Talao_message
from Talao_ipfs import ipfs_add, ipfs_get
import constante
from protocol import  ownersToContracts, token_transfer, createVaultAccess, ether_transfer, add_key, partnershiprequest, authorize_partnership
from protocol import Claim, update_self_claims
import ns
import privatekey

exporting_threads = {}

# Multithreading creatidentity setup
class ExportingThread(threading.Thread):
	def __init__(self, address, workspace_contract, private_key, username, email, mode, creator, partner, send_email,) :
		super().__init__()
		self.username = username
		self.email = email
		self.send_email = send_email
		self.mode = mode
		self.creator = creator
		self.partner = partner
		self.address = address
		self.workspace_contract = workspace_contract
		self.private_key = private_key

	def run(self):
		_create_user_step_2(self.address, self.workspace_contract, self.private_key, self.username, self.email, self.mode, self.creator, self.partner, self.send_email)
		return


# main function called by external modules
def create_user(username, email, mode, creator=None, wallet=False, partner=False, send_email=True, password=None, firstname=None,  lastname=None, phone=None, is_thread=True):
	"""
	is_thread :bool, by default partly an async task.

	"""

	# step 1, thus step is synchronous
	address, private_key, workspace_contract = _create_user_step_1(username, email, mode, creator, partner, send_email, password, firstname,  lastname, phone, wallet)
	if not address :
		return None, None, None

	# Step 2 : this step maybe asynchronous
	if is_thread :
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(address, workspace_contract, private_key, username, email, mode, creator, partner, send_email)
		exporting_threads[thread_id].start()
	else :
		_create_user_step_2(address, workspace_contract, private_key, username, email, mode, creator, partner, send_email,)

	return address, private_key, workspace_contract


def _create_user_step_1(username, email,mode, creator, partner, send_email, password, firstname,  lastname, phone, wallet) :
	email = email.lower()
	# Setup owner Wallet
	account = mode.w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530'+email)
	address = account.address
	private_key = account.privateKey.hex()
	print('Success : user address = ', address)
	print('Success : user private key = ', private_key)

	# create RSA key as derivative from Ethereum private key
	RSA_key, RSA_private, RSA_public = privatekey.create_rsa_key(private_key, mode)

	# store RSA key in file ./RSA_key/rinkeby, talaonet ou ethereum
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+str(address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	try :
		file = open(filename,"wb")
		file.write(RSA_private)
		file.close()
		print('Success : RSA key stored on disk')
	except :
		print('Error : RSA key not stored on disk')

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
		print('Success : ether transfer hash ', hash)

	# Talao tokens transfer from TalaoGen wallet
	hash = token_transfer(address,mode.talao_to_transfer,mode)
	if mode.test :
		print('Success : token transfer hash ', hash)

	# CreateVaultAccess call in the token to declare the identity within the Talao Token smart contract
	hash = createVaultAccess(address,private_key,mode)
	if mode.test :
		print('Success : create vault acces hash ', hash)

	# Identity setup
	contract = mode.w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
	nonce = mode.w3.eth.getTransactionCount(address)
	txn = contract.functions.createWorkspace(1001,1,1,RSA_public, AES_encrypted , SECRET_encrypted, bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 7500000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if not receipt['status'] :
		print('Error : transaction createWorkspace failed')
		return None, None, None

	# workspace_contract address to be read in fondation smart contract
	workspace_contract = ownersToContracts(address,mode)
	print('Success : workspace_contract has been setup = ',workspace_contract)

	# add username to register in local nameservice Database with last check.....
	if ns.username_exist(username, mode) :
		username = username + str(random.randint(1, 100))
	ns.add_identity(username, workspace_contract, email, mode)

	# setup password
	if password :
		ns.update_password(username, password, mode)
		print('Success : password has been updated')

	# setup phone
	if phone :
		ns.update_phone(username, phone, mode)
		print('Success : phone has been updated')

	# store Ethereum private key in keystore
	if not privatekey.add_private_key(private_key, mode) :
		print('Error : add private key in keystore failed')
		return None, None, None
	else :
		print('Success : private key in keystore')

	# claims for firstname and lastname
	if firstname and lastname :
		if not update_self_claims(address, private_key, {'firstname': firstname, 'lastname' : lastname}, mode) :
			print('Error : firstname and lastname not updated')
		print('Success : firstname and lastname updated')

	# add wallet address in resolver
	if wallet :
		if ns.update_wallet(workspace_contract, wallet, mode) :
			print('Success : wallet updated')
		else :
			print('Error : wallet update failed')


	# key 1 issued to Web Relay to act as agent.
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode)

	print('Success : end of step 1 create identity')
	return address, private_key, workspace_contract


def _create_user_step_2(address, workspace_contract, private_key, username, email, mode, creator, partner, send_email,) :

	# key 5 to Talao be in  White List
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 5, mode)

	# key 20002 to Talao to Issue Proof of Identity
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 20002 , mode)

	# Creator management
	if creator and creator != mode.owner_talao :
		creator_address =creator
		creator_workspace_contract = ownersToContracts(creator_address, mode)
		creator_rsa_key = privatekey.get_key(creator_address, 'rsa_key', mode)
		creator_private_key = privatekey.get_key(creator_address,'private_key', mode)
		RSA_private = privatekey.get_key(address, 'rsa_key', mode)
		# setup partnership
		if partner  :
			# creator requests partnership
			if partnershiprequest(creator_address, creator_workspace_contract, creator_address, creator_workspace_contract, creator_private_key, workspace_contract, creator_rsa_key, mode) :
				if authorize_partnership(address, workspace_contract, address, workspace_contract, private_key, creator_workspace_contract, RSA_private, mode) :
					print('Success : partnership request from creator has been accepted by Identity')
				else :
					print('Error : authorize partnership with creator failed')
			else :
				print('Error : creator partnership request failed')
		#add creator as referent
		if add_key(address, workspace_contract, address, workspace_contract, private_key, creator, 20002 , mode) :
			print('Warning : key 20002 issued for creator')
		else :
			print('Warning : key 20002 for creator failed')
	else :
		print('Warning : no company creator')

	# rewrite previous email to get an encrypted email 
	if Claim().add(address,workspace_contract, address, workspace_contract,private_key, 'email', email, 'private', mode)[0] :
		print('Success : email encryted updated')
	else :
		print('Error : email encrypted not updated')

	# emails send to user and admin
	Talao_message.messageLog("no lastname", "no firstname", username, email, "createidentity.py", address, private_key, workspace_contract, "", email, "", "", mode)
	# By default an email is sent to user
	if send_email :
		Talao_message.messageUser("no lastname", "no fistname", username, email, address, private_key, workspace_contract, mode)

	print("Success : create identity process step 2 is over")
	return
