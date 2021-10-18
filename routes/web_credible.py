from flask import jsonify, request, render_template, session, redirect, flash, Response
import json
from datetime import timedelta, datetime
from flask_babel import _

import logging
logging.basicConfig(level=logging.INFO)

""" download credential to wallet
those credential have been signed previously

"""

OFFER_DELAY = timedelta(seconds= 10*60)


def init_app(app,red, mode) :
    app.add_url_rule('/credible/credentialOffer/<id>',  view_func=credentialOffer_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/credible/credential/<id>',  view_func=credential_display, methods = ['GET', 'POST'])
    app.add_url_rule('/credible/wallet_credential/<id>',  view_func=credentialOffer, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/save_stream',  view_func=save_stream, methods = ['GET', 'POST'], defaults={'red' : red})
    return


def credentialOffer_qrcode(mode,id) :
    filename = id + ".jsonld"
    try :
        json.load(open('./signed_credentials/' + filename, 'r'))
    except :
        flash(_('This credential is not available.'), 'warning')
        return redirect("/user")
    url = mode.server + "credible/wallet_credential/" + id
    return render_template('credible/credential_qr.html', url=url, id=id, **session['menu'])


def credential_display(id):
    if id != 'presentation' :
        filename = id + ".jsonld"
        credential = open('./signed_credentials/' + filename, 'r').read()
    else :
        credential = _('No credential available.')
    return render_template('credible/credential.html', credential=credential)


def credentialOffer(id, red):
    filename = id + ".jsonld"
    credential = json.loads(open('./signed_credentials/' + filename, 'r').read())
    del credential['proof']
    credential2 = json.loads(open('./verifiable_credentials/ProfessionalExperienceAssessment.jsonld', 'r').read())
    if request.method == 'GET':
              
        #credential['credentialSubject']['signatureLines'] = credential2['credentialSubject']['signatureLines']
        #credential['credentialSubject']['description'] = credential2['credentialSubject']['description']
        #credential['credentialSubject']['skills'] = credential2['credentialSubject']['skills']
        #credential['credentialSubject']['issuedBy'] = credential2['credentialSubject']['issuedBy']

        credential['credentialSubject']['id'] = "did:"
        credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        credential['issuer'] = "did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk"
        credential['credentialSubject']['startDate'] = "2021-05-13T12:11:59Z"
        credential['credentialSubject']['endDate'] = "2021-05-15T12:11:59Z"
        return jsonify({
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z", 
            "scope" : [],
            "display" : {}
        })
    elif request.method == 'POST':
        # send event to client agent to go forward
        if request.form.get('subject_id') !=  credential['credentialSubject']['id'] :
            data = json.dumps({'id' : id, 'check' : 'incorrect subject'})
            logging.warning('incorrect subject')
            red.publish('credible', data)
            return jsonify({})
        else :
            data = json.dumps({'id' : id, 'check' : 'success'})
            red.publish('credible', data)
            return jsonify(credential)
     

# server event push 
def event_stream(red):
    pubsub = red.pubsub()
    pubsub.subscribe('credible')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def save_stream(red):
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)
