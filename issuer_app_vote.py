from flask import Flask, jsonify, redirect, request

# Init Flask
app = Flask(__name__)
app.config.update(SECRET_KEY = "abcdefgh")


# data provided by Saas4ssi platform
landing_page_link = 'http://192.168.0.123:3000/sandbox/op/issuer/fkzpmemedc'
client_secret = '9cc1446c-2203-11ed-84ae-6d9dcad4e1b3'


""" 
Step 1
Application redirects user to issuer page
"""
@app.route('/')
def index():
    return redirect(landing_page_link)



"""
Step 2
Application receives user data and return the credential data to issue
Application get a copy of teh credential seigned and transfered to wallet
"""
@app.route('/webhook', methods=['POST'])
def credential() :
    if request.headers.get("key") != client_secret :
        return jsonify("Forbidden"), 403

    data = request.get_json()    
    # send back data to issue credential
    if data['event'] == 'ISSUANCE' :
        credential = {
            "credentialSubject" : {
                "familyName" : data["vp"]["verifiableCredential"]["credentialSubject"]["familyName"],
                "givenName" : data["vp"]["verifiableCredential"]["credentialSubject"]["givenName"],
                "birthDate" : data["vp"]["verifiableCredential"]["credentialSubject"]["birthDate"],
                "issuedBy" : {
                    "name" : "Peeble.vote",
                    "website" : "https://www.pebble.vote/"
                }
            }
        }
        return jsonify(credential)
    
    # get the credential signed and transfered to wallet to store it locally (optional)
    if data['event'] == 'SIGNED_CREDENTIAL' :
        credential_signed = data['vc']
        print("credential signed = ", credential_signed)
        return jsonify('ok')
 
   


""" 
Step 3
Application get user back after issuance
"""
@app.route('/callback', methods=['GET'])
def callback() :
    return jsonify ('callback success')



if __name__ == '__main__':
    IP = "127.0.0.1"
    app.run( host = IP, port=4000, debug =True)
