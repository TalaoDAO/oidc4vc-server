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
from db_api import read_ebsi_verifier
import op_constante
import activity_db_api
import pkce # https://github.com/xzava/pkce

logging.basicConfig(level=logging.INFO)

ACCESS_TOKEN_LIFE = 1800
QRCODE_LIFE = 180
CODE_LIFE = 180
DID_VERIFIER = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

try :
    RSA_KEY_DICT = json.load(open("/home/admin/sandbox/keys.json", "r"))['RSA_key']
except :
    RSA_KEY_DICT = json.load(open("/home/thierry/sandbox/keys.json", "r"))['RSA_key']

rsa_key = jwk.JWK(**RSA_KEY_DICT) 
public_rsa_key =  rsa_key.export(private_key=False, as_dict=True)


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/ebsi/authorize',  view_func=ebsi_authorize, methods = ['GET', 'POST'], defaults={"red" : red, "mode" : mode})
    app.add_url_rule('/sandbox/ebsi/token',  view_func=ebsi_token, methods = ['GET', 'POST'], defaults={"red" : red, 'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/logout',  view_func=ebsi_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/ebsi/userinfo',  view_func=ebsi_userinfo, methods = ['GET', 'POST'], defaults={"red" : red})
    app.add_url_rule('/sandbox/ebsi/.well-known/openid-configuration', view_func=ebsi_openid_configuration, methods=['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/jwks.json', view_func=ebsi_jwks, methods=['GET'])
    app.add_url_rule('/sandbox/ebsi/webflow.altme.js', view_func=ebsi_webflow, methods=['GET'])
    # http://172.20.10.2:3000/sandbox/op/.well-known/openid-configuration
    
    # SIOPv2 endpoint
    app.add_url_rule('/sandbox/ebsi/login',  view_func=ebsi_login_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/login/endpoint/<stream_id>',  view_func=ebsi_login_endpoint, methods = ['POST'],  defaults={'red' : red})
    app.add_url_rule('/sandbox/ebsi/login/followup',  view_func=ebsi_login_followup, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/ebsi/login/stream',  view_func=ebsi_login_stream, defaults={ 'red' : red})
    return


def ebsi_webflow() :
    f = open('webflow_altme.js', 'r')
    payload = f.read()
    headers = {
            "Cache-Control" : "no-store",
            "Pragma" : "no-cache",
            "Content-Type": "text/javascript"}
    return Response(response=payload, headers=headers)
    

def ebsi_build_id_token(client_id, sub, nonce, vp, mode) :
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
        "sub" : sub,
    }  
    logging.info("ID Token payload = %s", payload)
    token = jwt.JWT(header=header,claims=payload, algs=["RS256"])
    token.make_signed_token(verifier_key)
    return token.serialize()
   

def ebsi_jwks() :
    return jsonify({"keys" : [public_rsa_key]})


def ebsi_openid_configuration(mode):
    """
    https://openid.net/specs/openid-connect-self-issued-v2-1_0.html#name-dynamic-self-issued-openid-
    """
    oidc = {
        "issuer": mode.server + 'sandbox/ebsi',
        "authorization_endpoint":  mode.server + 'sandbox/ebsi/authorize',
        "token_endpoint": mode.server + 'sandbox/ebsi/token',
        "userinfo_endpoint": mode.server + 'sandbox/ebsi/userinfo',
        "logout_endpoint": mode.server + 'sandbox/ebsi/logout',
        "jwks_uri": mode.server + 'sandbox/ebsi/jwks.json',
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
def ebsi_authorize(red, mode) :
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

        # implicit flow -> redirect with id_token in 
        elif session.get('response_type') == "id_token" :
            if session.get('response_mode') == "query" :
                sep = "?"
            else :
                sep = "#"
            code = request.args['code'] 
            try :
                vp = red.get(code + "_vp").decode()
            except :
                logging.error("code expired")
                resp = {'error' : "access_denied"}
                redirect_uri = session['redirect_uri']
                session.clear()
                return redirect(redirect_uri + sep + urlencode(resp)) 

            DID = json.loads(vp)['holder']
            id_token = ebsi_build_id_token(session['client_id'], DID, session.get('nonce'), vp, mode)
            resp = {"id_token" : id_token} 
            logging.info("redirect to client with id-token = %s", id_token)
            return redirect(session['redirect_uri'] + sep + urlencode(resp))
        
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
                resp["id_token"] = ebsi_build_id_token(session['client_id'], DID, session.get('nonce'), vp, mode)
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
    # PKCE https://datatracker.ietf.org/doc/html/draft-ietf-oauth-spop-14
    try :
        data = {
            'client_id' : request.args['client_id'],
            'scope' : request.args.get('scope'),
            'state' : request.args.get('state'),
            'response_type' : request.args['response_type'],
            'redirect_uri' : request.args['redirect_uri'],
            'nonce' : request.args.get('nonce'),  # nonce is required ????
            'code_challenge' : request.args.get('code_challenge'),
            'code_challenge_method' : request.args.get('code_challenge_method'),
            "expires" : datetime.timestamp(datetime.now()) + CODE_LIFE
        }
    except :
        logging.warning('invalid request received in authorization server')
        try :
            return manage_error_request("invalid_request_object")
        except :
            session.clear()
            return jsonify('request malformed'), 400

    if not read_ebsi_verifier(request.args['client_id']) :
        logging.warning('client_id not found id data base')
        return manage_error_request("unauthorized_client")

    session['client_id'] = request.args['client_id']

    verifier_data = json.loads(read_ebsi_verifier(request.args['client_id']))
    if request.args['redirect_uri'] != verifier_data['callback'] :
        logging.warning('redirect_uri of the request does not match the Callback URL')
        # TODO manage different redirect URL
        #return manage_error_request("invalid_request_object")
    session['redirect_uri'] = request.args['redirect_uri']
    if request.args['response_type'] not in ["code", "code id_token", "id_token", "id_token code", "vp_token", "id_token vp_token"] :
        logging.warning('unsupported response type %s', request.args['response_type'])
        return manage_error_request("unsupported_response_type")

    session['response_type'] = request.args['response_type']
    session['state'] = request.args.get('state')
    session['response_mode'] = request.args.get('response_mode')

    # creation grant (code)
    code = str(uuid.uuid1())
    red.setex(code, CODE_LIFE, json.dumps(data))
    resp = {'code' : code}
    return redirect('/sandbox/ebsi/login?code=' + code)
   

# token endpoint
async def ebsi_token(red, mode) :
    #https://datatracker.ietf.org/doc/html/rfc6749#section-5.2
    logging.info("token endpoint request ")

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
        verifier_data = json.loads(read_ebsi_verifier(client_id))
        grant_type =  request.form['grant_type']
        code = request.form['code']
        redirect_uri = request.form['redirect_uri']
        code_verifier = request.form.get('code_verifier')
    except :
        return manage_error("invalid_request")
     
    try :
        data = json.loads(red.get(code).decode())
    except :
        logging.error("red get probleme sur code")
        return manage_error("invalid_grant") 
    
    if client_id != data['client_id'] :
        return manage_error("invalid_client")
    if not verifier_data.get("pkce") and verifier_data['client_secret'] != client_secret :
        return manage_error("invalid_client")
    elif redirect_uri != data['redirect_uri']:
        return manage_error("invalid_redirect_uri")
    elif grant_type != 'authorization_code' :
        return manage_error("unhauthorized_client")
    if verifier_data.get('pkce') == 'on' and not code_verifier :
        logging.warning("pb code verifier")
        return manage_error("invalid_request")
    if verifier_data.get("pkce") and pkce.get_code_challenge(code_verifier) != data['code_challenge'] :
        logging.warning('code verifier not correct')
        return manage_error("unhauthorized_client")
    
    # token response
    try :
        vp = red.get(code + "_vp").decode()
    except :
        logging.error("red get probleme sur _vp")
        return manage_error("invalid_grant")
       
    DID = json.loads(vp)['verifiableCredential']['credentialSubject']['id']
    id_token = ebsi_build_id_token(client_id, DID, data['nonce'], vp, mode)
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
def ebsi_logout() :
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
def ebsi_userinfo(red) :
    logging.info("user info endpoint request")
    access_token = request.headers["Authorization"].split()[1]
    try :
        data = json.loads(red.get(access_token).decode())
        verifier_data = json.loads(read_ebsi_verifier(data['client_id']))
        payload = {"sub" : data['sub']}
        if verifier_data.get('standalone') :
            payload['vp'] = data["vp_token"]
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
https://openid.net/specs/openid-connect-self-issued-v2-1_0.html#section-10

qrcode ="openid://
    ?scope=openid
    &response_type=id_token
    &client_id=https%3A%2F%2Fapi-conformance.ebsi.eu%2Fconformance%2Fv2%2Fverifier-mock%2Fauthentication-responses
    &redirect_uri=https%3A%2F%2Fapi-conformance.ebsi.eu%2Fconformance%2Fv2%2Fverifier-mock%2Fauthentication-responses
    &claims=%7B%22id_token%22%3A%7B%22email%22%3Anull%7D%2C%22vp_token%22%3A%7B%22presentation_definition%22%3A%7B%22id%22%3A%22conformance_mock_vp_request%22%2C%22input_descriptors%22%3A%5B%7B%22id%22%3A%22conformance_mock_vp%22%2C%22name%22%3A%22Conformance%20Mock%20VP%22%2C%22purpose%22%3A%22Only%20accept%20a%20VP%20containing%20a%20Conformance%20Mock%20VA%22%2C%22constraints%22%3A%7B%22fields%22%3A%5B%7B%22path%22%3A%5B%22%24.vc.credentialSchema%22%5D%2C%22filter%22%3A%7B%22allOf%22%3A%5B%7B%22type%22%3A%22array%22%2C%22contains%22%3A%7B%22type%22%3A%22object%22%2C%22properties%22%3A%7B%22id%22%3A%7B%22type%22%3A%22string%22%2C%22pattern%22%3A%22https%3A%2F%2Fapi-conformance.ebsi.eu%2Ftrusted-schemas-registry%2Fv2%2Fschemas%2Fz3kRpVjUFj4Bq8qHRENUHiZrVF5VgMBUe7biEafp1wf2J%22%7D%7D%2C%22required%22%3A%5B%22id%22%5D%7D%7D%5D%7D%7D%5D%7D%7D%5D%2C%22format%22%3A%7B%22jwt_vp%22%3A%7B%22alg%22%3A%5B%22ES256K%22%5D%7D%7D%7D%7D%7D
    &nonce=051a1861-cfb6-48c8-861a-a61af5d1c139
    &conformance=36c751ad-7c32-4baa-ab5c-2a303aad548f"

"""

def ebsi_login_qrcode(red, mode):
    stream_id = str(uuid.uuid1())
    try :
        client_id = json.loads(red.get(request.args['code']).decode())['client_id']
        nonce = json.loads(red.get(request.args['code']).decode())['nonce']
    except :
        logging.error("session expired in login_qrcode")
        return render_template("session_expired.html")
    pattern = { 
        "scope" : "openid",
        "response_type" : "id_token",
        "client_id" : client_id,
        "redirect" : mode.server + "/sandbox/ebsi/login/endpoint/" + stream_id,
        "claims" : "",
        #"nonce" : nonce
    }
    if nonce :
        pattern['nonce'] = nonce

    verifier_data = json.loads(read_ebsi_verifier(client_id))
    claims = op_constante.ebsi_verifier_claims
    if verifier_data['vc'] == "DID" :
        pass
        print("credential not defined")
    #elif not verifier_data.get('vc_2') or verifier_data.get('vc_2') == "DID" :
    #    pass
    else :
        claims['vp_token']['presentation_definition']['id'] = str(uuid.uuid1())
        claims['vp_token']['presentation_definition']['input_descriptors'][0]['id'] = str(uuid.uuid1())
        claims['vp_token']['presentation_definition']['input_descriptors'][0]['name'] = ""
        claims['vp_token']['presentation_definition']['input_descriptors'][0]['purpose'] = verifier_data['reason'] 
        claims['vp_token']['presentation_definition']['input_descriptors'][0]['constraints']['fields'][0]['filter']['allOf'][0]['contains']['properties']['id']['pattern'] = verifier_data['vc'] 
        claims['vp_token']['presentation_definition']['format'] = {"jwt_vp":{"alg":["ES256K"]}}
    pattern['claims'] = claims
    data = { "pattern": pattern,"code" : request.args['code'] }
    red.setex(stream_id, QRCODE_LIFE, json.dumps(data))
    #url = mode.server + 'sandbox/login_presentation/' + stream_id + '?' + urlencode({'issuer' : DID_VERIFIER})
    url = 'openid://' + '?' + urlencode(pattern)
    deeplink_talao = mode.deeplink + 'app/download?' + urlencode({'uri' : url})
    deeplink_altme= mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url})

    if not verifier_data.get('verifier_landing_page_style') :
        qrcode_page = "op_verifier_qrcode_2.html"
    else : 
        qrcode_page = verifier_data.get('verifier_landing_page_style')
    print("qrcode = ", url)
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
    

async def ebsi_login_endpoint(stream_id, red):
    if request.method == 'POST' :
        
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
        
        async def check_credential(credential) :     
            result_credential = await didkit.verify_credential(json.dumps(credential), '{}')
            if json.loads(result_credential)['errors']  :       
                return manage_error("credential signature check failed")
            if  credential["credentialSubject"]['id'] != json.loads(presentation)['holder'] :
                if credential["credentialSubject"]['type'] == "AragoPass" :
                    logging.error("DID does not match in Arago pass")
                else :       
                    return manage_error("holder does not match subject.id")
            if credential.get('expirationDate') and credential.get('expirationDate') <  datetime.now().replace(microsecond=0).isoformat() + "Z" :
                return manage_error("credential expired")
            
            return

        presentation = request.form['presentation'] # string
        #result_presentation = await didkit.verify_presentation(presentation,  '{}')
        #if json.loads(result_presentation)['errors'] :
        #    return manage_error("presentation signature check failed")
        logging.info("check presentation = %s", await didkit.verify_presentation(presentation,  '{}'))

        credential = json.loads(presentation).get('verifiableCredential')
        if not credential :
            pass
        elif isinstance(credential, dict) :
            if credential["credentialSubject"]['type'] == "Pass" :
                code = json.loads(red.get(stream_id).decode())['code']
                client_id = json.loads(red.get(code).decode())['client_id']
                verifier_data = json.loads(read_ebsi_verifier(client_id))
                if credential["credentialSubject"]['issuedBy']['issuerId'] != verifier_data.get('vc_issuer_id') :
                    return manage_error("Pass issuer id does not match")
            await check_credential(credential)
        else :
            for vc in credential :
                await check_credential(vc)

        value = json.dumps({
                    "access" : "ok",
                    "vp" : json.loads(presentation),
                    "user" : json.loads(presentation)['holder']
                    })
        red.setex(stream_id + "_DIDAuth", 180, value)
        event_data = json.dumps({"stream_id" : stream_id})           
        red.publish('api_verifier', event_data)
        return jsonify("ok")


def ebsi_login_followup(red):  
    """
    check if user is connected or not and redirect data to authorization server
    create activity record
    """
    try :
        client_id = session['client_id']
        stream_id = request.args.get('stream_id')
    except :
        return jsonify("Forbidden"), 403 
    code = json.loads(red.get(stream_id).decode())['code']
    try :
        stream_id_DIDAuth = json.loads(red.get(stream_id + '_DIDAuth').decode())
    except :
        logging.error("code expired")
        resp = {'code' : code, 'error' : "access_denied"}
        session['verified'] = False
        return redirect ('/sandbox/ebsi/authorize?' + urlencode(resp))

    if stream_id_DIDAuth['access'] != 'ok' :
        resp = {'code' : code, 'error' : stream_id_DIDAuth['access']}
        session['verified'] = False
    else :
        session['verified'] = True
        red.setex(code +"_vp", 180, json.dumps(stream_id_DIDAuth['vp']))
        resp = {'code' : code}
    verifier_data = json.loads(read_ebsi_verifier(client_id))
    activity = {"presented" : datetime.now().replace(microsecond=0).isoformat() + "Z",
                "user" : stream_id_DIDAuth["user"],
                "credential_1" : verifier_data['vc'],
                "credential_2" : verifier_data.get('vc_2', "None"),
                "status" : session['verified']
    }
    activity_db_api.create(client_id, activity) 
    try :
        red.delete(stream_id + '_DIDAuth')
        red.delete(stream_id)
    except :
        pass
    return redirect ('/sandbox/ebsi/authorize?' + urlencode(resp))


def ebsi_login_stream(red):
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
