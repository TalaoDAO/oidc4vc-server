from flask import Flask, jsonify, redirect, request
from jwcrypto import jwk, jwt
import json
import sys

# Init Flask
app = Flask(__name__)
app.config.update(SECRET_KEY = "abcdefgh")


# data provided by Talao
landing_page_link = 'http://192.168.0.220:3000/sandbox/op/issuer/mmowtxhsxf'
public_key =  {"e":"AQAB","kid" : "123", "kty":"RSA","n":"uEUuur6rqoEMaV3qEgzf4a8jSWzLuftWzW1t9SApbKKKI9_M2ZCValgbUJqpto190zKgBge20d7Hwb24Y_SrxC2e8W7sQMNCEHdCrAvzjtk36o3tKHbsSfYFRfDexZJKQ75tsA_TOSMRKH_xGSO-15ZL86NXrwMrg3CLPXw6T0PjG38IsJ2UHAZL-3ezw7ibDto8LD06UhLrvCMpBlS6IMmDYFRJ-d2KvnWyKt6TyNC-0hNcDS7X0jaODATmDh-rOE5rv5miyljjarC_3p8D2MJXmYWk0XjxzozXx0l_iQyh-J9vQ_70gBqCV1Ifqlu8VkasOfIaSbku_PJHSXesFQ"}


""" 
Application redirects user to issuer landing page
"""
@app.route('/')
def index():
    return redirect(landing_page_link)



"""
Ressource server endpoint
The ressource server receives an access token with user data and return its response with the credential data
"""
@app.route('/credential', methods=['POST'])
def credential() :
    # Get user data from access_token received
    access_token = request.headers["Authorization"].split()[1]
    key = jwk.JWK(**public_key)
    try :
        ET = jwt.JWT(key=key, jwt=access_token)
    except :
        print ("signature error")
        sys.exit()
    user_data = json.loads(ET.claims)
    print('user data ', user_data)
    # Do what you need to build the certificate
 
    certificate = {
        "type": "VaccinationEvent",
        "batchNumber": "1183738569",
        "administeringCentre": "MoH",
        "healthProfessional": "MoH",
        "countryOfVaccination": "NZ",
        "recipient": {
            "type": "VaccineRecipient",
            "givenName": "JOHN",
            "familyName": "SMITH",
            "gender": "Male",
            "birthDate": "1958-07-17"
        },
        "vaccine": {
            "type": "Vaccine",
            "disease": "COVID-19",
            "atcCode": "J07BX03",
            "medicinalProductName": "COVID-19 Vaccine Moderna",
            "marketingAuthorizationHolder": "Moderna Biotech"
        }
    }
    return jsonify(certificate)
   


if __name__ == '__main__':
    IP = "127.0.0.1"
    app.run( host = IP, port=4000, debug =True)
