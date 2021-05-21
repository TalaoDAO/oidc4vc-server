from datetime import datetime
import sqlite3
import unidecode
import random
import constante
import json
import os
import logging
logging.basicConfig(level=logging.INFO)

"""
def add_table_employee(host_name, mode) :
	path = "/home/thierry/dbaws/"
	conn = sqlite3.connect(path + host_name + '.db')
	cur = conn.cursor()
	cur.execute('create table employee(employee_name text, identity_name text, email text, phone text, date real, password text, role text, referent text)')
	conn.commit()
	cur.close()
	return True


def alter_add_table_credential(database, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + database)
	cur = conn.cursor()
	cur.execute('create table credential(created real, user_name text, reviewer_name text, issuer_name text, status text, credential text, id text)')
	conn.commit()
	cur.close()
	return True
"""

def alter_resolver_table(mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	cur = conn.cursor()
	cur.execute('alter table resolver add column did text')
	cur.execute('alter table resolver add column personal text')
	conn.commit()
	cur.close()


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
	try :
		cur.execute('create table employee(employee_name text, identity_name text, email text, phone text, date real, password text, role text, referent text)')
		cur.execute('create table credential(created real, user_name text, reviewer_name text, issuer_name text, status text, credential text, id text, reference text)')
		cur.execute('create table campaign(campaign_name text, description text, date real)')
		conn.commit()
		cur.close()
		return True
	except :
		return False


def add_identity(identity_name, identity_workspace_contract, email, mode, phone='', password='identity', wallet='', did = '', personal='') :
	""" This is called once (first time), it creates a username for an identity and it creates an alias with same username as alias name. Publickey is created too"""
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	now = datetime.now()
	method = ''
	if password != 'identity' :
		password = mode.w3.keccak(text=password).hex()
	try :
		data = {'identity_name' : identity_name,
			 'identity_workspace_contract' : identity_workspace_contract,
			 'date' : datetime.timestamp(now),
			 'wallet' : wallet,
			 'method' : method,
			 'did' : json.dumps(did.split()),
			 'personal' : personal}
		c.execute("INSERT INTO resolver VALUES (:identity_name, :identity_workspace_contract, :date, :wallet, :method, :did, :personal)", data)
		data = {'alias_name' : identity_name,
			 'identity_name' : identity_name,
			 'email' : email,
			 'date' : datetime.timestamp(now),
			 'phone' : phone,
			 'password' : password} 
		c.execute("INSERT INTO alias VALUES (:alias_name, :identity_name, :email, :date, :phone, :password )", data)
		address = _contractsToOwners(identity_workspace_contract, mode)
		key = mode.w3.solidityKeccak(['address'], [address]).hex()
		data = {'address' : address, 'key' : key}
		c.execute("INSERT INTO publickey VALUES (:address, :key)", data)
	except :
		conn.close()
		return False
	conn.commit()
	conn.close()
	return True


def add_did(workspace_contract, did, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = { "workspace_contract" : workspace_contract}
	c.execute("SELECT did FROM resolver WHERE identity_workspace_contract = :workspace_contract", data)
	try :
		did_list = json.loads(c.fetchone()[0])
		if not did in did_list :
			did_list.append(did)
		else :
			logging.warning('did already in did list')
	except :
		did_list = list()
		did_list.append(did)
	did_list_str = json.dumps(did_list)
	data = { "workspace_contract" : workspace_contract, 'did' : did_list_str}
	c.execute("update resolver set did = :did where identity_workspace_contract = :workspace_contract", data )
	conn.commit()
	conn.close()


def get_did_list(workspace_contract,mode) :
	"""
	return list of dict
	"""
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = { "workspace_contract" : workspace_contract}
	c.execute("SELECT did FROM resolver WHERE identity_workspace_contract = :workspace_contract", data)
	did = c.fetchone()
	conn.close()
	try :
		return json.loads(did[0])
	except :
		return[]


def get_method(workspace_contract, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'workspace_contract' : workspace_contract}
	c.execute("SELECT method FROM resolver WHERE identity_workspace_contract = :workspace_contract " , data)
	select=c.fetchone()
	conn.close()
	if not select :
		return None
	return select[0]


def get_did(workspace_contract, mode) :
	"""
	return the current did as a str
	"""
	method = get_method(workspace_contract, mode)
	if not method :
		return None
	did_list = get_did_list(workspace_contract,mode)
	if not did_list :
		return None
	for did in did_list :
		if method == did.split(':')[1] :
			return did
	return None


def get_workspace_contract_from_did(did, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = { 'did' : '%"' + did + '"%'}
	c.execute('SELECT identity_workspace_contract FROM resolver WHERE did LIKE  :did ', data)
	wc = c.fetchone()
	conn.close()
	if not wc :
		return None
	return wc[0]


def add_publickey(address, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	key = mode.w3.solidityKeccak(['address'], [address]).hex()
	data = {'address' : address, 'key' : key}
	c.execute("INSERT INTO publickey VALUES (:address, :key)", data)
	conn.commit()
	conn.close()


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


def add_alias(alias_name, identity_name, email, mode, phone=None, password='identity') :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	now = datetime.now()
	data = {'alias_name' : alias_name, 'identity_name' : identity_name, 'email' : email, 'date' : datetime.timestamp(now), 'phone' : phone, 'password' : password}
	c.execute("INSERT INTO alias VALUES (:alias_name, :identity_name, :email, :date, :phone, :password )", data)
	conn.commit()
	conn.close()


def remove_alias(alias_name, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'alias_name' : alias_name}
	c.execute("DELETE FROM alias WHERE alias_name = :alias_name " , data)
	conn.commit()
	conn.close()


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
			conn.close()
			return None

		(identity_name, alias_email, phone, password) = select
		data ={'identity_name' : identity_name}
		c.execute("SELECT identity_workspace_contract FROM resolver WHERE identity_name = :identity_name " , data)
		select = c.fetchone()
		if select is None :
			logging.warning('alias ' + username + ' has no identity in resolver')
			conn.close()
			return None
		identity_workspace_contract = select[0]
		return identity_workspace_contract, None, alias_email, phone, password, None, None
	else :
		conn = sqlite3.connect(path + host_name + '.db')
		c = conn.cursor()
		data ={'employee_name' : employee_name}
		try :
			c.execute("SELECT identity_name, email, phone, password, role, referent FROM employee WHERE employee_name = :employee_name " , data)
		except sqlite3.OperationalError :
			logging.error('database ' + host_name + ' does not exist')
			conn.close()
			return None
		select = c.fetchone()
		if select is None :
			logging.error('employee name : '+ employee_name + ' does not exist in '+ host_name)
			conn.close()
			return None
		(identity_name, employee_email, phone, password, role, referent) = select
		conn.close()
		conn = sqlite3.connect(path + 'nameservice.db')
		c = conn.cursor()
		data ={'host_name' : host_name}
		c.execute("SELECT identity_workspace_contract FROM resolver WHERE identity_name = :host_name " , data)
		select = c.fetchone()
		if select is None :
			conn.close()
			logging.error('host not found in resolver table')
			return None
		host_workspace_contract = select[0]
		data ={'identity_name' : identity_name}
		c.execute("SELECT identity_workspace_contract FROM resolver WHERE identity_name = :identity_name " , data)
		identity_workspace_contract = c.fetchone()[0]
		conn.close()
		return identity_workspace_contract, host_workspace_contract, employee_email, phone, password, role, referent


def get_username_from_resolver(workspace_contract, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'identity_workspace_contract' : workspace_contract}
	c.execute("SELECT identity_name FROM resolver WHERE identity_workspace_contract = :identity_workspace_contract " , data)
	select=c.fetchone()
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
	conn.close()
	if not select :
		return None
	return select[0]


def get_method(workspace_contract, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'workspace_contract' : workspace_contract}
	c.execute("SELECT method FROM resolver WHERE identity_workspace_contract = :workspace_contract " , data)
	select=c.fetchone()
	conn.close()
	if not select :
		return None
	return select[0]


def get_personal(workspace_contract, mode) :
	"""
	return json 
	"""
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'workspace_contract' : workspace_contract}
	c.execute("SELECT personal FROM resolver WHERE identity_workspace_contract = :workspace_contract " , data)
	select=c.fetchone()
	conn.close()
	if not select :
		return None
	return select[0]


def update_method(workspace_contract, method, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	cur = conn.cursor()
	data = { 'method' : method, 'workspace_contract' : workspace_contract}
	cur.execute("update resolver set method = :method where identity_workspace_contract = :workspace_contract", data )
	conn.commit()
	conn.close()


def update_personal(workspace_contract, personal, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	cur = conn.cursor()
	data = { 'personal' : personal, 'workspace_contract' : workspace_contract}
	cur.execute("update resolver set personal = :personal where identity_workspace_contract = :workspace_contract", data )
	conn.commit()
	conn.close()


def get_workspace_contract_from_wallet(wallet, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	c = conn.cursor()
	data = {'wallet' : wallet}
	c.execute("SELECT identity_workspace_contract FROM resolver WHERE wallet = :wallet " , data)
	select=c.fetchone()
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
	conn.close()
	if select is None :
		return None
	return select[0]


def get_data_from_publickey(publickey, mode) :
	""" username comes from resolver database"""
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
	conn.close()
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
	conn.close()
	for row in select :
		username_list.append(row[0])
	return username_list


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
	elif len(username_split) == 2 :
		conn = sqlite3.connect(path + username_split[1] + '.db')
		cur = conn.cursor()
		data = { 'phone' : phone, 'employee_name' : username_split[0]}
		cur.execute("UPDATE employee set phone = :phone WHERE employee_name = :employee_name", data )
	else :
		return False
	conn.commit()
	conn.close()
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
	elif len(username_split) == 2 :
		conn = sqlite3.connect(path + username_split[1] + '.db')
		cur = conn.cursor()
		data = { 'password' : password, 'employee_name' : username_split[0]}
		cur.execute("UPDATE employee set password = :password WHERE employee_name = :employee_name", data )
	else :
		return False
	conn.commit()
	conn.close()
	return True


def update_wallet(workspace_contract, wallet, mode) :
	path = mode.db_path
	conn = sqlite3.connect(path + 'nameservice.db')
	cur = conn.cursor()
	data = { 'wallet' : wallet, 'workspace_contract' : workspace_contract}
	cur.execute("update resolver set wallet = :wallet where identity_workspace_contract = :workspace_contract", data )
	conn.commit()
	cur.close()


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
	if not data :
		return False
	if password == 'identity' :
		return password == data.get('hash_password')
	return mode.w3.keccak(text=password).hex() == data.get('hash_password')


def has_phone(username, mode) :
	if not username :
		return False
	data = get_data_from_username(username, mode)
	if not data or not data['phone'] :
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
	conn.close()
	return credentials

