from flask import jsonify, request, render_template, Response, redirect, session, jsonify
from flask import session,Response, jsonify
import json
from datetime import timedelta
import uuid
from urllib.parse import urlencode
import logging
import base64
from datetime import datetime
from jwcrypto import jwk, jwt
import didkit
from verifier_db_api import read_verifier


logging.basicConfig(level=logging.INFO)
OFFER_DELAY = timedelta(seconds= 10*60)

key = {"kty": "RSA", "kid" : "123", "n": "uEUuur6rqoEMaV3qEgzf4a8jSWzLuftWzW1t9SApbKKKI9_M2ZCValgbUJqpto190zKgBge20d7Hwb24Y_SrxC2e8W7sQMNCEHdCrAvzjtk36o3tKHbsSfYFRfDexZJKQ75tsA_TOSMRKH_xGSO-15ZL86NXrwMrg3CLPXw6T0PjG38IsJ2UHAZL-3ezw7ibDto8LD06UhLrvCMpBlS6IMmDYFRJ-d2KvnWyKt6TyNC-0hNcDS7X0jaODATmDh-rOE5rv5miyljjarC_3p8D2MJXmYWk0XjxzozXx0l_iQyh-J9vQ_70gBqCV1Ifqlu8VkasOfIaSbku_PJHSXesFQ", "e": "AQAB", "d": "SXFleQ-yqu_pSvuf5dbUyoX72fFvV255_8FsMGVDrWUxCrBR3Kr4Klz4cg1atAQ70JfeWNjtQEN7OVhM7CXh6fxG27JanktUguyNmbXfuqEP3L_5dIXFkoroOiKRH4y5Zbu5yxDbnmvAFHS92se48gMYvX_uXDY2uxn5nSVsthdI7TKyMbe_-sXui-Wg8uFmB3pAxueE2a1koDdMNmZJ9bjTopYrIq8HpgI2U_MRPqNU5lVoUVrGQbVMUaLkQsTXjJZJ-aCs9s7TvMYB164tWjc9MyUadnFR0f8wFdn5yDM6Abn7rYZ8lqq9Jfo_QSbb3jk7OoonZF3GWXWfz8MDhw", "p": "ufPro-NIo1vts5TFHJb0_61-qXV2ks5DctqfrJf3qFo5bsQOO5ICcl8zarso8M6qvbSuymC0QWgDKEAi_f3MBM3p9nHOEJiaS8NL2kDArL9NZXZJwE2a4aVmddEI6uVjgzTXZtXlmrvUJovdFu3XefJ5CIrmHtJuHCBrGcH_Etc", "q": "_a8Bho_BHTOMr86Wq3UXD6IFKZb8Aw6DTYa8Lxn1qw8YYDMOEAExChoTsB8M70sdz4G9UW1pBgfYUbXgs7dsXomoiJKsWtcGrSQYouV3smTw74vl3FsFJpiuovM_bD5txRLnHKsi6P97lVAo-6sJMj4KQyTXy0fOnLEU51AeRvM", "dp": "JKXB5wbAJhHUAvRq9Ht7xXf34oXX3I7yFAyqM2Wv1WoSr5XMCEl6WfgRNhO0ueDBHaoiWJg-bjWFicU6IDyInNnIJl2_ct3gatYOePESB_mb00dAubmRsK7cRpPv4ftbZVxgp0-4dIpYAVDHPeGZ-dqjp99YAvMN6FUrRmRJVPk", "dq": "TDWO18XH1eXulcISMV_zlZauxle9TY3GlDutvNinnMPkJsIvr08sVESRNY-eayS9x-DJ5vRfYJhqu-FPp62quJvSLXUiogeG0ezOGeGlm8oHN29nllMhsP6dOAarPvFiOJn9I_elfSmDDtAN_8zZ7mYE3zbqPP9NanUoOnUvI1E", "qi": "fpEiQo_OODLTehEXsdSh9LGN0G9s9MShWKONc5x1pIZXByLxgs-8cfa9uq2P1D-rajgzxPTfdCko3NJhf2AdT3ipDsDfdizGu8Pcd2TefpTa9Td7pVYym88ZJkK5_oR3a27rWrQLXsCOG1ALYO-Yr0-cPSjRZas6sEaRa81W6m0"}

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
    app.add_url_rule('/sandbox/op/authorize',  view_func=wallet_authorize, methods = ['GET', 'POST'], defaults={"red" : red})
    app.add_url_rule('/sandbox/op/token',  view_func=wallet_token, methods = ['GET', 'POST'], defaults={"red" : red, 'mode' : mode})
    app.add_url_rule('/sandbox/op/logout',  view_func=wallet_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/userinfo',  view_func=wallet_userinfo, methods = ['GET', 'POST'], defaults={"red" : red})
    app.add_url_rule('/sandbox/op/.well-known/openid-configuration', view_func=openid_configuration, methods=['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/jwks.json', view_func=jwks, methods=['GET'])

    # http://172.20.10.2:3000/sandbox/.well-known/openid-configuration
    app.add_url_rule('/sandbox/login',  view_func=login_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/sandbox/login_presentation/<stream_id>',  view_func=login_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    app.add_url_rule('/sandbox/login_followup',  view_func=login_followup, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/login_presentation_stream',  view_func=login_presentation_stream, defaults={ 'red' : red})
    return


async def build_id_token(client_id, sub, nonce, mode) :
    verifier_key = jwk.JWK(**key) 
    # https://jwcrypto.readthedocs.io/en/latest/jwk.html
    header = {
        "typ" :"JWT",
        "kid": key['kid'],
        "alg": "RS256"
    }
    payload = {
        "iss" : mode.server +'sandbox/op',
        "sub" : sub,
        "nonce" : nonce,
        "iat": datetime.timestamp(datetime.now()),
        "aud" : client_id,
        "exp": datetime.timestamp(datetime.now()) + 1000,
        "sub" : sub
    }
    token = jwt.JWT(header=header,claims=payload, algs=["RS256"])
    token.make_signed_token(verifier_key)
    return token.serialize()
   
"""
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
"""

def jwks() :
    key = { "keys" : [
        {"e":"AQAB","kid" : "123", "kty":"RSA","n":"uEUuur6rqoEMaV3qEgzf4a8jSWzLuftWzW1t9SApbKKKI9_M2ZCValgbUJqpto190zKgBge20d7Hwb24Y_SrxC2e8W7sQMNCEHdCrAvzjtk36o3tKHbsSfYFRfDexZJKQ75tsA_TOSMRKH_xGSO-15ZL86NXrwMrg3CLPXw6T0PjG38IsJ2UHAZL-3ezw7ibDto8LD06UhLrvCMpBlS6IMmDYFRJ-d2KvnWyKt6TyNC-0hNcDS7X0jaODATmDh-rOE5rv5miyljjarC_3p8D2MJXmYWk0XjxzozXx0l_iQyh-J9vQ_70gBqCV1Ifqlu8VkasOfIaSbku_PJHSXesFQ"}
        ]}
    return jsonify(key)


def openid_configuration(mode):
    oidc = {
        "issuer": mode.server + 'sandbox/op',
        "authorization_endpoint":  mode.server + 'sandbox/op/authorize',
        "token_endpoint": mode.server + 'sandbox/op/token',
        "userinfo_endpoint": mode.server + 'sandbox/op/userinfo',
        "logout_endpoint": mode.server + 'sandbox/op/logout',
        "jwks_uri": mode.server + 'sandbox/op/jwks.json',
        "scopes_supported": ["openid"],
        "response_types_supported": [
            "code",
        ],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic"
        ]
    }
    return jsonify(oidc)


# authorization server
def wallet_authorize(red) :
    # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2
    
    if session.get('is_connected') :
        logging.info('user is connected in OP')
        try :
            code = request.args['code']
        except :
            session.clear()
            return jsonify('request_malformed'),404        
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
async def wallet_token(red, mode) :
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
        endpoint_response= {"error": "invalid_request"}
        headers = {'Content-Type': 'application/json'}
        return Response(response=json.dumps(endpoint_response), status=400, headers=headers)
   
    data = json.loads(red.get(code).decode())
    if verifier_data['client_secret'] != client_secret or client_id != data['client_id'] or redirect_uri != data['redirect_uri']:
        logging.warning('client secret or code or redirect_uri incorrect' )
        endpoint_response= {"error": "invalid_client"}
        headers = {'Content-Type': 'application/json'}
        return Response(response=json.dumps(endpoint_response), status=400, headers=headers)
    
    if grant_type != 'authorization_code' :
        logging.warning('grant type is incorrect')
        endpoint_response= {"error": "unauthorzed_client"}
        headers = {'Content-Type': 'application/json'}
        return Response(response=json.dumps(endpoint_response), status=400, headers=headers)
    
    # token response
    vp = red.get(code + "_vp").decode()
    DID = json.loads(vp)['verifiableCredential']['credentialSubject']['id']
    id_token = await build_id_token(client_id, DID, data['nonce'], mode)
    logging.info('id_token and vp_token sent to RP')
    access_token = str(uuid.uuid1())
    endpoint_response = {"id_token" : id_token,
                        "access_token" : access_token,
                        "token_type" : "Bearer",
                        "expires_in": 180
                        }
    red.delete(code)
    red.delete(code + '_vp')
    red.set(access_token, json.dumps({"sub" : DID, "vp" : json.loads(vp)}))
    headers = {
        "Cache-Control" : "no-store",
        "Pragma" : "no-cache",
        'Content-Type': 'application/json'}
    return Response(response=json.dumps(endpoint_response), headers=headers)


# logout endpoint
def wallet_logout() :
    session.clear()
    logging.info("logout reçu")
    return jsonify('logout')


# userinfo endpoint
def wallet_userinfo(red) :
    access_token = request.headers["Authorization"].split()[1]
    data = json.loads(red.get(access_token).decode())
    return jsonify(data)

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


async def login_presentation_endpoint(stream_id, red):
    if request.method == 'GET':
        try :
            my_pattern = json.loads(red.get(stream_id).decode())['pattern']
        except :
            logging.error('red decode failed')
            red.set(stream_id + '_access',  'server_error')
            red.publish('login', json.dumps({"stream_id" : stream_id}))
            return jsonify("server error"), 500
        return jsonify(my_pattern)

    if request.method == 'POST' :
        presentation = request.form['presentation']
        # Test sur signature VC/VP
        result_presentation = await didkit.verify_presentation(presentation,  '{}')
        logging.info("check presentation = %s", result_presentation)
        credential = json.loads(presentation)['verifiableCredential']
        result_credential = await didkit.verify_credential(json.dumps(credential), '{}')
        logging.info("check credential = %s", result_credential)
        if json.loads(result_credential)['errors'] :
            red.set(stream_id + '_access',  'access_denied')
            event_data = json.dumps({"stream_id" : stream_id})           
            red.publish('login', event_data)
            return jsonify("signature_error"), 403
        
        # TODO check authorization criteria
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
                red.set(stream_id + '_access',  'access_denied')
                return jsonify("access_denied"), 404
        else :
            red.set(stream_id + '_access',  'ok')
        red.set(stream_id + '_vp',  request.form['presentation'])
        event_data = json.dumps({"stream_id" : stream_id})           
        red.publish('login', event_data)
        return jsonify("ok")


def login_followup(red):  
    stream_id = request.args['stream_id']
    code = json.loads(red.get(stream_id).decode())['code']
    if red.get(stream_id + '_access').decode() != 'ok' :
        resp = {'code' : code, 'error' : red.get(stream_id + '_access').decode()}
        session['is_connected'] = False
    else :
        vp = red.get(stream_id +'_vp').decode()     
        session['is_connected'] = True
        red.set(code +"_vp", vp)
        resp = {'code' : code}
    red.delete(stream_id + '_vp')
    red.delete(stream_id + '_access')
    red.delete(stream_id)
    return redirect ('/sandbox/op/authorize?' + urlencode(resp))


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
