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
key_pem = key1.export_to_pem(private_key=True, password=None).decode()



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
    print(' red get encoded = ', encoded)
    return jsonify(encoded)


def siopv2_verifier() :
    id = str(uuid.uuid1())
    return redirect('/siopv2/verifier/' + id)


# verifier siopv2
def siopv2_verifier_id(id, red, mode) :

# Claims for an EmailPass signed by Talao
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
                                                "Ed25519Signature2018",
                                                "JsonWebSignature2020"
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
                                    "purpose" : "One can only accept EmailPass",
                                    "filter": {
                                        "type": "string",
                                        "pattern": "EmailPass"
                                    }
                                },
                                {
                                    "path": [
                                        "$.issuer"
                                    ],
                                    "purpose" : "One can accept only EmailPass signed by Talao",
                                    "filter": {
                                        "type": "string",
                                        "pattern": "did:web:talao.co"
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
        "subject_syntax_types_supported": [
            "urn:ietf:params:oauth:jwk-thumbprint",
            "did:key",
            "did:web",
            "did:ethr",
            "did:tz"
        ]
    }

    claims_string = json.loads(json.dumps(claims, separators=(',', ':')))
    nonce = secrets.token_urlsafe()[0:10]
    verifier_request = {
                "scope" : "openid",
                "response_type" : "id_token",
                "client_id" : "did:web:talao.co",
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
    print('request uri = ', mode.server + "siopv2/verifier_request_uri/" + id)
    verifier_request_encoded = jwt.encode(verifier_request, key_pem, algorithm="RS256",  headers=jwt_header)
    print('verifier request jwt encoded = ', verifier_request_encoded)
    red.set(id + "_encoded", verifier_request_encoded)
    # preparation du QR code
    red.set(id, json.dumps(verifier_request))
    url = "openid://?" + urlencode(verifier_request)
    len_url = len(url)
    html_string = """  <!DOCTYPE html>
        <html>
        <head></head>
        <body>
        <center>
            <div>  
                <h1> SIOPv2 Verifier</h1>
                <h2>Scan the QR Code bellow with your Talao wallet</h2> 
                <br>  
                <div><img src="{{ qrcode(url)}}"  width="300" ></div>
            </div><br>
            <textarea cols="100" rows="20">{{url}}</textarea>
            <br>len = {{ len_url}}<br>
        
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
                                len_url=len_url,
                                claims=json.dumps(claims, indent=4)
                                )


"""
Endpoint de  la reponse du wallet en POST

"""
def siopv2_verifier_redirect(id, red) :
    try : 
        verifier_request = red.get(id).decode()
        nonce = json.loads(verifier_request)['nonce']
    except :
        print("red.get(id) error")
        return jsonify('server error'), 500

    # if user has aborted the process
    if request.form.get('error') :
        print("error returned by wallet = ", request.form.get('error_description', "Unknown"))
        event_data = json.dumps({"id" : id,
                             "check" : "ko",
                             "message" : request.form.get('error_description', "Unknown")
                             })   
        red.publish('siopv2_verifier', event_data)
        return jsonify("ko, user has probably aborted the process !"),500
    else :
        id_token = request.form['id_token']
        vp_token = request.form['vp_token']
        # let's verify the VP
        didkit_options = {
            "proofPurpose": "authentication",
            "verificationMethod": "did:web:ecole42.talao.co#key-1",
            "challenge" : nonce
            }
        result = json.loads(didkit.verify_presentation(vp_token, json.dumps(didkit_options)))
        print('verification VP = ', result)
        if result['errors'] :
            print("error signature = ", result)
            event_data = json.dumps({"id" : id,
                                    "check" : "ko",
                                    "message" : json.dumps(result)
                                    })   
            red.publish('siopv2_verifier', event_data)
            return jsonify("ko, signature verification failed !"),500
        # just to display the wallet response
        event_data = json.dumps({"id" : id,
                             "check" : "success",
                             })   
        red.set(id + "_vp_token", vp_token)
        red.set(id + "_id_token", id_token)
        red.publish('siopv2_verifier', event_data)
        return jsonify("ok, lets see the wallet response  !"), 200


# This is to get a feedback from the wallet and display id_token and vp_token
def verifier_followup(red) :
    if request.args.get('message') :
        html_string = """  <!DOCTYPE html>
            <html>
            <body>
            <center>  
                <h1> Talao SIOPv2 Verifier</h1>
                <h2> Process aborted by user !</h2>
                <h3> {{message}} </h3>
            </center>
            </body>
            </html>"""
        return render_template_string(html_string, message=request.args.get('message'))
    id = request.args['id']
    vp_token_dict = json.loads(red.get(id + "_vp_token").decode())
    vp_token = json.dumps(vp_token_dict, indent=4)
    id_token_encoded = red.get(id + "_id_token").decode()
    id_token_dict = jwt.decode( id_token_encoded, options={"verify_signature": False})
    id_token= json.dumps(id_token_dict, indent=4)
    html_string = """  <!DOCTYPE html>
        <html>
        <body>
        
            <center>  
                <h1> Talao SIOPv2 Verifier</h1>
                <h2> Congrats ! </h2>
            </center>
            <div>    
                <br><br>
                <h3> Verifiable Presentation received from wallet </h3>
                <br>  
                <pre>{{vp_token}}</pre><br>
                <h3> ID token received from wallet </h3>
                <br>  
                <pre>{{id_token}}</pre>
            </div>
        </body>
        </html>"""
    return render_template_string(html_string, vp_token=vp_token, id_token=id_token)


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