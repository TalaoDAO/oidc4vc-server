"""
SIOPV2 verifier
the wallet is the openID provider (SIOP)
The verifier is the relaying party (Client)
didkit 0.4.0 , async
https://openid.net/specs/openid-connect-self-issued-v2-1_0.html

"""

import json
from datetime import timedelta, datetime
import didkit
from jwcrypto import jwk, jwt
from flask import jsonify, request, Response, render_template, redirect, session
from flask_qrcode import QRcode
import logging
import secrets 
import uuid
from urllib.parse import urlencode
from claim import claims2
from db_api import read_verifier
import activity_db_api

logging.basicConfig(level=logging.INFO)
OFFER_DELAY = timedelta(seconds= 10*60)


try :
    RSA_KEY_DICT = json.load(open("/home/admin/sandbox/keys.json", "r"))['RSA_key']
except :
    RSA_KEY_DICT = json.load(open("/home/thierry/sandbox/keys.json", "r"))['RSA_key']

rsa_key = jwk.JWK(**RSA_KEY_DICT) 
public_rsa_key =  rsa_key.export(private_key=False, as_dict=True)


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/siopv2',  view_func=siopv2, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/sandbox/op/siopv2/redirect/<id>',  view_func=siopv2_redirect, methods = ['POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/op/siopv2/followup',  view_func=siopv2_followup, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/op/siopv2/stream',  view_func=siopv2_stream, methods = ['GET', 'POST'], defaults={ 'red' : red})
    app.add_url_rule('/sandbox/op/siopv2/request_uri/<id>',  view_func=siopv2_request_uri, methods = ['GET', 'POST'], defaults={ 'red' : red})
    return

registration = {
        "id_token_signing_alg_values_supported" : [
            "RS256",
            "ES256",
            "ES256K",
            "EdDSA"
        ],
        "subject_syntax_types_supported": [
            "did:web",
            "did:tz",
            "did:key",
            "did:ebsi"
            "did:pkh",
            "did:ethr"
        ]
    }

# request_uri endpoint
def siopv2_request_uri(id, red):
    encoded = red.get(id + "_encoded").decode()
    return jsonify(encoded)


# main entry
def siopv2(red, mode) :
    """
    https://openid.net/specs/openid-connect-self-issued-v2-1_0.html
    https://ec.europa.eu/digital-building-blocks/wikis/display/EBSIDOC/Verifiable+Presentation+Exchange+Guidelines
    https://openid.net/specs/openid-connect-federation-1_0.html#name-rp-metadata
    """
    try :
        client_id = json.loads(red.get(request.args['code']).decode())['client_id']
        nonce = json.loads(red.get(request.args['code']).decode())['nonce']
    except :
        logging.error("session expired in login_qrcode")
        return jsonify("session expired"), 403

    verifier_data = json.loads(read_verifier(client_id))
    verifier_key = jwk.JWK(**RSA_KEY_DICT) 
    stream_id = str(uuid.uuid1())
    claims = claims2.myclaim
    nonce = secrets.token_urlsafe()[0:10]
    login_request = {
                "scope" : "openid",
                "response_type" : "id_token",
                "client_id" : mode.server + "sandbox/op",
    	        "redirect_uri" : mode.server + "sandbox/op/siopv2/redirect/" + stream_id,
    	        "response_mode" : "post",
                "registration" : json.dumps(registration, separators=(',', ':')),
    	        "claims" : json.dumps(claims, separators=(',', ':')),
    	        "nonce" : nonce,
                "request_uri" : mode.server + "sandbox/op/siopv2/request_uri/" + stream_id,
    }
    
    # Request header for request_uri value
    header = {
        "typ" :"JWT",
        "kid": RSA_KEY_DICT['kid'],
         "alg": "RS256"
    }
    # Request signed by RP as a JWT 
    token = jwt.JWT(header=header,claims=login_request, algs=["RS256"])
    token.make_signed_token(verifier_key)
    login_request_encoded =  token.serialize()
    red.set(stream_id + "_encoded", login_request_encoded)

    # QR code and universal link display
    red.set(stream_id, json.dumps(login_request))
    RP_request = urlencode(login_request) # for desktop wallet
    url = "openid://?" + RP_request # for QR code 
    #url =  RP_request # for QR code 

    deeplink_altme = mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url }) # universal link
    # pour un acces direct 
    if request.method == 'POST' :
        return jsonify(RP_request)
    else :
        return render_template('op_siopv2_qrcode.html',
          back_button = False,
							url=url,
                            request=url,
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

"""
redirect_uri : Endpoint for wallet response as a SIOP

"""
async def siopv2_redirect(stream_id, red) :
    try : 
        login_request = red.get(stream_id).decode()
        nonce = json.loads(login_request).get('nonce', "no_nonce")
    except :
        return jsonify('server error'), 500
    
    def manage_error(msg) :
            value = json.dumps({
                    "access" : "access_denied",
                    })
            red.setex(stream_id + "_DIDAuth", 180, value)
            event_data = json.dumps({"stream_id" : stream_id})           
            red.publish('siopv2', event_data)
            logging.error(msg)
            return jsonify(msg), 403
    
    vp = request.form['vp_token']
    if isinstance(vp, str) :
        vp = json.loads(vp)
    vc = vp['verifiableCredential']
    if isinstance(vc, list) :
        vc = vc[0]
    vp_result = await didkit.verify_presentation(json.dumps(vp), '{}')

    if json.loads(vp_result)['errors'] :
         return manage_error("signature check failed")   
   
    VC_type =  vp['verifiableCredential']['credentialSubject']['type']
    if VC_type != 'ParticipantCredential' :
        return manage_error("signature check failed")   
       
    # success
    value = json.dumps({
                    "access" : "ok",
                    "vp" : vp,
                    "user" : vc["credentialSubject"]["id"]
                    })
    red.setex(stream_id + "_DIDAuth", 180, value)
    event_data = json.dumps({"stream_id" : stream_id})  
    red.publish('siopv2', event_data)     
    return jsonify("ok"), 200


def siopv2_followup(red):  
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


# Event stream to manage the front end page
def siopv2_stream(red):
    def login_event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('siopv2')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(login_event_stream(red), headers=headers)


"""

async def test_id_token(id_token, nonce) :
    id_token_kid = jwt.get_unverified_header(id_token)['kid']
    id_token_unverified = jwt.decode(id_token, options={"verify_signature": False})
    aud = id_token_unverified.get('aud')
    logging.info("audience = %s", aud)
    id_token_did = id_token_kid.split('#')[0] 
    # get the DID Document
    did_document = json.loads(await didkit.resolve_did(id_token_did, '{}')) #['didDocument']
    # extract public key JWK
    public_key = str()
    error = str()
    for key in did_document['verificationMethod'] :
        if key['id'] == id_token_kid :
            public_key = json.dumps(key['publicKeyJwk'])
            break
    if not public_key :
        error += "public key not found in DID Document <br>"
    logging.info('wallet public key = %s', public_key)
    op_key_pem = jwk.JWK(**json.loads(public_key)).export_to_pem(private_key=False, password=None).decode()
    try :
        if aud :
            id_token = jwt.decode(id_token, op_key_pem, audience=aud, algorithms=["RS256", "ES256", "ES256K", "EdDSA", "PS256"])
        else :
            id_token = jwt.decode(id_token, op_key_pem, algorithms=["RS256", "ES256", "ES256K", "EdDSA", "PS256"])
    except :
        error += "error decode Id token <br>"
        return error
        
    if not id_token.get('iat') :
        error += "iat is missing in id token <br> "
    if not id_token.get('exp') :
        error += "exp is missing in id token <br>"
    if round(datetime.timestamp(datetime.now())) > id_token.get('exp', 0) :
        error += "id token is expired <br>"
    if id_token.get('sub') != id_token_did :
        error += "sub is wrong or missing in id token <br>"
    if id_token.get('i_am_siop') != True :
        error += "I_am_siop is missing in id token <br>"
    if id_token.get('nonce') != nonce :
        error += "nonce is missing in id token <br>"
    return error

    """