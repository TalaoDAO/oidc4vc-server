"""
If this script is called in a standalone mode (_name_ == '_main_').
It will setup workspaces for Relay and Talao


Pour le lien au domaine:
did:web  ou did:ion
avec unservice endpoint sur linkedDomain
Puis un fichier  {
        "@context": "https://identity.foundation/.well-known/did-configuration/v1",
        "linked_dids": ["eyJhbGciOiJFUzI1NksiLCJraWQiOiJkaWQ6d2ViOnRhbGFvLmNvI2RvbWFpbi0xIn0.eyJleHAiOjE3Nzc2MzUwNDMsImlzcyI6ImRpZDp3ZWI7dGFsYW8uY28iLCJuYmYiOjE2MjAzODcwNDMsInN1YiI6ImRpZDp3ZWI6dGFsYW8uY28iLCJAY29udGV4dCI6WyJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy92MSIsImh0dHBzOi8vaWRlbnRpdHkuZm91bmRhdGlvbi8ud2VsbC1rbm93bi9kaWQtY29uZmlndXJhdGlvbi92MSJdLCJjcmVkZW50aWFsU3ViamVjdCI6eyJpZCI6ImRpZDp3ZWI6dGFsYW8uY28iLCJvcmlnaW4iOiJodHRwczovL3RhbGFvLmNvIn0sImV4cGlyYXRpb25EYXRlIjoiMjAyNS0xMi0wNFQxNDowODowMC0wMDowMCIsImlzc3VhbmNlRGF0ZSI6IjIwMjEtMDUtMDdUMTQ6MDg6MjgtMDY6MDAiLCJpc3N1ZXIiOiJkaWQ6d2ViOnRhbGFvLmNvIiwidHlwZSI6WyJWZXJpZmlhYmxlQ3JlZGVudGlhbCIsIkRvbWFpbkxpbmthZ2VDcmVkZW50aWFsIl19.V9jL8eMPHQW4SUy0CDds9VFaGrvkcBhaNYKvnb01rAdKQoKGtII00zzZggIS2KbF_zN_llP5Em1gkhnw6ztJLA"
            ]}
sur https://nom.domaone//.well-known/did-configuration.json
utiliser un JWT pour obtenir une signature correcte




"""
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Protocol.KDF import PBKDF2
import json
from Crypto.Cipher import AES
from datetime import datetime
import random
import logging
logging.basicConfig(level=logging.INFO)

# dependances
from protocol import ether_transfer, ownersToContracts, token_transfer, createVaultAccess, add_key
from protocol import createWorkspace
from components import Talao_message, ns, privatekey
import constante

relay_address = ""

# Main function
def create_company(email, username, did, mode, siren=None, name=None) :

	global relay_address

	# wallet init
	account = mode.w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
	address = account.address
	private_key = account.privateKey.hex()
	logging.info('adresse = %s', address)
	logging.info('Success : private key = %s', private_key)

	# calculate RSA key
	RSA_key, RSA_private, RSA_public = privatekey.create_rsa_key(private_key, mode)

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

	try :
		# Transaction pour le transfert des nethers depuis le portfeuille TalaoGen
		h1 = ether_transfer(address, mode.ether2transfer, mode)
		logging.info('ether transfer done')
		# Transaction pour le transfert des tokens Talao depuis le portfeuille TalaoGen
		h2 = token_transfer(address, mode.talao_to_transfer, mode)
		logging.info('token transfer done')
		# Transaction pour l'acces dans le token Talao par createVaultAccess
		h3 = createVaultAccess(address, private_key, mode)
		logging.info('create vault access done')
		# Transaction pour la creation du workspace :
		bemail = bytes(email , 'utf-8')
		h4 = createWorkspace(address, private_key, RSA_public, AES_encrypted, SECRET_encrypted, bemail, mode, user_type=2001)
		logging.info('create create workspace done')
	except :
		logging.error('transaction failed')
		return None, None, None
	if not (h1 and h2 and h3 and h4) :
		logging.error('transaction failed')
		return None, None, None

	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract = ownersToContracts(address, mode)
	logging.info( 'workspace contract = %s', workspace_contract)

	# store RSA key in file ./RSA_key/rinkeby, talaonet ou ethereum
	filename = "./RSA_key/" + mode.BLOCKCHAIN + '/did:talao:' + mode.BLOCKCHAIN + ':'  + workspace_contract[2:] + ".pem"
	try :
		file = open(filename,"wb")
		file.write(RSA_private)
		file.close()
		logging.info('RSA key stored on disk')
	except :
		logging.error(' RSA key not stored on disk')

	# add private key in keystore
	if privatekey.add_private_key(private_key, mode) :
		logging.info('private key added in keystore ')
	else :
		logging.error('add private key failed')
		return None, None, None

	# update resolver and create local database for this company
	if not ns.add_identity(username, workspace_contract, email, mode, did=did) :
		logging.error('add identity in nameservice failed')
		return None, None, None

	# create database for manager within the company
	if not ns.init_host(username, mode) :
		logging.error('add company in nameservice failed')

	# For setup of new chain one need to first create workspaces for Relay and Talao
	if username != 'relay' and username != 'talao' :
		# management key (1) issued to Relay
		add_key(address, workspace_contract, address, workspace_contract, private_key, mode.relay_address, 1, mode)

	if username == 'relay' :
		# one stores relay address for Talao workspace setup
		relay_address = address
	if username == 'talao' :
		add_key(address, workspace_contract, address, workspace_contract, private_key, relay_address, 1, mode)

	# send messages
	Talao_message.messageLog("no lastname","no firstname", username, email, 'Company created by Talao', address, private_key, workspace_contract, "", email, "", "", mode)
	# one sends an email by default
	Talao_message.messageUser("no lastname", "no firstname", username, email, address, private_key, workspace_contract, mode)

	logging.info('end of of create company')
	return address, private_key, workspace_contract


# MAIN, for new Blockchain setup. Talao and Relay setup
if __name__ == '__main__':

	import environment
	import os

	mychain = os.getenv('MYCHAIN')
	myenv = os.getenv('MYENV')
	password = os.getenv('PASSWORD')
	smtp_password = os.getenv('SMTP_PASSWORD')


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

