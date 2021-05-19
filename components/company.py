from datetime import datetime
import sqlite3
import logging
logging.basicConfig(level=logging.INFO)


class Campaign() :

	def __init__(self, company, mode) :
		self.company = company
		self.mode = mode

	def add(self, campaign, description) :
		path = self.mode.db_path
		conn = sqlite3.connect(path + self.company +'.db')
		c = conn.cursor()
		now = datetime.now()
		data = {'campaign_name' : campaign,
			'description' : description,
			'date' : datetime.timestamp(now)}
		try :
			c.execute("INSERT INTO campaign VALUES (:campaign_name, :description, :date )", data)
		except sqlite3.Error as er :
			logging.error('add campaign failed  %s', er)
			conn.close()
			return None
		conn.commit()
		conn.close()
		return True

	def delete(self, campaign) :
		path = self.mode.db_path
		conn = sqlite3.connect(path + self.company + '.db')
		c = conn.cursor()
		data = {'campaign_name' : campaign}
		try :
			c.execute("DELETE FROM campaign WHERE campaign_name = :campaign_name " , data)
			execution  = True
		except sqlite3.OperationalError :
			execution = False
		conn.commit()
		conn.close()
		return execution

	def get(self, campaign) :
		path = self.mode.db_path
		conn = sqlite3.connect(path + self.company + '.db')
		c = conn.cursor()
		data = {'campaign_name' : campaign}
		c.execute("SELECT description, date FROM campaign WHERE campaign_name = :campaign_name " , data)
		select=c.fetchone()
		conn.commit()
		conn.close()
		if not select :
			return None
		return select[0]

	def get_list(self) :
		path = self.mode.db_path
		conn = sqlite3.connect(path + self.company + '.db')
		c = conn.cursor()
		c.execute("SELECT campaign_name, description, date FROM campaign")
		select=c.fetchall()
		conn.commit()
		conn.close()
		if not select :
			return None
		campaign_list = list()
		for row in select :
			campaign_list.append({'campaign_name' : row[0], 'description' : row[1], 'date': row[2]})
		return campaign_list


class Employee() :

	def __init__(self, company, mode) :
		self.company = company
		self.mode = mode

	def add(self, employee_name, identity_name, role, referent, email, phone=None, password='identity') :
		path = self.mode.db_path
		conn = sqlite3.connect(path + self.company +'.db')
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

	def delete(self, employee_name) :
		path = self.mode.db_path
		conn = sqlite3.connect(path + self.company + '.db')
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

	def exist(self, employee_name) :
		path = self.mode.db_path
		conn = sqlite3.connect(path + self.company +'.db')
		c = conn.cursor()
		#now = datetime.now()
		data = {'employee_name' : employee_name}
		c.execute("SELECT identity_name FROM employee WHERE employee_name = :employee_name", data)
		select = c.fetchall()
		conn.close()
		if select == [] :
			return False
		else :
			return True

	def get_list(self, role, referent_name) :
		"""
		role is "admin" or "issuer" or "reviewer"
		"""
		if role not in ['issuer', 'admin', 'reviewer'] :
			logging.error('deprecated or malformed request')
			return None
		path = self.mode.db_path
		conn = sqlite3.connect(path + self.company + '.db')
		c = conn.cursor()
		data ={'role' : role, 'referent' : referent_name}
		try :
			if referent_name == 'all' :
				c.execute("SELECT employee_name, email, identity_name FROM employee where role = :role", data)
			else :
				c.execute("SELECT employee_name, email, identity_name FROM employee where role = :role and referent = :referent", data)
		except sqlite3.OperationalError :
			logging.error('database ' + self.company + ' not found')
			return []
		select = c.fetchall()
		employee_list = list()
		for row in select :
			employee_list.append({'username' : row[0]+'.' + self.company, 'email' : row[1], 'identity_name': row[2]})
		return employee_list

class Credential() :

    def __init__(self, company, mode) :
        self.company = company
        self.mode = mode

    def delete(self, id) :
	    path = self.mode.db_path
	    conn = sqlite3.connect(path + self.company + '.db')
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

    def add(self, talent_username, reviewer_username, issuer_username, status, id, credential, reference) :
	    """
	    credential is json unsigned (str)
	    status is draft/reviewed/signed
	    """
	    if status not in ['drafted', 'reviewed', 'signed'] :
		    logging.error('deprecated status')
		    return False
	    path = self.mode.db_path
	    conn = sqlite3.connect(path + self.company +'.db')
	    c = conn.cursor()
	    data = {
			'created' : datetime.now(),
			'user_name' : talent_username,
			'reviewer_name' : reviewer_username,
			'issuer_name' : issuer_username,
			'status' : status,
			'credential' : credential,
			'id' : id,
			'reference' : reference}
	    try :
		    c.execute("INSERT INTO credential VALUES (:created, :user_name, :reviewer_name, :issuer_name, :status, :credential, :id, :reference )", data)
		    conn.commit()
		    conn.close()
	    except :
		    conn.commit()
		    conn.close()
		    logging.error('add credential failed')
		    return False
	    return True

    def update(self, id, reviewer_username, issuer_username, status, credential) :
	    """
	    credential is json unsigned (str)
	    status is draft/reviewed/signed
	    """
	    if status not in ['drafted', 'reviewed', 'signed'] :
		    logging.error('deprecated status')
		    return False
	    path = self.mode.db_path
	    conn = sqlite3.connect(path + self.company +'.db')
	    c = conn.cursor()
	    data = {
			'reviewer_name' : reviewer_username,
			'issuer_name' : issuer_username,
			'status' : status,
			'credential' : credential,
			'id' : id}
	    try :
		    c.execute("UPDATE credential SET reviewer_name = :reviewer_name, issuer_name = :issuer_name, status = :status, credential = :credential  WHERE id = :id", data)
		    conn.commit()
		    conn.close()
	    except sqlite3.Error as er :
		    logging.error('update table credential failed %s', er)
		    conn.commit()
		    conn.close()
		    return False
	    return True


    def get(self, issuer_username, reviewer_username, status) :
	    path = self.mode.db_path
	    conn = sqlite3.connect(path + self.company +'.db')
	    c = conn.cursor()
	    data = {'issuer_name' : issuer_username,
			'reviewer_name' : reviewer_username,}
	    status = str(status)
	    try :
		    if issuer_username == 'all' and reviewer_username == 'all':
			    c.execute("SELECT created, user_name, reviewer_name, issuer_name, status, credential, id, reference  FROM credential WHERE status IN " + status, data)
		    elif reviewer_username == 'all' :
			    c.execute("SELECT created, user_name, reviewer_name, issuer_name, status, credential, id, reference FROM credential WHERE issuer_name = :issuer_name AND status IN " + status , data)
		    elif issuer_username == 'all' :
			    c.execute("SELECT created, user_name, reviewer_name, issuer_name, status, credential, id, reference FROM credential WHERE reviewer_name = :reviewer_name AND status IN " + status , data)
		    else :
			    c.execute("SELECT created, user_name, reviewer_name, issuer_name, status, credential, id, reference FROM credential WHERE reviewer_name = :reviewer_name AND issuer_name = :issuer_name AND status IN " + status , data)
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

    def get_by_id(self, id) :
	    path = self.mode.db_path
	    conn = sqlite3.connect(path + self.company +'.db')
	    c = conn.cursor()
	    data = {'id' : id,}
	    try :
		    c.execute("SELECT created, user_name, reviewer_name, issuer_name, status, credential, reference FROM credential WHERE id = :id", data)
	    except sqlite3.Error as er :
		    logging.error('get veriable credential by id failed  %s', er)
		    conn.close()
		    return None
	    select=c.fetchone()
	    conn.close()
	    if not select :
		    return None
	    return select

