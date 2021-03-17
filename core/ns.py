from datetime import datetime
import sqlite3
import unidecode
import random
import json
import constante
import os
import secrets
import logging
logging.basicConfig(level=logging.INFO)


def add_table_employee(host_name, mode) :
	""" This function is only used in createcompany """
	path = mode.db_path
	conn = sqlite3.connect(path + host_name + '.db')
	cur = conn.cursor()
	cur.execute('create table employee(employee_name text, identity_name text, email text, phone text, date real, password text, role text, referent text)')
	conn.commit()
	cur.close()
	return True

def alter_add_table_credential(database, mode) :
	path = mode.db_path
	""" This function is only used to update """
	conn = sqlite3.connect(path + database)
	cur = conn.cursor()
	cur.execute('create table credential(created real, user_name text, reviewer_name text, issuer_name text, status text, credential text, id text)')
	conn.commit()
	cur.close()
	return True


def alter_credential_table(database, mode) :
	path = mode.db_path
	""" This function is only used to update """
	conn = sqlite3.connect(path + database)
	cur = conn.cursor()
	cur.execute('alter table credential add column id text')
	conn.commit()
	cur.close()
	return True

# update pour la mise en place du champ wallet dans resolver
def alter_add_wallet_field(mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	cur = conn.cursor()
	cur.execute('alter table resolver add column wallet text')
	conn.commit()
	cur.close()
	return True


def _contractsToOwners(workspace_contract, mode) :
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	return address

def _ownersToContracts(address, mode) :
	contract = mode.w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	workspace_address = contract.functions.ownersToContracts(address).call()
	return workspace_address

def build_username(firstname, lastname,mode) :
	""" to get an unique username """
	_firstname = firstname.lower()
	_lastname = lastname.lower()
	_username = unidecode.unidecode(_firstname) + unidecode.unidecode(_lastname)
	username = _username.replace(" ", "")
	if username_exist(username, mode)  :
		username = username + str(random.randint(1, 100))
	return username

def init_host(host_name, mode) :
	""" This function is only used in createcompany """
	path = mode.db_path
	conn = sqlite3.connect(path + host_name + '.db')
	cur = conn.cursor()
	cur.execute('create table employee(employee_name text, identity_name text, email text, phone text, date real, password text, role text, referent text)')
	cur.execute('create table credential(created real, user_name text, reviewer_name text, issuer_name text, status text, credential text, id text)')
	conn.commit()
	cur.close()
	return True

def add_identity(identity_name, identity_workspace_contract, email, mode, phone=None, password='identity', wallet='') :
	""" This is called once (first time), it creates a username for an identity and it creates an alias with same username as alias name. Publickey is created too"""
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	now = datetime.now()

	data = {'identity_name' : identity_name, 'identity_workspace_contract' : identity_workspace_contract, 'date' : datetime.timestamp(now), 'wallet' : wallet} 
	c.execute("INSERT INTO resolver VALUES (:identity_name, :identity_workspace_contract, :date, :wallet)", data)

	data = {'alias_name' : identity_name, 'identity_name' : identity_name, 'email' : email, 'date' : datetime.timestamp(now), 'phone' : phone, 'password' : password} 
	c.execute("INSERT INTO alias VALUES (:alias_name, :identity_name, :email, :date, :phone, :password )", data)

	address = _contractsToOwners(identity_workspace_contract, mode)
	key = mode.w3.solidityKeccak(['address'], [address]).hex()
	data = {'address' : address, 'key' : key}
	c.execute("INSERT INTO publickey VALUES (:address, :key)", data)

	conn.commit()
	conn.close()
	return True

def add_publickey(address, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	key = mode.w3.solidityKeccak(['address'], [address]).hex()
	data = {'address' : address, 'key' : key}
	c.execute("INSERT INTO publickey VALUES (:address, :key)", data)
	conn.commit()
	conn.close()
	return True

def delete_identity(identity_name, mode, category=1001) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	# remove database for company
	if category == 2001 :
		os.remove(path + identity_name + '.db')
	data = {'identity_name' : identity_name}
	# we do not remove the publicHex key
	c.execute("DELETE FROM resolver WHERE identity_name = :identity_name", data)
	c.execute("DELETE FROM alias WHERE alias_name = :identity_name", data)
	conn.commit()
	conn.close()
	return True

def add_alias(alias_name, identity_name, email, mode, phone=None, password='identity') :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	now = datetime.now()
	data = {'alias_name' : alias_name, 'identity_name' : identity_name, 'email' : email, 'date' : datetime.timestamp(now), 'phone' : phone, 'password' : password}
	c.execute("INSERT INTO alias VALUES (:alias_name, :identity_name, :email, :date, :phone, :password )", data)
	conn.commit()
	conn.close()
	return True

def remove_alias(alias_name, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'alias_name' : alias_name}
	try :
		c.execute("DELETE FROM alias WHERE alias_name = :alias_name " , data)
		execution  = True
	except sqlite3.OperationalError :
		execution = False
	conn.commit()
	conn.close()
	return execution


def delete_verifiable_credential(id, host, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + host + '.db')
	c = conn.cursor()
	data = {'id' : id}
	try :
		c.execute("DELETE FROM credential WHERE id = :id " , data)
	except sqlite3.OperationalError as er :
		logging.error('delete credential failed %s', er)
		conn.commit()
		conn.close()
		return False
	conn.commit()
	conn.close()
	return True

def add_verifiable_credential(host_name, talent_username, reviewer_username, issuer_username, status, id, credential, mode) :
	"""
	credential is json unsigned (str)
	status is draft/reviewed/signed
	"""
	if status not in ['drafted', 'reviewed', 'signed'] :
		logging.error('deprecated status')
	path = mode.db_path
	conn = sqlite3.connect(path + host_name +'.db')
	c = conn.cursor()
	data = {
			'created' : datetime.now(),
			'user_name' : talent_username,
			'reviewer_name' : reviewer_username,
			'issuer_name' : issuer_username,
			'status' : status,
			'credential' : credential,
			'id' : id}
	try :
		c.execute("INSERT INTO credential VALUES (:created, :user_name, :reviewer_name, :issuer_name, :status, :credential, :id )", data)
		conn.commit()
		conn.close()
	except :
		conn.commit()
		conn.close()
		return False
	return True

def update_verifiable_credential(id, host_name, reviewer_username, issuer_username, status, credential, mode) :
	"""
	credential is json unsigned (str)
	status is draft/reviewed/signed
	"""
	if status not in ['drafted', 'reviewed', 'signed'] :
		logging.error('deprecated status')
	path = mode.db_path
	conn = sqlite3.connect(path + host_name +'.db')
	c = conn.cursor()
	data = {
			'reviewer_name' : reviewer_username,
			'issuer_name' : issuer_username,
			'status' : status,
			'credential' : credential,
			'id' : id}
	try :
		c.execute("UPDATE credential SET reviewer_name = :reviewer_name, issuer_name = :issuer_name, status = :status, credential = :credential  WHERE id = :id", data)
		logging.error('table credential updated')
		conn.commit()
		conn.close()
	except sqlite3.Error as er :
		logging.error('update table credential failed %s', er)
		conn.commit()
		conn.close()
		return False
	return True


def get_verifiable_credential(host, issuer_username, reviewer_username, status, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + host +'.db')
	c = conn.cursor()
	data = {'issuer_name' : issuer_username,
			'reviewer_name' : reviewer_username,}
	status = str(status)
	try :
		if issuer_username == 'all' and reviewer_username == 'all':
			c.execute("SELECT created, user_name, reviewer_name, issuer_name, status, credential, id  FROM credential WHERE status IN " + status, data)
		elif reviewer_username == 'all' :
			c.execute("SELECT created, user_name, reviewer_name, issuer_name, status, credential, id FROM credential WHERE issuer_name = :issuer_name AND status IN " + status , data)
		elif issuer_username == 'all' :
			c.execute("SELECT created, user_name, reviewer_name, issuer_name, status, credential, id FROM credential WHERE reviewer_name = :reviewer_name AND status IN " + status , data)
		else :
			c.execute("SELECT created, user_name, reviewer_name, issuer_name, status, credential, id FROM credential WHERE reviewer_name = :reviewer_name AND issuer_name = :issuer_name AND status IN " + status , data)
	except sqlite3.Error as er :
		logging.error('get veriable credential failed %s', er)
		conn.commit()
		conn.close()
		return None
	select=c.fetchall()
	conn.close()
	if not select :
		return None
	return select

def get_verifiable_credential_by_id(host, id, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + host +'.db')
	c = conn.cursor()
	data = {'id' : id,}
	try :
		c.execute("SELECT created, user_name, reviewer_name, issuer_name, status, credential FROM credential WHERE id = :id", data)
	except sqlite3.Error as er :
		logging.error('get veriable credential by id failed  %s', er)
		conn.close()
		return None
	select=c.fetchone()
	conn.close()
	if not select :
		return None
	return select


def add_employee(employee_name, identity_name, role, referent, host_name, email, mode, phone=None, password='identity') :
	path = mode.db_path
	conn = sqlite3.connect(path + host_name +'.db')
	c = conn.cursor()
	now = datetime.now()
	data = {'employee_name' : employee_name,
			'identity_name' : identity_name,
			'email' : email,
			'date' : datetime.timestamp(now),
			'phone' : phone,
			'password' : password,
			'role' : role,
			'referent' : referent}
	try :
		c.execute("INSERT INTO employee VALUES (:employee_name, :identity_name, :email, :phone, :date, :password, :role, :referent )", data)
	except sqlite3.Error as er :
		logging.error('add employee failed  %s', er)
		conn.close()
		return None
	conn.commit()
	conn.close()
	return True


def does_manager_exist(employee_name, host_name, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + host_name +'.db')
	c = conn.cursor()
	#now = datetime.now()
	data = {'employee_name' : employee_name,
			'role' : "issuer"}
	c.execute("SELECT identity_name FROM employee WHERE employee_name = :employee_name AND role = :role " , data)
	select = c.fetchall()
	conn.close()
	if select == [] :
		return False
	else :
		return True

def identity_list(mode) :
	""" Return list of username """
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	c.execute("SELECT alias_name FROM alias")
	select = c.fetchall()
	conn.close()
	my_list = [item[0] for item in select if item[0] != '' and item[0] != 'relay']
	my_list.sort()
	return my_list

def remove_manager(employee_name, host_name, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + host_name + '.db')
	c = conn.cursor()
	data = {'employee_name' : employee_name}
	try :
		c.execute("DELETE FROM employee WHERE employee_name = :employee_name " , data)
		execution  = True
	except sqlite3.OperationalError :
		execution = False
	conn.commit()
	conn.close()
	return execution


def _get_data(username, mode) :
	if not username :
		return None
	""" 
	return data from SQL database depending of type of user (manager or not) 
	for a person role = referent = None
	"""
	path = mode.db_path
	employee_name,s,host_name = username.rpartition('.')
	# it is not an employee
	if not employee_name  :
		conn = sqlite3.connect(path + 'nameservice.db')
		c = conn.cursor()
		data ={'username' : username}
		c.execute("SELECT identity_name, email, phone, password FROM alias WHERE alias_name = :username " , data)
		select = c.fetchone()
		if select is None :
			conn.commit()
			conn.close()
			logging.warning( username + ' does not exist in nameservice db')
			return None

		(identity_name, alias_email, phone, password) = select
		data ={'identity_name' : identity_name}
		c.execute("SELECT identity_workspace_contract FROM resolver WHERE identity_name = :identity_name " , data)
		select = c.fetchone()
		if select is None :
			conn.commit()
			conn.close()
			logging.warning('alias ' + username + ' has no identity in resolver')
			return None
		identity_workspace_contract = select[0]
		conn.commit()
		conn.close()
		return identity_workspace_contract, None, alias_email, phone, password, None, None
	else :
		conn = sqlite3.connect(path + host_name + '.db')
		c = conn.cursor()
		data ={'employee_name' : employee_name}
		try :
			c.execute("SELECT identity_name, email, phone, password, role, referent FROM employee WHERE employee_name = :employee_name " , data)
		except sqlite3.OperationalError :
			logging.error('database ' + host_name + ' does not exist')
			return None
		select = c.fetchone()
		if select is None :
			conn.commit()
			conn.close()
			logging.error('employee name : '+ employee_name + ' does not exist in '+ host_name)
			return None
		(identity_name, employee_email, phone, password, role, referent) = select
		conn.commit()
		conn.close()
		conn = sqlite3.connect(path + 'nameservice.db')
		c = conn.cursor()
		data ={'host_name' : host_name}
		c.execute("SELECT identity_workspace_contract FROM resolver WHERE identity_name = :host_name " , data)
		select = c.fetchone()
		if select is None :
			conn.commit()
			conn.close()
			logging.error('le host n existe pas dans le resolver')
			return None
		host_workspace_contract = select[0]
		data ={'identity_name' : identity_name}
		c.execute("SELECT identity_workspace_contract FROM resolver WHERE identity_name = :identity_name " , data)
		identity_workspace_contract = c.fetchone()[0]
		conn.commit()
		conn.close()
		return identity_workspace_contract, host_workspace_contract, employee_email, phone, password, role, referent

def get_username_from_resolver(workspace_contract, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'identity_workspace_contract' : workspace_contract}
	c.execute("SELECT identity_name FROM resolver WHERE identity_workspace_contract = :identity_workspace_contract " , data)
	select=c.fetchone()
	conn.commit()
	conn.close()
	if select is None :
		return None
	return select[0]

def get_username_from_wallet(wallet, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'wallet' : wallet}
	c.execute("SELECT identity_name FROM resolver WHERE wallet = :wallet " , data)
	select=c.fetchone()
	conn.commit()
	conn.close()
	if not select :
		return None
	return select[0]

def get_workspace_contract_from_wallet(wallet, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'wallet' : wallet}
	c.execute("SELECT identity_workspace_contract FROM resolver WHERE wallet = :wallet " , data)
	select=c.fetchone()
	conn.commit()
	conn.close()
	if not select :
		return None
	return select[0]

def get_wallet_from_workspace_contract(workspace_contract, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'workspace_contract' : workspace_contract}
	c.execute("SELECT wallet FROM resolver WHERE identity_workspace_contract = :workspace_contract " , data)
	select=c.fetchone()
	conn.commit()
	conn.close()
	if not select or not select[0]:
		return None
	return select[0]

def get_address_from_publickey(publickey, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'key' : publickey}
	c.execute("SELECT address FROM publickey WHERE key = :key " , data)
	select=c.fetchone()
	conn.commit()
	conn.close()
	if select is None :
		return None
	return select[0]

def get_data_from_publickey(publickey, mode) :
	""" username comes from resolver database"""
	#path = mode.db_path
	address = get_address_from_publickey(publickey, mode)
	if address is None :
		return None
	workspace_contract = _ownersToContracts(address,mode)
	username = get_username_from_resolver(workspace_contract, mode)
	if username is None :
		return None
	return {'address' : address,
			'workspace_contract' : workspace_contract,
			'username' : username}


def _get_data_for_login(username, mode) :
	if not username :
		return None
	""" ne pas utiliser en externe """
	call = _get_data(username, mode)
	if call is None :
		return None
	identity, host, email, phone, password, role, referent = call
	if host is None :
		return identity, email, phone, password, None, None, identity
	else :
		return host, email, phone, password, role, referent, identity

def username_exist(username, mode) :
	if not username :
		return False
	return  False if not _get_data(username,mode) else True

def get_data_from_username(username, mode) :
	""" It is almost the same as get_data_for_login but with dict as return """
	if not username :
		return dict()
	call = _get_data_for_login(username, mode)
	if call is None :
		return dict()
	workspace_contract, email, phone, password, role, referent, identity_workspace_contract = call
	address = _contractsToOwners(workspace_contract,mode)
	return {'email' : email,
			'address' : address,
			'workspace_contract' : workspace_contract,
			'identity_workspace_contract' : identity_workspace_contract,
			'username' : username,
			'phone' : phone,
			'hash_password' : password,
			'did' : 'did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract[2:],
			'role' : role,
			'referent' : referent
			}

def get_alias_list(workspace_contract, mode) :
	path = mode.db_path
	call = get_username_from_resolver(workspace_contract, mode)
	if call is None :
		return []
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	identity_name = call
	data ={'identity_name' : identity_name}
	c.execute("SELECT alias_name, email FROM alias WHERE identity_name = :identity_name " , data)
	select = c.fetchall()
	alias = list()
	for row in select :
		alias.append({'username' : row[0], 'email' : row[1]})
	return alias

def get_username_list_from_email(email, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data ={'email' : email}
	c.execute("SELECT identity_name FROM alias WHERE email = :email" , data)
	select = c.fetchall()
	username_list = list()
	for row in select :
		username_list.append(row[0])
	return username_list

def get_employee_list(host, role, referent_name, mode) :
	"""
	role is "admin" or "issuer" or "reviewer" 
	"""
	if role not in ['issuer', 'admin', 'reviewer'] :
		logging.error('deprecated or malformed request')
		return None
	path = mode.db_path
	conn = sqlite3.connect(path + host + '.db')
	c = conn.cursor()
	data ={'role' : role, 'referent' : referent_name}
	try :
		if referent_name == 'all' :
			c.execute("SELECT employee_name, email, identity_name FROM employee where role = :role", data)
		else :
			c.execute("SELECT employee_name, email, identity_name FROM employee where role = :role and referent = :referent", data)
	except sqlite3.OperationalError :
		logging.error('database ' + host + ' not found')
		return []
	select = c.fetchall()
	employee_list = list()
	for row in select :
		employee_list.append({'username' : row[0]+'.' + host, 'email' : row[1], 'identity_name': row[2]})
	return employee_list


def update_phone(username, phone, mode) :
	if not username :
		return False
	path = mode.db_path
	username_split = username.split('.')
	if len(username_split) == 1 :
		conn = sqlite3.connect(path + 'nameservice.db')
		cur = conn.cursor()
		data = { 'phone' : phone, 'alias_name' : username}
		cur.execute("UPDATE alias set phone = :phone WHERE alias_name = :alias_name", data )
		conn.commit()
		cur.close()
	if len(username_split) == 2 :
		conn = sqlite3.connect(path + username_split[1] + '.db')
		cur = conn.cursor()
		data = { 'phone' : phone, 'employee_name' : username_split[0]}
		cur.execute("UPDATE employee set phone = :phone WHERE employee_name = :employee_name", data )
		conn.commit()
		cur.close()
	else :
		return False
	return True

def update_password(username, new_password, mode) :
	if not username :
		return False
	password = mode.w3.keccak(text=new_password).hex()
	path = mode.db_path
	username_split = username.split('.')
	if len(username_split) == 1 :
		conn = sqlite3.connect(path + 'nameservice.db')
		cur = conn.cursor()
		data = { 'password' : password, 'alias_name' : username}
		cur.execute("UPDATE alias set password = :password WHERE alias_name = :alias_name", data )
		conn.commit()
		cur.close()
	if len(username_split) == 2 :
		conn = sqlite3.connect(path + username_split[1] + '.db')
		cur = conn.cursor()
		data = { 'password' : password, 'employee_name' : username_split[0]}
		cur.execute("UPDATE employee set password = :password WHERE employee_name = :employee_name", data )
		conn.commit()
		cur.close()
	else :
		return False
	return True


def update_wallet(workspace_contract, wallet, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	cur = conn.cursor()
	data = { 'wallet' : wallet, 'workspace_contract' : workspace_contract}
	print('data = ', data)
	try :
		cur.execute("update resolver set wallet = :wallet where identity_workspace_contract = :workspace_contract", data )
	except :
		return False
	conn.commit()
	cur.close()
	return True

def must_renew_password(username, mode) :
	if not username :
		return False
	data = get_data_from_username(username, mode)
	if data is None :
		return False
	return 'identity' == data.get('hash_password')

def check_password(username, password, mode) :
	if not username :
		return False
	data = get_data_from_username(username, mode)
	if data is None :
		return False
	# Backdoor en test
	if password == 'talaotalao' and mode.test :
		return True
	if password == 'identity' :
		return password == data.get('hash_password')
	return mode.w3.keccak(text=password).hex() == data.get('hash_password')

def has_phone(username, mode) :
	if not username :
		return False
	data = get_data_from_username(username, mode)
	if data is None or data['phone'] is None or data['phone'] == "" :
		return False
	else :
		return True

def get_credentials(username, mode) :
	if not username :
		return None
	path = mode.db_path
	conn = sqlite3.connect(path + 'db.sqlite')
	c = conn.cursor()
	c.execute("SELECT client_id, client_secret,client_metadata FROM oauth2_client ")
	select = c.fetchall()
	credentials = list()
	for row in select  :
		if row[2] :
			metadata = json.loads(row[2])
			if metadata['client_name'] == username :
				credentials.append({'client_id' : row[0],
				 'client_secret' : row[1],
				 'client_uri' : metadata['client_uri'],
				 'redirect_uris' : metadata['redirect_uris'],
				 'grant_types' : metadata['grant_types'],
				 'scope' : metadata['scope'] })
	return credentials

"""

if __name__ == '__main__':

	import environment
	# environment setup
	mode = environment.currentMode()
	w3 = mode.w3

	#setup()

"""
