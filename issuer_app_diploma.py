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
    credential = {
  "@context": [ ],
  "credentialSchema": {
    "id": "https://api.preprod.ebsi.eu/trusted-schemas-registry/v1/schemas/0xbf78fc08a7a9f28f5479f58dea269d3657f54f13ca37d380cd4e92237fb691dd",
    "type": "JsonSchemaValidator2018"
  },
  "credentialSubject": {
    "type": "VerifiableDiploma",
    "awardingOpportunity": {
      "awardingBody": {
          "eidasLegalIdentifier": "Unknown",
          "homepage": "https://leaston.bcdiploma.com/",
          "id": "did:ebsi:zdRvvKbXhVVBsXhatjuiBhs",
          "preferredName": "Leaston University",
          "registration": "0597065J"
      },
      "endedAtTime": "2020-06-26T00:00:00Z",
      "id": "https://leaston.bcdiploma.com/law-economics-management#AwardingOpportunity",
      "identifier": "https://certificate-demo.bcdiploma.com/check/87ED2F2270E6C41456E94B86B9D9115B4E35BCCAD200A49B846592C14F79C86BV1Fnbllta0NZTnJkR3lDWlRmTDlSRUJEVFZISmNmYzJhUU5sZUJ5Z2FJSHpWbmZZ",
      "location": "FRANCE",
      "startedAtTime": "2019-09-02T00:00:00Z"
    },
    "dateOfBirth": "1993-04-08",
    "familyName": "DOE",
    "givenName": "Jane",
    "gradingScheme": {
      "id": "https://leaston.bcdiploma.com/law-economics-management#GradingScheme",
      "title": "2 year full-time programme / 4 semesters"
    },
    "id": "did:tz:tz2TXUpeT6Sx1v7Ws7dhZxot87c2afzt68PY",
    "identifier": "0904008084H",
    "learningAchievement": {
      "additionalNote": [
          "DISTRIBUTION MANAGEMENT"
      ],
      "description": "The Master in Information and Computer Sciences (MICS) at the University of Luxembourg enables students to acquire deeper knowledge in computer science by understanding its abstract and interdisciplinary foundations, focusing on problem solving and developing lifelong learning skills.",
      "id": "https://leaston.bcdiploma.com/law-economics-management#LearningAchievment",
      "title": "Master in Information and Computer Sciences"
    },
    "learningSpecification": {
      "ectsCreditPoints": 120,
      "eqfLevel": 7,
      "id": "https://leaston.bcdiploma.com/law-economics-management#LearningSpecification",
      "iscedfCode": [
          "7"
      ],
      "nqfLevel": [
          "7"
      ]
    }
  },
  "evidence": {
    "documentPresence": [
      "Physical"
    ],
    "evidenceDocument": [
      "Passport"
    ],
    "id": "https://essif.europa.eu/tsr-va/evidence/f2aeec97-fc0d-42bf-8ca7-0548192d5678",
    "subjectPresence": "Physical",
    "type": [
      "DocumentVerification"
    ],
    "verifier": "did:ebsi:2962fb784df61baa267c8132497539f8c674b37c1244a7a"
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
