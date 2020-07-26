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


def decrypt_data(identity_workspace_contract, data, privacy, rsa_key, mode) :
	w3 = mode.w3

	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	mydata = contract.functions.identityInformation().call()
	if privacy == 'private' :
		aes_encrypted = mydata[5]
	if privacy == 'secret' :
		aes_encrypted = mydata[6]  
					
	# decoder ma cle AES128 cryptée avec ma cle RSA privée
	key = RSA.importKey(rsa_key)
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
		ipfs_hash = ipfs_add(data_encrypted)
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
		w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	return claim_id, ipfs_hash, transaction_hash
	
	
def get_claim(identity_workspace_contract, topicname, mode) :
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
	 return None, identity_workspace_contract, None, "", 0, None, None, None, 'public',topic_value, None
	print('topic name = ', topicname)
	claim_id = a[-1].hex()
	print('claim id = ', claim_id)
	claim = contract.functions.getClaim(claim_id).call()
	data = claim[4].decode('utf-8') 	# data public
	ipfs_hash = claim[5]
	issuer = claim[2]
	scheme = claim[1]
	
	if data == 'private' or data == 'secret':
		# read la cle privee RSA sur le fichier
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+identity_address + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
		try :
			fp = open(filename,"r")
			rsa_key=fp.read()	
			fp.close()  
			privacy = data
			data_encrypted = ipfs_get(ipfs_hash)
			data = decrypt_data(identity_workspace_contract, data_encrypted, privacy, rsa_key, mode)[topicname]
		except :
			print('rsa key not found')
			privacy = data
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
			try :
				transaction = w3.eth.getTransaction(transaction_hash)
				print('ok transaction')
				gas_price = transaction['gasPrice']
				identity_workspace_contract = transaction['to'] 
				block_number = transaction['blockNumber']
				print('avant get block')
				block = mode.w3.eth.getBlock(block_number)
				print('apres get block')
				date = datetime.fromtimestamp(block['timestamp'])
				gas_used = 1000				
				#gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
				created = str(date)
			except :
				print( 'probleme avec ', topicname, ' dans get claim')
				return None, identity_workspace_contract, None, "", 0, None, None, None, 'public',topic_value, None
	
	return issuer, identity_workspace_contract, data, ipfs_hash, gas_price*gas_used, transaction_hash, scheme, claim_id, privacy,topic_value, created

def get_claim_by_id(identity_workspace_contract, claim_id, mode) :
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
		# read la cle privee RSA sur le fichier
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+identity_address + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
		try :
			fp = open(filename,"r")
			rsa_key=fp.read()	
			fp.close()  
			privacy = data
			data_encrypted = ipfs_get(ipfs_hash)
			data = decrypt_data(identity_workspace_contract, data_encrypted, privacy, rsa_key, mode)[topicname]
		except :
			privacy = data
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
	
	def get_by_topic_name(self, identity_workspace_contract, topicname, mode, loading='full') :	
		
		(issuer_address, identity_workspace_contract, data, ipfs_hash, transaction_fee, transaction_hash, scheme, claim_id, privacy, self.topicvalue, created) = get_claim( identity_workspace_contract, topicname, mode)
		if issuer_address is not None :
			issuer_workspace_contract = owners_to_contracts(issuer_address, mode)
			(profil, issuer_category) = read_profil(issuer_workspace_contract, mode, loading)
			issuer_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:]
		else :
			return False
		
		self.created = created
		self.topicname = topicname
		self.claim_value = data
		self.issuer = {'address' : issuer_address,
						'workspace_contract' : issuer_workspace_contract,
						'category' : issuer_category,
						'id' : issuer_id }
		self.issuer.update(profil)		
		self.transaction_hash = transaction_hash
		self.transaction_fee = transaction_fee
		self.ipfs_hash = ipfs_hash
		self.data_location = mode.BLOCKCHAIN if ipfs_hash == "" else 'https://gateway.ipfs.io/ipfs/' + ipfs_hash
		self.privacy = privacy
		self.claim_id = claim_id
		self.id = 'did:talao:' + mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:] + ':claim:' + str(claim_id)
		
		contract = mode.w3.eth.contract(identity_workspace_contract,abi=constante.workspace_ABI)
		identity_category = contract.functions.identityInformation().call()[1]
		
		self.identity = {'address' : contracts_to_owners(identity_workspace_contract, mode),
								'workspace_contract' : identity_workspace_contract,
								'category' : identity_category,
								'id' : 'did:talao:' + mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:]}
		return True
			
	def get_by_id(self, identity_workspace_contract, claim_id, mode, loading='full') :		
		(issuer_address, identity_workspace_contract, data, ipfs_hash, transaction_fee, transaction_hash, scheme, claim_id, privacy, self.topicvalue, created) = get_claim_by_id(identity_workspace_contract, claim_id, mode)
		if issuer_address is not None :
			issuer_workspace_contract = owners_to_contracts(issuer_address, mode)
			(issuer_profil, issuer_category) = read_profil(issuer_workspace_contract, mode, loading)
			issuer_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:]

		else :
			return False
			
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
		return True
	
