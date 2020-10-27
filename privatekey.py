import csv
import json
from datetime import datetime
import sqlite3
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from eth_account import Account
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
		print(encrypted)
		with open(mode.keystore_path + encrypted['address'].lower() +".json", 'w') as f:
  			f.write(json.dumps(encrypted))
		f.close()
	return

def encrypt_data(identity_workspace_contract, data, privacy, mode) :
	# parameter data is dict
	# return dict is dict
	#https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html

	identity_address = contractsToOwners(identity_workspace_contract, mode)
	if privacy == 'public' :
		aes = b'public_ipfs_key_' #16 bytes long
	if privacy == 'private' :
		aes = get_key(identity_address, 'aes_key', mode)
	if privacy == 'secret' :
		aes = get_key(identity_address, 'secret_key', mode)

	# AES EAX encryption
	bytesdatajson = bytes(json.dumps(data), 'utf-8') # data(dict) -> json(str) -> bytes
	header = b"header"
	cipher = AES.new(aes, AES.MODE_EAX)
	cipher.update(header)
	ciphertext, tag = cipher.encrypt_and_digest(bytesdatajson)
	json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
	json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, header, ciphertext, tag] ]
	dict_data = dict(zip(json_k, json_v))
	return dict_data

def add_private_key(private_key, mode) :
	encrypted = Account.encrypt(private_key, mode.password)
	try :
		f = open(mode.keystore_path + encrypted['address'].lower() +".json", 'w')
	except :
		return False
	f.write(json.dumps(encrypted))
	f.close()
	return True

def create_rsa_key(private_key, mode) :
	global salt
	global master_key
	salt = private_key
	master_key = PBKDF2(mode.password, salt, count=10000)  # bigger count = better
	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
	return  RSA_key, RSA_key.exportKey('PEM'), RSA_key.publickey().exportKey('PEM')

def get_key(address,key_type, mode) :
	if key_type == 'private_key' :
		try :
			fp = open(mode.keystore_path + address[2:].lower() + '.json', "r")
		except :
			print('private key not found in privatekey.py')
			return None
		encrypted = fp.read()
		fp.close()
		return Account.decrypt(encrypted, mode.password).hex()
	else :
		# first we try to find a rsa file
		filename = "./RSA_key/" + mode.BLOCKCHAIN + '/' + str(address) + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
		try :
			fp = open(filename,"r")
			rsa_key = fp.read()
			fp.close()
		except IOError :
		#rsa file does not exist on disk then we determine RSA Key
			print('RSA file not found on file, lets calculate RSA key by algo from prvate key')
			global salt
			global master_key
			salt = get_key(address, 'private_key', mode)
			master_key = PBKDF2(mode.password, salt, count=10000)  # bigger count = better
			my_rand.counter = 0
			RSA_key = RSA.generate(2048, randfunc=my_rand)
			rsa_key = RSA_key.exportKey('PEM')
	if key_type == 'rsa_key' :
		return rsa_key
	workspace_contract = ownersToContracts(address, mode)
	contract = mode.w3.eth.contract(workspace_contract,abi = constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	aes_encrypted = data[5]
	secret_encrypted = data[6]
	if key_type == 'aes_key' :
		key = RSA.importKey(rsa_key)
		cipher = PKCS1_OAEP.new(key)
		return cipher.decrypt(aes_encrypted)
	if key_type == 'secret_key' :
		key = RSA.importKey(rsa_key)
		cipher = PKCS1_OAEP.new(key)
		return cipher.decrypt(secret_encrypted)

