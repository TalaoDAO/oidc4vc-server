import json
import hashlib
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from base64 import b64encode
from datetime import datetime, timedelta
from eth_account import Account
from eth_account.messages import encode_defunct
from base64 import b64encode, b64decode
import logging
logging.basicConfig(level=logging.INFO)


#dependances
import constante
from components import Talao_ipfs, privatekey
from .Talao_token_transaction import read_profil, contractsToOwners, ownersToContracts

def contracts_to_owners(workspace_contract, mode) :
	return contractsToOwners(workspace_contract, mode)

def owners_to_contracts(address, mode) :
	return ownersToContracts(address, mode)

def topicvalue2topicname(topic_value) :
	word=''
	tvs = str(topic_value)
	i = 0
	while i < len(tvs) :
		if tvs[i] == '9' :
			letter = chr(int('0'+tvs[i]+tvs[i+1]))
			i = i+2
		else :
			letter = chr(int(tvs[i] + tvs[i+1] + tvs[i+2]))
			i = i+3
		word = word + letter
	return word

def topicname2topicvalue(topicname) :
	topicvaluestr =''
	for i in range(0, len(topicname))  :
		a = str(ord(topicname[i]))
		if int(a) < 100 :
			a='0'+a
		topicvaluestr = topicvaluestr + a
	i =  999999999999999999999999999999 # modulo 10 letters max
	return int(topicvaluestr) % i


def create_claim(address_from,workspace_contract_from, address_to, workspace_contract_to,private_key_from, topicname, data, privacy, mode, synchronous) :
	""" main reate claim function
	@data = str
	@topicname is credential id
	@privacy is public/private/secret
	scheme 2
	"""
	# calculate claim_id derived from credential "id" (topicname)
	topicvalue = topicname2topicvalue(topicname)
	claim_id = mode.w3.solidityKeccak(['address', 'uint256'], [address_from, topicvalue]).hex()
	# encrypt data
	data_encrypted = privatekey.encrypt_data(workspace_contract_to, {topicname : data}, privacy, mode, address_caller=address_from)
	if not data_encrypted :
		logging.warning('no data encrypted')
		return None

	# store on IPFS
	ipfs_hash = Talao_ipfs.ipfs_add(data_encrypted, mode)
	if not ipfs_hash :
		logging.error('ipfs hash error create_claim')
		return None

	# fire transaction
	nonce = mode.w3.eth.getTransactionCount(address_from)
	contract = mode.w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	txn = contract.functions.addClaim(topicvalue, 2, address_from, b'signature', privacy.encode(), ipfs_hash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key_from)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if not receipt['status'] :
		logging.error('transaction failed')
		return None
	logging.info('claim has been added on repository')
	return claim_id


def get_claim(workspace_contract_from, private_key_from, identity_workspace_contract, topicname, mode) :
	topic_value =  topicname2topicvalue(topicname)
	contract = mode.w3.eth.contract(identity_workspace_contract,abi=constante.workspace_ABI)
	a = contract.functions.getClaimIdsByTopic(topic_value).call()
	if not a :
		return None, identity_workspace_contract, None, "", 0, None, None, None, 'public',topic_value, None
	claim_id = a[-1].hex()
	return _get_claim(workspace_contract_from, private_key_from, identity_workspace_contract, claim_id, mode)

def get_claim_by_id(workspace_contract_from, private_key_from, identity_workspace_contract, claim_id, mode) :
	return _get_claim(workspace_contract_from, private_key_from, identity_workspace_contract, claim_id, mode)

def _get_claim(workspace_contract_from, private_key_from, identity_workspace_contract, claim_id, mode) :
	""" Internal function to access claim data """
	w3 = mode.w3
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	claim = contract.functions.getClaim(claim_id).call()
	data = claim[4].decode('utf-8') 	# privacy
	ipfs_hash = claim[5]
	issuer = claim[2]
	scheme = claim[1]
	topic_value = claim[0]
	#topicname = topicvalue2topicname(topic_value)
	if data != 'private' and data != 'secret' and data != 'public' :
		# compatiblité avec version precedente. data public non cryptee
		to_be_decrypted = False
		privacy = 'public'
	else :
		# toutes les datas sont encryptees
		to_be_decrypted = True
		privacy = data
	if to_be_decrypted :
		# upload data encrypted from ipfs
		data_encrypted = Talao_ipfs.ipfs_get(ipfs_hash)
		address_from = contracts_to_owners(workspace_contract_from, mode)
		msg = privatekey.decrypt_data(identity_workspace_contract, data_encrypted, privacy, mode, address_caller=address_from)
		if msg :
			#data= msg[topicname]
			data = list(msg.values())[0]
		else :
			logging.error('decrypt claim failed')
			data = None

	gas_used = 1000
	created = ""
	gas_price = 1
	transaction_hash = "0"

	return issuer, identity_workspace_contract, data, ipfs_hash, gas_price*gas_used, transaction_hash, scheme, claim_id, privacy,topic_value, created

def delete_claim(address_from, workspace_contract_from, address_to, workspace_contract_to,private_key_from,claim_id, mode):
	w3=mode.w3
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)
	# Build transaction
	txn = contract.functions.removeClaim(claim_id).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash =w3.toHex(w3.keccak(signed_txn.rawTransaction))
	receipt = w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if not receipt['status'] :
		return None, None, None
	transaction = w3.eth.getTransaction(transaction_hash)
	gas_price = transaction['gasPrice']
	block_number = transaction['blockNumber']
	block = mode.w3.eth.getBlock(block_number)
	date = datetime.fromtimestamp(block['timestamp'])
	gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
	deleted = date.strftime("%y/%m/%d")
	return transaction_hash, gas_used*gas_price, deleted

class Claim() :
	def __init__(self,
				topicvalue=None,
				topicname=None,
				created=None,
				transaction_hash=None,
				issuer = None,
				transaction_fee= None,
				claim_id = None,
				ipfs_hash = None,
				data_location=None,
				privacy = 'public',
				identity = None,
				claim_value = None
				) :

		self.topicvalue = topicvalue
		self.topicname = topicname
		#self.created = created
		#self.transaction_hash = transaction_hash
		self.issuer = issuer
		#self.transaction_fee = transaction_fee
		self.claim_id = claim_id
		self.ipfs_hash = ipfs_hash
		self.data_location = data_location
		self.privacy = privacy
		self.identity = identity
		self.claim_value = claim_value

	def relay_add(self, identity_workspace_contract, topicname, data, privacy, mode, synchronous=True) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create_claim(mode.relay_address,mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, topicname, data, privacy, mode, synchronous)

	def add(self, address_from,workspace_contract_from, address_to, workspace_contract_to,private_key_from, topicname, data, privacy, mode, synchronous = True) :
		return create_claim(address_from,workspace_contract_from, address_to, workspace_contract_to,private_key_from, topicname, data, privacy, mode, synchronous)

	def relay_delete(self, identity_workspace_contract, claim_id, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return  delete_claim(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, claim_id, mode)

	def get_by_topic_name(self, workspace_contract_from, private_key_from, identity_workspace_contract, topicname, mode, loading='full') :
		arg = get_claim(workspace_contract_from, private_key_from, identity_workspace_contract, topicname, mode)
		return self._get_by(*arg, mode, loading)

	def get_by_id(self, workspace_contract_from, private_key_from, identity_workspace_contract, claim_id, mode, loading='full') :
		arg = get_claim_by_id(workspace_contract_from, private_key_from, identity_workspace_contract, claim_id, mode)
		return self._get_by(*arg, mode,loading)

	def _get_by(self, issuer_address, identity_workspace_contract, data, ipfs_hash, transaction_fee, transaction_hash, scheme, claim_id, privacy, topicvalue, created, mode, loading) :
		""" Internal function """
		self.topicvalue = topicvalue
		if issuer_address  :
			issuer_workspace_contract = ownersToContracts(issuer_address, mode)
			(issuer_profil, issuer_category) = read_profil(issuer_workspace_contract, mode, loading)
			issuer_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:]
		else :
			return False
		#self.created = created
		self.topicname = topicvalue2topicname(self.topicvalue)
		self.claim_value = data
		self.issuer = {'address' : issuer_address,
						'workspace_contract' : issuer_workspace_contract,
						'category' : issuer_category,
						'id' : issuer_id}
		if issuer_profil :
			self.issuer.update(issuer_profil)
		#self.transaction_hash = transaction_hash
		#self.transaction_fee = transaction_fee
		self.ipfs_hash = ipfs_hash
		self.data_location = mode.BLOCKCHAIN if ipfs_hash == "" else 'https://gateway.ipfs.io/ipfs/' + ipfs_hash
		self.privacy = privacy
		self.claim_id = claim_id
		self.id = 'did:talao:' + mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:] + ':claim:' + str(claim_id)
		contract = mode.w3.eth.contract(identity_workspace_contract,abi=constante.workspace_ABI)
		category = contract.functions.identityInformation().call()[1]
		self.identity = {'address' : contracts_to_owners(identity_workspace_contract, mode),
						'workspace_contract' : identity_workspace_contract,
						'category' : category,
						'id' : 'did:talao:' + mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:]}
		return True
