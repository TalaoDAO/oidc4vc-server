from flask import Flask, jsonify, redirect, request
from jwcrypto import jwk, jwt
import json
import sys

# Init Flask
app = Flask(__name__)
app.config.update(SECRET_KEY = "abcdefgh")


# data provided by Saas4ssi platform
landing_page_link = 'http://192.168.43.67:3000/sandbox/op/issuer/demo'
public_key =  {"e":"AQAB","kid" : "123", "kty":"RSA","n":"uEUuur6rqoEMaV3qEgzf4a8jSWzLuftWzW1t9SApbKKKI9_M2ZCValgbUJqpto190zKgBge20d7Hwb24Y_SrxC2e8W7sQMNCEHdCrAvzjtk36o3tKHbsSfYFRfDexZJKQ75tsA_TOSMRKH_xGSO-15ZL86NXrwMrg3CLPXw6T0PjG38IsJ2UHAZL-3ezw7ibDto8LD06UhLrvCMpBlS6IMmDYFRJ-d2KvnWyKt6TyNC-0hNcDS7X0jaODATmDh-rOE5rv5miyljjarC_3p8D2MJXmYWk0XjxzozXx0l_iQyh-J9vQ_70gBqCV1Ifqlu8VkasOfIaSbku_PJHSXesFQ"}


""" 
Step 1
Application redirects user to issuer landing page
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
    credential = {
    "credentialSubject": {
        "familyName": "Skywalker",
        "givenName": "Lea",
        "birthDate": "2000-02-15",
        "hasCredential": {
            "title":  "Certificat Professionnel Chargé(e) de recrutement",
            "description" : "Cette certification se propose de faire face à l'évolution structurelle et souhaitable du métier de chargé(e) de recrutement.",
            "inDefinedTermSet" : "https://talao.io/vocab"
        },
        "issuedBy" : {
            "name": "CFA Recrutement The Adecco Groupe",
            "address" : "4, rue Louis-Guérin, 69626 Villeurbanne, France",
            "logo" : "https://talao.mypinata.cloud/ipfs/QmXytsKby4yF3TFDfo2KUZSmnkdc7hkFGAPDpTyd3pdBpx"
        }
    },
    "evidence": {
        "id": "https://example.edu/evidence/f2aeec97-fc0d-42bf-8ca7-0548192d4231",
        "type": ["DocumentVerification"]
    }
}
   
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
