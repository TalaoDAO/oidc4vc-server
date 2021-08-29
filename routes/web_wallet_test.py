from flask import jsonify, request, render_template, Response, render_template_string
import json
from datetime import timedelta, datetime
from signaturesuite import vc_signature
from components import privatekey,ns
from github import Github
import base64
import uuid
import logging

logging.basicConfig(level=logging.INFO)



OFFER_DELAY = timedelta(seconds= 10*60)
DID_WEB = 'did:web:talao.cp'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID = DID_ETHR


def dir_list_calculate() :
    dir_list=list()
    contents = repo.get_contents("test/CredentialOffer")
    for content_file in contents :
        if content_file.name.split('.')[1] =='jsonld' :
            dir_list.append(content_file.name)
    return dir_list


def credential_from_filename(filename) :
    file = repo.get_contents("test/CredentialOffer/" + filename)
    encoded_content = file.__dict__['_rawData']['content']
    return json.loads(base64.b64decode(encoded_content).decode())


def init_app(app,red, mode) :
    app.add_url_rule('/wallet/test/credentialOffer',  view_func=test_credentialOffer_qrcode, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/wallet_credential/<id>',  view_func=test_credentialOffer_endpoint, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/offer_stream',  view_func=offer_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/display',  view_func=test_credential_display, methods = ['GET', 'POST'])

    app.add_url_rule('/wallet/test/presentationRequest',  view_func=test_presentationRequest_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/wallet/test/wallet_presentation/<stream_id>',  view_func=test_presentationRequest_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    app.add_url_rule('/wallet/test/presentation_display',  view_func=test_presentation_display, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/presentation_stream',  view_func=presentation_stream, defaults={ 'red' : red})

    global SERVER, PVK, repo
    PVK = privatekey.get_key(mode.owner_talao, 'private_key', mode)
    SERVER = mode.server
    g = Github(mode.github)
    repo = g.get_repo("TalaoDAO/context")
    return

######################### Credential Offer ###########


def test_credentialOffer_qrcode(red) :
    if request.method == 'GET' :
        # list all the files of github directory 
        html_string = str()  
        dir_list = dir_list_calculate()
        for filename in dir_list :
            credential = credential_from_filename(filename)
            credential['issuer'] = DID
            html_string += """
                    <p> filename : <a href='/wallet/test/display?filename=""" + filename + """'>""" + filename + """</a></p>
                    <p> id : """ + credential.get("id", "") + """</p>
                    <p> type : """ + ", ".join(credential.get("type", "")) + """</p>
                    <p>credentialSubject.type : """ + credential['credentialSubject'].get('type', "") + """ </p>
                    <p> issuer : """ + credential['issuer'] + """ </p>
                    <form action="/wallet/test/credentialOffer" method="POST" >
                    <input hidden name="filename" value='""" + filename + """'> 
                    
                    <p>Scopes :
                    Subject_id<input type="checkbox" disabled checked  >
                    givenName<input type="checkbox" name="givenName"  value="on">
                    familyName<input type="checkbox" name="familyName" value="on">
                    email<input type="checkbox" name="email" value="on">
                    address<input type="checkbox" name="address"  value="on">
                    phone<input type="checkbox" name="phone"  value="on"> </p>
                    <br><br><button  type"submit" >QR code for Offer</button></form>
                    ------------------"""
        html_string = "<html><body><br><h1><strong>Issuer Simulator</strong></h1><br>" + html_string + "</body></html>"
        return render_template_string (html_string) 
    else :
        filename = request.form['filename']
        credential = credential_from_filename(filename)
        credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        credential['credentialSubject']['id'] = "did:..."
        credential['proof'] =  {"@context": [],"type": "","proofPurpose": "","verificationMethod": "","created": "","jws": ""}
        credential['issuer'] = DID
        scopes = ["subject_id"]
        if request.form.get("address") :
            scopes.append("address")
        if request.form.get("phone") :
            scopes.append("phone")
        if request.form.get("givenName") :
            scopes.append("givenName")
        if request.form.get("familyName") :
            scopes.append("familyName")
        if request.form.get("email") :
            scopes.append("email")
        credentialOffer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
            "scopes" : scopes
        }
        url = SERVER + "wallet/test/wallet_credential/" + credential['id']
        red.set(credential['id'], json.dumps(credentialOffer))
        return render_template('wallet/test/credential_offer_qr.html',
                                url=url,
                                id=credential['id'],
                                credentialOffer=json.dumps(credentialOffer, indent=4),
                                type = credentialOffer['credentialPreview']['type'][1]
                                )


def test_credential_display():  
    filename = request.args['filename']
    # mise en forem
    credential = credential_from_filename(filename)
    credential['credentialSubject']['id'] = "did:..."
    credential['issuer'] = DID
    credential_txt = json.dumps(credential, indent=4)
    html_string = """
        <!DOCTYPE html>
        <html>
        <body class="h-screen w-screen flex">
        <pre class="whitespace-pre-wrap m-auto">""" + credential_txt + """</pre>
        </body>
        </html>"""
    return render_template_string(html_string)


def test_credentialOffer_endpoint(id, red):
    credentialOffer = json.loads(red.get(id).decode())
    if request.method == 'GET':
        return jsonify(credentialOffer)
    else :
        credential =  credentialOffer['credentialPreview']
        red.delete(id)
        try :
            credential['credentialSubject']['id'] = request.form['subject_id']
        except :
            logging.error("wallet error")
            return jsonify('ko')
        del credential['proof']
        signed_credential = vc_signature.sign(credential, PVK, DID)
        # send event to client agent to go forward
        data = json.dumps({'id' : id, 'check' : 'success'})
        red.publish('credible', data)
        return jsonify(signed_credential)


# server event push for user agent EventSource
def offer_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('credible')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()  
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)


######################### Presentation Request ###########

DIDAuth = {
            "type": "VerifiablePresentationRequest",
            "query": {
            	"type": 'DIDAuth'
            },
            "challenge": "",
            "domain" : ""
            }

QueryBYExample = {
            "type": "VerifiablePresentationRequest",
            "query": {
                "type": "QueryByExample",
                "credentialQuery": ""
            },
            "challenge": "",
            "domain" : ""
            }

pattern = QueryBYExample

def test_presentationRequest_qrcode(red, mode):
    if request.method == 'GET' :
        return render_template('wallet/test/credential_presentation.html')
							
    else :
        stream_id = str(uuid.uuid1())
        if request.form['query'] == 'DIDAuth' :
            pattern = DIDAuth
        else :
            pattern =  QueryBYExample
            pattern['query']["credentialQuery"] = dict()
            if request.form.get('reason') :
                pattern['query']["credentialQuery"]['reason'] = [
                                                                {"@value": "Text in English", "@language": "en"},
                                                                {"@value" : request.form['reason'], "@language" : "fr"},
                                                                {"@value" : "text in German", "@language": "De"}
                                                                ]            
            if request.form.get('type') :
                pattern['query']["credentialQuery"]['type'] = [key.replace(" ", "") for key in request.form['type'].split(',') ]
            if request.form.get('trustedIssuer') :
                pattern['query']["credentialQuery"]['trustedIssuer'] = [key.replace(" ", "") for key in request.form['trustedIssuer'].split(',') ]
            if request.form.get('credentialSchema') :
                pattern['query']["credentialQuery"]['credentialSchema'] = [key.replace(" ", "") for key in request.form['credentialSchema'].split(',') ]
        pattern['challenge'] = str(uuid.uuid1())
        pattern['domain'] = mode.server
        red.set(stream_id,  json.dumps(pattern))
        return render_template('wallet/test/credential_presentation_qr.html',
							url=mode.server + 'wallet/test/wallet_presentation/' + stream_id,
							stream_id=stream_id, 
                            pattern=json.dumps(pattern, indent=4))

def test_presentationRequest_endpoint(stream_id, red):
    pattern = json.loads(red.get(stream_id).decode())
    challenge = pattern['challenge']
    domain = pattern['domain']
    if request.method == 'GET':
        return jsonify(pattern)
    elif request.method == 'POST' :
        red.delete(stream_id)
        presentation = json.loads(request.form['presentation'])
        try : 
            response_challenge = presentation['proof']['challenge']
            response_domain = presentation['proof']['domain']
        except :
            logging.warning('presentation is not correct')
            event_data = json.dumps({"stream_id" : stream_id, "message" : "Presentation format failed."})
            red.publish('credible', event_data)
            return jsonify("ko")
        if response_domain != domain or response_challenge != challenge :
            logging.warning('challenge or domain failed')
            event_data = json.dumps({"stream_id" : stream_id, "message" : "The presentation challenge failed."})
            red.publish('credible', event_data)
            return jsonify("ko")
        else :
            # we just display the presentation VC
            red.set(stream_id,  request.form['presentation'])
            event_data = json.dumps({"stream_id" : stream_id,
			                        "message" : "ok"})           
            red.publish('credible', event_data)
            return jsonify("ok")


def event_stream(red):
    pubsub = red.pubsub()
    pubsub.subscribe('credible')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def presentation_stream(red):
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)


def test_presentation_display(red):  
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
        credential = json.dumps(presentation, indent=4)
    html_string = """
        <!DOCTYPE html>
        <html>
        <body class="h-screen w-screen flex">
        <br>Number of credentials : """ + nb_credentials + """<br>
        <br>Holder (wallet DID)  : """ + holder + """<br>
        <br>Issuers : """ + issuers + """<br>
        <br>Credential types : """ + types + """
        <br><br><br>
         <form action="/wallet/test/presentationRequest" method="GET" >
                    <button  type"submit" >QR code for Request</button></form>
                    <br>---------------------------------------------------<br>
        <pre class="whitespace-pre-wrap m-auto">""" + credential + """</pre>
        </body>
        </html>"""
    return render_template_string(html_string)


