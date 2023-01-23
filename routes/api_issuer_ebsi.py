"""
https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-response


"""


from flask import jsonify, request, render_template, Response, redirect, session
import json
from datetime import timedelta, datetime
import uuid
import logging
from urllib.parse import urlencode
import db_api
from jwcrypto import jwk, jwt
import ebsi
import base64
import issuer_activity_db_api
import pyotp
import base58
import os
import ebsi
import copy

from op_constante_ebsi import ebsi_credential_to_issue_list

logging.basicConfig(level=logging.INFO)

ACCESS_TOKEN_LIFE = 1000
GRANT_LIFE = 180
C_NONCE_LIFE = 1000

CRYPTOGRAPHIC_SUITES = ['ES256K','ES256','ES384','ES512','RS256']
#DID_METHODS = ["did:ebsi","did:key","did:tz","did:pkh","did:ethr","did:web"]
DID_METHODS = ["did:ebsi"]


def init_app(app,red, mode) :
    # endpoint for application
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>',  view_func=ebsi_issuer_landing_page, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/issuer_stream',  view_func=ebsi_issuer_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/ebsi/issuer_followup',  view_func=ebsi_issuer_followup, methods = ['GET'])
    
    # EBSI protocol with wallet
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>/.well-known/openid-configuration', view_func=ebsi_issuer_openid_configuration, methods=['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>/authorize',  view_func=ebsi_issuer_authorize, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>/token',  view_func=ebsi_issuer_token, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>/credential',  view_func=ebsi_issuer_credential, methods = ['GET', 'POST'], defaults={'red' :red})
    return


def ebsi_issuer_openid_configuration(issuer_id, mode):
    return jsonify(oidc(issuer_id, mode))

def oidc(issuer_id, mode) :
    """
    Attention for EBSI "types" = id of data model
    https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#section-10.2.3
    """
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id)) 
    
    # credential manifest
    #https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-server-metadata
    file_path = './credential_manifest/' + ebsi_credential_to_issue_list.get(issuer_data['credential_to_issue']) + '_credential_manifest.json'
    credential_manifest = [json.load(open(file_path))]
    credential_manifest[0]['issuer']['id'] = issuer_data['did_ebsi']
    credential_manifest[0]['issuer']['name'] = issuer_data['application_name']
    
    #credential supported
    credential_supported = [{
                        'format': 'jwt_vc',
                        'id': ebsi_credential_to_issue_list.get(issuer_data['credential_to_issue'], 'unknown id') ,
                        'types':  issuer_data['credential_to_issue'],
                        "display": [
                            {
                                "name": issuer_data['company_name'],
                                "locale": "en-US",
                                #"logo": {
                                #    "url": "https://exampleuniversity.com/public/logo.png",
                                #    "alternative_text": "a square logo of a university"
                                #},
                                #"background_color": "#12107c",
                                #"text_color": "#FFFFFF"
                            }
                        ],
                        'cryptographic_binding_methods_supported': [
                            'did'
                        ],
                        'cryptographic_suites_supported': CRYPTOGRAPHIC_SUITES
        }]
    
    openid_configuration = {
        'credential_issuer': mode.server + 'sandbox/ebsi/issuer/' + issuer_id,
        'authorization_endpoint':  mode.server + 'sandbox/ebsi/issuer/' + issuer_id + '/authorize',
        'token_endpoint': mode.server + 'sandbox/ebsi/issuer/' + issuer_id + '/token',
        'credential_endpoint': mode.server + 'sandbox/ebsi/issuer/' + issuer_id + '/credential',
        'batch_credential_endpoint' : None,
        'pre-authorized_grant_anonymous_access_supported' : False,
        "subject_syntax_types_supported": DID_METHODS,
        'credential_supported' : credential_supported,
        'credential_manifests' : credential_manifest,
    }
    return openid_configuration


# initiate endpoint with QRcode
def ebsi_issuer_landing_page(issuer_id, red, mode) :
    """
    see EBSI specs as OpenID siopv2 for issuance has changed

    https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-issuance-initiation-request

    openid://initiate_issuance
    ?issuer=http%3A%2F%2F192.168.0.65%3A3000%2Fsandbox%2Febsi%2Fissuer%2Fhqplzbjrhg
    &credential_type=Pass
    &op_stat=40fd65cf-98ba-11ed-957d-512a313adf23

    """
    logging.info('Issuer openid-configuration = %s', mode.server + '/sandbox/ebsi/issuer/' + issuer_id + '/.well-known/openid-configuration' )

    session['is_connected'] = True
    try :
        issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    except :
        logging.error('issuer id not found')
        return render_template('op_issuer_removed.html')
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))

    issuer_state = stream_id = str(uuid.uuid1())
    qrcode_page = issuer_data.get('landing_page_style')
    # Option 1 https://api-conformance.ebsi.eu/docs/wallet-conformance/issue
    url_data  = { 
        'issuer' : mode.server +'sandbox/ebsi/issuer/' + issuer_id,
        'credential_type'  : issuer_data['credential_to_issue'],
        'issuer_state' : issuer_state
    }
    url = 'openid://initiate_issuance?' + urlencode(url_data)
    """
    # Option 2 OpenID
    url_data = {
        "credential_issuer": mode.server +'sandbox/ebsi/issuer/' + issuer_id,
        "credentials": [
            {
                "format": "jwt_vc_json",
                "types": [issuer_data['credential_to_issue']
                ]
            }
        ]
    }
    url = 'openid-credential-offer://credential_offer=' + urlencode(url_data)
    """
    logging.info('qrcode = %s', url)
    openid_configuration  = json.dumps(oidc(issuer_id, mode), indent=4)

    return render_template(
        qrcode_page,
        openid_configuration = openid_configuration,
        url_data = json.dumps(url_data,indent = 6),
        url=url,
        deeplink_altme='',
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

def ebsi_issuer_authorize(issuer_id, red) :
    """
      my_request = {
        'scope' : 'openid',
        'client_id' : 'https://wallet.com/callback',
        'response_type' : 'code',
        'authorization_details' : json.dumps([{'type':'openid_credential',
                        'credential_type': credential_type,
                        'format':'jwt_vc'}]),
        'redirect_uri' :  ngrok + '/callback',
        'state' : '1234',
        'issuer_state' : 'mlkmlkhm'
        }
    """
    
    def manage_error (error, error_description) :
        """
        error=invalid_request
        &error_description=Unsupported%20response_type%20value
        https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-authorization-error-respons
        https://www.rfc-editor.org/rfc/rfc6749.html#page-26
        """
        logging.warning(error_description)
        resp = {
            'error_description' : error_description,
            'error' : error
        }
        return redirect(redirect_uri + '?' + urlencode(resp))

    try :
        client_id = request.args['client_id']
        redirect_uri = request.args['redirect_uri']
    except :
        return jsonify("invalid_request"), 400
    
    try :
        scope = request.args['scope']
    except :
        return manage_error("invalid_request", "scope is missing")
    
    issuer_state = request.args.get('issuer_state')
    if not issuer_state :
        logging.warning("invalid_request", "issuer state is missing")
    
    try :
        response_type = request.args['response_type']
    except :
        return manage_error("invalid_request", "reponse_type is missing")
    
    try :
        authorization_details = request.args['authorization_details']
    except :
        return manage_error("invalid_request", "authorization_detail is missing")
    
    try :
        credential_type = json.loads(request.args['authorization_details'])[0]['credential_type']
    except :
        return manage_error("invalid_request", "credential_type is missing")
    
    try :
        format = json.loads(request.args['authorization_details'])[0]['format']
    except :
        return manage_error("invalid_request", "format is missing")

    if not db_api.read_ebsi_issuer(issuer_id) :
        return manage_error("unauthorized_client", "issuer_id not found in data base")
    
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))

    if scope != 'openid' :
        return manage_error("invalid_scope", "unsupported scope")
    if response_type != 'code' :
        return manage_error("unsupported_response_type", "unsupported response type")
    if credential_type != issuer_data['credential_to_issue'] :
        return manage_error("invalid_request", "unsupported credential type")
    if format not in ['jwt_vc', 'jwt_vc_json'] :
        return manage_error("invalid_request", "unsupported format")

    # Code creation
    code = str(uuid.uuid1())
    logging.info('code grant = %s', code)

    data = {
        'client_id' : client_id,
        'scope' : scope,
        'state' : request.args.get('state'),
        'response_type' : response_type,
        'redirect_uri' : redirect_uri,
        'nonce' : request.args.get('nonce'),
        'authorization_details' : authorization_details,
        'credential_type' : credential_type,
        'format' : format,
        # TODO PKCE
        #'code_challenge' : request.args.get('code_challenge'), 
        #'code_challenge_method' : request.args.get('code_challenge_method'),
        'expires' : datetime.timestamp(datetime.now()) + GRANT_LIFE
    }
    # for dynamic credential request register Altme wallet
    # https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-dynamic-credential-request
    # default altme authorization_endpoint =  'https://app.altme.io/app/authorize' 
    if not request.args.get('wallet_issuer') :
        data['wallet_issuer'] = 'https://app.altme.io/app/issuer'
    else :
        data['wallet_issuer'] = request.args['wallet_issuer']
    if not request.args.get('user_hint') :
        data['user_hint'] = str(uuid.uuid1())
    else :
        data['user_hint'] = request.args['user_hint']
    
    code_data = copy.deepcopy(data)
    code_data['issuer_state'] = issuer_state
    red.setex(code, GRANT_LIFE, json.dumps(code_data))    
    
    resp = {'code' : code}
    if request.args.get('state') :
        resp['state'] = request.args['state']
    return redirect(redirect_uri + '?' + urlencode(resp))
   
def manage_error(error, error_description) :
        # https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-error-response
        logging.warning(error_description)   
        payload = {
            "error" : error,
            "error_description" : error_description
        }
        headers = {
            'Cache-Control' : 'no-store',
            'Content-Type': 'application/json'}
        return {"response" : json.dumps(payload), "status" : 400, "headers" : headers}

# token endpoint
def ebsi_issuer_token(issuer_id, red) :
     #https://datatracker.ietf.org/doc/html/rfc6749#section-5.2
    logging.info("token endpoint request = %s", request.form)

    try :
        #token = request.headers['Authorization']
        #token = token.split(" ")[1]
        #token = base64.b64decode(token).decode()
        #client_secret = token.split(":")[1]
        #client_id = token.split(":")[0]
        issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
        grant_type =  request.form['grant_type']
        code = request.form['code']
        #redirect_uri = request.form['redirect_uri']
    except :
        return Response(**manage_error("invalid_request", "Request format is incorrect"))

    try :
        data = json.loads(red.get(code).decode())
    except :
        return Response(**manage_error("invalid_grant", "Code expired"))     
    
    if grant_type != 'authorization_code' :
        return Response(**manage_error("invalid_grant", "Authorization code not supported"))

    # token response
    access_token = str(uuid.uuid1())
    endpoint_response = {
        'access_token' : access_token,
        'c_nonce' : str(uuid.uuid1()),
        'token_type' : 'Bearer',
        'expires_in': ACCESS_TOKEN_LIFE
    }
    
    token_endpoint_data = {
        'access_token' : access_token,
        'c_nonce' : endpoint_response['c_nonce'],
        'access_token_expires_in': ACCESS_TOKEN_LIFE,
        'code' : code,
        "client_id" : data['client_id'],
        "issuer_id" : issuer_id,
        "credential_type" : data['credential_type'],
        'issuer_state' : data['issuer_state']
    }
    print('token endpoint data =', token_endpoint_data)
    red.setex(access_token, ACCESS_TOKEN_LIFE,json.dumps(token_endpoint_data))

    headers = {
        'Cache-Control' : 'no-store',
        'Content-Type': 'application/json'}
    return Response(response=json.dumps(endpoint_response), headers=headers)
 

# credential endpoint
def ebsi_issuer_credential(issuer_id, red) :
    
    # Check access token
    try :
        access_token = request.headers['Authorization'].split()[1]
    except :
        return Response(**manage_error('invalid_token', 'Access token not passed in request header'))
    try :
        access_token_data = json.loads(red.get(access_token).decode())
    except :
        return Response(**manage_error('invalid_token', 'Access token expired')) 
    if access_token_data['issuer_id'] != issuer_id :
        return Response (**manage_error('invalid_token', 'Access token does not match with issuer')) 
    
    # Check request 
    result = request.json
    try :
        credential_type = result['type']
        proof_format = result['format']
        proof_type  = result['proof']['proof_type']
        proof = result['proof']['jwt']
    except :
        return Response(**manage_error('invalid_request', 'Invalid request format')) 
    if credential_type != access_token_data['credential_type'] :
        return Response(**manage_error('unsupported_credential_tyoe', 'The credential type is not supported')) 
    if proof_format != 'jwt_vc' :
        return Response(**manage_error('unsupported_credential_format', 'The proof format is not supported')) 
    if proof_type != 'jwt' :
        return Response(**manage_error('invalid_or_missing_proof ', 'The proof type is not supported')) 

    # Get holder pub key from holder wallet and verify proof
    proof_header = json.loads(base64.urlsafe_b64decode(proof.split('.')[0]).decode())
    proof_payload = json.loads(base64.urlsafe_b64decode(proof.split('.')[1]).decode())
    holder_did = proof_payload['iss']
    holder_jwk = proof_header['jwk']
    try :
        ebsi.verif_proof_of_key (holder_jwk, proof)
    except :
        return Response(**manage_error('invalid_or_missing_proof ', 'The proof check failed')) 

    # TODO Build JWT VC and sign VC
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    file_path = './verifiable_credentials/' + ebsi_credential_to_issue_list.get(credential_type) + '.jsonld'
    credential = json.load(open(file_path))
    issuer_key =  issuer_data['jwk'] 
    issuer_did = issuer_data['did_ebsi'] 
    issuer_vm = issuer_did + "#" +  ebsi.thumbprint(issuer_key)
    credential['credentialSubject']['id'] = holder_did
    credential['issuer']= issuer_data['did_ebsi']
    credential['issued'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
    credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
    credential['validFrom'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
    credential_signed = ebsi.sign_jwt_vc(credential, issuer_vm , issuer_key, issuer_did, holder_did, access_token_data["c_nonce"])
    
    # Follow up page
    event_data = json.dumps({
        "stream_id" : access_token_data['issuer_state'],
        "result" : True})           
    red.publish('issuer_ebsi', event_data)

    # Transfer VC
    payload = {
        "format" : proof_format,
        "credential" : credential_signed,
        "c_nonce": str(uuid.uuid1()),
        "c_nonce_expires_in": C_NONCE_LIFE
    }
    headers = {
        'Cache-Control' : 'no-store',
        'Content-Type': 'application/json'}
    return Response(response=json.dumps(payload), headers=headers)
  

def ebsi_issuer_followup():  
    try :
        issuer_id = request.args['issuer_id']
    except :
        return jsonify('Unhautorized'), 401
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    if not issuer_data :
        return jsonify('Not found'), 404
    if request.args.get('message') :
        return render_template('op_issuer_failed.html', next = issuer_data['issuer_landing_page'])
    return redirect (issuer_data['callback'])
    
    
# server event push for user agent EventSource
def ebsi_issuer_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('issuer_ebsi')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()  
    headers = { 'Content-Type' : 'text/event-stream',
                'Cache-Control' : 'no-cache',
                'X-Accel-Buffering' : 'no'}
    return Response(event_stream(red), headers=headers)



