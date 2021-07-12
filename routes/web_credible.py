from flask import jsonify, request, render_template, session, redirect, flash, Response
import json
import redis
from datetime import timedelta, datetime

""" download credential to wallet
those credential have been signed previously

"""

OFFER_DELAY = timedelta(seconds= 10*60)

red = redis.Redis()


def init_app(app,mode) :
    app.add_url_rule('/credible/credentialOffer/<id>',  view_func=credentialOffer_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/credible/credential/<id>',  view_func=credential_display, methods = ['GET', 'POST'])
    app.add_url_rule('/credible/wallet_credential/<id>',  view_func=credentialOffer, methods = ['GET', 'POST'])
    app.add_url_rule('/save_stream',  view_func=save_stream, methods = ['GET', 'POST'])
    return


def credentialOffer_qrcode(mode,id) :
    filename = id + ".jsonld"
    try :
        json.load(open('./signed_credentials/' + filename, 'r'))
    except :
        flash('no credential available on server', 'warning')
        return redirect("/user")
    url = mode.server + "credible/wallet_credential/" + id
    return render_template('credible/credential_qr.html', url=url, id=id, **session['menu'])


def credential_display(id):
    if id != 'presentation' :
        filename = id + ".jsonld"
        credential = open('./signed_credentials/' + filename, 'r').read()
    else :
        credential = "No credential available"
    return render_template('credible/credential.html', credential=credential)


def credentialOffer(id):
    filename = id + ".jsonld"
    credential = json.load(open('./signed_credentials/' + filename, 'r'))
    if request.method == 'GET':   
        return jsonify({
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z"
        })
    elif request.method == 'POST':
        # send event to client agent to go forward
        data = json.dumps({'id' : id, 'check' : 'success'})
        red.publish('credible', data)
        return jsonify(credential)
     

# server event push 
def event_stream():
    pubsub = red.pubsub()
    pubsub.subscribe('credible')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def save_stream():
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(), headers=headers)
