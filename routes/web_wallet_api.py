from flask import jsonify, request, render_template, Response, redirect, session, jsonify
from flask import session,Response, jsonify
import json
from datetime import timedelta
import uuid
from urllib.parse import urlencode
import logging
import base64
import sqlite3
import sys

logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)

Mode=dict()


credential_list = {
                    'EmailPass' : 'Proof of email',
                    'Kyc' : 'Identity card',
                    'Over18' : 'Over 18',
                    'Tez_Voucher_1' : "Voucher 15% Tezotopia",
                    'LearningAchievement' : 'Diploma',
                    'StudentCard' : 'Student card',
                    'CertificateOfEmployment' : 'Certificate of employment',
                    'DID' : "Decentralized Identifier"
                }

protocol_list = {'w3cpr' : "W3C Presentation Request ",
                 'openid4vc' : 'OpenID 4 VC'
                 }

client_data_pattern = {
                "client_id" :  "",
                "client_secret" : "",
                "company_name" : "",
                "website" : "",
                "callback_url" : "",
                "logout_url" : "",
                "reason" : "",
                "authorized_emails" : "",
                "vc" : "",
                "protocol" : ""
                }

did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/console',  view_func=console, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/console/select',  view_func=select, methods = ['GET', 'POST'])

    app.add_url_rule('/sandbox/authorize',  view_func=wallet_authorize, methods = ['GET', 'POST'], defaults={"red" : red})
    app.add_url_rule('/sandbox/token',  view_func=wallet_token, methods = ['GET', 'POST'], defaults={"red" : red})
    app.add_url_rule('/sandbox/logout',  view_func=wallet_logout, methods = ['GET', 'POST'])
    
    app.add_url_rule('/sandbox/login',  view_func=login_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/sandbox/login_presentation/<stream_id>',  view_func=login_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    app.add_url_rule('/sandbox/login_followup',  view_func=login_followup, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/login_presentation_stream',  view_func=login_presentation_stream, defaults={ 'red' : red})
    global Mode
    Mode=mode
    return



def extract_client(Mode):
    return 'http://'+ Mode.IP +':4000'

def extract_bridge(Mode):
    return 'http://'+ Mode.IP +':3000'



def add_client(client_id, data) :
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


def get_client(client_id) :
    conn = sqlite3.connect('api.db')
    c = conn.cursor()
    db_data = { 'client_id' : client_id}
    c.execute('SELECT data FROM client WHERE client_id = :client_id ', db_data)
    client_data = c.fetchone()
    conn.close()
    if not client_data :
        return None
    return client_data[0]


def client_list() :
    """ Return list of username """
    conn = sqlite3.connect('api.db')
    c = conn.cursor()
    c.execute("SELECT client_id, data FROM client")
    db_select = c.fetchall()
    conn.close()
    select = [item[1] for item in db_select]
    return select



def remove_client(client_id) :
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


def select() :
    if request.method == 'GET' :  
        my_list = client_list()
        select=str()
        for data in my_list :
            data_dict = json.loads(data)
            data_displayed = "client_id : " + data_dict['client_id'] +  "&nbsp&nbsp&nbsp&nbsp" + "client_secret : " + data_dict['client_secret'] + "&nbsp&nbsp&nbsp&nbsp" +  "company name : " + data_dict['company_name'] 
            select +=  "<option value=" + data_dict['client_id'] + ">" + data_displayed + "</option>"      
        return render_template('select.html', select=select) 
    else :
        client_id = request.form['client_id']
        return redirect ('/sandbox/console?client_id=' + client_id)



def console() :
    global vc, reason
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            session['client_data'] = client_data_pattern
            session['client_data']['client_id'] =  str(uuid.uuid1())[:10]
            session['client_data']['client_secret'] =   str(uuid.uuid1())
        else  :
            session['client_data'] = json.loads(get_client(request.args.get('client_id')))
        protocol_select = vc_select = str()
        for key, value in credential_list.items() :
                if key ==   session['client_data']['vc'] :
                    vc_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    vc_select +=  "<option value=" + key + ">" + value + "</option>"

        for key, value in protocol_list.items() :
                if key ==   session['client_data'].get('protocol', "") :
                    protocol_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    protocol_select +=  "<option value=" + key + ">" + value + "</option>"
       
        return render_template('console.html',
                client_id= session['client_data']['client_id'],
                client_secret= session['client_data']['client_secret'],
                callback_url= session['client_data']['callback_url'],
                logout_url=session['client_data']['logout_url'],
                token=extract_bridge(Mode) + '/sandbox/authorize',
                authorization=extract_bridge(Mode) + '/sandbox/token',
                website = session['client_data']['website'],
                company_name = session['client_data']['company_name'],
                reason = session['client_data']['reason'],
                authorized_emails = session['client_data']['authorized_emails'],
                protocol = session['client_data'].get('protocol', ""),
                vc_select=vc_select,
                protocol_select=protocol_select
                )
    if request.method == 'POST' :
        if request.form['button'] == "new" :
            return redirect ('/sandbox/console')
        
        elif request.form['button'] == "select" :
            return redirect ('/sandbox/console/select')
        
        elif request.form['button'] == "update" or request.form['button'] == "create" :
            session['client_data'] = client_data_pattern
            session['client_data']['client_id'] =  request.form['client_id']
            session['client_data']['client_secret'] = request.form['client_secret']
            session['client_data']['company_name'] = request.form['company_name']
            session['client_data']['website'] = request.form['website']
            session['client_data']['callback_url'] = request.form['callback_url']
            session['client_data']['logout_url'] = request.form['callback_url']
            session['client_data']['reason'] = request.form.get('reason', "")
            session['client_data']['authorized_emails'] = request.form.get('authorized_emails', "")
            session['client_data']['vc'] = request.form['vc']
            session['client_data']['protocol'] = request.form['protocol']

            if request.form['button'] == "update" :
                remove_client( request.form['client_id'])
            add_client(request.form['client_id'],json.dumps(session['client_data']))  
            return redirect('/sandbox/console?client_id=' + session['client_data']['client_id'])


# authorization server
def wallet_authorize(red) :
    # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2
    if session.get('is_connected') :
        logging.info('user is connected in OP')
        code = request.args['code']
        data =  json.loads(red.get(code).decode())
        if  data['client_data'].get('state') :
            resp = '?code=' + code + 'state=' + data['client_data']['state']
        else :
            resp = '?code=' + code
        return redirect(data['client_data']['callback_url'] + resp) 
    
    if 'error' in request.args :
        if request.args['error'] == 'access_denied' :
            logging.warning('user is denied')
            code = request.args['code']
            data =  json.loads(red.get(code).decode())
            return redirect(data['client_data']['callback_url'] +'?error= access_denied') 
        elif request.args['error'] == 'server_error' :
            logging.error('server error')
            code = request.args['code']
            data =  json.loads(red.get(code).decode())
            return redirect(data['client_data']['callback_url'] +'?error=server_error') 
    
    logging.info('user is not connected in OP')
    code = str(uuid.uuid1())
    try : 
        data = {
            'client_id' : request.args['client_id'],
            'state' : request.args.get('state', ""),
            'scope' : request.args['scope'],
            'redirect_uri' : request.args['redirect_uri'],
            'client_data' : json.loads(get_client(request.args['client_id']))
            }
    except :
        return jsonify('request malformed'),404

    if not get_client(request.args['client_id']) :
        logging.warning('client_id not found')
        return redirect(request.args['redirect_uri'] + '?error=unauthorized_client')
    
    red.set(code, json.dumps(data))
    return redirect('/sandbox/login?code=' + code)
   

# token endpoint
def wallet_token(red) :
    token = request.headers['Authorization']
    token = token.split(" ")[1]
    token = base64.b64decode(token).decode()
    #client_secret = token.split(":")[1]
    #client_id = token.split(":")[0]
    try :
        code = request.form.get('code')
        vp = red.get(code + "_vp").decode()
    except :
        return redirect(extract_client())
    my_response = {
                    'id_token' : "",
                    "access_token" : "",
                    "token_type":"Bearer",
                    "vp" : vp
                }
    red.delete(code)
    return jsonify(my_response)


# logout endpoint
def wallet_logout() :
    session.clear()
    logging.info("logout reçu")
    return jsonify('logout')



"""
Protocol pour Presentation Request
"""

credentialQuery = {
                    "example" : {
                        "type" : "EmailPass",
                    },
                    "reason": [
                        {
                            "@language": "en",
                            "@value": ""
                        }
                    ]
                }


model_DIDAuth = {
           "type": "VerifiablePresentationRequest",
           "query": [{
               "type": "DIDAuth"
               }],
           "challenge": "a random uri",
           "domain" : "talao.co"
    }

model_any = {
            "type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": []
                }
            ],
            "challenge": "",
            "domain" : ""
            }


def login_qrcode(red, mode):
    stream_id = str(uuid.uuid1())
    data = json.loads(red.get(request.args['code']).decode())['client_data']
    if data['vc'] == "Any" :
        pattern = model_any
    elif data['vc'] == "DID" :
        pattern = model_DIDAuth
    else :
        model_any['query'][0]['credentialQuery'].append(credentialQuery)
        pattern = model_any
        pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = data['reason']
        pattern["query"][0]["credentialQuery"][0]["example"]["type"] = data['vc']
      
    pattern['challenge'] = str(uuid.uuid1())
    pattern['domain'] = mode.server
    data = { "pattern": pattern,
            "code" : request.args['code'] }
    red.set(stream_id,  json.dumps(data))
    url = mode.server + 'sandbox/login_presentation/' + stream_id +'?issuer=' + did_selected
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    return render_template('login_presentation_qr.html',
							url=url,
                            deeplink=deeplink,
							stream_id=stream_id 
                            )


def login_presentation_endpoint(stream_id, red):
    try :
        my_pattern = json.loads(red.get(stream_id).decode())['pattern']
    except :
        logging.error('red decode failed')
        red.set(stream_id + '_access',  'ko')
        event_data = json.dumps({"stream_id" : stream_id})
        red.publish('credible', event_data)
        return jsonify("server error"), 500

    if request.method == 'GET':
        return jsonify(my_pattern)

    elif request.method == 'POST' :
        #presentation = request.form['presentation']
        # Test sur presentation
        logging.info('Presentation received from wallet is correctly formated')
        # check authorization criteria
        #code = json.loads(red.get(stream_id).decode())['code']
        #data =  json.loads(red.get(code).decode())
        red.set(stream_id + '_access',  'ok')
        #red.set(stream_id + '_access',  'ko')
        red.set(stream_id + '_vp',  request.form['presentation'])
        event_data = json.dumps({"stream_id" : stream_id})           
        red.publish('login', event_data)
        return jsonify("ok")


def login_followup(red):  
    stream_id = request.args['stream_id']
    code = json.loads(red.get(stream_id).decode())['code']
    if red.get(stream_id + '_access').decode() != 'ok' :
        red.delete(stream_id)
        red.delete(stream_id + '_access')
        return redirect ('/sandbox/authorize?code=' + code +'error=access_denied')
    else :
        try :
            vp = red.get(stream_id +'_vp').decode()
            red.delete(stream_id + '_vp')
            red.delete(stream_id + '_access')
            red.delete(stream_id)
        except :
            logging.warning('red.get problem')
            return redirect ('/sandbox/authorize?code=' + code +'error=server_error')
        session['is_connected'] = True
        red.set(code +"_vp", vp)
    return redirect ('/sandbox/authorize?code=' + code)


def login_presentation_stream(red):
    def login_event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('login')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(login_event_stream(red), headers=headers)
