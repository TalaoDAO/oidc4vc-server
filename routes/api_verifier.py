from flask import jsonify, request, render_template, Response, redirect, session, jsonify
from flask import session,Response, jsonify
import json
from datetime import timedelta
import uuid
from urllib.parse import urlencode
import logging
import base64
import sqlite3
from datetime import datetime
from jwcrypto import jwk, jwt
import didkit


logging.basicConfig(level=logging.INFO)
OFFER_DELAY = timedelta(seconds= 10*60)

Mode=dict()

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



async def build_id_token(client_id, sub, key, method) :
    if isinstance(key, dict) :
        key = json.dumps(key)

    key_dict = json.loads(key)
    if key_dict['kty'] == "OKP" :
        alg = "EdDSA"
    elif key_dict['kty'] == "EC" and key_dict["crv"] == "secp256k1" :
        alg = "ES256K"
    elif key_dict['kty'] == "EC" and key_dict["crv"] == "P-256" :
        alg = "ES256"
    elif key_dict['kty'] == "RSA" :
        alg = "RS256"
    else :
        print("key type not supported")
        return None
    
    verifier_key = jwk.JWK.from_json(key) 
    # https://jwcrypto.readthedocs.io/en/latest/jwk.html
    header = {
        "typ" :"JWT",
        "kid": await didkit.key_to_verification_method(method, key),
        "alg": alg
    }
    payload = {
        "iat": round(datetime.timestamp(datetime.now())),
        "aud" : client_id,
        "exp": round(datetime.timestamp(datetime.now())) + 1000,
        "sub" : sub
    }
    token = jwt.JWT(header=header,claims=payload, algs=["ES256", "ES256K", "EdDSA", "RS256"])
    token.make_signed_token(verifier_key)
    return token.serialize()
   
   

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


# authorization server
def wallet_authorize(red) :
    # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2
    
    if session.get('is_connected') :
        logging.info('user is connected in OP')
        code = request.args['code']
        data =  json.loads(red.get(code).decode())
        if  data.get('state') :
            resp = {'code' : code,  'state' : data['state']}
        else :
            resp = {'code' : code}
        return redirect(data['redirect_uri'] + '?' + urlencode(resp)) 
    
    if 'error' in request.args :
        logging.warning('error = %s', request.args['error'])
        code = request.args['code']
        data =  json.loads(red.get(code).decode())
        if data.get('state') :
            resp = {'error' : request.args['error'], 'state' : data['state']}
        else :
            resp = {'error' : request.args['error']}
        return redirect(data['redirect_uri'] + '?' + urlencode(resp)) 
    
    logging.info('user is not connected in OP')
    try : 
        data = {
            'client_id' : request.args['client_id'],
            'scope' : request.args['scope'],
            'state' : request.args.get('state'),
            'response_type' : request.args['response_type'],
            'redirect_uri' : request.args['redirect_uri'],
            'nonce' : request.args.get('nonce'),
            "expires" : round(datetime.timestamp(datetime.now())) + 1000
        }
    except :
        logging.warning('invalid request')
        try :
            resp = {'error' : 'invalid_request_object'}
            return redirect(request.args['redirect_uri'] + '?' + urlencode(resp))
        except :
            return jsonify('request malformed'), 400

    if not read_verifier(request.args['client_id']) :
        logging.warning('client_id not found')
        resp = {'error' : 'unauthorized_client'}
        return redirect(request.args['redirect_uri'] + '?' +urlencode(resp))

    if request.args['response_type'] != "code" :
        logging.warning('unsupported response type')
        resp = {'error' : 'unsupported_response_type'}
        return redirect(request.args['redirect_uri'] + '?' +urlencode(resp))
    
    # creation code
    code = str(uuid.uuid1())
    red.set(code, json.dumps(data))
    return redirect('/sandbox/login?code=' + code)
   

# token endpoint
async def wallet_token(red) :
    try :
        token = request.headers['Authorization']
        token = token.split(" ")[1]
        token = base64.b64decode(token).decode()
        client_secret = token.split(":")[1]
        client_id = token.split(":")[0]
        verifier_data = json.loads(read_verifier(client_id))
        grant_type =  request.form['grant_type']
        code = request.form['code']
        redirect_uri = request.form['redirect_uri']
    except :
        logging.warning('invalid request')
        return jsonify({"error": "invalid_request"}), 400
    
    vp_token = red.get(code + "_vp").decode()
    data = json.loads(red.get(code).decode())
    print(data)
    
    if verifier_data['client_secret'] != client_secret or client_id != data['client_id'] or redirect_uri != data['redirect_uri']:
        logging.warning('client secret or code or redirect_uri incorrect' )
        return jsonify({"error": "invalid_client"}), 400
    
    if grant_type != 'authorization_code' :
        logging.warning('grant type is incorrect')
        return jsonify({"error": "unauthorized_client"}), 400

    DID = json.loads(vp_token)['verifiableCredential']['credentialSubject']['id']
    id_token = await build_id_token(client_id, DID, verifier_data['jwk'], verifier_data['method'])
    logging.info('id_token and vp_token sent to RP')
    my_response = {"id_token" : id_token, "vp_token" : vp_token}
    """
    if "id_token" in data['response_type'].split() :
        my_response.update({"id_token" : id_token})
    if "vp_token" in data['response_type'].split() :
        my_response.update({"vp_token" : vp_token})
    """
    red.delete(code)
    red.delete(code + '_vp')
    return jsonify(my_response)


# logout endpoint
def wallet_logout() :
    session.clear()
    logging.info("logout reçu")
    return jsonify('logout')



"""
Protocol pour Presentation Request
"""

model_one = {
            "type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": [{
                    "example" : {
                        "type" : "",
                    },
                    "reason": [
                        {
                            "@language": "en",
                            "@value": ""
                        }
                    ]
                }]
                }
            ],
            "challenge": "",
            "domain" : ""
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
                    "credentialQuery": list()
                }
            ],
            "challenge": "",
            "domain" : ""
            }


def login_qrcode(red, mode):
    stream_id = str(uuid.uuid1())
    client_id = json.loads(red.get(request.args['code']).decode())['client_id']
    nonce = json.loads(red.get(request.args['code']).decode())['nonce']
    verifier_data = json.loads(read_verifier(client_id))
    qrcode_message = verifier_data.get('qrcode_message', "No message")
    mobile_message = verifier_data.get('mobile_message', "No message")
    if verifier_data['vc'] == "ANY" :
        pattern = model_any
    elif verifier_data['vc'] == "DID" :
        pattern = model_DIDAuth
    else :
        pattern = model_one
        pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = verifier_data['reason']
        pattern["query"][0]["credentialQuery"][0]["example"]["type"] = verifier_data['vc']
    if nonce :
        pattern['challenge'] = nonce
    pattern['domain'] = mode.server
    data = { "pattern": pattern,"code" : request.args['code'] }
    red.set(stream_id,  json.dumps(data))
    url = mode.server + 'sandbox/login_presentation/' + stream_id + '?' + urlencode({'issuer' : did_selected})
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url})
    return render_template('login_qrcode.html',
							url=url,
                            deeplink=deeplink,
							stream_id=stream_id,
                            qrcode_message=qrcode_message,
                            mobile_message=mobile_message 
                            )


def login_presentation_endpoint(stream_id, red):
    try :
        my_pattern = json.loads(red.get(stream_id).decode())['pattern']
    except :
        logging.error('red decode failed')
        red.set(stream_id + '_access',  'ko')
        red.publish('login', json.dumps({"stream_id" : stream_id}))
        return jsonify("server error"), 500

    if request.method == 'GET':
        print(my_pattern)
        return jsonify(my_pattern)

    elif request.method == 'POST' :
        presentation = request.form['presentation']
        print('presentation = ', presentation)
        # Test sur presentation
        logging.info('Presentation received from wallet is correctly formated')
        # check authorization criteria
        code = json.loads(red.get(stream_id).decode())['code']
        client_id =  json.loads(red.get(code).decode())['client_id']
        verifier_data = json.loads(read_verifier(client_id))
        # emails filtering
        if verifier_data['emails'] :
            authorized_emails = verifier_data['authorized_emails']
            authorized_list = [emails.replace(" ", "") for emails in authorized_emails.split(' ')]
            if json.loads(presentation)['verifiableCredential']['credentialSubject']['email'] in authorized_list :
                red.set(stream_id + '_access',  'ok')
            else :
                red.set(stream_id + '_access',  'ko')
        else :
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
        resp = {'code' : code, 'error' : 'access_denied'}
        return redirect ('/sandbox/authorize?' + urlencode(resp))
    else :
        try :
            vp = red.get(stream_id +'_vp').decode()
            red.delete(stream_id + '_vp')
            red.delete(stream_id + '_access')
            red.delete(stream_id)
        except :
            logging.warning('red.get problem')
            resp = {'code' : code, 'error' : 'server_error'}
            return redirect ('/sandbox/authorize?' + urlencode(resp))
        session['is_connected'] = True
        red.set(code +"_vp", vp)
    resp = {'code' : code}
    return redirect ('/sandbox/authorize?' + urlencode(resp))


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
