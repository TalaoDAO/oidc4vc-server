
from datetime import datetime
import sqlite3
import constante
import csv

	
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
		add_identity(data)
	
	identity_file.close()
	
	return			
	

def add_identity(data, mode) :
	#data = {  'username' : username, 'address' : address, 'created' : str(datetime.today()), 'private_key' : private_key, 'workspace_contract' : workspace_contract, 'email' : email, 'secret' : secret, 'aes' : aes} 
	path = mode.db_path

	try :
		conn = sqlite3.connect(path + 'private_key.db')
	except :
		return None
	c = conn.cursor()
	c.execute("INSERT INTO key VALUES (:created, :username, :address, :private_key, :workspace_contract, :email, :secret, :aes)", data)
	conn.commit()
	conn.close()
	return True
	
	
def get_key(address,key_type, mode) :	
	path = mode.db_path

	try :
		conn = sqlite3.connect(path + 'private_key.db')
	except :
		return None
	c = conn.cursor()
	data = {'address' : address}
	if key_type == 'private_key' : 
		c.execute("SELECT private_key FROM key WHERE address = :address " , data)
	elif key_type == 'aes' :
		c.execute("SELECT aes FROM key WHERE address = :address " , data)
	elif key_type == 'secret' :
		c.execute("SELECT secret FROM key WHERE address = :address " , data)
	else :
		print('erreur de key')
		return None	
	select=c.fetchone()
	conn.commit()
	conn.close()
	if select is None :
		return None
	return select[0]	

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


