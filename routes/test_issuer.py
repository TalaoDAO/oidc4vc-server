from flask import redirect, jsonify, request
from datetime import datetime, timedelta
import json
import uuid
import requests

REDIRECT = True


def init_app(app,red, mode) :
    app.add_url_rule('/issuer/default',  view_func=issuer_default, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/issuer/hedera',  view_func=issuer_hedera, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/issuer/hedera_2',  view_func=issuer_hedera_2, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/issuer/hedera_3',  view_func=issuer_hedera_3, methods = ['GET'], defaults={'mode' : mode})

    app.add_url_rule('/issuer/gaia-x',  view_func=issuer_gaiax, methods = ['GET'], defaults={'mode' : mode})

    app.add_url_rule('/issuer/default_2',  view_func=issuer_default_2, methods = ['GET'], defaults={'mode' : mode}) # test code return
    app.add_url_rule('/issuer/default_3',  view_func=issuer_default_3, methods = ['GET'], defaults={'mode' : mode}) # test code return


    app.add_url_rule('/issuer/callback',  view_func=issuer_callback, methods = ['GET'])


def issuer_callback():
    return jsonify("Great ! request = " + json.dumps(request.args))


def issuer_default(mode):
  
    api_endpoint = mode.server + "issuer/api/npwsshblrm"
    client_secret = "731dc86d-2abb-11ee-825b-9db9eb02bfb8"
    offer = ["EmailPass"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + 'issuer/callback',
        "redirect" : REDIRECT
        }
    print('ok 1')
    resp = requests.post(api_endpoint, headers=headers, json = data)
    if REDIRECT :
        try :
            qrcode =  resp.json()['redirect_uri']
        except :
            return jsonify("No qr code")
        return redirect(qrcode) 
    else :
        return jsonify(resp.json()['qrcode'])


def issuer_default_2(mode):
 
    api_endpoint = mode.server + "issuer/api/omjqeppxps"
    client_secret = "731dc86d-2abb-11ee-825b-9db9eb02bfb8"

    offer = ["VerifiableId"]

    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + 'issuer/callback',
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
    


def issuer_default_3(mode):
          
    api_endpoint = mode.server + "issuer/api/omjqeppxps"
    client_secret = "731dc86d-2abb-11ee-825b-9db9eb02bfb8"

    offer = ["VerifiableId"]

    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + 'issuer/callback',
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
    
    api_endpoint = mode.server + "issuer/api/cqmygbreop"
    client_secret = "a71f33f9-3100-11ee-825b-9db9eb02bfb8"

    offer = "EmployeeCredential"
    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + 'issuer/callback',
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
   
    api_endpoint = mode.server + "issuer/api/uxzjfrjptk"
    client_secret = "2675ebcf-2fc1-11ee-825b-9db9eb02bfb8"

    offer = ["EmployeeCredential", "VerifiableId"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + 'issuer/callback',
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
   

def issuer_hedera_2(mode):
   
    api_endpoint = mode.server + "issuer/api/fixmtbwkfr"
    client_secret = "2675ebcf-2fc1-11ee-825b-9db9eb02bfb8"

    offer = ["EmployeeCredential", "AgeOver18"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + 'issuer/callback',
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


def issuer_hedera_3(mode):
   
    api_endpoint = mode.server + "issuer/api/mzejfxwvon"
    client_secret = "d4e08abe-37bb-11ee-b7a3-299494bdab61"

    offer = ["EmployeeCredential", "Over18"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Bearer ' + client_secret
    }
    data = { 
        "vc" : build_credential_offered(offer), 
        "pre-authorized_code" : str(uuid.uuid1()),
        "credential_type" : offer,
        "callback" : mode.server + 'issuer/callback',
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
    if isinstance(offer, str) :
        offer = [offer]
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


