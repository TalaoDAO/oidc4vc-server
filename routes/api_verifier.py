from flask import jsonify, request, render_template, Response, redirect, session, jsonify
from flask import session,Response, jsonify
import json
import uuid
from urllib.parse import urlencode
import logging
import base64
from datetime import datetime
from jwcrypto import jwk, jwt
import didkit
from db_api import read_verifier
import op_constante

logging.basicConfig(level=logging.INFO)
ACCESS_TOKEN_LIFE = 180
CODE_LIFE = 180


try :
    rsa_key_dict = json.load(open("/home/admin/sandbox/keys.json", "r"))['RSA_key']
except :
    rsa_key_dict = json.load(open("/home/thierry/sandbox/keys.json", "r"))['RSA_key']

rsa_key = jwk.JWK(**rsa_key_dict) 
public_rsa_key =  rsa_key.export(private_key=False, as_dict=True)

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


def build_id_token(client_id, sub, nonce, mode) :
    verifier_key = jwk.JWK(**rsa_key_dict) 
    # https://jwcrypto.readthedocs.io/en/latest/jwk.html
    header = {
        "typ" :"JWT",
        "kid": rsa_key_dict['kid'],
        "alg": "RS256"
    }
    payload = {
        "iss" : mode.server +'sandbox/op',
        "nonce" : nonce,
        "iat": datetime.timestamp(datetime.now()),
        "aud" : client_id,
        "exp": datetime.timestamp(datetime.now()) + 1000,
        "sub" : sub
    }
    token = jwt.JWT(header=header,claims=payload, algs=["RS256"])
    token.make_signed_token(verifier_key)
    return token.serialize()
   

def jwks() :
    print(public_rsa_key)
    return jsonify({"keys" : [public_rsa_key]})


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
        logging.warning('there is an error in the OP')
        logging.warning('error = %s', request.args['error'])
        code = request.args['code']
        try : 
            data =  json.loads(red.get(code).decode())
        except :
            return jsonify('request expired'), 400
        resp = {'error' : request.args['error']}
        if data.get('state') :
            resp['state'] = data['state']
        red.delete(code)
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
            "expires" : datetime.timestamp(datetime.now()) + CODE_LIFE
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
    
    # creation grant (code)
    code = str(uuid.uuid1())
    red.set(code, json.dumps(data))
    return redirect('/sandbox/login?code=' + code)
   

# token endpoint
async def wallet_token(red, mode) :
    #https://datatracker.ietf.org/doc/html/rfc6749#section-5.2
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

    try :
        data = json.loads(red.get(code).decode())
    except :
        logging.warning('code expired' )
        endpoint_response= {"error": "invalid_grant"}
        headers = {'Content-Type': 'application/json'}
        return Response(response=json.dumps(endpoint_response), status=400, headers=headers)
    
    if verifier_data['client_secret'] != client_secret :
        logging.warning('client secret incorrect' )
        endpoint_response= {"error": "invalid_client"}
        headers = {'Content-Type': 'application/json'}
        return Response(response=json.dumps(endpoint_response), status=400, headers=headers)

    if client_id != data['client_id'] or redirect_uri != data['redirect_uri']:
        logging.warning('client_id or redirect_uri incorrect' )
        endpoint_response= {"error": "invalid_client"}
        headers = {'Content-Type': 'application/json'}
        return Response(response=json.dumps(endpoint_response), status=400, headers=headers)
    
    if grant_type != 'authorization_code' :
        logging.warning('grant type is incorrect')
        endpoint_response= {"error": "unauthorized_client"}
        headers = {'Content-Type': 'application/json'}
        return Response(response=json.dumps(endpoint_response), status=400, headers=headers)
    
    # token response
    vp = red.get(code + "_vp").decode()
    DID = json.loads(vp)['verifiableCredential']['credentialSubject']['id']
    id_token = build_id_token(client_id, DID, data['nonce'], mode)
    logging.info('id_token and vp_token sent to RP')
    access_token = str(uuid.uuid1())
    endpoint_response = {"id_token" : id_token,
                        "access_token" : access_token,
                        "token_type" : "Bearer",
                        "expires_in": ACCESS_TOKEN_LIFE
                        }
    red.delete(code)
    red.delete(code + '_vp')
    red.setex(access_token, 
            ACCESS_TOKEN_LIFE,
            json.dumps({"sub" : DID,"vp_token" : json.loads(vp)}))
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
    try :
        data = json.loads(red.get(access_token).decode())
        return jsonify(data)
    except :
        logging.warning("access token expired")
        headers = {'WWW-Authenticate' : 'Bearer realm="userinfo", error="invalid_token", error_description = "The access token expired"'}
        return Response(status=401,headers=headers)



"""
Protocol pour Presentation Request
"""


def login_qrcode(red, mode):

    stream_id = str(uuid.uuid1())
    try :
        client_id = json.loads(red.get(request.args['code']).decode())['client_id']
    except :
        logging.error("session expired in login_qrcode")
        return jsonify("session expired"), 404
    nonce = json.loads(red.get(request.args['code']).decode())['nonce']
    verifier_data = json.loads(read_verifier(client_id))
    if verifier_data['vc'] == "ANY" :
        pattern = op_constante.model_any
    elif verifier_data['vc'] == "DID" :
        pattern = op_constante.model_DIDAuth
    else :
        pattern = op_constante.model_one
        pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = verifier_data['reason']
        pattern["query"][0]["credentialQuery"][0]["example"]["type"] = verifier_data['vc']
    if nonce :
        pattern['challenge'] = nonce
    pattern['domain'] = mode.server
    data = { "pattern": pattern,"code" : request.args['code'] }
    red.set(stream_id,  json.dumps(data))
    url = mode.server + 'sandbox/login_presentation/' + stream_id + '?' + urlencode({'issuer' : did_selected})
    deeplink_talao = mode.deeplink + 'app/download?' + urlencode({'uri' : url})
    deeplink_altme= mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url})
    return render_template('op_verifier_qrcode.html',
							url=url,
                            deeplink_talao=deeplink_talao,
                            deeplink_altme=deeplink_altme,
							stream_id=stream_id,
                            qrcode_message=verifier_data.get('qrcode_message'),
                            mobile_message=verifier_data.get('mobile_message'),
                            landing_page_url= verifier_data['landing_page_url'],
                            title=verifier_data['title'],
                            terms_url= verifier_data.get('terms_url'),
                            privacy_url=verifier_data.get('privacy_url'),
                            company_name=verifier_data.get('company_name'),
                            page_title=verifier_data['page_title'],
                            page_subtitle=verifier_data['page_subtitle'],
                            page_description=verifier_data['page_description'],
                            page_background_color = verifier_data['page_background_color'],
                            page_text_color = verifier_data['page_text_color'],
                            qrcode_background_color = verifier_data['qrcode_background_color']
                            )
    


async def login_presentation_endpoint(stream_id, red):
    """
    stream_id_access : message d'erreur retourné a l authorization server 
    stream_id_vp : presentation reçu du wallet
    
    """
    if request.method == 'GET':
        my_pattern = json.loads(red.get(stream_id).decode())['pattern']
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
            email = json.loads(presentation)['verifiableCredential']['credentialSubject']['email'].lower()
            if email not in authorized_list :
                logging.warning('email not in authorized list')
                red.set(stream_id + '_access',  'access_denied')
                event_data = json.dumps({"stream_id" : stream_id})           
                red.publish('login', event_data)
                return jsonify("access_denied"), 404
        
        red.set(stream_id + '_access',  'ok')
        red.set(stream_id + '_vp',  request.form['presentation'])
        event_data = json.dumps({"stream_id" : stream_id})           
        red.publish('login', event_data)
        return jsonify("ok")


# check if user is connected or not
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
    # redirect to authorize server
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
