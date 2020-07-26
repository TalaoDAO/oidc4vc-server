import json
import hashlib
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from eth_account import Account
from base64 import b64encode
from datetime import datetime, timedelta
from base64 import b64encode, b64decode

from Talao_ipfs import ipfs_add, ipfs_get

#dependances
import constante

 
def contracts_to_owners(workspace_contract, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.contractsToOwners(workspace_contract).call()	 
 

def owners_to_contracts(address, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.ownersToContracts(address).call()
	

def read_profil (workspace_contract, mode, loading) :
	w3 = mode.w3
	# setup constante person
	person_topicnames = {'firstname' : 102105114115116110097109101,
						'lastname' : 108097115116110097109101,
						'contact_email' : 99111110116097099116095101109097105108,
						'contact_phone' : 99111110116097099116095112104111110101,
						'postal_address' : 112111115116097108095097100100114101115115,
						'birthdate' : 98105114116104100097116101,
						'about' : 97098111117116,
						'education' : 101100117099097116105111110,
						'profil_title' : 112114111102105108095116105116108101}
			
	# setup constant company
	company_topicnames = {'name' : 110097109101,
						'contact_name' : 99111110116097099116095110097109101,
						'contact_email' : 99111110116097099116095101109097105108,
						'contact_phone' : 99111110116097099116095112104111110101,
						'website' : 119101098115105116101,
						'about' : 97098111117116,}

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
 	 

def create_document(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, doctype, data, mydays, privacy, mode, synchronous) :
# @data = dict	
	w3=mode.w3	
	
	# cryptage des données par le user
	if privacy != 'public' :
		encrypted_data = data
		#recuperer la cle AES cryptée
		contract = w3.eth.contract(workspace_contract_to,abi = constante.workspace_ABI)
		mydata = contract.functions.identityInformation().call()
		if privacy == 'private' :
			my_aes_encrypted = mydata[5]
		if privacy == 'secret' :
			my_aes_encrypted = mydata[6]

		# read la cle privee RSA sur le fichier
		filename = "./RSA_key/"+mode.BLOCKCHAIN + '/' + address_to + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1" + ".txt"
		with open(filename,"r") as fp :
			my_rsa_key = fp.read()	
			fp.close()   

		# decoder la cle AES128 cryptée avec la cle RSA privée
		key = RSA.importKey(my_rsa_key)
		cipher = PKCS1_OAEP.new(key)	
		my_aes = cipher.decrypt(my_aes_encrypted)
		
		# coder les datas
		bytesdatajson = bytes(json.dumps(encrypted_data), 'utf-8') # dict -> json(str) -> bytes
		header = b"header"
		cipher = AES.new(my_aes, AES.MODE_EAX) #https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html
		cipher.update(header)
		ciphertext, tag = cipher.encrypt_and_digest(bytesdatajson)
		json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
		json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, header, ciphertext, tag] ]
		data = dict(zip(json_k, json_v))
	
			
	# calcul de la date
	if mydays == 0 :
		expires = 0
	else :	
		myexpires = datetime.utcnow() + datetime.timedelta(days = mydays, seconds = 0)
		expires = int(myexpires.timestamp())	
		
	#envoyer la transaction sur le contrat
	contract = w3.eth.contract(workspace_contract_to,abi = constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)  
	
	# stocke sur ipfs les data attention on archive des bytes
	ipfs_hash = ipfs_add(data)
	if ipfs_hash is None :
		return None
	
	# calcul du checksum en bytes des data, conversion du dictionnaire data en chaine str
	_data = json.dumps(data)
	checksum = hashlib.md5(bytes(_data, 'utf-8')).hexdigest()
	# la conversion inverse de bytes(data, 'utf-8') est XXX.decode('utf-8')
	
	encrypted = False if privacy == 'public' else True
	# Transaction
	txn = contract.functions.createDocument(doctype,2,expires,checksum,1, bytes(ipfs_hash, 'utf-8'), encrypted).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(transaction_hash)		
	
	# recuperer l iD du document sur le dernier event DocumentAdded
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	myfilter = contract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
	eventlist = myfilter.get_all_entries()
	document_id = eventlist[-1]['args']['id']
	return document_id, ipfs_hash, transaction_hash
	
def update_document(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, doc_id, doctype, data, mydays, privacy, mode, synchronous) :
# @data = dict	
	w3=mode.w3	
	privacy = 'public'		
	# calcul de la date
	if mydays == 0 :
		expires = 0
	else :	
		myexpires = datetime.utcnow() + datetime.timedelta(days = mydays, seconds = 0)
		expires = int(myexpires.timestamp())	
		
	#envoyer la transaction sur le contrat
	contract = w3.eth.contract(workspace_contract_to,abi = constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)  
	
	# stocke sur ipfs les data attention on archive des bytes
	ipfs_hash = ipfs_add(data)
	if ipfs_hash is None :
		return None
	
	# calcul du checksum en bytes des data, conversion du dictionnaire data en chaine str
	_data = json.dumps(data)
	checksum = hashlib.md5(bytes(_data, 'utf-8')).hexdigest()
	# la conversion inverse de bytes(data, 'utf-8') est XXX.decode('utf-8')
	
	encrypted = False if privacy == 'public' else True
	# Transaction
	txn = contract.functions.updateDocument(doc_id, doctype,2,expires,checksum,1, bytes(ipfs_hash, 'utf-8'), encrypted).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(transaction_hash)		
	
	# recuperer l iD du document sur le dernier event DocumentAdded
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	myfilter = contract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
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
	claim_filter = contract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
	event_list = claim_filter.get_all_entries()
	for doc in event_list :
		if doc['args']['id'] == documentId :
			transactionhash = doc['transactionHash']
			transaction_hash = transactionhash.hex()
			try : 
				transaction = w3.eth.getTransaction(transaction_hash)
			except :
				print('error dans document.py, ligne 219', documentId, doctype, privacy, transaction_hash)
				return None, None, None, None, None, None, None, None, None, None, None , None, None
			gas_price = transaction['gasPrice']
			identity_workspace_contract = transaction['to'] 
			block_number = transaction['blockNumber']
			block = mode.w3.eth.getBlock(block_number)
			date = datetime.fromtimestamp(block['timestamp'])
			gas_used = 1000				
			#gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
			created = str(date)

	# recuperation du msg 
	data = ipfs_get(ipfshash.decode('utf-8'))
	# calcul de la date
	if expires == 0 :
		expires = 'Unlimited'
	else :	
		myexpires = datetime.fromtimestamp(expires)
		#expires = myexpires.strftime("%y/%m/%d")
		expires = str(myexpires)

	if privacy  == 'public' :
		return issuer, identity_workspace_contract, data, ipfshash.decode('utf-8'), gas_price*gas_used, transaction_hash, doctype, doctypeversion, created, expires, issuer, privacy, related
	
	if encrypted != 'public' and private_key_from is None : 
		print ("document is  encrypted and no keys has been given ")
		return None, None, None, None, None, None, None, None, None, None, None , None, None

	#recuperer la cle AES cryptée
		contract = w3.eth.contract(workspace_contract_user,abi = constante.workspace_ABI)
		mydata = contract.functions.identityInformation().call()
		if privacy == 'private' :
			his_aes_encrypted = mydata[5]
		if privacy == 'secret' :
			his_aes_encrypted = mydata[6]
		
	# read la cle privee RSA sur le fichier
	address_user = contracts_to_owners(workspace_contract_user, mode)
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+address_from+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	try :
		fp = open(filename,"r")
		rsa_key = fp.read()
		fp.close()  
	except IOError :
		print ("RSA key file not found")
		return None, None, None, None, None, None, None, None, None, None, None , None, None	
					
	# decoder ma cle AES128 cryptée avec ma cle RSA privée
	key = RSA.importKey(rsa_key)
	cipher = PKCS1_OAEP.new(key)	
	his_aes=cipher.decrypt(his_aes_encrypted)
		
		# decoder les datas
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
		print("Data Decryption error")
		return None, None, None, None, None, None, None, None, None, None, None , None, None

				
def delete_document(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, documentId, mode):
	w3 = mode.w3
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token
	nonce = w3.eth.getTransactionCount(address_from)  
	# Build transaction
	txn = contract.functions.deleteDocument(int(documentId)).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
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
							
	def add(self, address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, data, mode, mydays=0, privacy='public', synchronous=True) :			 			
		return create_document(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, self.doctype, data, mydays, privacy, mode, synchronous)
							
	def relay_add(self, identity_workspace_contract, data, mode, mydays=0, privacy='public', synchronous=True) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create_document(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, self.doctype, data, mydays, privacy, mode, synchronous)
	
	def relay_update(self, identity_workspace_contract, doc_id, data, mode, mydays=0, privacy='public', synchronous=True) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return update_document(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, doc_id, self.doctype, data, mydays, privacy, mode, synchronous)
	
	def talao_add(self, identity_workspace_contract, data, mode, mydays=0, privacy='public', synchronous=True) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create_document(mode.owner_talao,  mode.workspace_contract_talao, identity_address, identity_workspace_contract, mode.owner_talao_private_key, self.doctype, data, mydays, privacy, mode, synchronous)
	
	def relay_get(self, identity_workspace_contract, doc_id, mode, loading='light') :	
		(issuer_address, identity_workspace_contract, data, ipfshash, transaction_fee, transaction_hash, doctype, doctypeversion, created, expires, issuer, privacy, related) = get_document(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, doc_id, mode)
		
		if issuer_address is None :
			return False
		else :	
			self.__dict__.update(data)
			issuer_workspace_contract = owners_to_contracts(issuer_address, mode)
			(issuer_profil, issuer_category) = read_profil(issuer_workspace_contract, mode, loading)
			issuer_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:]
		
			self.created = created
			self.issuer = {'address' : issuer_address,
						'workspace_contract' : issuer_workspace_contract,
						'category' : issuer_category,
						'id' : issuer_id}
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
