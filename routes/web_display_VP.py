from flask import jsonify, request, render_template, Response, render_template_string
import json
from datetime import timedelta
from components import privatekey
import uuid
import logging
from flask_babel import Babel, _
from urllib.parse import urlencode

logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)

did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

def init_app(app,red, mode) :
    app.add_url_rule('/wallet/test/display_VP',  view_func=test_display_VP_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/wallet/test/VP_presentation/<stream_id>',  view_func=VP_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    app.add_url_rule('/wallet/test/VP_presentation_display',  view_func=test_VP_presentation_display, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/VP_presentation_stream',  view_func=VP_presentation_stream, defaults={ 'red' : red})
    global PVK
    PVK = privatekey.get_key(mode.owner_talao, 'private_key', mode)
    return

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


def test_display_VP_qrcode(red, mode):
    stream_id = str(uuid.uuid1())
    pattern['challenge'] = str(uuid.uuid1())
    pattern['domain'] = mode.server
    red.set(stream_id,  json.dumps(pattern))
    url = mode.server + 'wallet/test/VP_presentation/' + stream_id +'?issuer=' + did_selected
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    return render_template('wallet/test/VP_presentation_qr.html',
							url=url,
                            deeplink=deeplink,
							stream_id=stream_id, 
                            pattern=json.dumps(pattern, indent=4),
                            simulator="Display VP")


def VP_presentation_endpoint(stream_id, red):
    try :
        my_pattern = json.loads(red.get(stream_id).decode())
    except :
        logging.error('red decode failed')
        event_data = json.dumps({"stream_id" : stream_id, "message" : "Server error."})
        red.publish('credible', event_data)
        return jsonify("server error"), 500
    challenge = my_pattern['challenge']
    domain = my_pattern['domain']
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
        if response_domain != domain or response_challenge != challenge :
            logging.warning('challenge or domain failed')
            #event_data = json.dumps({"stream_id" : stream_id, "message" : "The presentation challenge failed."})
            #red.publish('credible', event_data)
            #return jsonify("ko")
        #else :
            # we just display the presentation VC
        red.set(stream_id,  request.form['presentation'])
        event_data = json.dumps({"stream_id" : stream_id,
			                        "message" : "ok"})           
        red.publish('display_VP', event_data)
        return jsonify("ok")


def event_stream(red):
    pubsub = red.pubsub()
    pubsub.subscribe('display_VP')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def VP_presentation_stream(red):
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)


def test_VP_presentation_display(red):  
    if request.args.get('message') :
        credential = request.args['message']
        nb_credentials = holder = issuers = "Unknown"
    else :
        presentation_json = red.get(request.args['stream_id']).decode()
        red.delete(request.args['stream_id'])
        presentation = json.loads(presentation_json)
        holder = presentation['holder']
        if isinstance(presentation['verifiableCredential'], dict) :
            nb_credentials = "1"
            issuers = presentation['verifiableCredential']['issuer']
            types = presentation['verifiableCredential']['type'][1]
            credential = json.dumps(presentation['verifiableCredential'], indent=4, ensure_ascii=False)
        else :
            nb_credentials = str(len(presentation['verifiableCredential']))
            issuer_list = list()
            type_list = list()
            for credential in presentation['verifiableCredential'] :
                if credential['issuer'] not in issuer_list :
                    issuer_list.append(credential['issuer'])
                if credential['type'][1] not in type_list :
                    type_list.append(credential['type'][1])
            issuers = ", ".join(issuer_list)
            types = ", ".join(type_list)
            credential = json.dumps(presentation['verifiableCredential'][0], indent=4, ensure_ascii=False)
        presentation = json.dumps(presentation, indent=4, ensure_ascii=False)

    html_string = """
        <!DOCTYPE html>
        <html>
        <body class="h-screen w-screen flex">
        <br>Number of credentials : """ + nb_credentials + """<br>
        <br>Holder (wallet DID)  : """ + holder + """<br>
        <br>Issuers : """ + issuers + """<br>
        <br>Credential types : """ + types + """
        <br><br><br>
         <form action="/wallet/test/display_VP" method="GET" >
                    <button  type"submit" >QR code for Request</button></form>
                    <br>---------------------------------------------------<br>
        
        <h2> Verifiable Credential </h2>
        <pre class="whitespace-pre-wrap m-auto">""" + credential + """</pre>
        <h2> Verifiable Presentation </h2>
        <pre class="whitespace-pre-wrap m-auto">""" + presentation + """</pre>
        </body>
        </html>"""
    return render_template_string(html_string)