
from flask import jsonify, request, render_template, Response, redirect, session
import json
from datetime import timedelta, datetime
import uuid
import logging
from urllib.parse import urlencode
import requests
import db_api
from jwcrypto import jwk, jwt
import ebsi
import base64
import issuer_activity_db_api
import pyotp


from op_constante import ebsi_credential_to_issue_list

logging.basicConfig(level=logging.INFO)
OFFER_DELAY = timedelta(seconds= 10*60)


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
    """
    Attention for EBSI "types" = id of data model
    https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#section-10.2.3
    """
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    oidc = {
        'credential_issuer': mode.server + 'sandbox/ebsi/issuer/' + issuer_id,
        'authorization_endpoint':  mode.server + 'sandbox/ebsi/issuer/' + issuer_id + '/authorize',
        'token_endpoint': mode.server + 'sandbox/ebsi/issuer/' + issuer_id + '/token',
        'credential_endpoint': mode.server + 'sandbox/ebsi/issuer/' + issuer_id + '/credential',
        # 'batch_credential_endpoint' :
        # 'display' : -> output descriptors ?????
        "subject_syntax_types_supported": [
                "did:ebsi"
        ],
        'credential_supported' : [{
                        'format': 'jwt_vc',
                        'id': ebsi_credential_to_issue_list.get(issuer_data['credential_to_issue'], 'unknown id') ,
                        'types':  issuer_data['credential_to_issue'],
                        'cryptographic_binding_methods_supported': [
                            'did'
                        ],
                        'cryptographic_suites_supported': [
                            'ES256K',
                            'ES256'
                        ]
        }],
    }
    return jsonify(oidc)


# initiate endpoint with QRcode
def ebsi_issuer_landing_page(issuer_id, red, mode) :
    """
    see EBSI specs as OpenID siopv2 for issuance has changed

    https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-issuance-initiation-request

    """
    session['is_connected'] = True
    try :
        issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    except :
        logging.error('issuer id not found')
        return render_template('op_issuer_removed.html')
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))

    stream_id = str(uuid.uuid1())
    op_stat = str(uuid.uuid1())
    qrcode_page = issuer_data.get('landing_page_style')
    url_data  = { 
            'issuer' : mode.server +'sandbox/ebsi/issuer/' + issuer_id,
            'credential_type'  : issuer_data['credential_to_issue'],
            'op_stat' : op_stat
    }
    url = 'openid://initiate_issuance?' + urlencode(url_data)
    logging.info('qrcode = %s', url_data)
    return render_template(
        qrcode_page,
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
        'client_id' : 'https://client.com/callback',
        'response_type' : 'code',
        'authorization_details' : json.dumps([{'type':'openid_credential',
                        'credential_type': credential_type,
                        'format':'jwt_vc'}]),
        'redirect_uri' :  ngrok + '/callback',
        'state' : '1234'
        }
    """
    def manage_error (msg) :
        logging.warning(msg)
        resp = {'error' : msg}
        return redirect(request.args['redirect_uri'] + '?' + urlencode(resp))
    try :
        data = {
            'client_id' : request.args['client_id'],
            'scope' : request.args.get('scope'),
            'state' : request.args.get('state'),
            'response_type' : request.args['response_type'],
            'redirect_uri' : request.args['redirect_uri'],
            'nonce' : request.args.get('nonce'),
            'authorization_details' : request.args['authorization_details'],
            # TODO PKCE
            #'code_challenge' : request.args.get('code_challenge'), 
            #'code_challenge_method' : request.args.get('code_challenge_method'),
            'expires' : datetime.timestamp(datetime.now()) + 180
        }
    except :
        logging.warning('invalid request received in authorization server')
        return manage_error("invalid_request_object")
    
    # for dynamic credential request register Altme wallet
    # https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html#name-dynamic-credential-request
    # altme authorization_endpoint =  'https://app.altme.io/app/authorize' 
    if not request.args.get('wallet_issuer') :
        data['user_hint'] = str(uuid.uuid1())
        data['wallet_issuer'] = 'https://app.altme.io/app/issuer'
    else :
        data['wallet_issuer'] = request.args['wallet_issuer']
        data['user_hint'] = request['user_hint']

    if not db_api.read_ebsi_issuer(issuer_id) :
        logging.warning('issuer_id not found in data base')
        return manage_error("invalid_request")
    
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))

    if request.args['response_type'] != 'code' :
        logging.warning('unsupported response type %s', request.args['response_type'])
        return manage_error("unsupported_response_type")
    
    try :
        credential_type = json.loads(request.args['authorization_details'])[0]['credential_type']
    except :
        return manage_error("invalid_request")
    if credential_type != issuer_data['credential_to_issue'] :
        logging.warning('credential type %s does not match', request.args['response_type'])
        return manage_error("unsupported_credential_type")

    try :
        format = json.loads(request.args['authorization_details'])[0]['format']
    except :
        return manage_error("invalid_request")
    if format not in ['jwt_vc', 'jwt_vc_json'] :
        return manage_error("unsupported_format")

    # creation grant
    code = str(uuid.uuid1())
    red.setex(code, 180, json.dumps(data))
    resp = {'code' : code}
    if request.args.get('state') :
        resp['state'] = request.args.get('state')
    return redirect(issuer_data['callback'] + '?' + urlencode(resp))
   

# token endpoint
def ebsi_issuer_token(issuer_id, red) :
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
        issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
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
                        'access_token' : access_token,
                        'c_nonce' : str(uuid.uuid1()),
                        'token_type' : 'Bearer',
                        'expires_in': 1000
                        }
    red.delete(code)
    red.setex(access_token, 1000,json.dumps({'issuer_id' : issuer_id}))
    headers = {
        'Cache-Control' : 'no-store',
        'Pragma' : 'no-cache',
        'Content-Type': 'application/json'}
    return Response(response=json.dumps(endpoint_response), headers=headers)
 

# credential endpoint
def ebsi_issuer_credential(issuer_id, red) :
    access_token = request.headers['Authorization'].split()[1]
    try :
        data = json.loads(red.get(access_token).decode())
    except :
        logging.warning("access token expired")
        headers = {"WWW-Authenticate' : 'Bearer realm='userinfo', error='invalid_token', error_description = 'The access token expired'"}
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
    payload = { 'credential' : 'test'}
    headers = {
        'Cache-Control' : 'no-store',
        'Pragma' : 'no-cache',
        'Content-Type': 'application/json'}
    return Response(response=json.dumps(payload), headers=headers)
  

def ebsi_issuer_followup():  
    if not session.get('is_connected') :
        logging.error('user is not connectd')
        return render_template('op_issuer_removed.html',next = issuer_data['issuer_landing_page'])
    session.clear()
    issuer_id = request.args.get('issuer_id')
    issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    if request.args.get('message') :
        return render_template('op_issuer_failed.html', next = issuer_data['issuer_landing_page'])
    try :
        issuer_data = json.loads(db_api.read_ebsi_issuer(issuer_id))
    except :
        return render_template('op_issuer_removed.html',next = issuer_data['issuer_landing_page'])
    return redirect (issuer_data['callback'])
    
    
# server event push for user agent EventSource
def ebsi_issuer_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('op_issuer')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()  
    headers = { 'Content-Type' : 'text/event-stream',
                'Cache-Control' : 'no-cache',
                'X-Accel-Buffering' : 'no'}
    return Response(event_stream(red), headers=headers)



