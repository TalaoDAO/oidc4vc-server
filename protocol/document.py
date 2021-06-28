"""

doctypeversion = 1 freedapp (Deprecated)
doctypeversion = 2 data plaintext on ipfs (Deprecated)
doctypeversion = 3 : data encrypted with AES public (Deprecated on the 28/04/2021)
doctypeversion = 4 : data encrypted server side as JWE with Identity RSA key (default)
doctypeversion = 5 : data encrypted client side as JW. There is no encryption , we just upload on IPFS '{"jwe" : data}'


+--------------------+-----------+-----------+-----------+
|       doctype      |  Public   |  Private  |   Secret  |
+====================+===========+===========+===========+
| certificate        |   20000   |    20001  |  20002    |
+--------------------+-----------+-----------+-----------+
| education          |   40000   |   40001   |   40002   |
+--------------------+-----------+-----------+-----------+
| experience         |   50000   |   50001   |   50002   |
+--------------------+-----------+-----------+-----------+
| file               |   30000   |   30001   |   30002   | managed by file.py
+--------------------+-----------+-----------+-----------+

"""


import json
import hashlib
from authlib.jose import JsonWebEncryption
from Crypto.PublicKey import RSA
import uuid
import logging
logging.basicConfig(level=logging.INFO)

#dependances

from components import Talao_ipfs, privatekey
import constante

def contracts_to_owners(workspace_contract, mode) :
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.contractsToOwners(workspace_contract).call()

def owners_to_contracts(address, mode) :
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.ownersToContracts(address).call()

def _create(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, doctype, data, mydays, privacy, mode, synchronous, version, id, sequence) :

	# align doctype with privacy
	if privacy == 'private' and doctype == 20000 :
		doctype = 20001
	if privacy == 'secret' and doctype == 20000 :
		doctype = 20002

	# @data = dict
	if isinstance (data, str) :
		data = json.loads(data)
		logging.error('data must be a dict')

	#encrypt data with AES key (public, private or secret) Deprecated
	if version == 3 :
		data = privatekey.encrypt_data(workspace_contract_to, data, privacy, mode)
		if not data :
			logging.error('encryption problem')
			return None, None, None

	#encrypt server side data as JWE with identity RSA key
	elif version == 4 :
		jwe = JsonWebEncryption()
		protected = {'alg': 'RSA-OAEP', 'enc': 'A256GCM'}
		payload = json.dumps(data).encode()
		private_rsa_key = privatekey.get_key(address_to, 'rsa_key', mode)
		RSA_KEY = RSA.import_key(private_rsa_key)
		public_rsa_key = RSA_KEY.publickey().export_key('PEM').decode('utf-8')
		if not id :
			id = str(uuid.uuid1())
		if not sequence :
			sequence = 0
		data = {
			"id" : id,
			"sequence" : sequence,
			"jwe": jwe.serialize_compact(protected, payload, public_rsa_key).decode()}

	# encrypt data with AES key of identity"
	elif version == 5 :
		jwe = JsonWebEncryption()
		protected = {'alg': 'A128KW', 'enc' : 'A128CBC-HS256'}
		payload = json.dumps(data).encode()
		if privacy == 'public' :
			secret =  mode.aes_public_key.encode()
		else :
			secret = privatekey.get_key(address_to, privacy, mode)
		if not id :
			id = str(uuid.uuid1())
		if not sequence :
			sequence = 0
		data = {
			"id" : id,
			"sequence" : sequence,
			"jwe": jwe.serialize_compact(protected, payload, secret).decode()}

	# No data encryption. data have been probably encrypted as JWE client side
	elif version == 6 :
		data = {
			"id" : str(uuid.uuid1()),
			"sequence" : 0,
			'jwe' : json.dumps(data)}

	else :
		logging.error('pb version')
		return None, None, None

	# Build transaction
	contract = mode.w3.eth.contract(workspace_contract_to,abi = constante.workspace_ABI)
	nonce = mode.w3.eth.getTransactionCount(address_from)

	# upkoad on ipfs
	ipfs_hash = Talao_ipfs.ipfs_add(data, mode)
	if not ipfs_hash :
		logging.error('IPFS connexion problem')
		return None, None, None

	# checksum (bytes)
	checksum = hashlib.md5(bytes(json.dumps(data), 'utf-8')).hexdigest()

	# Transaction
	expires = 0
	txn = contract.functions.createDocument(doctype, version, expires, checksum, 1, bytes(ipfs_hash, 'utf-8'), True).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 1000000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key_from)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	if synchronous :
		if not mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)['status'] :
			logging.error('transaction to create document failed')
			return None, None, None

		# Get document id on last event
		contract = mode.w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
		from_block = mode.w3.eth.blockNumber - 10
		myfilter = contract.events.DocumentAdded.createFilter(fromBlock= from_block ,toBlock = 'latest')
		eventlist = myfilter.get_all_entries()
		document_id = eventlist[-1]['args']['id']
		return document_id, ipfs_hash, transaction_hash
	else :
		return None, None, None

def _get(workspace_contract_from, private_key_from, workspace_contract_user, documentId, mode) :

	# @documentID is int
	if not isinstance (documentId, int) :
		documentId = int(documentId)
		logging.error('doc_id must be int')

	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_user,abi=constante.workspace_ABI)
	try :
		(doctype, doctypeversion, unused, issuer, unused, unused, ipfshash, unused, unused) = contract.functions.getDocument(documentId).call()
		print('connexion ok')
	except :
		logging.error('connexion blockchain talaonet impossble, document.py')
		return None, None, None, None, None, None, None

	if doctype in [50000,40000,10000,15000,20000,11000] :
		privacy = 'public'
	if doctype in [50001, 40001, 15001, 20001]:
		privacy = 'private'
	if doctype in [50002, 40002, 20002] :
		privacy = 'secret'
	workspace_contract_identity = workspace_contract_user

	# download from IPFS
	ipfs_data = Talao_ipfs.ipfs_get(ipfshash.decode('utf-8'))

	# previous version (deprecated)
	if privacy  == 'public' and doctypeversion == 2 :
		return issuer, workspace_contract_identity, ipfs_data, ipfshash.decode(), privacy, "", 0

	# data encrypted server side with AES algo and server keys (public, private, secret)
	elif doctypeversion == 3 :
		msg = privatekey.decrypt_data(workspace_contract_user, ipfs_data, privacy, mode)
		if msg :
			# decrypt avec algo AES-EAX ou AES-CBC
			return issuer, workspace_contract_user, msg, ipfshash.decode('utf-8'), privacy, "", 0
		else :
			# la clé RSA n'est pas disponible sur le serveur
			logging.warning('Cannot decrypt data')
			return issuer, workspace_contract_user, {"data" : 'Encrypted'} ,ipfshash.decode('utf-8'), privacy, "", 0

	# data encrypted server side as JWE with RSA identity key
	elif  doctypeversion == 4 :
		jwe = JsonWebEncryption()
		address_user = contracts_to_owners(workspace_contract_user, mode)
		key = privatekey.get_key(address_user, 'rsa_key', mode)
		data = jwe.deserialize_compact(ipfs_data['jwe'], key)
		payload = data['payload']
		return issuer, workspace_contract_user, payload.decode(), ipfshash.decode(), privacy, "", 0

	# data encrypted server side as JWE with AES key
	elif  doctypeversion == 5 :
		jwe = JsonWebEncryption()
		address_user = contracts_to_owners(workspace_contract_user, mode)
		if privacy == 'public' :
			secret =  mode.aes_public_key.encode()
		else :
			secret = privatekey.get_key(address_user, privacy, mode)
		data = jwe.deserialize_compact(ipfs_data['jwe'], secret)
		payload = data['payload']
		return issuer, workspace_contract_user, payload.decode(), ipfshash.decode(), privacy, ipfs_data['id'], ipfs_data['sequence']

	# data encrypted client side as JWE. There is no server decryption.
	elif  doctypeversion == 6 :
		return issuer, workspace_contract_user, ipfs_data['jwe'], ipfshash.decode(), privacy, "", 0

	else :
		logging.error('pb doctypeversion')
		return None, None, None, None, None, None, None

def _delete(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, documentId, mode):
	w3 = mode.w3
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)
	# Build transaction
	txn = contract.functions.deleteDocument(int(documentId)).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	# send transaction
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	return w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)['status']

class Document() :
	def __init__(self, topic) :
		self.topic = topic
		self.doctype = self.get_doctype(self.topic)

	# only public data
	def get_doctype(self, my_topic) :
		if my_topic == 'skills' :
			return 11000
		elif my_topic in ['certificate', 'credential'] :
			return 20000
		elif my_topic in ['private_credential'] :
			return 20001
		elif my_topic in ['secret_credential'] :
			return 20002


	def relay_add(self, identity_workspace_contract, data, mode, mydays=0, privacy='public', synchronous=True, version=5, id=None, sequence=None) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return _create(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, self.doctype, data, mydays, privacy, mode, synchronous, version, id, sequence)


	def relay_get(self, identity_workspace_contract, doc_id, mode, loading='light') :
		(issuer_address, identity_workspace_contract, data, ipfshash, privacy, id, sequence) = _get(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, doc_id, mode)
		if not issuer_address :
			return False
		else :
			if isinstance(data, str) :
				data = json.loads(data)
			self.__dict__.update(data)
			self.data_location = 'https://gateway.pinata.cloud/ipfs/'+ ipfshash
			self.privacy = privacy
			self.doc_id = doc_id
			self.id = 'did:talao:talaonet:' + identity_workspace_contract[2:] + ':document:' + str(doc_id)
			del self.doctype
		return True


	def relay_get_credential(self, identity_workspace_contract, doc_id, mode) :
		(issuer_address, identity_workspace_contract, data, ipfshash, privacy, id, sequence) = _get(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, doc_id, mode)
		if issuer_address :
			if isinstance(data, str) :
				data = json.loads(data)
			self.__dict__.update(data)
			del self.doctype
			del self.topic
			return True


	def relay_delete(self, identity_workspace_contract, doc_id, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return _delete(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, doc_id, mode)


	def relay_update_privacy(self, identity_workspace_contract, doc_id, new_privacy, mode) :
		(issuer_address, identity_workspace_contract, data, ipfshash, privacy, id, sequence) = _get(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, doc_id, mode)
		if privacy == new_privacy or issuer_address is None :
			return None, None, None
		self.relay_delete(identity_workspace_contract, doc_id, mode)
		sequence += 1
		return self.relay_add(identity_workspace_contract, data, mode, mydays=0, privacy=new_privacy,version=5, id=id, sequence=sequence)


