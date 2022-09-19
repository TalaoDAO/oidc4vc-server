from flask import Flask, jsonify, redirect, request
import base64
from datetime import datetime, timedelta
import json
import uuid
import didkit

# Init Flask
app = Flask(__name__)
app.config.update(SECRET_KEY = "abcdefgh")
issuer_key = {
    "alg": "ES256K-R",
    "crv": "secp256k1",
    "d": "_GsK8Br06HXl6qgV0eR9j5FcNkwm6xOCgps9DhtzT9c",
    "kty": "EC",
    "x": "fhHKGHBlgXlGt30upZ4NOiWFUQvbyyajr0whka4z1xA",
    "y": "9eMTPBFHOM9s6IuIyvQ9c6xd79eb4ScAkoUP6_3bEOA"
}


"""
Step 0 : configure an issuer with https://talao.co/sandbox/saas4ssi
Copy the issuer page URL and provide your callback and webhook endpoint
Configure your issuer page, text, color and if needed SSI data as keys, DID method, etc
"""
qrcode_page = 'http://192.168.0.220:3000/sandbox/op/issuer/eahsvvdyzm'
client_secret = 'fe55ca5c-3678-11ed-a2b1-817c238705ae'


""" 
Step 1 : Application redirects user to issuer page with QR code
"""
@app.route('/')
def index():
  return redirect(qrcode_page)


"""
Step 2  Application receives user login and password and return the signed credential to transfer to wallet
"""
@app.route('/webhook', methods=['POST'])
async def credential() :
  if request.headers.get("key") != client_secret :
      return jsonify("Forbidden"), 403
  
  # get user and password
  authorization = request.headers['Authorization']
  user_password_encoded = authorization.split()[1]
  user_password = base64.b64decode(user_password_encoded).decode()
  user = user_password.split(':')[0]
  password = user_password.split(':')[1]

  # check if user exists
  if user != "user1" or password != 'password1' :
    return jsonify("Unauthorized"), 400
  # sign credential and send it back in webhook response
  with open('./verifiable_credentials/VerifiableDiploma.jsonld', 'r') as f :
    credential = json.loads(f.read())
  data = request.get_json()  # data sent to application is 
  credential["credentialSubject"]["id"] = data['holder'] # wallet did
  credential['issuer'] = didkit.key_to_did('ethr', json.dumps(issuer_key))
  credential['expirationDate'] =  (datetime.now().replace(microsecond=0) + timedelta(days= 365)).isoformat() + "Z"
  credential['id'] = "urn:uuid:" + str(uuid.uuid4())
  credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
  didkit_options = {
                "proofPurpose": "assertionMethod",
                "verificationMethod": await didkit.key_to_verification_method('ethr', json.dumps(issuer_key))
      } 
  signed_credential =  await didkit.issue_credential(
                json.dumps(credential),
                didkit_options.__str__().replace("'", '"'),
                json.dumps(issuer_key)
                )
  return jsonify(signed_credential)


""" 
Step 3 : Application get its user back after transfer to wallet 
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
