from flask import Flask, redirect, jsonify
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
    app.add_url_rule('/sandbox/issuer/employee',  view_func=issuer_employee, methods = ['GET'], defaults={'mode' : mode})


def issuer_diploma(mode):
    if mode.myenv == 'aws' :
        api_endpoint = "https://talao.co/sandbox/ebsi/issuer/api/kgivldcsuz"
        client_secret = "c99fa8c0-c330-11ed-b3af-0a1628958560"
    elif  mode.server == "http://192.168.0.65:3000/" : # Paris
        api_endpoint = "http://192.168.0.65:3000/sandbox/ebsi/issuer/api/kofuoqhfyd"
        client_secret = 'e6e78946-9a7d-11ed-9ab1-a3c488752cd7'
    elif  mode.server == "http://192.168.0.20:3000/"  :        # Houdan
        api_endpoint = "http://192.168.0.20:3000/sandbox/ebsi/issuer/api/zkreuxqsjl"
        client_secret = "3a3c8567-1642-11ee-a2c2-dda61b79189f"
    elif  mode.server == "http://192.168.1.54:3000/"  :        # Biscarosse
        api_endpoint = "http://192.168.1.54:3000/sandbox/ebsi/issuer/api/zxhaokccsi"
        client_secret = "0e2e27b3-28a9-11ee-825b-9db9eb02bfb8"
    else :
        return jsonify("University client issue")

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
        "pre-authorized_code" : "100",
        "credential_type" : 'VerifiableDiploma'
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    qrcode =  resp.json()['initiate_qrcode']
    return redirect(qrcode) 



def issuer_employee(mode):
    if mode.myenv == 'aws' :
        api_endpoint = "https://talao.co/sandbox/ebsi/issuer/api/kgivldcsuz"
        client_secret = "c99fa8c0-c330-11ed-b3af-0a1628958560"
    elif  mode.server == "http://192.168.0.65:3000/" : # Paris
        api_endpoint = "http://192.168.0.65:3000/sandbox/ebsi/issuer/api/kofuoqhfyd"
        client_secret = 'e6e78946-9a7d-11ed-9ab1-a3c488752cd7'
    elif  mode.server == "http://192.168.0.20:3000/"  :        # Houdan
        api_endpoint = "http://192.168.0.20:3000/sandbox/ebsi/issuer/api/zkreuxqsjl"
        client_secret = "3a3c8567-1642-11ee-a2c2-dda61b79189f"
    elif  mode.server == "http://192.168.1.54:3000/"  :        # Biscarosse
        api_endpoint = "http://192.168.1.54:3000/sandbox/ebsi/issuer/api/wgfbfgpsnq"
        client_secret = "8fcaf313-295e-11ee-825b-9db9eb02bfb8"
    else :
        return jsonify("Employee credential client issue")

    with open('./verifiable_credentials/EmployeeCredential.jsonld', 'r') as f :
        credential = json.loads(f.read())
    credential['id'] = "urn:uuid:" + str(uuid.uuid4())
    credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
    credential['issued'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
    credential['validFrom'] =  (datetime.now().replace(microsecond=0) + timedelta(days= 365)).isoformat() + "Z"
    credential['expirationDate'] =  (datetime.now().replace(microsecond=0) + timedelta(days= 365)).isoformat() + "Z"
    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : credential, 
        "pre-authorized_code" : "200",
        "credential_type" : 'EmployeeCredential'
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    qrcode =  resp.json()['initiate_qrcode']
    return redirect(qrcode) 

# Python Flask http server loop
if __name__ == '__main__':
    IP = "127.0.0.1"
    app.run( host = IP, port=4000, debug =True)