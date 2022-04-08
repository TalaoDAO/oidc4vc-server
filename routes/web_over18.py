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
    key = json.dumps(json.load(open("/home/admin/Talao/keys.json", "r"))['talaonet'].get('talao_Ed25519_private_key'))
except :
    key = json.dumps(json.load(open("/home/thierry/Talao/keys.json", "r"))['talaonet'].get('talao_Ed25519_private_key'))
issuer_did = didkit.keyToDID('tz', key)
vm = didkit.keyToVerificationMethod('tz', key)

 
def init_app(app,red, mode) :
    app.add_url_rule('/over18',  view_func=over18, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/over18/webhook',  view_func=over18_webhook, methods = ['GET', 'POST'], defaults={ 'mode' : mode})
    app.add_url_rule('/over18/endpoint/<id>',  view_func=over18_endpoint, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/over18/stream',  view_func=over18_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/over18/back',  view_func=over18_back, methods = ['GET', 'POST'], defaults={'red' :red})
    return


def add_over18(email, check) :
    if get_over18(email) :
        return 
    conn = sqlite3.connect('over18.db')
    c = conn.cursor()
    data = {'email' : email,
			 'over18_check' : check}
    c.execute("INSERT INTO over18 VALUES (:email, :over18_check)", data)
    conn.commit()
    conn.close()
    return


def get_over18(email) :
	conn = sqlite3.connect('over18.db')
	c = conn.cursor()
	data = { "email" : email}
	c.execute("SELECT over18_check FROM over18 WHERE email = :email", data)
	check = c.fetchone()
	conn.close()
	try :
		return check[0]
	except :
		return None


def over18(red, mode) :
    id = str(uuid.uuid1())
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
            "display": {"backgroundColor": "ffffff"}
    }
    url = mode.server + "over18/endpoint/" + id +'?issuer=' + issuer_did
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    red.set(id, json.dumps(credentialOffer))
    return render_template('/over18/over18.html',
                                url=url,
                                id=id,
                                deeplink=deeplink
                                )


"""
curl --location --request POST 'http://192.168.0.65:3000/over18/webhook' \
--header 'Content-Type: application/json' \
--data-raw '{"event": "VERIFICATION_REVIEWED","key": "b76e244e-26a3-49ef-9c72-3e599bf0b5f2", "status": "approved"}'
"""

def over18_webhook(mode) :
    # get email and id
    webhook = request.get_json()
    logging.info("webhook = %s", webhook)
    if webhook['event' ] == "VERIFICATION_REVIEWED" and webhook['status'] == "approved" :
        key = webhook['key']
        logging.info("identityKey = %s", key)
    elif  webhook['event' ] == "VERIFICATION_REVIEWED" and webhook['status'] != "approved" :
        key = webhook['key']
        logging.warning("Identity not approuved = %s", key)
        return jsonify('Identity not approuved')
    else :
        logging.warning("Verification not completed")
        return jsonify('Verification not completed')
    
    # get identity data and set the database
    """
    url = "https://api.passbase.com/verification/v1/identities/" + key
    headers = {
        'accept' : 'application/json',
        'X-API-KEY' : mode.passbase
    }

    r = requests.get(url, headers=headers)
    logging.info("status code = ", r.status_code)
    if not 199<r.status_code<300 :
        logging.error("API call rejected")
        return jsonify('API call rejected')

    # treatment of API data
    identity = r.json()
    logging.info("API data = ", identity)
    birthDate = identity['ressources']['datapoints']['date_of_birth'] # "1970-01-01"
    email = identity['owner']['email']
    
    email = "thierry.thevenet@talao.io" # for test
    current_date = datetime.now()
    date1 = datetime.strptime(birthDate,'%Y-%m-%d') + timedelta(weeks=18*52)
    over18 = 1 if (current_date > date1) else 0
    """
    email = "thierry.thevenet@talao.io" # for test
    over18 = 1 # for test
    
    # update database email/over18
    add_over18(email, over18)

    

    # send notification by email
    link_text = "Follow this link to get an Over 18 credential " + mode.server + 'over18'
    Talao_message.message("Over 18 credential", email, link_text, mode)

    return jsonify('ok')

def over18_endpoint(id, red):
    try : 
        credentialOffer = json.loads(red.get(id).decode())
    except :
        logging.error("red get id error, or request time out ")
        return jsonify ('request time out'),408

    if request.method == 'GET':
        return jsonify(credentialOffer)

    credential =  credentialOffer['credentialPreview']
    red.delete(id)
    did = request.form['subject_id']
    """
    emailpass = request.form['verifiablepresentaTion'][0]
    email  = emailpass['credentialSubject']['email']
    """
    email = "thierry.thevenet@talao.io" # for test

    over18 = get_over18(email)
    if not over18 :
        data = json.dumps({
                    'id' : id,
                    'check' : 'failed',
                        })
        red.publish('over18', data)
        return jsonify(signed_credential)
    try :
        credential['credentialSubject']['id'] = did
    except :
        logging.error("wallet error")
        return jsonify('ko'), 500

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
    red.publish('over18', data)
    return jsonify(signed_credential)


def over18_back():
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
        <form action="/over18" method="GET" >
        <button  type"submit" >Back</button></form>
        </body>
        </html>"""
    return render_template_string(html_string)


# server event push for user agent EventSource
def over18_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('over18')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()  
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)



