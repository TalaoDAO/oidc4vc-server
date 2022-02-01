from flask import jsonify, request, render_template, Response, render_template_string
import json
from datetime import timedelta
from signaturesuite import vc_signature, helpers
from components import privatekey
import uuid
import logging
from flask_babel import _
import didkit
import random


logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)
TEST_REPO = "TalaoDAO/wallet-tools"
REGISTRY_REPO = "TalaoDAO/context"
DID_WEB = 'did:web:talao.co'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ2 = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY =  'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'        

did_selected = DID_ETHR



QueryBYExample = {
            "type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": []
                }
            ],
            "challenge": "",
            "domain" : ""
            }

pattern = QueryBYExample

try :
    RSA = open("/home/admin/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
    P256 = json.dumps(json.load(open("/home/admin/Talao/keys.json", "r"))['talaonet'].get('talao_P256_private_key'))
    Ed25519 = json.dumps(json.load(open("/home/admin/Talao/keys.json", "r"))['talaonet'].get('talao_Ed25519_private_key'))

except :
    RSA = open("/home/thierry/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
    P256 = json.dumps(json.load(open("/home/thierry/Talao/keys.json", "r"))['talaonet'].get('talao_P256_private_key'))
    Ed25519 = json.dumps(json.load(open("/home/thierry/Talao/keys.json", "r"))['talaonet'].get('talao_Ed25519_private_key'))


def init_app(app,red, mode) :
    
    app.add_url_rule('/wallet/test/return_code_GET',  view_func=return_code_GET, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode} )
    app.add_url_rule('/wallet/test/return_code_GET_endpoint/<id>',  view_func=return_code_GET_endpoint, methods = ['GET', 'POST'], defaults={'red' : red} )

    app.add_url_rule('/wallet/test/return_code_POST',  view_func=return_code_POST, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode} )
    app.add_url_rule('/wallet/test/return_code_POST_endpoint/<id>',  view_func=return_code_POST_endpoint, methods = ['GET', 'POST'], defaults={'red' : red} )

    app.add_url_rule('/wallet/test/return_code_POST_co',  view_func=return_code_POST_co, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode} )
    app.add_url_rule('/wallet/test/return_code_POST_co_endpoint/<id>',  view_func=return_code_POST_co_endpoint, methods = ['GET', 'POST'], defaults={'red' : red} )

    global PVK
    PVK = privatekey.get_key(mode.owner_talao, 'private_key', mode)
    return

######################### test return code GET ###########


def return_code_GET(red, mode) :
    if request.method == 'GET' :
        html_string =  """
        
        <center>
                <h2> test return code -> GET </h2>
                
                    <form action="/wallet/test/return_code_GET" method="POST" >
                  
                        <br><br>

                        <button name="code" type="submit" value="200">code 200</button>
                        <button name="code" type="submit" value="201">code 201</button>

                        <button name="code" type="submit" value="400">code 400</button>
                        <button name="code" type="submit" value="401">code 401</button>
                        <button name="code" type="submit" value="403">code 403</button>
                        <button name="code" type="submit" value="408">code 408</button>
                        <button name="code" type="submit" value="429">code 429</button>

                        <button name="code" type="submit" value="500">code 500</button>
                        <button name="code" type="submit" value="501">code 501</button>
                        <button name="code" type="submit" value="504">code 504</button>
                     
                        <button name="code" type="submit" value="000">code random</button>
                   
                    </form>*
         </center>

                    """
        return render_template_string(html_string)
    if request.method == 'POST' :
        id = str(uuid.uuid1())
        print(id)
        url = mode.server + "wallet/test/return_code_GET_endpoint/" + id + '?issuer=' + did_selected
        red.set(id, request.form['code'])
        return render_template('wallet/test/credential_offer_qr_2.html',
                                url=url,
                                )

def return_code_GET_endpoint(id, red) :
    code = red.get(id).decode()
    if code == "000" :
        int_code =  random.randrange(100, 999)
    else :
        int_code = int(code)
    print("code = ", int_code)

    pattern['challenge'] = "1234"
    pattern['domain'] = "https://talao.co"
    return jsonify(pattern), int_code 




######################### test return code POST for presentationRequest ###########


def return_code_POST(red, mode) :
    if request.method == 'GET' :
        html_string =  """
        
        <center>
                <h2> test return code for presentationRequest -> POST </h2>
                
                    <form action="/wallet/test/return_code_POST_co" method="POST" >
                  
                        <br><br>

                        <button name="code" type="submit" value="200">code 200</button>
                        <button name="code" type="submit" value="201">code 201</button>

                        <button name="code" type="submit" value="400">code 400</button>
                        <button name="code" type="submit" value="401">code 401</button>
                        <button name="code" type="submit" value="403">code 403</button>
                        <button name="code" type="submit" value="408">code 408</button>
                        <button name="code" type="submit" value="429">code 429</button>

                        <button name="code" type="submit" value="500">code 500</button>
                        <button name="code" type="submit" value="501">code 501</button>
                        <button name="code" type="submit" value="504">code 504</button>
                     
                        <button name="code" type="submit" value="000">code random</button>
                   
                    </form>*
         </center>

                    """
        return render_template_string(html_string)
    if request.method == 'POST' :
        id = str(uuid.uuid1())
        print(id)
        url = mode.server + "wallet/test/return_code_POST_co_endpoint/" + id + '?issuer=' + did_selected
        red.set(id, request.form['code'])
        return render_template('wallet/test/credential_offer_qr_2.html',
                                url=url,
                                )

def return_code_POST_co_endpoint(id, red) :
    code = red.get(id).decode()
    if code == "000" :
        int_code =  random.randrange(100, 999)
    else :
        int_code = int(code)
    if request.method == 'GET' :
        pattern['challenge'] = "1234"
        pattern['domain'] = "https://talao.co"
        return jsonify(pattern), 200
    if request.method == 'POST' :
        return jsonify("Test return code POST / credential offer"), int_code




######################### test return code POST for credentialOffer ###########


def return_code_POST_co(red, mode) :
    if request.method == 'GET' :
        html_string =  """
        
        <center>
                <h2> test return code for credentialOffer -> POST </h2>
                
                    <form action="/wallet/test/return_code_POST" method="POST" >
                  
                        <br><br>

                        <button name="code" type="submit" value="200">code 200</button>
                        <button name="code" type="submit" value="201">code 201</button>

                        <button name="code" type="submit" value="400">code 400</button>
                        <button name="code" type="submit" value="401">code 401</button>
                        <button name="code" type="submit" value="403">code 403</button>
                        <button name="code" type="submit" value="408">code 408</button>
                        <button name="code" type="submit" value="429">code 429</button>

                        <button name="code" type="submit" value="500">code 500</button>
                        <button name="code" type="submit" value="501">code 501</button>
                        <button name="code" type="submit" value="504">code 504</button>
                     
                        <button name="code" type="submit" value="000">code random</button>
                   
                    </form>*
         </center>

                    """
        return render_template_string(html_string)
    if request.method == 'POST' :
        id = str(uuid.uuid1())
        print(id)
        url = mode.server + "wallet/test/return_code_POST_co__endpoint/" + id + '?issuer=' + did_selected
        red.set(id, request.form['code'])
        return render_template('wallet/test/credential_offer_qr_2.html',
                                url=url,
                                )

def return_code_POST_endpoint(id, red) :
    code = red.get(id).decode()
    if code == "000" :
        int_code =  random.randrange(100, 999)
    else :
        int_code = int(code)
    if request.method == 'GET' :
        pattern['challenge'] = "1234"
        pattern['domain'] = "https://talao.co"
        return jsonify(pattern), 200
    if request.method == 'POST' :
        return jsonify("Test return code POST / credentialOffer"), int_code






