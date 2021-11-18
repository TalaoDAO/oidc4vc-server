"""
pour l authentication cf https://realpython.com/token-based-authentication-with-flask/
pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization
interace wsgi https://www.bortzmeyer.org/wsgi.html
request : http://blog.luisrei.com/articles/flaskrest.html

"""
from flask import request, redirect, render_template,abort, Response, jsonify
from flask_babel import _
from urllib.parse import urlencode

from datetime import timedelta, datetime
import json
from Crypto.PublicKey import RSA
from authlib.jose import JsonWebEncryption
from urllib.parse import urlencode
import logging
from components import ns, privatekey
import uuid
import didkit

PRESENTATION_DELAY = 600 # seconds

DID_WEB = 'did:web:talao.cp'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY =  'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'                      

logging.basicConfig(level=logging.INFO)

def init_app(app, red, mode) :
    app.add_url_rule('/app/login/<stream_id>',  view_func=deeplink_endpoint, methods = ['GET', 'POST'], defaults={'mode': mode, 'red' : red} )
    app.add_url_rule('/app/login',  view_func=app_login, methods = ['GET', 'POST'], defaults={'mode': mode} )
    app.add_url_rule('/app/login/stream',  view_func=app_stream, defaults={ 'red' : red})
    app.add_url_rule('/app/links/',  view_func=app_link, methods = ['GET', 'POST'])

    return


def app_link(): 
    return jsonify("link to Apple and Google store")


def app_login(mode) :
    stream_id = str(uuid.uuid1())
    uri = "https://18.190.21.227/app/login/" + stream_id
    deeplink = 'https://talao.co/app/links/?' + urlencode({'uri' : uri ,  'issuer' : DID_ETHR})
    print ('deeplink = ', deeplink)
    return render_template("login/deeplink_login.html", deeplink=deeplink, stream_id=stream_id)

def deeplink_endpoint(stream_id, red, mode):
    if request.method == 'GET':
        challenge = str(uuid.uuid1())
        red.set(stream_id, challenge)
        did_auth_request = {
            "type": "VerifiablePresentationRequest",
            "query": [{
            	"type": 'DIDAuth'
            	}],
            "challenge": challenge,
            "domain" : mode.server
        }
        return jsonify(did_auth_request)
    elif request.method == 'POST' :
        challenge = red.get(stream_id).decode()
        presentation = json.loads(request.form['presentation'])   
        logging.info('verify presentation = ' + didkit.verify_presentation(json.dumps(presentation), '{}'))
        """
        if json.loads(didkit.verify_presentation(request.form['presentation'], '{}'))['errors'] :
            logging.warning('signature failed')
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ko",
									 "message" : _("Signature verification failed.")})
            red.publish('credible', event_data)
            return jsonify("Signature verification failed"), 401
        """    
        #try : # FIXME
        issuer = presentation['verifiableCredential']['issuer']
        holder = presentation['holder']
        challenge = presentation['proof']['challenge']
        domain = presentation['proof']['domain']
        #except :
        #    logging.warning('to be fixed, presentation is not correct')
        #    event_data = json.dumps({"stream_id" : stream_id,
		#							"code" : "ko",
		#							 "message" : _("Presentation check failed.")})
        #    red.publish('credible', event_data)
        #    return jsonify("Presentation malformed"), 400
        if domain != mode.server or challenge != challenge :
            logging.warning('challenge failed')
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ko",
									 "message" : _("The presentation challenge failed.")})
            red.publish('credible', event_data)
            return jsonify("Challenge failed"), 401
        elif issuer not in [DID_WEB, DID_ETHR, DID_TZ, DID_KEY] :
            logging.warning('unknown issuer')
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ko",
									 "message" : _("This issuer is unknown.")})
            red.publish('credible', event_data)
            return jsonify("Issuer unknown"), 403
        
        elif not ns.get_workspace_contract_from_did(holder, mode) :
            # user has no account
            logging.warning('User unknown')
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ko",
									 "message" : _('Your Digital Identity has not been registered yet.')})
            red.publish('credible', event_data)
            return  jsonify("User unknown"), 403
        else :
			# Successfull login 
            # we transfer a JWE token to user agent to sign in
            logging.info('log with DID')
            token = generate_token(holder, "", "",mode)
            event_data = json.dumps({"stream_id" : stream_id,
									"code" : "ok",
			                        "message" : "ok",
			                        "token" : token})
            red.publish('credible', event_data)
            return jsonify("ok"), 201


def event_stream(red):
    pubsub = red.pubsub()
    pubsub.subscribe('credible')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def app_stream(red):
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)


def callback() :
    credential = 'holder : ' + request.args['holder'] + ' issuer : ' + request.args['issuer']
    return render_template('credible/credential.html', credential=credential)


def generate_token(did,issuer_username, vc, mode) :
    private_rsa_key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
    RSA_KEY = RSA.import_key(private_rsa_key)
    public_rsa_key = RSA_KEY.publickey().export_key('PEM').decode('utf-8')
    expired = datetime.timestamp(datetime.now()) + 5 # 5s live
    # build JWE
    jwe = JsonWebEncryption()
    header = {'alg': 'RSA1_5', 'enc': 'A256GCM'}
    json_string = json.dumps({'did' : did,
							 'issuer_username' : issuer_username,
							 'vc' : vc,
							 'exp' : expired})
    payload = bytes(json_string, 'utf-8')
    return jwe.serialize_compact(header, payload, public_rsa_key).decode()

