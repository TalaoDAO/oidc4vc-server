"""
NEW


https://issuer.walt.id/issuer-api/default/oidc

https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html

support Authorization code flow and pre-authorized code flow of OIDC4VCI

"""
from flask import jsonify, request, render_template, Response, redirect
import json
from datetime import datetime
import uuid
import logging
import didkit
from urllib.parse import urlencode
import db_api
import oidc4vc
import base64
import issuer_activity_db_api
from oidc4vc_constante import type_2_schema
from profile import profile

logging.basicConfig(level=logging.INFO)

API_LIFE = 1000
ACCESS_TOKEN_LIFE = 1000
GRANT_LIFE = 1000
C_NONCE_LIFE = 1000
DID_METHODS = ['did:ebsi']
GRANT_TYPE_SUPPORTED = [ 'urn:ietf:params:oauth:grant-type:pre-authorized_code', 'authorization_code']


def init_app(app,red, mode) :
    # endpoint for application
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>/<stream_id>',  view_func=ebsi_issuer_landing_page, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/issuer_stream',  view_func=ebsi_issuer_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/ebsi/issuer_followup/<stream_id>',  view_func=ebsi_issuer_followup, methods = ['GET'], defaults={'red' :red})
 
    # api v2
    app.add_url_rule('/sandbox/ebsi/issuer/api/<issuer_id>',  view_func=issuer_api_endpoint, methods = ['POST'], defaults={'red' :red, 'mode' : mode})
    
    # EBSI protocol with wallet
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>/.well-known/openid-configuration', view_func=ebsi_issuer_openid_configuration, methods=['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>/authorize',  view_func=ebsi_issuer_authorize, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>/token',  view_func=ebsi_issuer_token, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/ebsi/issuer/<issuer_id>/credential',  view_func=ebsi_issuer_credential, methods = ['GET', 'POST'], defaults={'red' :red})
    return


def ebsi_issuer_openid_configuration(issuer_id, mode):
    doc = oidc(issuer_id, mode)
    if not doc :
        return jsonify('Not found'), 404
    return jsonify(doc)


def oidc(issuer_id, mode) :
    """
    Attention for EBSI "types" = id of data model
    https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html
    ATTENTION new standard is https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html
    """
    try :
        issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id)) 
        issuer_profile = profile[issuer_data.get('profile', 'DEFAULT')]
    except :
        logging.warning('issuer_id not found for %s', issuer_id)
        return
    # Credential supported section
    cs = list()
    for vc in issuer_profile['credential_supported']:
        cs.append({
            'format': issuer_profile['issuer_vc_type'],
            'id': vc,
            'display': [
                {
                    'name': issuer_data['company_name'],
                    'locale': 'en-US',
                }
            ],
            'cryptographic_binding_methods_supported': issuer_profile['cryptographic_binding_methods_supported'],
            'cryptographic_suites_supported': issuer_profile['cryptographic_suites_supported']
            })
        
    # Credential manifest section
    #https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-server-metadata    
    cm = list()  
    for vc in issuer_profile['credential_supported']:
        file_path = './credential_manifest/' + vc + '_credential_manifest.json'
        cm_to_add = json.load(open(file_path))
        cm_to_add['issuer']['id'] = issuer_data.get('did' , 'Unknown')
        cm_to_add['issuer']['name'] = issuer_data['application_name']
        cm.append(cm_to_add)
    
    # https://www.rfc-editor.org/rfc/rfc8414.html#page-4

    openid_configuration = dict()
    if issuer_profile.get('service_documentation') :
        openid_configuration['service_documentation'] = issuer_profile['service_documentation']
    openid_configuration .update({
        'credential_issuer': mode.server + 'sandbox/ebsi/issuer/' + issuer_id,
        'authorization_endpoint':  mode.server + 'sandbox/ebsi/issuer/' + issuer_id + '/authorize',
        'token_endpoint': mode.server + 'sandbox/ebsi/issuer/' + issuer_id + '/token',
        'credential_endpoint': mode.server + 'sandbox/ebsi/issuer/' + issuer_id + '/credential',
        'pre-authorized_grant_anonymous_access_supported' : False,
        'subject_syntax_types_supported': issuer_profile['subject_syntax_types_supported'],
        'credential_supported' : cs,
        'credential_manifests' : cm,
    })
    return openid_configuration


# Customer API
def issuer_api_endpoint(issuer_id, red, mode) :
    """
    This API returns the QRcode content to be diplayed by teh website

    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer <client_secret>'
    }
    data = { 
        "vc" : {....}, -> object
        pre-authorized_code : "lklkjlkjh",   -> optional,
        "credential_type" : "VerifibaleDiploma",
        "user_pin_required" : false -> optional
        }
    resp = requests.post(token_endpoint, headers=headers, data = data)
    return resp.json()

    dans l api on passe le credential type, le pre authorization code si existe et le VC avec les données utilisateurs
    """    
    try :
        token = request.headers['Authorization']
        client_secret = token.split(" ")[1]
        issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
        vc =  request.json['vc']
        credential_type = request.json['credential_type']
    except :
        return Response(**manage_error("invalid_request", "Request format is incorrect"))
    
    if client_secret != issuer_data['client_secret'] :
        return Response(**manage_error("Unauthorized", "Client secret is incorrect"))
    user_data = {
        'vc' : vc,
        'issuer_id' : issuer_id,
        'credential_type' : credential_type,
        'pre-authorized_code' : request.json.get('pre-authorized_code'),
        'user_pin_required' : request.json.get('user_pin_required')
    }
    stream_id = str(uuid.uuid1())
    red.setex(stream_id, API_LIFE, json.dumps(user_data))
    response = {"initiate_qrcode" : mode.server+ 'sandbox/ebsi/issuer/' + issuer_id +'/' + stream_id }
    logging.info('initiate qrcode = %s', mode.server+ 'sandbox/ebsi/issuer/' + issuer_id +'/' + stream_id)
    return jsonify( response)



# initiate endpoint with QRcode
def ebsi_issuer_landing_page(issuer_id, stream_id, red, mode) :
    #see EBSI specs as OpenID OIDC4VC issuance for issuance has changed
    #https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html
    #openid://initiate_issuance
    #?issuer=http%3A%2F%2F192.168.0.65%3A3000%2Fsandbox%2Febsi%2Fissuer%2Fhqplzbjrhg
    #&credential_type=Pass
    #&op_state=40fd65cf-98ba-11ed-957d-512a313adf23
    #pre_authorized_code
    #logging.info('Issuer openid-configuration = %s', mode.server + '/sandbox/ebsi/issuer/' + issuer_id + '/.well-known/openid-configuration' )

    try :
        issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
        issuer_profile = profile[issuer_data.get('profile', 'DEFAULT')]
    except :
        logging.error('issuer id not found')
        return render_template('op_issuer_removed.html')
    try :
        user_data = json.loads(red.get(stream_id).decode())
        pre_authorized_code = user_data['pre-authorized_code']
        vc = user_data['vc']
        credential_type = user_data['credential_type']
    except :
        logging.error('API not set correctly')
        return jsonify('api not set correctly')
    
    qrcode_page = issuer_data.get('landing_page_style')
    # Option 1 https://api-conformance.ebsi.eu/docs/wallet-conformance/issue
    if issuer_data['profile'] == 'EBSIV2' :
        url_data  = { 
            'issuer' : mode.server +'sandbox/ebsi/issuer/' + issuer_id,
            'credential_type'  : type_2_schema[credential_type],
            'op_state' : stream_id, #  op_stat 
        }
    elif issuer_data['profile'] == 'CUSTOM' :
        url_data  = { 
            'issuer' : mode.server +'sandbox/ebsi/issuer/' + issuer_id,
            'credential_type'  : credential_type,
            'op_state' : stream_id, #  op_stat 
        }
    else :
        url_data  = { 
            "credential_offer" : {
                'credential_issuer' : mode.server +'sandbox/ebsi/issuer/' + issuer_id,
                'credentials'  : credential_type,
                #'op_state' : stream_id, #  op_stat 
            }
        }
    
    #  https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-pre-authorized-code-flow
    # TODO PIN code not supported
    if pre_authorized_code and issuer_data['profile'] in ['EBSIV2', 'CUSTOM'] :
        url_data['pre-authorized_code'] = pre_authorized_code
        url_data['user_pin_required']= False
        code_data = {
            'credential_type' : credential_type,
            'format' : issuer_profile['issuer_vc_type'],
            'stream_id' : stream_id,
            'vc' : vc
        }
        red.setex(pre_authorized_code, GRANT_LIFE, json.dumps(code_data)) 
    
    elif pre_authorized_code and issuer_data['profile'] not in ['EBSIV2', 'CUSTOM'] :
        url_data['credential_offer'] ['grants'] ={
            'urn:ietf:params:oauth:grant-type:pre-authorized_code': {
                'pre-authorized_code': pre_authorized_code,
                'user_pin_required': False
            }
        }
        code_data = {
            'credential_type' : credential_type,
            'format' : issuer_profile['issuer_vc_type'],
            'stream_id' : stream_id,
            'vc' : vc
        }
        red.setex(pre_authorized_code, GRANT_LIFE, json.dumps(code_data)) 
    
    elif not pre_authorized_code and issuer_data['profile'] not in  ['EBSIV2', 'CUSTOM'] :
        url_data['credential_offer']['grants'] ={
            'authorization_code': {
            'issuer_state': stream_id
            }
        }
        code_data = {
            'credential_type' : credential_type,
            'format' : issuer_profile['issuer_vc_type'],
            'stream_id' : stream_id,
            'vc' : vc,
            'issuer_state' : stream_id
        }
        red.setex(pre_authorized_code, GRANT_LIFE, json.dumps(code_data))
    else :
        logging.warning('Not supported')
        jsonify('Parameters not supported')
    print(url_data)
    url = issuer_profile['oidc4vci_prefix'] + '?' + urlencode(url_data)
    logging.info('qrcode = %s', url)
    
    openid_configuration  = json.dumps(oidc(issuer_id, mode), indent=4)
    deeplink_talao = mode.deeplink_talao + 'app/download/ebsi?' + urlencode({'uri' : url })
    deeplink_altme = mode.deeplink_altme + 'app/download/ebsi?' + urlencode({'uri' : url})
    logging.info("deeplink altme = %s", deeplink_altme)

    return render_template(
        qrcode_page,
        openid_configuration = openid_configuration,
        url_data = json.dumps(url_data,indent = 6),
        url=url,
        deeplink_altme=deeplink_altme,
        deeplink_talao=deeplink_talao,
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
    https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-credential-authorization-re
      
    my_request = {
        'scope' : 'openid',
        'client_id' : 'https://wallet.com/callback',
        'response_type' : 'code',
        'authorization_details' : json.dumps([{'type':'openid_credential',
                        'credential_type': credential_type,
                        'format':'jwt_vc'}]),
        'redirect_uri' :  ngrok + '/callback',
        'state' : '1234', # wallet state
        'op_state' : 'mlkmlkhm' #issuer state
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
        op_state = request.args.get('op_state')
        issuer_state = request.args.get('issuer_state')
    except :
        return jsonify('invalid_request'), 400
    
    op_state = op_state if op_state else issuer_state

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

    # TODO Manage login and get vc for this user
    file_path = './verifiable_credentials/PhoneProof.jsonld'
    vc_for_test = json.load(open(file_path))

    # Code creation
    code = str(uuid.uuid1())
    code_data = {
        'credential_type' : credential_type,
        'format' : format,
        'stream_id' : op_state,
        'vc' : vc_for_test
        # TODO PKCE
        #'code_challenge' : request.args.get('code_challenge'), 
        #'code_challenge_method' : request.args.get('code_challenge_method'),
    }
    red.setex(code, GRANT_LIFE, json.dumps(code_data))    

    # TODO dynamic credential request register Altme wallet
    # https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-dynamic-credential-request
    # https://openid.net/specs/openid-connect-self-issued-v2-1_0.html#name-cross-device-self-issued-ope
    

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
            user_pin = request.form.get('user_pin')
        except :
            logging.warning('pre authorized code is missing')
            return Response(**manage_error("invalid_grant", "Request format is incorrect"))
    
    elif grant_type == 'authorization_code' :
        try :
            code = request.form['code']
        except :
            logging.warning('code from authorization server is missing')
            return Response(**manage_error("invalid_request", "Request format is incorrect"))
    else : 
        pass # future use  
    
    logging.info('user_pin = %s', user_pin)

    if not code : # in case of wallet error
        logging.warning('code is null')
        return Response(**manage_error("invalid_grant", "Request format is incorrect"))

    try :
        data = json.loads(red.get(code).decode())
    except :
        return Response(**manage_error("invalid_grant", "Grant code expired"))     
    
    # token response
    access_token = str(uuid.uuid1())
    # TODO add id_token ???
    endpoint_response = {
        'access_token' : access_token,
        'c_nonce' : str(uuid.uuid1()),
        'token_type' : 'Bearer',
        'expires_in': ACCESS_TOKEN_LIFE
    }
    token_endpoint_data = {
        'access_token' : access_token,
        'pre_authorized_code' : code,
        'c_nonce' : endpoint_response['c_nonce'],
        'format' : data['format'],
        'credential_type' : data['credential_type'],
        'vc' : data['vc'],
        'stream_id' : data['stream_id'],
    }
    red.setex(access_token, ACCESS_TOKEN_LIFE,json.dumps(token_endpoint_data))

    headers = {
        'Cache-Control' : 'no-store',
        'Content-Type': 'application/json'}
    return Response(response=json.dumps(endpoint_response), headers=headers)
 

# credential endpoint
async def ebsi_issuer_credential(issuer_id, red) :
    """
    https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-credential-endpoint
    
    https://api-conformance.ebsi.eu/docs/specs/credential-issuance-guidelines#credential-request

    {
    "format":"jwt_vc_json",
    "types":[
      "VerifiableCredential",
      "UniversityDegreeCredential"
    ],
    "proof":{
      "proof_type":"jwt",
      "jwt":"eyJraWQiOiJkaWQ6ZXhhbXBsZTplYmZlYjFmNzEyZWJjNmYxYzI3NmUxMmVjMjEva2V5cy8
      xIiwiYWxnIjoiRVMyNTYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJzNkJoZFJrcXQzIiwiYXVkIjoiaHR
      0cHM6Ly9zZXJ2ZXIuZXhhbXBsZS5jb20iLCJpYXQiOiIyMDE4LTA5LTE0VDIxOjE5OjEwWiIsIm5vbm
      NlIjoidFppZ25zbkZicCJ9.ewdkIkPV50iOeBUqMXCC_aZKPxgihac0aW9EkL1nOzM"
    }
    }
    
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
    
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    logging.info('Profile = %s', issuer_data['profile'])

    issuer_profile = profile[issuer_data['profile']]
    
    # Check request 
    try :
        result = request.json
        credential_type = result['type']
        proof_format = result['format']
        proof_type  = result['proof']['proof_type']
        proof = result['proof']['jwt']
    except :
        return Response(**manage_error("invalid_request", "Invalid request format 2")) 
    
    # check credential type requested
    logging.info('credential type requested = %s', access_token_data['credential_type'])
    if issuer_data['profile'] == 'EBSIV2' :
        if credential_type != type_2_schema[access_token_data['credential_type']] :
            return Response(**manage_error("unsupported_credential_type", "The credential type is not supported")) 
    else :
        if credential_type != access_token_data['credential_type'] :
            return Response(**manage_error("unsupported_credential_type", "The credential type is not supported")) 
    
    # check proof format requested
    logging.info("proof format requested = %s", proof_format)
    if proof_format not in ['jwt_vc_json', 'jwt_vc_json-ld', 'ldp_vc'] :
        return Response(**manage_error("unsupported_credential_format", "The proof format requested is not supported")) 

    # Check proof  of key ownership received
    logging.info("proof of key ownership received = %s", proof)
    try :
        oidc4vc.verif_token(proof, access_token_data['c_nonce'])
        logging.info('proof of ownership is validated')
    except Exception as e :
        logging.warning("proof of ownership error = %s", str(e))
        return Response(**manage_error("invalid_or_missing_proof", str(e))) 
    
    proof_payload=oidc4vc.get_payload_from_token(proof)
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    credential = access_token_data['vc']
    credential['credentialSubject']['id'] = proof_payload['iss']
    credential['issuer']= issuer_data.get('did', 'Unknown')
    credential['issued'] = datetime.now().replace(microsecond=0).isoformat() + 'Z'
    credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + 'Z'
    credential['validFrom'] = datetime.now().replace(microsecond=0).isoformat() + 'Z'
    
    issuer_key =  issuer_data['jwk'] 
    issuer_did = issuer_data.get('did', 'Unknown') 
    issuer_vm = issuer_data.get('verification_method', 'Unknown') 

    
    if proof_format in ['jwt_vc_json', 'jwt_vc_json-ld'] :        
        credential_signed = oidc4vc.sign_jwt_vc(credential, issuer_vm , issuer_key, access_token_data['c_nonce'])

    else : 
        # proof_format == 'ldp_vc' :
        didkit_options = {
                "proofPurpose": "assertionMethod",
                "verificationMethod": issuer_vm
        }
        credential_signed =  await didkit.issue_credential(
                json.dumps(credential),
                didkit_options.__str__().replace("'", '"'),
                issuer_key
                )
    
    logging.info('credential signed sent to wallet = %s', credential_signed)

    # send event to front to go forward callback and send credential to wallet
    data = json.dumps({
        'stream_id' : access_token_data['stream_id']
    })
    red.publish('issuer_ebsi', data)
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
  

def ebsi_issuer_followup(stream_id, red):  
    #try :
    
    data = json.loads(red.get(stream_id).decode())
    print(data)
    issuer_id = data['issuer_id']
    pre_authorized_code = data['pre-authorized_code']
    #except :
    #    return jsonify('Unhautorized'), 401
    issuer_data = db_api.read_ebsi_issuer(issuer_id)
    if not issuer_data :
        return jsonify('Not found'), 404
    return redirect (json.loads(issuer_data)['callback'] + '?pre_authorized_code=' + pre_authorized_code)
    
    
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



