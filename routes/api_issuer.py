"""
def get_version() -> str: ...
def generate_ed25519_key() -> str: ...
def key_to_did(method_pattern: str, jwk: str) -> str: ...
async def key_to_verification_method(method_pattern: str, jwk: str) -> str: ...
async def issue_credential(credential: str, proof_options: str, key: str) -> str: ...
async def verify_credential(credential: str, proof_options: str) -> str: ...
async def issue_presentation(presentation: str, proof_options: str, key: str) -> str: ...
async def verify_presentation(presentation: str, proof_options: str) -> str: ...
async def resolve_did(did: str, input_metadata: str) -> str: ...
async def dereference_did_url(did_url: str, input_metadata: str) -> str: ...
async def did_auth(did: str, options: str, key: str) -> str: ...
"""

from flask import jsonify, request, render_template, Response, redirect, session
import json
from datetime import timedelta, datetime
import uuid
import didkit
import logging
from urllib.parse import urlencode
import requests
import db_api
from jwcrypto import jwk, jwt
import ebsi
import base64
import issuer_activity_db_api
import pyotp

logging.basicConfig(level=logging.INFO)
OFFER_DELAY = timedelta(seconds= 10*60)

try :
    ISSUER_KEY_DICT = json.load(open("/home/admin/sandbox/keys.json", "r"))['issuer_key']
except :
    ISSUER_KEY_DICT = json.load(open("/home/thierry/sandbox/keys.json", "r"))['issuer_key']

issuer_key = jwk.JWK(**ISSUER_KEY_DICT) 
public_issuer_key =  issuer_key.export(private_key=False, as_dict=True)


def init_app(app,red, mode) :
    # endpoint for application
    app.add_url_rule('/sandbox/op/issuer/<issuer_id>',  view_func=issuer_landing_page, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer_stream',  view_func=issuer_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/op/issuer_followup',  view_func=issuer_followup, methods = ['GET'])
    app.add_url_rule('/sandbox/op/login_password/<issuer_id>',  view_func=login_password, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/secret/<issuer_id>',  view_func=secret, methods = ['GET', 'POST'])

    # enpoint for siopv2 protocol with wallet
    app.add_url_rule('/sandbox/op/issuer/siopv2/<issuer_id>',  view_func=issuer_landing_page_siopv2, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer/siopv2/<issuer_id>/.well-known/openid-configuration', view_func=issuer_siopv2_openid_configuration, methods=['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer/siopv2/<issuer_id>jwks.json', view_func=issuer_siopv2_jwks, methods=['GET'])
    app.add_url_rule('/sandbox/op/issuer/siopv2/<issuer_id>/authorize',  view_func=issuer_siopv2_authorize, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/op/issuer/siopv2/<issuer_id>/token',  view_func=issuer_siopv2_token, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/op/issuer/siopv2/<issuer_id>/credential',  view_func=issuer_siopv2_credential, methods = ['GET', 'POST'], defaults={'red' :red})

    # endpoint for VC API protocol with wallet
    app.add_url_rule('/sandbox/op/issuer_endpoint/<issuer_id>/<stream_id>',  view_func=issuer_endpoint, methods = ['GET', 'POST'], defaults={'red' :red})
    return


def issuer_siopv2_jwks(issuer_id) :
    return jsonify({"keys" : [public_issuer_key]})


def issuer_siopv2_openid_configuration(issuer_id, mode):
    issuer_data = json.loads(db_api.read_issuer(issuer_id))
    oidc = {
        "issuer": mode.server + 'sandbox/op/issuer/' + issuer_id,
        "authorization_endpoint":  mode.server + 'sandbox/op/issuer/siopv2/' + issuer_id + '/authorize',
        "token_endpoint": mode.server + 'sandbox/op/issuer/siopv2/' + issuer_id + '/token',
        "credential_endpoint": mode.server + 'sandbox/op/issuer/siopv2/' + issuer_id + '/credential',
        "jwks_uri": mode.server + 'sandbox/op/issuer/siopvé/' + issuer_id + '/jwks.json',
        "scopes_supported": ["openid"],
        "response_types_supported": ["code"],
        "credential_supported" : [issuer_data['credential_to_issue']],
        "token_endpoint_auth_methods_supported": ["client_secret_basic"]
    }
    return jsonify(oidc)


def update_credential_manifest(reason, credential_requested, credential_manifest) :
    input_descriptor = {"id": str(uuid.uuid1()),
                        "purpose" : reason,
                        "constraints": {
                            "fields": [
                                {"path": ["$.type"],
                                "filter": {"type": "string",
                                            "pattern": credential_requested}
                                }]}}
    credential_manifest['presentation_definition']['input_descriptors'].append(input_descriptor)
    return credential_manifest


def update_credential_manifest_all_address(reason, credential_manifest) :
    input_descriptor = {"id": str(uuid.uuid1()),
                        "purpose" : reason,
                        "constraints": {
                            "fields": [
                                {"path": ["$.credentialSubject.associatedAddress"]}
                                ]}}
    credential_manifest['presentation_definition']['input_descriptors'].append(input_descriptor)
    return credential_manifest


def login_password(issuer_id) :
    if request.method == 'GET' :
        try :
            issuer_data = json.loads(db_api.read_issuer(issuer_id))
        except :
            logging.error('issuer id not found')
            return render_template('op_issuer_removed.html')
        return render_template ('login_password.html',
            issuer_id=issuer_id,
            page_title=issuer_data['page_title'],
            page_subtitle=issuer_data['page_subtitle'],
            page_description=issuer_data['page_description'],
            title=issuer_data['title'],
            qrcode_message=issuer_data['qrcode_message'],
            landing_page_url=issuer_data['landing_page_url'],
            privacy_url=issuer_data['privacy_url'],
            terms_url=issuer_data['terms_url'],
            mobile_message=issuer_data['mobile_message'],
            page_background_color = issuer_data['page_background_color'],
            page_text_color = issuer_data['page_text_color'],
            qrcode_background_color = issuer_data['qrcode_background_color'])
    if request.method == 'POST' :
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        session['login_password'] = True
        return redirect('/sandbox/op/issuer/' + issuer_id)

# secret and TOTP case
def secret(issuer_id) :
    try :
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
    except :
        logging.error('issuer id not found')
        return render_template('op_issuer_removed.html')
    if request.method == 'GET' :
        if issuer_data['credential_requested'] == 'totp' and request.args.get('totp') :
            totp = pyotp.TOTP(issuer_data.get('secret'), interval=int(issuer_data.get("totp_interval", "30")))
            if  totp.verify(request.args['totp']) :
                session['login_secret'] = True
                return redirect('/sandbox/op/issuer/' + issuer_id)
            else :
                logging.warning('TOTP secret is incorrect')
                session.clear()
                return render_template('secret_access_denied.html', next=issuer_data['callback'])
        return render_template ('secret.html',
            issuer_id=issuer_id,
            page_title=issuer_data['page_title'],
            page_subtitle=issuer_data['page_subtitle'],
            page_description=issuer_data['page_description'],
            title=issuer_data['title'],
            qrcode_message=issuer_data['qrcode_message'],
            landing_page_url=issuer_data['landing_page_url'],
            privacy_url=issuer_data['privacy_url'],
            terms_url=issuer_data['terms_url'],
            mobile_message=issuer_data['mobile_message'],
            page_background_color = issuer_data['page_background_color'],
            page_text_color = issuer_data['page_text_color'],
            qrcode_background_color = issuer_data['qrcode_background_color'])
    if request.method == 'POST' :
        if issuer_data['credential_requested'] == 'totp' :
            totp = pyotp.TOTP(issuer_data.get('secret', "base32secret3232"), interval=int(issuer_data.get("totp_interval", "30")))
            if  totp.verify(request.form['secret']) :
                session['login_secret'] = True
                logging.info('TOTP secret is correct')
                return redirect('/sandbox/op/issuer/' + issuer_id)
            logging.warning('secret is incorrect')
            session.clear()
            return render_template('secret_access_denied.html', next=issuer_data['callback'])
        else :
            if  request.form['secret'] == issuer_data.get('secret') :
                session['login_secret'] = True
                return redirect('/sandbox/op/issuer/' + issuer_id)
            logging.warning('secret is incorrect')
            session.clear()
            return render_template('secret_access_denied.html', next=issuer_data['callback'])
           

def issuer_landing_page(issuer_id, red, mode) :
    session['is_connected'] = True
    try :
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
    except :
        logging.error('issuer id not found')
        return render_template('op_issuer_removed.html')
    
    # redirectt to siopv2 landing page 
    if issuer_data['protocol'] in ["siopv2", "siopv2_openid"] :
        redirect_uri = '/sandbox/op/issuer/siopv2/' + issuer_id
        if request.args.get('id') :
            redirect_uri = redirect_uri + '?id=' +  request.args.get('id')
        return redirect(redirect_uri)

    if issuer_data['credential_requested'] == "login" and not session.get('login_password') :
        session['issuer_id'] = issuer_id
        return redirect('/sandbox/op/login_password/' + issuer_id)
    
    if issuer_data['credential_requested'] in ["secret", "totp"] and not session.get('login_secret') :
        session['issuer_id'] = issuer_id
        if issuer_data['credential_requested'] == "totp" and request.args.get('totp') :
            return redirect('/sandbox/op/secret/' + issuer_id + "?totp=" + request.args['totp'])
        return redirect('/sandbox/op/secret/' + issuer_id )
    
    credential = json.load(open('./verifiable_credentials/' + issuer_data['credential_to_issue'] + '.jsonld'))
    credential['id'] = "urn:uuid:" + str(uuid.uuid1())
    credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
    credential["issuer"] ="did:ebsi:"
    credential["credentialSubject"]['id'] ="did:example:xxxxx:"
    
    try :
        credential_manifest = json.load(open('./credential_manifest/' + issuer_data['credential_to_issue'] + '_credential_manifest.json'))
    except :
        logging.error('credential manifest not found or error %s', issuer_data['credential_to_issue'])
        return render_template('op_issuer_removed.html')
    if issuer_data['method'] == "ebsi" :
        issuer_did =  issuer_data['did_ebsi']
    elif issuer_data['method'] == "relay" :
        issuer_did = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
    else : 
        issuer_did = didkit.key_to_did(issuer_data['method'], issuer_data['jwk'])
    # update credential manifest
    credential_manifest['id'] = str(uuid.uuid1())
    credential_manifest['output_descriptors'][0]['id'] = str(uuid.uuid1())
    credential_manifest['output_descriptors'][0]['schema'] = "https://github.com/TalaoDAO/wallet-tools/blob/main/test/CredentialOffer2/" + issuer_data['credential_to_issue'] + '.jsonld'
    credential_manifest['output_descriptors'][0]['display']['title']['fallback'] = issuer_data['card_title']
    credential_manifest['output_descriptors'][0]['display']['subtitle']['fallback'] = issuer_data['card_subtitle']
    credential_manifest['output_descriptors'][0]['display']['description']['fallback'] = issuer_data['card_description']
    credential_manifest['output_descriptors'][0]['styles'] = {
            'background' : {'color' : issuer_data['card_background_color']},
            'text' : { 'color' : issuer_data['card_text_color']}}
    
    credential_manifest['issuer']['id'] = issuer_did
    credential_manifest['issuer']['name'] = issuer_data['company_name']
    if issuer_data['credential_requested'] in ["DID", "login", "secret", "totp"] and issuer_data['credential_requested_2'] in ["DID", "login", "secret", "totp"] : # No credential 2 requested to issue 
        credential_manifest['presentation_definition'] = dict()
    else :
        credential_manifest['presentation_definition'] = {"id": str(uuid.uuid1()), "input_descriptors": list()}    

        if issuer_data['credential_requested'] == "AllAddress" :
            credential_manifest = update_credential_manifest_all_address(issuer_data['reason'], credential_manifest)
        elif issuer_data['credential_requested'] not in ["DID", "login", "secret", "totp"] :
            credential_manifest = update_credential_manifest(issuer_data['reason'], issuer_data['credential_requested'], credential_manifest)
        
        if issuer_data['credential_requested_2'] == "AllAddress" :
            credential_manifest = update_credential_manifest_all_address(issuer_data['reason'], credential_manifest)
        elif issuer_data.get('credential_requested_2', 'DID') not in ["DID", "login", "secret", "totp"] : 
            credential_manifest = update_credential_manifest(issuer_data['reason_2'], issuer_data['credential_requested_2'], credential_manifest)

        if issuer_data['credential_requested_3'] == "AllAddress" :
            credential_manifest = update_credential_manifest_all_address(issuer_data['reason'], credential_manifest)
        elif issuer_data.get('credential_requested_3', 'DID') not in ["DID", "login", "secret", "totp"] :  
            credential_manifest = update_credential_manifest(issuer_data['reason_3'], issuer_data['credential_requested_3'], credential_manifest)

        if issuer_data['credential_requested_4'] == "AllAddress" :
            credential_manifest = update_credential_manifest_all_address(issuer_data['reason'], credential_manifest)
        elif issuer_data.get('credential_requested_4', 'DID') not in ["DID", "login", "secret", "totp"] :  
            credential_manifest = update_credential_manifest(issuer_data['reason_4'], issuer_data['credential_requested_4'], credential_manifest)

    if not request.args.get('id') :
        logging.warning("no id passed by application")

    credentialOffer = {
        "id" : request.args.get('id'),
        "type": "CredentialOffer",
        "challenge" : str(uuid.uuid1()),
        "domain" : "https://altme.io",
        "credentialPreview": credential,
        "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
        "credential_manifest" : credential_manifest
    }   
    stream_id = str(uuid.uuid1())
    # TODO
    issuer_did = "did:tz:tz1NyjrTUNxDpPaqNZ84ipGELAcTWYg6s5Du"
    url = mode.server + "sandbox/op/issuer_endpoint/" + issuer_id + '/' + stream_id + '?issuer=' + issuer_did 
    deeplink_altme = mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url })
    red.setex(stream_id, 180, json.dumps(credentialOffer))
    if issuer_data['credential_requested'] == "login" :
        red.setex(stream_id + "_login", 180, json.dumps({"username" : session['username'],
                                                         "password" : session["password"]
                                                         } ))
    if not issuer_data.get('landing_page_style') :
        qrcode_page = "op_issuer_qrcode_2.html"
    else : 
        qrcode_page = issuer_data.get('landing_page_style')
  
    return render_template(qrcode_page,
                                url=url,
                                deeplink_altme=deeplink_altme,
                                stream_id=stream_id,
                                issuer_id=issuer_id,
                                page_title=issuer_data['page_title'],
                                page_subtitle=issuer_data['page_subtitle'],
                                page_description=issuer_data['page_description'],
                                title=issuer_data['title'],
                                qrcode_message=issuer_data['qrcode_message'],
                                landing_page_url=issuer_data['landing_page_url'],
                                privacy_url=issuer_data['privacy_url'],
                                terms_url=issuer_data['terms_url'],
                                mobile_message=issuer_data['mobile_message'],
                                page_background_color = issuer_data['page_background_color'],
                                page_text_color = issuer_data['page_text_color'],
                                qrcode_background_color = issuer_data['qrcode_background_color'],
                                )


def issuer_landing_page_siopv2(issuer_id, red, mode) :
    # https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-issuance-initiation-request
    issuer_data = json.loads(db_api.read_issuer(issuer_id))
    if issuer_data.get('pre_authorized_code') and not request.args.get('id') :
        logging.error("Pre authorized code missing")
        return jsonify("Pre authorized code missing")

    stream_id = str(uuid.uuid1())
    op_stat = str(uuid.uuid1())
    if not issuer_data.get('landing_page_style') :
        qrcode_page = "op_issuer_qrcode_2.html"
    else : 
        qrcode_page = issuer_data.get('landing_page_style')
    if issuer_data['protocol'] == "siopv2_openid" :
        url_data  = { 
            "issuer" : mode.server +'sandbox/op/issuer/siopv2/' + issuer_id,
            "credentials": [ issuer_data['credential_to_issue']],
            "op_stat" : op_stat
        }
    if issuer_data['protocol'] == "siopv2" :
        url_data  = { 
            "issuer" : mode.server +'sandbox/op/issuer/siopv2/' + issuer_id,
            "credential_type"  : issuer_data['credential_to_issue'],
            "op_stat" : op_stat
        }
    if issuer_data.get('pre_authorized_code') == "poc" and issuer_data['protocol'] == "siopv2_openid" :
        url_data["pre_authorized_code"] = request.args.get('id', 'not_indicated')
        url_data["user_pin_required"]= False
    
    if issuer_data.get('pre_authorized_code') == "poc_pin" and issuer_data['protocol'] == "siopv2_openid" :
        url_data["pre_authorized_code"] = request.args.get('id', 'not_indicated')
        url_data["user_pin_required"]= True
        
    url = "openid://initiate_issuance?" + urlencode(url_data)
    logging.info("qrcode = %s", url)
    return render_template(qrcode_page,
                                url=url,
                                deeplink_altme="",
                                stream_id=stream_id,
                                issuer_id=issuer_id,
                                page_title=issuer_data['page_title'],
                                page_subtitle=issuer_data['page_subtitle'],
                                page_description=issuer_data['page_description'],
                                title=issuer_data['title'],
                                qrcode_message=issuer_data['qrcode_message'],
                                landing_page_url=issuer_data['landing_page_url'],
                                privacy_url=issuer_data['privacy_url'],
                                terms_url=issuer_data['terms_url'],
                                mobile_message=issuer_data['mobile_message'],
                                page_background_color = issuer_data['page_background_color'],
                                page_text_color = issuer_data['page_text_color'],
                                qrcode_background_color = issuer_data['qrcode_background_color'],
                                )


def issuer_siopv2_authorize(issuer_id, red) :
    def manage_error_request(msg) :
        resp = {'error' : msg}
        return redirect(request.args['redirect_uri'] + '?' +urlencode(resp))    
    try :
        data = {
            'client_id' : request.args['client_id'],
            'scope' : request.args.get('scope'),
            'state' : request.args.get('state'),
            'response_type' : request.args['response_type'],
            'redirect_uri' : request.args['redirect_uri'],
            'nonce' : request.args.get('nonce'),
            #'code_challenge' : request.args.get('code_challenge'),
            #'code_challenge_method' : request.args.get('code_challenge_method'),
            "expires" : datetime.timestamp(datetime.now()) + 180
        }
    except :
        logging.warning('invalid request received in authorization server')
        return manage_error_request("invalid_request_object")

    if not db_api.read_issuer(issuer_id) :
        logging.warning('issuer_id not found in data base')
        return manage_error_request("invalid_request")
    
    issuer_data = json.loads(db_api.read_issuer(issuer_id))

    if request.args['response_type'] != "code" :
        logging.warning('unsupported response type %s', request.args['response_type'])
        return manage_error_request("unsupported_response_type")
    
    try :
        credential_type = json.loads(request.args['authorization_details'])[0]['credential_type']
    except :
        return manage_error_request("invalid_request")

    if credential_type != issuer_data["credential_to_issue"] :
        logging.warning('credential type %s does not match', request.args['response_type'])
        return manage_error_request("unsupported_credential_type")

    # creation grant (code) and redirect to callback
    code = str(uuid.uuid1())
    red.setex(code, 180, json.dumps(data))
    resp = {'code' : code}
    if request.args.get('state') :
        resp['state'] = request.args.get('state')
    return redirect(issuer_data['callback'] + '?' + urlencode(resp))
   

def issuer_siopv2_token(issuer_id, red) :
     #https://datatracker.ietf.org/doc/html/rfc6749#section-5.2
    logging.info("token endpoint request = %s", request.form)

    def manage_error (msg) :
        logging.warning(msg)
        endpoint_response= {"error": msg}
        headers = {'Content-Type': 'application/json'}
        return Response(response=json.dumps(endpoint_response), status=400, headers=headers)
        
    try :
        #token = request.headers['Authorization']
        #token = token.split(" ")[1]
        #token = base64.b64decode(token).decode()
        #client_secret = token.split(":")[1]
        #client_id = token.split(":")[0]
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
        grant_type =  request.form['grant_type']
        code = request.form['code']
        #redirect_uri = request.form['redirect_uri']
    except :
        return manage_error("invalid_request")
    try :
        data = json.loads(red.get(code).decode())
    except :
        return manage_error("invalid_grant")     
    if grant_type != 'authorization_code' :
        return manage_error("unhauthorized_client")

    # token response
    access_token = str(uuid.uuid1())
    endpoint_response = {
                        "access_token" : access_token,
                        "c_nonce" : str(uuid.uuid1()),
                        "token_type" : "Bearer",
                        "expires_in": 1000
                        }
    red.delete(code)
    red.setex(access_token, 1000,json.dumps({"issuer_id" : issuer_id}))
    headers = {
        "Cache-Control" : "no-store",
        "Pragma" : "no-cache",
        'Content-Type': 'application/json'}
    return Response(response=json.dumps(endpoint_response), headers=headers)
 

def issuer_siopv2_credential(issuer_id, red) :
    access_token = request.headers["Authorization"].split()[1]
    try :
        data = json.loads(red.get(access_token).decode())
    except :
        logging.warning("access token expired")
        headers = {'WWW-Authenticate' : 'Bearer realm="userinfo", error="invalid_token", error_description = "The access token expired"'}
        return Response(status=401,headers=headers)

    if data['issuer_id'] != issuer_id :
        logging.warning("access token does not match")
        headers = {'WWW-Authenticate' : 'Bearer realm="userinfo", error="invalid_token", error_description = "The access token expired"'}
        return Response(status=401,headers=headers)

    result = request.json
    try :
        type = result['type']
        format = result['format']
        proof = result['proof']
        jwt = proof['jwt']
    except :
        logging.warning("invalid request data")
        headers = {'WWW-Authenticate' : 'Bearer realm="userinfo", error="invalid_request", error_description = "The data format is incorect"'}
        return Response(status=401,headers=headers)
    payload = { "credential" : "test"}
    headers = {
        "Cache-Control" : "no-store",
        "Pragma" : "no-cache",
        "Content-Type": "application/json"}
    return Response(response=json.dumps(payload), headers=headers)
  

############################################################################################""

async def issuer_endpoint(issuer_id, stream_id, red):
    try : 
        credentialOffer = red.get(stream_id).decode()
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
    except :
        logging.error("red.get(id) errorn offer expired")
        data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Offer expired"})
        red.publish('op_issuer', data)
        return jsonify("Unauthorized"),400 
    
    # wallet GET
    if request.method == 'GET':
        return jsonify(credentialOffer)
                        
    # wallet POST
    if request.method == 'POST':
        if not issuer_data :
            logging.error("Unhauthorized")
            data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Offer expired"})
            red.publish('op_issuer', data)
            return jsonify("Unauthorized"),400  
     
        # send data to application webhook to get the credential data
        data_received = dict()
        if issuer_data.get('standalone', None) == 'on' :
            headers = {
                    "key" : issuer_data['client_secret'],
                    "Content-Type": "application/json" 
                    }       
            url = issuer_data['webhook']
            payload = { 'event' : 'ISSUANCE',
                    'vp': json.loads(request.form['presentation']),
                    "id": request.form.get('id')
                    }
            if issuer_data['credential_requested'] == 'login' :
                user_pass = json.loads(red.get(stream_id + "_login").decode())
                usrPass = (user_pass['username'] + ':' + user_pass['password']).encode()
                b64Val = base64.b64encode(usrPass) 
                headers["Authorization"] = "Basic " + b64Val.decode()

            r = requests.post(url,  data=json.dumps(payload), headers=headers)
            if not 199<r.status_code<300 :
                logging.error('issuer failed to call application, status code = %s', r.status_code)
                data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Issuer failed to call application"})
                red.publish('op_issuer', data)
                return jsonify("application error"),500    
            logging.info('status code ok')
        
            try :
                data_received = r.json()
            except :
                logging.error('aplication data are not json')
                data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Application data received are not json format"})
                red.publish('op_issuer', data)
                return jsonify("application error"),500

            # If credential is signed by external issuer
            if issuer_data['method'] == "relay" :
                # send event to front to go forward callback
                data = json.dumps({'stream_id' : stream_id,"result" : True})
                red.publish('op_issuer', data)
                logging.info('credential signed by external signer')
                return jsonify(data_received)

        # get credential   
        credential =  json.loads(credentialOffer)['credentialPreview']

        # If needed extract data sent by application and merge them with verifiable credential data
        if data_received and issuer_data.get('standalone', None) == 'on' :
            credential["credentialSubject"] = data_received
            logging.info("Data received from application added to credential")

        # set basic credential attributes
        credential['id'] = "urn:uuid:" + str(uuid.uuid4())
        credential['credentialSubject']['id'] = request.form['subject_id']
        credential['credentialSubject']['type'] = issuer_data['credential_to_issue']
        credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
        duration = issuer_data.get('credential_duration', "365")
        credential['expirationDate'] =  (datetime.now().replace(microsecond=0) + timedelta(days= int(duration))).isoformat() + "Z"
        
        # fill Pass number in credential
        if issuer_data['credential_to_issue'] == 'Pass' :
            credential['credentialSubject']['issuedBy']['name'] = issuer_data.get('company_name', 'Not indicated')
            credential['credentialSubject']['issuedBy']['issuerId'] = issuer_id
        
        #TODO
        # for EBSI demo with VerifiableDiploma and VerifiableId type
        try :
            presentation_list = json.loads(request.form['presentation'])
            if isinstance(presentation_list, dict) :
                presentation_list = [presentation_list] 
            for presentation in presentation_list :     
                if issuer_data['credential_to_issue'] == "VerifiableDiploma" and presentation['verifiableCredential']['credentialSubject']['type'] == 'VerifiableId' :
                    credential['credentialSubject']['firstName'] = presentation['verifiableCredential']['credentialSubject']['firstName']
                    credential['credentialSubject']['familyName'] = presentation['verifiableCredential']['credentialSubject']['familyName']
                    credential['credentialSubject']['dateOfBirth'] = presentation['verifiableCredential']['credentialSubject']['dateOfBirth']
                    break
        except :
            logging.info("EBSI demo problem")

        # sign credential
        if issuer_data['method'] == "ebsi" :
            logging.warning("EBSI issuer")
            credential["issuer"] = issuer_data['did_ebsi']
            signed_credential = ebsi.lp_sign(credential, issuer_data['jwk'], issuer_data['did_ebsi'])
            logging.info("credential signed by EBSI")
        else :
            credential["issuer"] = didkit.key_to_did(issuer_data['method'], issuer_data['jwk'])  
            didkit_options = {
                "proofPurpose": "assertionMethod",
                "verificationMethod": await didkit.key_to_verification_method(issuer_data['method'], issuer_data['jwk'])
            }
            try :
                signed_credential =  await didkit.issue_credential(
                    json.dumps(credential),
                    didkit_options.__str__().replace("'", '"'),
                    issuer_data['jwk']
                )
            except :
                message = 'Signature failed'
                logging.error(message)
                data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : message})
                red.publish('op_issuer', data)
                return jsonify("server error, signature failed"),500                
            logging.info('signature ok')
       
        # transfer credential signed and credential recieved to application
        headers = {
            "key" : issuer_data['client_secret'],
            "Content-Type": "application/json" 
        }      
        url = issuer_data['webhook']
        payload = { 
            'event' : 'SIGNED_CREDENTIAL',
            'vc': json.loads(signed_credential),
            'vp' : json.loads(request.form['presentation']),
            "id": request.form.get('id')
        }
        r = requests.post(url,  data=json.dumps(payload), headers=headers)
        if not 199<r.status_code<300 :
            logging.error('issuer failed to send signed credential to application, status code = %s', r.status_code)
        else :
            logging.info('signed credential sent to application')
        
        # send event to front to go forward callback and send credential to wallet
        data = json.dumps({'stream_id' : stream_id,"result" : True})
        red.publish('op_issuer', data)
        
        # record activity
        activity = {"presented" : datetime.now().replace(microsecond=0).isoformat() + "Z",
                "wallet_did" : request.form['subject_id'],
                "vp" : json.loads(request.form['presentation'])
        }
        issuer_activity_db_api.create(issuer_id, activity) 

        # send VC to wallet
        return jsonify(signed_credential)
        

def issuer_followup():  
    if not session.get('is_connected') :
        logging.error('user is not connectd')
        return render_template('op_issuer_removed.html',next = issuer_data['issuer_landing_page'])
    session.clear()
    issuer_id = request.args.get('issuer_id')
    issuer_data = json.loads(db_api.read_issuer(issuer_id))
    if request.args.get('message') :
        return render_template('op_issuer_failed.html', next = issuer_data['issuer_landing_page'])
    try :
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
    except :
        return render_template('op_issuer_removed.html',next = issuer_data['issuer_landing_page'])
    return redirect (issuer_data['callback'])
    
    
# server event push for user agent EventSource
def issuer_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('op_issuer')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()  
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)



