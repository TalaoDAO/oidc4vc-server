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


#dependances
import constante
from Talao_ipfs import ipfs_add, ipfs_get


def contracts_to_owners(workspace_contract, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.contractsToOwners(workspace_contract).call()

def owners_to_contracts(address, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.ownersToContracts(address).call()


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
	return int(topicvaluestr)	


def read_profil (workspace_contract, mode, loading) :
	w3=mode.w3
	# setup constante person
	person_topicnames = {'firstname' : 102105114115116110097109101,
			'lastname' : 108097115116110097109101,
			'contact_email' : 99111110116097099116095101109097105108,
			'contact_phone' : 99111110116097099116095112104111110101,
			'postal_address' : 112111115116097108095097100100114101115115,
			'birthdate' : 98105114116104100097116101,
			'about' : 97098111117116,
			'education' : 101100117099097116105111110,
			'profil_title' : 112114111102105108095116105116108101
			}
	# setup constant company
	company_topicnames = {'name' : 110097109101,
				'contact_name' : 99111110116097099116095110097109101,
				'contact_email' : 99111110116097099116095101109097105108,
				'contact_phone' : 99111110116097099116095112104111110101,
				'website' : 119101098115105116101,
				'about' : 97098111117116,
				}
	if loading != 'full' :
		person_topicnames = {'firstname' : 102105114115116110097109101,
							'lastname' : 108097115116110097109101,
							}
		# setup constant company
		company_topicnames = {'name' : 110097109101,
							}

	profil = dict()
	# category
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	category = contract.functions.identityInformation().call()[1]

	topic_dict = person_topicnames if category == 1001 else company_topicnames

	for topicname, topic in topic_dict.items() :
		claim = contract.functions.getClaimIdsByTopic(topic).call()
		if len(claim) == 0 :
			profil[topicname] = None
		else :
			claimId = claim[-1].hex()
			data = contract.functions.getClaim(claimId).call()
			profil[topicname]=data[4].decode('utf-8')

	return profil,category 

def encrypt_data(identity_workspace_contract,data, privacy, mode) :
	#@ data = dict	
	w3 = mode.w3	
	#recuperer la cle AES cryptée de l identité
	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	mydata = contract.functions.identityInformation().call()
	if privacy == 'private' :
		my_aes_encrypted = mydata[5]
	if privacy == 'secret' :
		my_aes_encrypted = mydata[6] 

	identity_address = contracts_to_owners(identity_workspace_contract, mode)
	filename = "./RSA_key/"+mode.BLOCKCHAIN + '/' + identity_address + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1" + ".txt"
	try :
		fp = open(filename,"r")
		my_rsa_key = fp.read()	
		fp.close()  
	except IOError :
		print('RSA not found')
		return None 

	# decoder ma cle AES128 cryptée avec ma cle RSA privée
	key = RSA.importKey(my_rsa_key)
	cipher = PKCS1_OAEP.new(key)
	my_aes = cipher.decrypt(my_aes_encrypted)

	# coder les datas
	bytesdatajson = bytes(json.dumps(data), 'utf-8') # dict -> json(str) -> bytes
	header = b"header"
	cipher = AES.new(my_aes, AES.MODE_EAX) #https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html
	cipher.update(header)
	ciphertext, tag = cipher.encrypt_and_digest(bytesdatajson)
	json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
	json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, header, ciphertext, tag] ]
	dict_data = dict(zip(json_k, json_v))
	return dict_data


""" si public data = 'pierre' si crypté alors data = 'private' ou 'secret' et on encrypte un dict { 'firstane' ; 'pierre'} """
def create_claim(address_from,workspace_contract_from, address_to, workspace_contract_to,private_key_from, topicname, data, privacy, mode, synchronous = True) :
	# @data = str
	w3 = mode.w3

	topicvaluestr =''
	for i in range(0, len(topicname))  :
		a = str(ord(topicname[i]))
		if int(a) < 100 :
			a='0'+ a
		topicvaluestr = topicvaluestr + a
	topic_value = int(topicvaluestr)

	if privacy == 'public' :
		ipfs_hash = ""
	else :
		data_encrypted = encrypt_data(workspace_contract_to,{topicname : data}, privacy, mode)
		if data_encrypted is None :
			return None, None, None
		ipfs_hash = ipfs_add(data_encrypted, mode)
		if ipfs_hash is None :
			print('ipfs hash error create_claim')
			return None, None, None
		data = privacy

	nonce = w3.eth.getTransactionCount(address_from)
	issuer = address_from
	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfs_hash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=private_key_from)
	signature = signed_message['signature']
	claim_id = w3.solidityKeccak(['address', 'uint256'], [address_from, topic_value]).hex()

	#transaction
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	txn = contract.functions.addClaim(topic_value,2,issuer, signature, bytes(data, 'utf-8'),ipfs_hash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		receipt = w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
		if receipt['status'] == 0 :
			return None, None, None
	return claim_id, ipfs_hash, transaction_hash


def get_claim(workspace_contract_from, private_key_from, identity_workspace_contract, topicname, mode) :
	w3 = mode.w3
	topic_value =  topicname2topicvalue(topicname)
	contract = w3.eth.contract(identity_workspace_contract,abi=constante.workspace_ABI)
	a = contract.functions.getClaimIdsByTopic(topic_value).call()
	if len(a) == 0 :
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
	data = claim[4].decode('utf-8') 	# data public
	ipfs_hash = claim[5]
	issuer = claim[2]
	scheme = claim[1]
	topic_value = claim[0]
	topicname = topicvalue2topicname(topic_value)
	print('topicname calculé = ', topicname)

	if data != 'private' and data != 'secret' :
		to_be_decrypted = False
		privacy = 'public'

	elif workspace_contract_from == identity_workspace_contract :
		#recuperer les cle AES cryptée dans l identité
		contract = w3.eth.contract(workspace_contract_from,abi = constante.workspace_ABI)
		mydata = contract.functions.identityInformation().call()
		to_be_decrypted = True
		if data == 'private' :
			privacy = 'private'
			aes_encrypted = mydata[5]
		if data == 'secret' :
			privacy = 'secret'
			aes_encrypted = mydata[6]

	elif workspace_contract_from != identity_workspace_contract and data == 'private' and private_key_from is not None and workspace_contract_from is not None :
		print(' private_key ', private_key_from)
		#recuperer les cle AES cryptée du user sur son partnership de l identité
		contract = w3.eth.contract(workspace_contract_from, abi = constante.workspace_ABI)
		acct = Account.from_key(private_key_from)
		mode.w3.eth.defaultAccount = acct.address
		partnership_data = contract.functions.getPartnership(identity_workspace_contract).call()
		print('partnership data = ', partnership_data)
		privacy = 'private'	
		# one tests if the user in in partnershipg with identity (pending or authorized) and his aes_key exist (status rejected ?)
		if partnership_data[1] in [1, 2] and partnership_data[4] != b'':
			aes_encrypted = partnership_data[4]
			to_be_decrypted = True
		else :
			to_be_decrypted = False
		print('to be decrypted = ', to_be_decrypted)

	else : 	# workspace_contract_from != wokspace_contract_user and privacy == secret or private_key_from is None:
		to_be_decrypted = False
		privacy = 'secret'
		print('workspace_contract_from != wokspace_contract_user and privacy == secret or private_key_from is None')

	# data decryption
	if to_be_decrypted :
		# read la cle RSA privee sur le fichier du from
		contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
		address_from = contract.functions.contractsToOwners(workspace_contract_from).call()
		RSA_filename = "./RSA_key/"+mode.BLOCKCHAIN+'/' + address_from + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
		try :
			fp = open(RSA_filename,"r")
			rsa_key=fp.read()
			fp.close()
		except :
			print(' get_claim : cannot open rsa file to decrypt ')
			return issuer, identity_workspace_contract, None, "", 0, None, None, None, privacy,topic_value, None
		# upload data encrypted from ipfs
		print('ipfs hash = ', ipfs_hash, ' topicname = ', privacy, data)
		data_encrypted = ipfs_get(ipfs_hash)
		# decoder la cle AEScryptée avec la cle RSA privée
		key = RSA.importKey(rsa_key)
		cipher = PKCS1_OAEP.new(key)
		aes = cipher.decrypt(aes_encrypted)
		# decoder les datas
		try:
			b64 = data_encrypted
			json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
			jv = {k:b64decode(b64[k]) for k in json_k}
			cipher = AES.new(aes, AES.MODE_EAX, nonce=jv['nonce'])
			cipher.update(jv['header'])
			plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
			msg = json.loads(plaintext.decode('utf-8'))
			data =  msg[topicname] 
		except ValueError :
			print("data decryption error")
			return issuer, identity_workspace_contract, None, "", 0, None, None, None, privacy,topic_value, None

	# get transaction info
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	claim_filter = contract.events.ClaimAdded.createFilter(fromBlock=mode.fromBlock,toBlock = 'latest')
	event_list = claim_filter.get_all_entries()
	found = False
	for claim in event_list :
		if claim['args']['claimId'].hex() == claim_id :
			found = True
			transactionhash = claim['transactionHash']
			transaction_hash = transactionhash.hex()
			try :
				transaction = w3.eth.getTransaction(transaction_hash)
				gas_price = transaction['gasPrice']
				identity_workspace_contract = transaction['to'] 
				block_number = transaction['blockNumber']
				block = mode.w3.eth.getBlock(block_number)
				date = datetime.fromtimestamp(block['timestamp'])
				gas_used = 1000
				#gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
				created = str(date)
			except :
				print( 'probleme avec dans get claim')
				return issuer, identity_workspace_contract, None, "", 0, None, None, None, 'public',topic_value, None
			break
	if not found :
		print( 'probleme avec dans get claim')
		return issuer, identity_workspace_contract, None, "", 0, None, None, None, 'public',topic_value, None
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
	if receipt['status'] == 0 :
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
		self.created = created
		self.transaction_hash = transaction_hash
		self.issuer = issuer
		self.transaction_fee = transaction_fee
		self.claim_id = claim_id
		self.ipfs_hash = ipfs_hash
		self.data_location = data_location
		self.privacy = privacy
		self.identity = identity
		self.claim_value = claim_value

	def relay_add(self, identity_workspace_contract, topicname, data, privacy, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create_claim(mode.relay_address,mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, topicname, data, privacy, mode, synchronous = True) 

	def add(self, address_from,workspace_contract_from, address_to, workspace_contract_to,private_key_from, topicname, data, privacy, mode, synchronous = True) :
		return create_claim(address_from,workspace_contract_from, address_to, workspace_contract_to,private_key_from, topicname, data, privacy, mode, synchronous = True)

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
		if issuer_address is not None :
			issuer_workspace_contract = owners_to_contracts(issuer_address, mode)
			(issuer_profil, issuer_category) = read_profil(issuer_workspace_contract, mode, loading)
			issuer_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:]
		else :
			return
		self.created = created
		self.topicname = topicvalue2topicname(self.topicvalue)
		self.claim_value = data
		self.issuer = {'address' : issuer_address,
						'workspace_contract' : issuer_workspace_contract,
						'category' : issuer_category,
						'id' : issuer_id}
		self.issuer.update(issuer_profil)
		self.transaction_hash = transaction_hash
		self.transaction_fee = transaction_fee
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
		return
