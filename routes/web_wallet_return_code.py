from flask import jsonify, request, render_template, render_template_string
from datetime import timedelta
from components import privatekey
import uuid
import logging
from flask_babel import _
import random
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)
did_selected = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'

pattern = {
            "type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": []
                }
            ],
            "challenge": "",
            "domain" : ""
            }

def init_app(app,red, mode) :
    
    app.add_url_rule('/wallet/test/test1',  view_func=test1, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode} )
    app.add_url_rule('/wallet/test/test1_endpoint/<id>',  view_func=test1_endpoint, methods = ['GET', 'POST'], defaults={'red' : red} )

    app.add_url_rule('/wallet/test/test2',  view_func=test2, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode} )
    app.add_url_rule('/wallet/test/test2_endpoint/<id>',  view_func=test2_endpoint, methods = ['GET', 'POST'], defaults={'red' : red} )
    
    app.add_url_rule('/wallet/test/test3',  view_func=test3, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode} )
    app.add_url_rule('/wallet/test/test3_endpoint/<id>',  view_func=test3_endpoint, methods = ['GET', 'POST'], defaults={'red' : red} )

    global PVK
    PVK = privatekey.get_key(mode.owner_talao, 'private_key', mode)
    return

######################### Test 1  ###########

def test1(red, mode) :
    if request.method == 'GET' :
        html_string =  """
        
        <center>
                <h2> Test 1 : user connects to a verifier which returns an error code</h2>
                
                    <form action="/wallet/test/test1" method="POST" >
                  
                        <br><br>                   

                        <button name="code" type="submit" value="400">code 400</button>
                        <button name="code" type="submit" value="401">code 401</button>
                        <button name="code" type="submit" value="403">code 403</button>
                        <button name="code" type="submit" value="408">code 408</button>
                        <button name="code" type="submit" value="429">code 429</button>

                        <button name="code" type="submit" value="500">code 500</button>
                        <button name="code" type="submit" value="501">code 501</button>
                        <button name="code" type="submit" value="504">code 504</button>
                     
                        <button name="code" type="submit" value="000">code random</button>
                   
                    </form>

## Servers return codes
<p>   
 ### 200 OK
 Color : Green  
 Message : No message or Credential presented successfully
 </p>
 <p>
 ### 201 Created
 Color : Green  
 Message : Ressource created
 </p>
 <p>
 ### 400 Bad Request
 Color : Red  
 Message : Bad request
 </p>
 <p>
 ### 401  unauthenticated
 Color : Red  
 Message :  The user must authenticate itself to get the requested response. 
 </p>
 <p>
 ### 403 Forbidden
 Color : Red  
 Message : Unauthorized request.  
 </p>
 <p>
 ### 408 Request Timeout
 Color : Red  
 Message : Request timeout
 </p>
 <p>
 ### 429 : Too many requests
 Color : Red  
 Message : The user has sent too many requests in a given amount of time.
 </p>
 <p>
 ### 500 Internal Server Error
 Color : Red  
 Message : This is a server internal error. Contact the server administrator.
 </p>
 <p>
 ### 501 Not Implemented
 Color : Red  
 Message : Not implemented 
 </p>
 <p>
 ### 504 Gateway Timeout
 Color : Red  
 Message : The gateway encountered a timeout
</p>
 <p>
 ### other code
 Color : Red  
 Message : Received invalid status code
</p>
 

         </center>

                    """
        return render_template_string(html_string)
    if request.method == 'POST' :
        id = str(uuid.uuid1())
        print(id)
        url = mode.server + "wallet/test/test1_endpoint/" + id + '?issuer=' + did_selected
        red.set(id, request.form['code'])
        return render_template('wallet/test/credential_offer_qr_2.html',
                                url=url,
                                )

def test1_endpoint(id, red) :
    code = red.get(id).decode()
    if code == "000" :
        int_code =  random.randrange(300, 999)
    else :
        int_code = int(code)
    print("code = ", int_code)

    pattern['challenge'] = "1234"
    pattern['domain'] = "https://talao.co"
    return jsonify(pattern), int_code 


######################### Test 2 ###########


def test2(red, mode) :
    if request.method == 'GET' :
        html_string =  """
        
        <center>
                <h2> Test 2 : user connects to a verifier, user selects a VC and transfers it to the server which send back an error code </h2>
                
                    <form action="/wallet/test/test2" method="POST" >
                  
                        <br><br>

                        <button name="code" type="submit" value="400">code 400</button>
                        <button name="code" type="submit" value="401">code 401</button>
                        <button name="code" type="submit" value="403">code 403</button>
                        <button name="code" type="submit" value="408">code 408</button>
                        <button name="code" type="submit" value="429">code 429</button>

                        <button name="code" type="submit" value="500">code 500</button>
                        <button name="code" type="submit" value="501">code 501</button>
                        <button name="code" type="submit" value="504">code 504</button>
                     
                        <button name="code" type="submit" value="000">code random</button>
                   
                    </form>

## Servers return codes
<p>   
 ### 200 OK
 Color : Green  
 Message : No message or Credential presented successfully
 </p>
 <p>
 ### 201 Created
 Color : Green  
 Message : Ressource created
 </p>
 <p>
 ### 400 Bad Request
 Color : Red  
 Message : Bad request
 </p>
 <p>
 ### 401  unauthenticated
 Color : Red  
 Message :  The user must authenticate itself to get the requested response. 
 </p>
 <p>
 ### 403 Forbidden
 Color : Red  
 Message : Unauthorized request.  
 </p>
 <p>
 ### 408 Request Timeout
 Color : Red  
 Message : Request timeout
 </p>
 <p>
 ### 429 : Too many requests
 Color : Red  
 Message : The user has sent too many requests in a given amount of time.
 </p>
 <p>
 ### 500 Internal Server Error
 Color : Red  
 Message : This is a server internal error. Contact the server administrator.
 </p>
 <p>
 ### 501 Not Implemented
 Color : Red  
 Message : Not implemented 
 </p>
 <p>
 ### 504 Gateway Timeout
 Color : Red  
 Message : The gateway encountered a timeout
</p>
 <p>
 ### other code
 Color : Red  
 Message : Received invalid status code
</p>
 
         </center>

                    """
        return render_template_string(html_string)

    if request.method == 'POST' :
        id = str(uuid.uuid1())
        url = mode.server + "wallet/test/test2_endpoint/" + id + '?issuer=' + did_selected
        red.set(id, request.form['code'])
        return render_template('wallet/test/credential_offer_qr_2.html',
                                url=url,
                                )

def test2_endpoint(id, red) :
    code = red.get(id).decode()
    if code == "000" :
        int_code =  random.randrange(300, 999)
    else :
        int_code = int(code)

    if request.method == 'GET' :
        print('enter GET')
        pattern['challenge'] = "1234"
        pattern['domain'] = "https://talao.co"
        return jsonify(pattern), 200
    
    if request.method == 'POST' :
        return jsonify("Test2"), int_code


######################### Test 3 ###########


def test3(red, mode) :
    if request.method == 'GET' :
        html_string =  """
        
        <center>
                <h2> Test 3 : user connects to an issuer, user accepts the  VC offered and the server sends back an error code </h2>
                
                    <form action="/wallet/test/test3" method="POST" >
                  
                        <br><br>

                        <button name="code" type="submit" value="400">code 400</button>
                        <button name="code" type="submit" value="401">code 401</button>
                        <button name="code" type="submit" value="403">code 403</button>
                        <button name="code" type="submit" value="408">code 408</button>
                        <button name="code" type="submit" value="429">code 429</button>

                        <button name="code" type="submit" value="500">code 500</button>
                        <button name="code" type="submit" value="501">code 501</button>
                        <button name="code" type="submit" value="504">code 504</button>
                     
                        <button name="code" type="submit" value="000">code random</button>
                   
                    </form>

## Servers return codes
<p>   
 ### 200 OK
 Color : Green  
 Message : No message or Credential presented successfully
 </p>
 <p>
 ### 201 Created
 Color : Green  
 Message : Ressource created
 </p>
 <p>
 ### 400 Bad Request
 Color : Red  
 Message : Bad request
 </p>
 <p>
 ### 401  unauthenticated
 Color : Red  
 Message :  The user must authenticate itself to get the requested response. 
 </p>
 <p>
 ### 403 Forbidden
 Color : Red  
 Message : Unauthorized request.  
 </p>
 <p>
 ### 408 Request Timeout
 Color : Red  
 Message : Request timeout
 </p>
 <p>
 ### 429 : Too many requests
 Color : Red  
 Message : The user has sent too many requests in a given amount of time.
 </p>
 <p>
 ### 500 Internal Server Error
 Color : Red  
 Message : This is a server internal error. Contact the server administrator.
 </p>
 <p>
 ### 501 Not Implemented
 Color : Red  
 Message : Not implemented 
 </p>
 <p>
 ### 504 Gateway Timeout
 Color : Red  
 Message : The gateway encountered a timeout
</p>
 <p>
 ### other code
 Color : Red  
 Message : Received invalid status code
</p>
 
         </center>

                    """
        return render_template_string(html_string)

    if request.method == 'POST' :
        id = str(uuid.uuid1())
        url = mode.server + "wallet/test/test3_endpoint/" + id + '?issuer=' + did_selected
        red.set(id, request.form['code'])
        return render_template('wallet/test/credential_offer_qr_2.html',
                                url=url,
                                )

def test3_endpoint(id, red) :
    code = red.get(id).decode()
    if code == "000" :
        return_code =  random.randrange(300, 999)
    else :
        return_code = int(code)
    credential = json.loads(open('./verifiable_credentials/EmailPass.jsonld', 'r').read())
    credential['description'][0]['@value']= "Add this credential and the server will return an error code " + code + "."
    credential['description'][2]['@value']= "Ajoutez cette attestation et le serveur retournera un core erreur " + code + "."
    credential["issuer"] = did_selected
    credential['id'] = "urn:uuid:..."
    credential['credentialSubject']['id'] = "did:..."
    credential['expirationDate'] =  (datetime.now() + timedelta(days= 365)).isoformat() + "Z"
    credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    credential['credentialSubject']['email'] = "test3@talao.io"

    if request.method == 'GET': 
        # make an offer  
        credential_offer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat(),
            "display": {"backgroundColor": "ffffff"},
             "shareLink" : json.dumps(credential, separators=(',', ':'))
        }
        return jsonify(credential_offer), 200
      
    if request.method == 'POST' :
        return jsonify("Test3"), return_code


