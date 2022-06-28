from flask import jsonify, request, render_template, Response, redirect, session
from flask import session,Response, jsonify
import json
from datetime import timedelta
import uuid
from urllib.parse import urlencode
import logging

logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)

Mode=dict()

did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/console',  view_func=console, methods = ['GET', 'POST'], defaults={"red" : red})

    app.add_url_rule('/sandbox/authorize',  view_func=wallet_authorize, methods = ['GET', 'POST'], defaults={"red" : red})
    app.add_url_rule('/sandbox/token',  view_func=wallet_token, methods = ['GET', 'POST'], defaults={"red" : red})
    app.add_url_rule('/sandbox/logout',  view_func=wallet_logout, methods = ['GET', 'POST'])
    
    app.add_url_rule('/sandbox/display_login',  view_func=test_display_login_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/sandbox/login_presentation/<stream_id>',  view_func=login_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    app.add_url_rule('/sandbox/login_presentation_display',  view_func=login_followup, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/login_presentation_stream',  view_func=login_presentation_stream, defaults={ 'red' : red})
    global Mode
    Mode=mode
    return


def extract_client(Mode):
    return 'http://'+ Mode.IP +':4000'

def extract_bridge(Mode):
    return 'http://'+ Mode.IP +':3000'


def console(red) :
    global vc, reason
    if request.method == 'GET' :
        if session.get('vc') == "EmailPass" :
            credential = "Email proof"
        elif  session.get('vc') == "Kyc" :
            credential = "KYC"
        elif  session.get('vc') == "StudentCard" :
            credential = "Student card"
        elif  session.get('vc') == "CertificateOfEmployment" :
            credential = "Certificate of employment"
        elif  session.get('vc') == "LearningAchievement" :
            credential = "Diploma"
        elif  session.get('vc') == "Tez_Voucher_1" :
            credential = "Voucher Tezotopia 15%"
        elif  session.get('vc') == "Over18" : 
            credential = "Over 18 proof"
        else :
            credential = "Any"
        print("credential = ", credential)
        return render_template('console.html',
                 callback_url=extract_client(Mode) + '/callback',
                 logout_url=extract_client(Mode) + '/logout',
                 token=extract_bridge(Mode) + '/sandbox/authorize',
                 authorization=extract_bridge(Mode) + '/sandbox/token',
                 website = extract_client(Mode),
                 credential=credential,
                 vc=session.get('vc',""),
                 reason=session.get('reason', '')
                 )
    if request.method == 'POST' :
        session['vc'] = request.form['vc']
        session['reason'] = request.form['reason']
        session['client_id'] = request.form['client_id']
        data = {'vc' : session['vc'],
                'reason' : session['reason']}
        red.set( session['client_id'], json.dumps(data))
        return redirect('/sandbox/console')


def wallet_authorize(red) :
    if session.get('is_connected') :
        print('user is connected in OP')
        code = request.args.get('code', '')
        return redirect(extract_client(Mode) + '/callback?code=' + code) 
    code = str(uuid.uuid1())
    print('user is not connected in OP')
    data = {
            'client_id' : request.args.get('client_id'),
            'scope' : request.args.get('scope'),
            'redirect_uri' : request.args.get( 'redirect_uri'),
            'client_data' : json.loads(red.get(request.args.get('client_id')).decode())
            }
    red.set(code, json.dumps(data))
    print("data reçu dans authorization server ", data)
    return redirect('/sandbox/display_login?code=' + code)


def wallet_token(red) :
    print(request.headers)
    print("from token endpoint client_id = ", request.form['client_id'])
    print("from token endpoint code = ", request.form['code'])
    try :
        vp = red.get(request.form.get('code', "")).decode()
    except :
        return redirect (extract_client())
    my_response = {
                    'id_token' : "eyjklhdfmljkhkj8765GLKJGKLHJG9769876LB",
                    "access_token" : "mkljhluhjhmlkhmljkh",
                    "vp" : vp
                }
    return jsonify(my_response)


def wallet_logout() :
    session.clear()
    print("logout reçu")
    return jsonify('logout')


model_pattern = {
    "type": "VerifiablePresentationRequest",
    "query": [
        {
            "type": "QueryByExample",
            "credentialQuery": [
                {
                    "example" : {
                        "type" : "EmailPass",
                    },
                    "reason": [
                        {
                            "@language": "en",
                            "@value": "Join a resident card and your driver license"
                        }
                    ]
                }
            ]
        }
    ]
}



model_pattern_any = {
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
    client_data = json.loads(red.get(request.args['code']).decode())['client_data']
    if client_data['vc'] == "Any" :
        pattern = model_pattern_any
    else :
        pattern = model_pattern
        pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = client_data['reason']
        pattern["query"][0]["credentialQuery"][0]["example"]["type"] = client_data['vc']

    pattern['challenge'] = str(uuid.uuid1())
    pattern['domain'] = mode.server
    red.set(stream_id,  json.dumps(pattern))
    red.set(stream_id + "_code",  request.args['code'])
    url = mode.server + 'sandbox/login_presentation/' + stream_id +'?issuer=' + did_selected
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    return render_template('login_presentation_qr.html',
							url=url,
                            deeplink=deeplink,
							stream_id=stream_id, 
                            pattern=json.dumps(pattern, indent=4)
                            )


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
        """
        Tout est ok,
        on peut verifier maintenant par exemple que le type du VC est un EmailPass et permettre le login par exemple en utilisant l email comme id du user.
    
        """
        red.set(stream_id,  request.form['presentation'])
        event_data = json.dumps({"stream_id" : stream_id,
			                        "message" : "ok"})           
        red.publish('display_login', event_data)
        return jsonify("ok")


def login_presentation_stream(red):
    def login_event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('display_login')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(login_event_stream(red), headers=headers)


def login_followup(red):  
    if request.args.get('message') :
        message = request.args['message']
        print(message)
    else :
        stream_id = request.args['stream_id']
        try :
            vp = red.get(stream_id).decode()
            code = red.get(stream_id +"_code").decode()
            red.delete(stream_id)
            red.delete(stream_id + "_code")
            presentation = json.loads(vp)
        except :
            logging.warning('red.get problem')
        holder = presentation['holder']
        print('user is connected in OP ', holder)
        session['is_connected'] = True
        red.set(code, vp)
    return redirect ('/sandbox/authorize?code=' + code)