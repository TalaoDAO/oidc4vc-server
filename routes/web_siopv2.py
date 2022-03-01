import json
from datetime import timedelta, datetime
import uuid
from flask_babel import _
import didkit
from jwcrypto import jwk
from flask import Flask, jsonify, request, Response, render_template_string
from flask_qrcode import QRcode
from datetime import timedelta, datetime
import socket
from urllib.parse import urlencode
import secrets 
import logging
import jwt

app = Flask(__name__)
qrcode = QRcode(app)

logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)
DID_WEB = 'did:web:talao.co'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ2 = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY =  'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'        


OFFER_DELAY = timedelta(seconds= 10*60)
PORT = 3000

did_selected = DID_WEB

try :
    RSA = open("/home/admin/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
except :
    RSA = open("/home/thierry/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()


rsa_key = jwk.JWK.from_pem(RSA.encode())
key_dict = json.loads(rsa_key.export_private())
did = "did:web:talao.co"
key_dict['kid'] = did + "#key-2"
key = json.dumps(key_dict)



def init_app(app,red, mode) :
    app.add_url_rule('/siopv2/verifier',  view_func=siopv2_verifier, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/siopv2/verifier_endpoint/<id>',  view_func=siopv2_verifier_endpoint, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/siopv2/verifier_followup',  view_func=verifier_followup, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/siopv2/verifier_stream',  view_func=verifier_stream, defaults={ 'red' : red})

    return


# verifier siopv2
def siopv2_verifier(red, mode) :
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
    claims_string = json.loads(json.dumps(claims, separators=(',', ':')))
    nonce = secrets.token_urlsafe()[0:10]
    id = secrets.token_urlsafe()[0:10]
    request = {
                "scope" : "openid",
                "response_type" : "id_token",
                "client_id" : "did:web:talao.co",
    	        "redirect_uri" : "http://172.16.9.19:3000/siopv2/verifier_endpoint/" + id,
    	        "response_mode" : "post",
    	        "claims" : claims_string,
    	        "nonce" : nonce
            }
    red.set(id, json.dumps(request))
    url = "openid://?" + urlencode(request)
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
            <textarea cols="50" rows="30">{{url}}</textarea>
            <br>len = {{ len_url}}<br>
        
        </center>
        <script>
            var source = new EventSource('/siopv2/verifier_stream');
            source.onmessage = function (event) {
                const result = JSON.parse(event.data)
                if (result.check == 'success' & result.id == '{{id}}'){
                window.location.href="/siopv2/verifier_followup?id=" + '{{id}}';
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


def siopv2_verifier_endpoint(id, red) :
    try : 
        verifier_request = red.get(id).decode()
    except :
        print("red.get(id) error")
        return jsonify('server error'), 500
    id_token = request.form['id_token']
    vp_token = request.form['vp_token']
    event_data = json.dumps({"id" : id,
                             "check" : "success",
                             })   
    red.set(id + "_vp_token", vp_token)
    red.set(id + "_id_token", id_token)
    red.publish('siopv2_verifier', event_data)
    return jsonify("ok")


def verifier_followup(red) :
    id = request.args['id']
    vp_token_dict = json.loads(red.get(id + "_vp_token").decode())
    vp_token = json.dumps(vp_token_dict, indent=4)
    id_token_encoded = red.get(id + "_id_token").decode()
    id_token_dict = jwt.decode( id_token_encoded, options={"verify_signature": False})
    id_token= json.dumps(id_token_dict, indent=4)

    html_string = """  <!DOCTYPE html>
        <html>
        <head></head>
        <body>
        
            <div>  
                <h1> SIOPv2 Verifier</h1>
                <h2> Verifiable Presentation received from wallet </h2
                <br>  
                <pre>{{vp_token}}</pre><br>
                <h2> ID token received from wallet </h2
                <br>  
                <pre>{{id_token}}</pre>
            </div>
        
        </body>
        </html>"""
    return render_template_string(html_string, vp_token=vp_token, id_token=id_token)


def verifier_event_stream(red):
    pubsub = red.pubsub()
    pubsub.subscribe('siopv2_verifier')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def verifier_stream(red):
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(verifier_event_stream(red), headers=headers)