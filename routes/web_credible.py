from flask import jsonify, request, render_template, Response, session, redirect, flash
import json
from components import privatekey,ns
from Crypto.PublicKey import RSA
from authlib.jose import JsonWebEncryption
from datetime import datetime
import redis
import didkit

red = redis.StrictRedis()

def init_app(app,mode) :
    app.add_url_rule('/credible/credentialOffer/<id>',  view_func=credentialOffer_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/credible/credential/<id>',  view_func=credential_display, methods = ['GET', 'POST'])
    app.add_url_rule('/credible/wallet_credential/<id>',  view_func=credentialOffer, methods = ['GET', 'POST'])

    app.add_url_rule('/credible/VerifiablePresentationRequest',  view_func=VerifiablePresentationRequest_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/credible/wallet_presentation',  view_func=wallet_presentation, methods = ['GET', 'POST'],  defaults={'mode' : mode})
    
    app.add_url_rule('/stream',  view_func=stream)
    app.add_url_rule('/credible/callback',  view_func=callback, methods = ['GET', 'POST'])
    return


# credential offer

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
    print('request values = ', request.values)
    filename = id + ".jsonld"
    credential = json.load(open('./signed_credentials/' + filename, 'r'))
    if request.method == 'GET':   
        print('request form = ', request.form, request.data)
        return jsonify({
            "type": "CredentialOffer",
            "credentialPreview": credential
        })
    elif request.method == 'POST':
        #data = json.dumps({"check" : "ok"})
        #red.publish('credible', data)
        return jsonify(credential)


# presentation for login with credible

def VerifiablePresentationRequest_qrcode(mode):
    url = mode.server + "credible/wallet_presentation"
    return render_template('credible/login_qr.html', url=url, id='presentation')

def wallet_presentation(mode):
    if request.method == 'GET':
        credential_query = [
	        {'reason' : 'Sign in',
            'required' : False,
	        'example' : [
		        {'@context' : [
			        'https://www.w3.org/2018/credentials/v1'
		        ],
		        'type' : 'VerifiableCredential'
                }
            ]}
            ]
        
        query = [
		{'type' : 'QueryByExample',
		'credentialQuery' : credential_query}
        ]

        did_auth_request = {
            "type": "VerifiablePresentationRequest",
            "query": [{
            "type": 'DIDAuth'
            }],
            "challenge": '99612b24-63d9-11ea-b99f-4f66f3e4f81a',
            "domain": 'example.com'
            }
        base_request = {
            "type": "VerifiablePresentationRequest",
            "query" : query,
            "challenge": "credential",
            "domain" : "https://talao.co"
            }
        
        return jsonify(did_auth_request)

    elif request.method == 'POST':
        presentation = json.loads(request.form['presentation'])
        print('presentation = ', presentation)
        print('verifify presentation,  = ', didkit.verifyPresentation(request.form['presentation'], '{}'))
        holder = presentation['holder']
        if not  ns.get_workspace_contract_from_did(holder, mode) :
            # user has no account
            data = json.dumps({"check" : "unknown account"})
        else :
            data = json.dumps({"check" : "ok", "token" : generate_token(holder, mode)})
        red.publish('credible', data)
        return jsonify("ok")


# server event push 

def event_stream():
    pubsub = red.pubsub()
    pubsub.subscribe('credible')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()

def stream():
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(), headers=headers)


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