from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import csv
import sys
import time
import hashlib
import json
from datetime import datetime
from eth_account.messages import encode_defunct
import random

# dependances
import Talao_ipfs
import Talao_message
import constante
import ns

def ownersToContracts(address, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	workspace_address = contract.functions.ownersToContracts(address).call()
	if workspace_address == '0x0000000000000000000000000000000000000000' :
		return None
	return workspace_address

def destroy_workspace(workspace_contract, private_key, mode) :
	# remove workspace data from blockchain
	address = contractsToOwners(workspace_contract, mode)
	contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)

	# Build, sign transaction
	nonce = mode.w3.eth.getTransactionCount(address)
	txn = contract.functions.destroyWorkspace().buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)

	# send transaction
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1 = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
	if receipt['status'] == 0 :
		return None
	return hash1

def contractsToOwners(workspace_contract, mode) :
	w3 = mode.w3
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	if address == '0x0000000000000000000000000000000000000000' :
		return None
	return address

def get_data_from_token(mode) :
	w3 = mode.w3
	contract=w3.eth.contract(mode.Talao_token_contract,abi=constante.Talao_Token_ABI)
	total_deposit = contract.functions.totalDeposit().call()
	vault_deposit = contract.functions.vaultDeposit().call()
	return total_deposit, vault_deposit

def token_transfer(address_to, value, mode) :
	""" Transfert de tokens  Talao depuis le portefeuille TalaoGen """
	w3 = mode.w3
	contract=w3.eth.contract(mode.Talao_token_contract,abi=constante.Talao_Token_ABI)
	# calcul du nonce de l envoyeur de token . Ici le portefeuille TalaoGen
	nonce = w3.eth.getTransactionCount(mode.Talaogen_public_key)
	# Build transaction
	valueTalao=value*10**18
	w3.eth.defaultAccount=mode.Talaogen_public_key
	print ("token balance Talaogen = ", token_balance(mode.Talaogen_public_key,mode))
	# tx_hash = contract.functions.transfer(bob, 100).transact({'from': alice})
	transaction_hash=contract.functions.transfer(address_to, valueTalao ).transact({'from' : mode.Talaogen_public_key,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce})	
	receipt = w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if receipt['status'] == 0 :
		return None
	return transaction_hash.hex()

def ether_transfer(address_to, value, mode) :
	w3 = mode.w3
	# calcul du nonce de l envoyeur de token . Ici le portefeuille TalaoGen
	talaoGen_nonce = w3.eth.getTransactionCount(mode.Talaogen_public_key)
	# build transaction
	eth_value=w3.toWei(str(value), 'milli')
	transaction = {'to': address_to,'value': eth_value,'gas': 50000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': talaoGen_nonce,'chainId': mode.CHAIN_ID}
	#sign transaction with TalaoGen wallet
	key = mode.Talaogen_private_key
	signed_txn = w3.eth.account.sign_transaction(transaction, key)
	# alert Admin
	address = mode.Talaogen_public_key
	balance = w3.eth.getBalance(address)/1000000000000000000
	if balance < 0.2 :
		Talao_message.messageAdmin('nameservice', 'balance Talaogen < 0.2eth', mode)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000)
	if receipt['status'] == 0 :
		return None
	return hash

def token_balance(address,mode) :
	w3 = mode.w3
	contract=w3.eth.contract(mode.Talao_token_contract,abi=constante.Talao_Token_ABI)
	raw_balance = contract.functions.balanceOf(address).call()
	balance=raw_balance//10**18
	return balance

def createVaultAccess(address,private_key,mode) :
	w3 = mode.w3
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
	receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)
	if receipt['status'] == 0 :
		return None
	return hash

def createWorkspace(address,private_key,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail,mode) :
	w3 = mode.w3
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
	receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)
	if receipt['status'] == 0 :
		return None
	return hash

def authorize_partnership(address_from, workspace_contract_from, identity_address, identity_workspace_contract, private_key_from, partner_workspace_contract, user_rsa_key, mode, synchronous = True) :	
	# user = address_to
	w3 = mode.w3
	partner_address = contractsToOwners(partner_workspace_contract, mode)

	#get Key purpose
	key = mode.w3.soliditySha3(['address'], [partner_address])
	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	address_purpose_list = contract.functions.getKeyPurposes(key).call()
	print('purpose de address ', address_purpose_list)
	key = mode.w3.soliditySha3(['address'], [partner_workspace_contract])
	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	workspace_contract_purpose_list = contract.functions.getKeyPurposes(key).call()
	print('purpose de woorkspace contract ', workspace_contract_purpose_list)


	# Check if partner has key in Identity, it has to be removed first.
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	key = mode.w3.soliditySha3(['address'], [partner_address])
	for purpose in address_purpose_list :
		nonce = w3.eth.getTransactionCount(address_from)
		gas_price = w3.toWei(mode.GASPRICE, 'gwei')
		txn = contract.functions.removeKey(key, purpose).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 2000000,'gasPrice': gas_price,'nonce': nonce,})
		signed_txn = w3.eth.account.signTransaction(txn, private_key_from)
		w3.eth.sendRawTransaction(signed_txn.rawTransaction)
		hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
		receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)
		if receipt['status'] == 0 :
			print('Echec remove key of address, purpose = ', purpose, 'hash = ', hash)
			return False
		else :
			print('Success remove key of address, purpose = ', purpose, 'hash = ', hash)

	# if partner workspace contract has a key in Identity, it has to be removed first.
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	key = mode.w3.soliditySha3(['address'], [partner_workspace_contract])
	for purpose in workspace_contract_purpose_list :
		nonce = w3.eth.getTransactionCount(address_from)
		txn = contract.functions.removeKey(key, purpose).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
		signed_txn = w3.eth.account.signTransaction(txn, private_key_from)
		w3.eth.sendRawTransaction(signed_txn.rawTransaction)
		hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
		receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)
		if receipt['status'] == 0 :
			print(' echec remove key of workspace _contract, purpose =', purpose, 'hash = ',hash)
			return False
		else :
			print(' success remove key of workspace _contract, purpose =', purpose, 'hash = ',hash)

	# calcul du nonce de l envoyeur de token . Ici le from
	nonce = w3.eth.getTransactionCount(address_from)
	#recuperer la cle AES cryptée du user
	contract=w3.eth.contract(identity_workspace_contract,abi=constante.workspace_ABI)
	mydata = contract.functions.identityInformation().call()
	user_aes_encrypted=mydata[5]
	# decoder la cle AES cryptée du user avec la cle RSA privée du user
	key = RSA.importKey(user_rsa_key)
	cipher = PKCS1_OAEP.new(key)
	user_aes=cipher.decrypt(user_aes_encrypted)
	print('user aes =', user_aes)
	#recuperer la cle RSA publique du partner
	contract=w3.eth.contract(partner_workspace_contract,abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	partner_rsa_key=data[4]
	# encryption de la cle AES du user avec la cle RSA du partner
	key=RSA.importKey(partner_rsa_key)
	cipher = PKCS1_OAEP.new(key)
	user_aes_encrypted_with_partner_key = cipher.encrypt(user_aes)

	# Build transaction
	contract=w3.eth.contract(identity_workspace_contract,abi=constante.workspace_ABI)
	txn=contract.functions.authorizePartnership(partner_workspace_contract, user_aes_encrypted_with_partner_key).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	#sign transaction with caller wallet ici from
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)

	# send transaction
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	h = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		receipt = w3.eth.waitForTransactionReceipt(h, timeout=2000, poll_latency=1)
		if receipt['status'] == 0 :
			print('echec transaction de authorize partnership')
			return False
	return True


# 		0 identityInformation.creator = msg.sender;
#       1 identityInformation.category = _category;
#       2 identityInformation.asymetricEncryptionAlgorithm = _asymetricEncryptionAlgorithm;
#       3 identityInformation.symetricEncryptionAlgorithm = _symetricEncryptionAlgorithm;
#       4 identityInformation.asymetricEncryptionPublicKey = _asymetricEncryptionPublicKey;
#       5 identityInformation.symetricEncryptionEncryptedKey = _symetricEncryptionEncryptedKey;
#       6 identityInformation.encryptedSecret = _encryptedSecret;

def partnershiprequest(address_from, workspace_contract_from, identity_address, identity_workspace_contract, private_key_from, partner_workspace_contract, identity_rsa_key, mode, synchronous= True) :
	# identity is the partner requested
	w3 = mode.w3
	partner_address = contractsToOwners(partner_workspace_contract, mode)

	#get Key purpose
	key = mode.w3.soliditySha3(['address'], [partner_address])
	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	address_purpose_list = contract.functions.getKeyPurposes(key).call()
	print('purpose de address ', address_purpose_list)
	key = mode.w3.soliditySha3(['address'], [partner_workspace_contract])
	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	workspace_contract_purpose_list = contract.functions.getKeyPurposes(key).call()
	print('purpose de woorkspace contract ', workspace_contract_purpose_list)


	# Check if partner has key in Identity, it has to be removed first.
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	key = mode.w3.soliditySha3(['address'], [partner_address])
	for purpose in address_purpose_list :
		nonce = w3.eth.getTransactionCount(address_from)
		txn = contract.functions.removeKey(key, purpose).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 2000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
		signed_txn = w3.eth.account.signTransaction(txn, private_key_from)
		w3.eth.sendRawTransaction(signed_txn.rawTransaction)
		hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
		receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)
		if receipt['status'] == 0 :
			print('Echec remove key of address, purpose = ', purpose, 'hash = ', hash)
			return False
		else :
			print('Success remove key of address, purpose = ', purpose, 'hash = ', hash)

	# if partner workspace contract has a key in Identity, it has to be removed first.
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	key = mode.w3.soliditySha3(['address'], [partner_workspace_contract])
	for purpose in workspace_contract_purpose_list :
		nonce = w3.eth.getTransactionCount(address_from)
		txn = contract.functions.removeKey(key, purpose).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
		signed_txn = w3.eth.account.signTransaction(txn, private_key_from)
		w3.eth.sendRawTransaction(signed_txn.rawTransaction)
		hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
		receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)
		if receipt['status'] == 0 :
			print(' echec remove key of workspace _contract, purpose =', purpose, 'hash = ',hash)
			return False
		else :
			print(' success remove key of workspace _contract, purpose =', purpose, 'hash = ',hash)

	#recuperer la cle AES cryptée de l identité
	contract = w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	identity_aes_encrypted = data[5]

	#recuperer la cle RSA publique du partner
	contract = w3.eth.contract(partner_workspace_contract, abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	partner_rsa_key = data[4]

	# decrypt AES key de l identité avec la RSA key de l'identite
	key = RSA.importKey(identity_rsa_key)
	cipher = PKCS1_OAEP.new(key)
	identity_aes = cipher.decrypt(identity_aes_encrypted)

	# encryption de la cle AES de lidentité avec la cle RSA publique du partner
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
			print('echec transaction de request partnership')
			return False
	return True


# remove a partnership
def remove_partnership(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, partner_workspace_contract, mode, synchronous= True):
	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token
	nonce = w3.eth.getTransactionCount(address_from)

	# Build and send transaction
	txn = contract.functions.removePartnership(partner_workspace_contract).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1 = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	print('hash de remove partnership = ', hash1)
	if synchronous :
		receipt = w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
		if receipt['status'] == 0 :
			print('echec transaction de remove partnership')
			return False
	return True


# reject a partnership
def reject_partnership(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, partner_workspace_contract, mode, synchronous= True):

	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token
	nonce = w3.eth.getTransactionCount(address_from)

	# Build and send transaction
	txn = contract.functions.rejectPartnership(partner_workspace_contract).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1 = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	print('hash de reject parnership = ', hash1)
	if synchronous :
		receipt = w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
		if receipt['status'] == 0 :
			print('echec transaction de request partnership')
			return False
	return True

##################################################################
#    get image from identity
##################################################################
def get_image(workspace_contract, image_type, mode) :
# image(profil picture) = 105109097103101  signature = 115105103110097116117114101

	w3 = mode.w3
	topicvalue = 105109097103101 if image_type in ['photo', 'logo', 'image', 'picture'] else 115105103110097116117114101
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	try :
		a = contract.functions.getClaimIdsByTopic(topicvalue).call()
	except Exception as res :
		print('get picture in talao_transaction ', res)
		return None
	if len(a) != 0:
		claim_Id = a[-1].hex()
		picture_hash = contract.functions.getClaim(claim_Id).call()[5]
		return picture_hash
	else :
		return None


############################################################
#  Update pictures or signature, etc
############################################################
#  @picturefile : type str, nom fichier de la photo avec path ex  './cvpdh.json'
# claim topic 105109097103101
def save_image(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, picturefile, picture_type, mode, synchronous = True) :

	# upload picture on ipfs
	picture_hash = Talao_ipfs.file_add(picturefile, mode)

	topic = 105109097103101 if picture_type == 'picture' else 115105103110097116117114101
	contract = mode.w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)

	# Build and sign transaction
	nonce = mode.w3.eth.getTransactionCount(address_from)
	txn = contract.functions.addClaim(topic,1,address_from, '0x', '0x01',picture_hash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key_from)

	# send transaction
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1 = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		receipt = mode.w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
		if receipt['status'] == 0 :
			return None
	return picture_hash

############################################################
#  Mise a jour du profil 2 000 000 gas
############################################################
#
# function updateSelfClaims(
#        uint256[] _topic,
#        bytes _data,
#        uint256[] _offsets

def saveworkspaceProfile(address, private_key, _givenName, _familyName, _jobTitle, _worksFor, _workLocation, _url, _email, _description,mode) :
	w3 = mode.w3

	givenName = 103105118101110078097109101
	familyName = 102097109105108121078097109101
	jobTitle = 106111098084105116108101
	worksFor = 119111114107115070111114
	workLocation = 119111114107076111099097116105111110
	url = 117114108
	email = 101109097105108
	description = 100101115099114105112116105111110
	topic =[givenName, familyName, jobTitle, worksFor, workLocation, url, email, description]
	#image= 105109097103101

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
	receipt = w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
	if receipt['status'] == 0 :
		return None
	return hash1

############################################################
# 	@chaine=_givenName+_familyName+_jobTitle+_worksFor+_workLocation+_url+_email+_description
#	@topic =[givenName, familyName, jobTitle, worksFor, workLocation, url, email, description]
# 	@offset [len(_givenName), len(_familyName), len(_jobTitle), len(_worksFor), len(_workLocation), len(_url), len(_email), len(_description)]

def updateSelfclaims(address, private_key, topic,chaine, offset, mode, synchronous=True) :

	w3 = mode.w3
	bchaine = bytes(chaine, 'utf-8')
	workspace_contract = ownersToContracts(address,mode)
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
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
		receipt = w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
		if receipt['status'] == 0 :
			return None
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
	#return aes and secret as bytes
	w3 = mode.w3

	workspace_contract=ownersToContracts(address,mode)
	key = RSA.importKey(rsa_key)
	cipher = PKCS1_OAEP.new(key)

	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	category = data[1]

	#recuperer et decoder le secret crypté
	secret_encrypted=data[6]
	secret = cipher.decrypt(secret_encrypted)

	#recuperer et decoder la clé AES cryptée
	aes_encrypted=data[5]
	aes = cipher.decrypt(aes_encrypted)

	return category, secret, aes


#########################################################
# read Talao experience or diploma index
#########################################################
# @_doctype = int (40000 = Diploma, 50000 = experience)
# return Int
# attention cela retourne le nombre de doc mais pas les docuements actifs !!!!

def getDocumentIndex(address, _doctype,mode) :
	w3 = mode.w3

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
#################################################
#  add self claim
#################################################
# @data : bytes
# @topicname : type str , 'contact'
# @ipfshash = str exemple  b'qlkjglgh'.decode('utf-8')
# signature cf https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message

def addselfclaim(workspace_contract, private_key, topicname, issuer, data, ipfshash,mode, synchronous=True) :

	w3 = mode.w3

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

"""
