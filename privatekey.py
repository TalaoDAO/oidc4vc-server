import csv
from datetime import datetime
import sqlite3
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Protocol.KDF import PBKDF2

import constante



# Gloval variables for RSA algo
master_key = ""
salt = ""

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


def init_private_key_db(mode):
	path = mode.db_path
	conn = sqlite3.connect(path + 'private_key.db')
	cur = conn.cursor()
	cur.execute('create table key(created real, username text, address text, private_key text, workspace_contract text, email text, secret text, aes text)')
	conn.commit()
	cur.close()
	return


def setup(mode) :
	fname = mode.BLOCKCHAIN + "_Talao_Identity.csv"
	identity_file = open(fname, newline='')
	reader = csv.DictReader(identity_file)
	for row in reader :
		data = dict(row)
		data['address'] = row['ethereum_address']
		data['secret'] = row['password']
		print(data)
		add_identity(data, mode)
	identity_file.close()
	return


def add_identity(data, mode) :
	#data = {  'username' : username, 'address' : address, 'created' : str(datetime.today()), 'private_key' : private_key, 'workspace_contract' : workspace_contract, 'email' : email, 'secret' : secret, 'aes' : aes} 
	path = mode.db_path
	try :
		conn = sqlite3.connect(path + 'private_key.db')
	except :
		return False
	c = conn.cursor()
	c.execute("INSERT INTO key VALUES (:created, :username, :address, :private_key, :workspace_contract, :email, :secret, :aes)", data)
	conn.commit()
	conn.close()
	return True

def get_key(address,key_type, mode) :

	if key_type == 'private_key' :
		path = mode.db_path
		try :
			conn = sqlite3.connect(path + 'private_key.db')
		except :
			return None
		c = conn.cursor()
		data = {'address' : address}
		c.execute("SELECT private_key FROM key WHERE address = :address " , data)
		select=c.fetchone()
		conn.commit()
		conn.close()
		if select is None :
			return None
		return select[0]
	else :
		# deterministic RSA key https://stackoverflow.com/questions/20483504/making-rsa-keys-from-a-password-in-python
		global salt
		global master_key
		salt = get_key(address, 'private_key', mode)
		master_key = PBKDF2(mode.password, salt, count=10000)  # bigger count = better
		my_rand.counter = 0
		RSA_key = RSA.generate(2048, randfunc=my_rand)
		rsa_key = RSA_key.exportKey('PEM')
		"""
		from file :

		filename = "./RSA_key/" + mode.BLOCKCHAIN + '/' + str(address) + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
		try :
			fp = open(filename,"r")
			rsa_key = fp.read()
			print('rsa key du fichier = ', rsa_key)
			fp.close()
		except IOError :
			print('RSA file not found')
			return None
		"""
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

def get_email(address, mode) :
	path = mode.db_path

	try :
		conn = sqlite3.connect(path + 'private_key.db')
	except :
		return None
	c = conn.cursor()
	data = {'address' : address}
	c.execute("SELECT email FROM key WHERE address = :address " , data)
	select=c.fetchone()
	conn.commit()
	conn.close()
	if select is None :
		return None
	return select[0]


"""
if __name__ == '__main__':
	
	choice = input ('Do you confirm init setup Yes/No ?')
	if choice == 'yes' :
		mode = environment.currentMode()
		w3 = mode.w3
		init_private_key_db()
		setup(mode) 
		print(' setup Done')
"""	


