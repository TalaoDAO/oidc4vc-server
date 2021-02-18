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
import time

# import des fonctions custom
import Talao_message
from Talao_ipfs import ipfs_add, ipfs_get
import constante
from protocol import  ownersToContracts, token_transfer, createVaultAccess, ether_transfer, add_key, partnershiprequest, authorize_partnership, transfer_workspace
from protocol import Claim, update_self_claims
import ns
import privatekey
#import ethereum_bridge

# main function called by external modules
def create_user(wallet_address, username, email, mode, user_aes_encrypted_with_talao_key = None, rsa=None, secret=None, private=None, password=None, firstname=None,  lastname=None, phone=None, transfer=True):

	# STEP 1 : create a worskpace contract with a random ethereum address
	address, private_key, workspace_contract = _create_user_step_1(wallet_address, email, mode, firstname,  lastname, rsa, private, secret)
	if not address :
		return None, None, None

	# STEP 2 : finish the work to be done
	_create_user_step_2(wallet_address, address, workspace_contract, private_key, username, email, mode, user_aes_encrypted_with_talao_key, transfer)

	# STEP 3 : transfer ownership of workspace contract to wallet address or setup an alias
	if not _create_user_step_3(address, private_key, wallet_address, workspace_contract, username, email, password, phone, mode, transfer) :
		return None, None, None

	return wallet_address, None, workspace_contract

def _create_user_step_1(wallet_address, email,mode, firstname, lastname, rsa, private, secret) :

	# clean RSA pem key received (str)
	RSA_public = rsa.encode('utf-8')
	RSA_public = RSA_public.replace(b'\r\n', b'\n')

	print('private reçu = ', private, type(private))
	# get bytes from keys generated and encrypted client side. Keys have been passed (JS=>Python) un hex trsing
	AES_encrypted = bytes.fromhex(private[2:])
	SECRET_encrypted = bytes.fromhex(secret[2:])

	# Setup an initial random private key and derive address
	account = mode.w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530'+email)
	address = account.address
	private_key = account.privateKey.hex()

	# store Ethereum private key in keystore
	if not privatekey.add_private_key(private_key, mode) :
		print('Error : add private key in keystore failed')
		return None, None, None
	else :
		print('Success : private key in keystore')

	# Email requested by solidity function. it will be encrypted later on
	#bemail = bytes(email.lower() , 'utf-8')
	bemail = bytes(" ".lower() , 'utf-8')

	# Ether transfer from TalaoGen wallet to address
	ether_transfer(address, mode.ether2transfer,mode)
	# Talao tokens transfer from TalaoGen wallet to address
	token_transfer(address,mode.talao_to_transfer,mode)
	# CreateVaultAccess call in the token to declare the identity within the Talao Token smart contract
	if not createVaultAccess(address,private_key,mode) :
		print('Error : transaction createVultAccess failed')
		return None, None, None

	# Identity setup, deploy workspace contract on blockchain
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
	print('Success : workspace_contract has been setup = ',workspace_contract)

	# add hexpublic key for wallet address
	ns.add_publickey(wallet_address, mode)

	 # claims for firstname and lastname
	if firstname and lastname :
		if not update_self_claims(address, private_key, {'firstname': firstname, 'lastname' : lastname}, mode) :
			print('Error : firstname and lastname not updated')
		print('Success : firstname and lastname updated')

	print("Success : create identity process step 1 is over")
	return address, private_key, workspace_contract

def _create_user_step_2(wallet_address, address, workspace_contract, private_key, username, email, mode, user_aes_encrypted_with_talao_key, transfer) :

	# get bytes from str received from JS
	user_private_encrypted_with_talao_key = bytes.fromhex(user_aes_encrypted_with_talao_key[2:])

	# For ID issuance Talao requests partnership to Identity, (key 3 will be issued too)
	talao_rsa_key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
	talao_private_key = privatekey.get_key(mode.owner_talao,'private_key', mode)
	if partnershiprequest(mode.owner_talao, mode.workspace_contract_talao, mode.owner_talao, mode.workspace_contract_talao, talao_private_key, workspace_contract, talao_rsa_key, mode, user_aes_encrypted_with_talao_key) :
		print('Success : Talao partnership request has been sent')
		# Identity(user) must accept partnership request
		nonce = mode.w3.eth.getTransactionCount(address)
		contract= mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		txn=contract.functions.authorizePartnership(mode.workspace_contract_talao, user_private_encrypted_with_talao_key).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
		signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)
		mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
		h = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
		receipt = mode.w3.eth.waitForTransactionReceipt(h, timeout=2000, poll_latency=1)
		if receipt['status']  :
			print('Success : Talao partnership request has been accepted by Identity')
		else :
			print('Error : authorize partnership with Talao failed')
	else :
		print('Error : partnership request from Talao failed')

	# key 3 issued to Web Relay to issue self claims
	if add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 3, mode) :
		print('Warning : key 3 issued to Relay')
	else :
		print('Warning : key 3 to Relay failed')

	# key 20002 issued to Web Relay to issue documents for self resume
	if add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 3, mode) :
		print('Warning : key 20002 issued to Relay')
	else :
		print('Warning : key 20002 to Relay failed')

	# key 5 to Talao be in  White List
	#if add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 5, mode) :
	#	print('Warning : key 5 issued to Talao')
	#else :
	#	print('Warning : key 5 to Talao failed')

	# key 20002 issued Talao to issue documents
	#if not transfer :
	#	if add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 20002 , mode) :
	#		print('Warning : key 20002 issued to Talao')
	#	else :
	#		print('Warning : key 20002 to Talao failed')

	# rewrite previous email to get an encrypted email with public key
	#if Claim().add(address,workspace_contract, address, workspace_contract,private_key, 'email', email, 'public', mode)[0] :
	#	print('Success : email encryted updated')
	#else :
	#	print('Error : email encrypted not updated')

	print("Success : create identity process step 2 is over")
	return True

# this function transfers workspace to new wallet OR add wallet as an alias and setup identity in nameservice
def _create_user_step_3(address, private_key, wallet_address, workspace_contract, username, email, password, phone, mode, transfer) :

	# add username to register in local nameservice Database with last check
	if ns.username_exist(username, mode) :
		username = username + str(random.randint(1, 100))
	ns.add_identity(username, workspace_contract, email, mode)

	# transfer workspace / alias
	if transfer :
		email_address = wallet_address
		if not transfer_workspace(address, private_key, wallet_address, mode) :
			print('Error : status transfer failed')
			return False
		print('Success : workspace ownership tranfered to ' + wallet_address)
	else :
		email_address = address
		ns.update_wallet(workspace_contract, wallet_address, mode)
		print('Warning : wallet address added as an alias')


	# setup password
	if password :
		ns.update_password(username, password, mode)
		print('Success : password has been updated')

	# setup phone
	if phone :
		ns.update_phone(username, phone, mode)
		print('Success : phone has been updated')

	#pre-activation de l'address de la wallet, il faudra faire un createVaultAccess par la suite
	#ether_transfer(wallet_address, mode.ether2transfer,mode)
	#token_transfer(wallet_address,mode.talao_to_transfer,mode)

	#time.sleep(10)

	# emails send to user and admin
	Talao_message.messageLog("", "", username, email, "createidentity.py", email_address, "", workspace_contract, "", email, "", "", mode)
	# an email is sent to user
	Talao_message.messageUser("", "", username, email, email_address, "", workspace_contract, mode)

	#if mode.myenv == 'aws' :
	#	ethereum_bridge.lock_ico_token(None, None)
	#	print('transfer Ethereum token done')

	print("Success : create identity process step 3 is over")
	return True