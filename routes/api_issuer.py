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

from flask import jsonify, request, render_template, Response, render_template_string
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

except :
    Ed25519 = json.dumps(json.load(open("/home/thierry/sandbox/keys.json", "r"))['talao_Ed25519_private_key'])


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/issuer/<issuer_id>',  view_func=issuer_landing_page, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer_endpoint/<issuer_id>/<stream_id>',  view_func=issuer_endpoint, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer_stream',  view_func=issuer_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/op/issuer_followup',  view_func=issuer_followup, methods = ['GET', 'POST'], defaults={'red' :red})
    return

key = {"kty": "RSA", "kid" : "123", "n": "uEUuur6rqoEMaV3qEgzf4a8jSWzLuftWzW1t9SApbKKKI9_M2ZCValgbUJqpto190zKgBge20d7Hwb24Y_SrxC2e8W7sQMNCEHdCrAvzjtk36o3tKHbsSfYFRfDexZJKQ75tsA_TOSMRKH_xGSO-15ZL86NXrwMrg3CLPXw6T0PjG38IsJ2UHAZL-3ezw7ibDto8LD06UhLrvCMpBlS6IMmDYFRJ-d2KvnWyKt6TyNC-0hNcDS7X0jaODATmDh-rOE5rv5miyljjarC_3p8D2MJXmYWk0XjxzozXx0l_iQyh-J9vQ_70gBqCV1Ifqlu8VkasOfIaSbku_PJHSXesFQ", "e": "AQAB", "d": "SXFleQ-yqu_pSvuf5dbUyoX72fFvV255_8FsMGVDrWUxCrBR3Kr4Klz4cg1atAQ70JfeWNjtQEN7OVhM7CXh6fxG27JanktUguyNmbXfuqEP3L_5dIXFkoroOiKRH4y5Zbu5yxDbnmvAFHS92se48gMYvX_uXDY2uxn5nSVsthdI7TKyMbe_-sXui-Wg8uFmB3pAxueE2a1koDdMNmZJ9bjTopYrIq8HpgI2U_MRPqNU5lVoUVrGQbVMUaLkQsTXjJZJ-aCs9s7TvMYB164tWjc9MyUadnFR0f8wFdn5yDM6Abn7rYZ8lqq9Jfo_QSbb3jk7OoonZF3GWXWfz8MDhw", "p": "ufPro-NIo1vts5TFHJb0_61-qXV2ks5DctqfrJf3qFo5bsQOO5ICcl8zarso8M6qvbSuymC0QWgDKEAi_f3MBM3p9nHOEJiaS8NL2kDArL9NZXZJwE2a4aVmddEI6uVjgzTXZtXlmrvUJovdFu3XefJ5CIrmHtJuHCBrGcH_Etc", "q": "_a8Bho_BHTOMr86Wq3UXD6IFKZb8Aw6DTYa8Lxn1qw8YYDMOEAExChoTsB8M70sdz4G9UW1pBgfYUbXgs7dsXomoiJKsWtcGrSQYouV3smTw74vl3FsFJpiuovM_bD5txRLnHKsi6P97lVAo-6sJMj4KQyTXy0fOnLEU51AeRvM", "dp": "JKXB5wbAJhHUAvRq9Ht7xXf34oXX3I7yFAyqM2Wv1WoSr5XMCEl6WfgRNhO0ueDBHaoiWJg-bjWFicU6IDyInNnIJl2_ct3gatYOePESB_mb00dAubmRsK7cRpPv4ftbZVxgp0-4dIpYAVDHPeGZ-dqjp99YAvMN6FUrRmRJVPk", "dq": "TDWO18XH1eXulcISMV_zlZauxle9TY3GlDutvNinnMPkJsIvr08sVESRNY-eayS9x-DJ5vRfYJhqu-FPp62quJvSLXUiogeG0ezOGeGlm8oHN29nllMhsP6dOAarPvFiOJn9I_elfSmDDtAN_8zZ7mYE3zbqPP9NanUoOnUvI1E", "qi": "fpEiQo_OODLTehEXsdSh9LGN0G9s9MShWKONc5x1pIZXByLxgs-8cfa9uq2P1D-rajgzxPTfdCko3NJhf2AdT3ipDsDfdizGu8Pcd2TefpTa9Td7pVYym88ZJkK5_oR3a27rWrQLXsCOG1ALYO-Yr0-cPSjRZas6sEaRa81W6m0"}
public_key =  {"e":"AQAB","kid" : "123", "kty":"RSA","n":"uEUuur6rqoEMaV3qEgzf4a8jSWzLuftWzW1t9SApbKKKI9_M2ZCValgbUJqpto190zKgBge20d7Hwb24Y_SrxC2e8W7sQMNCEHdCrAvzjtk36o3tKHbsSfYFRfDexZJKQ75tsA_TOSMRKH_xGSO-15ZL86NXrwMrg3CLPXw6T0PjG38IsJ2UHAZL-3ezw7ibDto8LD06UhLrvCMpBlS6IMmDYFRJ-d2KvnWyKt6TyNC-0hNcDS7X0jaODATmDh-rOE5rv5miyljjarC_3p8D2MJXmYWk0XjxzozXx0l_iQyh-J9vQ_70gBqCV1Ifqlu8VkasOfIaSbku_PJHSXesFQ"}


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
def build_access_token(vp, did, issuer_id, mode) :
    # https://jwcrypto.readthedocs.io/en/latest/jwk.html
   
    issuer_key = jwk.JWK(**key) 
    header = {
        "typ" :"JWT",
        "kid": key['kid'],
        "alg": "RS256"
    }
    payload = {
        "iss" : mode.server +'sandbox/op/issuer',
        "sub" : did,
        "iat": datetime.timestamp(datetime.now()),
        "aud" : issuer_id,
        "exp": datetime.timestamp(datetime.now()) + 1000
    }
    if vp :
        if isinstance(vp, str) :
            vp = json.loads(vp)
        payload.update(vp)
    token = jwt.JWT(header=header,claims=payload, algs=["RS256"])
    token.make_signed_token(issuer_key)
    return token.serialize()
"""


"""
Direct access to one VC with filename passed as an argument
"""
async def issuer_landing_page(issuer_id, red, mode) :
    stream_id = str(uuid.uuid1())
    issuer_data = json.loads(db_api.read_issuer(issuer_id))
    credential = json.load(open('./verifiable_credentials/vaccination.jsonld'))
    credential_manifest = json.load(open('./test/credential_manifest/vaccination_credential_manifest.json'))
    credential_manifest['presentation_definition']['input_descriptors'][0]['purpose'] = issuer_data['reason']
    credential_manifest['presentation_definition']['input_descriptors'][0]['constraints']['fields'][0]['filter']['pattern'] = issuer_data['vc']
    print('credential manifest = ', credential_manifest)
    credentialOffer = {
        "type": "CredentialOffer",
        "credentialPreview": credential,
        "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
        "credential_manifest" : credential_manifest,
    }
    url = mode.server + "sandbox/op/issuer_endpoint/" + issuer_id + '/' + stream_id + '?issuer=' + await didkit.key_to_verification_method('tz', Ed25519)
    deeplink_talao = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    deeplink_altme = mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url })
    red.set(stream_id, json.dumps(credentialOffer))
    return render_template('op_issuer_qrcode.html',
                                url=url,
                                deeplink_talao=deeplink_talao,
                                deeplink_atme=deeplink_altme,
                                stream_id=stream_id,
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
    else :
        vm = await didkit.key_to_verification_method('tz', Ed25519)
        issuer_DID = didkit.key_to_did('tz', Ed25519)
        
        # call API du ressource server
        try :
            vp = json.loads(request.form['presentation'])['verifiableCredential']['credentialSubject']
        except : 
            vp = None
            logging.warning('no verifiable presentation')
        access_token = build_access_token(vp, request.form['subject_id'], issuer_id, key, mode)
        header = {"Authorization" : "Bearer " + access_token}
        r = requests.post('http://127.0.0.1:4000/credential', headers=header)
                
        credential =  json.loads(credentialOffer)['credentialPreview']
        credential['credentialSubject']['id'] = request.form['subject_id']
        credential["credentialSubject"] = r.json()
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
        
        # send event to client agent to go forward
        data = json.dumps({'stream_id' : stream_id})
        red.publish('op_issuer', data)
        return jsonify(signed_credential)
        

def issuer_followup(red):  
    stream_id = request.args['stream_id']
    credentialOffer = red.get(stream_id).decode()
    html_string = """
        <!DOCTYPE html>
        <html>
        <body class="h-screen w-screen flex">
        <pre class="whitespace-pre-wrap m-auto">""" + "done" + """</pre>
        </body>
        </html>"""
    return render_template_string(html_string)


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



