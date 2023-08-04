from flask import Flask, redirect, jsonify, request
import base64
from datetime import datetime, timedelta
import json
import uuid
import requests
from flask_qrcode import QRcode

REDIRECT = True


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
    app.add_url_rule('/sandbox/issuer/default',  view_func=issuer_default, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/issuer/hedera',  view_func=issuer_hedera, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/issuer/gaia-x',  view_func=issuer_gaiax, methods = ['GET'], defaults={'mode' : mode})

    app.add_url_rule('/sandbox/issuer/callback',  view_func=issuer_callback, methods = ['GET'])


def issuer_callback():
    return jsonify("Great ! pre-authorized_code =" + request.args.get('pre-authorized_code'))


def issuer_ebsiv2(mode):
    if mode.myenv == 'aws' :
        api_endpoint = "https://talao.co/sandbox/ebsi/issuer/api/zxhaokccsi"
        client_secret = "0e2e27b3-28a9-11ee-825b-9db9eb02bfb8"
    
    elif  mode.server == "http://192.168.0.20:3000/"  :        # Houdan
        api_endpoint = "http://192.168.0.20:3000/sandbox/ebsi/issuer/api/zxhaokccsi"
        client_secret = "0e2e27b3-28a9-11ee-825b-9db9eb02bfb8"
    
    elif  mode.server == "http://192.168.0.65:3000/"  :        # Paris
        api_endpoint = "http://192.168.0.65:3000/sandbox/ebsi/issuer/api/zxhaokccsi"
        client_secret = "0e2e27b3-28a9-11ee-825b-9db9eb02bfb8"
    else :
        return jsonify("Profile EBSIV2 client issue")

    offer = 'VerifiableDiploma'
    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + '/sandbox/issuer/callback',
        "redirect" : REDIRECT
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    if REDIRECT :
        try :
            qrcode =  resp.json()['redirect_uri']
        except :
            return jsonify("No qr code")
        return redirect(qrcode) 
    else :
        return jsonify(resp.json()['qrcode'])
   



def issuer_default(mode):
    if mode.myenv == 'aws' :
        api_endpoint = "https://talao.co/sandbox/ebsi/issuer/api/npwsshblrm"
        client_secret = "731dc86d-2abb-11ee-825b-9db9eb02bfb8"
    elif  mode.server == "http://192.168.0.20:3000/"  :        # Houdan
        api_endpoint = "http://192.168.0.20:3000/sandbox/ebsi/issuer/api/npwsshblrm"
        client_secret = "731dc86d-2abb-11ee-825b-9db9eb02bfb8"
    elif  mode.server == "http://192.168.0.65:3000/"  :        # Paris
        api_endpoint = "http://192.168.0.65:3000/sandbox/ebsi/issuer/api/npwsshblrm"
        client_secret = "731dc86d-2abb-11ee-825b-9db9eb02bfb8"
    else :
        return jsonify("Profile DEFAULT client issue")

    offer = ["ProofOfAsset", "EmployeeCredential"]

    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + '/sandbox/issuer/callback',
        "redirect" : REDIRECT
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    if REDIRECT :
        try :
            qrcode =  resp.json()['redirect_uri']
        except :
            return jsonify("No qr code")
        return redirect(qrcode) 
    else :
        return jsonify(resp.json()['qrcode'])


def issuer_gaiax(mode):
    if mode.myenv == 'aws' :
        api_endpoint = "https://talao.co/sandbox/ebsi/issuer/api/mfyttabosy"
        client_secret = "c0ab5d96-3113-11ee-a3e3-0a1628958560"
    elif  mode.server == "http://192.168.0.20:3000/"  :        # Houdan
        api_endpoint = "http://192.168.0.20:3000/sandbox/ebsi/issuer/api/cqmygbreop"
        client_secret = "a71f33f9-3100-11ee-825b-9db9eb02bfb8"
    elif  mode.server == "http://192.168.0.65:3000/"  :        # Paris
        api_endpoint = ""
        client_secret = ""
    else :
        return jsonify("Profile GAIA-X client issue")

    offer = ["EmployeeCredential", "ProofOfAsset"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + '/sandbox/issuer/callback',
        "redirect" : REDIRECT
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    if REDIRECT :
        try :
            qrcode =  resp.json()['redirect_uri']
        except :
            return jsonify("No qr code")
        return redirect(qrcode) 
    else :
        return jsonify(resp.json()['qrcode'])


def issuer_hedera(mode):
    if mode.myenv == 'aws' :
        api_endpoint = "https://talao.co/sandbox/ebsi/issuer/api/nkpbjplfbi"
        client_secret = "ed055e57-3113-11ee-a280-0a1628958560"
    
    elif  mode.server == "http://192.168.0.20:3000/"  :        # Houdan
        api_endpoint = "http://192.168.0.20:3000/sandbox/ebsi/issuer/api/uxzjfrjptk"
        client_secret = "2675ebcf-2fc1-11ee-825b-9db9eb02bfb8"
    
    elif  mode.server == "http://192.168.0.65:3000/"  :        # Paris
        api_endpoint = "http://192.168.0.65:3000/sandbox/ebsi/issuer/api/uxzjfrjptk"
        client_secret = "2675ebcf-2fc1-11ee-825b-9db9eb02bfb8"
    else :
        return jsonify("Profile HEDERA client issue")

    offer = "EmployeeCredential"
    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + '/sandbox/issuer/callback',
        "redirect" : REDIRECT
        }
    resp = requests.post(api_endpoint, headers=headers, json = data)
    if REDIRECT :
        try :
            qrcode =  resp.json()['redirect_uri']
        except :
            return jsonify("No qr code")
        return redirect(qrcode) 
    else :
        return jsonify(resp.json()['qrcode'])
   

def build_credential_offered(offer) :
    credential_offered = dict()
    for vc in offer :
        try :
            with open('./verifiable_credentials/' + vc + '.jsonld', 'r') as f :
                credential = json.loads(f.read())
        except :
            return
        credential['id'] = "urn:uuid:" + str(uuid.uuid4())
        credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
        credential['issued'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
        credential['validFrom'] =  (datetime.now().replace(microsecond=0) + timedelta(days= 365)).isoformat() + "Z"
        credential['expirationDate'] =  (datetime.now().replace(microsecond=0) + timedelta(days= 365)).isoformat() + "Z"
        credential_offered[vc] = credential
    return credential_offered

# Python Flask http server loop
if __name__ == '__main__':
    IP = "127.0.0.1"
    app.run( host = IP, port=4000, debug =True)
