"""
If this script is called in a standalone mode (_name_ == '_main_').
It will setup workspaces for Relay and Talao
"""

from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Protocol.KDF import PBKDF2
import json
from eth_account.messages import encode_defunct
from Crypto.Cipher import AES
from base64 import b64encode
from datetime import datetime
from base64 import b64encode, b64decode

# dependances
from protocol import ether_transfer, ownersToContracts, token_transfer, createVaultAccess, add_key
from Talao_ipfs import ipfs_add, ipfs_get
import Talao_message
import constante
import ns
import privatekey
#import ethereum_bridge see later

# Global variables for RSA
#master_key = ""
#salt = ""
# Global variable for Relay and Talao setup
relay_address = ""

def email2(address, workspace_contract, private_key, email, AES_key, mode) :
	""" This function signs a claim with sheme 2 and an encrypted email with secret key. email  topicvalue = 101109097105108
	Tiis is the only solution to rewrite and encrypt the email which is stored at workspace setup (seen workspace factory)
	"""
	w3 = mode.w3

	# encrypt email
	bytesdatajson = bytes(json.dumps({'email' : email}), 'utf-8') # dict -> json(str) -> bytes
	header = b"header"
	cipher = AES.new(AES_key, AES.MODE_EAX) #https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html
	cipher.update(header)
	ciphertext, tag = cipher.encrypt_and_digest(bytesdatajson)
	json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
	json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, header, ciphertext, tag] ]
	dict_data = dict(zip(json_k, json_v))

	ipfs_hash = ipfs_add(dict_data,mode)

	if mode.test :
		print('ipfs_hash email2 = ', ipfs_hash)


	# Signature
	nonce = w3.eth.getTransactionCount(address)
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes('email', 'utf-8'), address, bytes(email, 'utf-8'), bytes(ipfs_hash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=private_key)
	signature = signed_message['signature']

	# ERC725 claim id
	claim_id = w3.solidityKeccak(['address', 'uint256'], [address, 101109097105108]).hex()

	# Transaction
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	txn = contract.functions.addClaim(101109097105108, 2, 	address, signature, bytes('secret', 'utf-8'),ipfs_hash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = w3.eth.account.signTransaction(txn,private_key)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	receipt = w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	if receipt['status'] == 0 :
		return False

	if mode.test :
		print ('email claim Id = ', claim_id)
		print('email 2 transaction hash = ', transaction_hash)

	return True

def _createWorkspace(address,private_key,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail,mode) :
	""" Main transaction to create workspace in protocol """

	w3 = mode.w3
	contract = w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)
	nonce = w3.eth.getTransactionCount(address)

	# Transaction
	txn=contract.functions.createWorkspace(2001,1,1,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)
	if receipt['status'] == 0 :
		print('Failed transaction createWprkspace')
		return None
	return hash


def create_company(email, username, mode, creator=None, partner=False) :
	""" username is a company name here
	one does not check if username exist here """

	global relay_address

	# wallet init
	account = mode.w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
	address = account.address
	private_key = account.privateKey.hex()
	print('adresse = ', address)
	print('private key = ', private_key)

	RSA_key, RSA_private, RSA_public = privatekey.create_rsa_key(private_key, mode)

	# stockage de la cle privée RSA dans un fichier du repertoire ./RSA_key/rinkeby ou ethereum ou talaonet
	filename = "./RSA_key/" + mode.BLOCKCHAIN + '/'+ str(address) + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	try :
		file=open(filename,"wb")
		file.write(RSA_private)
		file.close()
	except :
		print('RSA key not stored')

	# création de la cle AES
	AES_key = get_random_bytes(16)

	# création de la cle SECRET
	SECRET_key = get_random_bytes(16)

	# encryption de la cle AES avec la cle RSA
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted=cipher_rsa.encrypt(AES_key)

	# encryption de la cle SECRET avec la cle RSA
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted=cipher_rsa.encrypt(SECRET_key)

	# Email to bytes
	bemail = bytes(email , 'utf-8')

	# Transaction pour le transfert des nethers depuis le portfeuille TalaoGen
	hash1 = ether_transfer(address, mode.ether2transfer, mode)
	print('hash de transfert de 0.06 eth = ',hash1)

	# Transaction pour le transfert des tokens Talao depuis le portfeuille TalaoGen
	hash2 = token_transfer(address, mode.talao_to_transfer, mode)
	print('hash de transfert de 101 TALAO = ', hash2)

	# Transaction pour l'acces dans le token Talao par createVaultAccess
	hash3=createVaultAccess(address, private_key, mode)
	print('hash du createVaultaccess = ', hash3)

	# Transaction pour la creation du workspace :
	bemail = bytes(email , 'utf-8')
	hash =_createWorkspace(address, private_key, RSA_public, AES_encrypted, SECRET_encrypted, bemail, mode)
	if hash is None :
		return None, None, None
	print('hash de createWorkspace =', hash)

	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract = ownersToContracts(address, mode)
	print( 'workspace contract = ', workspace_contract)

	# For setup of new chain one need to first create workspaces for Relay and Talao
	if username != 'relay' and username != 'talao' :
		# management key (1) issued to Relay
		add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode, synchronous=True)
	if username == 'relay' :
		# one stores relay address for Talao workspace setup
		relay_address = address
	if username == 'talao' :
		add_key(address, workspace_contract, address, workspace_contract, private_key, relay_address, 1, mode, synchronous=True) 

	# rewrite encrypted email with scheme 2 to differenciate from freedapp email that are not encrypted
	email2(address, workspace_contract, private_key, email, AES_key, mode)

	if username != 'talao' and username != 'relay' :
		# key 20002 to Talao to Issue Proof of Identity
		add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 20002 , mode, synchronous=True) 
		# key 5 to Talao to be in White List
		add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 5 , mode, synchronous=True) 
	else :
		pass

	# update resolver and create local database for this company
	ns.add_identity(username, workspace_contract, email, mode)
	# create databe for manager within the company
	ns.init_host(username, mode)

	# add private key
	if privatekey.add_private_key(private_key, mode) :
		print('New company has been added ')
		Talao_message.messageLog("no lastname",
								 "no firstname",
								 username, email,
								 'Company created by Talao',
								 address,
								 private_key,
								 workspace_contract,
								 "",
								 email,
								 SECRET_key.hex(),
								 AES_key.hex(),
								 mode)
	else :
		print('add private key failed')
		return None, None, None

	# synchro with ICO token
	#ethereum_bridge.lock_ico_token(address, private_key)

	return address, private_key, workspace_contract


# MAIN, for new Blockchain setup. Talao and Relay setup
if __name__ == '__main__':

	import environment
	import os

	mychain = os.getenv('MYCHAIN')
	myenv = os.getenv('MYENV')
	password = os.getenv('PASSWORD')
	smtp_password = os.getenv('SMTP_PASSWORD')

	print('environment variable : ',mychain, myenv, password)
	print('New BLockchain Setup')
	print('Setup Relay and Talao company')

	# environment setup
	mode = environment.currentMode(mychain, myenv)

	# relay setup
	(relay_address, relay_private_key, relay_workspace_contract) = create_company('thierry.thevenet@talao.io', 'relay', mode)

	# Talao setup (one uses Relay address which has beee stored in Global variable)
	(talao_address, talao_private_key, talao_workspace_contract) = create_company('thierry.thevenet@talao.io', 'talao', mode)

	print('relay owner address : ', relay_address)
	print('relay private key : ' , relay_private_key)
	print('relay workspace contract : ', relay_workspace_contract)
	print('talao owner address : ', talao_address)
	print('talao private key : ' , talao_private_key)
	print('talao workspace contract : ', talao_workspace_contract)

