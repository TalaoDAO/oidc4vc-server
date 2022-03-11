
"""
https://server.com/.well-known/openid-configuration





"""
import json
from datetime import timedelta, datetime
import uuid
from flask_babel import _
import didkit
from jwcrypto import jwk
from flask import Flask, jsonify, request, Response, render_template_string, redirect
from flask_qrcode import QRcode
from datetime import timedelta, datetime
import socket
from urllib.parse import urlencode, parse_qs
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

# key Talao
try :
    RSA = open("/home/admin/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
except :
    RSA = open("/home/thierry/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
t_key = jwk.JWK.from_pem(RSA.encode())
talao_key = t_key.export_private()

rsa_key = jwk.JWK.from_pem(RSA.encode())
key_dict = json.loads(rsa_key.export_private())
did = "did:web:talao.co"
kid = "did:web:talao.co#key-2"
key_dict['kid'] = kid
key = json.dumps(key_dict)


def init_app(app,red, mode) :
    app.add_url_rule('/.well-known/openid-configuration',  view_func=openid_configuration, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})

    app.add_url_rule('/siopv2/issuer/email',  view_func=issuer_email, methods = ['GET'])
    app.add_url_rule('/siopv2/issuer/email/<id>',  view_func=issuer_email_id, methods = ['GET', 'POST'])
    app.add_url_rule('/siopv2/issuer/followup/<id>',  view_func=issuer_followup, methods = ['GET', 'POST'])

    app.add_url_rule('/siopv2/issuer/token',  view_func=issuer_token, methods = ['GET', 'POST'])
    app.add_url_rule('/siopv2/issuer/credential',  view_func=issuer_credential, methods = ['GET', 'POST'], defaults={ 'red' : red})
    app.add_url_rule('/siopv2/issuer_stream',  view_func=issuer_stream, defaults={ 'red' : red})
    return


def openid_configuration(mode)  :
    oidc = {"issuer": mode.server + "siopv2/issuer",
        "nonce_endpoint" : mode.server + "siopv2/issuer/nonce",
        "authorization_endpoint": mode.server + "siopv2/issuer/authorize",
        "token_endpoint": mode.server + "siopv2/issuer/token",
        "credential_endpoint": mode.server + "siopv2/issuer/credential",
        "response_types_supported": [
            "code",
            "id_token",
            "token id_token"
        ]
    }
    return jsonify(oidc)


def issuer_email() :
    id = str(uuid.uuid1())
    return redirect('/siopv2/issuer/email/' + id)


def issuer_email_id(id) :
    if request.method == 'GET' :
        html_string = """  <!DOCTYPE html>
        <html>
        <head></head>
        <body>
        <br><br>
        <center>
        <form name="form" class="user" action="/siopv2/issuer/email/{{id}}" method="post">
                                        <div class="form-group">
                                       <input  type="text" placeholder="Enter your email"  name="email"></div>
                                       

                                        <button type="submit">'Next'</button>
                            </form>
        </center>
        </body>
        </html>"""
        return render_template_string(html_string, id=id) 
    if request.method == 'POST' :
        # on prepare token de reponse
        jwt_header = {
            "typ" :"JWT",
            "kid": kid
        }
        now = datetime.now()
        nonce = secrets.token_urlsafe()[0:10]
        timestamp = round(datetime.timestamp(now))
        jwt_payload = {
            "iat": timestamp,
            "exp": timestamp + 30,
            "sub" : "user#1200",
            "iss": did,
            "id" : id,
            "sub_jwk" :  {
                "kty": "RSA",
                "kid" : kid,
                "n": key_dict['n'],
                "e": "AQAB"
            },
            "nonce": nonce
        }
        encoded = jwt.encode(jwt_payload, RSA, algorithm="RS256",  headers=jwt_header)
        code = "code=" + encoded + "&state=" + id
        html_string = """  <!DOCTYPE html>
        <html>
        <head></head>
        <body>
        <center>
            <div>  
                <h1> SIOPv2 Issuer</h1>
                <h2>Scan the QR Code bellow with your Talao wallet</h2> 
                <br>  
                <div><img src="{{ qrcode(code)}}"  width="300" ></div>
            </div><br>
            <textarea cols="50" rows="30">{{code}}</textarea>
        
        </center>
        <script>
            var source = new EventSource('/siopv2/issuer_stream');
            source.onmessage = function (event) {
                const result = JSON.parse(event.data)
                if (result.check == 'success' & result.id == '{{id}}'){
                window.location.href="/siopv2/issuer_followup?id=" + '{{id}}';
            }
        };
        </script>
        </body>
        </html>"""
        return render_template_string(html_string, code=code)


# token endpoint
def issuer_token() :
    if (request.content_type.startswith('application/json')):
        data = request.data.decode()
        code = json.loads(data)['code']
    elif(request.content_type.startswith("application/x-www-form-urlencoded")):
        try : 
            data = list(request.form.to_dict().keys())[0]
            code = json.loads(data)['code']
        except :
            data = request.form
            code = json.loads(data)['code']
    else :
        response = {"error" : "invalid_request"}
        return jsonify(response), 404      
    try :
        decoded_code = jwt.decode( code, options={"verify_signature": False})
        id = decoded_code['id']
        print('id retrouvé = ', id)
    except :
        response = {"error" : "invalid_request"}
        return jsonify(response), 404
    jwt_header = {
            "typ" :"JWT",
            "kid": kid
    }
    timestamp = round(datetime.timestamp(datetime.now()))
    jwt_payload = {
            "iat": timestamp,
            "exp": timestamp + 12*60*60,
            "id" : id,
            "iss": did,
            "sub_jwk" :  {
                "kty": "RSA",
                "kid" : kid,
                "n": key_dict['n'],
                "e": "AQAB"
            }
    }
    access_token = jwt.encode(jwt_payload, RSA, algorithm="RS256",  headers=jwt_header)
    response = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 86400,
            "id_token": "",
            "c_nonce": "tZignsnFbp",
            "c_nonce_expires_in": 86400
    }
    return jsonify(response)
        


def issuer_credential(red) :
    data_credential = json.loads(request.data.decode())
    did = data_credential['id']
    vp_token = data_credential.get('vp_token')
    type = data_credential.get('type')
    print('vp token = ', vp_token)
    id = ""
    credential = json.load(open('./verifiable_credentials/' + type + '.jsonld', 'r'))
    credential["issuer"] = "did:web:talao.co"
    credential['credentialSubject']['id'] = did
    credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
    credential['expirationDate'] =  (datetime.now() + timedelta(days= 365)).isoformat() + "Z"
    credential['id'] = "urn:uuid:" + str(uuid.uuid4())
    credential["credentialSubject"]["email"] = "test_siopv2@talao.co"
    didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": kid,
        }
    try :
        signed_credential = didkit.issue_credential(json.dumps(credential,ensure_ascii=False),
                                    didkit_options.__str__().replace("'", '"'),
                                     talao_key)
    except :
        signed_credential = didkit.issueCredential(json.dumps(credential,ensure_ascii=False),
                                    didkit_options.__str__().replace("'", '"'),
                                     talao_key)
    event_data = json.dumps({"id" : id, "check" : "success"})   
    red.publish('siopv2_issuer', event_data)                                 
    return jsonify(signed_credential)


def issuer_followup(id) :
    id = request.args['id']
    html_string = """  <!DOCTYPE html>
        <html>
        <head></head>
        <body>
        
            <div>  
                <h1> SIOPv2 Issuer</h1>
                <h2> Verifiable Credential issuer to wallet</h2
                <br>  
                id = {{id}}
            </div>
        
        </body>
        </html>"""
    return render_template_string(html_string, id=id)


def issuer_stream(red):
    def issuer_event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('siopv2_issuer')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(issuer_event_stream(red), headers=headers)