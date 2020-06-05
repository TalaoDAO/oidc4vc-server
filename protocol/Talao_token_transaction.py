from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import csv
import sys
import time
import hashlib
import json
import ipfshttpclient
from datetime import datetime
from eth_account.messages import encode_defunct
import random

# dependances
import Talao_ipfs
import Talao_message
import constante

############################################################
# appel de ownersToContracts de la fondation
############################################################
#
# Owners (EOA) to contract addresses relationships.
#   mapping(address => address) public ownersToContracts;

def ownersToContracts(address, mode) :
	w3=mode.initProvider()
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	workspace_address = contract.functions.ownersToContracts(address).call()
	return workspace_address
	
	
###########################################################
# remove workspace	
############################################################	
# function destroyWorkspace() external onlyIdentityOwner {
#        if (cleanupPartnership() && foundation.renounceOwnershipInFoundation()) {
#            selfdestruct(msg.sender);	

def destroyWorkspace(workspace_contract, private_key, mode) :
	w3=mode.initProvider()
	address=contractsToOwners(workspace_contract, mode)
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	
	# calcul du nonce de l envoyeur de token
	nonce = w3.eth.getTransactionCount(address)  
	
	# Build transaction
	txn = contract.functions.destroyWorkspace().buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
		
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)		
	return hash1
	

############################################################
# appel de contractsToOwners de la fondation
############################################################
#
def contractsToOwners(workspace_contract, mode) :
	w3=mode.initProvider()
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	return address	

###############################################################
# DEPRECATED cf ReadProfil de GetResume read Talao profil
###############################################################
# return a dictionnaire {'givenName' ; 'Jean', 'familyName' ; 'Pascal'.....
# https://fr.wikibooks.org/wiki/Les_ASCII_de_0_%C3%A0_127/La_table_ASCII
# ord('a')=97...attention ajouté un 0 au dessus dessous de 99....

def readProfil (address,mode) :

	w3=mode.w3

	# liste des claim topic , 
	givenName = 103105118101110078097109101
	familyName = 102097109105108121078097109101
	jobTitle = 106111098084105116108101
	worksFor = 119111114107115070111114
	workLocation = 119111114107076111099097116105111110
	url = 117114108
	email = 101109097105108
	description = 100101115099114105112116105111110
	
	topicvalue =[givenName, familyName, jobTitle, worksFor, workLocation, url, email, description]
	topicname =['givenName', 'familyName', 'jobTitle', 'worksFor', 'workLocation', 'url', 'email', 'description']
	
	workspace_contract=ownersToContracts(address,mode)
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	profil=dict()
	index=0
	for i in topicvalue :
		try :
			claim=contract.functions.getClaimIdsByTopic(i).call()
		except :
			claim=[]
		if len(claim) != 0 : # uniquement si les information ont ete entrées a la creation de l identité
			claimId = claim[len(claim)-1].hex()
			data = contract.functions.getClaim(claimId).call()
			profil[topicname[index]]=data[4].decode('utf-8')
		#else :
		#	profil[topicname[index]]=None
		index = index+1
	return profil
	

############################################################
# Transfert de tokens  Talao depuis le portefeuille TalaoGen 
############################################################

def token_transfer(address_to, value, mode) :
	
	w3=mode.initProvider()

	contract=w3.eth.contract(mode.Talao_token_contract,abi=constante.Talao_Token_ABI)

	# calcul du nonce de l envoyeur de token . Ici le portefeuille TalaoGen
	nonce = w3.eth.getTransactionCount(mode.Talaogen_public_key)  

	# Build transaction
	valueTalao=value*10**18	
	w3.eth.defaultAccount=mode.Talaogen_public_key
	print ("token balance Talaogen = ", token_balance(mode.Talaogen_public_key,mode))
	# tx_hash = contract.functions.transfer(bob, 100).transact({'from': alice})
	hash1=contract.functions.transfer(address_to, valueTalao ).transact({'from' : mode.Talaogen_public_key,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce})	
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	
	return hash1.hex()
	

###############################################################
# Transfert d'ether depuis le portefuille TalaoGen
#
# attention value est en millieme d ether
###############################################################

def ether_transfer(address_to, value, mode) :
	
	w3=mode.initProvider()
	
	# calcul du nonce de l envoyeur de token . Ici le portefeuille TalaoGen	
	talaoGen_nonce = w3.eth.getTransactionCount(mode.Talaogen_public_key) 

	# build transaction
	eth_value=w3.toWei(str(value), 'milli')
	transaction = {'to': address_to,'value': eth_value,'gas': 50000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': talaoGen_nonce,'chainId': mode.CHAIN_ID}

	#sign transaction with TalaoGen wallet
	key = mode.Talaogen_private_key
	signed_txn = w3.eth.account.sign_transaction(transaction, key)

	# alert Admin
	address=mode.Talaogen_public_key
	balance =w3.eth.getBalance(address)/1000000000000000000
	if balance < 0.2 :
		Talao_message.messageAdmin('nameservice', 'balance Talaogen < 0.2eth', mode)
		
	#w3.eth.defaultAccount=mode.Talaogen_public_key

	#signed_txn = w3.eth.signTransaction(dict(nonce=talaoGen_nonce,gasPrice=w3.toWei(mode.GASPRICE, 'gwei'),gas=50000,to=address_to,value=eth_value,data=b'',))
	
	# send transaction
	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash, timeout=2000)	
	return hash



###############################################################
# Balance d'un compte en token Talao
#
###############################################################

def token_balance(address,mode) :
	w3=mode.w3
	contract=w3.eth.contract(mode.Talao_token_contract,abi=constante.Talao_Token_ABI)
	raw_balance = contract.functions.balanceOf(address).call()
	balance=raw_balance//10**18
	return balance

############################################################
# appel de createVaultAcces (uint price) 
############################################################

def createVaultAccess(address,private_key,mode) :
	w3=mode.initProvider()

	contract=w3.eth.contract(mode.Talao_token_contract,abi=constante.Talao_Token_ABI)

	# calcul du nonce de l envoyeur de token 
	nonce = w3.eth.getTransactionCount(address)  

	# Build transaction
	txn = contract.functions.createVaultAccess(0).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 150000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)		
	return hash


############################################################
# creation d'un workspace
############################################################

def createWorkspace(address,private_key,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail,mode) :
	w3=mode.initProvider()

	contract=w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)

	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(address)  

	# Build transaction
	txn=contract.functions.createWorkspace(1001,1,1,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)	
	return hash
 

###################################################################
#  authorize partnership, from user to partner
###################################################################
#     */
#    function authorizePartnership(address _hisContract, bytes _ourSymetricKey)
#        external
#        onlyIdentityPurpose(1)
#   {


def authorizepartnership(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, workspace_contract_partner,mode, synchronous = True) :
	
	# user = address_to
	w3=mode.initProvider()
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	
	# calcul du nonce de l envoyeur de token . Ici le from
	nonce = w3.eth.getTransactionCount(address_from)  

	#recuperer la cle AES cryptée du user
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	mydata = contract.functions.identityInformation().call()
	user_aes_encrypted=mydata[5]
		
	# read la cle privee RSA du user sur le fichier
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+address_to+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	try :
		fp = open(filename,"r")
	except :
		print (filename, " has not been found")
		return False
	user_rsa_key=fp.read()	
	fp.close()   

	# decoder la cle AES128 cryptée du user avec la cle RSA privée du user
	key = RSA.importKey(user_rsa_key)
	cipher = PKCS1_OAEP.new(key)	
	user_aes=cipher.decrypt(user_aes_encrypted)
	
	#recuperer la cle RSA publique du partner
	contract=w3.eth.contract(workspace_contract_partner,abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	partner_rsa_key=data[4]
	
	# encryption de la cle AES du user avec la cle RSA du partner
	key=RSA.importKey(partner_rsa_key)	
	cipher = PKCS1_OAEP.new(key)
	user_aes_encrypted_with_partner_key = cipher.encrypt(user_aes)
	
	# Build transaction
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	txn=contract.functions.authorizePartnership(workspace_contract_partner, user_aes_encrypted_with_partner_key).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	#sign transaction with caller wallet ici from
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	h= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(h, timeout=2000, poll_latency=1)	
	return h
	
	
	

# 		0 identityInformation.creator = msg.sender;
#       1 identityInformation.category = _category;
#       2 identityInformation.asymetricEncryptionAlgorithm = _asymetricEncryptionAlgorithm;
#       3 identityInformation.symetricEncryptionAlgorithm = _symetricEncryptionAlgorithm;
#       4 identityInformation.asymetricEncryptionPublicKey = _asymetricEncryptionPublicKey;
#       5 identityInformation.symetricEncryptionEncryptedKey = _symetricEncryptionEncryptedKey;
#       6 identityInformation.encryptedSecret = _encryptedSecret;

def partnershiprequest(address_from, workspace_contract_from, identity_address, identity_workspace_contract, private_key_from, partner_workspace_contract, identity_rsa_key, mode, synchronous= True) :

	w3 = mode.w3
	partner_address = contractsToOwners(partner_workspace_contract, mode)	
		
	# if partner has a claim 3 key, it has to be removed first. 
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	key = mode.w3.soliditySha3(['address'], [partner_address])
	has_key = contract.functions.keyHasPurpose(key, 3).call()
	print(' key ', has_key)
	if has_key :
		nonce = w3.eth.getTransactionCount(address_from)  
		txn = contract.functions.removeKey(key, 3).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
		signed_txn = w3.eth.account.signTransaction(txn, private_key_from)
		w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
		hash_transaction = w3.toHex(w3.keccak(signed_txn.rawTransaction))
		print('talao_token_transaction.py, hash transaction parnership request = ', hash_transaction)
		receipt = w3.eth.waitForTransactionReceipt(hash_transaction, timeout=2000, poll_latency=1)	
		if receipt['status'] == 0 :
			return False	
		print( 'claim key removed')
	
	#recuperer la cle AES cryptée de l identitté
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	identity_aes_encrypted = data[5]
	
	#recuperer la cle RSA publique du partner
	contract = w3.eth.contract(partner_workspace_contract, abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	partner_rsa_key = data[4]
	
	# decrypt AES key de l identité avec la RSA key
	key = RSA.importKey(identity_rsa_key)
	cipher = PKCS1_OAEP.new(key)	
	identity_aes = cipher.decrypt(identity_aes_encrypted)
	
	# encryption de la cle AES de lidentité avec la cle RSA du partner
	
	key = RSA.importKey(partner_rsa_key)	
	cipher = PKCS1_OAEP.new(key)
	identity_aes_encrypted_with_partner_key = cipher.encrypt(identity_aes)

	# build, sign and send transaction
	contract = w3.eth.contract(identity_workspace_contract,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)  
	txn = contract.functions.requestPartnership(partner_workspace_contract, identity_aes_encrypted_with_partner_key).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn = w3.eth.account.signTransaction(txn, private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash_transaction = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	print('talao_token_transaction.py, hash transaction parnership request = ', hash_transaction)
	if synchronous :
		receipt = w3.eth.waitForTransactionReceipt(hash_transaction, timeout=2000, poll_latency=1)	
		if receipt['status'] == 0 :
			return False	
	return True


# reject a partnership
def remove_partnership(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, partner_workspace_contract, mode, synchronous= True):
#     solidity	  function rejectPartnership(address _hisContract)

	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token
	nonce = w3.eth.getTransactionCount(address_from)

	# Build and send transaction
	txn = contract.functions.removePartnership(partner_workspace_contract).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash1 = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	print('hash = ', hash1)
	if synchronous :
		w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)		
	return True


"""
#################################################################
#  get Privatkey
#################################################################
def getPrivatekey(workspace_contract,mode) :

	w3 = mode.initProvider()
	fichiercsv = mode.BLOCKCHAIN+'_Talao_Identity.csv'
	csvfile = open(fichiercsv,newline='')
	reader = csv.DictReader(csvfile) 
	search = False
	for row in reader :
		if row['workspace_contract'] == workspace_contract :
			private_key=row.get('private_key')
			search = True
	csvfile.close()
	if search :
		return private_key
	else :
		return None
"""
"""
#################################################################
#  get Privatekey, aes and SECRET
#################################################################
def getAll(workspace_contract,mode) :

	w3 = mode.initProvider()
	fichiercsv = mode.BLOCKCHAIN+'_Talao_Identity.csv'
	csvfile = open(fichiercsv,newline='')
	reader = csv.DictReader(csvfile) 
	search = False
	for row in reader :
		if row['workspace_contract'] == workspace_contract :
			private_key=row.get('private_key')
			AES_key=row.get('aes')
			SECRET=row.get('password')
			search = True
	csvfile.close()
	if search :
		return private_key, SECRET, AES_key
	else :
		return None
"""
"""
##################################################################
#    get Email from identity 
# DEPRECATED email is encypted wuth RSA 
##################################################################
def getEmail(workspace_contract, mode) :

	w3=mode.initProvider()
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	try :
		a = contract.functions.getClaimIdsByTopic(101109097105108).call()
	except :
		return None	
	if len(a) != 0:
		# always the last one
		claim_Id = a[len(a)-1].hex()
		email = contract.functions.getClaim(claim_Id).call()[4].decode('utf-8')
		return email
	else :
		return None	
"""

##################################################################
#    get Picture from identity 
##################################################################
def getpicture(workspace_contract, mode) :

	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	try :
		a = contract.functions.getClaimIdsByTopic(105109097103101).call()
	except :
		return None	
	if len(a) != 0:
		claim_Id = a[len(a)-1].hex()
		picture_hash = contract.functions.getClaim(claim_Id).call()[5]
		return picture_hash
	else :
		return None	
		
##################################################################
# Delete document
##################################################################
def deleteDocument(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from,documentId, mode):
#     solidity	  function deleteDocument (uint _id) external onlyIdentityPurpose(20002)
	
	w3=mode.initProvider()
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token
	nonce = w3.eth.getTransactionCount(address_from)  

	# Build transaction
	txn = contract.functions.deleteDocument(int(documentId)).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
		
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)		
	return hash


##################################################################
# Delete claim
##################################################################
def deleteClaim(address_from, workspace_contract_from, address_to, workspace_contract_to,private_key_from,claimId, mode):
#     solidity	  removeClaim(Id)
	
	w3=mode.initProvider()
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token, ici my_address
	nonce = w3.eth.getTransactionCount(address_from)

	# Build transaction
	txn = contract.functions.removeClaim(claimId).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
		
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)		
	return hash

###################################################################
# Création de document 250000 000 gas
# @data = dictionnaire = {"user": { "ethereum_account": '123' , "ethereum_contract": '234' ,"first_name" : 'Jean' ,"last_name" : 'Pierre' }}
# @encrypted = False ici
# location engine = 1 pour IPFS, doctypeversion = 1, expire =Null, 
###################################################################

# DEPRECATED !!!!!!!

def createDocument(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, doctype, data, encrypted,mode, synchronous = True) :

	w3=mode.initProvider()
	
	encrypted = False

	#envoyer la transaction sur le contrat
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)

	# calcul du nonce de l envoyeur de token . Ici le portefeuille TalaoGen
	nonce = w3.eth.getTransactionCount(address_from)  

	# stocke sur ipfs (un dictionnaire)
	hash=Talao_ipfs.IPFS_add(data)
	print('ipfshash = ', hash)
	
	# calcul du checksum en bytes des data, conversion du dictionnaire data en chaine str
	_data= json.dumps(data)
	checksum=hashlib.md5(bytes(_data, 'utf-8')).hexdigest()
	# la conversion inverse de bytes(data, 'utf-8') est XXX.decode('utf-8')

	# Build transaction
	txn = contract.functions.createDocument(doctype,1,0,checksum,1, bytes(hash, 'utf-8'), encrypted).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(hash)		
	return hash



###################################################################
# issue certifica 250000 000 gas
# @data = dictionnaire = {"user": { "ethereum_account": '123' , "ethereum_contract": '234' ,"first_name" : 'Jean' ,"last_name" : 'Pierre' }}
# @encrypted = False ou True => AES
# location engine = 1 pour IPFS, doctypeversion = 1, expire =Null, 
###################################################################
#   
#      function issueCertificate(
#        uint16 _docType,
#        uint16 _docTypeVersion,
#        bytes32 _fileChecksum,
#        uint16 _fileLocationEngine,
#        bytes _fileLocationHash,
#        bool _encrypted,
#        uint16 _related

def createCertificate(address_to, address_from, private_key_from, doctype, data, encrypted, related,mode, synchronous = True) :
	w3=mode.initProvider()
	
	
	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract_to=ownersToContracts(address_to,mode)

	#envoyer la transaction sur le contrat
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)

	# calcul du nonce de l envoyeur de token
	nonce = w3.eth.getTransactionCount(address_from)  

	# stocke sur ipfs (un dictionnaire)
	ipfshash=Talao_ipfs.IPFS_add(data)
	
	# calcul du checksum en bytes des data, conversion du dictionnaire data en chaine str
	_data= json.dumps(data)
	checksum=hashlib.md5(bytes(_data, 'utf-8')).hexdigest()
	# la conversion inverse de bytes(data, 'utf-8') est XXX.decode('utf-8')

	# Build transaction
	txn = contract.functions.issueCertificate(doctype,1,checksum,1, bytes(ipfshash, 'utf-8'), encrypted, related).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(hash1)		
	return hash1
 
############################################################
#  Mise a jour de la photo
############################################################
#
#  @picturefile : type str, nom fichier de la phooto avec path ex  './cvpdh.json'
# claim topic 105109097103101
    

def savepictureProfile(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, picturefile,mode, synchronous = True) :
	w3=mode.initProvider()

	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	response=client.add(picturefile)
	picturehash=response['Hash']	
	image= 105109097103101 
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)

	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(address_from)  

	# Build transaction
	txn=contract.functions.addClaim(image,1,address_from, '0x', '0x01',picturehash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	return picturehash



 
############################################################
#  Mise a jour du profil 2 000 000 gas
############################################################
#
# function updateSelfClaims(
#        uint256[] _topic,
#        bytes _data,
#        uint256[] _offsets

def saveworkspaceProfile(address, private_key, _givenName, _familyName, _jobTitle, _worksFor, _workLocation, _url, _email, _description,mode) :
	w3=mode.initProvider()

	givenName = 103105118101110078097109101
	familyName = 102097109105108121078097109101
	jobTitle = 106111098084105116108101
	worksFor = 119111114107115070111114
	workLocation = 119111114107076111099097116105111110
	url = 117114108
	email = 101109097105108
	description = 100101115099114105112116105111110
	topic =[givenName, familyName, jobTitle, worksFor, workLocation, url, email, description]
	image= 105109097103101
 
	chaine=_givenName+_familyName+_jobTitle+_worksFor+_workLocation+_url+_email+_description
	bchaine=bytes(chaine, 'utf-8')

	offset=[len(_givenName), len(_familyName), len(_jobTitle), len(_worksFor), len(_workLocation), len(_url), len(_email), len(_description)]

	workspace_contract=ownersToContracts(address,mode)
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)

	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(address)  

	# Build transaction
	txn=contract.functions.updateSelfClaims(topic, bchaine,offset).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	return hash1

############################################################
# 	@chaine=_givenName+_familyName+_jobTitle+_worksFor+_workLocation+_url+_email+_description
#	@topic =[givenName, familyName, jobTitle, worksFor, workLocation, url, email, description]
# 	@offset [len(_givenName), len(_familyName), len(_jobTitle), len(_worksFor), len(_workLocation), len(_url), len(_email), len(_description)]
"""
	givenName = 103105118101110078097109101
	familyName = 102097109105108121078097109101
	jobTitle = 106111098084105116108101
	worksFor = 119111114107115070111114
	workLocation = 119111114107076111099097116105111110
	url = 117114108
	email = 101109097105108
	description = 100101115099114105112116105111110
	image= 105109097103101
	"""
def updateSelfclaims(address, private_key, topic,chaine, offset, mode, synchronous=True) :
	
	w3=mode.w3
	bchaine=bytes(chaine, 'utf-8')
	workspace_contract=ownersToContracts(address,mode)
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(address)  
	# Build transaction
	txn=contract.functions.updateSelfClaims(topic, bchaine,offset).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	return hash1


 
############################################################
#  Read workspace Info
############################################################
#	0 identityInformation.creator = msg.sender;
#       1 identityInformation.category = _category;
#       2 identityInformation.asymetricEncryptionAlgorithm = _asymetricEncryptionAlgorithm;
#       3 identityInformation.symetricEncryptionAlgorithm = _symetricEncryptionAlgorithm;
#       4 identityInformation.asymetricEncryptionPublicKey = _asymetricEncryptionPublicKey;
#       5 identityInformation.symetricEncryptionEncryptedKey = _symetricEncryptionEncryptedKey;
#       6 identityInformation.encryptedSecret = _encryptedSecret;

def read_workspace_info (address, rsa_key, mode) : 
	w3 = mode.w3
		
	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract=ownersToContracts(address,mode)

	# recuperation du email 
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	claim = contract.functions.getClaimIdsByTopic(101109097105108).call()
	claim_id = claim[-1].hex()
	data = contract.functions.getClaim(claim_id).call()
	scheme = data[1]
	if scheme == 1 : # freedap creation
		email = data[4].decode('utf-8')
	elif scheme == 2 :
		# decoder l 'email cryptée avec la cle RSA privée
		key = RSA.importKey(rsa_key)
		cipher = PKCS1_OAEP.new(key)	
		bemail = cipher.decrypt(secret_encrypted)			
		email = bemail.hex()
	else :
		print('erreur email ', scheme)


	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	
	category = data[1]
	
	#recuperer le secret crypté
	secret_encrypted=data[6]	
	# decoder le secret cryptée avec la cle RSA privée
	key = RSA.importKey(rsa_key)
	cipher = PKCS1_OAEP.new(key)	
	secret = cipher.decrypt(secret_encrypted).hex()			
	
	
	#recuperer la clé AES cryptée 
	aes_encrypted=data[5]
	# decoder le secret cryptée avec la cle RSA privée
	key = RSA.importKey(rsa_key)
	cipher = PKCS1_OAEP.new(key)	
	aes = cipher.decrypt(aes_encrypted)				
	
	return workspace_contract, category, email , secret, aes 

 
############################################################
#  Create and publish experience in one step
############################################################
# experience={ 'experience':{'title': _experienceTitle, 'description': _experienceDescription, 'from': _fromdate, 'to': _todate, 'location': '', 'remote': True, 'organization_name': 'Talao','skills': [] }}
	

def createandpublishExperience(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, exprience, mode, synchronous = True) :
	w3 = mode.w3

	# recuperer les infos du compte sur le workspace
	(workspace_contract_to,_email, _password, aes)=readWorkspaceInfo(address_to,mode)
	
	# recuperer les info du profil
	profile = readProfil(address_to,mode)
	#	topicname =['givenName', 'familyName', 'jobTitle', 'worksFor', 'workLocation', 'url', 'email', 'description']
	_familyName = profile["familyName"]
	_givenName = profile["givenName"]
	_jobTitle = profile["jobTitle"]

	#recuperer le token sur le backend
	conn = http.client.HTTPConnection(mode.ISSUER)
	if constante.BLOCKCHAIN == 'ethereum' :
		conn = http.client.HTTPSConnection(constante.ISSUER)
	headers = {'Accept': 'application/json','Content-type': 'application/json'}
	payload = {"email" : _email ,"password" : _password}
	data = json.dumps(payload)
	conn.request('POST', '/login',data, headers)
	response = conn.getresponse()
	res = response.read()
	token = json.loads(res)["token"]

	# creation experience sur le backend
	headers = {'Accept': 'application/json','Content-type': 'application/json',  'Authorization':'Bearer '+token}
	payload = experience
	data = json.dumps(payload)
	conn.request('POST', '/experiences',data, headers)
	response = conn.getresponse()
	res = response.read()
	experience_id = json.loads(res)['experience']['id']	
	conn.close()

	# publish experience sur ipfs et la blockchain
	data = {"documentType":50000,
			"version":2,
			"recipient": {"givenName":_givenName,
						"familyName":_familyName,
						"title": _jobTitle,
						"email":_email[5:],
						"ethereum_account": address_to,
						"ethereum_contract": workspace_contract_to},
			"issuer":{"organization":{"email":"",
									"url":"",
									"image":"",
									"ethereum_account":"",
									"ethereum_contract":""},
									"responsible":{"name":"",
													"title":"",
													"image":""},
			"partner":{"name":"",
						"text":""}},
			"certificate":{"title":_experienceTitle,
							"description":_experienceDescription,
							"from":_fromdate,
							"to":_todate,
							"skills":[],
							"ratings":[]}}

	createDocument(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, 50000, data, False, mode, synchronous = True)

	# recuperer l iD du document sur le dernier event DocumentAdded
	mycontract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	myfilter = mycontract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
	eventlist = myfilter.get_all_entries()
	document_id = eventlist[-1]['args']['id']

	# update de l experience sur la backend . on change le status et on donne le numero du doc 
	token = Talao_backend_transaction.login(_email, _password)
	headers = {'Accept': 'application/json','Content-type': 'application/json',  'Authorization':'Bearer '+token}
	payload = {"experience":{"blockchain_experience_id":document_id,"blockchain_status":1},"action":"SET_DRAFT"}
	data = json.dumps(payload)
	conn.request('PUT', '/experiences/' + str(experience_id),data, headers)
	response = conn.getresponse()
	res = response.read()
	print(json.loads(res))	
	conn.close()
	return


#########################################################	
# read Talao experience or diploma index
#########################################################
# @_doctype = int (40000 = Diploma, 50000 = experience)
# return Int
# attention cela retourne le nombre de doc mais pas les docuements actifs !!!!

def getDocumentIndex(address, _doctype,mode) :
	w3=mode.initProvider()

	workspace_contract=ownersToContracts(address,mode)
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	docindex=contract.functions.getDocuments().call()
	index=0
	for i in docindex :
		doc=contract.functions.getDocument(i).call()
		if doc[0]==_doctype :
			index=index+1			
	return index

"""
######################################################	
# read Talao experience or diploma
######################################################
# @_doctype = integer, 40000 = Diploma, 50000 = experience, 60000 certificate
# return dictionnaire

def getDocument(address, _doctype,_index,mode) :
	w3=mode.initProvider()

	workspace_contract=ownersToContracts(address,mode)
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	docindex=contract.functions.getDocuments().call() # la liste de tous les doc_id actifs
	index=0
	for i in docindex :
		doc=contract.functions.getDocument(i).call()
		if doc[0] ==_doctype :
			if index==_index :
				ipfs_hash=doc[6].decode('utf-8')
				return Talao_ipfs.IPFS_get(ipfs_hash)
			else :
				index=index+1				
"""

"""
#####################################
#authentication d'un json de type str
#####################################
def authenticate(docjson, address, private_key,mode) :
# @docjson : type str au format json
# @address, @private_key  : le Creator est celui qui signe
# return le str json authentifié
# pour decoder :
# message = encode_defunct(text=msg)
# address=w3.eth.account.recover_message(message, signature=signature)
#
# cf : https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message

	w3=mode.initProvider()

	# conversion en Dict python
	objectdata=json.loads(docjson)

	# mise a jour du Dict avec les infos d authentication
	objectdata.update({'Authentication' : 
	{'@context' : 'this Key can be used to authenticate the creator of this doc. Ownernership of did can be checked at https://rinkeby.etherscan.io/address/0xde4cf27d1cefc4a6fa000a5399c59c59da1bf253#readContract',
	'type' : 'w3.eth.account.sign_message',
	'PublicKey' : address,
	'Created' : str(datetime.today()),
	"Creator" : address,
	'message' : 'to be added',
	'signature' : 'to be added' }
	}) 
	
	# upload et pin sur ipfs
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	response=client.add_json(objectdata)
	client.pin.add(response)

	# le lien sur le fichier IPFS est le message	
	msg='https://ipfs.io/ipfs/'+response
	message = encode_defunct(text=msg)
	# signature du messaga avec web3 compatible avce solidity erocover 
	signed_message = w3.eth.account.sign_message(message, private_key=private_key)
	signature=signed_message.signature.hex()
	
	# complement du Dict
	objectdata["Authentication"]["message"]=msg
	objectdata["Authentication"]["signature"]=signature
	
	# conversion du Dict en str json
	auth_docjson=json.dumps(objectdata,indent=4)
		
	return auth_docjson
"""

#################################################
#  add claim
#################################################
# @data : str
# @topicname : type str , 'contact'
# @ipfshash = str exemple  b'qlkjglgh'.decode('utf-8') 
# signature cf https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message

def addclaim(address_from,workspace_contract_from, address_to, workspace_contract_to,private_key_from, topicname, issuer, data, ipfshash, mode, synchronous = True) :
	
	w3=mode.w3
	
	# on va chercher topicvalue dans le dict existant (constante.py) si il n existe pas on le calcule
	topicvalue=constante.topic.get(topicname)
	if topicvalue== None :
		topicvaluestr =''
		for i in range(0, len(topicname))  :
			a = str(ord(topicname[i]))
			if int(a) < 100 :
				a='0'+a
			topicvaluestr=topicvaluestr+a
		topicvalue=int(topicvaluestr)
	
	nonce = w3.eth.getTransactionCount(address_from)  
	
	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=private_key_from)
	signature=signed_message['signature']
	
	# Build transaction
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	txn=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
	print('hash de addclaim =', hash1)	
	return hash1

#################################################
#  add self claim
#################################################
# @data : bytes	
# @topicname : type str , 'contact'
# @ipfshash = str exemple  b'qlkjglgh'.decode('utf-8') 
# signature cf https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message

def addselfclaim(workspace_contract, private_key, topicname, issuer, data, ipfshash,mode, synchronous=True) :
	
	w3=mode.initProvider()

	topicvalue=constante.topic[topicname]
	
	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(issuer)  
	
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])

	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
	message = encode_defunct(text=msg)
	signed_message = w3.eth.account.sign_message(message, private_key=private_key)
	signature=signed_message['signature']
	
	# Build transaction
	txn=contract.functions.addClaim(topicvalue,1,issuer, signature, data,ipfshash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	return hash1



##############################################
# detrmination de la nature de l addresse
##############################################
# @thisaddress, address
# return dictionnaire

def whatisthisaddress(thisaddress,mode) :

	w3=mode.initProvider()

	# est ce une addresse Ethereum ?
	if w3.isAddress(thisaddress) == False :
		category = False
		owner = None
		workspace= None	
	else :
		
		# test sur la nature de thisaddress
		contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
		address = contract.functions.contractsToOwners(thisaddress).call()
		workspace=contract.functions.ownersToContracts(thisaddress).call()
		
		# thisaddress est un owner
		if address == '0x0000000000000000000000000000000000000000' and workspace != '0x0000000000000000000000000000000000000000' :
			category = "owner"
			owner = thisaddress
			workspace=workspace
			
		# thisaddress est un workspace
		if address != '0x0000000000000000000000000000000000000000' and workspace == '0x0000000000000000000000000000000000000000' :
			category = 'workspace'
			owner=address
			workspace=thisaddress
		
		# thisaddressn est une addresse ethereum standard
		if address == '0x0000000000000000000000000000000000000000' and workspace == '0x0000000000000000000000000000000000000000' :
			category = 'unknown'
			owner = None
			workspace = None
			
	return {"type" : category, "owner" : owner, 'workspace' : workspace}
	

##############################################
# detrmination de la validité d'un did
##############################################
# did
# return bool	

def isdid(did,mode) :
	didsplit=did.split(':')
	if len(didsplit) != 4 :
		return False
	if didsplit[0] != 'did' or didsplit[1] != 'talao' or didsplit[2] != mode.BLOCKCHAIN :
		return False 
	if whatisthisaddress('0x'+didsplit[3], mode)["type"] != "workspace" :
		return False
	return True	

