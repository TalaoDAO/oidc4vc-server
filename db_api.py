import json
import uuid
import logging
import sqlite3
import random 
import string
from op_constante import issuer_client_data_pattern, verifier_client_data_pattern
logging.basicConfig(level=logging.INFO)

def create_verifier(mode) :
    return create('verifier.db', mode)
def update_verifier(client_id, data) :
    return update(client_id, data, 'verifier.db')
def read_verifier(client_id) :
    return read(client_id, 'verifier.db')
def list_verifier() :
    return list('verifier.db')
def delete_verifier(client_id) :
    return delete(client_id, 'verifier.db')
def create_issuer(mode) :
    return create('issuer.db', mode)
def update_issuer(client_id, data) :
    return update(client_id, data, 'issuer.db')
def read_issuer(client_id) :
    return read(client_id, 'issuer.db')
def list_issuer() :
    return list('issuer.db')
def delete_issuer(client_id) :
    return delete(client_id, 'issuer.db')


def create(db, mode) :
    letters = string.ascii_lowercase
    if db == 'issuer.db' :
        data = issuer_client_data_pattern     
        data['client_id'] = ''.join(random.choice(letters) for i in range(10))
        data['issuer_landing_page'] = mode.server + 'sandbox/op/issuer/' + data['client_id']
    else :
        data = verifier_client_data_pattern
        data['client_id'] = ''.join(random.choice(letters) for i in range(10))
        data['client_secret'] = str(uuid.uuid1())
    conn = sqlite3.connect(db)
    c = conn.cursor()
    db_data = { "client_id" : data['client_id'] ,"data" :json.dumps(data)}
    try :
        c.execute("INSERT INTO client VALUES (:client_id, :data)", db_data)
    except :
        logging.error('DB error')
        return None
    conn.commit()
    conn.close()
    return data['client_id']


def update(client_id, data, db) :
    delete(client_id, db)
    conn = sqlite3.connect(db)
    c = conn.cursor()
    db_data = { "client_id" : client_id,
            "data" : data}
    try :
        c.execute("INSERT INTO client VALUES (:client_id, :data)", db_data)
    except :
        return None
    conn.commit()
    conn.close()


def read(client_id, db) :
    conn = sqlite3.connect(db)
    c = conn.cursor()
    db_data = { 'client_id' : client_id}
    c.execute('SELECT data FROM client WHERE client_id = :client_id ', db_data)
    client_data = c.fetchone()
    conn.close()
    if not client_data :
        return None
    return client_data[0]


def list(db) :
    """ Return list of username """
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT client_id, data FROM client")
    db_select = c.fetchall()
    conn.close()
    select = [item[1] for item in db_select]
    return select


def delete(client_id, db) :
    conn = sqlite3.connect(db)
    c = conn.cursor()
    db_data = {'client_id' : client_id}
    try :
        c.execute("DELETE FROM client WHERE client_id = :client_id " , db_data)
    except :
        return None
    conn.commit()
    conn.close()
    return True