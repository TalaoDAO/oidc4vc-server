""" Création d'un repository pour un DID

Creation d'un wallet pour le owner derivé du DID. Il est prévu de gerer l'authentifcation sur le repository par did_authn

Creation des cle de cyryptage : 1 RSA dérivé de la clé privée Ethereum

Création de 2 cle symetriques aléatoires

L email est gardé uniquement pour l authentification

une cle 1 (ERC725) est donnée au Web Relay pour la gestion du repository

smart contract déployé sur talaonet

"""
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA512
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP, AES
import json

import logging
logging.basicConfig(level=logging.INFO)

import constante
from protocol import  ownersToContracts, contractsToOwners, token_transfer, createVaultAccess, ether_transfer, get_all_credentials
from protocol import add_key, destroy_workspace, read_workspace_info, transfer_workspace, Claim, Document
from components import privatekey
from signaturesuite import helpers



class RepositoryException(Exception):

	def __init__(self, message) :
		pass


class Repository() :
	SALT = 'repository_salt'

	def load(self, mode, did=None, workspace_contract=None, address=None) :
		self.mode = mode
		if did :
			if did.split(':')[1] not in ['web', 'tz', 'ethr', 'key'] :
				raise RepositoryException('DID method not supported')
			self.did = did
			self.private_key = '0x' + PBKDF2(did.encode(), self.SALT, 32, count=1000000, hmac_hash_module=SHA512).hex()
			self.address = helpers.ethereum_pvk_to_address(self.private_key)
			self.workspace_contract = ownersToContracts(self.address, self.mode)
			if not self.workspace_contract or self.workspace_contract == '0x0000000000000000000000000000000000000000' :
				logging.warning('no repository for this DID')
				self.workspace_contract = None
				return

		elif workspace_contract :
			self.workspace_contract = workspace_contract
			self.did = 'did:talao:talaonet:' + workspace_contract[2:]
			self.address = contractsToOwners(self.workspace_contract, self.mode)
			if not self.address or self.address == '0x0000000000000000000000000000000000000000' :
				logging.warning('no address for this workspace_contract')
				self.workspace_contract = None
				return

		elif address :
			self.address = address
			self.workspace_contract = ownersToContracts(address, self.mode)
			self.did = 'did:talao:talaonet:' + workspace_contract[2:]
			if not self.workspace_contract or self.workspace_contract == '0x0000000000000000000000000000000000000000' :
				logging.warning('no repository for this address')
				self.workspace_contract = None
				return

		else :
			raise RepositoryException("no data were passed for loading")

		self.RSA_private = privatekey.get_key(self.address, 'rsa_key', self.mode)
		self.private_key = privatekey.get_key(self.address, 'private_key', self.mode)
		self.public_key = helpers.ethereum_pvk_to_pub(self.private_key)
		self.jwk = helpers.ethereum_to_jwk(self.private_key, 'ethr')
		self.private = privatekey.get_key(self.address, 'private', self.mode)
		self.secret = privatekey.get_key(self.address, 'secret', self.mode)
		self.category = read_workspace_info (self.address, self.RSA_private, self.mode)[0]
		self.email = None # need email TODO
		return self


	def did_to_repository(self, did) :
		if did.split(':')[1] not in ['web', 'tz', 'ethr', 'key'] :
			raise RepositoryException('DID method not supported')
		pvk = '0x' + PBKDF2(did.encode(), self.SALT, 32, count=1000000, hmac_hash_module=SHA512).hex()
		address = helpers.ethereum_pvk_to_address(pvk)
		return ownersToContracts(address, self.mode)


	def delete(self) :
		return destroy_workspace(self.workspace_contract, self.private_key, self.mode)


	def transfer(self, address_to) :
		return transfer_workspace(self.address, self.private_key, address_to, self.mode)


	def get_resume(self) :
		""" return a link to the resume of talao.co
		"""
		return 'https://talao.co/resume/?did=did:talao:talaonet:' + self.workspace_contract[2:]


	def store_credential(self, signed_credential) :
		""" store credential encrypted to the repository
		signed_credential is json or dict
		return document_id
		"""
		if not isinstance(signed_credential, dict) :
			signed_credential = json.loads(signed_credential)
		credential = Document('private_credential')
		return credential.relay_add(self.workspace_contract, signed_credential, self.mode, privacy='private')[0]


	def publish_credential(self, signed_credential) :
		""" add credential to the repository
		signed_credential is json or dict
		return link to display the credential
		"""
		if not isinstance(signed_credential, dict) :
			signed_credential = json.loads(signed_credential)
		credential = Document('credential')
		credential_id = credential.relay_add(self.workspace_contract, signed_credential, self.mode)[0]
		if credential_id :
			return 'https://talao.co/certificate/?certificate_id=' + self.did + ':document:' + str(credential_id)
		else :
			return None


	def get_all_credentials(self) :
		""" return a list of credentials as json_ld
		"""
		credential_list = []
		document_id_list = self.get_credentials_list()
		for document_id in document_id_list :
			credential_list.append(self.get_credential(document_id))
		return credential_list


	def get_credentials_list(self) :
		""" get a document id list for all credentials
		document id is not the json credential id
		return list int : list of document id
		"""
		return get_all_credentials(self.workspace_contract, self.mode) 


	def get_credential(self, document_id) :
		""" get a credential as a json_ld
		"""
		credential = Document('credential')
		credential.relay_get_credential(self.workspace_contract, document_id, self.mode)
		return json.dumps(credential.__dict__, ensure_ascii=False)


	def remove_credential(self, document_id) :
		credential  = Document('credential')
		return credential.relay_delete(self.workspace_contract, document_id, self.mode)


	def create(self, did, email, mode, password=False, phone=None, wallet=None, category=1001) :
		""" Main function to create a repository for a user
		category is 1001 for person and 2001 for company
		DID is used to generate an ethereum private key
		email is used to recover in case of did keys are lost
		Talao smart contract is deployed on talaonet
		"""
		# Setup with DID as password, deterministic way to generate an address
		if did.split(':')[1] not in ['web', 'tz', 'ethr', 'key'] :
			raise RepositoryException('DID method not supported')
		self.did = did
		self.email = email
		self.mode = mode
		if category not in [1001, 2001] :
			raise RepositoryException('wrong category')
		self.category = category
		self.private_key = '0x' + PBKDF2(self.did.encode(), self.SALT, 32, count=1000000, hmac_hash_module=SHA512).hex()
		self.address = helpers.ethereum_pvk_to_address(self.private_key)
		if ownersToContracts(self.address, self.mode) :
			logging.warning('A repository already exists for this DID')
			return None
		self.public_key = helpers.ethereum_pvk_to_pub(self.private_key)
		self.jwk = helpers.ethereum_to_jwk(self.private_key, 'ethr')

		# create RSA key as derivative from Ethereum private key
		RSA_key, self.RSA_private, self.RSA_public = privatekey.create_rsa_key(self.private_key, self.mode)
		logging.info('RSA key generated')

		# Setup an AES key named 'private' to encrypt private data and to be shared with partnership
		self.private = get_random_bytes(16)

		# Setup an AES key named 'secret' to encrypt secret data FIXME
		self.secret = get_random_bytes(16)

		# AES private encrypted with RSA key
		cipher_rsa = PKCS1_OAEP.new(RSA_key)
		private_encrypted = cipher_rsa.encrypt(self.private)

		# AES secret encrypted with RSA key
		cipher_rsa = PKCS1_OAEP.new(RSA_key)
		secret_encrypted = cipher_rsa.encrypt(self.secret)

		try :
			# Ether transfer from TalaoGen wallet
			ether_transfer(self.address, self.mode.ether2transfer,self.mode)
			logging.info('ether transfer done ')
			# Talao tokens transfer from TalaoGen wallet
			token_transfer(self.address, self.mode.talao_to_transfer, self.mode)
			logging.info('token transfer done')
			# CreateVaultAccess call in the token to declare the identity within the Talao Token smart contract
			createVaultAccess(self.address, self.private_key, self.mode)
			logging.info('create vault acces')
		except :
			logging.error('init Talao protocol failed')
			return None

		# Identity setup
		contract = self.mode.w3.eth.contract(self.mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
		nonce = self.mode.w3.eth.getTransactionCount(self.address)
		bemail = bytes(self.email.lower() , 'utf-8')
		txn = contract.functions.createWorkspace(self.category,
												1,
												1,
												self.RSA_public,
												private_encrypted,
												secret_encrypted,
												bemail).buildTransaction({'chainId': self.mode.CHAIN_ID,
																			'gas': 7500000,
																			'gasPrice': self.mode.w3.toWei(self.mode.GASPRICE, 'gwei'),
																			'nonce': nonce})
		signed_txn = self.mode.w3.eth.account.signTransaction(txn, self.private_key)
		self.mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
		transaction_hash = self.mode.w3.toHex(self.mode.w3.keccak(signed_txn.rawTransaction))
		receipt = self.mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
		if not receipt['status'] :
			logging.error('transaction to create repository failed')
			return None

		# workspace_contract address to be read in fondation smart contract
		self.workspace_contract = ownersToContracts(self.address, self.mode)
		logging.info('repository has been deployed')

		# store RSA key in file ./RSA_key/rinkeby, talaonet ou ethereum
		filename = "./RSA_key/" + self.mode.BLOCKCHAIN + '/did:talao:' + self.mode.BLOCKCHAIN + ':'  + self.workspace_contract[2:] + ".pem"
		try :
			file = open(filename,"wb")
			file.write( self.RSA_private)
			file.close()
			logging.info('RSA key stored on server')
		except :
			logging.warning('RSA key not stored on server')
			return None

		# store Ethereum private key in keystore
		if not privatekey.add_private_key(self.private_key, self.mode) :
			logging.error('private key storage failed')
			return None
		else :
			logging.info('private key stored on server')

		# key 1 issued to Web Relay as the Repository Manager
		if not add_key(self.address, self.workspace_contract, self.address, self.workspace_contract, self.private_key, self.mode.relay_address, 1, self.mode) :
			logging.error('ERC725 key 1 to repository manager failed')
			return None
		else :
			logging.error('ERC725 key 1 isued to repository manager')

		# rewrite email for recovery
		if Claim().add(self.address, self.workspace_contract, self.address, self.workspace_contract, self.private_key, 'email', self.email, 'public', self.mode)[0] :
			logging.info('email encryted updated')
		else :
			logging.warning('email encrypted not updated')

		"""
		# emails send to user and admin
		Talao_message.messageLog(lastname, firstname, username, email, "createidentity.py", address, private_key, workspace_contract, "", email, "", "", self.mode)
		# By default an email is sent to user
		if send_email :
			Talao_message.messageUser(lastname, firstname, username, email, address, private_key, workspace_contract, self.mode)
		"""

		logging.info('end of create repository')
		return self.address, self.private_key, self.workspace_contract

