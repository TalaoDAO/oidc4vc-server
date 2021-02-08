"""
Pour la creation d'un workspace vierge puis tansfert du worjspace vers le owner de la wallet

Creation et sauvegarde des cle de cyryptage : 1 RSA (asymetric) , et 2 cle symetriques.
La cle RSA est sauvegardé dans le format PEM (fichier did.pem)

L email est gardé uniquement pour l authentification, il est crypté dans l identité

Pour la base nameservice on y met "prenom.nom" ou une iteration avec random

une cle 3 est donnée au Web Relay pour une délégation de signature
une cle 20002 est donné a Talao pour emettre des documents et e particulier le proof of identity
une cle 5 est donnée a Talao pour etre ddans al whitelist

La cle privée de l identité n'est pas sauvegardé

"""
import sys
import csv
from Crypto.Protocol.KDF import PBKDF2
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import json
import random
from Crypto.Cipher import AES
from base64 import b64encode
from eth_account.messages import encode_defunct
from datetime import datetime, timedelta
from base64 import b64encode, b64decode

# import des fonctions custom
import Talao_message
from Talao_ipfs import ipfs_add, ipfs_get
import constante
from protocol import  ownersToContracts, token_transfer, createVaultAccess, ether_transfer, add_key, partnershiprequest, authorize_partnership, transfer_workspace
from protocol import Claim, update_self_claims
import ns
import privatekey


# main function called by external modules
def create_user(wallet_address, username, email, mode, rsa=None, secret=None, private=None, creator=None, partner=False,  password=None, firstname=None,  lastname=None, phone=None):
	"""
	wallet_address : crypto account from mobile wallet
	creator : creator address
	"""
	# create a worskpace contract with a random ethereum address
	address, private_key, workspace_contract = _create_user_step_1(wallet_address, email, mode, firstname,  lastname, rsa, private, secret)
	if not address :
		return None, None, None

	# finish the work to be done 
	_create_user_step_2(wallet_address, address, workspace_contract, private_key, username, email, mode, creator, partner,)

	# transfer ownership of workspace contract to wallet address
	if not _create_user_step_3(address, private_key, wallet_address, workspace_contract, username, email, password, phone, mode) :
		return None, None, None

	return wallet_address, None, workspace_contract

def _create_user_step_1(wallet_address, email,mode, firstname, lastname, rsa, private, secret) :

	email = email.lower()
	
	# Setup an initial random private key, public key and address
	account = mode.w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530'+email)
	address = account.address
	private_key = account.privateKey.hex()
	print('Success : random  address = ', address)
	print('Success :  private key = ', private_key)

	if not rsa and not private and  not secret :
		print('rsa key vient du python')
		# create RSA key
		RSA_key = RSA.generate(2048)
		RSA_private = 	RSA_key.exportKey('PEM')
		RSA_public = RSA_key.publickey().exportKey('PEM')

		# Setup a symetric key named 'AES' to encrypt data be shared with partnership. Those data will be said 'private'
		AES_key = get_random_bytes(16)

		# Setup another symetric key named 'SECRET' . those data will be said 'secret'
		SECRET_key = get_random_bytes(16)

		# AES key encrypted with RSA key
		cipher_rsa = PKCS1_OAEP.new(RSA_key)
		AES_encrypted = cipher_rsa.encrypt(AES_key)

		# SECRET encrypted with RSA key
		cipher_rsa = PKCS1_OAEP.new(RSA_key)
		SECRET_encrypted = cipher_rsa.encrypt(SECRET_key)
	else :
		print('rsa key vient de JS')
		RSA_public = rsa
		AES_encrypted = bytes.fromhex(private)
		SECRET_encrypted = bytes.fromhex(secret)

	# Email encrypted with RSA Key
	bemail = bytes(email , 'utf-8')

	print('aes encrypted = ', AES_encrypted)
	print('rsa public =  ', RSA_public)
	return None, None, None

	# activation de l address random
	# Ether transfer from TalaoGen wallet to address
	hash = ether_transfer(address, mode.ether2transfer,mode)
	# Talao tokens transfer from TalaoGen wallet to address
	hash = token_transfer(address,mode.talao_to_transfer,mode)
	# CreateVaultAccess call in the token to declare the identity within the Talao Token smart contract
	hash = createVaultAccess(address,private_key,mode)
	print('Success : create vault acces hash ', hash)

	#pre-activation de l'address de la wallet, il faudra faire un createVaultAccess par la suite
	# Ether transfer from TalaoGen wallet to crypto wallet address
	hash = ether_transfer(wallet_address, mode.ether2transfer,mode)
	# Talao tokens transfer from TalaoGen wallet to crypto wallet address
	hash = token_transfer(wallet_address,mode.talao_to_transfer,mode)

	# Identity setup, creation du workspace contract
	contract = mode.w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
	nonce = mode.w3.eth.getTransactionCount(address)
	
	txn = contract.functions.createWorkspace(1001,1,1,RSA_public, AES_encrypted , SECRET_encrypted, bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 7500000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	receipt = mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if not receipt['status'] :
		print('Error : transaction createWorkspace failed')
		return None, None, None

	# workspace_contract address to be read in foundation smart contract
	workspace_contract = ownersToContracts(address,mode)
	did = 'did:talao:' + mode.BLOCKCHAIN + ':'  + workspace_contract[2:]
	print('Success : workspace_contract has been setup = ',workspace_contract)
	
	if not rsa :
		# store RSA key in file ./RSA_key/rinkeby, talaonet ou ethereum. Format PEM finame = "did.pem"
		filename = "./RSA_key/" + mode.BLOCKCHAIN + "/" + did + ".pem"
		try :
			file = open(filename,"wb")
			file.write(RSA_private)
			file.close()
			print('Success : RSA key stored on disk as ' + did + '.pem')
		except :
			print('Error : RSA key not stored on disk')

	# add plublic key for wallet address
	ns.add_publickey(wallet_address, mode)

	# claims for firstname and lastname
	if firstname and lastname :
		if not update_self_claims(address, private_key, {'firstname': firstname, 'lastname' : lastname}, mode) :
			print('Error : firstname and lastname not updated')
		print('Success : firstname and lastname updated')

	print("Success : create identity process step 1 is over")
	return address, private_key, workspace_contract


def _create_user_step_2(wallet_address, address, workspace_contract, private_key, username, email, mode, creator, partner) :

	# key 5 to Talao be in  White List
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 5, mode)

	# key 20002 to Talao to Issue Proof of Identity
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 20002 , mode)

	# key 3 issued to Web Relay to issue claims
	add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 3, mode)

	# Creator management
	if creator and creator != mode.owner_talao :
		creator_address =creator
		creator_workspace_contract = ownersToContracts(creator_address, mode)
		creator_rsa_key = privatekey.get_key(creator_address, 'rsa_key', mode)
		creator_private_key = privatekey.get_key(creator_address,'private_key', mode)
		RSA_private = privatekey.get_key(address, 'rsa_key', mode)
		# setup partnership
		if partner  :
			# creator requests partnership
			if partnershiprequest(creator_address, creator_workspace_contract, creator_address, creator_workspace_contract, creator_private_key, workspace_contract, creator_rsa_key, mode) :
				if authorize_partnership(address, workspace_contract, address, workspace_contract, private_key, creator_workspace_contract, RSA_private, mode) :
					print('Success : partnership request from creator has been accepted by Identity')
				else :
					print('Error : authorize partnership with creator failed')
			else :
				print('Error : creator partnership request failed')
		#add creator as referent
		if add_key(address, workspace_contract, address, workspace_contract, private_key, creator, 20002 , mode) :
			print('Warning : key 20002 issued for creator')
		else :
			print('Warning : key 20002 for creator failed')
	else :
		print('Warning : no company creator')

	# rewrite previous email to get an encrypted email
	if Claim().add(address,workspace_contract, address, workspace_contract,private_key, 'email', email, 'private', mode)[0] :
		print('Success : email encryted updated')
	else :
		print('Error : email encrypted not updated')

	# emails send to user and admin
	Talao_message.messageLog("no lastname", "no firstname", username, email, "createidentity.py", wallet_address, private_key, workspace_contract, "", email, "", "", mode)

	# an email is sent to user
	Talao_message.messageUser("no lastname", "no fistname", username, email, wallet_address, private_key, workspace_contract, mode)

	print("Success : create identity process step 2 is over")
	return True


# this function transfers workspace to new wallet and setup identity in nameservice
def _create_user_step_3(address, private_key, wallet_address, workspace_contract, username, email, password, phone, mode) :
	# transfer workspace
	if not transfer_workspace(address, private_key, wallet_address, mode) :
		print('Error : transfer failed')
		return False

	# add username to register in local nameservice Database with last check.....
	if ns.username_exist(username, mode) :
		username = username + str(random.randint(1, 100))
	ns.add_identity(username, workspace_contract, email, mode)

		# setup password
	if password :
		ns.update_password(username, password, mode)
		print('Success : password has been updated')

	# setup phone
	if phone :
		ns.update_phone(username, phone, mode)
		print('Success : phone has been updated')

	print("Success : create identity process step 3 is over")
	return True