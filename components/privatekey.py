import json
import os
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from eth_account import Account
from Crypto.Util.Padding import pad
import logging
from jwcrypto import jwk

logging.basicConfig(level=logging.INFO)

import constante
from signaturesuite import helpers

def ownersToContracts(address, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	workspace_address = contract.functions.ownersToContracts(address).call()
	return workspace_address


def contractsToOwners(workspace_contract, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	return address


def decrypt_data(workspace_contract_user, data, privacy, mode, address_caller=None) :
	#recuperer la cle AES cryptée
	# on encrypt en mode CBC pour compatiblité avec librairie JS
	address_user = contractsToOwners(workspace_contract_user, mode)
	if privacy == 'public' :
		aes = mode.aes_public_key.encode('utf-8')
	elif privacy == 'private' :
		aes = get_key(address_user, 'aes_key', mode, address_caller)
	elif privacy == 'secret' :
		logging.warning('secret key has been called in privateky.py')
		aes = get_key(address_user, 'secret_key', mode)
	else :
		logging.error("privacy error")
		return None
	if not aes :
		logging.info('no RSA key on server')
		return None
	# decrypt data
	try:
		b64 = data #json.loads(json_input)
		json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
		jv = {k:b64decode(b64[k]) for k in json_k}
		cipher = AES.new(aes, AES.MODE_EAX, nonce=jv['nonce'])
		cipher.update(jv['header'])
		plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag']).decode('utf-8')
		logging.warning('EAX decryptage - to be deprecated')
	except :
		data = b64decode(data['ciphertext'])
		bytes = PBKDF2(aes, "salt".encode("utf-8"), 128, 128)
		iv = bytes[0:16]
		key = bytes[16:48]
		cipher = AES.new(key, AES.MODE_CBC, iv)
		plaintext = cipher.decrypt(data)
		plaintext = plaintext[:-plaintext[-1]].decode("utf-8")
	return json.loads(plaintext)


def encrypt_data(identity_workspace_contract, data, privacy, mode, address_caller=None) :
	# parameter data is dict
	# return dict is dict
	#https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html
	# on enc rypte ne ode CBC a/c de 01/02/2021

	identity_address = contractsToOwners(identity_workspace_contract, mode)
	if privacy == 'public' :
		aes = mode.aes_public_key.encode()
	elif privacy == 'private' :
		aes = get_key(identity_address, 'aes_key', mode)
	elif privacy == 'secret' :
		aes = get_key(identity_address, 'secret_key', mode)
	else :
		logging.error('incorrect privacy ')
		return None
	if not aes :
		logging.error('RSA key not found on server or cannot decrypt AES')
		return None

	# AES-CBC encryption for compatibility with Javascrip librairy
	message = json.dumps(data).encode('utf-8')
	bytes = PBKDF2(aes, "salt".encode("utf-8"), 128, 128)
	iv = bytes[0:16]
	key = bytes[16:48]
	cipher = AES.new(key, AES.MODE_CBC, iv)
	encrypted = cipher.encrypt(pad(message, AES.block_size))
	ct = b64encode(encrypted).decode('utf-8')
	dict_data = {"ciphertext" : ct}
	return dict_data


def add_private_key(private_key, mode) :
	encrypted = Account.encrypt(private_key, mode.password)
	address = mode.w3.toChecksumAddress(encrypted['address'])
	try :
		f = open(mode.keystore_path + address[2:] +".json", 'w')
	except :
		return False
	f.write(json.dumps(encrypted))
	f.close()
	return True


def generate_store_key(address, curve, mode) :
	"""
	curve = Ed25519 or P-256, and secp255k1... id needed
	return str
	"""
	if curve == 'Ed25519' :
		key = jwk.JWK.generate(kty="OKP", crv='Ed25519')
	elif curve == 'P-256' :
		key = jwk.JWK.generate(kty="EC", crv="P-256")
	elif curve == 'secpp256k1' :
		key = jwk.JWK.generate(kty="EC", crv="secp256k1")
		logging.info('key not stored')
		return False
	else :
		logging.error('curve not supported')
		return False
	curve = curve.replace('-','')
	key_pem = key.export_to_pem(private_key=True, password=mode.password.encode())
	filename = getattr(mode, curve + '_path') + address + '.' + curve
	f = open(filename, 'w')
	f.write(key_pem.decode())
	f.close()
	return True


# create a RSA key
def create_rsa_key(private_key, mode) :
	RSA_key = RSA.generate(2048)
	return  RSA_key, RSA_key.exportKey('PEM'), RSA_key.publickey().exportKey('PEM')


def get_key(address, key_type, mode, address_caller=None) :
	""" main function to get key from server storage

	"""
	if not mode.w3.isAddress(address) or address == '0x0000000000000000000000000000000000000000' :
		logging.error('incorrect address = %s', address)
		return None

	if key_type == 'P-256' :
		try :
			fp = open(mode.P256_path + address + '.P256', 'r')
		except :
			logging.error('P256 key not found in privatekey.py')
			return None
		key = jwk.JWK.from_pem(fp.read().encode(), password=mode.password.encode())
		return key.export_private()

	if key_type == 'Ed25519' :
		try :
			fp = open(mode.Ed25519_path + address + '.Ed25519', 'r')
		except :
			logging.error('Ed25519 key not found in privatekey.py')
			return None
		key = jwk.JWK.from_pem(fp.read().encode(), password=mode.password.encode())
		return key.export_private()

	if key_type == 'secp256k1' :
		try :
			fp = open(mode.keystore_path + address[2:] + '.json', 'r')
		except :
			logging.error('private key not found in privatekey.py')
			return None
		pvk = Account.decrypt(fp.read(), mode.password).hex()
		return helpers.ethereum_to_jwk(pvk, mode)

	if key_type == 'private_key' :
		try :
			fp = open(mode.keystore_path + address[2:] + '.json', 'r')
		except :
			logging.error('private key not found in privatekey.py')
			return None
		return Account.decrypt(fp.read(), mode.password).hex()

	# first we try to find a the new rsa file with .pem
	workspace_contract = ownersToContracts(address, mode)
	previous_filename = "./RSA_key/" + mode.BLOCKCHAIN + '/' + address + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
	new_filename = "./RSA_key/" + mode.BLOCKCHAIN + '/did:talao:' + mode.BLOCKCHAIN + ':'  + workspace_contract[2:] + ".pem"
	try :
		fp_new = open(new_filename,'r')
	except IOError :
		try :
			fp_prev = open(previous_filename,'r')
		except IOError :
			logging.warning('RSA key not found')
			rsa_key  = None
		else :
			rsa_key = fp_prev.read()
			os.rename(previous_filename, new_filename)
	else :
		rsa_key = fp_new.read()

	if key_type in ['rsa_key', 'RSA'] :
		return rsa_key

	# get data for AES keys from workspace contract
	contract = mode.w3.eth.contract(workspace_contract,abi = constante.workspace_ABI)
	data = contract.functions.identityInformation().call()

	if key_type in ['aes_key', 'private']  and rsa_key :
		key = RSA.importKey(rsa_key)
		cipher = PKCS1_OAEP.new(key)
		return cipher.decrypt(data[5])

	elif key_type in ['secret_key', 'secret'] and rsa_key :
		key = RSA.importKey(rsa_key)
		cipher = PKCS1_OAEP.new(key)
		return cipher.decrypt(data[6])

	elif key_type in ['aes_key', 'private'] and address_caller : # look for partnership data
		#recuperer les cle AES cryptée du user sur son partnership de l identité (caller)
		workspace_contract_caller = ownersToContracts(address_caller, mode)
		contract = mode.w3.eth.contract(workspace_contract_caller, abi = constante.workspace_ABI)
		private_key_caller = get_key(address_caller, 'private_key', mode)
		try :
			acct = Account.from_key(private_key_caller)
		except :
			return None
		mode.w3.eth.defaultAccount = acct.address
		try :
			partnership_data = contract.functions.getPartnership(workspace_contract).call()
		except :
			logging.error('problem with getPartnership')
			return None
		# one tests if the user is in partnershipg with identity (pending or authorized) and if his aes_key exist (status rejected ?)
		if partnership_data[1] in [1, 2] and partnership_data[4] != b'':
			aes_encrypted = partnership_data[4]
		else :
			# no partnership
			logging.info('no partnership with Identity')
			return None
		rsa_key_caller = get_key(address_caller, 'rsa_key', mode)
		key = RSA.importKey(rsa_key_caller)
		cipher = PKCS1_OAEP.new(key)
		logging.info('private key decrypted with partnership data = %s', cipher.decrypt(aes_encrypted))
		return cipher.decrypt(aes_encrypted)

	else :
		logging.error('no key decrypted %s', key_type)
		return None

