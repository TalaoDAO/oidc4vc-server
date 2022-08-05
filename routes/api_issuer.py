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

from flask import jsonify, request, render_template, Response, redirect
import json
from datetime import timedelta, datetime
import uuid
import didkit
import logging
from urllib.parse import urlencode
from jwcrypto import jwk, jwt
import requests
import db_api

logging.basicConfig(level=logging.INFO)
OFFER_DELAY = timedelta(seconds= 10*60)

try :
    Ed25519 = json.dumps(json.load(open("/home/admin/sandbox/keys.json", "r"))['talao_Ed25519_private_key'])
    key = json.dumps(json.load(open("/home/admin/sandbox/keys.json", "r"))['RSA_key'])

except :
    Ed25519 = json.dumps(json.load(open("/home/thierry/sandbox/keys.json", "r"))['talao_Ed25519_private_key'])
    key = json.dumps(json.load(open("/home/thierry/sandbox/keys.json", "r"))['RSA_key'])

#public_key =  {"e": key['e'],"kid" : key['kid'],"kty": key['kty'],"n": key['n']}

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
        payload.update(vp)
    token = jwt.JWT(header=header,claims=payload, algs=["ES256", "ES256K", "EdDSA", "RS256"])
    token.make_signed_token(verifier_key)
    return token.serialize()


"""
Direct access to one VC with filename passed as an argument
"""
async def issuer_landing_page(issuer_id, red, mode) :
    try :
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
        credential = json.load(open('./verifiable_credentials/' + issuer_data['credential_to_issue'] + '.jsonld'))
        credential_manifest = json.load(open('./test/credential_manifest/' + issuer_data['credential_to_issue'] + '_credential_manifest.json'))
    except :
        return render_template('op_issuer_removed.html')
    credential_manifest['presentation_definition']['input_descriptors'][0]['purpose'] = issuer_data['reason']
    credential_manifest['presentation_definition']['input_descriptors'][0]['constraints']['fields'][0]['filter']['pattern'] = issuer_data['credential_requested']
    # TODO to remove
    print('credential manifest = ', credential_manifest)
    credentialOffer = {
        "type": "CredentialOffer",
        "credentialPreview": credential,
        "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
        "credential_manifest" : credential_manifest,
    }
    stream_id = str(uuid.uuid1())
    url = mode.server + "sandbox/op/issuer_endpoint/" + issuer_id + '/' + stream_id + '?issuer=' + await didkit.key_to_verification_method('tz', Ed25519)
    deeplink_talao = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    deeplink_altme = mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url })
    red.set(stream_id, json.dumps(credentialOffer))
    return render_template('op_issuer_qrcode.html',
                                url=url,
                                deeplink_talao=deeplink_talao,
                                deeplink_atme=deeplink_altme,
                                stream_id=stream_id,
                                issuer_id=issuer_id,
                                page_title=issuer_data['page_title'],
                                page_subtitle=issuer_data['page_subtitle'],
                                page_description=issuer_data['page_description'],
                                title=issuer_data['title'],
                                qrcode_message=issuer_data['qrcode_message'],
                                landing_page_url=issuer_data['landing_page_url'],
                                privacy_url=issuer_data['privacy_url'],
                                terms_url=issuer_data['terms_url']
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
        red.delete(stream_id)
       
        # build access token and call application webhook to receive application data
        try :
            credentialSubject = json.loads(request.form['presentation'])['verifiableCredential']['credentialSubject']
        except : 
            credentialSubject = None
            logging.warning('no verifiable presentation')
        access_token = build_access_token(credentialSubject, request.form['subject_id'], issuer_id, key, mode)
        header = {"Authorization" : "Bearer " + access_token}      
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
        r = requests.post(issuer_data['webhook'], headers=header)
        application_data = r.json()

        # prepare credential to issue and sign it   
        # TODO get DID from application user
        vm = await didkit.key_to_verification_method('tz', Ed25519)
        issuer_DID = didkit.key_to_did('tz', Ed25519)  
   
        credential =  json.loads(credentialOffer)['credentialPreview']
        credential['credentialSubject']['id'] = request.form['subject_id']
        credential["credentialSubject"] = application_data
        credential["issuer"] = issuer_DID
        credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
        credential['expirationDate'] =  (datetime.now() + timedelta(days= 365)).isoformat() + "Z"
        credential['id'] = "urn:uuid:" + str(uuid.uuid4())
        didkit_options = {
                "proofPurpose": "assertionMethod",
                "verificationMethod": vm
        }
        signed_credential =  await didkit.issue_credential(
                json.dumps(credential),
                didkit_options.__str__().replace("'", '"'),
                Ed25519
                )
        
        # send event to front to go forward
        data = json.dumps({'stream_id' : stream_id})
        red.publish('op_issuer', data)
        return jsonify(signed_credential)
        

def issuer_followup():  
    issuer_id = request.args.get('issuer_id')
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



