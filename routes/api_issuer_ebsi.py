"""
NEW

https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html

support Authorization code flow and pre-authorized code flow of OIDC4VCI

"""
from flask import jsonify, request, render_template, Response, redirect
import json
from datetime import datetime
import uuid
import logging
from urllib.parse import urlencode
import db_api
import ebsi
import base64
import issuer_activity_db_api
import ebsi
from op_constante_ebsi import ebsi_credential_to_issue_list

logging.basicConfig(level=logging.INFO)

API_LIFE = 1000
ACCESS_TOKEN_LIFE = 1000
GRANT_LIFE = 1000
C_NONCE_LIFE = 1000
CRYPTOGRAPHIC_SUITES = ['ES256K','ES256','ES384','ES512','RS256']
#DID_METHODS = ['did:ebsi','did:key','did:tz','did:pkh','did:ethr','did:web']
DID_METHODS = ['did:ebsi']
GRANT_TYPE_SUPPORTED = [ 'urn:ietf:params:oauth:grant-type:pre-authorized_code', 'authorization_code']


def init_app(app,red, mode) :
    # endpoint for application
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>/<user_id>',  view_func=ebsi_issuer_landing_page, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/issuer_stream',  view_func=ebsi_issuer_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/ebsi/issuer_followup',  view_func=ebsi_issuer_followup, methods = ['GET'])
 
    # api v2
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>',  view_func=ebsi_issuer_api, methods = ['POST'], defaults={'red' :red, 'mode' : mode})
    
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
    https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html
    ATTENTION new standard is https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html
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
        'id': ebsi_credential_to_issue_list[issuer_data['credential_to_issue']],
        'types':  issuer_data['credential_to_issue'],
        'display': [
            {
                'name': issuer_data['company_name'],
                'locale': 'en-US',
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
        'pre-authorized_grant_anonymous_access_supported' : True,
        'subject_syntax_types_supported': DID_METHODS,
        'credential_supported' : credential_supported,
        'credential_manifests' : credential_manifest,
    }
    return openid_configuration


# Customer API
def ebsi_issuer_api(issuer_id, red, mode) :
    """
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization' : 'Bearer <client_secret>'
    }
    data = { 
        "vc" : {....}, -> object
        pre-authorized_code : "lklkjlkjh"   -> optional
        }
    resp = requests.post(token_endpoint, headers=headers, data = data)
    return resp.json()

    dans l api on passe le credential type, le pre authorization code si existe et le VC avec les données utilisateurs
    """
    try :
        token = request.headers['Authorization']
        client_secret = token.split(" ")[1]
        issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
        vc =  request.form['vc']
    except :
        return Response(**manage_error("invalid_request", "Request format is incorrect"))
    
    pre_authorized_code = request.form.get('pre-authorized_code')
    if client_secret != issuer_data['client_secret'] :
        return Response(**manage_error("Unauthorized", "Client secret is incorrect"))
    
    user_id = str(uuid.uuid1())
    file_path = './verifiable_credentials/' + ebsi_credential_to_issue_list.get(issuer_data['credential_to_issue']) + '.jsonld'
    vc = json.load(open(file_path))
    user_data = {
        'vc' : vc,
        'credential_type' : issuer_data['credential_to_issue'],
        'pre-authorized_code' : pre_authorized_code
    }
    red.setex(user_id, API_LIFE, json.dumps(user_data))
    response = {"initiate_qrcode" : mode.server+ '/sandbox/ebsi/issuer/' + issuer_id +'/' +user_id}
    logging.info('initiate qrcode = ', mode.server+ '/sandbox/ebsi/issuer/' + issuer_id +'/' +user_id)
    return jsonify( response)


# initiate endpoint with QRcode
def ebsi_issuer_landing_page(issuer_id, user_id, red, mode) :
    """
    see EBSI specs as OpenID OIDC4VC issuance for issuance has changed

    https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html

    openid://initiate_issuance
    ?issuer=http%3A%2F%2F192.168.0.65%3A3000%2Fsandbox%2Febsi%2Fissuer%2Fhqplzbjrhg
    &credential_type=Pass
    &op_state=40fd65cf-98ba-11ed-957d-512a313adf23

    pre_authorized_code

    """
    #logging.info('Issuer openid-configuration = %s', mode.server + '/sandbox/ebsi/issuer/' + issuer_id + '/.well-known/openid-configuration' )

    try :
        issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    except :
        logging.error('issuer id not found')
        return render_template('op_issuer_removed.html')
    
    if issuer_data['credential_to_issue'] == 'DID' :
        logging.error('credetial to issue not set')
        return jsonify('Credential to issue not set correctly')
    
    # Test with pre authorized code
    if user_id == 'test' :
        pre_authorized_code = str(uuid.uuid1())
    # Test with authorization server
    elif user_id == 'test_authorization_server' :
        pre_authorized_code = None
    # Production
    else :
        try :
            user_data = json.loads(red.get(user_id).decode())
            pre_authorized_code = user_data.get('pre-authorized_code')
        except :
            logging.error('API not set correctly')
            return jsonify('api not set correctly')
    
    qrcode_page = issuer_data.get('landing_page_style')
    # Option 1 https://api-conformance.ebsi.eu/docs/wallet-conformance/issue
    url_data  = { 
        'issuer' : mode.server +'sandbox/ebsi/issuer/' + issuer_id,
        'credential_type'  : issuer_data['credential_to_issue'],
        'op_state' : user_id, #  op_stat 
        }
    #  https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-pre-authorized-code-flow
    # TODO PIN code not supported
    if pre_authorized_code :
        url_data['pre-authorized_code'] = pre_authorized_code
        url_data['user_pin_required']= False
        code_data = {
            'credential_type' : issuer_data['credential_to_issue'],
            'format' : 'jwt_vc',
            'op_state' : user_id,
            'user_id' : user_id
        }
        red.setex(pre_authorized_code, GRANT_LIFE, json.dumps(code_data)) 

    url = 'openid://initiate_issuance?' + urlencode(url_data)
    logging.info('qrcode = %s', url)
    openid_configuration  = json.dumps(oidc(issuer_id, mode), indent=4)
    deeplink_talao = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    deeplink_altme = mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url})

    return render_template(
        qrcode_page,
        openid_configuration = openid_configuration,
        url_data = json.dumps(url_data,indent = 6),
        url=url,
        deeplink_altme=deeplink_altme,
        deeplink_talao=deeplink_talao,
        stream_id=user_id,
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
    https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-credential-authorization-re
      
    my_request = {
        'scope' : 'openid',
        'client_id' : 'https://wallet.com/callback',
        'response_type' : 'code',
        'authorization_details' : json.dumps([{'type':'openid_credential',
                        'credential_type': credential_type,
                        'format':'jwt_vc'}]),
        'redirect_uri' :  ngrok + '/callback',
        'state' : '1234',
        'op_state' : 'mlkmlkhm'
        }

    """
    def authorization_error_response(error, error_description, stream_id, red) :
        """
        https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-authentication-error-respon
        
        https://www.rfc-editor.org/rfc/rfc6749.html#page-26
        """
        # front channel follow up 
        if stream_id  :
            event_data = json.dumps({'stream_id' : stream_id})           
            red.publish('issuer_ebsi', event_data)
        logging.warning(error_description)
        resp = {
            'error_description' : error_description,
            'error' : error
        }
        return redirect(redirect_uri + '?' + urlencode(resp))

    logging.info("authorization request received = %s", request.args)
    try :
        client_id = request.args['client_id']
        redirect_uri = request.args['redirect_uri']
    except :
        return jsonify('invalid_request'), 400

    op_state = request.args.get('op_state')
    if not op_state :
        logging.warning("op_state is missing")
    user_id = op_state
    
    try :
        scope = request.args['scope']
    except :
        return authorization_error_response("invalid_request", "scope is missing", op_state, red)
    
    try :
        response_type = request.args['response_type']
    except :
        return authorization_error_response("invalid_request", "reponse_type is missing", op_state, red)
    
    try :
        credential_type = json.loads(request.args['authorization_details'])[0]['credential_type']
    except :
        return authorization_error_response("invalid_request", "credential_type is missing", op_state, red)
    
    try :
        format = json.loads(request.args['authorization_details'])[0]['format']
    except :
        return authorization_error_response("invalid_request", "format is missing", op_state, red)

    if not db_api.read_ebsi_issuer(issuer_id) :
        return authorization_error_response("unauthorized_client", "issuer_id not found in data base", op_state, red)
    
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))

    if scope != 'openid' :
        return authorization_error_response("invalid_scope", "unsupported scope", op_state, red)

    if response_type != 'code' :
        return authorization_error_response("unsupported_response_type", "unsupported response type", op_state, red)

    if credential_type != issuer_data['credential_to_issue'] :
        return authorization_error_response("invalid_request", "unsupported credential type", op_state, red)

    if format not in ['jwt_vc', 'jwt_vc_json'] :
        return authorization_error_response("invalid_request", "unsupported format", op_state, red)

    # Code creation
    code = str(uuid.uuid1())
    code_data = {
        'client_id' : client_id,
        'nonce' : request.args.get('nonce'),
        'credential_type' : credential_type,
        'format' : format,
        'user_id' : user_id
        # TODO PKCE
        #'code_challenge' : request.args.get('code_challenge'), 
        #'code_challenge_method' : request.args.get('code_challenge_method'),
    }
    red.setex(code, GRANT_LIFE, json.dumps(code_data))    

    # TODO dynamic credential request register Altme wallet
    # https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-dynamic-credential-request
    # https://openid.net/specs/openid-connect-self-issued-v2-1_0.html#name-cross-device-self-issued-ope
    
    # Follow up 
    if op_state :
        event_data = json.dumps({'stream_id' : op_state})           
        red.publish('issuer_ebsi', event_data)

    resp = {'code' : code}
    if request.args.get('state') :
        resp['state'] = request.args['state']
    return redirect(redirect_uri + '?' + urlencode(resp))


def manage_error(error, error_description) :
    """
    # https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-credential-error-response
    """
    logging.warning(error_description)   
    payload = {
        'error' : error,
        'error_description' : error_description
    }
    headers = {
        'Cache-Control' : 'no-store',
        'Content-Type': 'application/json'}
    return {'response' : json.dumps(payload), 'status' : 400, 'headers' : headers}


# token endpoint
def ebsi_issuer_token(issuer_id, red) :
    """
    https://datatracker.ietf.org/doc/html/rfc6749#section-5.2

    https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-token-endpoint
    """
    logging.info("token endpoint request = %s", json.dumps(request.form))
    try :
        grant_type =  request.form['grant_type']
    except :
        return Response(**manage_error("invalid_request", "Request format is incorrect"))
    
    if grant_type not in GRANT_TYPE_SUPPORTED :
        return Response(**manage_error("invalid_grant", "Grant type not supported"))

    if grant_type == 'urn:ietf:params:oauth:grant-type:pre-authorized_code' :
        try :
            code = request.form['pre-authorized_code']
        except :
            logging.warning('pre authorized code is missing')
            return Response(**manage_error("invalid_grant", "Request format is incorrect"))
    else:
        try :
            code = request.form['code']
        except :
            logging.warning('code from authorization server is missing')
            return Response(**manage_error("invalid_request", "Request format is incorrect"))

    try :
        data = json.loads(red.get(code).decode())
    except :
        return Response(**manage_error("invalid_grant", "Grant code expired"))     
    
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
        'format' : data['format'],
        'credential_type' : data['credential_type'],
        'user_id' : data['user_id'],
    }
    red.setex(access_token, ACCESS_TOKEN_LIFE,json.dumps(token_endpoint_data))

    headers = {
        'Cache-Control' : 'no-store',
        'Content-Type': 'application/json'}
    return Response(response=json.dumps(endpoint_response), headers=headers)
 

# credential endpoint
def ebsi_issuer_credential(issuer_id, red) :
    """
    https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-credential-endpoint
    
    https://api-conformance.ebsi.eu/docs/specs/credential-issuance-guidelines#credential-request
    """
    logging.info("credential endpoint request")
    # Check access token
    try :
        access_token = request.headers['Authorization'].split()[1]
    except :
        return Response(**manage_error("invalid_token", "Access token not passed in request header"))
    try :
        access_token_data = json.loads(red.get(access_token).decode())
    except :
        return Response(**manage_error("invalid_token", "Access token expired")) 
    
    # Check request 
    try :
        result = request.json
        credential_type = result['type']
        proof_format = result['format']
        proof_type  = result['proof']['proof_type']
        proof = result['proof']['jwt']
    except :
        return Response(**manage_error("invalid_request", "Invalid request format 2")) 
    
    if credential_type != access_token_data['credential_type'] :
        return Response(**manage_error("unsupported_credential_type", "The credential type is not supported")) 
    if proof_format != 'jwt_vc' :
        return Response(**manage_error("unsupported_credential_format", "The proof format is not supported")) 
    if proof_type != 'jwt' :
        return Response(**manage_error("invalid_or_missing_proof", "The proof type is not supported")) 

    # Get holder pub key from holder wallet and verify proof
    logging.info("proof of owbership = %s", proof)
    try :
        ebsi.verif_proof_of_key(proof, access_token_data['c_nonce'])
    except Exception as e :
        logging.error("verif proof error = %s", str(e))
        return Response(**manage_error("invalid_or_missing_proof", str(e))) 
    
    # TODO Build JWT VC and sign VC
    payload = proof.split('.')[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)
    proof_payload = json.loads(base64.urlsafe_b64decode(payload).decode())
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    if access_token_data['user_id'] == 'test' :
        logging.info("test use case")
        file_path = './verifiable_credentials/' + ebsi_credential_to_issue_list.get(credential_type) + '.jsonld'
        credential = json.load(open(file_path))
    else :
        logging.info("standard use case")
        credential = json.loads(red.get(access_token_data['user_id']).decode())
    issuer_key =  issuer_data['jwk'] 
    issuer_did = issuer_data['did_ebsi'] 
    issuer_vm = issuer_did + '#' +  ebsi.thumbprint(issuer_key)
    credential['credentialSubject']['id'] = proof_payload['iss']
    credential['issuer']= issuer_data['did_ebsi']
    credential['issued'] = datetime.now().replace(microsecond=0).isoformat() + 'Z'
    credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + 'Z'
    credential['validFrom'] = datetime.now().replace(microsecond=0).isoformat() + 'Z'
    credential_signed = ebsi.sign_jwt_vc(credential, issuer_vm , issuer_key, issuer_did, proof_payload['iss'], access_token_data['c_nonce'])

    # Transfer VC
    payload = {
        'format' : proof_format,
        'credential' : credential_signed,
        'c_nonce': str(uuid.uuid1()),
        'c_nonce_expires_in': C_NONCE_LIFE
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



