import json
import hashlib
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import ipfshttpclient
from base64 import b64encode
from datetime import datetime, timedelta
from eth_account import Account
from eth_account.messages import encode_defunct
from base64 import b64encode, b64decode


#dependances
import constante

def get_username(workspace_contract,mode) :
	for a in mode.register  :
		if mode.register[a].get('workspace_contract') == workspace_contract :
			return  mode.register[a].get('username')
	return None

			
def contracts_to_owners(workspace_contract, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.contractsToOwners(workspace_contract).call()	 
 

def owners_to_contracts(address, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.ownersToContracts(address).call()
	
def ipfs_add(json_data) :
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https', chunk_size=35000)
	response=client.add_json(json_data)
	response2=client.pin.add(response)
	return response


def ipfs_get(ipfs_hash) :
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	return(client.get_json(ipfs_hash))


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

def read_profil (workspace_contract, mode) :
	w3=mode.w3
	# setup constante person
	person= {'firstname' : 102105114115116110097109101,
			'lastname' : 108097115116110097109101,
			'url' : 117114108,
			'email' : 101109097105108
			}
	# setup constant company
	company = {'name' : 110097109101,
				'contact_name' : 99111110116097099116095110097109101,
				'contact_email' : 99111110116097099116095101109097105108,
				'contact_phone' : 99111110116097099116095112104111110101,
				'website' : 119101098115105116101,
				'email' : 101109097105108
				}

	profil = dict()
	# category
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	category = contract.functions.identityInformation().call()[1]	
	
	# if person
	if category == 1001 : 
		for topicname, topic in person.items() :
			claim = contract.functions.getClaimIdsByTopic(topic).call()
			if len(claim) == 0 :
				profil[topicname] = None			
			else :
				claimId = claim[-1].hex()
				data = contract.functions.getClaim(claimId).call()
				profil[topicname]=data[4].decode('utf-8')					
	if category == 2001 : 
		for topicname, topic in company.items() :
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
	#recuperer ma cle AES cryptée
	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	mydata = contract.functions.identityInformation().call()
	if privacy == 'private' :
		my_aes_encrypted = mydata[5]
	if privacy == 'secret' :
		my_aes_encrypted = mydata[6] 
	
	identity_address = contracts_to_owners(identity_workspace_contract, mode)
	filename = "./RSA_key/"+mode.BLOCKCHAIN + '/' + identity_address + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1" + ".txt"
	with open(filename,"r") as fp :
		my_rsa_key = fp.read()	
		fp.close()   

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


def decrypt_data(identity_workspace_contract, data, privacy, mode) :
	w3 = mode.w3

	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	mydata = contract.functions.identityInformation().call()
	if privacy == 'private' :
		aes_encrypted = mydata[5]
	if privacy == 'secret' :
		aes_encrypted = mydata[6]  
		
	# read ma cle privee RSA sur le fichier
	identity_address = contracts_to_owners(identity_workspace_contract, mode)
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+identity_address + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	with open(filename,"r") as fp :
		my_rsa_key=fp.read()	
		fp.close()   
					
	# decoder ma cle AES128 cryptée avec ma cle RSA privée
	key = RSA.importKey(my_rsa_key)
	cipher = PKCS1_OAEP.new(key)	
	aes = cipher.decrypt(aes_encrypted)
		
	# decoder les datas
	try:
		b64 = data #json.loads(json_input)
		json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
		jv = {k:b64decode(b64[k]) for k in json_k}
		cipher = AES.new(aes, AES.MODE_EAX, nonce=jv['nonce'])
		cipher.update(jv['header'])
		plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
		msg = json.loads(plaintext.decode('utf-8'))
		return msg 
			
	except ValueError :
		print("data Decryption error")
		return None
		
		
		
""" data = 'pierre' si crypté alors data = 'private' et on encrypte un dict { 'firstane' ; 'pierre'} """
def create_claim(address_from,workspace_contract_from, address_to, workspace_contract_to,private_key_from, topicname, data, privacy, mode, synchronous = True) :
	# @data = str
	w3 = mode.w3
	
	topicvaluestr =''
	for i in range(0, len(topicname))  :
		a = str(ord(topicname[i]))
		if int(a) < 100 :
			a='0'+a
		topicvaluestr = topicvaluestr + a
	topic_value = int(topicvaluestr)
	
	if privacy == 'public' :
		ipfs_hash = "" 
	else : 
		data_encrypted = encrypt_data(workspace_contract_to,{topicname : data}, privacy, mode)
		ipfs_hash = ipfs_add(data_encrypted)
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
		w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	return claim_id, ipfs_hash, transaction_hash
	
	
def get_claim(workspace_contract_from, private_key_from, identity_workspace_contract, topicname, mode) :
	w3 = mode.w3
	
	topicvaluestr =''
	for i in range(0, len(topicname))  :
		a = str(ord(topicname[i]))
		if int(a) < 100 :
			a='0'+a
		topicvaluestr = topicvaluestr + a
	topic_value = int(topicvaluestr)
	
	contract = w3.eth.contract(identity_workspace_contract,abi=constante.workspace_ABI)
	a = contract.functions.getClaimIdsByTopic(topic_value).call()
	if len(a) == 0 :
	 return None, identity_workspace_contract, None, "", 0, None, None, None, None,topic_value, None
	claim_id = a[-1].hex()
	claim = contract.functions.getClaim(claim_id).call()
	data = claim[4].decode('utf-8') 	# data public
	ipfs_hash = claim[5]
	issuer = claim[2]
	scheme = claim[1]
	if data == 'private' or data == 'secret':
		privacy = data
		data_encrypted = ipfs_get(ipfs_hash)
		data = decrypt_data(identity_workspace_contract, data_encrypted, privacy, mode)[topicname]
	else :
		privacy = 'public'
	
	# get transaction info
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	claim_filter = contract.events.ClaimAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
	event_list = claim_filter.get_all_entries()
	for claim in event_list :
		
		if claim['args']['claimId'].hex() == claim_id :
			transactionhash = claim['transactionHash']
			transaction_hash = transactionhash.hex()
			transaction = w3.eth.getTransaction(transaction_hash)
			gas_price = transaction['gasPrice']
			identity_workspace_contract = transaction['to'] 
			block_number = transaction['blockNumber']
			block = mode.w3.eth.getBlock(block_number)
			date = datetime.fromtimestamp(block['timestamp'])				
			gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
			created = str(date)
	
	return issuer, identity_workspace_contract, data, ipfs_hash, gas_price*gas_used, transaction_hash, scheme, claim_id, privacy,topic_value, created

def get_claim_by_id(workspace_contract_from, private_key_from, identity_workspace_contract, claim_id, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	claim = contract.functions.getClaim(claim_id).call()
	data = claim[4].decode('utf-8') 	# data public
	ipfs_hash = claim[5]
	issuer = claim[2]
	scheme = claim[1]
	topic_value = claim[0]
	topicname = topicvalue2topicname(topic_value)
	
	if data == 'private' or data == 'secret':
		privacy = data
		data_encrypted = ipfs_get(ipfs_hash)
		data = decrypt_data(identity_workspace_contract, data_encrypted, privacy, mode)[topicname]
	else :
		privacy = 'public'
	
	# get transaction info
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	claim_filter = contract.events.ClaimAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
	event_list = claim_filter.get_all_entries()
	for claim in event_list :
		
		if claim['args']['claimId'].hex() == claim_id :
			transactionhash = claim['transactionHash']
			transaction_hash = transactionhash.hex()
			transaction = w3.eth.getTransaction(transaction_hash)
			gas_price = transaction['gasPrice']
			identity_workspace_contract = transaction['to'] 
			block_number = transaction['blockNumber']
			block = mode.w3.eth.getBlock(block_number)
			date = datetime.fromtimestamp(block['timestamp'])				
			gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
			created = str(date)
	
	return issuer, identity_workspace_contract, data, ipfs_hash, gas_price*gas_used, transaction_hash, scheme, claim_id, privacy,topic_value, created

def delete_claim(address_from, workspace_contract_from, address_to, workspace_contract_to,private_key_from,claim_id, mode):
	
	w3=mode.w3
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)

	# Build transaction
	txn = contract.functions.removeClaim(claimId).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)		
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	transaction_hash =w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
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
				topic_value=None,
				topic_name=None,
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
		
		self.topic_value = topic_value
		self.topic_name = topic_name
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
	
	def relay_delete(self, identity_workspace_contract, claim_id, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return  delete_claim(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, claim_id, mode)	
	
	def relay_get(self, identity_workspace_contract, topic_name, mode) :	
		
		(issuer_address, identity_workspace_contract, data, ipfs_hash, transaction_fee, transaction_hash, scheme, claim_id, privacy, topic_value, created) = get_claim(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, topic_name, mode)
		if issuer_address is not None :
			issuer_workspace_contract = owners_to_contracts(issuer_address, mode)
			(profil, category) = read_profil(issuer_workspace_contract, mode)
		else :
			issuer_workspace_contract = None
			(profil, category) = (dict(), 1001)
		this_claim=dict()
		this_claim['created'] = created
		this_claim['topic_name'] = topic_name
		this_claim['topic_value'] = topic_value
		this_claim['claim_value'] = data
		this_claim['issuer']= {'address' : issuer_address,
						'workspace_contract' : issuer_workspace_contract,
						'category' : category}
		this_claim['issuer']['type'] = 'Person' if category == 1001 else 'Company'
		this_claim['issuer']['username'] = get_username(issuer_workspace_contract, mode)
		this_claim['issuer'].update(profil)
		this_claim['transaction_hash'] = transaction_hash
		this_claim['transaction_fee'] = transaction_fee
		this_claim['ipfs_hash'] = ipfs_hash
		this_claim['data_location'] = 'https://ipfs.infura.io/ipfs/'+ ipfs_hash
		this_claim['privacy'] = privacy
		this_claim['claim_id'] = claim_id
		this_claim['identity']= {'address' : contracts_to_owners(identity_workspace_contract, mode),
								'workspace_contract' : identity_workspace_contract}
		this_claim['transaction_fee'] = transaction_fee
		return Claim(**this_claim)
			
	def relay_get_by_id(self, identity_workspace_contract, claim_id, mode) :		
		(issuer_address, identity_workspace_contract, data, ipfs_hash, transaction_fee, transaction_hash, scheme, claim_id, privacy, topic_value, created) = get_claim_by_id(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, claim_id, mode)
		if issuer_address is not None :
			issuer_workspace_contract = owners_to_contracts(issuer_address, mode)
			(profil, category) = read_profil(issuer_workspace_contract, mode)
		else :
			issuer_workspace_contract = None
			(profil, category) = (dict(), 1001)
		this_claim=dict()
		this_claim['created'] = created
		this_claim['topic_name'] = topicvalue2topicname(topic_value)
		this_claim['topic_value'] = topic_value
		this_claim['claim_value'] = data
		this_claim['issuer']= {'address' : issuer_address,
						'workspace_contract' : issuer_workspace_contract,
						'category' : category}
		this_claim['issuer']['type'] = 'Person' if category == 1001 else 'Company'
		this_claim['issuer']['username'] = get_username(issuer_workspace_contract, mode)
		this_claim['issuer'].update(profil)
		this_claim['transaction_hash'] = transaction_hash
		this_claim['transaction_fee'] = transaction_fee
		this_claim['ipfs_hash'] = ipfs_hash
		this_claim['data_location'] = 'https://ipfs.infura.io/ipfs/'+ ipfs_hash
		this_claim['privacy'] = privacy
		this_claim['claim_id'] = claim_id
		this_claim['identity']= {'address' : contracts_to_owners(identity_workspace_contract, mode),
								'workspace_contract' : identity_workspace_contract}
		this_claim['transaction_fee'] = transaction_fee
		return Claim(**this_claim)
	
