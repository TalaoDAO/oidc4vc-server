import json
import uuid
import logging
import sqlite3
import random 
import string
from op_constante import client_data_pattern
logging.basicConfig(level=logging.INFO)


def create_verifier() :
    data = client_data_pattern
    letters = string.ascii_lowercase
    data['client_id'] = ''.join(random.choice(letters) for i in range(10))
    data['client_secret'] = str(uuid.uuid1())
    conn = sqlite3.connect('api.db')
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


def update_verifier(client_id, data) :
    delete_verifier(client_id)
    conn = sqlite3.connect('api.db')
    c = conn.cursor()
    db_data = { "client_id" : client_id,
            "data" : data}
    try :
        c.execute("INSERT INTO client VALUES (:client_id, :data)", db_data)
    except :
        return None
    conn.commit()
    conn.close()


def read_verifier(client_id) :
    conn = sqlite3.connect('api.db')
    c = conn.cursor()
    db_data = { 'client_id' : client_id}
    c.execute('SELECT data FROM client WHERE client_id = :client_id ', db_data)
    client_data = c.fetchone()
    conn.close()
    if not client_data :
        return None
    return client_data[0]


def list_verifier() :
    """ Return list of username """
    conn = sqlite3.connect('api.db')
    c = conn.cursor()
    c.execute("SELECT client_id, data FROM client")
    db_select = c.fetchall()
    conn.close()
    select = [item[1] for item in db_select]
    return select



def delete_verifier(client_id) :
    conn = sqlite3.connect('api.db')
    c = conn.cursor()
    db_data = {'client_id' : client_id}
    try :
        c.execute("DELETE FROM client WHERE client_id = :client_id " , db_data)
    except :
        return None
    conn.commit()
    conn.close()
    return True




