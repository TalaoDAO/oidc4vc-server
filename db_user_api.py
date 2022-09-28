import json
import logging
import sqlite3
logging.basicConfig(level=logging.INFO)


def create(login_name, data) :
    if isinstance(data, dict) :
        data = json.dumps(data)
    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    db_data = { "login_name" : login_name ,"data" : data}
    try :
        c.execute("INSERT INTO user_data VALUES (:login_name, :data)", db_data)
    except :
        logging.error('DB error')
        return None
    conn.commit()
    conn.close()
    return True


def update(login_name, data) :
    delete(login_name)
    return create(login_name, data)


def read(login_name) :
    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    db_data = { 'login_name' : login_name}
    c.execute('SELECT data FROM user_data WHERE login_name = :login_name ', db_data)
    client_data = c.fetchone()
    conn.close()
    if not client_data :
        return None
    return client_data[0]


def list() :
    """ Return list of user """
    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    c.execute("SELECT login_name, data FROM user_db")
    db_select = c.fetchall()
    conn.close()
    select = [item[1] for item in db_select]
    return select


def delete(client_id, db) :
    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    db_data = {'client_id' : client_id}
    try :
        c.execute("DELETE FROM client WHERE client_id = :client_id " , db_data)
    except :
        return None
    conn.commit()
    conn.close()
    return True