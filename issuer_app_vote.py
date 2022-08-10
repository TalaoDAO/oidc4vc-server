from flask import Flask, jsonify, redirect, request
from jwcrypto import jwk, jwt
import json
import sys

# Init Flask
app = Flask(__name__)
app.config.update(SECRET_KEY = "abcdefgh")


# data provided by Saas4ssi platform
landing_page_link = 'http://192.168.0.220:3000/sandbox/op/issuer/ualqtjnowx'
public_key =  {'kty': 'RSA', 'kid': '123', 'n': 'pPocyKreTAn3YrmGyPYXHklYqUiSSQirGACwJSYYs-ksfw4brtA3SZCmA2sdAO8a2DXfqADwFgVSxJFtJ3GkHLV2ZvOIOnZCX6MF6NIWHB9c64ydrYNJbEy72oyG_-v-sE6rb0x-D-uJe9DFYIURzisyBlNA7imsiZPQniOjPLv0BUgED0vdO5HijFe7XbpVhoU-2oTkHHQ4CadmBZhelCczACkXpOU7mwcImGj9h1__PsyT5VBLi_92-93NimZjechPaaTYEU2u0rfnfVW5eGDYNAynO4Q2bhpFPRTXWZ5Lhnhnq7M76T6DGA3GeAu_MOzB0l4dxpFMJ6wHnekdkQ', 'e': 'AQAB'}

""" 
Step 1
Application redirects user to issuer page
"""
@app.route('/')
def index():
    return redirect(landing_page_link)



"""
Step 2
Application receives an access token with user data and return the credential data to issue
"""
@app.route('/webhook', methods=['POST'])
def credential() :

    # Get user data from access_token received (optional)
    access_token = request.headers["Authorization"].split()[1]
    key = jwk.JWK(**public_key)
    try :
        ET = jwt.JWT(key=key, jwt=access_token)
    except :
        print ("signature error")
        sys.exit()
    user_data = json.loads(ET.claims)
    #print('user data received from platform = ', user_data)

    # Do what you need to prepare the credential to issue (required)
    try :
        credential = {
    "@context": [],
    "id": "",
    "type": ["VerifiableCredential", "VotersCard"],
    "issuer": "",
    "issuanceDate": "",
    "credentialSubject" : {
        "id": "",
        "type" : "VotersCard",
        "familyName" : user_data["vp"]["verifiableCredential"]["credentialSubject"]["familyName"],
        "givenName" : user_data["vp"]["verifiableCredential"]["credentialSubject"]["givenName"],
        "birthDate" : user_data["vp"]["verifiableCredential"]["credentialSubject"]["birthDate"],
       "issuedBy" : {
            "name" : "Peeble.vote",
            "website" : "https://www.pebble.vote/"
        }
    }
    }
    except :
        credential = dict()
    print("my credential = ", credential)
    return jsonify(credential)
   


""" 
Step 3
Application get user back after issuance
"""
@app.route('/callback', methods=['GET'])
def callback() :
    print("callback success")
    return jsonify ('callback success')





if __name__ == '__main__':
    IP = "127.0.0.1"
    app.run( host = IP, port=4000, debug =True)
