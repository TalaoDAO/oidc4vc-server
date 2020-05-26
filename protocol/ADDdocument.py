import hashlib
import json
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import datetime
import ipfshttpclient
from eth_account import Account
from base64 import b64encode, b64decode

#dependances
import constante
import Talao_ipfs


###################################################################
# @data = dictionnaire 
# @encrypted = False ou True => AES128 AES.MODE_EAX
# @expires : days from now, 0 if unlimited
# location engine = 1 pour IPFS, doctypeversion = 1, expire =Null, 
###################################################################
  

def createdocument(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, doctype, data, mydays, encrypted, mode, synchronous=True) :
	
	w3=mode.w3	
	
	# cryptage des données par le user
	if encrypted == True  and workspace_contract_from == workspace_contract_to :
		
		#recuperer ma cle AES cryptée
		contract = w3.eth.contract(workspace_contract_from,abi = constante.workspace_ABI)
		mydata = contract.functions.identityInformation().call()
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
		bytesdatajson = bytes(json.dumps(data), 'utf-8') # dict -> json(str) -> bytes
		header = b"header"
		cipher = AES.new(my_aes, AES.MODE_EAX) #https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html
		cipher.update(header)
		ciphertext, tag = cipher.encrypt_and_digest(bytesdatajson)
		json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
		json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, header, ciphertext, tag] ]
		result = dict(zip(json_k, json_v))
	
	else :
		result = data
			
	# calcul de la date
	if mydays == 0 :
		expires = 0
	else :	
		myexpires = datetime.datetime.utcnow() + datetime.timedelta(days = mydays, seconds = 0)
		expires = int(myexpires.timestamp())	
		
	#envoyer la transaction sur le contrat
	contract = w3.eth.contract(workspace_contract_to,abi = constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)  
	
	# stocke sur ipfs les data attention on archive des bytes
	ipfshash = Talao_ipfs.IPFS_add(result)
	
	# calcul du checksum en bytes des data, conversion du dictionnaire data en chaine str
	_data = json.dumps(data)
	checksum = hashlib.md5(bytes(_data, 'utf-8')).hexdigest()
	# la conversion inverse de bytes(data, 'utf-8') est XXX.decode('utf-8')
	
	# Transaction
	txn = contract.functions.createDocument(doctype,1,expires,checksum,1, bytes(ipfshash, 'utf-8'), encrypted).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	myhash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(myhash)		
	
	# recuperer l iD du document sur le dernier event DocumentAdded
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	myfilter = contract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
	#myfilter = contract.events.DocumentAdded.createFilter(fromBlock= 5800000)
	eventlist = myfilter.get_all_entries()
	l = len(eventlist)
	document_id = eventlist[l-1]['args']['id']
	return document_id
	
	
#################################################################################
# get document
#################################################################################
# from : celui qui veut acceder a l information du user

def getdocument(workspace_contract_from, private_key_from, workspace_contract_user, documentId, mode) :
	w3=mode.w3

	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address_from = contract.functions.contractsToOwners(workspace_contract_from).call()
	
	contract=w3.eth.contract(workspace_contract_user,abi=constante.workspace_ABI)
	(doctype, doctypeversion, expires, issuer, checksum, engine, ipfshash, encrypted, related) = contract.functions.getDocument(documentId).call()
	
	# recuperation du msg 
	data=Talao_ipfs.IPFS_get(ipfshash.decode('utf-8'))
	
	if encrypted == False :
		return data
	
	if encrypted == True and private_key_from == '0x0' : # pas de possiblite de decrypter
		print ("document is  encrypted and no keys has been given ")
		return None
	
	else :  # msg crypté
		
		# verifier si ils sont en partnership
		contract=w3.eth.contract(workspace_contract_from,abi=constante.workspace_ABI)
		acct =Account.from_key(private_key_from)
		w3.eth.defaultAccount=acct.address
		mypartnershiplist = contract.functions.getKnownPartnershipsContracts().call()
		if workspace_contract_user in mypartnershiplist : # ils sont en parnership
			
			contract=w3.eth.contract(workspace_contract_from,abi=constante.workspace_ABI)
			his_aes_encrypted=contract.functions.getPartnership(workspace_contract_user).call()[4] 
				
			# read ma cle privee RSA sur le fichier
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
				msg=json.loads(plaintext.decode('utf-8'))
				return msg				
			
			except ValueError :
				print("data Decryption error")
				return None
		else :
			print ("document is encrypted private_key has been given but there is no partnership between them")
			return None
				

	
