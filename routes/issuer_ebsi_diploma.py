from flask import Flask, redirect
import base64
from datetime import datetime, timedelta
import json
import uuid
import requests
from flask_qrcode import QRcode


# Init Flask
app = Flask(__name__)
app.config.update(SECRET_KEY = "abcdefgh")
qrcode = QRcode(app)

"""
Step 0 : configure an issuer with https://talao.co/sandbox/saas4ssi
Copy the issuer page URL and provide your callback and webhook endpoint
Configure your issuer page, text, color and if needed SSI data as keys, DID method, etc
"""


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/issuer/diploma',  view_func=issuer_diploma, methods = ['GET'], defaults={'mode' : mode})



""" 
Step 1 : Application redirects user to issuer page with QR code
"""
@app.route('/')
def issuer_diploma(mode):
    if mode.myenv == 'aws' :
        api_endpoint = "https://talao.co/sandbox/ebsi/issuer/kgivldcsuz"
        issuer_id = "kgivldcsuz"
        client_secret = "c99fa8c0-c330-11ed-b3af-0a1628958560"
    else :
        # Paris
        api_endpoint = "http://192.168.0.65:3000/sandbox/ebsi/issuer/kofuoqhfyd"
        issuer_id = 'kofuoqhfyd'
        client_secret = 'e6e78946-9a7d-11ed-9ab1-a3c488752cd7'
        # Houdan
        api_endpoint = "http://192.168.0.20:3000/sandbox/ebsi/issuer/zkreuxqsjl"
        issuer_id = "zkreuxqsjl"
        client_secret = "3a3c8567-1642-11ee-a2c2-dda61b79189f"


    with open('./verifiable_credentials/VerifiableDiploma.jsonld', 'r') as f :
        credential = json.loads(f.read())
    credential['id'] = "urn:uuid:" + str(uuid.uuid4())
    credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
    credential['expirationDate'] =  (datetime.now().replace(microsecond=0) + timedelta(days= 365)).isoformat() + "Z"
    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : credential, 
        "pre-authorized_code" : "100"
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    qrcode =  resp.json()['initiate_qrcode']
    print('qrcode = ', qrcode)
    return redirect(qrcode) 


# Python Flask http server loop
if __name__ == '__main__':
    IP = "127.0.0.1"
    app.run( host = IP, port=4000, debug =True)
