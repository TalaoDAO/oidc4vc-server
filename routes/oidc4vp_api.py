"""
This is a bridge between the SIOPV2 flow used by EBSI with a verifier and a standard Openid authorization code flow or implicit flow with used with the customer application

Customer can use any OpenId lib in its own framework to access an EBSI conformant wallet


"""

from flask import jsonify, request, render_template, redirect
from flask import session, Response, jsonify
import json
import uuid
from urllib.parse import urlencode
import logging
import base64
from datetime import datetime
from jwcrypto import jwk, jwt
from db_api import read_ebsi_verifier
import activity_db_api
import pkce # https://github.com/xzava/pkce
import oidc4vc
from profile import profile
from oidc4vc_constante import type_2_schema

logging.basicConfig(level=logging.INFO)

# customer application 
ACCESS_TOKEN_LIFE = 2000
CODE_LIFE = 2000

# wallet
QRCODE_LIFE = 2000

# verfier supported alg for siopv2
SUPPORTED_ALG = ['ES256K', 'ES256', 'ES384', 'ES512', 'RS256']

# OpenID key of the OP for customer application
try :
    RSA_KEY_DICT = json.load(open("/home/admin/sandbox/keys.json", "r"))['RSA_key']
except :
    RSA_KEY_DICT = json.load(open("/home/thierry/sandbox/keys.json", "r"))['RSA_key']
rsa_key = jwk.JWK(**RSA_KEY_DICT) 
public_rsa_key =  rsa_key.export(private_key=False, as_dict=True)


def init_app(app,red, mode) :
    # endpoints for OpenId customer application
    app.add_url_rule('/sandbox/ebsi/authorize',  view_func=ebsi_authorize, methods = ['GET', 'POST'], defaults={"red" : red, "mode" : mode})
    app.add_url_rule('/sandbox/ebsi/token',  view_func=ebsi_token, methods = ['GET', 'POST'], defaults={"red" : red, 'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/logout',  view_func=ebsi_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/ebsi/userinfo',  view_func=ebsi_userinfo, methods = ['GET', 'POST'], defaults={"red" : red})
    app.add_url_rule('/sandbox/ebsi/.well-known/openid-configuration', view_func=ebsi_openid_configuration, methods=['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/jwks.json', view_func=ebsi_jwks, methods=['GET'])
    
    # endpoints for siopv2/EBSI wallet
    app.add_url_rule('/sandbox/ebsi/login',  view_func=ebsi_login_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/login/endpoint/<stream_id>',  view_func=ebsi_login_endpoint, methods = ['POST'],  defaults={'red' : red}) # redirect_uri for PODST
    app.add_url_rule('/sandbox/ebsi/login/request_uri/<stream_id>',  view_func=ebsi_request_uri, methods = ['GET'], defaults={'red' : red})
    app.add_url_rule('/sandbox/ebsi/login/client_metadata_uri/<stream_id>',  view_func=client_metadata_uri, methods = ['GET'], defaults={'red' : red})
    app.add_url_rule('/sandbox/ebsi/login/followup',  view_func=ebsi_login_followup, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/ebsi/login/stream',  view_func=ebsi_login_stream, defaults={ 'red' : red})
    return
    

def ebsi_build_id_token(client_id, sub, nonce, mode) :
    """
    alg value : https://www.rfc-editor.org/rfc/rfc7518#section-3
    https://jwcrypto.readthedocs.io/en/latest/jwk.html
    """
    verifier_key = jwk.JWK(**RSA_KEY_DICT) 
    header = {
        "typ" :"JWT",
        "kid": RSA_KEY_DICT['kid'],
        "alg": "RS256"
    }
    # https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims
    payload = {
        "iss" : mode.server +'sandbox/ebsi',
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


# For customer app
def ebsi_openid_configuration(mode):
    """
    For the customer application of the saas platform  
    https://openid.net/specs/openid-connect-self-issued-v2-1_0.html#name-dynamic-self-issued-openid-
    """
    oidc = {
        "issuer": mode.server + 'sandbox/ebsi',
        "authorization_endpoint":  mode.server + 'sandbox/ebsi/authorize',
        "token_endpoint": mode.server + 'sandbox/ebsi/token',
        "userinfo_endpoint": mode.server + 'sandbox/ebsi/userinfo',
        "logout_endpoint": mode.server + 'sandbox/ebsi/logout',
        "jwks_uri": mode.server + 'sandbox/ebsi/jwks.json',
        "scopes_supported": ["openid diploma verifiableid"],
        "response_types_supported": ["code", "id_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic"]
    }
    return jsonify(oidc)


# authorization server for customer application
"""
response_type supported = code or id_token or vp_token
code -> authorization code flow
id_token -> implicit flow

# https://openid.net/specs/openid-4-verifiable-presentations-1_0.html

"""
def ebsi_authorize(red, mode) :
    logging.info("authorization endpoint request args = %s", request.args)
    """ https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2
     code_wallet_data = 
    {
        "vp_token_payload", : xxxxx
        "sub" : xxxxxx
    }
    """
    # user is connected, successfull exit to client with code
    if session.get('verified') and request.args.get('code') :

        # authorization code flow -> redirect with code
        if session.get('response_type') == 'code' :
            logging.info("response_type = code : successfull redirect to client with code = %s", request.args.get('code'))
            code = request.args['code']  
            resp = {'code' : code,  'state' : session['state']}  if  session.get('state') else {'code' : code}
            return redirect(session['redirect_uri'] + '?' + urlencode(resp)) 

        # implicit flow -> redirect with id_token
        elif session.get('response_type') == 'id_token' :
            sep = "?" if session.get('response_mode') == 'query' else "#"
            code = request.args['code'] 
            try :
                code_wallet_data = json.loads(red.get(code + "_wallet_data").decode())
            except :
                logging.error("code expired")
                resp = {'error' : "access_denied"}
                redirect_uri = session['redirect_uri']
                session.clear()
                return redirect(redirect_uri + sep + urlencode(resp)) 
            id_token = ebsi_build_id_token(session['client_id'], code_wallet_data['sub'], session.get('nonce'), mode)
            resp = {"id_token" : id_token} 
            logging.info("redirect to client with id-token = %s", id_token)
            return redirect(session['redirect_uri'] + sep + urlencode(resp))
        
        else :
            logging.error("session expired")
            resp = {'error' : "access_denied"}
            redirect_uri = session['redirect_uri']
            session.clear()
            return redirect(redirect_uri + '?' + urlencode(resp)) 
    
    # error in login, exit, clear session
    if 'error' in request.args :
        logging.warning('Error in the login process, redirect to client with error code = %s', request.args['error'])
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
            'scope' : request.args.get('scope').split(),
            'state' : request.args.get('state'),
            'response_type' : request.args['response_type'],
            'redirect_uri' : request.args['redirect_uri'],
            'nonce' : request.args.get('nonce'),
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
        logging.warning('client_id not found ebsi client data base')
        return manage_error_request("unauthorized_client")

    session['client_id'] = request.args['client_id']

    verifier_data = json.loads(read_ebsi_verifier(request.args['client_id']))
    if request.args['redirect_uri'] != verifier_data['callback'] :
        logging.warning('redirect_uri of the request does not match the Callback URL')

    session['redirect_uri'] = request.args['redirect_uri']
    if request.args['response_type'] not in ["code", "id_token"] :
        logging.warning('unsupported response type %s', request.args['response_type'])
        return manage_error_request("unsupported_response_type")

    session['response_type'] = request.args['response_type']
    session['state'] = request.args.get('state')
    session['response_mode'] = request.args.get('response_mode')

    # creation grant = code
    code = str(uuid.uuid1())
    red.setex(code, CODE_LIFE, json.dumps(data))
    resp = {'code' : code}
    return redirect('/sandbox/ebsi/login?code=' + code)
   

# token endpoint for customer application
def ebsi_token(red, mode) :
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
        code_wallet_data = json.loads(red.get(code + "_wallet_data").decode())
    except :
        logging.error("redis get problem to get code_ebsi")
        return manage_error("invalid_grant")
    id_token = ebsi_build_id_token(client_id, code_wallet_data['sub'], data['nonce'], mode)
    logging.info('id_token and access_token sent to client from token endpoint')
    access_token = str(uuid.uuid1())
    endpoint_response = {"id_token" : id_token,
                        "access_token" : access_token,
                        "token_type" : "Bearer",
                        "expires_in": ACCESS_TOKEN_LIFE
                        }
    red.setex(access_token + '_wallet_data', 
            ACCESS_TOKEN_LIFE,
            json.dumps({
                "client_id" : client_id,
                "sub" : code_wallet_data['sub'],
                "vp_token_payload" : code_wallet_data['vp_token_payload']}))
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
        wallet_data = json.loads(red.get(access_token + '_wallet_data').decode())
        payload = {
            "sub" : wallet_data['sub'],
            "vp_token_payload" : wallet_data["vp_token_payload"]
        }
        headers = {
            "Cache-Control" : "no-store",
            "Pragma" : "no-cache",
            "Content-Type": "application/json"}
        return Response(response=json.dumps(payload), headers=headers)
    
    except :
        logging.warning("access token expired")
        headers = {'WWW-Authenticate' : 'Bearer realm="userinfo", error="invalid_token", error_description = "The access token expired"'}
        return Response(status=401,headers=headers)
    
################################# SIOPV2 OIDC4VP ###########################################

"""
https://openid.net/specs/openid-connect-self-issued-v2-1_0.html#section-10

example of an siopv2 authorisation request
qrcode ="openid://
    ?scope=openid
    &response_type=id_token
    &client_id=https%3A%2F%2Fapi-conformance.ebsi.eu%2Fconformance%2Fv2%2Fverifier-mock%2Fauthentication-responses
    &redirect_uri=https%3A%2F%2Fapi-conformance.ebsi.eu%2Fconformance%2Fv2%2Fverifier-mock%2Fauthentication-responses
    &claims=%7B%22id_token%22%3A%7B%22email%22%3Anull%7D%2C%22vp_token%22%3A%7B%22presentation_definition%22%3A%7B%22id%22%3A%22conformance_mock_vp_request%22%2C%22input_descriptors%22%3A%5B%7B%22id%22%3A%22conformance_mock_vp%22%2C%22name%22%3A%22Conformance%20Mock%20VP%22%2C%22purpose%22%3A%22Only%20accept%20a%20VP%20containing%20a%20Conformance%20Mock%20VA%22%2C%22constraints%22%3A%7B%22fields%22%3A%5B%7B%22path%22%3A%5B%22%24.vc.credentialSchema%22%5D%2C%22filter%22%3A%7B%22allOf%22%3A%5B%7B%22type%22%3A%22array%22%2C%22contains%22%3A%7B%22type%22%3A%22object%22%2C%22properties%22%3A%7B%22id%22%3A%7B%22type%22%3A%22string%22%2C%22pattern%22%3A%22https%3A%2F%2Fapi-conformance.ebsi.eu%2Ftrusted-schemas-registry%2Fv2%2Fschemas%2Fz3kRpVjUFj4Bq8qHRENUHiZrVF5VgMBUe7biEafp1wf2J%22%7D%7D%2C%22required%22%3A%5B%22id%22%5D%7D%7D%5D%7D%7D%5D%7D%7D%5D%2C%22format%22%3A%7B%22jwt_vp%22%3A%7B%22alg%22%3A%5B%22ES256K%22%5D%7D%7D%7D%7D%7D
    &nonce=051a1861-cfb6-48c8-861a-a61af5d1c139
    &conformance=36c751ad-7c32-4baa-ab5c-2a303aad548f"

"""

def client_metadata_uri(stream_id, red):
    #https://openid.net/specs/openid-connect-registration-1_0.html
    return jsonify(client_metadata(stream_id, red))

def client_metadata(stream_id, red) :
    client_id = json.loads(red.get(stream_id).decode())['client_id']
    verifier_data = json.loads(read_ebsi_verifier(client_id))
    verifier_profile = profile[verifier_data['profile']]
    client_metadata = {
        'subject_syntax_types_supported': verifier_profile['subject_syntax_types_supported'], 
        'cryptographic_suites_supported' : verifier_profile['cryptographic_suites_supported'],
        'client_name': 'Talao-Altme Verifier',
        'Profile' : verifier_data['profile'],
        "logo_uri": "https://altme.io/",
        "contacts": ["contact@talao.io"]
    }
    return client_metadata

def ebsi_login_qrcode(red, mode):
    stream_id = str(uuid.uuid1())
    try :
        client_id = json.loads(red.get(request.args['code']).decode())['client_id']
        verifier_data = json.loads(read_ebsi_verifier(client_id))
        verifier_profile = profile[verifier_data['profile']]
    except :
        logging.error("session expired in login_qrcode")
        return render_template("ebsi/verifier_session_problem.html", message='Session expired')
       
    presentation_definition = {
                "id":"",
                "input_descriptors":[],
                "format":""
    }
    presentation_definition['id'] = str(uuid.uuid1())
    presentation_definition['format'] = {
        verifier_profile['verifier_vp_type'] : {
            "alg" : verifier_profile["cryptographic_suites_supported"]}
    } 

    if verifier_data['vc'] == "None" and verifier_data['vc_2'] == "None":
        logging.warning('Wrong configuration')
        return jsonify("KO"), 400
    
    elif verifier_data['vc'] == "DID" and verifier_data['vc_2'] in  ['None', 'DID'] :
        logging.info("SIOPV2 mode")
        response_type = "id_token"

    elif verifier_data['vc_2'] == "DID" and verifier_data['vc'] in  ['None', 'DID'] :
        logging.info("SIOPV2 mode")
        response_type = "id_token"
    
    elif verifier_data['vc'] == 'DID' or verifier_data['vc_2'] == 'DID':
        response_type = "id_token vp_token"
        logging.info("OIDC4VP mode")
        logging.info("1 credential requested")
        filter = {"type": "string"}  
        input_descriptor = {"constraints":{"fields":[{"path":[]}]}}
        if verifier_data['profile'] == "EBSI-V2" :
            input_descriptor["constraints"]["fields"][0]['path'].append("$.credentialSchema.id")
        else :
            input_descriptor["constraints"]["fields"][0]['path'].append("$.credentialSubject.type")
        input_descriptor["id"] = str(uuid.uuid1())
        input_descriptor["name"] = "Input descriptor 1"
        input_descriptor["purpose"] = verifier_data['reason']
        if verifier_data['profile'] == "EBSI-V2" :
            filter["pattern"] =  type_2_schema[verifier_data['vc']]
        else :
            filter["pattern"] =  verifier_data['vc']
        input_descriptor["constraints"]["fields"][0]["filter"] = filter
        presentation_definition["input_descriptors"].append(input_descriptor)
    
    elif (verifier_data['vc'] != 'DID' and verifier_data['vc_2'] ==  'None') or (verifier_data['vc_2'] != 'DID' and verifier_data['vc'] ==  'None') :
        response_type = "vp_token"
        logging.info("OIDC4VP mode")
        logging.info("1 credential requested")
        filter = {"type": "string"}  
        input_descriptor = {"constraints":{"fields":[{"path":[]}]}}
        if verifier_data['profile'] == "EBSI-V2" :
            input_descriptor["constraints"]["fields"][0]['path'].append("$.credentialSchema.id")
        else :
            input_descriptor["constraints"]["fields"][0]['path'].append("$.credentialSubject.type")
        input_descriptor["id"] = str(uuid.uuid1())
        input_descriptor["name"] = "Input descriptor 1"
        input_descriptor["purpose"] = verifier_data['reason']
        if verifier_data['profile'] == "EBSI-V2" :
            filter["pattern"] =  type_2_schema[verifier_data['vc']]
        else :
            filter["pattern"] =  verifier_data['vc']
        input_descriptor["constraints"]["fields"][0]["filter"] = filter
        presentation_definition["input_descriptors"].append(input_descriptor)

    else :
        response_type = "vp_token"
        logging.info("OIDC4VP mode")
        logging.info("2 credentials requested")
        filter_1 = {"type": "string"} 
        input_descriptor_1 = {"constraints":{"fields":[{"path":[]}]}}
        if verifier_data['profile'] == "EBSI-V2" :
            input_descriptor_1["constraints"]["fields"][0]['path'].append("$.credentialSchema.id")
        else :
            input_descriptor_1["constraints"]["fields"][0]['path'].append("$.credentialSubject.type")
        input_descriptor_1["id"] = str(uuid.uuid1())
        input_descriptor_1["name"] = "Input descriptor 1"
        input_descriptor_1["purpose"] = verifier_data['reason'] 
        if verifier_data['profile'] == "EBSI-V2" :
            filter_1["pattern"] =  type_2_schema[verifier_data['vc']]
        else :
            filter_1["pattern"] =  verifier_data['vc']
        input_descriptor_1["constraints"]["fields"][0]["filter"] = filter_1
        presentation_definition["input_descriptors"].append(input_descriptor_1)
        
        filter_2 = {"type": "string"} 
        input_descriptor_2 = {"constraints":{"fields":[{"path":[]}]}}
        if verifier_data['profile'] == "EBSI-V2" :
            input_descriptor_2["constraints"]["fields"][0]['path'].append("$.credentialSchema.id")
        else :
            input_descriptor_2["constraints"]["fields"][0]['path'].append("$.credentialSubject.type")
        input_descriptor_2["id"] = str(uuid.uuid1())
        input_descriptor_2["name"] = "input descriptor 2"
        input_descriptor_2["purpose"] = verifier_data["reason_2"] 
        if verifier_data['profile'] == "EBSI-V2" :
            filter_2["pattern"] =  type_2_schema[verifier_data['vc_2']]
        else :
            filter_2["pattern"] =  verifier_data['vc_2']
        input_descriptor_2["constraints"]["fields"][0]["filter"] = filter_2
        presentation_definition["input_descriptors"].append(input_descriptor_2)

    authorization_request = { 
        "response_type" : response_type,
        "client_id" : verifier_data['did'],
        "redirect_uri" : mode.server + "sandbox/ebsi/login/endpoint/" + stream_id,
        "nonce" : str(uuid.uuid1())
    }
    if verifier_data['profile'] == "EBSI-V2" :
        # previoous release of the OIDC4VC specifications
        # OIDC claims parameter https://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter
        authorization_request['scope'] = 'openid'
        authorization_request['claims'] = {"vp_token":{"presentation_definition": presentation_definition}}
        prefix = verifier_profile["oidc4vp_prefix"]
    
    else :
        authorization_request['response_mode'] = 'post'
        authorization_request['aud'] = 'https://self-issued.me/v2'
        authorization_request['client_metadata_uri'] = mode.server + "sandbox/ebsi/login/client_metadata_uri/" + stream_id
        # OIDC4VP
        if response_type == "id_token vp_token" :
            authorization_request['scope'] = 'openid'
            authorization_request['presentation_definition'] = presentation_definition
            prefix = verifier_profile["oidc4vp_prefix"]
        elif response_type == "vp_token" :
            authorization_request['presentation_definition'] = presentation_definition
            prefix = verifier_profile["oidc4vp_prefix"]
        # SIOPV2
        elif response_type == "id_token" :
            authorization_request['scope'] = 'openid'
            prefix = verifier_profile["siopv2_prefix"]
            #authorization_request['claims'] = 'not supported'

    if not verifier_data.get('request_uri') and verifier_data['profile'] in ["EBSI-V2" ] :
        authorization_request_displayed = authorization_request
    else :
        authorization_request_displayed = { 
            "client_id" : verifier_data['did'],
            "request_uri" : mode.server + "sandbox/ebsi/login/request_uri/" + stream_id 
        }
    data = { 
        "pattern": authorization_request,
        "code" : request.args['code'],
        "client_id" : client_id }
    red.setex(stream_id, QRCODE_LIFE, json.dumps(data))
    url = prefix + '?' + urlencode(authorization_request_displayed)
    deeplink_talao = mode.deeplink_talao + 'app/download/ebsi?' + urlencode({'uri' : url})
    deeplink_altme= mode.deeplink_altme + 'app/download/ebsi?' + urlencode({'uri' : url})
    qrcode_page = verifier_data.get('verifier_landing_page_style')
    return render_template(qrcode_page,
                            back_button = False,
							url=url,
                            authorization_request=json.dumps(authorization_request, indent=4),
                            url_json=json.dumps(authorization_request_displayed, indent=4),
                            client_metadata=json.dumps(client_metadata(stream_id, red), indent=4),
                            deeplink_talao=deeplink_talao,
                            deeplink_altme=deeplink_altme,
							stream_id=stream_id,
                            #application_name=verifier_data.get('application_name'),
                            #qrcode_message=verifier_data.get('qrcode_message'),
                            #mobile_message=verifier_data.get('mobile_message'),
                            #landing_page_url= verifier_data['landing_page_url'],
                            title=verifier_data['title'],
                            #terms_url= verifier_data.get('terms_url'),
                            #privacy_url=verifier_data.get('privacy_url'),
                            #company_name=verifier_data.get('company_name'),
                            page_title=verifier_data['page_title'],
                            page_subtitle=verifier_data['page_subtitle'],
                            page_description=verifier_data['page_description'],
                            #page_background_color = verifier_data['page_background_color'],
                            #page_text_color = verifier_data['page_text_color'],
                            #qrcode_background_color = verifier_data['qrcode_background_color']
                            )
    

def ebsi_request_uri(stream_id, red) :
    """
    Request by uri
    https://www.rfc-editor.org/rfc/rfc9101.html
    """
    payload = json.loads(red.get(stream_id).decode())['pattern']
    client_id = json.loads(red.get(stream_id).decode())['client_id']
    verifier_data = json.loads(read_ebsi_verifier(client_id))
    verifier_key = verifier_data['jwk']
    verifier_key = json.loads(verifier_key) if isinstance(verifier_key, str) else verifier_key
    signer_key = jwk.JWK(**verifier_key) 
    header = {
      'typ' :'JWT',
      'kid': oidc4vc.verification_method(verifier_data['did'], verifier_key),
      'alg': oidc4vc.alg(verifier_key)
    }
    token = jwt.JWT(header=header,claims=payload, algs=[oidc4vc.alg(verifier_key)])
    token.make_signed_token(signer_key)
    # https://tedboy.github.io/flask/generated/generated/flask.Response.html
    headers = { "Content-Type" : "application/oauth-authz-req+jwt",
                "Cache-Control" : "no-cache"
    }
    return Response(token.serialize(), headers=headers)



def ebsi_login_endpoint(stream_id, red):
    logging.info("Enter wallet response endpoint")
    """
    https://openid.net/specs/openid-4-verifiable-presentations-1_0.html#section-6.2
    
    """

    client_id = json.loads(red.get(stream_id).decode())['client_id']
    verifier_data = json.loads(read_ebsi_verifier(client_id))
    verifier_profile = profile[verifier_data['profile']]

    logging.info('Profile = %s', verifier_data['profile'])
    
    # prepare the verifier response to wallet
    status_code = 200
    response_format = "Unknown"
    presentation_submission_status = "Unknown"
    qrcode_status = "Unknown"
    vp_token_status = "Unknown"
    id_token_status = "Unknown"
    credential_status = "unknown"
    issuer_status = "Unknown"
    holder_did_status = "unbknown"
    access = "ok"
    vp_token_payload = {}
    id_token_payload = {}
       
    # Check qrcode expiration
    if not red.get(stream_id) :
        qrcode_status = "QR code expired"
        status_code = 400
        access = "access_denied"
    else :
        qrcode_status = "ok"
        data = json.loads(red.get(stream_id).decode())

    # get nonce and token
    if access == "ok" :
        nonce = data['pattern']['nonce']
        try :
            vp_token =request.form.get('vp_token')
            id_token = request.form.get('id_token')
            presentation_submission =request.form.get('presentation_submission')
            response_format = "ok"
            logging.info('id_token = %s', json.dumps(id_token, indent=4))
            logging.info('vp token = %s', json.dumps(vp_token, indent=4))
        except :
            response_format = "invalid request format",
            status_code = 400
            access = "access_denied"
    if not id_token :
         id_token_status = "Not received"
    if not vp_token :
         vp_token_status = "Not received"
         
    # check presentation submission
    if vp_token and verifier_data['profile'] != "EBSI-V2" :
        if not presentation_submission :
            access = "access_denied"
            presentation_submission_status = "Not found"

    # check signature of id_token if exists
    if access == "ok"  and id_token :
        try :
            oidc4vc.verif_token(id_token, nonce)
            id_token_payload = oidc4vc.get_payload_from_token(id_token)
            id_token_status = "ok"
        except :
            id_token_status = "signature check failed"
            status_code = 400
            access = "access_denied" 
    

    if access == 'ok' and vp_token :
        try :
            oidc4vc.verif_token(vp_token, nonce)
            vp_token_status = "ok"
            vp_token_payload = oidc4vc.get_payload_from_token(vp_token)
        except :
            vp_token_status = "signature check failed"
            status_code = 400
            access = "access_denied"

    
    # check wallet DID
    if access == "ok" :
        id_token_header = oidc4vc.get_header_from_token(id_token)
        jwk = id_token_header['jwk']
        kid = id_token_header['kid']
        did_wallet = oidc4vc.generate_np_ebsi_did(jwk)
        if did_wallet != kid.split('#')[0] :
            holder_did_status = "DID incorrect"
            status_code = 400
            access = "access_denied"
        else :
            holder_did_status = "ok"

    # check iss and sub
    if access == "ok" :
        if did_wallet != vp_token_payload['iss'] or did_wallet != vp_token_payload['sub'] :
            vp_token_status = "iss or sub not set correctly"
            #status_code = 400
            #access = "access_denied"
        else :
            vp_token_status = "ok"
    
    # verify issuers signatures
    if access == "ok" : 
        credential_list = vp_token_payload['vp']['verifiableCredential']
        if isinstance(credential_list, str) :
            credential_list = [credential_list]
        test = True
        for credential in credential_list :
            # Check credential signature with Issuers public key received from EBSI
            header = oidc4vc.get_header_from_token(credential)
            issuer_vm = header['kid']
            issuer_did = issuer_vm.split('#')[0]
            logging.info('issuer did = %s', issuer_did)
            pub_key = oidc4vc.get_lp_public_jwk(issuer_did,issuer_vm)
            if not pub_key :
                #test =  False
                logging.warning('Issuer not registered')
                issuer_status = 'Issuer not registered'
                break
            logging.info('EBSI issuer pub key = %s', pub_key)
            try :
                oidc4vc.verify_jwt_credential(credential, pub_key)
                issuer_status = 'Issuer is registered and signature ok'
            except :
                #test = False
                logging.warning('Signature check failed')
                issuer_status = 'Issuer signature failed'
                break
        if test :
            credential_status = "ok"
        else :
            access = "access_denied"
            status_code = 400

    response = {
      "created": datetime.timestamp(datetime.now()),
      "qrcode_status" : qrcode_status,
      "holder_did_status" : holder_did_status,
      "presentation_submission_status" : presentation_submission_status,
      "response_format" : response_format,
      "id_token_status" : id_token_status,
      "vp_token_status" : vp_token_status,
      "issuer_status" : issuer_status,
      "credential_status" : credential_status,
      "access" : access,
      "status_code" : status_code    
    }
    logging.info("response = %s",json.dumps(response, indent=4))
    # follow up
    wallet_data = json.dumps({
                    "access" : access,
                    "vp_token_payload" : vp_token_payload,
                    "sub" : id_token_payload.get('sub')
                    })
    red.setex(stream_id + "_wallet_data", CODE_LIFE, wallet_data)
    event_data = json.dumps({"stream_id" : stream_id})           
    red.publish('api_ebsi_verifier', event_data)
    return jsonify(response), status_code



def ebsi_login_followup(red):  
    """
    check if user is connected or not and redirect data to authorization server
    Prepare de data to transfer
    create activity record
    """
    logging.info("Enter follow up endpoint")
    try :
        _session = session['client_id'] # needed to check authorized session
        stream_id = request.args.get('stream_id')
    except :
        return jsonify("Forbidden"), 403 
    code = json.loads(red.get(stream_id).decode())['code']
    try :
        stream_id_wallet_data = json.loads(red.get(stream_id + '_wallet_data').decode())
    except :
        logging.error("code expired in follow up")
        resp = {'code' : code, 'error' : "access_denied"}
        session['verified'] = False
        return redirect ('/sandbox/ebsi/authorize?' + urlencode(resp))

    if stream_id_wallet_data['access'] != 'ok' :
        resp = {'code' : code, 'error' : stream_id_wallet_data['access']}
        session['verified'] = False
    else :
        session['verified'] = True
        red.setex(code +"_wallet_data", CODE_LIFE, json.dumps(stream_id_wallet_data))
        resp = {'code' : code}

    """
    verifier_data = json.loads(read_ebsi_verifier(client_id))
    
    # for activity tracking
    activity = {"presented" : datetime.now().replace(microsecond=0).isoformat() + "Z",
                "user" : stream_id_wallet_data["sub"],
                "credential_1" : verifier_data['vc'],
                "credential_2" : verifier_data.get('vc_2', "None"),
                "status" : session['verified']
    }
    activity_db_api.create(client_id, activity) 
    """
    return redirect ('/sandbox/ebsi/authorize?' + urlencode(resp))


def ebsi_login_stream(red):
    def login_event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('api_ebsi_verifier')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(login_event_stream(red), headers=headers)
