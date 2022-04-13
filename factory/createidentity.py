"""
Pour la cration d'un workspace vierge Identity) depuis le webserver :
Creation d' un wallet pour le owner
Creation des cle de cyryptage : 1 RSA (asymetric) , et 2 cle symetriques
L email est gardé uniquement pour l authentification, il est crypté dans l identité
Pour la base SQL (nameservice) on y met "prenom.nom" ou un equivalent
une cle 1 (ERC725) est donnée au Web Relay pour uen délégation de signature
La cle privée de l identité est sauvergaée dans private.key.db

"""
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import json
import didkit

import logging
logging.basicConfig(level=logging.INFO)

# import des fonctions custom
import constante
from protocol import  ownersToContracts, token_transfer, createVaultAccess, ether_transfer, add_key
from components import privatekey, ns, Talao_message
from signaturesuite import helpers

# main function called by external modules
def create_user(username, email, mode, did='', password='', firstname=None,  lastname=None, phone='', silent=False):

	email = email.lower()

	# Setup user address for repository
	account = mode.w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530'+email)
	address = account.address
	private_key = account.key.hex()
	logging.info('user repository talaonet address setup')
	print('did = ', did)
	if did in ['tz', 'ethr'] :
		# one creates did from scratch
		this_key = helpers.ethereum_to_jwk256kr(private_key)
		did = didkit.key_to_did(did, this_key)
		logging.info('registration with password')
	else :
		logging.info('registration with wallet')

	# create RSA key as derivative from Ethereum private key
	RSA_key, RSA_private, RSA_public = privatekey.create_rsa_key(private_key, mode)
	# Setup a key (symetric) named 'AES' to encrypt private data and to be shared with partnership
	AES_key = get_random_bytes(16)

	# Setup another key named 'SECRET' (symetric) to encrypt secret data
	SECRET_key = get_random_bytes(16)

	# AES key encrypted with RSA key
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted = cipher_rsa.encrypt(AES_key)

	# SECRET encrypted with RSA key
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted = cipher_rsa.encrypt(SECRET_key)

	# Email encrypted with RSA Key
	bemail = bytes(email , 'utf-8')

	# Ether transfer from TalaoGen wallet
	if not ether_transfer(address, mode.ether2transfer,mode) :
		logging.error('ether transfer failed')
		return None, None, None
	logging.info('ether transfer done')

	# Talao tokens transfer from TalaoGen wallet
	if not token_transfer(address,mode.talao_to_transfer,mode) :
		logging.error('token transfer failed')
		return None, None, None
	logging.info('token transfer done')

	# CreateVaultAccess call in the token to declare the identity within the Talao Token smart contract
	if not createVaultAccess(address,private_key,mode) :
		logging.error('create vault access failed')
		return None, None, None
	logging.info('create vault access done')

	# Identity setup
	contract = mode.w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
	nonce = mode.w3.eth.getTransactionCount(address)
	txn = contract.functions.createWorkspace(1001,1,1,RSA_public, AES_encrypted , SECRET_encrypted, bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 7500000,'gasPrice': mode.w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = mode.w3.eth.account.signTransaction(txn,private_key)
	mode.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = mode.w3.toHex(mode.w3.keccak(signed_txn.rawTransaction))
	if not mode.w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)['status'] :
		logging.error('transaction createWorkspace failed')
		return None, None, None
	logging.info('createWorkspace done')

	# workspace_contract address to be read in fondation smart contract
	workspace_contract = ownersToContracts(address,mode)
	logging.info('workspace_contract has been setup = %s',workspace_contract)

	# store RSA key in file ./RSA_key/rinkeby, talaonet ou ethereum
	filename = "./RSA_key/" + mode.BLOCKCHAIN + '/did:talao:' + mode.BLOCKCHAIN + ':'  + workspace_contract[2:] + ".pem"
	try :
		file = open(filename,"wb")
		file.write(RSA_private)
		file.close()
		logging.info('RSA key stored on disk')
	except :
		logging.error('RSA key not stored on disk')

	# add username to register in local nameservice Database
	
	filename = mode.db_path + 'person.json'
	personal = json.load(open(filename, 'r'))
	personal['signature'] = 'QmPZxzrmh29sNcgrT7hyrrP6BWyahLwYUvzbuf5vUFxw91' #'macron.png'
	personal['picture'] = 'QmRPGGnVSa6jpaDSYnfk1v2bRZ2kkTML2aapU9cqzVRqXN' # 'unknown.png'
	personal['contact_email']['claim_value'] = email
	if firstname and lastname :
		personal['lastname']['claim_value'] = lastname
		personal['firstname']['claim_value'] = firstname
	personal = json.dumps(personal, ensure_ascii = False)
	if not ns.add_identity(username,
						workspace_contract,
						email,
						mode,
						phone=phone,
						password=password,
						did=did,
						personal=personal)  :
		logging.error('add identity in nameservice.db failed')
		return None, None, None
	logging.info('add identity in nameservice.db done')

	# store Ethereum private key in keystore
	if not privatekey.add_private_key(private_key, mode) :
		logging.error('add private key in keystore failed')
		return None, None, None
	else :
		logging.info('private key in keystore')

	# key 1 issued to Web Relay to act as agent.
	if not add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode) :
		logging.error('add key 1 to web Relay failed')
	else :
		logging.info('key 1 to web Relay has been added')

	# emails send to admin
	Talao_message.messageLog(lastname, firstname, username, email, "createidentity.py", address, private_key, workspace_contract, "", email, "", "", mode)

	if not silent :
		# By default an email is sent to user
		Talao_message.messageUser(lastname, firstname, username, email, address, private_key, workspace_contract, mode)

	logging.info('end of create identity')
	return address, private_key, workspace_contract

