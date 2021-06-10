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
from Crypto.Cipher import PKCS1_OAEP
from flask import jsonify, request, Response
import json
from authlib.jose import jwt

from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO)

import didkit
import constante
from protocol import  ownersToContracts, token_transfer, createVaultAccess, ether_transfer
from protocol import add_key, destroy_workspace, get_category, Claim
from components import privatekey
from signaturesuite import helpers

SALT = 'repository_salt'


class RepositoryException(Exception):
	def __init__(self, message) :
		pass


class Repository() :

	def load(self, mode, did) :
		if did.split(':')[1] not in ['web', 'tz', 'ethr', 'key'] :
			raise RepositoryException('DID method not supported')
		self.did = did
		self.private_key = '0x' + PBKDF2(did.encode(), SALT, 32, count=1000000, hmac_hash_module=SHA512).hex()
		self.address = helpers.ethereum_pvk_to_address(self.private_key)
		self.workspace_contract = ownersToContracts(self.address, mode)
		if not self.workspace_contract or self.workspace_contract == '0x0000000000000000000000000000000000000000' :
			logging.warning('no repository for this DID')
			return False
		self.RSA_private = privatekey.get_key(self.address, 'rsa_key', mode)
		if not self.RSA_private :
			logging.warning('RSA file not found')
			return False
		self.public_key = helpers.ethereum_pvk_to_pub(self.private_key)
		self.jwk = helpers.ethereum_to_jwk(self.private_key, 'ethr')
		self.private = privatekey.get_key(self.address, 'private', mode).hex()
		self.secret = privatekey.get_key(self.address, 'secret', mode).hex()
		self.category = get_category(self.workspace_contract, mode)
		self.email = None # need email TODO
		return True


	def delete_credential(self, mode) :
		return destroy_workspace(self.workspace_contract, self.private_key, mode)


	def store_credential(self, signed_credential, mode) :
		""" store credential encrypted to the repository
		signed_credential is json or dict
		return document_id
		"""
		if not isinstance(signed_credential, dict) :
			signed_credential = json.loads(signed_credential)
		credential = Claim()
		return credential.relay_add(self.workspace_contract, signed_credential['id'], signed_credential, 'private', mode)


	def publish_credential(self, signed_credential, mode) :
		""" add credential to the repository
		signed_credential is json or dict
		return link to display the credential
		"""
		if not isinstance(signed_credential, dict) :
			signed_credential = json.loads(signed_credential)
		credential = Claim()
		credential_id = credential.relay_add(self.workspace_contract, signed_credential['id'], signed_credential, 'public', mode)
		if credential_id :
			return 'https://talao.co/certificate/?certificate_id=' + self.did + ':claim:' + credential_id
		else :
			return None


	def get_credential(self, credential_id, mode) :
		""" get a credential as a json_ld
		credential id is our internal doc_id 
		"""
		credential = Claim()
		credential.get_by_topic_name(mode.relay_workspace_contract, None, self.workspace_contract, credential_id, mode)
		print(credential.__dict__)
		return json.dumps(credential.claim_value, ensure_ascii=False)




	def remove_credential(self, credential_id, mode) :
		credential  = Claim()
		return credential.relay_delete(self.workspace_contract, credential_id, mode)


	def create(self, did, mode, email=None, password=False, phone=None, wallet=None, category=1001) :
		""" Main function to create a repository for a user
		category is 1001 for person and 2001 for company
		DID is used to generate an ethereum private key
		email is used to recover in case of did keys are lost
		Talao smart contract is deployed on talaonet
		"""
		# Setup with DID as password, deterministic way to generate an address
		if not did :
			logging.error('did malformed')
			return False
		if did.split(':')[1] not in ['web', 'tz', 'ethr', 'key'] :
			logging.error('did not supported')
			return False
		repository = Repository()
		if repository.load(mode, did) :
			logging.error('A repository already exists for this DID')
			return False
		self.did = did
		self.email = email if email else ""
		if category not in [1001, 2001] :
			logging.error('wrong category')
			return False
		self.category = category
		self.private_key = '0x' + PBKDF2(self.did.encode(), SALT, 32, count=1000000, hmac_hash_module=SHA512).hex()
		self.address = helpers.ethereum_pvk_to_address(self.private_key)
		self.public_key = helpers.ethereum_pvk_to_pub(self.private_key)
		self.jwk = helpers.ethereum_to_jwk(self.private_key, 'ethr')

		# create RSA key
		RSA_key = RSA.generate(2048)
		self.RSA_private = RSA_key.exportKey('PEM')
		self.RSA_public =  RSA_key.publickey().exportKey('PEM')
		logging.info('RSA key generated')

		# Setup an AES key named 'private' to encrypt private data and to be shared with partnership
		private = get_random_bytes(16)
		self.private = private.hex()

		# Setup an AES key named 'secret' to encrypt secret data FIXME
		secret = get_random_bytes(16)
		self.secret = secret.hex()

		# AES private encrypted with RSA key
		cipher_rsa = PKCS1_OAEP.new(RSA_key)
		private_encrypted = cipher_rsa.encrypt(private)

		# AES secret encrypted with RSA key
		cipher_rsa = PKCS1_OAEP.new(RSA_key)
		secret_encrypted = cipher_rsa.encrypt(secret)

		try :
			# Ether transfer from TalaoGen wallet
			ether_transfer(self.address, mode.ether2transfer,mode)
			logging.info('ether transfer done ')
			# Talao tokens transfer from TalaoGen wallet
			token_transfer(self.address, mode.talao_to_transfer, mode)
			logging.info('token transfer done')
			# CreateVaultAccess call in the token to declare the identity within the Talao Token smart contract
			createVaultAccess(self.address, self.private_key, mode)
			logging.info('vault access created')
		except :
			logging.error('init Talao protocol failed')
			return False

		# Identity setup
		contract = mode.w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
		nonce = mode.w3.eth.getTransactionCount(self.address)
		bemail = bytes(self.email.lower() , 'utf-8')
		txn = contract.functions.createWorkspace(self.category,
												1,
												1,
												self.RSA_public,
												private_encrypted,
												secret_encrypted,
												bemail).buildTransaction({'chainId': mode.CHAIN_ID,
																			'gas': 7500000,
																			'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),
																			'nonce': nonce})
		signed_txn = mode.w3.eth.account.signTransaction(txn, self.private_key)
		mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
		transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
		receipt = mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
		if not receipt['status'] :
			logging.error('transaction to create repository failed')
			return False

		# workspace_contract address to be read in fondation smart contract
		self.workspace_contract = ownersToContracts(self.address, mode)
		logging.info('repository has been deployed')

		# store RSA key in file ./RSA_key/rinkeby, talaonet ou ethereum
		filename = "./RSA_key/" + mode.BLOCKCHAIN + '/did:talao:' + mode.BLOCKCHAIN + ':'  + self.workspace_contract[2:] + ".pem"
		try :
			file = open(filename,"wb")
			file.write( self.RSA_private)
			file.close()
			logging.info('RSA key stored on server')
		except :
			logging.error('RSA key not stored on server')
			return False

		# store Ethereum private key in keystore
		if not privatekey.add_private_key(self.private_key, mode) :
			logging.error('private key storage failed')
			return False
		else :
			logging.info('private key stored on server')

		# ERC725 key 1 issued to Web Relay as the Repository Manager
		if not add_key(self.address, self.workspace_contract, self.address, self.workspace_contract, self.private_key, mode.relay_address, 1, mode) :
			logging.error('ERC725 key 1 to repository manager failed')
			return False
		else :
			logging.error('ERC725 key 1 isued to repository manager')

		# rewrite email for recovery
		if Claim().add(self.address, self.workspace_contract, self.address, self.workspace_contract, self.private_key, 'email', self.email, 'public', mode)[0] :
			logging.info('email encryted updated')
		else :
			logging.warning('email encrypted not updated')

		logging.info('end of create repository')
		return True


def create(mode) :
	"""
	@app.route('/repository/create', methods=['GET'])
	"""
	repository = Repository()
	if repository.load(mode, request.args.get('did')) :
		return Response('{"message" : "repository found for this DID"}', status=406, mimetype='application/json')
	if not repository.create(request.args.get('did'), mode, email=request.args.get('email'))  :
		return Response('{"message" : "creation failed"}', status=406, mimetype='application/json')
	return Response('{"message" : "repository created"}', status=200, mimetype='application/json')


def authn(mode) :
	"""
	@app.route('/repository/authn', methods=['POST'])
	"""
	# verify authn request
	try :
		verificationPurpose = {
			"proofPurpose": "authentication",
			"verificationMethod": request.json['proof']['verificationMethod'],
			"domain" :  request.json['proof']['domain']
			}
		verifyResult = didkit.verifyPresentation(
			request.data.decode(),
			verificationPurpose.__str__().replace("'", '"'))
	except :
		return Response('{"message" : "request malformed"}', status=406, mimetype='application/json')

	# check authentication
	if json.loads(verifyResult)["errors"] :
		return Response('{"message" : "authentication failed"}', status=406, mimetype='application/json')

	# check if repository exists
	repository = Repository()
	if not repository.load(mode, request.json['holder'] ) :
		return Response('{"message" : "no repository found"}', status=406, mimetype='application/json')

	# generate access token, 30s live
	iat = datetime.timestamp(datetime.now())
	payload = {'iss': 'https://talao.co/repository',
				'sub': request.json['holder'],
				'exp' : iat + 30,
				'iat' : iat,
				'aud' : request.json['proof']['domain']
				}
	token = jwt.encode({'alg': 'HS256'}, payload, mode.password.encode()).decode()
	return Response(json.dumps({"token" : token}),status=200,mimetype='application/json')


def publish(mode) :
	"""
	@app.route('/repository/publish', methods=['POST'])
	"""
	payload = verify_token(request.json['token'], mode)
	if not payload :
			return jsonify({'message' : 'authenticaton failed'})
	repository = Repository()
	repository.load(mode, payload['sub'])
	return jsonify({'link' : repository.publish_credential(request.json['credential'], mode)})


def get(mode) :
	"""
	@app.route('/repository/get', methods=['POST'])
	"""
	payload = verify_token(request.json['token'], mode)
	if not payload :
		return jsonify({'message' : 'authenticaton failed'})
	repository = Repository()
	repository.load(mode, payload['sub'])
	return jsonify(repository.get_credential(request.json['credential_id'], mode))


def verify_token(token,mode) :
	try :
		payload = jwt.decode(token, mode.password.encode())
	except :
		logging.error('wrong signature')
		return None
	if datetime.timestamp(datetime.now()) > payload['exp'] :
		logging.error('token expired')
		return None
	if payload['aud'] != 'https://talao.co/repository' :
		logging.error('wrong domain')
		return None
	return payload