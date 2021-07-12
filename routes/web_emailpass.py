from flask import jsonify, request, render_template, session, redirect, flash, Response
import json
from components import privatekey, Talao_message
import redis
import uuid
import secrets
from datetime import timedelta, datetime
import logging
logging.basicConfig(level=logging.INFO)
from signaturesuite import vc_signature
from flask_babel import _
import secrets

OFFER_DELAY = timedelta(seconds= 10*60)
DID = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'

red = redis.Redis()

def init_app(app,mode) :
    app.add_url_rule('/emailpass',  view_func=emailpass, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/emailpass/qrcode',  view_func=emailpass_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/emailpass/offer/<id>',  view_func=emailpass_offer, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/emailpass/authentication',  view_func=emailpass_authentication, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/emailpass/stream',  view_func=emailpass_stream, methods = ['GET', 'POST'])
    app.add_url_rule('/emailpass/end',  view_func=emailpass_end, methods = ['GET', 'POST'])
    return


"""
Email Pass : credential offer for a VC with email only
VC is signed by Talao

"""

def emailpass(mode) :
    if request.method == 'GET' :
        return render_template('emailpass/emailpass.html')
    if request.method == 'POST' :
        # traiter email
        session['email'] = request.form['email']
        session['code'] = str(secrets.randbelow(99999))
        session['code_delay'] = datetime.now() + timedelta(seconds= 180)
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


def emailpass_qrcode(mode) :
    if request.method == 'GET' :
        id = str(uuid.uuid1())
        url = mode.server + "emailpass/offer/" + id 
        red.setex(id, OFFER_DELAY, value=session['email'])
        logging.info('url = %s', url)
        return render_template('emailpass/emailpass_qrcode.html', url=url, id=id)
   

def emailpass_offer(id, mode):
    """ Endpoint for wallet
    """
    credential = json.loads(open('./verifiable_credentials/EmailPass.jsonld', 'r').read())
    credential["issuer"] = DID
    credential['id'] = "urn:uuid:" + str(uuid.uuid1())
    credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    try :
        credential['credentialSubject']['email'] = red.get(id).decode()
    except :
        logging.warning('QR code expired')
        data = json.dumps({"url_id" : id, "check" : "expired"})
        red.publish('credible', data)
        return jsonify('ko')
    credential['credentialSubject']['expires'] = (datetime.now() + timedelta(days= 365)).replace(microsecond=0).isoformat() + "Z"
    if request.method == 'GET': 
        # make an offer  
        return jsonify({
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z"
        })
    elif request.method == 'POST':    
        # sign credential
        credential['credentialSubject']['id'] = request.form.get('subject_id', 'unknown DID')
        pvk = privatekey.get_key(mode.owner_talao, 'private_key', mode)
        signed_credential = vc_signature.sign(credential, pvk, DID)
        if not signed_credential :
            logging.error('credential signature failed')

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

        # send signed credential to wallet
        return jsonify(signed_credential)
 

def emailpass_end() :
    if request.args['followup'] == "success" :
        message = _('Great ! you have now an Email Pass')
    elif request.args['followup'] == 'expired' :
        message = _('Delay expired')
    return render_template('emailpass/emailpass_end.html', message=message)


# server event push 
def event_stream():
    pubsub = red.pubsub()
    pubsub.subscribe('credible')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def emailpass_stream():
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(), headers=headers)
