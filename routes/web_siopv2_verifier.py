import json
from datetime import timedelta, datetime
import uuid
from flask_babel import _
import didkit
from jwcrypto import jwk
from flask import Flask, jsonify, request, Response, render_template_string, redirect
from flask_qrcode import QRcode
from datetime import timedelta, datetime
from urllib.parse import urlencode
import secrets 
import logging
import jwt

app = Flask(__name__)
qrcode = QRcode(app)

logging.basicConfig(level=logging.INFO)
OFFER_DELAY = timedelta(seconds= 10*60)

# Talao key 
try :
    RSA = open("/home/admin/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
except :
    RSA = open("/home/thierry/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
rsa_key = jwk.JWK.from_pem(RSA.encode())
key = rsa_key.export_private() # private key jwk
key_dict = json.loads(key)
did = "did:web:talao.co"
key_dict['kid'] = kid = did + "#key-2"
key1 = jwk.JWK(**key_dict)
key_pem = key1.export_to_pem(private_key=True, password=None).decode() # private key pem

vc_type = "EmailPass"
vc_issuer = "did:web:talao.co"
client_id= "did:web:talao.co"


def init_app(app,red, mode) :
    app.add_url_rule('/siopv2/verifier',  view_func=siopv2_verifier, methods = ['GET'])
    app.add_url_rule('/siopv2/verifier/<id>',  view_func=siopv2_verifier_id, methods = ['GET', 'POST'], defaults={'red' :red, "mode" : mode})
    app.add_url_rule('/siopv2/verifier_redirect/<id>',  view_func=siopv2_verifier_redirect, methods = ['POST'], defaults={'red' :red})
    app.add_url_rule('/siopv2/verifier_followup',  view_func=verifier_followup, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/siopv2/verifier_stream',  view_func=verifier_stream, methods = ['GET', 'POST'], defaults={ 'red' : red})
    app.add_url_rule('/siopv2/verifier_request_uri/<id>',  view_func=verifier_request_uri, methods = ['GET', 'POST'], defaults={ 'red' : red})
    return


def verifier_request_uri(id, red):
    encoded = red.get(id + "_encoded").decode()
    return jsonify(encoded)


def siopv2_verifier() :
    id = str(uuid.uuid1())
    return redirect('/siopv2/verifier/' + id)


# verifier siopv2
def siopv2_verifier_id(id, red, mode) :
# Claims for an EmailPass signed by Talao
    vc_type = 'EmailPass'
    claims = {
        "vp_token": {
            "presentation_definition": {
                "id": "emailpass_for_gaiax",
                "input_descriptors": [
                    {
                        "id": "EmailPass issued by Talao",
                        "purpose" : "Test for GAIA-X project",
                        "format" : {
                            "ldp_vc": {
                                "proof_type": [
                                                "JsonWebSignature2020",
                                ]
                            }
                        },
                        "constraints": {
                            "limit_disclosure": "required",
                            "fields": [
                                {
                                    "path": [
                                        "$.credentialSubject.type"
                                    ],
                                    "purpose" : "One can only accept " + vc_type,
                                    "filter": {
                                        "type": "string",
                                        "pattern": vc_type
                                    }
                                },
                                {
                                    "path": [
                                        "$.issuer"
                                    ],
                                    "purpose" : "One can accept only EmailPass signed by Talao",
                                    "filter": {
                                        "type": "string",
                                        "pattern": vc_issuer
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }

# DID method supported by Talao verifier 
    registration = {
        "id_token_signing_alg_values_supported" : [
            "RS256"
        ],
        "subject_syntax_types_supported": [
            "did:web"
        ]
    }
    claims_string = json.loads(json.dumps(claims, separators=(',', ':')))
    nonce = secrets.token_urlsafe()[0:10]
    verifier_request = {
                "scope" : "openid",
                "response_type" : "id_token",
                "client_id" : client_id,
    	        "redirect_uri" : mode.server + "siopv2/verifier_redirect/" + id,
    	        "response_mode" : "post",
    	        "claims" : claims_string,
    	        "nonce" : nonce,
                "registration" : registration,
                "request_uri" : mode.server + "siopv2/verifier_request_uri/" + id,
    }
    # calcul de request 
    jwt_header = {
        "typ" :"JWT",
        "kid": kid
    }
    verifier_request_encoded = jwt.encode(verifier_request, key_pem, algorithm="RS256",  headers=jwt_header)
    red.set(id + "_encoded", verifier_request_encoded)
    # preparation du QR code
    red.set(id, json.dumps(verifier_request))
    url = "openid://?" + urlencode(verifier_request)
    html_string = """  <!DOCTYPE html>
        <html>
        <head></head>
        <body>
        <center>
            <div>  
                <h1>Verifier simulator - SIOPv2</h1>
                <h2>Scan the QR Code bellow with your smartphone wallet or copy the request to your desktop wallet</h2> 
                <br>  
                <div><img src="{{ qrcode(url)}}"  width="300" ></div>
            </div><br><br>
            Request<br>
            <textarea cols="100" rows="20">{{url}}</textarea>
            <br><br>
            <br>
        
        </center>
        <script>
            var source = new EventSource('/siopv2/verifier_stream');
            source.onmessage = function (event) {
                const result = JSON.parse(event.data);
                if (result.check == 'success' & result.id == '{{id}}'){
                    window.location.href="/siopv2/verifier_followup?id=" + '{{id}}';
                }            
                if (result.check == 'ko' & result.id == '{{id}}'){
                    window.location.href="/siopv2/verifier_followup?id=" + "{{id}}" + "&message=" + result.message ;
                }
            };
     
        </script>
        </body>
        </html>"""
    return render_template_string(html_string,
                                url=url,
                                id=id,
                                encoded=verifier_request_encoded,
                                claims=json.dumps(claims, indent=4)
                                )


"""
Endpoint de  la reponse du wallet en POST

"""
def siopv2_verifier_redirect(id, red) :
    try : 
        verifier_request = red.get(id).decode()
        nonce = json.loads(verifier_request)['nonce']
        client_id = json.loads(verifier_request)['client_id']
    except :
        return jsonify('server error'), 500

    # if user has aborted the process
    if request.form.get('error') :
        event_data = json.dumps({"id" : id,
                             "check" : "ko",
                             "message" : request.form.get('error_description', "Unknown")
                             })   
        red.publish('siopv2_verifier', event_data)
        return jsonify("ko, user has probably aborted the process !"),500
    
    try :
        id_token = request.form['id_token']
        vp_token = request.form['vp_token']
    except :
        event_data = json.dumps({"id" : id,
                         "check" : "ko",
                         "message" : "Response malformed"
                         })   
        red.publish('siopv2_verifier', event_data)
        return jsonify("Response malformed"),500

    error = str()
    error += test_vp_token(vp_token, nonce)
    error += test_id_token(id_token, nonce)
    if error :    
        event_data = json.dumps({"id" : id,
                                "check" : "ko",
                                "message" : error
                                })   
        red.publish('siopv2_verifier', event_data)
        return jsonify("ko, signature verification failed !"),500

    # just to say its fine your are logged in !
    event_data = json.dumps({"id" : id,
                         "check" : "success",
                         })   
    red.publish('siopv2_verifier', event_data)
    return jsonify("Everything is fine !"), 200


def test_vp_token(vp_token, nonce) :
    didkit_options = {
            "proofPurpose": "authentication",
            "verificationMethod": "did:web:ecole42.talao.co#key-1",
            "challenge" : nonce
            }
    error = str()
  
    result = didkit.verifyPresentation(vp_token, json.dumps(didkit_options))
   
    if json.loads(result)['errors'] :
        error += "VP signature error , didkit result = " + result + "<br>"
    if json.loads(vp_token)['verifiableCredential']['credentialSubject']['type'] != vc_type :
        error += "VC type error <br>"
    if json.loads(vp_token)['proof']['challenge'] != nonce :
        error += "Different nonce/challenge in VC <br>"
    if json.loads(vp_token)['verifiableCredential']['issuer'] != vc_issuer :
        error += "VC issuer error <br>"
    return error


def test_id_token(id_token, nonce) :
    id_token_kid = jwt.get_unverified_header(id_token)['kid']
    id_token_did = id_token_kid.split('#')[0] 
 
    did_document = json.loads(didkit.resolveDid(id_token_did, '{}'))['didDocument']
    public_key = str()
    error = str()
    for key in did_document['verificationMethod'] :
        if key['id'] == id_token_kid :
            public_key = json.dumps(key['publicKeyJwk'])
            break
    if not public_key :
        error += "public key not found in DID Document <br>"
    try :
        op_key_pem = jwk.JWK(**json.loads(public_key)).export_to_pem(private_key=False, password=None).decode()
        id_token = jwt.decode(id_token, op_key_pem, audience=client_id, algorithms=["RS256"])
    except :
        error += "error decode Id token or audience issue <br>"
    if not id_token.get('iat') :
        error += "error; iat is missing in id token<br> "
    if not id_token.get('exp') :
        error += "error: exp is missing in id token <br>"
    if round(datetime.timestamp(datetime.now())) > id_token.get('exp', 0) :
        error += "id token is expired <br>"
    if id_token.get('sub') != id_token_did :
        error += "error: sub is wrong or missing in id token <br>"
    if id_token.get('i_am_siop') != True :
        error += "error: I am siop is missing in id token <br>"
    if id_token.get('nonce') != nonce :
        error += "error: nonce is missing in id token <br>"
    return error


# This is to get a feedback from the wallet and display id_token and vp_token
def verifier_followup(red) :
    if request.args.get('message') :
        html_string = """  <!DOCTYPE html>
            <html>
            <body>
            <center>  
                <h1> Talao SIOPv2 Verifier</h1>
                <h2>Problems occured</h2>
                <h4> {{message|safe}} </h4>
                 <form   action="/siopv2/verifier" method="GET">
                <br><br>
                <button type="submit">Return</button>
                </form>
            </center>
            </body>
            </html>"""
        return render_template_string(html_string, message=request.args.get('message'))

    id = request.args['id']
    html_string = """  <!DOCTYPE html>
        <html>
        <body>
            <center>  
                <h1> Talao SIOPv2 Verifier</h1>
                <h2> Congrats ! </h2>
                <h2> You are logged in </h2>
                 <form   action="/siopv2/verifier" method="GET">
                <br><br>
                <button type="submit">Return</button>
                </form>
            </center>
        </body>
        </html>"""
    return render_template_string(html_string)


# Event stream to manage the front end page
def verifier_stream(red):
    def verifier_event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('siopv2_verifier')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(verifier_event_stream(red), headers=headers)