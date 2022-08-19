from flask import jsonify, request, render_template, Response, render_template_string
import json
from datetime import timedelta
import uuid
import logging
from urllib.parse import urlencode
import didkit

logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)

did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

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


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/display_VP',  view_func=test_display_VP_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/VP_presentation/<stream_id>',  view_func=VP_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/sandbox/VP_presentation_display',  view_func=test_VP_presentation_display, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/VP_presentation_stream',  view_func=VP_presentation_stream, defaults={ 'red' : red})
    return


def test_display_VP_qrcode(mode):
    stream_id = str(uuid.uuid1())
    url = mode.server + 'sandbox/VP_presentation/' + stream_id +'?issuer=' + did_selected
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    altme_deeplink = mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url })
    return render_template('VP_presentation_qr.html',
							url=url,
                            deeplink=deeplink,
                            altme_deeplink=altme_deeplink,
							stream_id=stream_id, 
                            pattern=json.dumps(pattern, indent=4),
                            simulator="Display VP")


def VP_presentation_endpoint(stream_id, mode, red):

    if request.method == 'GET':
        pattern['challenge'] = str(uuid.uuid1())
        pattern['domain'] = mode.server
        red.set(stream_id,  json.dumps(pattern))
        return jsonify(pattern)
    elif request.method == 'POST' :
        try :
            my_pattern = json.loads(red.get(stream_id).decode())
            challenge = my_pattern['challenge']
            domain = my_pattern['domain']
        except :
            logging.error('red decode failed')
            event_data = json.dumps({"stream_id" : stream_id, "message" : "Server error."})
            red.publish('credible', event_data)
            return jsonify("URL not found"), 404
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


async def test_VP_presentation_display(red):  
    if request.args.get('message') :
        credential = request.args['message']
        nb_credentials = holder = issuers = "Unknown"
    else :
        try :
            presentation_json = red.get(request.args['stream_id']).decode()
            #red.delete(request.args['stream_id'])
        except :
            return jsonify('server problem')
        presentation_result = await didkit.verify_presentation(presentation_json, '{}')
        presentation = json.loads(presentation_json)
        holder = presentation['holder']
        credential_json = "No check done"
        if isinstance(presentation['verifiableCredential'], dict) :
            credential_json = json.dumps(presentation['verifiableCredential'])
            credential_result = await didkit.verify_credential(credential_json, '{}')
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
        
        <br><b>wallet DID  : </b>""" + holder + """<br>
        
        <br><b>Issuers DID : </b>""" + issuers + """<br>
        
        <br><b>Signature Issuer VC verify : </b>""" + credential_result + """<br> 

        <br><b>Signature Wallet VP verify : </b>""" + presentation_result + """<br> 
       
        <br><b>Credential types : </b>""" + types + """
        <br><br><br>
         <form action="/sandbox/display_VP" method="GET" >
                    <button  type"submit" >QR code for Request</button></form>
                    <br>---------------------------------------------------<br>
        
       
        <h2> Verifiable Presentation sent by the wallet :</h2>
        <pre class="whitespace-pre-wrap m-auto">""" + presentation + """</pre>
        </body>
        </html>"""
    return render_template_string(html_string)