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
    app.add_url_rule('/sandbox/issuer/ebsiv2',  view_func=issuer_ebsiv2, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/issuer/gaiax',  view_func=issuer_gaiax, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/issuer/default',  view_func=issuer_default, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/issuer/custom',  view_func=issuer_custom, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/issuer/callback',  view_func=issuer_callback, methods = ['GET'])


def issuer_callback():
    return jsonify("Great !")

def issuer_ebsiv2(mode):
    if mode.myenv == 'aws' :
        api_endpoint = "https://talao.co/sandbox/ebsi/issuer/api/zxhaokccsi"
        client_secret = "0e2e27b3-28a9-11ee-825b-9db9eb02bfb8"
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
        "credential_type" : 'VerifiableDiploma',
        "callback" : mode.server + '/sandbox/issuer/callback'
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    try :
        qrcode =  resp.json()['initiate_qrcode']
    except :
        return jsonify("No qr code")
    return redirect(qrcode) 



def issuer_gaiax(mode):
    if mode.myenv == 'aws' :
        api_endpoint = "https://talao.co/sandbox/ebsi/issuer/api/npwsshblrm"
        client_secret = "731dc86d-2abb-11ee-825b-9db9eb02bfb8"
    elif  mode.server == "http://192.168.0.65:3000/" : # Paris
        api_endpoint = ""
        client_secret = ''
    elif  mode.server == "http://192.168.0.20:3000/"  :        # Houdan
        api_endpoint = ""
        client_secret = ""
    elif  mode.server == "http://192.168.1.54:3000/"  :        # Biscarosse
        api_endpoint = "http://192.168.1.54:3000/sandbox/ebsi/issuer/api/npwsshblrm"
        client_secret = "731dc86d-2abb-11ee-825b-9db9eb02bfb8"
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
        "credential_type" : 'EmployeeCredential',
        "callback" : mode.server + '/sandbox/issuer/callback'
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    try :
        qrcode =  resp.json()['initiate_qrcode']
    except :
        return jsonify("No qr code")
    return redirect(qrcode) 

def issuer_default(mode):
    if mode.myenv == 'aws' :
        api_endpoint = 'https://talao.co/sandbox/ebsi/issuer/api/xjcqarovuv'
        client_secret = '9130b204-89eb-11ed-8d59-838cdcf07a4a'
    elif  mode.server == "http://192.168.0.65:3000/" : # Paris
        api_endpoint = ''
        client_secret = ''
    elif  mode.server == "http://192.168.0.20:3000/"  :        # Houdan
        api_endpoint = ''
        client_secret = ''
    elif  mode.server == "http://192.168.1.54:3000/"  :        # Biscarosse
        api_endpoint = "http://192.168.1.54:3000/sandbox/ebsi/issuer/api/xjcqarovuv"
        client_secret = "9130b204-89eb-11ed-8d59-838cdcf07a4a"
    else :
        return jsonify("Verifiable Id client issue")

    with open('./verifiable_credentials/VerifiableId.jsonld', 'r') as f :
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
        "pre-authorized_code" : "300",
        "credential_type" : 'VerifiableId',
        "callback" : mode.server + '/sandbox/issuer/callback'
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    try :
        qrcode =  resp.json()['initiate_qrcode']
    except :
        return jsonify("No qr code")
    return redirect(qrcode) 

def issuer_custom(mode):
    if mode.myenv == 'aws' :
        api_endpoint = "https://talao.co/sandbox/ebsi/issuer/api/dcizhznqih"
        client_secret = "4aa305b1-2aec-11ee-825b-9db9eb02bfb8"
    elif  mode.server == "http://192.168.0.65:3000/" : # Paris
        api_endpoint = ""
        client_secret = ''
    elif  mode.server == "http://192.168.0.20:3000/"  :        # Houdan
        api_endpoint = ""
        client_secret = ""
    elif  mode.server == "http://192.168.1.54:3000/"  :        # Biscarosse
        api_endpoint = "http://192.168.1.54:3000/sandbox/ebsi/issuer/api/dcizhznqih"
        client_secret = "4aa305b1-2aec-11ee-825b-9db9eb02bfb8"
    else :
        return jsonify("Verifiable Id client issue")

    with open('./verifiable_credentials/VerifiableId.jsonld', 'r') as f :
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
        "pre-authorized_code" : "300",
        "credential_type" : 'VerifiableId',
        "callback" : mode.server + '/sandbox/issuer/callback'
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    try :
        qrcode =  resp.json()['initiate_qrcode']
    except :
        return jsonify("No qr code")
    return redirect(qrcode) 


# Python Flask http server loop
if __name__ == '__main__':
    IP = "127.0.0.1"
    app.run( host = IP, port=4000, debug =True)
