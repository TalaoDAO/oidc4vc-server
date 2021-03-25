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
from datetime import datetime, timedelta
from base64 import b64encode, b64decode
import threading
import logging

logging.basicConfig(level=logging.INFO)

from signaturesuite import RsaSignatureSuite2017

# import des fonctions custom
import constante
from protocol import  ownersToContracts, token_transfer, createVaultAccess, ether_transfer, add_key, partnershiprequest, authorize_partnership
from protocol import Claim, update_self_claims
from components import privatekey, ns, Talao_message

exporting_threads_all = {}
exporting_threads = {}


# Multithreading creatidentity setup for step 1 and 2 asynchronous
class ExportingThread_all(threading.Thread):
	def __init__(self, username, email, mode, creator=None, wallet=None, partner=False, send_email=True, password=None, firstname=None,  lastname=None, phone=None,) :
		super().__init__()
		self.username = username
		self.email = email
		self.send_email = send_email
		self.mode = mode
		self.firstname = firstname
		self.lastname = lastname
		self.creator = creator
		self.partner = partner
		self.phone = phone
		self.password=password
		self.wallet = wallet
	def run(self):
		address, private_key, workspace_contract = _create_user_step_1(self.username, self.email, self.mode, self.creator, self.partner, self.send_email, self.password, self.firstname,  self.lastname, self.phone, self.wallet)
		if not address :
			return None, None, None
		_create_user_step_2(address, workspace_contract, private_key, self.username, self.firstname, self.lastname, self.email, self.mode, self.creator, self.partner, self.send_email)
		return  address, private_key, workspace_contract


# Multithreading creatidentity setup for step 2 only
class ExportingThread(threading.Thread):
	def __init__(self, address, workspace_contract, private_key, username, firstname, lastname, email, mode, creator, partner, send_email,) :
		super().__init__()
		self.username = username
		self.email = email
		self.send_email = send_email
		self.firstname = firstname
		self.lastname = lastname
		self.mode = mode
		self.creator = creator
		self.partner = partner
		self.address = address
		self.workspace_contract = workspace_contract
		self.private_key = private_key
	def run(self):
		_create_user_step_2(self.address, self.workspace_contract, self.private_key, self.username, self.firstname, self.lastname, self.email, self.mode, self.creator, self.partner, self.send_email)
		return


# main function called by external modules
def create_user(username, email, mode, creator=None, wallet=None, partner=False, send_email=True, password=False, firstname=None,  lastname=None, phone=None, is_thread=True, is_all_thread=False):
	"""
	is_thread :bool, by default partly an async task.

	"""
	# step 1 and 2 asynchronous (create person)
	if is_all_thread :
		thread_id_all = str(random.randint(0,10000 ))
		exporting_threads_all[thread_id_all] = ExportingThread_all(username, email, mode, creator, wallet, partner, send_email, password, firstname,  lastname, phone)
		#address, private_key, workspace_contract = exporting_threads_all[thread_id_all].start()
		exporting_threads_all[thread_id_all].start()
		return
	else :
		# step 1, is always synchronous
		address, private_key, workspace_contract = _create_user_step_1(username, email, mode, creator, partner, send_email, password, firstname,  lastname, phone, wallet)
		if not address :
			return None, None, None
		# Step 2 : this step maybe asynchronous
		if is_thread :
			thread_id = str(random.randint(0,10000 ))
			exporting_threads[thread_id] = ExportingThread(address, workspace_contract, private_key, username, firstname, lastname, email, mode, creator, partner, send_email)
			exporting_threads[thread_id].start()
		else :
			_create_user_step_2(address, workspace_contract, private_key, username, firstname, lastname, email, mode, creator, partner, send_email,)
		return address, private_key, workspace_contract


def _create_user_step_1(username, email,mode, creator, partner, send_email, password, firstname,  lastname, phone, wallet) :
	email = email.lower()
	# Setup owner Wallet
	account = mode.w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530'+email)
	address = account.address
	private_key = account.key.hex()

	# create RSA key as derivative from Ethereum private key
	RSA_key, RSA_private, RSA_public = privatekey.create_rsa_key(private_key, mode)

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
	logging.info('ether transfer hash = %s', hash)

	# Talao tokens transfer from TalaoGen wallet
	hash = token_transfer(address,mode.talao_to_transfer,mode)
	logging.info('token transfer hash = %s', hash)

	# CreateVaultAccess call in the token to declare the identity within the Talao Token smart contract
	hash = createVaultAccess(address,private_key,mode)
	logging.info('create vault acces hash = %s', hash)

	# Identity setup
	contract = mode.w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
	nonce = mode.w3.eth.getTransactionCount(address)
	txn = contract.functions.createWorkspace(1001,1,1,RSA_public, AES_encrypted , SECRET_encrypted, bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 7500000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if not receipt['status'] :
		logging.info('transaction createWorkspace failed')
		return None, None, None

	# workspace_contract address to be read in fondation smart contract
	workspace_contract = ownersToContracts(address,mode)
	logging.info('workspace_contract has been setup = %s',workspace_contract)

	# store RSA key in file ./RSA_key/rinkeby, talaonet ou ethereum
	filename = "./RSA_key/" + mode.BLOCKCHAIN + '/did:talao:' + mode.BLOCKCHAIN + ':'  + workspace_contract[2:] + ".pem"
	try :
		file = open(filename,"wb")
		file.write(RSA_private)
		file.close()
		logging.info('RSA key stored on disk')
	except :
		logging.error('RSA key not stored on disk')

	# add username to register in local nameservice Database with last check.....
	if ns.username_exist(username, mode) :
		username = username + str(random.randint(1, 100))
	ns.add_identity(username, workspace_contract, email, mode)

	# setup password
	if password :
		ns.update_password(username, password, mode)
		logging.info('password has been updated')

	# setup phone
	if phone :
		ns.update_phone(username, phone, mode)
		logging.info('phone has been updated')

	# store Ethereum private key in keystore
	if not privatekey.add_private_key(private_key, mode) :
		logging.error('add private key in keystore failed')
		return None, None, None
	else :
		logging.info('private key in keystore')

	# claims for firstname and lastname
	if firstname and lastname :
		if not update_self_claims(address, private_key, {'firstname': firstname, 'lastname' : lastname}, mode) :
			logging.warning('firstname and lastname not updated')
		else :
			logging.info('firstname and lastname updated')

	# add wallet address in resolver
	if wallet :
		if ns.update_wallet(workspace_contract, wallet, mode) :
			logging.info('Success : wallet updated')
		else :
			logging.warning('wallet update failed')

	# key 1 issued to Web Relay to act as agent.
	if not add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode) :
		logging.error('add key 1 to web Relay failed')
	else :
		logging.info('key 1 to web Relay has been added')

	logging.info('end of step 1 create identity')
	return address, private_key, workspace_contract


def _create_user_step_2(address, workspace_contract, private_key, username, firstname, lastname, email, mode, creator, partner, send_email,) :

	# key 5 to Talao to be in White List
	if not add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 5, mode) :
		logging.error('add key 5 to Talao White list failed')
	else :
		logging.info("key 5 to Talao has been added")

	# key 20002 to Talao to Issue Proof of Identity
	if not 	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 20002 , mode) :
		logging.error('add key 20002 to Talao failed')
	else :
		logging.info('key 20002 to Talao has been added')

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
					logging.info('partnership request from creator has been accepted by Identity')
				else :
					logging.warning('authorize partnership with creator failed')
			else :
				logging.warning('creator partnership request failed')
		#add creator as referent
		if add_key(address, workspace_contract, address, workspace_contract, private_key, creator, 20002 , mode) :
			logging.info('key 20002 issued for creator')
		else :
			logging.warning('key 20002 for creator failed')
	else :
		logging.info('no company creator')

	# rewrite previous email to get an encrypted email
	if Claim().add(address,workspace_contract, address, workspace_contract,private_key, 'email', email, 'private', mode)[0] :
		logging.info('email encryted updated')
	else :
		logging.warning('email encrypted not updated')

	#Identity Verifiable claim issued by creator
	if creator and creator != mode.owner_talao :
		unsigned_credential = {
			"@context": [
			"https://www.w3.org/2018/credentials/v1",
			],
			"id": "did:talao:talaonet:" + workspace_contract[2:] + "#did_authn",
			"issuer": 'did:talao:talaonet:' + creator_workspace_contract[2:],
			"issuanceDate": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
			"type": ["VerifiableCredential"],
			"credentialSubject": {
				"id": "did:talao:talaonet:" + workspace_contract[2:],
				'family_name' : lastname,
				"given_name" : firstname,
				"birthdate" : "",
				"address" : "",
				"telephone" : "",
				"email" : "",
				"gender" : "",
				},
			}
		signed_credential = RsaSignatureSuite2017.sign(unsigned_credential, creator_rsa_key)
		# signed kyc stored as did_authn ERC735 Claim
		claim=Claim()
		if not claim.add(creator_address,
			 	creator_workspace_contract,
				address,
				workspace_contract,
				creator_private_key,
				'did_authn',
				signed_credential,
				'private',
				mode,
				synchronous = True)[0] :
			logging.error('transaction for proof of identity failed')
		else :
			logging.info('proof of identity has been issued')

	# emails send to user and admin
	Talao_message.messageLog(lastname, firstname, username, email, "createidentity.py", address, private_key, workspace_contract, "", email, "", "", mode)
	# By default an email is sent to user
	if send_email :
		Talao_message.messageUser(lastname, firstname, username, email, address, private_key, workspace_contract, mode)

	logging.info("create identity process step 2 is over")
	return
