"""

doctypeversion = 1 freedapp
doctypeversion = 2 public data el clair sur ipfs
doctype version = 3 : RGPD --> public data encodé avec une clea aes publique

"""


import json
import hashlib
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from eth_account import Account
from base64 import b64encode
from datetime import datetime, timedelta
from base64 import b64encode, b64decode

#dependances
from Talao_ipfs import ipfs_add, ipfs_get
import constante
import privatekey
from .Talao_token_transaction import read_profil

def contracts_to_owners(workspace_contract, mode) :
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.contractsToOwners(workspace_contract).call()

def owners_to_contracts(address, mode) :
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.ownersToContracts(address).call()

def create_document(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, doctype, data, mydays, privacy, mode, synchronous, request) :
	# @data = dict
	# insert data about user request for audit
	if request :
		data['request_remote_addr'] = request.remote_addr
		data['request_remote_user'] = request.remote_user
		data['request_user_agent'] = request.user_agent.__dict__

	print("certificate avant issue = ", data)
	#encrypt data with AES key (public, private or secret)
	data = privatekey.encrypt_data(workspace_contract_to, data, privacy, mode)

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
	ipfs_hash = ipfs_add(data, mode)
	if not ipfs_hash :
		return None, None, None
	# checksum (bytes)
	_data = json.dumps(data)
	checksum = hashlib.md5(bytes(_data, 'utf-8')).hexdigest()
	# la conversion inverse de bytes(data, 'utf-8') est XXX.decode('utf-8')

	# Transaction with doctypevesrion = 3 for RGPD constraint
	txn = contract.functions.createDocument(doctype,3,expires,checksum,1, bytes(ipfs_hash, 'utf-8'), True).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 1000000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key_from)
	try :
		mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	except ValueError :
		print('Error : valueError dans create document, on reessaie avec un gasprice plus élevé')
		nonce = mode.w3.eth.getTransactionCount(address_from)
		gasprice = mode.w3.toWei('4', 'gwei')
		txn = contract.functions.createDocument(doctype,3,expires,checksum,1, bytes(ipfs_hash, 'utf-8'), True).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 1000000,'gasPrice': gasprice,'nonce': nonce,})
		signed_txn = mode.w3.eth.account.signTransaction(txn,private_key_from)
		mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	if synchronous :
		receipt = mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
		if not receipt['status'] :
			print('Error : transaction to create document failed. See receipt : ', receipt)
			return None, None, None

	# Get document  id on last event
	contract = mode.w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	from_block = mode.w3.eth.blockNumber - 10
	myfilter = contract.events.DocumentAdded.createFilter(fromBlock= from_block ,toBlock = 'latest')
	eventlist = myfilter.get_all_entries()
	document_id = eventlist[-1]['args']['id']
	return document_id, ipfs_hash, transaction_hash


def get_document(workspace_contract_from, private_key_from, workspace_contract_user, documentId, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_user,abi=constante.workspace_ABI)
	try :
		(doctype, doctypeversion, expires, issuer, checksum, engine, ipfshash, encrypted, related) = contract.functions.getDocument(documentId).call()
	except :
		return None, None, None, None, None, None, None, None, None, None, None , None, None

	if doctype in [50000,40000,10000,15000,20000, 11000] :
		privacy = 'public'
	if doctype == 50001 or doctype == 40001 :
		privacy = 'private'
	if doctype == 50002 or doctype == 40002 :
		privacy = 'secret'

	# get transaction info
	contract = w3.eth.contract(workspace_contract_user, abi=constante.workspace_ABI)
	claim_filter = contract.events.DocumentAdded.createFilter(fromBlock=mode.fromBlock,toBlock = 'latest')
	event_list = claim_filter.get_all_entries()
	found = False
	for doc in event_list :
		if doc['args']['id'] == documentId :
			found = True
			transactionhash = doc['transactionHash']
			transaction_hash = transactionhash.hex()
			try :
				transaction = w3.eth.getTransaction(transaction_hash)
			except :
				print('Error : get transacion document.py', documentId, doctype, privacy, transaction_hash)
				return None, None, None, None, None, None, None, None, None, None, None , None, None
			gas_price = transaction['gasPrice']
			identity_workspace_contract = transaction['to']
			block_number = transaction['blockNumber']
			block = mode.w3.eth.getBlock(block_number)
			date = datetime.fromtimestamp(block['timestamp'])
			gas_used = 1000
			#gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
			created = str(date)
			break
	if not found :
		print('Error : document not found in event list')
		return None
	# recuperation du msg
	data = ipfs_get(ipfshash.decode('utf-8'))
	# calcul de la date
	if not expires :
		expires = 'Unlimited'
	else :
		myexpires = datetime.fromtimestamp(expires)
		expires = str(myexpires)

	#compatiblité avec les documents non cryptés
	if privacy  == 'public' and doctypeversion == 2 :
		return issuer, identity_workspace_contract, data, ipfshash.decode('utf-8'), gas_price*gas_used, transaction_hash, doctype, doctypeversion, created, expires, issuer, privacy, related

	#recuperer la cle AES cryptée
	address_user = owners_to_contracts(workspace_contract_user, mode)
	if privacy == 'public' and doctypeversion == 3 :
		his_aes = b'public_ipfs_key_'
	elif privacy == 'private' :
		his_aes = privatekey.get_key(address_user, 'aes_key', mode)
	elif privacy == 'secret' :
		his_aes == privatekey.get_key(address_user, 'secret_key', mode)
	else :
		print ("Error : key not found")
		return None, None, None, None, None, None, None, None, None, None, None , None, None
	# decrypt data
	try:
		b64 = data #json.loads(json_input)
		json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
		jv = {k:b64decode(b64[k]) for k in json_k}
		cipher = AES.new(his_aes, AES.MODE_EAX, nonce=jv['nonce'])
		cipher.update(jv['header'])
		plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
		msg = json.loads(plaintext.decode('utf-8'))
		return issuer, identity_workspace_contract, msg,ipfshash.decode('utf-8'), gas_price*gas_used, transaction_hash, doctype, doctypeversion, created, expires, issuer, privacy, related	
	except ValueError :
		print("Error : data Decryption error")
		return None, None, None, None, None, None, None, None, None, None, None , None, None

def delete_document(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, documentId, mode):
	w3 = mode.w3
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)
	# Build transaction
	txn = contract.functions.deleteDocument(int(documentId)).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	# send transaction
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	receipt = w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if receipt['status'] == 0 :
		return None
	#transaction = w3.eth.getTransaction(transaction_hash)
	#gas_price = transaction['gasPrice']
	#block_number = transaction['blockNumber']
	#block = mode.w3.eth.getBlock(block_number)
	#date = datetime.fromtimestamp(block['timestamp'])
	#gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
	gas_used = 10000
	gas_price = 1
	date= datetime.now()
	deleted = date.strftime("%y/%m/%d")
	return transaction_hash, gas_used*gas_price, deleted

class Document() :
	def __init__(self, topic) :
		self.topic = topic
		self.doctype = self.get_doctype(self.topic)

	# only public data
	def get_doctype(self, my_topic) :
		if my_topic == 'skills' :
			return 11000
		if my_topic == 'education' :
			return 40000
		if my_topic == 'experience' :
			return 50000
		if my_topic == 'kbis' :
			return 10000
		if my_topic == 'kyc' :
			return 15000
		if my_topic == 'certificate' :
			return 20000

	def add(self, address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, data, mode, mydays=0, privacy='public', synchronous=True, request=None) :
		return create_document(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, self.doctype, data, mydays, privacy, mode, synchronous, request)

	def relay_add(self, identity_workspace_contract, data, mode, mydays=0, privacy='public', synchronous=True, request=None) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create_document(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, self.doctype, data, mydays, privacy, mode, synchronous, request)

	def talao_add(self, identity_workspace_contract, data, mode, mydays=0, privacy='public', synchronous=True, request=None) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create_document(mode.owner_talao,  mode.workspace_contract_talao, identity_address, identity_workspace_contract, mode.owner_talao_private_key, self.doctype, data, mydays, privacy, mode, synchronous, request)

	def relay_get(self, identity_workspace_contract, doc_id, mode, loading='light') :
		(issuer_address, identity_workspace_contract, data, ipfshash, transaction_fee, transaction_hash, doctype, doctypeversion, created, expires, issuer, privacy, related) = get_document(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, doc_id, mode)

		if not issuer_address :
			return False
		else :
			self.__dict__.update(data)
			issuer_workspace_contract = owners_to_contracts(issuer_address, mode)
			(issuer_profil, issuer_category) = read_profil(issuer_workspace_contract, mode, loading)
			issuer_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:]

			self.request_remote_addr = data.get('request_remote_addr','None')
			self.request_remote_user = data.get('request_remote_user', 'None')
			self.request_remote_user_agent = data.get('request_user_agent', dict())

			self.created = created
			self.issuer = {'address' : issuer_address,
						'workspace_contract' : issuer_workspace_contract,
						'category' : issuer_category,
						'id' : issuer_id}
			if issuer_profil :
				self.issuer.update(issuer_profil)
			self.transaction_hash = transaction_hash
			self.transaction_fee = transaction_fee
			self.doctypeversion = doctypeversion
			self.ipfshash = ipfshash
			self.data_location = 'https://gateway.pinata.cloud/ipfs/'+ ipfshash
			self.expires = expires
			self.privacy = privacy
			self.doc_id = doc_id
			self.id = 'did:talao:' + mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:] + ':document:' + str(doc_id)

			contract = mode.w3.eth.contract(identity_workspace_contract,abi=constante.workspace_ABI)
			identity_category = contract.functions.identityInformation().call()[1]

			self.identity= {'address' : contracts_to_owners(identity_workspace_contract, mode),
						'workspace_contract' : identity_workspace_contract,
						'category' : identity_category,
						'id' : 'did:talao:' + mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:] }
			self.transaction_fee = transaction_fee

		return True

	def relay_delete(self, identity_workspace_contract, doc_id, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return delete_document(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, doc_id, mode)

	def delete(self, identity_workspace_contract, identity_private_key, doc_id, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return delete_document(identity_address, identity_workspace_contract, identity_address, identity_workspace_contract, identity_private_key, doc_id, mode)