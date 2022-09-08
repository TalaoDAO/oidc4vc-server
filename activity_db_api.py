import json
import uuid
import traceback
import logging
import sys
import sqlite3
logging.basicConfig(level=logging.INFO)


def create(client_id, record) :
    if not isinstance(record, str) :
        record = json.dumps(record)
    conn = sqlite3.connect("verifier_activity.db")
    c = conn.cursor()
    db_data = { "client_id" : client_id ,"data" : record}
    try :
        c.execute("INSERT INTO activity VALUES (:client_id, :data)", db_data)
        conn.commit()
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
        logging.error('DB error')
        return None
    conn.close()
    return True


def list(client_id) :
    """ Return list of username """
    conn = sqlite3.connect("verifier_activity.db")
    data = {"client_id" : client_id}
    c = conn.cursor()
    c.execute("SELECT data FROM activity WHERE client_id = :client_id ", data)
    db_select = [x[0]for x in c.fetchall()]
    conn.close()
    return db_select
