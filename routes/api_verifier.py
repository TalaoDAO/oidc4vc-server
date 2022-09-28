from flask import jsonify, request, render_template, Response, redirect, session, jsonify
from flask import session,Response, jsonify
import json
import uuid
from urllib.parse import urlencode
import logging
import base64
import time
from datetime import datetime
from jwcrypto import jwk, jwt
import didkit
from db_api import read_verifier
import op_constante
import activity_db_api

logging.basicConfig(level=logging.INFO)

ACCESS_TOKEN_LIFE = 1800
QRCODE_LIFE = 180
CODE_LIFE = 180
DID_VERIFIER = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
TRUSTED_ISSUER = [
    "did:tz:tz1RuLH4TvKNpLy3AqQMui6Hys6c1Dvik8J5",
    "did:tz:tz2X3K4x7346aUkER2NXSyYowG23ZRbueyse",
    "did:ethr:0x61fb76ff95f11bdbcd94b45b838f95c1c7307dbd",
    "did:web:talao.co",
    "did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250",
    "did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk",
    "did:ethr:0xd6008c16068c40c05a5574525db31053ae8b3ba7",
    "did:tz:tz1NyjrTUNxDpPaqNZ84ipGELAcTWYg6s5Du",
    "did:tz:tz2UFjbN9ZruP5pusKoAKiPD3ZLV49CBG9Ef"
]

try :
    RSA_KEY_DICT = json.load(open("/home/admin/sandbox/keys.json", "r"))['RSA_key']
except :
    RSA_KEY_DICT = json.load(open("/home/thierry/sandbox/keys.json", "r"))['RSA_key']

rsa_key = jwk.JWK(**RSA_KEY_DICT) 
public_rsa_key =  rsa_key.export(private_key=False, as_dict=True)



def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/authorize',  view_func=wallet_authorize, methods = ['GET', 'POST'], defaults={"red" : red, "mode" : mode})
    app.add_url_rule('/sandbox/op/token',  view_func=wallet_token, methods = ['GET', 'POST'], defaults={"red" : red, 'mode' : mode})
    app.add_url_rule('/sandbox/op/logout',  view_func=wallet_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/userinfo',  view_func=wallet_userinfo, methods = ['GET', 'POST'], defaults={"red" : red})
    app.add_url_rule('/sandbox/op/.well-known/openid-configuration', view_func=openid_configuration, methods=['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/jwks.json', view_func=jwks, methods=['GET'])
    app.add_url_rule('/sandbox/op/webflow.altme.js', view_func=webflow, methods=['GET'])


    # http://172.20.10.2:3000/sandbox/.well-known/openid-configuration
    app.add_url_rule('/sandbox/login',  view_func=login_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/sandbox/login_presentation/<stream_id>',  view_func=login_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    app.add_url_rule('/sandbox/login_followup',  view_func=login_followup, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/login_presentation_stream',  view_func=login_presentation_stream, defaults={ 'red' : red})
    return


def webflow() :
    f = open('webflow_altme.js', 'r')
    payload = f.read()
    headers = {
            "Cache-Control" : "no-store",
            "Pragma" : "no-cache",
            "Content-Type": "text/javascript"}
    return Response(response=payload, headers=headers)
    

def build_id_token(client_id, sub, nonce, vp, mode) :
    verifier_key = jwk.JWK(**RSA_KEY_DICT) 
    # https://jwcrypto.readthedocs.io/en/latest/jwk.html
    header = {
        "typ" :"JWT",
        "kid": RSA_KEY_DICT['kid'],
        "alg": "RS256"
    }
    # https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims
    payload = {
        "iss" : mode.server +'sandbox/op',
        "nonce" : nonce,
        "iat": datetime.timestamp(datetime.now()),
        "aud" : client_id,
        "exp": datetime.timestamp(datetime.now()) + 1000,
        "sub" : sub
    }
    verifier_data = json.loads(read_verifier(client_id))
    presentation = json.loads(vp)
    vc_expiration_date = presentation['verifiableCredential']['issuanceDate'][:19]
    payload["updated_at"] = time.mktime(time.strptime(vc_expiration_date, '%Y-%m-%dT%H:%M:%S'))
    if verifier_data['vc'] == "IdCard" :
        payload["given_name"] = presentation['verifiableCredential']['credentialSubject']['givenName']
        payload["family_name"] = presentation['verifiableCredential']['credentialSubject']['familyName']
        payload["gender"] = presentation['verifiableCredential']['credentialSubject']['gender']
        payload["birthdate"] = presentation['verifiableCredential']['credentialSubject']['birthDate']
    elif verifier_data['vc'] == "EmailPass" :
        payload["email"] = presentation['verifiableCredential']['credentialSubject']['email']
        payload["email_verified"] = True
    elif verifier_data['vc'] == "AgeRange" :
        payload["age_range"] = presentation['verifiableCredential']['credentialSubject']['ageRange']
    elif verifier_data['vc'] == "Over18" :
        payload["over_18"] = True
    elif verifier_data['vc'] == "Gender" :
        payload["gender"] = presentation['verifiableCredential']['credentialSubject']['gender']
    elif verifier_data['vc'] == "Nationality" :
        payload["nationality"] = presentation['verifiableCredential']['credentialSubject']['nationality']
    elif verifier_data['vc'] == "AragoPass" :
        payload["group"] = presentation['verifiableCredential']['credentialSubject']['group']
    else :
        pass
    logging.info("ID Token payload = %s", payload)
    token = jwt.JWT(header=header,claims=payload, algs=["RS256"])
    token.make_signed_token(verifier_key)
    return token.serialize()
   

def jwks() :
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
        "response_types_supported": ["code", "id_token", "vp_token" ],
        "token_endpoint_auth_methods_supported": ["client_secret_basic"]
    }
    return jsonify(oidc)


# authorization server
"""
response_type supported = code or id_token or vp_token
code -> authorization code flow
id_token -> implicit flow
id_token vp_token or vp_token -> oidc4vp

    # https://openid.net/specs/openid-4-verifiable-presentations-1_0.html

"""
def wallet_authorize(red, mode) :
    logging.info("authorization endpoint request args = %s", request.args)
    # https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2

    # user is connected, successfull exit to client with code
    if session.get('verified') and request.args.get('code') :

        # authorization code flow -> redirect with code
        if "code" in session.get('response_type', []).split() :
            logging.info("response_type = code : successfull redirect to client with code = %s", request.args.get('code'))
            code = request.args['code']  
            if  session.get('state') :
                resp = {'code' : code,  'state' : session['state']}
            else :
                resp = {'code' : code}
            return redirect(session['redirect_uri'] + '?' + urlencode(resp)) 

        # implicit flow -> redirect with id_token
        elif session.get('response_type') == "id_token" :
            code = request.args['code'] 
            try :
                vp = red.get(code + "_vp").decode()
            except :
                logging.error("code expired")
                resp = {'error' : "access_denied"}
                redirect_uri = session['redirect_uri']
                session.clear()
                return redirect(redirect_uri + '?' + urlencode(resp)) 

            DID = json.loads(vp)['verifiableCredential']['credentialSubject']['id']
            id_token = build_id_token(session['client_id'], DID, session.get('nonce'), vp, mode)
            resp = {"id_token" : id_token} 
            logging.info("redirect to client with id-token = %s", id_token)
            return redirect(session['redirect_uri'] + '?' + urlencode(resp))
        
        # oidc4vp  -> redirect with vp_token and eventually id_token
        elif "vp_token" in session.get('response_type').split() :
            code = request.args['code'] 
            try :
                vp = red.get(code + "_vp").decode()
            except :
                logging.error("code expired")
                resp = {'error' : "access_denied"}
                redirect_uri = session['redirect_uri']
                session.clear()
                return redirect(redirect_uri + '?' + urlencode(resp)) 
            DID = json.loads(vp)['verifiableCredential']['credentialSubject']['id']
            resp = {"vp_token" : json.loads(vp)} 
            if "id_token" in session.get('response_type').split() :
                resp["id_token"] = build_id_token(session['client_id'], DID, session.get('nonce'), vp, mode)
                logging.info("redirect to client with id-token = %s",  resp["id_token"])
            logging.info("redirect to client with vp-token = %s", vp)
            return redirect(session['redirect_uri'] + '?' + urlencode(resp))
        
        else :
            logging.error("session expired")
            resp = {'error' : "access_denied"}
            redirect_uri = session['redirect_uri']
            session.clear()
            return redirect(redirect_uri + '?' + urlencode(resp)) 
    
    # error in login, exit, clear session
    if 'error' in request.args :
        logging.warning('there is an error in the login process, redirect to client with error code')
        logging.warning('error code = %s', request.args['error'])
        code = request.args['code']
        resp = {'error' : request.args['error']}
        if session.get('state') :
            resp['state'] = session['state']
        red.delete(code)
        redirect_uri = session['redirect_uri']
        session.clear()
        return redirect(redirect_uri + '?' + urlencode(resp)) 
    
    # User is not connected
    def manage_error_request(msg) :
        session.clear()
        resp = {'error' : msg}
        return redirect(request.args['redirect_uri'] + '?' +urlencode(resp))

    session['verified'] = False
    logging.info('user is not connected in OP')
    try :
        data = {
            'client_id' : request.args['client_id'],
            'scope' : request.args.get('scope'),
            'state' : request.args.get('state'),
            'response_type' : request.args['response_type'],
            'redirect_uri' : request.args['redirect_uri'],
            'nonce' : request.args.get('nonce'),
            "expires" : datetime.timestamp(datetime.now()) + CODE_LIFE
        }
    except :
        logging.warning('invalid request received in authorization server')
        try :
            return manage_error_request("invalid_request_object")
        except :
            session.clear()
            return jsonify('request malformed'), 400

    if not read_verifier(request.args['client_id']) :
        logging.warning('client_id not found id data base')
        return manage_error_request("unauthorized_client")

    session['client_id'] = request.args['client_id']

    verifier_data = json.loads(read_verifier(request.args['client_id']))
    if request.args['redirect_uri'] != verifier_data['callback'] :
        logging.warning('redirect_uri does not match Callback URL')
        return manage_error_request("invalid_request_object")
       
    session['redirect_uri'] = request.args['redirect_uri']

    if request.args['response_type'] not in ["code", "code id_token", "id_token", "id_token code", "vp_token", "id_token vp_token"] :
        logging.warning('unsupported response type %s', request.args['response_type'])
        return manage_error_request("unsupported_response_type")

    session['response_type'] = request.args['response_type']
    session['state'] = request.args.get('state')

    # creation grant (code) and redirect to  wallet login
    code = str(uuid.uuid1())
    red.setex(code, CODE_LIFE, json.dumps(data))
    resp = {'code' : code}
    if verifier_data['protocol'] == "w3cpr" :
        if session['state'] :
            resp['state'] = session['state']
        return redirect('/sandbox/login?' + urlencode(resp))
    else :
        if session['response_type'] not in ["vp_token"] :
            logging.warning('unsupported response type for siopv2 %s', request.args['response_type'])
            return manage_error_request("unsupported_response_type")
        else :
            return redirect('/sandbox/op/siopv2?code=' + code)
   

# token endpoint
async def wallet_token(red, mode) :
    #https://datatracker.ietf.org/doc/html/rfc6749#section-5.2
    logging.info("token endpoint request = %s", request.form)

    def manage_error (msg) :
        logging.warning(msg)
        endpoint_response= {"error": msg}
        headers = {'Content-Type': 'application/json'}
        return Response(response=json.dumps(endpoint_response), status=400, headers=headers)
    
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
        return manage_error("invalid_request")
     
    try :
        data = json.loads(red.get(code).decode())
    except :
        return manage_error("invalid_grant")
       
    if verifier_data['client_secret'] != client_secret or client_id != data['client_id'] :
        return manage_error("invalid_client")
    elif redirect_uri != data['redirect_uri']:
        return manage_error("invalid_redirect_uri")
    elif grant_type != 'authorization_code' :
        return manage_error("unhauthorized_client")
    
    # token response
    try :
        vp = red.get(code + "_vp").decode()
    except :
        return manage_error("invalid_grant")
       
    DID = json.loads(vp)['verifiableCredential']['credentialSubject']['id']
    id_token = build_id_token(client_id, DID, data['nonce'], vp, mode)
    logging.info('id_token and access_token sent to client from token endpoint')
    access_token = str(uuid.uuid1())
    endpoint_response = {"id_token" : id_token,
                        "access_token" : access_token,
                        "token_type" : "Bearer",
                        "expires_in": ACCESS_TOKEN_LIFE
                        }
    try :
        red.delete(code)
        red.delete(code + '_vp')
    except :
        pass
    red.setex(access_token, 
            ACCESS_TOKEN_LIFE,
            json.dumps({
                "client_id" : client_id,
                "sub" : DID,
                "vp_token" : json.loads(vp)}))
    headers = {
        "Cache-Control" : "no-store",
        "Pragma" : "no-cache",
        'Content-Type': 'application/json'}
    return Response(response=json.dumps(endpoint_response), headers=headers)
 

# logout endpoint
#https://openid.net/specs/openid-connect-rpinitiated-1_0-02.html
def wallet_logout() :
    if not session.get('verified') :
        return jsonify ('Forbidden'), 403
    if request.method == "GET" :
        post_logout_redirect_uri = session.args.get('post_logout_redirect_uri')
    elif request.method == "POST" :
        post_logout_redirect_uri = session.form.get('post_logout_redirect_uri')
    if not post_logout_redirect_uri :
        post_logout_redirect_uri = session['redirect_uri']
    session.clear()
    logging.info("logout call received, redirect to %s", post_logout_redirect_uri)
    return redirect(post_logout_redirect_uri)


# userinfo endpoint
"""
 https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims
 only access token is needed

"""
def wallet_userinfo(red) :
    access_token = request.headers["Authorization"].split()[1]
    try :
        data = json.loads(red.get(access_token).decode())
        payload = {"sub" : data['sub']}
        payload['_vp'] = data["vp_token"]
        headers = {
            "Cache-Control" : "no-store",
            "Pragma" : "no-cache",
            "Content-Type": "application/json"}
        return Response(response=json.dumps(payload), headers=headers)
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
        nonce = json.loads(red.get(request.args['code']).decode())['nonce']
    except :
        logging.error("session expired in login_qrcode")
        return jsonify("session expired"), 403
    verifier_data = json.loads(read_verifier(client_id))
    if verifier_data['vc'] == "ANY" :
        pattern = op_constante.model_any
    elif verifier_data['vc'] == "DID" :
        pattern = op_constante.model_DIDAuth
    elif not verifier_data.get('vc_2') or verifier_data.get('vc_2') == "DID" :
        pattern = op_constante.model_one
        pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = verifier_data['reason']
        pattern["query"][0]["credentialQuery"][0]["example"]["type"] = verifier_data['vc']
    else :
        pattern = op_constante.model_two
        pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = verifier_data['reason']
        pattern["query"][0]["credentialQuery"][0]["example"]["type"] = verifier_data['vc']
        pattern["query"][0]["credentialQuery"][1]["reason"][0]["@value"] = verifier_data['reason_2']
        pattern["query"][0]["credentialQuery"][1]["example"]["type"] = verifier_data['vc_2']
    
    if nonce :
        pattern['challenge'] = nonce
    pattern['domain'] = mode.server
    data = { "pattern": pattern,"code" : request.args['code'] }
    red.setex(stream_id, QRCODE_LIFE, json.dumps(data))
    url = mode.server + 'sandbox/login_presentation/' + stream_id + '?' + urlencode({'issuer' : DID_VERIFIER})
    deeplink_talao = mode.deeplink + 'app/download?' + urlencode({'uri' : url})
    deeplink_altme= mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url})

    if not verifier_data.get('verifier_landing_page_style') :
        qrcode_page = "op_verifier_qrcode_2.html"
    else : 
        qrcode_page = verifier_data.get('verifier_landing_page_style')
    return render_template(qrcode_page,
                            back_button = False,
							url=url,
                            deeplink_talao=deeplink_talao,
                            deeplink_altme=deeplink_altme,
							stream_id=stream_id,
                            application_name=verifier_data.get('application_name'),
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
    Redis : stream_id_DIDAuth : data pushed to followup endpoint  
    
    """
    if request.method == 'GET':
        try :
            my_pattern = json.loads(red.get(stream_id).decode())['pattern']
        except :
            value = json.dumps({"access" : "access_denied"})
            red.setex(stream_id + "_DIDAuth", 180, value)
            event_data = json.dumps({"stream_id" : stream_id})           
            red.publish('api_verifier', event_data)
            logging.error("QR code expired")
            return jsonify("signature_error"), 403
        print(my_pattern)
        return jsonify(my_pattern)

    if request.method == 'POST' :
        presentation = request.form['presentation'] # string

        # Check signature VC/VP and trusted issuer
        result_presentation = await didkit.verify_presentation(presentation,  '{}')
        logging.info("check presentation = %s", result_presentation)
        credential = json.loads(presentation)['verifiableCredential']
        result_credential = await didkit.verify_credential(json.dumps(credential), '{}')
        logging.info("check credential = %s", result_credential)

        def manage_error(msg) :
            value = json.dumps({
                    "access" : "access_denied",
                    "user" : credential["credentialSubject"]["id"]
                    })
            red.setex(stream_id + "_DIDAuth", 180, value)
            event_data = json.dumps({"stream_id" : stream_id})           
            red.publish('api_verifier', event_data)
            logging.error(msg)
            return jsonify(msg), 403

        """
        if json.loads(result_presentation)['errors'] :
            return manage_error("presentation signature check failed")
        """
      
        if json.loads(result_credential)['errors'] or credential["credentialSubject"]['id'] != json.loads(presentation)['holder'] :
            return manage_error("credential signature check failed")
        
        if credential.get('expirationDate') and credential.get('expirationDate') <  datetime.now().replace(microsecond=0).isoformat() + "Z" :
            return manage_error("credential expired")

        if credential['issuer'] not in TRUSTED_ISSUER :
            return manage_error("issuer not in trusted list")
       
        value = json.dumps({
                    "access" : "ok",
                    "vp" : json.loads(presentation),
                    "user" : credential["credentialSubject"]["id"]
                    })
        red.setex(stream_id + "_DIDAuth", 180, value)
        event_data = json.dumps({"stream_id" : stream_id})           
        red.publish('api_verifier', event_data)
        return jsonify("ok")


def login_followup(red):  
    """
    check if user is connected or not and redirect data to authorization server
    create activity record
    """
    try :
        client_id = session['client_id']
        stream_id = request.args.get('stream_id')
    except :
        return jsonify("Forbidden"), 403 
    
    try :
        stream_id_DIDAuth = json.loads(red.get(stream_id + '_DIDAuth').decode())
        code = json.loads(red.get(stream_id).decode())['code']
    except :
        logging.error("code expired")
        resp = {'code' : code, 'error' : "access_denied"}
        session['verified'] = False
        return redirect ('/sandbox/op/authorize?' + urlencode(resp))

    if stream_id_DIDAuth['access'] != 'ok' :
        resp = {'code' : code, 'error' : stream_id_DIDAuth['access']}
        session['verified'] = False
    else :
        session['verified'] = True
        red.setex(code +"_vp", 180, json.dumps(stream_id_DIDAuth['vp']))
        resp = {'code' : code}
    verifier_data = json.loads(read_verifier(session['client_id']))
    activity = {"presented" : datetime.now().replace(microsecond=0).isoformat() + "Z",
                "user" : stream_id_DIDAuth["user"],
                "credential_1" : verifier_data['vc'],
                "credential_2" : verifier_data.get('vc_2', "None"),
                "status" : session['verified']
    }
    activity_db_api.create(session['client_id'], activity) 
    try :
        red.delete(stream_id + '_DIDAuth')
        red.delete(stream_id)
    except :
        pass
    return redirect ('/sandbox/op/authorize?' + urlencode(resp))


def login_presentation_stream(red):
    def login_event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('api_verifier')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(login_event_stream(red), headers=headers)
