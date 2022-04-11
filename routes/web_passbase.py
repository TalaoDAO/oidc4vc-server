import sqlite3
from flask import jsonify, request, render_template, Response, render_template_string
import json
from datetime import timedelta, datetime
import didkit
import uuid
from urllib.parse import urlencode

import logging
from flask_babel import Babel, _
import sqlite3
import requests
from components import Talao_message

logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)
EXPIRATION_DELAY = timedelta(weeks=52)

try :
    key = json.dumps(json.load(open("/home/admin/Talao/keys.json", "r"))['talao_Ed25519_private_key'])
except :
    key = json.dumps(json.load(open("/home/thierry/Talao/keys.json", "r"))['talao_Ed25519_private_key'])
issuer_did = didkit.keyToDID('tz', key)
vm = didkit.keyToVerificationMethod('tz', key)

 
def init_app(app,red, mode) :
    app.add_url_rule('/passbase',  view_func=passbase, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/passbase/webhook',  view_func=passbase_webhook, methods = ['GET', 'POST'], defaults={ 'mode' : mode})
    app.add_url_rule('/passbase/endpoint/<id>',  view_func=passbase_endpoint, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/passbase/stream',  view_func=passbase_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/passbase/back',  view_func=passbase_back, methods = ['GET', 'POST'], defaults={'red' :red})
    return


def add_passbase(email, check, did, key, created) :
    if get_passbase(did) :
        return 
    conn = sqlite3.connect('passbase_check.db')
    c = conn.cursor()
    data = {'email' : email,                       
			 'status' : check,
             "did" : did,
             "key" : key,
             "created" : created}      
    c.execute("INSERT INTO webhook VALUES (:email, :status, :did; :key, :created)", data)
    conn.commit()
    conn.close()
    return


def get_passbase(did) :
	conn = sqlite3.connect('passbase_check.db')
	c = conn.cursor()
	data = { "did" : did}
	c.execute("SELECT status, key FROM webhook WHERE did = :did", data)
	check = c.fetchone()
	conn.close()
	try :
		return check[0]
	except :
		return None


def get_identity(passbase_key, mode) :
    url = "https://api.passbase.com/verification/v1/identities/" + passbase_key
    print("api key = ", mode.passbase)
    print("url = ", url)
    headers = {
        'accept' : 'application/json',
        'X-API-KEY' : mode.passbase
    }
    r = requests.get(url, headers=headers)
    logging.info("status code = %s", r.status_code)
    if not 199<r.status_code<300 :
        logging.error("API call rejected")
        return None
    # treatment of API data
    identity = r.json()
    logging.info("API data = %s", identity)
    return identity


def passbase(red, mode) :
    id = str(uuid.uuid1())
    challenge = str(uuid.uuid1())[0:1]
    credential = json.loads(open("./verifiable_credentials/Over18.jsonld", 'r').read())
    credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    credential['expirationDate'] = (datetime.now() + EXPIRATION_DELAY).replace(microsecond=0).isoformat() + "Z"
    credential['issuer'] = issuer_did
    credential['id'] =  "urn:uuid:" + str(uuid.uuid1())
    credential['credentialSubject']['id'] = "did:..."
    credentialOffer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
            "display": {"backgroundColor": "ffffff"},
            "challenge" : challenge
    }
    url = mode.server + "passbase/endpoint/" + id +'?issuer=' + issuer_did
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    red.set(id, json.dumps(credentialOffer))
    return render_template('/passbase/over18.html',
                                url=url,
                                id=id,
                                deeplink=deeplink
                                )


"""
curl --location --request POST 'http://192.168.0.65:3000/passbase/webhook' \
--header 'Content-Type: application/json' \
--data-raw '{"event": "VERIFICATION_REVIEWED","key": "72be8407-a1df-47d7-af1b-e00f6ba4f96c", "status": "approved", "created" : 1582628711}'
"""

def passbase_webhook(mode) :
    # get email and id
    webhook = request.get_json()
    logging.info("webhook = %s", webhook)
    if webhook['event' ] == "VERIFICATION_REVIEWED" :
        logging.info("identityKey = %s", webhook['key'])
    else :
        logging.warning("Verification not completed")
        return jsonify('Verification not completed')
    
    # get identity data and set the database
    identity = get_identity(webhook['key'], mode)
    if not identity :
        logging.error("probleme d acces API")
        return jsonify("probleme d acces API")

    #if not identity['metadata'].get('did') :
    #    logging.error("probleme d encryptage metadata")
    #    return jsonify("probleme d encryptage metadata")
    email = identity['owner']['email']
    email = "thierry.thevenet@talao.io"
    add_passbase(email,
                webhook['status'],
                identity['metadata'].get('did',""),
                webhook['key'],
                webhook['created'] )

    # send notification by email
    link_text = "Follow this link to get an identity credential " + mode.server + 'passbase'
    Talao_message.message("Identity credential", identity['owner']['email'], link_text, mode)
    return jsonify('ok')

def passbase_endpoint(id, red,mode):
    try : 
        credentialOffer = json.loads(red.get(id).decode())
    except :
        logging.error("red get id error, or request time out ")
        return jsonify ('request time out'),408

    if request.method == 'GET':
        return jsonify(credentialOffer)

    credential =  credentialOffer['credentialPreview']
    red.delete(id)
    wallet_did = request.form['subject_id']
    status, passbase_key = get_passbase(wallet_did)
    if status != "approved" :
        data = json.dumps({
                    'id' : id,
                    'check' : 'failed',
                        })
        red.publish('passbase', data)
        return jsonify('not approved')

    identity = get_identity(passbase_key,mode)
    birthDate = identity['resources'][0]['datapoints']['date_of_birth'] # "1970-01-01"
    current_date = datetime.now()
    date1 = datetime.strptime(birthDate,'%Y-%m-%d') + timedelta(weeks=18*52)
    if (current_date > date1) :
        credential['credentialSubject']['id'] = wallet_did
    else :
        logging.error("below 18")
        return jsonify('ko')

    didkit_options = {
            "proofPurpose": "assertionMethod",
            "verificationMethod": vm
        }
    signed_credential =  didkit.issueCredential(
            json.dumps(credential),
            didkit_options.__str__().replace("'", '"'),
            key
    )
        
    # send event to client agent to go forward
    data = json.dumps({
                    'id' : id,
                    'check' : 'success',
                        })
    red.publish('passbase', data)
    return jsonify(signed_credential)


def passbase_back():
    result = request.args['followup']
    if result == 'failed' :
        message = 'Your request failed, sorry'
    else :
        message  = """ <h2>Congrats !<br><br>
        Your Over 18 credential has been signed and transfered to your wallet"</h2>"""
    html_string = """
        <!DOCTYPE html>
        <html>
        <body class="h-screen w-screen flex">
        """ + message + """
        <br><br><br>
        <form action="/passbase" method="GET" >
        <button  type"submit" >Back</button></form>
        </body>
        </html>"""
    return render_template_string(html_string)


# server event push for user agent EventSource
def passbase_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('passbase')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()  
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)



