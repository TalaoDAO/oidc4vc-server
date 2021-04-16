"""

doctypeversion = 1 freedapp. 
doctypeversion = 2 public data en clair sur ipfs
doctypeversion = 3 : RGPD --> public data encodé avec une cle aes publique


+--------------------+-----------+-----------+-----------+
|       doctype      |  Public   |  Private  |   Secret  |
+====================+===========+===========+===========+
| kbis               |   10000   |    N/A    |    N/A    |
+--------------------+-----------+-----------+-----------+
| kyc/kyc_p          |   15000   |  15001    |    N/A    | unused see ERC725 did_authn
+--------------------+-----------+-----------+-----------+
| certificate        |   20000   |    N/A    |    N/A    |
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
from eth_account import Account
from datetime import datetime, timedelta
from base64 import b64encode, b64decode
import logging
logging.basicConfig(level=logging.INFO)

#dependances
from components import Talao_ipfs, privatekey
import constante
from .Talao_token_transaction import read_profil

def contracts_to_owners(workspace_contract, mode) :
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.contractsToOwners(workspace_contract).call()

def owners_to_contracts(address, mode) :
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.ownersToContracts(address).call()

def create(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, doctype, data, mydays, privacy, mode, synchronous, request, address_caller=None) :

	# @data = dict 
	if isinstance (data, str) :
		data = json.loads(data)
		logging.error('data must be a dict')

	# check privacy vs doctype
	if doctype in [50000, 40000, 10000, 15000, 20000, 11000] :
		standard_privacy = 'public'
	elif doctype in [50001, 40001, 15001, 20001] :
		standard_privacy = 'private'
	elif doctype in [50002, 40002] :
		standard_privacy = 'secret'
	else :
		standard_privacy = None
	if standard_privacy != privacy :
		logging.error('privacy does not match with doctype')

	#encrypt data with AES key (public, private or secret)
	data = privatekey.encrypt_data(workspace_contract_to, data, privacy, mode, address_caller=address_caller)
	if not data :
		logging.error('encryption problem')
		return None, None, None

	# Date
	if not mydays :
		expires = 0
	else :
		myexpires = datetime.utcnow() + datetime.timedelta(days = mydays, seconds = 0)
		expires = int(myexpires.timestamp())

	# Build transaction
	contract = mode.w3.eth.contract(workspace_contract_to,abi = constante.workspace_ABI)
	nonce = mode.w3.eth.getTransactionCount(address_from)

	# store bytes on ipfs
	try :
		ipfs_hash = Talao_ipfs.ipfs_add(data, mode)
	except :
		logging.error('IPFS connexion problem')
		return None, None, None

	# checksum (bytes)
	_data = json.dumps(data)
	checksum = hashlib.md5(bytes(_data, 'utf-8')).hexdigest()

	# Transaction with doctype version = 3 for RGPD constraint
	txn = contract.functions.createDocument(doctype,3,expires,checksum,1, bytes(ipfs_hash, 'utf-8'), True).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 1000000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key_from)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if not receipt['status'] :
		logging.error('transaction to create document failed. See receipt : %s', receipt)
		return None, None, None

	# Get document  id on last event
	contract = mode.w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	from_block = mode.w3.eth.blockNumber - 10
	myfilter = contract.events.DocumentAdded.createFilter(fromBlock= from_block ,toBlock = 'latest')
	eventlist = myfilter.get_all_entries()
	document_id = eventlist[-1]['args']['id']
	return document_id, ipfs_hash, transaction_hash

def get(workspace_contract_from, private_key_from, workspace_contract_user, documentId, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_user,abi=constante.workspace_ABI)
	try :
		(doctype, doctypeversion, expires, issuer, checksum, engine, ipfshash, encrypted, related) = contract.functions.getDocument(documentId).call()
	except :
		return None, None, None, None, None

	if doctype in [50000,40000,10000,15000,20000,11000] :
		privacy = 'public'
	if doctype in [50001, 40001, 15001, 20001]:
		privacy = 'private'
	if doctype in [50002, 40002] :
		privacy = 'secret'
	created = ""
	workspace_contract_identity = workspace_contract_user
	#transaction_hash = "0"

	# recuperation du msg
	data = Talao_ipfs.ipfs_get(ipfshash.decode('utf-8'))

	# calcul de la date
	if not expires :
		expires = 'Unlimited'
	else :
		myexpires = datetime.fromtimestamp(expires)
		expires = str(myexpires)

	# compatiblité avec les documents non cryptés des version precedentes
	if privacy  == 'public' and doctypeversion == 2 :
		return issuer, workspace_contract_identity, data, ipfshash.decode('utf-8'), privacy

	# decrypt data pour autres documents
	msg = privatekey.decrypt_data(workspace_contract_user, data, privacy, mode)
	if msg :
		# decrypt avec algo AES-EAX ou AES-CBC
		return issuer, workspace_contract_user, msg, ipfshash.decode('utf-8'), privacy
	else :
		# la clé RSA n'est pas disponible sur le serveur
		logging.warning('Cannot decrypt data')
		return issuer, workspace_contract_user, {"data" : 'Encrypted'} ,ipfshash.decode('utf-8'), privacy

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
		elif my_topic == 'education' :
			return 40000
		elif my_topic == 'experience' :
			return 50000
		elif my_topic == 'kbis' :
			return 10000
		elif my_topic == 'kyc' :
			return 15000
		elif my_topic == 'kyc_p' :
			return 15001
		elif my_topic in ['certificate', 'credential'] :
			return 20000
		elif my_topic in ['private_credential'] :
			return 20001

	def add(self, address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, data, mode, mydays=0, privacy='public', synchronous=True, request=None) :
		return create(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, self.doctype, data, mydays, privacy, mode, synchronous, request)


	def relay_add(self, identity_workspace_contract, data, mode, mydays=0, privacy='public', synchronous=True, request=None) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, self.doctype, data, mydays, privacy, mode, synchronous, request)


	def talao_add(self, identity_workspace_contract, data, mode, mydays=0, privacy='public', synchronous=True, request=None) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create(mode.owner_talao,  mode.workspace_contract_talao, identity_address, identity_workspace_contract, mode.owner_talao_private_key, self.doctype, data, mydays, privacy, mode, synchronous, request, address_caller=mode.owner_talao)


	def relay_get(self, identity_workspace_contract, doc_id, mode, loading='light') :
		(issuer_address, identity_workspace_contract, data, ipfshash, privacy) = get(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, doc_id, mode)
		if not issuer_address :
			return False
		else :
			if isinstance(data, str) :
				data = json.loads(data)
			self.__dict__.update(data)
			#self.ipfshash = ipfshash
			self.data_location = 'https://gateway.pinata.cloud/ipfs/'+ ipfshash
			self.privacy = privacy
			self.doc_id = doc_id
			self.id = 'did:talao:' + mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:] + ':document:' + str(doc_id)
			del self.doctype
			del self.topic
		return True


	def relay_get_credential(self, identity_workspace_contract, doc_id, mode, loading='light') :
		(issuer_address, identity_workspace_contract, data, ipfshash, privacy) = get(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, doc_id, mode)
		if not issuer_address :
			return False
		else :
			if isinstance(data, str) :
				data = json.loads(data)
			self.__dict__.update(data)
			del self.doctype
			del self.topic
		return True


	def relay_delete(self, identity_workspace_contract, doc_id, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return _delete(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, doc_id, mode)


	def delete(self, identity_workspace_contract, identity_private_key, doc_id, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return _delete(identity_address, identity_workspace_contract, identity_address, identity_workspace_contract, identity_private_key, doc_id, mode)