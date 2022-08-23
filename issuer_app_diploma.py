from flask import Flask, jsonify, redirect, request

# Init Flask
app = Flask(__name__)
app.config.update(SECRET_KEY = "abcdefgh")


# data provided by Saas4ssi platform
landing_page_link = 'http://192.168.0.123:3000/sandbox/op/issuer/shgvbdvxgr'
client_secret = "fd0b496e-2210-11ed-84ae-6d9dcad4e1b3"

"""
Step 0 : configure an issuer with https://talao.co/sandbox/saas4ssi
Note the issuer page URL and provides your call back and webhook endpoint
Configure your issuer page, text, color and if needed SSI data as keys, DID method, etc
"""


""" 
Step 1 : Your application redirects user to your issuer page
"""
@app.route('/')
def index():
  """
  add an id as an argument to the link if needed to keep state
  landing_page_link = 'http://192.168.43.67:3000/sandbox/op/issuer/demo&id=my_id'
  """
  return redirect(landing_page_link)


"""
Step 2  your application receives user data and return the credential data to issue
user data is the credential requested to issue the diploma : maybe none if your issuer is behind a portal (university) or maybe an ID card or what ever you may need to authenticate your user
"""
@app.route('/webhook', methods=['POST'])
def credential() :
    if request.headers.get("key") != client_secret :
      return jsonify("Forbidden"), 403
    # data sent by platform
    data = request.get_json()
    
    # send user back data to issuer. If you need to link those data to the issuer which is logged to your portal use the id in the redirect link : id = data['id']
    # event = 'ISSUANCE'
    if data['event'] == 'ISSUANCE' :
      credential = {
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
          "additionalNote": ["DISTRIBUTION MANAGEMENT"],
          "description": "The Master in Information and Computer Sciences (MICS) at the University of Luxembourg enables students to acquire deeper knowledge in computer science by understanding its abstract and interdisciplinary foundations, focusing on problem solving and developing lifelong learning skills.",
          "id": "https://leaston.bcdiploma.com/law-economics-management#LearningAchievment",
          "title": "Master in Information and Computer Sciences"
        },
        "learningSpecification": {
          "ectsCreditPoints": 120,
          "eqfLevel": 7,
          "id": "https://leaston.bcdiploma.com/law-economics-management#LearningSpecification",
          "iscedfCode": ["7"],
          "nqfLevel": ["7"]
          }
        },
        "evidence": {
          "documentPresence": ["Physical"],
          "evidenceDocument": ["Passport"],
          "id": "https://essif.europa.eu/tsr-va/evidence/f2aeec97-fc0d-42bf-8ca7-0548192d5678",
          "subjectPresence": "Physical",
          "type": ["DocumentVerification"],
          "verifier": "did:ebsi:2962fb784df61baa267c8132497539f8c674b37c1244a7a"
        }
      } 
      return jsonify(credential)

    # Optional event = 'RECEIPT': this is to store a copy of the signed credential if needed 
    if data['event'] == 'SIGNED_CREDENTIAL' :
      print("credential issued to store = ", data['vc'])
      return jsonify('ok')
   


""" 
Step 3 : your application get its user back after issuance here 
"""
@app.route('/callback', methods=['GET'])
def callback() :
    print("callback success")
    # Do what you want now.....
    return jsonify ('callback success')




# Python Flask http server loop
if __name__ == '__main__':
    IP = "127.0.0.1"
    app.run( host = IP, port=4000, debug =True)
