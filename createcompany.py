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
import random

# dependances
from protocol import ether_transfer, ownersToContracts, token_transfer, createVaultAccess, add_key, authorize_partnership, partnershiprequest
from protocol import createWorkspace, Claim

from Talao_ipfs import ipfs_add, ipfs_get
import Talao_message
import constante
import ns
from privatekey import get_key, create_rsa_key, add_private_key
#import ethereum_bridge see later

relay_address = ""

def create_company(email, username, mode, creator=None, partner=False, send_email=True, siren=None, password=None) :
	""" username is a company name here
	one does not check if username exist here """
	global relay_address

	# wallet init
	account = mode.w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
	address = account.address
	private_key = account.privateKey.hex()
	print('Success : adresse = ', address)
	print('Success : private key = ', private_key)

	# calculate RSA key
	RSA_key, RSA_private, RSA_public = create_rsa_key(private_key, mode)
	# we store the private RSA key PEM in ./RSA_key/chain directyory
	filename = "./RSA_key/" + mode.BLOCKCHAIN + '/'+ str(address) + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	try :
		file=open(filename,"wb")
		file.write(RSA_private)
		file.close()
	except :
		print('Error : RSA key not stored')

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
	print('Success : hash for eth transfert 0.06 eth = ',hash1)

	# Transaction pour le transfert des tokens Talao depuis le portfeuille TalaoGen
	hash2 = token_transfer(address, mode.talao_to_transfer, mode)
	print('Success : hash for token transfert  101 TALAO = ', hash2)

	# Transaction pour l'acces dans le token Talao par createVaultAccess
	hash3=createVaultAccess(address, private_key, mode)
	print('Success : hash createVaultaccess = ', hash3)

	# Transaction pour la creation du workspace :
	bemail = bytes(email , 'utf-8')
	hash = createWorkspace(address, private_key, RSA_public, AES_encrypted, SECRET_encrypted, bemail, mode, user_type=2001)
	if not hash :
		return None, None, None
	print('Success : hash createWorkspace =', hash)

	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract = ownersToContracts(address, mode)
	print( 'Success : workspace contract = ', workspace_contract)



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
	claim_id = Claim().add(address,workspace_contract, address, workspace_contract,private_key, 'email', email, 'private', mode)[0]
	if claim_id :
		print('Success : email updated')
	else :
		print('Error : email update')

	# add siren
	if siren :
		claim_id = Claim().add(address,workspace_contract, address, workspace_contract,private_key, 'siren', siren, 'private', mode)[0]
		if claim_id :
			print('Success : siren updated')
		else :
			print('Error : siren update')

	if username != 'talao' and username != 'relay' :
		# key 20002 to Talao to ask Talao to issue Proof of Identity
		add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 20002 , mode, synchronous=True) 
		# key 5 to put Talao in White List
		# add_key(address, workspace_contract, address, workspace_contract, private_key, mode.owner_talao, 5 , mode, synchronous=True)
		# key 5 to put ourself in Whitelist
		add_key(address, workspace_contract, address, workspace_contract, private_key, address, 5 , mode, synchronous=True)

	# Creator
	if creator and creator != mode.owner_talao :
		creator_address = creator
		creator_workspace_contract = ownersToContracts(creator_address, mode)
		creator_rsa_key = get_key(creator, 'rsa_key', mode)
		creator_private_key = get_key(creator,'private_key', mode)
		# setup parnership with creator
		if partner :
			# creator requests partnership
			if partnershiprequest(creator_address, creator_workspace_contract, creator_address, creator_workspace_contract, creator_private_key, workspace_contract, creator_rsa_key, mode, synchronous= True) :
				if authorize_partnership(address, workspace_contract, address, workspace_contract, private_key, creator_workspace_contract, RSA_private, mode, synchronous = True) :
					print('Success : partnership request from creator has been accepted')
				else :
					print('Error : authorize partnership with creator failed')
			else :
				print('Error : creator partnership request failed')
		#add creator as referent
		if add_key(address, workspace_contract, address, workspace_contract, private_key, creator, 20002 , mode, synchronous=True) :
			print('Success : key 20002 issued for creator')
		else :
			print('Success : key 20002 for creator failed')

	# update resolver and create local database for this company with last check on username
	if ns.username_exist(username, mode) :
		username = username + str(random.randint(1, 100))
	ns.add_identity(username, workspace_contract, email, mode)
	if password :
		ns.update_password(username, password, mode)
		print('Success : password has been updated')
	# create database for manager within the company
	ns.init_host(username, mode)

	# add private key in keystore
	if add_private_key(private_key, mode) :
		print('Success : new company has been added ')
		Talao_message.messageLog("no lastname","no firstname", username, email, 'Company created by Talao', address, private_key, workspace_contract, "", email, SECRET_key.hex(), AES_key.hex(), mode)
		# one sends an email by default
		if send_email :
			Talao_message.messageUser("no lastname", "no firstname", username, email, address, private_key, workspace_contract, mode)
	else :
		print('Error : add private key failed')
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

