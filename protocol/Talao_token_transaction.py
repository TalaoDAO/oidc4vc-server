from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
#import time
import hashlib
import json
from datetime import datetime
from eth_account.messages import encode_defunct
from eth_account import Account
import logging
logging.basicConfig(level=logging.INFO)

# dependances
from components import Talao_ipfs, Talao_message, ns, privatekey
import constante

def read_profil (workspace_contract, mode, loading) :
	""" Read profil data as ERC725 claims witgout any decryption..."""

	# setup constante person
	person_topicnames = {'firstname' : 102105114115116110097109101,
						'lastname' : 108097115116110097109101,
						'contact_email' : 99111110116097099116095101109097105108,
						'contact_phone' : 99111110116097099116095112104111110101,
						'postal_address' : 112111115116097108095097100100114101115115,
						'birthdate' : 98105114116104100097116101,
						'about' : 97098111117116,
						'gender' : 103101110100101114,
						'education' : 101100117099097116105111110,
						'profil_title' : 112114111102105108095116105116108101,
						}

	# setup constant company
	company_topicnames = {'name' : 110097109101,
						'contact_name' : 99111110116097099116095110097109101,
						'contact_email' : 99111110116097099116095101109097105108,
						'contact_phone' : 99111110116097099116095112104111110101,
						'website' : 119101098115105116101,
						'about' : 97098111117116,
						'staff' : 115116097102102,
						'sales' : 115097108101115,
						'mother_company' : 109111116104101114095099111109112097110121,
						'siret' : 115105114101116,
						'siren' : 115105114101110,
						'postal_address' : 112111115116097108095097100100114101115115, }

	if loading != 'full' :
		person_topicnames = {'firstname' : 102105114115116110097109101,
							'lastname' : 108097115116110097109101,
							'profil_title' : 112114111102105108095116105116108101,
							}

		# setup constant company
		company_topicnames = {'name' : 110097109101,
							'siren' : 115105114101110,
							'postal_address' : 112111115116097108095097100100114101115115,}

	profil = dict()
	# test if identity exist and get category
	contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	try :
		category = contract.functions.identityInformation().call()[1]
	except :
		return None, None
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

def get_keylist(key, workspace_contract, mode) :
	contract = mode.w3.eth.contract(workspace_contract,abi = constante.workspace_ABI)
	return [ key.hex() for key in  contract.functions.getKeysByPurpose(key).call()]


def get_category (workspace_contract, mode) :
	contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	try :
		category = contract.functions.identityInformation().call()[1]
	except :
		logging.error('identity does not exist')
		return None
	return category

def contractsToOwners(workspace_contract, mode) :
	if not workspace_contract :
		return None
	if workspace_contract == '0x0000000000000000000000000000000000000000' :
		logging.warning('contracts to owners return 0x')
		return workspace_contract
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	if address == '0x0000000000000000000000000000000000000000' :
		return None
	return address

def ownersToContracts(address, mode) :
	if not address :
		logging.warning('owners to contracts : its not an address')
		return None
	if address == '0x0000000000000000000000000000000000000000' :
		logging.warning('owners to contract : return 0x')
		return None
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	workspace_address = contract.functions.ownersToContracts(address).call()
	if workspace_address == '0x0000000000000000000000000000000000000000' :
		logging.warning('owners to contract : return 0x')
	return workspace_address

def destroy_workspace(workspace_contract, private_key, mode) :
	# remove workspace data from blockchain
	address = contractsToOwners(workspace_contract, mode)
	contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	nonce = mode.w3.eth.getTransactionCount(address)
	txn = contract.functions.destroyWorkspace().buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1 = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
	if not receipt['status'] :
		return False
	return True

def transfer_workspace(address_from, private_key, address_to, mode) :

	workspace_contract = ownersToContracts(address_from, mode)
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)

	#setup default account for previous address
	acct = Account.from_key(private_key)
	mode.w3.eth.defaultAccount = acct.address

	nonce = mode.w3.eth.getTransactionCount(address_from)
	txn = contract.functions.transferOwnershipInFoundation(workspace_contract, address_to).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)

	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1 = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
	if not receipt['status'] :
		return False
	return True


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
	logging.info("token balance Talaogen = %s", token_balance(mode.Talaogen_public_key,mode))
	# tx_hash = contract.functions.transfer(bob, 100).transact({'from': alice})
	transaction_hash=contract.functions.transfer(address_to, valueTalao ).transact({'from' : mode.Talaogen_public_key,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce})	
	receipt = w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if not receipt['status'] :
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
		Talao_message.message('nameservice', 'thierry.thevenet@talao.io','balance Talaogen < 0.2eth', mode)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000)
	if not receipt['status'] :
		return None
	return hash

def token_balance(address,mode) :
	w3 = mode.w3
	contract=w3.eth.contract(mode.Talao_token_contract,abi=constante.Talao_Token_ABI)
	raw_balance = contract.functions.balanceOf(address).call()
	balance=raw_balance//10**18
	return balance

def has_vault_access(address, mode) :
	w3 = mode.w3
	contract=w3.eth.contract(mode.Talao_token_contract,abi=constante.Talao_Token_ABI)
	return contract.functions.hasVaultAccess(address, address).call()

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
	if not receipt['status'] :
		return None
	return hash

def createWorkspace(address,private_key,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail,mode, user_type=1001) :
	w3 = mode.w3
	contract=w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(address)
	# Build transaction
	txn=contract.functions.createWorkspace(user_type,1,1,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	# send transaction
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)
	if not receipt['status'] :
		return None
	return hash


# check if address is in teh partner list of identity workspace contract
def is_partner(address, identity_workspace_contract, mode):
	# on obtient la liste des partners avec le Relay qui a une cle 1
	acct = Account.from_key(mode.relay_private_key)
	mode.w3.eth.defaultAccount = acct.address
	contract = mode.w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	partner_list = contract.functions.getKnownPartnershipsContracts().call()
	liste = ["Unknown", "Authorized", "Pending", "Rejected", "Removed", ]
	for partner_workspace_contract in partner_list:
		try:
			authorization_index = contract.functions.getPartnership(
			    partner_workspace_contract).call()[1]
		except Exception as ex:
			logging.error('Error : %s',ex)
			return False
		partner_address = contractsToOwners(partner_workspace_contract, mode)
		if partner_address == address and liste[authorization_index] == 'Authorized':
			return True
	return False


# check if address is in the partner list of identity workspace contract
def get_partner_status(address, identity_workspace_contract, mode):
	# on obtient la liste des partners avec le Relay qui a une cle 1
	acct = Account.from_key(mode.relay_private_key)
	mode.w3.eth.defaultAccount = acct.address
	contract = mode.w3.eth.contract(identity_workspace_contract, abi=constante.workspace_ABI)
	partner_list = contract.functions.getKnownPartnershipsContracts().call()
	liste = ["Unknown", "Authorized", "Pending", "Rejected", "Removed", ]
	for partner_workspace_contract in partner_list:
		try:
			authorization_index = contract.functions.getPartnership(partner_workspace_contract).call()[1]
		except Exception as ex:
			logging.error('E = %s',ex)
			return None, None
		partner_address = contractsToOwners(partner_workspace_contract, mode)
		if partner_address == address :
			local_status = liste[authorization_index]
			break
	identity_address = contractsToOwners(identity_workspace_contract, mode)
	identity_private_key = privatekey.get_key(identity_address, 'private_key', mode)
	if identity_private_key :
		acct = Account.from_key(identity_private_key)
		mode.w3.eth.defaultAccount = acct.address
		contract = mode.w3.eth.contract(partner_workspace_contract,abi=constante.workspace_ABI)
		partner_status = liste[contract.functions.getMyPartnershipStatus().call()]
	else :
		partner_status = None
	return local_status, partner_status


def authorize_partnership(address_from, workspace_contract_from, identity_address, identity_workspace_contract, private_key_from, partner_workspace_contract, user_rsa_key, mode, synchronous = True) :	
	# user = identity
	w3 = mode.w3
	partner_address = contractsToOwners(partner_workspace_contract, mode)

	#get Key purpose
	key = mode.w3.soliditySha3(['address'], [partner_address])
	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	address_purpose_list = contract.functions.getKeyPurposes(key).call()
	key = mode.w3.soliditySha3(['address'], [partner_workspace_contract])
	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	workspace_contract_purpose_list = contract.functions.getKeyPurposes(key).call()


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
		if not receipt['status'] :
			logging.error('remove key of address failed purpose = %s', purpose)
			return False
		else :
			logging.info('remove key of address, purpose = %s', purpose)

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
		if not receipt['status'] :
			logging.error('remove key of workspace _contract, purpose = %s', purpose)
			return False
		else :
			logging.info('remove key of workspace _contract, purpose = %s', purpose)

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
	logging.info('user aes = %s', user_aes)
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
	if synchronous  :
		receipt = w3.eth.waitForTransactionReceipt(h, timeout=2000, poll_latency=1)
		if not receipt['status']  :
			logging.error('transaction authorize partnership failed')
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
	key = mode.w3.soliditySha3(['address'], [partner_workspace_contract])
	contract = w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
	workspace_contract_purpose_list = contract.functions.getKeyPurposes(key).call()

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
		if not receipt['status'] :
			logging.error('remove key of address failed, purpose = %s', purpose)
			return False
		else :
			logging.info('remove key of address, purpose = %s', purpose)

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
		if not receipt['status'] :
			logging.error('remove key of workspace _contract failed, purpose = %s', purpose)
			return False
		else :
			logging.info('remove key of workspace _contract, purpose = %s', purpose)

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
	logging.info('talao_token_transaction.py, hash transaction partnership request = %s', hash_transaction)
	if synchronous :
		receipt = w3.eth.waitForTransactionReceipt(hash_transaction, timeout=2000, poll_latency=1)
		if not receipt['status'] :
			logging.error('transaction request partnership failed')
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
	logging.info('hash remove partnership = %s', hash1)
	if synchronous :
		receipt = w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
		if not receipt['status'] :
			logging.error('remove partnership failed')
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
	logging.info('hash reject parnership = %s', hash1)
	if synchronous :
		receipt = w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
		if not receipt['status'] :
			logging.error('transaction request partnership failed')
			return False
	return True


def get_image(workspace_contract, image_type, mode) :
	"""
	image(profil picture) = 105109097103101  signature = 115105103110097116117114101
	return ipfs id
	"""
	w3 = mode.w3
	topicvalue = 105109097103101 if image_type in ['photo', 'logo', 'image', 'picture'] else 115105103110097116117114101
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	try :
		a = contract.functions.getClaimIdsByTopic(topicvalue).call()
	except Exception as res :
		logging.error('get picture in talao_transaction %s', res)
		return None
	if len(a) :
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
	if synchronous :
		receipt = mode.w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
		if not receipt['status'] :
			return None
	return picture_hash

def topicname2topicvalue(topicname) :
	topicvaluestr =''
	for i in range(0, len(topicname))  :
		a = str(ord(topicname[i]))
		if int(a) < 100 :
			a='0'+a
		topicvaluestr = topicvaluestr + a
	return int(topicvaluestr)


############################################################
#  Mise a jour du profil 
############################################################
#
# function updateSelfClaims(
#        uint256[] _topic,
#        bytes _data,
#        uint256[] _offsets

def update_self_claims(address, private_key, mydict, mode) :
	# dict
	w3 = mode.w3
	chaine = ''
	offset = list()
	topic = list()
	for key in mydict :
		#chaine = chaine + '_' + dict[key]
		#offset.append(len('_' +  dict[key]))
		chaine = chaine + mydict[key]
		offset.append(len(mydict[key]))
		topic.append(topicname2topicvalue(key))
	bchaine=bytes(chaine, 'utf-8')
	workspace_contract=ownersToContracts(address,mode)
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(address)
	txn=contract.functions.updateSelfClaims(topic, bchaine,offset).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	# send transaction
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	receipt = w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)
	if not receipt['status']  :
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


def get_all_credentials(workspace_contract, mode) :
	credentials_list=[]
	contract = mode.w3.eth.contract(workspace_contract,abi = constante.workspace_ABI)
	document_list =  contract.functions.getDocuments().call()
	print(document_list)
	for document_id in document_list :
		doctype = contract.functions.getDocument(document_id).call()[0]
		if doctype in [20000, 20001] :
			credentials_list.append(document_id)
	return credentials_list