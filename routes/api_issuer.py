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
from jwcrypto import jwk, jwt
import requests
import db_api
import ebsi

logging.basicConfig(level=logging.INFO)
OFFER_DELAY = timedelta(seconds= 10*60)

try :
    key = json.dumps(json.load(open("/home/admin/sandbox/keys.json", "r"))['RSA_key'])

except :
    key = json.dumps(json.load(open("/home/thierry/sandbox/keys.json", "r"))['RSA_key'])


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/issuer/<issuer_id>',  view_func=issuer_landing_page, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer_endpoint/<issuer_id>/<stream_id>',  view_func=issuer_endpoint, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer_stream',  view_func=issuer_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/op/issuer_followup',  view_func=issuer_followup, methods = ['GET'])
    return


def build_access_token(vp, did, client_id, key, mode) :
    if isinstance(key, str) :
        key = json.loads(key)
    if key['kty'] == "OKP" :
        alg = "EdDSA"
    elif key['kty'] == "EC" and key["crv"] == "secp256k1" :
        alg = "ES256K"
    elif key['kty'] == "EC" and key["crv"] == "P-256" :
        alg = "ES256"
    elif key['kty'] == "RSA" :
        alg = "RS256"
    else :
        logging.error("key type not supported")
        return None
    
    verifier_key = jwk.JWK(**key) 
    # https://jwcrypto.readthedocs.io/en/latest/jwk.html
    header = {
        "typ" :"JWT",
        "kid": key['kid'],
        "alg": alg
    }
    payload = {
        "iss" : mode.server +'sandbox/op/issuer',
        "iat": datetime.timestamp(datetime.now()),
        "aud" : client_id,
        "exp": datetime.timestamp(datetime.now()) + 1000,
        "sub" : did
    }
    if vp :
        if isinstance(vp, str) :
            vp = json.loads(vp)
        payload['vp'] = vp
    token = jwt.JWT(header=header,claims=payload, algs=["ES256", "ES256K", "EdDSA", "RS256"])
    token.make_signed_token(verifier_key)
    return token.serialize()


"""
Direct access to one VC with filename passed as an argument
"""
def issuer_landing_page(issuer_id, red, mode) :
    session['is_connected'] = True
    try :
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
    except :
        logging.error('issuer id not found')
        return render_template('op_issuer_removed.html')
    try :
        credential = json.load(open('./verifiable_credentials/' + issuer_data['credential_to_issue'] + '.jsonld'))
    except :
        logging.error('credential not found %s', issuer_data['credential_to_issue'])
        return render_template('op_issuer_removed.html')
    try :
        credential_manifest = json.load(open('./credential_manifest/' + issuer_data['credential_to_issue'] + '_credential_manifest.json'))
    except :
        logging.error('credential manifest not found or error %s', issuer_data['credential_to_issue'])
        return render_template('op_issuer_removed.html')
    
    if issuer_data['method'] == "ebsi" :
        issuer_did =  issuer_data['did_ebsi']
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
    if issuer_data['credential_requested'] == "DID" : # No credential requested to issue 
        credential_manifest['presentation_definition'] = {}
    else :
        # one sets up the presentation definition
        credential_manifest['presentation_definition']['id'] = str(uuid.uuid1())
        credential_manifest['presentation_definition']['input_descriptors'][0]['purpose'] = issuer_data['reason']
        credential_manifest['presentation_definition']['input_descriptors'][0]['constraints']['fields'][0]['filter']['pattern'] = issuer_data['credential_requested']
        credential_manifest['presentation_definition']['input_descriptors'][0]['id'] = str(uuid.uuid1())

    credentialOffer = {
        "type": "CredentialOffer",
        "credentialPreview": credential,
        "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
        "credential_manifest" : credential_manifest,
    }
    stream_id = str(uuid.uuid1())
    url = mode.server + "sandbox/op/issuer_endpoint/" + issuer_id + '/' + stream_id + '?issuer=' + issuer_did 
    deeplink_talao = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    deeplink_altme = mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url })
    red.set(stream_id, json.dumps(credentialOffer))
    return render_template('op_issuer_qrcode.html',
                                url=url,
                                deeplink_talao=deeplink_talao,
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


async def issuer_endpoint(issuer_id, stream_id, red, mode):
    try : 
        credentialOffer = red.get(stream_id).decode()
    except :
        logging.error("red.get(id) error")
        return jsonify('server error'), 500
    
    # wallet GET
    if request.method == 'GET':
        return jsonify(credentialOffer)
                        
    # wallet POST
    if request.method == 'POST':
        try :
            red.delete(stream_id)
        except :
            logging.warning('delete stream_id failed')
            pass

        # build access token and call application webhook to receive application data
        vp = json.loads(request.form['presentation'])
        access_token = build_access_token(vp, request.form['subject_id'], issuer_id, key, mode)
        header = {"Authorization" : "Bearer " + access_token}      
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
        r = requests.post(issuer_data['webhook'], headers=header)
        if not r.status_code == requests.codes.ok :
            logging.error('issuer failed to call application')
            data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Issuer failed to call application"})
            red.publish('op_issuer', data)
            return jsonify("application error"),500
        logging.info('status code ok')
        
        try :
            credential_received = r.json()
        except :
            logging.error('aplication data are not json')
            data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Application data are not json"})
            red.publish('op_issuer', data)
            return jsonify("application error"),500

        # prepare credential to issue   
        credential =  json.loads(credentialOffer)['credentialPreview']
        credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
        if credential_received.get('validFrom') :
            credential['validFrom'] =  (datetime.now() + timedelta(days= 365)).isoformat() + "Z"
        else : 
            credential['expirationDate'] =  (datetime.now() + timedelta(days= 365)).isoformat() + "Z"
        credential['id'] = "urn:uuid:" + str(uuid.uuid4())
        credential_type = credential['credentialSubject']['type']

        # extract data sent by application and merge them with verifiable credential data
        try : 
            credential["credentialSubject"] = credential_received['credentialSubject']
        except :
            logging.error('application failed to return correct data')
            data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Application failed to send correct data"})
            red.publish('op_issuer', data)
            return jsonify("application error"),500
        logging.info('credential received ok')

        if credential_received.get('evidence') :
            credential["evidence"] = credential_received['evidence']
        if credential_received.get('credentialSchema') :
            credential["credentialSchema"] = credential_received['credentialSchema']
        credential['credentialSubject']['id'] = request.form['subject_id']
        credential['credentialSubject']['type'] = credential_type

        # sign credential
        if issuer_data['method'] == "ebsi" :
            logging.warning("EBSI issuer")
            credential["issuer"] = issuer_data['did_ebsi']
            signed_credential = ebsi.lp_sign(credential, issuer_data['jwk'], issuer_data['did_ebsi'])
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
                logging.error('Signature error, application failed to return correct data')
                data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Signature error, application failed to send correct data"})
                red.publish('op_issuer', data)
                return jsonify("application error"),500

        logging.info('signature ok')
        # send event to front to go forward callback
        data = json.dumps({'stream_id' : stream_id,
                            "result" : True
                            })
        red.publish('op_issuer', data)
        return jsonify(signed_credential)
        

def issuer_followup():  
    if not session.get('is_connected') :
        logging.error('user is not connectd')
        return render_template('op_issuer_removed.html')
    session.clear()
    issuer_id = request.args.get('issuer_id')
    issuer_data = json.loads(db_api.read_issuer(issuer_id))
    if request.args.get('message') :
        return render_template('op_issuer_failed.html', next = issuer_data['issuer_landing_page'])
    try :
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
    except :
        return render_template('op_issuer_removed.html')
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



