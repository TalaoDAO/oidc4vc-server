import json
import hashlib
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import ipfshttpclient
from eth_account import Account
from datetime import datetime, timedelta
from base64 import b64encode, b64decode


#dependances
import constante
import environment


# environment setup
mode=environment.currentMode()
w3=mode.w3

def ipfs_add(json_data) :
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https', chunk_size=1000000)
	response=client.add_json(json_data)
	response2=client.pin.add(response)
	return response

def ipfs_get(ipfs_hash) :
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	return(client.get_json(ipfs_hash))

def add_file(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, doctype, file_name, mydays, privacy, mode, synchronous) :
	w3=mode.w3	
	
	try :
		this_file = open(file_name, mode='rb')  # b is important -> binary
		this_data = this_file.read()
	except :
		print('file error')
		return False
		
	data = {'filename' : file_name , 'content' : b64encode(this_data).decode('utf_8')}
	
	# cryptage des données par le user
	if privacy != 'public' :
		
		#recuperer les cle AES cryptée
		contract = w3.eth.contract(workspace_contract_to,abi = constante.workspace_ABI)
		mydata = contract.functions.identityInformation().call()
		if privacy == 'private' :
			aes_encrypted = mydata[5]
		if privacy == 'secret' :
			aes_encrypted = mydata[6]

		# read la cle privee RSA sur le fichier
		filename = "./RSA_key/"+mode.BLOCKCHAIN + '/' + address_to + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1" + ".txt"
		with open(filename,"r") as fp :
			my_rsa_key = fp.read()	
			fp.close()   

		# decoder la cle AES128 cryptée avec la cle RSA privée
		key = RSA.importKey(my_rsa_key)
		cipher = PKCS1_OAEP.new(key)	
		my_aes = cipher.decrypt(aes_encrypted)
		
		# coder les datas
		bytesdatajson = bytes(json.dumps(data), 'utf-8') # dict -> json(str) -> bytes
		header = b'header'
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
	#_data = json.dumps(data)
	#checksum = hashlib.md5(bytes(_data, 'utf-8')).hexdigest()
	# la conversion inverse de bytes(data, 'utf-8') est XXX.decode('utf-8')
	checksum = b''
	
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

	
def get_file(workspace_contract_from, private_key_from, workspace_contract_user, documentId, new_filename, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_user,abi=constante.workspace_ABI)
	(doctype, doctypeversion, expires, issuer, checksum, engine, ipfshash, encrypted, related) = contract.functions.getDocument(documentId).call()
	if doctype == 30000  :
		privacy = 'public'
	elif doctype == 30001 :
		privacy = 'private'
	elif doctype == 30002 :
		privacy = 'secret'
	else :
		print('error doctype ')
		return False
	
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
			#gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
			gas_used = 1000
			created = str(date)

	# recuperation du msg 
	data = ipfs_get(ipfshash.decode('utf-8'))
	# calcul de la date
	expires = 'Unlimited' if expires == 0 else str(datetime.fromtimestamp(expires))

	if privacy  != 'public' :		
	
		#recuperer les cle AES cryptée
		contract = w3.eth.contract(workspace_contract_user,abi = constante.workspace_ABI)
		mydata = contract.functions.identityInformation().call()
		if privacy == 'private' :
			his_aes_encrypted = mydata[5]
		if privacy == 'secret' :
			his_aes_encrypted = mydata[6]
		
		# read la cle privee RSA sur le fichier
		contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
		address_user = contract.functions.contractsToOwners(workspace_contract_user).call()
		filename = "./RSA_key/"+mode.BLOCKCHAIN+'/' + address_user + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
		with open(filename,"r") as fp :
			rsa_key=fp.read()	
			fp.close()   
					
		# decoder la cle AES128 cryptée avec la cle RSA privée
		key = RSA.importKey(rsa_key)
		cipher = PKCS1_OAEP.new(key)	
		his_aes = cipher.decrypt(his_aes_encrypted)
		
		# decoder les datas
		try:
			b64 = data #json.loads(json_input)
			json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
			jv = {k:b64decode(b64[k]) for k in json_k}
			cipher = AES.new(his_aes, AES.MODE_EAX, nonce=jv['nonce'])
			cipher.update(jv['header'])
			plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
			msg = json.loads(plaintext.decode('utf-8'))
			data = msg
		except ValueError :
			print("data Decryption error")
			return None
	
	if new_filename != "" :	
		new_file = open(new_filename, "wb")
		new_file.write(b64decode(data['content']))
		new_file.close()
	
	return issuer, identity_workspace_contract, data, ipfshash.decode('utf-8'), gas_price*gas_used, transaction_hash, doctype, doctypeversion, created, expires, issuer, privacy, related	
			
	
	


class File() :
	def __init__(self) :
		pass
	
	def get(self, workspace_contract_user, doc_id, new_filename, mode) :	
		(self.issuer,
		 self.identity_workspace_contract,
		 data,
		 self.ipfs_hash,
		 self.transaction_fee,
		 self.transaction_hash,
		 self.doctype,
		 self.doctypeversion,
		 self.created,
		 self.expires,
		 self.issuer_address,
		 self.privacy,
		 self.related) = get_file ("", "", workspace_contract_user, doc_id, new_filename, mode) 
		self.filename = data['filename']
		self.new_filename = new_filename
		self.doc_id = doc_id
		self.id = 'did:talao:' + mode.BLOCKCHAIN + ':' + self.identity_workspace_contract[2:] + ':document:' + str(doc_id)
		
		return
		
	def add(self, address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, file_name, privacy, mode, synchronous=True) :
		if privacy == 'public' :
			doctype = 30000
		if privacy == 'private' :
			doctype = 30001
		if privacy == 'private' :
			doctype = 30002
		mydays = 0
		(self.document_id, self.ipfs_hash, self.transaction_hash) = add_file(address_from,
																			workspace_contract_from,
																			address_to,
																			workspace_contract_to,
																			private_key_from,
																			doctype,
																			file_name,
																			mydays,
																			privacy,
																			mode,
																			synchronous)
		return self.document_id, self.ipfs_hash, self.transaction_hash
