import logging
logging.basicConfig(level=logging.INFO)

#dependances
import constante
from components import Talao_ipfs
from .Talao_token_transaction import contractsToOwners

SALT = 'repository_salt'

def topicname2topicvalue(topicname) :
	topicvaluestr =''
	for i in range(0, len(topicname))  :
		a = str(ord(topicname[i]))
		if int(a) < 100 :
			a='0'+a
		topicvaluestr = topicvaluestr + a
	i =  999999999999999999999999999999 # modulo 10 letters max
	return int(topicvaluestr) % i


def create_claim(address_from,workspace_contract_from, address_to, workspace_contract_to,private_key_from, topicname, data, privacy, mode) :
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
	data_encrypted = encrypt_data(workspace_contract_to, {topicname : data}, privacy, mode, address_caller=address_from)
	if not data_encrypted :
		logging.warning('data encryption failed')
		return None

	# store on IPFS
	ipfs_hash = Talao_ipfs.ipfs_add(data_encrypted, mode)
	if not ipfs_hash :
		logging.error('ipfs failed')
		return None

	# fire transaction
	nonce = mode.w3.eth.getTransactionCount(address_from)
	contract = mode.w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	txn = contract.functions.addClaim(topicvalue, 2, address_from, b'signature', privacy.encode(), ipfs_hash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key_from)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	if not mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)['status']
		logging.error('transaction failed')
		return None
	return claim_id


def get_claim(workspace_contract_from, private_key_from, identity_workspace_contract, topicname, mode) :
	topic_value =  topicname2topicvalue(topicname)
	contract = mode.w3.eth.contract(identity_workspace_contract,abi=constante.workspace_ABI)
	claim_list = contract.functions.getClaimIdsByTopic(topic_value).call()
	if not claim_list :
        logging.error('no claim found')
		return None
	claim_id = claim_list[-1].hex()
	return _get_claim(workspace_contract_from, identity_workspace_contract, claim_id, mode)


def get_claim_by_id(workspace_contract_from, identity_workspace_contract, claim_id, mode) :
	return _get_claim(workspace_contract_from, identity_workspace_contract, claim_id, mode)


def _get_claim(workspace_contract_from, identity_workspace_contract, claim_id, mode) :
	""" Internal function to access claim data """
	w3 = mode.w3
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	claim = contract.functions.getClaim(claim_id).call()
	privacy = claim[4].decode()
	ipfs_hash = claim[5]
	issuer = claim[2]
	scheme = claim[1]
	topic_value = claim[0]
	data_encrypted = Talao_ipfs.ipfs_get(ipfs_hash)
	address_from = contracts_to_owners(workspace_contract_from, mode)
	msg = decrypt_data(identity_workspace_contract, data_encrypted, privacy, mode, address_caller=address_from)
	if msg :
		data = list(msg.values())[0]
	else :
		logging.error('decrypt claim failed')
		return None
	return issuer, identity_workspace_contract, data, ipfs_hash,  scheme, claim_id, privacy, topic_value


def delete_claim(address_from, workspace_contract_from, address_to, workspace_contract_to,private_key_from,claim_id, mode):
	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)
	# Build transaction
	txn = contract.functions.removeClaim(claim_id).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash =w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if not w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)['status'] :
        logging.error('transaction failed')
		return False
	return True


class Claim() :

	def add(self, identity_workspace_contract, topicname, data, privacy, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create_claim(mode.relay_address,mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, topicname, data, privacy, mode)


	def delete(self, identity_workspace_contract, claim_id, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return  delete_claim(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, claim_id, mode)


    def get_by_topic(self, workspace_contract_from, identity_workspace_contract, topicname, mode) :
        arg = get_claim(workspace_contract_from, identity_workspace_contract, topicname, mode)
        if not arg :
            return False
        return self._get(*arg, mode)


	def get_by_id(self, workspace_contract_from, identity_workspace_contract, claim_id, mode) :
		arg = get_claim_by_id(workspace_contract_from, identity_workspace_contract, claim_id, mode)
         if not arg :
            return False
		return self._get(*arg, mode)


	def _get(self, issuer_address, identity_workspace_contract, data, ipfs_hash, scheme, claim_id, privacy, topicvalue, mode) :
		self.data = data
		self.ipfs_hash = ipfs_hash
		self.data_location =  'https://gateway.ipfs.io/ipfs/' + ipfs_hash
		self.claim_id = claim_id
		return True


def encrypt_data(identity_workspace_contract, data, privacy, mode, address_caller=None) :
	# parameter data is dict
	# return dict is dict
	identity_address = contractsToOwners(identity_workspace_contract, mode)
	if privacy == 'public' :
		aes = mode.aes_public_key.encode()
	elif privacy == 'private' :
		aes = get_key(identity_address, 'aes_key', mode, address_caller=address_caller)
	else  : #privacy == 'secret' :
		aes = get_key(identity_address, 'secret_key', mode)
	if not aes :
		logging.error('RSA key not found on server or cannot decrypt AES')
		return None

	# AES-CBC encryption for compatibility with Javascrip librairy
	message = json.dumps(data).encode()
	bytes = PBKDF2(aes, SALT.encode(), 128, 128)
	iv = bytes[0:16]
	key = bytes[16:48]
	cipher = AES.new(key, AES.MODE_CBC, iv)
	encrypted = cipher.encrypt(pad(message, AES.block_size))
	ct = b64encode(encrypted).decode()
	return {"ciphertext" : ct}


def decrypt_data(workspace_contract_user, data, privacy, mode, address_caller=None) :
	#recuperer la cle AES cryptée
	# on encrypt en mode CBC pour compatiblité avec librairie JS
	address_user = contractsToOwners(workspace_contract_user, mode)
	if privacy == 'public' :
		aes = mode.aes_public_key.encode()
	elif privacy == 'private' :
		aes = get_key(address_user, 'aes_key', mode, address_caller)
	else : #privacy == 'secret' :
		aes = get_key(address_user, 'secret_key', mode)
	if not aes :
		logging.info('no RSA key on server')
		return None

	# decrypt data
	data = b64decode(data['ciphertext'])
	bytes = PBKDF2(aes, SALT.encode(), 128, 128)
	iv = bytes[0:16]
	key = bytes[16:48]
	cipher = AES.new(key, AES.MODE_CBC, iv)
	plaintext = cipher.decrypt(data)
	plaintext = plaintext[:-plaintext[-1]].decode()
	return json.loads(plaintext)
