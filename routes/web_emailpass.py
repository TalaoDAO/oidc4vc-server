from flask import jsonify, request, render_template, session, redirect, flash, Response
import json
from components import privatekey, Talao_message
from datetime import datetime
import redis
import uuid
import secrets
from datetime import timedelta, datetime
import logging
logging.basicConfig(level=logging.INFO)
from signaturesuite import vc_signature
from flask_babel import _


red = redis.StrictRedis()


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
    	    return render_template("emailpass/email_authentication.html")


def emailpass_qrcode(mode) :
    if request.method == 'GET' :
        id = str(uuid.uuid1())
        url = mode.server + "emailpass/offer/" + id 
        red.set(id, session['email'])
        return render_template('emailpass/emailpass_qrcode.html', url=url, id=id)
   

def emailpass_offer(id, mode):
    credential = json.loads(open('./verifiable_credentials/EmailPass.jsonld', 'r').read())
    if request.method == 'GET':   
        return jsonify({
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : datetime.timestamp(datetime.now()) + 5*60 #5 minutes
        })
    elif request.method == 'POST':
        credential["issuer"] = "did:web:talao.co"
        credential['id'] = "urn:uuid:" + str(uuid.uuid1())
        credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        credential['credentialSubject']['id'] = request.form['subject_id']
        credential['credentialSubject']['email'] = red.get(id).decode()
        pvk = privatekey.get_key(mode.owner_talao, 'private_key', mode)
        signed_credential = vc_signature.sign(credential, pvk, "did:web:talao.co")
        print(json.dumps(signed_credential, indent=4))
        data = json.dumps({"stream_id" : id, "check" : "ok"})
        red.publish('credible', data)
        return jsonify(signed_credential)
 

def emailpass_end() :
    return render_template('emailpass/emailpass_end.html')


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
