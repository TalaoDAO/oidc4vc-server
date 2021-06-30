from flask import jsonify, request, render_template, Response, session, redirect, flash
import json
import redis
from components import privatekey
from Crypto.PublicKey import RSA
from authlib.jose import JsonWebEncryption
from datetime import datetime


red = redis.StrictRedis()

def init_app(app,mode) :
    app.add_url_rule('/credible/credentialOffer/<id>',  view_func=credentialOffer_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/credible/credential/<id>',  view_func=credential_display, methods = ['GET', 'POST'])
    app.add_url_rule('/credible/wallet_credential/<id>',  view_func=credentialOffer, methods = ['GET', 'POST'])

    app.add_url_rule('/credible/VerifiablePresentationRequest',  view_func=VerifiablePresentationRequest_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/credible/wallet_presentation',  view_func=wallet_presentation, methods = ['GET', 'POST'],  defaults={'mode' : mode})
    
    app.add_url_rule('/stream',  view_func=stream, methods = ['GET', 'POST'])
    app.add_url_rule('/credible/callback',  view_func=callback, methods = ['GET', 'POST'])
    return


# credential 

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
            "credentialPreview": credential
        })
    elif request.method == 'POST':
        #data = json.dumps({"check" : "ok"})
        #red.publish('credible', data)
        return jsonify(credential)


# presentation for login

def VerifiablePresentationRequest_qrcode(mode):
    url = mode.server + "credible/wallet_presentation"
    return render_template('credible/login_qr.html', url=url, id='presentation')

def wallet_presentation(mode):
    """
    request a presentation for authorization (login ?)
    """
    if request.method == 'GET':
        return jsonify({
            "type": "VerifiablePresentationRequest",
            "challenge": "credential",
            "domain" : "https://talao.co"
        })
    elif request.method == 'POST':
        presentation = json.loads(request.form['presentation'])
        holder = presentation['holder']
        #issuer = presentation['verifiableCredential']['issuer']
        #workspace_contract = ns.get_workspace_contract_from_did(holder, mode)
        data = json.dumps({"check" : "ok", "token" : generate_token(holder, mode)})
        red.publish('credible', data)
        return jsonify("ok")


# server event push 

def event_stream():
    pubsub = red.pubsub()
    pubsub.subscribe('credible')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode('utf-8')


def stream():
    return Response(event_stream(), mimetype="text/event-stream")


def callback() :
    credential = 'holder : ' + request.args['holder'] + ' issuer : ' + request.args['issuer']
    return render_template('credible/credential.html', credential=credential)

def generate_token(did,mode) :
    private_rsa_key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
    RSA_KEY = RSA.import_key(private_rsa_key)
    public_rsa_key = RSA_KEY.publickey().export_key('PEM').decode('utf-8')
    expired = datetime.timestamp(datetime.now()) + 180 # 3 minutes live
    # build JWE
    jwe = JsonWebEncryption()
    header = {'alg': 'RSA1_5', 'enc': 'A256GCM'}
    json_string = json.dumps({'did' : did, 'exp' : expired})
    payload = bytes(json_string, 'utf-8')
    return jwe.serialize_compact(header, payload, public_rsa_key).decode()