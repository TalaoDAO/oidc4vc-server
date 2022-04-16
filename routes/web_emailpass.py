from flask import jsonify, request, render_template, session, redirect, flash, Response
import json
from components import Talao_message
import uuid
from datetime import timedelta, datetime
import logging
logging.basicConfig(level=logging.INFO)
from flask_babel import _
import secrets
from urllib.parse import urlencode
import didkit
import base64
import subprocess


OFFER_DELAY = timedelta(seconds= 10*60)


DID_TZ1 = "did:tz:tz1NyjrTUNxDpPaqNZ84ipGELAcTWYg6s5Du"
try :
    key_tz1 = json.dumps(json.load(open("/home/admin/Talao/keys.json", "r"))['talao_Ed25519_private_key'])
except :
    key_tz1 = json.dumps(json.load(open("/home/thierry/Talao/keys.json", "r"))['talao_Ed25519_private_key'])
vm_tz1 = didkit.keyToVerificationMethod('tz', key_tz1)
DID = DID_TZ1


def init_app(app,red, mode) :
    app.add_url_rule('/emailpass',  view_func=emailpass, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/emailpass/qrcode',  view_func=emailpass_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode, 'red' : red})
    app.add_url_rule('/emailpass/offer/<id>',  view_func=emailpass_offer, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/emailpass/authentication',  view_func=emailpass_authentication, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/emailpass/stream',  view_func=emailpass_stream, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/emailpass/end',  view_func=emailpass_end, methods = ['GET', 'POST'])
    return


def build_metadata(metadata) :
    with open("passbase-test-private-key.pem", "rb") as f:
        p = subprocess.Popen(
            "/usr/bin/openssl rsautl -sign -inkey " + f.name,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        signature, stderr = p.communicate(input=metadata)
        logging.error('erreur = %s', stderr)
        encrypted_metadata = base64.b64encode(signature)
    return encrypted_metadata.decode()


def emailpass(mode) :
    if request.method == 'GET' :
        return render_template('emailpass/emailpass.html')
    if request.method == 'POST' :
        session['email'] = request.form['email']
        session['code'] = str(secrets.randbelow(99999))
        session['code_delay'] = datetime.now() + OFFER_DELAY
        try : 
            subject = 'Talao : Email authentification  '
            Talao_message.messageHTML(subject, session['email'], 'code_auth', {'code' : session['code']}, mode)
            logging.info('secret code sent = %s', session['code'])
            flash(_(_("Secret code sent to your email.")), 'success')
            session['try_number'] = 1
        except :
            flash(_("Email failed."), 'danger')
            return render_template('emailpass/email.html.html')
    return redirect ('emailpass/authentication')


def emailpass_authentication(mode) :
    if request.method == 'GET' :
        return render_template('emailpass/emailpass_authentication.html')
    if request.method == 'POST' :
        code = request.form['code']
        session['try_number'] +=1
        logging.info('code received = %s', code)
        if code == session['code'] and datetime.now() < session['code_delay'] :
    	    # success exit
            return redirect(mode.server + 'emailpass/qrcode')
        elif session['code_delay'] < datetime.now() :
            flash(_("Code expired."), "warning")
            return render_template('emailpass/emailpass.html')
        elif session['try_number'] > 3 :
            flash(_("Too many trials (3 max)."), "warning")
            return render_template('emailpass/emailpass.html')
        else :
            if session['try_number'] == 2 :
                flash(_('This code is incorrect, 2 trials left.'), 'warning')
            if session['try_number'] == 3 :
                flash(_('This code is incorrect, 1 trial left.'), 'warning')
            return render_template("emailpass/emailpass_authentication.html")


def emailpass_qrcode(red, mode) :
    if request.method == 'GET' :
        id = str(uuid.uuid1())
        url = mode.server + "emailpass/offer/" + id +'?' + urlencode({'issuer' : DID})
        deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
        red.set(id,  session['email'])
        return render_template('emailpass/emailpass_qrcode.html',
                                url=url,
                                deeplink=deeplink,
                                id=id)
   

def emailpass_offer(id, red):
    """ Endpoint for wallet
    """
    credential = json.loads(open('./verifiable_credentials/EmailPass.jsonld', 'r').read())
    credential["issuer"] = DID
    credential['id'] = "urn:uuid:..."
    credential['credentialSubject']['id'] = "did:..."
    credential['expirationDate'] =  (datetime.now() + timedelta(days= 365)).isoformat() + "Z"
    credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    try :
        credential['credentialSubject']['email'] = red.get(id).decode()
    except :
        logging.error('redis pb, id deleted ?')
        data = json.dumps({"url_id" : id, "check" : "failed"})
        red.publish('credible', data)
        return jsonify('id deleted'), 408
    if request.method == 'GET': 
        # make an offer  
        credential_offer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat(),
            #"display": {"backgroundColor": "ffffff"}
        }
        return jsonify(credential_offer)

    elif request.method == 'POST': 
        red.delete(id)   #TODO remplacer par set time
        # init credential
        credential['id'] = "urn:uuid:" + str(uuid.uuid1())
        email =  credential['credentialSubject']['email']
        did = request.form.get('subject_id', 'unknown DID')
        credential['credentialSubject']['id'] = did
        # calcul passbase metadata
        data = json.dumps({"did" : did, "email" : email})
        bytes_metadata = bytearray(data, 'utf-8')
        credential['credentialSubject']['passbaseMetadata'] = build_metadata(bytes_metadata)
        logging.info('metadata = %s', credential['credentialSubject']['passbaseMetadata'])
        # signature 
        didkit_options = {
            "proofPurpose": "assertionMethod",
            "verificationMethod": vm_tz1
            }
        signed_credential =  didkit.issueCredential(
                json.dumps(credential),
                didkit_options.__str__().replace("'", '"'),
                key_tz1)
        if not signed_credential :
            logging.error('credential signature failed')
            data = json.dumps({"url_id" : id, "check" : "failed"})
            red.publish('credible', data)
            return jsonify('Server error'), 500
         # store signed credential on server
        try :
            filename = credential['id'] + '.jsonld'
            path = "./signed_credentials/"
            with open(path + filename, 'w') as outfile :
                json.dump(json.loads(signed_credential), outfile, indent=4, ensure_ascii=False)
        except :
            logging.error('signed credential not stored')
        # send event to client agent to go forward
        data = json.dumps({"url_id" : id, "check" : "success"})
        red.publish('credible', data)
        return jsonify(signed_credential)
 

def emailpass_end() :
    if request.args['followup'] == "success" :
        message = _('Great ! you have now an Email Pass.')
    elif request.args['followup'] == 'expired' :
        message = _('Delay expired.')
    return render_template('emailpass/emailpass_end.html', message=message)


# server event push 
def event_stream(red):
    pubsub = red.pubsub()
    pubsub.subscribe('credible')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def emailpass_stream(red):
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)
