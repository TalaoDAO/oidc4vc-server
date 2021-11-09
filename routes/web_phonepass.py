from flask import jsonify, request, render_template, session, redirect, flash, Response
import json
from components import privatekey, sms
import uuid
import secrets
from datetime import timedelta, datetime
import logging
logging.basicConfig(level=logging.INFO)
from signaturesuite import vc_signature
from flask_babel import _
from urllib.parse import urlencode

OFFER_DELAY = timedelta(seconds= 10*60)

DID_WEB = 'did:web:talao.co'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ2 = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY = 'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'
DID = DID_TZ2

def init_app(app,red, mode) :
    app.add_url_rule('/phonepass',  view_func=phonepass, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/phonepass/qrcode',  view_func=phonepass_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode, 'red' : red})
    app.add_url_rule('/phonepass/offer/<id>',  view_func=phonepass_offer, methods = ['GET', 'POST'], defaults={'mode' : mode, 'red' : red})
    app.add_url_rule('/phonepass/authentication',  view_func=phonepass_authentication, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/phonepass/stream',  view_func=phonepass_stream, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/phonepass/end',  view_func=phonepass_end, methods = ['GET', 'POST'])
    return

"""
phone Pass : credential offer for a VC with phone only
VC is signed by Talao

"""

def phonepass(mode) :
    if request.method == 'GET' :
        return render_template('phonepass/phonepass.html')
    if request.method == 'POST' :
        # traiter phone
        session['phone'] = request.form['phone']
        session['code'] = str(secrets.randbelow(99999))
        session['code_delay'] = datetime.now() + timedelta(seconds= 180)
        try : 
            sms.send_code(session['phone'], session['code'], mode)
            logging.info('secret code sent = %s', session['code'])
            flash(_(_("Secret code sent to your phone.")), 'success')
            session['try_number'] = 1
        except :
            flash(_("phone failed."), 'danger')
            return render_template('phonepass/phone.html.html')
    return redirect ('phonepass/authentication')


def phonepass_authentication(mode) :
    if request.method == 'GET' :
        return render_template('phonepass/phonepass_authentication.html')
    if request.method == 'POST' :
        code = request.form['code']
        session['try_number'] +=1
        logging.info('code received = %s', code)
        if code == session['code'] and datetime.now() < session['code_delay'] :
    	    # success exit
    	    return redirect(mode.server + 'phonepass/qrcode')
        elif session['code_delay'] < datetime.now() :
    	    flash(_("Code expired."), "warning")
    	    return render_template('phonepass/phonepass.html')
        elif session['try_number'] > 3 :
    	    flash(_("Too many trials (3 max)."), "warning")
    	    return render_template('phonepass/phonepass.html')
        else :
    	    if session['try_number'] == 2 :
    		    flash(_('This code is incorrect, 2 trials left.'), 'warning')
    	    if session['try_number'] == 3 :
    		    flash(_('This code is incorrect, 1 trial left.'), 'warning')
    	    return render_template("phonepass/phonepass_authentication.html")


def phonepass_qrcode(red, mode) :
    if request.method == 'GET' :
        id = str(uuid.uuid1())
        url = mode.server + "phonepass/offer/" + id +'?' + urlencode({'issuer' : DID})
        red.set(id,  session['phone'])
        logging.info('url = %s', url)
        return render_template('phonepass/phonepass_qrcode.html', url=url, id=id)
   

def phonepass_offer(id, red, mode):
    """ Endpoint for wallet
    """
    credential = json.loads(open('./verifiable_credentials/PhonePass.jsonld', 'r').read())
    credential["issuer"] = DID
    credential['id'] = "urn:uuid:..."
    credential['credentialSubject']['id'] = "did:..."
    credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    credential['credentialSubject']['phone'] = red.get(id).decode()
    credential['expirationDate'] =  (datetime.now() + timedelta(days= 365)).isoformat() + "Z"
    if request.method == 'GET': 
        # make an offer  
        credential_offer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
            "display" : {"backgroundColor" : "ffffff"},
            "shareLink" : json.dumps(credential, separators=(',', ':'))
        }
        return jsonify(credential_offer)
    elif request.method == 'POST': 
        red.delete(id)   
        # sign credential
        credential['id'] = "urn:uuid:" + str(uuid.uuid1())
        credential['credentialSubject']['id'] = request.form.get('subject_id', 'unknown DID')
        pvk = privatekey.get_key(mode.owner_talao, 'private_key', mode)
        signed_credential = vc_signature.sign(credential, pvk, DID)
        if not signed_credential :
            logging.error('credential signature failed')
            data = json.dumps({"url_id" : id, "check" : "failed"})
            red.publish('credible', data)
            return jsonify('server error'), 500
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
 

def phonepass_end() :
    if request.args['followup'] == "success" :
        message = _('Great ! you have now a Phone Pass.')
    elif request.args['followup'] == 'expired' :
        message = _('Delay expired.')
    return render_template('phonepass/phonepass_end.html', message=message)


# server event push 
def event_stream(red):
    pubsub = red.pubsub()
    pubsub.subscribe('credible')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def phonepass_stream(red):
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)
