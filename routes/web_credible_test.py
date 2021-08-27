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
    app.add_url_rule('/credible_test/credentialOffer',  view_func=test_credentialOffer_qrcode, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/credible_test/wallet_credential/<id>',  view_func=test_credentialOffer_endpoint, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/test_save_stream',  view_func=test_save_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/credible_test/display',  view_func=test_credential_display, methods = ['GET', 'POST'])

    app.add_url_rule('/credible_test/presentationRequest',  view_func=test_presentationRequest_qrcode, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/credible_test/wallet_presentation/<stream_id>',  view_func=test_presentationRequest_endpoint, methods = ['GET', 'POST'],  defaults={'mode' : mode, 'red' :red})
    app.add_url_rule('/credible_test/presentation_display',  view_func=test_presentation_display, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/presentation_stream',  view_func=presentation_stream, defaults={ 'red' : red})

    global SERVER, PVK, repo
    PVK = privatekey.get_key(mode.owner_talao, 'private_key', mode)
    SERVER = mode.server
    g = Github(mode.github)
    repo = g.get_repo("TalaoDAO/context")
    return


def test_credentialOffer_qrcode(red) :
    if request.method == 'GET' :
        # list all the files of github directory 
        html_string = str()  
        dir_list = dir_list_calculate()
        for filename in dir_list :
            credential = credential_from_filename(filename)
            credential['issuer'] = DID
            html_string += """
                    <p> filename : <a href='/credible_test/display?filename=""" + filename + """'>""" + filename + """</a></p>
                    <p> id : """ + credential.get("id", "") + """</p>
                    <p> type : """ + ", ".join(credential.get("type", "")) + """</p>
                    <p>credentialSubject.type : """ + credential['credentialSubject'].get('type', "") + """ </p>
                    <p> issuer : """ + credential['issuer'] + """ </p>
                    <form action="/credible_test/credentialOffer" method="POST" >
                    <input hidden name="filename" value='""" + filename + """'></input>
                    <button  type"submit" >QR code for Offer</button></form>
                    ------------------"""
        html_string = "<html><body>" + html_string + "</body></html>"
        return render_template_string (html_string) 
    filename = request.form['filename']
    credential = credential_from_filename(filename)
    url = SERVER + "credible_test/wallet_credential/" + credential['id']
    red.set(credential['id'], filename)
    return render_template('credible_test/credential_offer_qr.html', url=url, id=credential['id'])


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
    filename = red.get(id).decode()
    credential = credential_from_filename(filename)
    if request.method == 'GET':
        # avant gestion du bug sur wallet
        credential['credentialSubject']['id'] = "did:..."
        credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        # avant gestion du bug sur wallet
        credential['proof'] =  {
            "@context": [
                "https://identity.foundation/EcdsaSecp256k1RecoverySignature2020/lds-ecdsa-secp256k1-recovery2020-0.0.jsonld",
                "https://demo.spruceid.com/EcdsaSecp256k1RecoverySignature2020/esrs2020-extra-0.0.jsonld"
            ],
            "type": "EcdsaSecp256k1RecoverySignature2020",
            "proofPurpose": "assertionMethod",
            "verificationMethod": "did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250#controller",
            "created": "2021-07-12T07:48:02.147Z",
            "jws": "eyJhbGciOiJFUzI1NkstUiIsImNyaXQiOlsiYjY0Il0sImI2NCI6ZmFsc2V9..4sJPmOqA8bp2WjeH4lCPKj2iAxIG2kB3Ol1gyBpaUxQmyXNjwFPqAjnGGHjK8zt2Izba0QZgA8HSjO2FDOfe8gE"
            }
        return jsonify({
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z"
        })
    elif request.method == 'POST':
        credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        credential['issuer'] = DID
        credential['credentialSubject']['id'] = request.form.get('subject_id', 'unknown DID')
        print(credential)
        signed_credential = vc_signature.sign(credential, PVK, DID)
        # send event to client agent to go forward
        data = json.dumps({'id' : id, 'check' : 'success'})
        red.publish('credible', data)
        return jsonify(signed_credential)


# server event push for user agent EventSource
def test_save_stream(red):
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


####################################

def test_presentationRequest_qrcode(red, mode):
    stream_id = str(uuid.uuid1())
   
    if request.args.get('vc') == 'certificateofemployment' : 
        message = 'Get a Certificate of Employment'
    elif request.args.get('vc') == 'professionalexperienceassessment' :
        message = 'Request a Professional Experience Assessment'
    else :
        message = 'PresentationRequest test'
    return render_template('credible_test/credential_presentation_qr.html',
							url=mode.server + 'credible_test/wallet_presentation/' + stream_id,
							stream_id=stream_id, message=message)


def test_presentationRequest_endpoint(stream_id, red, mode):
    if request.method == 'GET':
        challenge = str(uuid.uuid1()) 
        red.set(stream_id,  challenge)
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
        red.delete(stream_id)
        presentation = json.loads(request.form['presentation'])
		# FIXME pb de version et voir comment on gere le challenge
        try : # FIXME
            issuer = presentation['verifiableCredential']['issuer']
            #holder = presentation['holder']
            response_challenge = presentation['proof']['challenge']
            domain = presentation['proof']['domain']
        except :
            logging.warning('to be fixed, presentation is not correct')
            event_data = json.dumps({"stream_id" : stream_id, "message" : "Presentation check failed."})
            red.publish('credible', event_data)
            return jsonify("ko")
        if domain != mode.server or response_challenge != challenge :
            logging.warning('challenge failed')
            event_data = json.dumps({"stream_id" : stream_id, "message" : "The presentation challenge failed."})
            red.publish('credible', event_data)
            return jsonify("ko")
        elif issuer not in [DID_WEB, DID_ETHR, DID_TZ] :
            logging.warning('unknown issuer')
            event_data = json.dumps({"stream_id" : stream_id, "message" : "This issuer is unknown."})
            red.publish('credible', event_data)
            return jsonify("ko")
        else :
            # we just displzay the presentation VC
            #print(json.dumps(presentation, indent=4))
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
    else :
        presentation = red.get(request.args['stream_id']).decode()
        credential = json.dumps(json.loads(presentation), indent=4)
    html_string = """
        <!DOCTYPE html>
        <html>
        <body class="h-screen w-screen flex">
        <pre class="whitespace-pre-wrap m-auto">""" + credential + """</pre>
        </body>
        </html>"""
    return render_template_string(html_string)


