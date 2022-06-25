from flask import jsonify, request, render_template, Response, render_template_string, redirect
from flask import session, flash, Response, jsonify
import requests
import json
from datetime import timedelta
import uuid
from urllib.parse import urlencode
import logging

logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)

did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

def init_app(app,red, mode) :
    app.add_url_rule('/wallet/authorize',  view_func=wallet_authorize, methods = ['GET', 'POST'], defaults={"red" : red})
    app.add_url_rule('/wallet/token',  view_func=wallet_token, methods = ['GET', 'POST'], defaults={"red" : red})

    app.add_url_rule('/wallet/test/display_login',  view_func=test_display_login_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/wallet/test/login_presentation/<stream_id>',  view_func=login_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    app.add_url_rule('/wallet/test/login_presentation_display',  view_func=test_login_presentation_display, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/login_presentation_stream',  view_func=login_presentation_stream, defaults={ 'red' : red})
    return



def wallet_authorize(red) :
    if session.get('logged') :
        print('user is connected in OP')
        code = request.args.get('code', 'vide')
        return redirect('http://192.168.0.65:4000/callback?code=' + code) 
    code = str(uuid.uuid1())
    print('user is not connected in OP')
    print("code généré dans authorization server = ", code)
    data = {
            'client_id' : request.args.get('client_id'),
            'scope' : request.args.get('scope'),
            'redirect_uri' : request.args.get( 'redirect_uri')
            }
    red.set(code, json.dumps(data))
    print("data reçu dans authorization server ", data)
    return redirect('/wallet/test/display_login?code=' + code)

def wallet_token(red) :
    print(request.headers)
    print("from token endpoint client_id = ", request.form['client_id'])
    print("from token endpoint code = ", request.form['code'])
    try :
        vp = red.get(request.form.get('code', "")).decode()
    except :
        vp =""
    my_response = {
                    'id_token' : "eyjklhdfmljkhkj8765GLKJGKLHJG9769876LB",
                    "access_token" : "mkljhluhjhmlkhmljkh",
                    "vp" : vp
                }
    session['logged'] = False
    print('user is disconnected in OP') 
    return jsonify(my_response)



pattern = {
            "type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": []
                }
            ],
            "challenge": "",
            "domain" : ""
            }


def test_display_login_qrcode(red, mode):
    stream_id = str(uuid.uuid1())
    pattern['challenge'] = str(uuid.uuid1())
    pattern['domain'] = mode.server
    red.set(stream_id,  json.dumps(pattern))
    red.set(stream_id + "_code",  request.args['code'])
    url = mode.server + 'wallet/test/login_presentation/' + stream_id +'?issuer=' + did_selected
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    return render_template('wallet/test/login_presentation_qr.html',
							url=url,
                            deeplink=deeplink,
							stream_id=stream_id, 
                            pattern=json.dumps(pattern, indent=4),
                            simulator="Custom login")


def login_presentation_endpoint(stream_id, red):
    try :
        my_pattern = json.loads(red.get(stream_id).decode())
    except :
        logging.error('red decode failed')
        event_data = json.dumps({"stream_id" : stream_id, "message" : "Server error."})
        red.publish('credible', event_data)
        return jsonify("server error"), 500
    challenge = my_pattern.get('challenge')
    domain = my_pattern.get('domain')
    if request.method == 'GET':
        return jsonify(my_pattern)
    elif request.method == 'POST' :
        red.delete(stream_id)
        presentation = json.loads(request.form['presentation'])
        try : 
            response_challenge = presentation['proof']['challenge']
            response_domain = presentation['proof']['domain']
        except :
            logging.warning('presentation is not correct')
            event_data = json.dumps({"stream_id" : stream_id, "message" : "Presentation format failed."})
            red.publish('display_VP', event_data)
            return jsonify("presentation is not correct"), 500
        logging.info('Presentation received from wallet is correctly formated')
        if response_domain != domain or response_challenge != challenge :
            logging.warning('challenge or domain failed')
            #event_data = json.dumps({"stream_id" : stream_id, "message" : "The presentation challenge failed."})
            #red.publish('credible', event_data)
            #return jsonify("ko")
        """
        Tout est ok,
        on peut verifier maintenant par exemple que le type du VC est un EmailPass et permettre le login par exemple en utilisant l email comme id du user.
    
        """
        red.set(stream_id,  request.form['presentation'])
        event_data = json.dumps({"stream_id" : stream_id,
			                        "message" : "ok"})           
        red.publish('display_login', event_data)
        return jsonify("ok")


def login_event_stream(red):
    pubsub = red.pubsub()
    pubsub.subscribe('display_login')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def login_presentation_stream(red):
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(login_event_stream(red), headers=headers)


def test_login_presentation_display(red):  
    if request.args.get('message') :
        message = request.args['message']
        print(message)
    else :
        stream_id = request.args['stream_id']
        try :
            presentation_json = red.get(stream_id).decode()
            code = red.get(stream_id +"_code").decode()
            red.delete(stream_id)
            red.delete(stream_id + "_code")
            presentation = json.loads(presentation_json)
        except :
            logging.warning('red.get problem')
        holder = presentation['holder']
        print('user is connected in OP ', holder)
        session['logged'] = True
        vp = presentation_json
        red.set(code, vp)
    return redirect ('/wallet/authorize?code=' + code)