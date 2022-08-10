from flask import Flask, jsonify, redirect, request
from jwcrypto import jwk, jwt
import json
import sys

# Init Flask
app = Flask(__name__)
app.config.update(SECRET_KEY = "abcdefgh")


# data provided by Saas4ssi platform
landing_page_link = 'http://192.168.0.220:3000/sandbox/op/issuer/fpbiarujhx'
public_key =  {"e":"AQAB","kid" : "123", "kty":"RSA","n":"uEUuur6rqoEMaV3qEgzf4a8jSWzLuftWzW1t9SApbKKKI9_M2ZCValgbUJqpto190zKgBge20d7Hwb24Y_SrxC2e8W7sQMNCEHdCrAvzjtk36o3tKHbsSfYFRfDexZJKQ75tsA_TOSMRKH_xGSO-15ZL86NXrwMrg3CLPXw6T0PjG38IsJ2UHAZL-3ezw7ibDto8LD06UhLrvCMpBlS6IMmDYFRJ-d2KvnWyKt6TyNC-0hNcDS7X0jaODATmDh-rOE5rv5miyljjarC_3p8D2MJXmYWk0XjxzozXx0l_iQyh-J9vQ_70gBqCV1Ifqlu8VkasOfIaSbku_PJHSXesFQ"}


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
    print('user data received from platform = ', user_data)

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
