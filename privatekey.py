import csv
import json
import os
from datetime import datetime
import sqlite3
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from eth_account import Account
from Crypto.Util.Padding import pad

import constante

# Gloval variables for RSA algo
master_key = ""
salt = ""

# deterministic RSA key https://stackoverflow.com/questions/20483504/making-rsa-keys-from-a-password-in-python
# deterministic rand function for RSA calculation
def my_rand(n):
    """ use of kluge: use PBKDF2 with count=1 and incrementing salt as deterministic PRNG """
    my_rand.counter += 1
    return PBKDF2(master_key, "my_rand:%d" % my_rand.counter, dkLen=n, count=1)


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


# to setup keystore first time from previous SQLIte database. To be removed later
def setup_keystore(mode) :
	path = mode.db_path
	try :
		conn = sqlite3.connect(path + 'private_key.db')
	except :
		return None
	c = conn.cursor()
	c.execute("SELECT private_key FROM key")
	select = c.fetchall()
	conn.close()
	if select is None :
		return None
	for private_key in [pvk[0] for pvk in select] :
		encrypted = Account.encrypt(private_key, mode.password)
		address = mode.w3.toChecksumAddress(encrypted['address'])
		with open(mode.keystore_path + address[2:] +".json", 'w') as f:
  			f.write(json.dumps(encrypted))
		f.close()
	return

def decrypt_data(workspace_contract_user, data, privacy, mode) :
	#recuperer la cle AES cryptée
	# on encrypt en mode CBC pour compatiblité avec librairie JS
	address_user = contractsToOwners(workspace_contract_user, mode)
	if privacy == 'public' :
		aes = mode.aes_public_key.encode('utf-8')
	elif privacy == 'private' :
		aes = get_key(address_user, 'aes_key', mode)
	elif privacy == 'secret' :
		aes == get_key(address_user, 'secret_key', mode)
	else :
		print ("Error : privacy error")
		return None
	if not aes :
		print('Warning : No RSA key on server')
		return None
	# decrypt data
	try:
		b64 = data #json.loads(json_input)
		json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
		jv = {k:b64decode(b64[k]) for k in json_k}
		cipher = AES.new(aes, AES.MODE_EAX, nonce=jv['nonce'])
		cipher.update(jv['header'])
		plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
		msg = json.loads(plaintext.decode('utf-8'))
	except :
		data = b64decode(data['ciphertext'])
		bytes = PBKDF2(aes, "salt".encode("utf-8"), 128, 128)
		iv = bytes[0:16]
		key = bytes[16:48]
		cipher = AES.new(key, AES.MODE_CBC, iv)
		plaintext = cipher.decrypt(data)
		plaintext = plaintext[:-plaintext[-1]].decode("utf-8")
		msg = json.loads(plaintext)
	return msg

def encrypt_data(identity_workspace_contract, data, privacy, mode, address_caller=None) :
	# parameter data is dict
	# return dict is dict
	#https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html
	# on enc rypte ne ode CBC a/c de 01/02/2021

	identity_address = contractsToOwners(identity_workspace_contract, mode)
	if privacy == 'public' :
		aes = mode.aes_public_key.encode('utf-8')
	elif privacy == 'private' :
		aes = get_key(identity_address, 'aes_key', mode, address_caller=address_caller)
	elif privacy == 'secret' :
		aes = get_key(identity_address, 'secret_key', mode)
	else :
		print('Error : incorrect privacy ')
		return None
	if not aes :
		print('Error : RSA key not found on server or cannot decrypt AES')
		return None
	"""
	# AES-EAX encryption
	try : 
		bytesdatajson = bytes(json.dumps(data), 'utf-8') # data(dict) -> json(str) -> bytes
		header = b"header"
		cipher = AES.new(aes, AES.MODE_EAX)
		cipher.update(header)
		ciphertext, tag = cipher.encrypt_and_digest(bytesdatajson)
	except :
		print('Error : decrypt problem dans private key . decrypt')
		return None
	json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
	json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, header, ciphertext, tag] ]
	dict_data = dict(zip(json_k, json_v))
	"""
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

# create a RSA key from Ethereum private key
def create_rsa_key(private_key, mode) :
	global salt
	global master_key
	salt = private_key
	master_key = PBKDF2(mode.password, salt, count=10000)
	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
	return  RSA_key, RSA_key.exportKey('PEM'), RSA_key.publickey().exportKey('PEM')


def get_key(address, key_type, mode, address_caller=None) :
	if not mode.w3.isAddress(address) or address == '0x0000000000000000000000000000000000000000' :
		return None

	if key_type == 'private_key' :
		try :
			fp = open(mode.keystore_path + address[2:] + '.json', "r")
		except :
			print('Error : private key not found in privatekey.py')
			return None
		encrypted = fp.read()
		fp.close()
		return Account.decrypt(encrypted, mode.password).hex()

	# first we try to find a the new rsa file with .pem
	workspace_contract = ownersToContracts(address, mode)
	previous_filename = "./RSA_key/" + mode.BLOCKCHAIN + '/' + address + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
	new_filename = "./RSA_key/" + mode.BLOCKCHAIN + '/did:talao:' + mode.BLOCKCHAIN + ':'  + workspace_contract[2:] + ".pem"
	try :
		fp_new = open(new_filename,"r")
	except IOError :
		print('Warning : new RSA file (.pem) not found on disk')
		try :
			fp_prev = open(previous_filename,"r")
		except IOError :
			print('Warning : old RSA file not found on disk ')
			print('Warning : no RSA key available on server')
			rsa_key  = None
		else :
			rsa_key = fp_prev.read()
			fp_prev.close()
			os.rename(previous_filename, new_filename)
			print('Warning : old RSA file renamed')
	else :
		rsa_key = fp_new.read()
		fp_new.close()
		print('Success : new RSA file found')

	if key_type == 'rsa_key' :
		return rsa_key
	
	contract = mode.w3.eth.contract(workspace_contract,abi = constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	aes_encrypted = data[5]
	secret_encrypted = data[6]

	if key_type == 'aes_key' and rsa_key :
		key = RSA.importKey(rsa_key)
		cipher = PKCS1_OAEP.new(key)
		return cipher.decrypt(aes_encrypted)

	elif key_type == 'aes_key' and address_caller : # look for partnership data
		print('address caller = ', address_caller)
		#recuperer les cle AES cryptée du user sur son partnership de l identité (caller)
		workspace_contract_caller = ownersToContracts(address_caller, mode)
		contract = mode.w3.eth.contract(workspace_contract_caller, abi = constante.workspace_ABI)
		private_key_caller = get_key(address_caller, 'private_key', mode)
		acct = Account.from_key(private_key_caller)
		mode.w3.eth.defaultAccount = acct.address
		partnership_data = contract.functions.getPartnership(workspace_contract).call()
		print('partnership data = ', partnership_data)
		# one tests if the user in partnershipg with identity (pending or authorized) and his aes_key exist (status rejected ?)
		if partnership_data[1] in [1, 2] and partnership_data[4] != b'':
			aes_encrypted = partnership_data[4]
		rsa_key_caller = get_key(address_caller, 'rsa_key', mode)
		key = RSA.importKey(rsa_key_caller)
		cipher = PKCS1_OAEP.new(key)
		print('cle private decrypté =', cipher.decrypt(aes_encrypted))
		return cipher.decrypt(aes_encrypted)

	elif key_type == 'secret_key' and rsa_key :
		key = RSA.importKey(rsa_key)
		cipher = PKCS1_OAEP.new(key)
		return cipher.decrypt(secret_encrypted)

	else :
		print('Warning : No key decrypted ', key_type)
		return None

