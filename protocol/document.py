import json
import hashlib
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import ipfshttpclient
from eth_account import Account
from base64 import b64encode
from datetime import datetime, timedelta
from base64 import b64encode, b64decode


#dependances
import constante

def ipfs_add(json_data) :
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https', chunk_size=35000)
	response=client.add_json(json_data)
	response2=client.pin.add(response)
	return response

def ipfs_get(ipfs_hash) :
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	return(client.get_json(ipfs_hash))
	
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
 	 

def create_document(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, doctype, data, mydays, privacy, mode, synchronous=True) :
# @data = dict	
	w3=mode.w3	
	
	# cryptage des données par le user
	if privacy != 'public' :
		encrypted_data = data
		#recuperer ma cle AES cryptée
		contract = w3.eth.contract(workspace_contract_from,abi = constante.workspace_ABI)
		mydata = contract.functions.identityInformation().call()
		if privacy == 'private' :
			my_aes_encrypted = mydata[5]
		if privacy == 'secret' :
			my_aes_encrypted = mydata[5]

		# read ma cle privee RSA sur le fichier
		filename = "./RSA_key/"+mode.BLOCKCHAIN + '/' + address_from + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1" + ".txt"
		with open(filename,"r") as fp :
			my_rsa_key = fp.read()	
			fp.close()   

		# decoder ma cle AES128 cryptée avec ma cle RSA privée
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
	
	
def get_document(workspace_contract_from, private_key_from, workspace_contract_user, documentId, mode) :
	w3=mode.w3
	contract = w3.eth.contract(workspace_contract_user,abi=constante.workspace_ABI)
	(doctype, doctypeversion, expires, issuer, checksum, engine, ipfshash, encrypted, related) = contract.functions.getDocument(documentId).call()
	
	if doctype == 50000 or doctype == 30000 or doctype == 40000 :
		privacy = 'public'
	if doctype == 50001 or doctype == 30001 :
		privacy = 'private'
	if doctype == 50002 or doctype == 30002 :
		privacy = 'secret'
	
	# get transaction info
	contract = w3.eth.contract(workspace_contract_user, abi=constante.workspace_ABI)
	claim_filter = contract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
	event_list = claim_filter.get_all_entries()
	for doc in event_list :
		if doc['args']['id'] == documentId :
			transactionhash = doc['transactionHash']
			transaction_hash = transactionhash.hex()
			transaction = w3.eth.getTransaction(transaction_hash)
			gas_price = transaction['gasPrice']
			identity_workspace_contract = transaction['to'] 
			block_number = transaction['blockNumber']
			block = mode.w3.eth.getBlock(block_number)
			date = datetime.fromtimestamp(block['timestamp'])				
			gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
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
	
	if encrypted != 'public' and private_key_from == None : 
		print ("document is  encrypted and no keys has been given ")
		return None
	
	# verifier si ils sont en partnership
	contract=w3.eth.contract(workspace_contract_from,abi=constante.workspace_ABI)
	acct =Account.from_key(private_key_from)
	w3.eth.defaultAccount=acct.address
	mypartnershiplist = contract.functions.getKnownPartnershipsContracts().call()
	if workspace_contract_user in mypartnershiplist : # ils sont en partnership			
		contract=w3.eth.contract(workspace_contract_from,abi=constante.workspace_ABI)
		if privacy == 'private' :
			his_aes_encrypted=contract.functions.getPartnership(workspace_contract_user).call()[4] 
		if privacy == 'secret' :
			his_aes_encrypted=contract.functions.getPartnership(workspace_contract_user).call()[5] 
		
		# read ma cle privee RSA sur le fichier
		address_from = contracts_to_owners(workspace_contract_from, mode)
		filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+address_from+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
		with open(filename,"r") as fp :
			my_rsa_key=fp.read()	
			fp.close()   
					
		# decoder sa cle AES128 cryptée avec ma cle RSA privée
		key = RSA.importKey(my_rsa_key)
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
			print("data Decryption error")
			return None
	else :
		print ("document is encrypted private_key has been given but there is no partnership between them")
		return None

				
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
	transaction = w3.eth.getTransaction(transaction_hash)
	gas_price = transaction['gasPrice']
	block_number = transaction['blockNumber']
	block = mode.w3.eth.getBlock(block_number)
	date = datetime.fromtimestamp(block['timestamp'])				
	gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
	deleted = date.strftime("%y/%m/%d")		
	return transaction_hash, gas_used*gas_price, deleted

class Document() :
	def __init__(self,
				start_date=None,
				end_date=None,
				title=None,
				skills=[],
				description=None,
				certificate_link=None,
				created=None,
				transaction_hash=None,
				issuer = None,
				transaction_fee= None,
				doctypeversion = None,
				doc_id = None,
				ipfshash = None,
				data_location=None,
				expires = 0,
				privacy = 'public',
				identity = None
				) :		
		
		self.title = title
		self.description = description
		self.start_date = start_date
		self.end_date = end_date
		self.skills = skills
		self.certificate_link = certificate_link
		self.created = created
		self.transaction_hash = transaction_hash
		self.doc_id = doc_id
		self.issuer = issuer
		self.transaction_fee = transaction_fee
		self.doctypeversion = doctypeversion
		self.ipfshash = ipfshash
		self.data_location = data_location
		self.expires = expires
		self.privacy = privacy
		self.identity = identity
					
	def relay_add(self, identity_workspace_contract, mode, mydays=0, privacy='public', synchronous=True) :			
		data = self.__dict__
		print('data = ',data)
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create_document(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, data['doctype'], data, mydays, privacy, mode, synchronous=True)
	
	def relay_get(self, identity_workspace_contract, doc_id, mode) :	
		(issuer_address, identity_workspace_contract, data, ipfshash, transaction_fee, transaction_hash, doctype, doctypeversion, created, expires, issuer, privacy, related) = get_document(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, doc_id, mode)
		issuer_workspace_contract = owners_to_contracts(issuer_address, mode)
		(profil, category) = read_profil(issuer_workspace_contract, mode)
		data['created'] = created
		data['issuer']= {'address' : issuer_address,
						'workspace_contract' : issuer_workspace_contract,
						'category' : category}
		data['issuer']['type'] = 'Person' if category == 1001 else 'Company'
		data['issuer']['username'] = get_username(issuer_workspace_contract, mode)
		data['issuer'].update(profil)
		data['transaction_hash'] = transaction_hash
		data['transaction_fee'] = transaction_fee
		data['doctypeversion'] = doctypeversion
		data['ipfshash'] = ipfshash
		data['data_location'] = 'https://ipfs.infura.io/ipfs/'+ ipfshash
		data['expires'] = expires
		data['privacy'] = privacy
		data['doc_id'] = doc_id
		data['identity']= {'address' : contracts_to_owners(identity_workspace_contract, mode),
							'workspace_contract' : identity_workspace_contract}
		data['transaction_fee'] = transaction_fee
		del data['doctype']
		if doctype == 50000 or doctype == 50001 or doctype == 50002 :
			return Experience(**data)
		if doctype == 40000 :
			return Education(**data)
		if doctype == 30000 or doctype == 30001 or doctype == 30002 :
			return File(**data)	
			
	def relay_delete(self, identity_workspace_contract, doc_id, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return delete_document(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, doc_id, mode)
	


class Education(Document) :
	def __init__(self,
				organization= {'name' : None,
								'contact_name' : None,
								'contact_email' : None,
								'contact_phone' : None,
								'website' : None,
								'address' : None,
								'workspace_contract' : None},
				start_date=None,
				end_date=None,
				title=None,
				skills=[],
				description=None,
				doc_id=None,
				certificate_link=None,
				topic = 'Education',				
				created=None,
				transaction_hash=None,
				issuer = None,							
				transaction_fee= None,
				doctypeversion = None,
				ipfshash = None,
				data_location=None,
				expires = 0,
				privacy = 'public',
				identity = { 'address' : None,
							'workspace_contract' : None},
				) :		
		Document.__init__(self,
				start_date,
				end_date,
				title,
				skills,
				description,
				certificate_link,
				created,
				transaction_hash,
				issuer,
				transaction_fee,
				doctypeversion,
				doc_id,
				ipfshash,
				data_location,
				expires,
				privacy,
				identity
				)	
		self.topic = topic
		self.doctype = 40000
		self.organization = organization


class Experience(Document) :
	def __init__(self,
				company = {'name' : None,
							'contact_name' : None,
							'contact_email' : None,
							'contact_phone' : None,
							'website' : None,
							'address' : None,
							'workspace_contract' : None}, 
				start_date=None,
				end_date=None,
				title=None,
				skills=[],
				description=None,
				certificate_link=None,
				topic = 'Experience',
				created=None,
				doc_id= None,
				transaction_hash=None,
				issuer = None,
				transaction_fee= None,
				doctypeversion = None,
				ipfshash = None,
				data_location=None,
				expires = 0,
				privacy = 'public',
				identity = {'address' : None,
							'workspace_contract' : None}
				) :	
		Document.__init__(self,
				start_date,
				end_date,
				title,
				skills,
				description,
				certificate_link,
				created,
				transaction_hash,
				issuer,
				transaction_fee,
				doctypeversion,
				doc_id,
				ipfshash,
				data_location,
				expires,
				privacy,
				identity
				)		
		self.topic = topic
		self.company = company
		if self.privacy == 'public' :
			self.doctype = 50000
		if self.privacy == 'private' :
			self.doctype = 50001
		if self.privacy == 'secret' :
			self.doctype == 50002	
		


class File(Document) :
	def __init__(self,
				start_date=None,
				end_date=None,
				title=None,
				skills=[],
				description=None,
				certificate_link=None,
				doctype= None,
				topic = 'Experience',
				created=None,
				doc_id= None,
				transaction_hash=None,
				issuer = None,
				transaction_fee= None,
				doctypeversion = None,
				ipfshash = None,
				data_location=None,
				expires = 0,
				privacy = 'public',
				identity = {'address' : None,
							'workspace_contract' : None}
				) :	
		Document.__init__(self,
				start_date,
				end_date,
				title,
				skills,
				description,
				certificate_link,
				created,
				transaction_hash,
				issuer,
				transaction_fee,
				doctypeversion,
				doc_id,
				ipfshash,
				data_location,
				expires,
				privacy,
				identity
				)		
		self.topic = topic
		self.company = company
		if self.privacy == 'public' :
			self.doctype = 30000
		if self.privacy == 'private' :
			self.doctype = 30001
		if self.privacy == 'secret' :
			self.doctype == 30002	
		

"""  exemple
creation

my_experience = Experience()
my_experience.title = 'CFO'
my_experience.start_date = "20/02/02"
...
my_experience.relay_add(w, mode))


get 
my_experience = Experience().relay_get(w, 14, mode)

delete
Experience.relay_delete(w, 14, mode)
"""

