from flask import jsonify, request, render_template, Response, render_template_string
import json
from datetime import timedelta, datetime
import os


OFFER_DELAY = timedelta(seconds= 10*60)


def init_app(app,red, mode) :
    app.add_url_rule('/credible_test/credentialOffer',  view_func=test_credentialOffer_qrcode, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/credible_test/wallet_credential/<id>',  view_func=test_credentialOffer_endpoint, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/test_save_stream',  view_func=test_save_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/credible_test/display',  view_func=test_credential_display, methods = ['GET', 'POST'])
    global VC_PATH, SERVER
    VC_PATH = mode.sys_path + '/Talao/signed_credentials/'
    SERVER = mode.server
    return


def test_credentialOffer_qrcode(red) :
    if request.method == 'GET' :
        # list all the files of directory 
        dir_list = os.listdir(VC_PATH)
        html_string = str()  
        for filename in dir_list :
            try :
                credential = json.loads(open(VC_PATH + filename, 'r').read())
                print(credential["id"], "-->", credential['credentialSubject'].get('type'))
                html_string += """
                    <p> filename : <a href='/credible_test/display?filename=""" + filename + """'>""" + filename + """</a></p>
                    <p> id : """ + credential["id"] + """</p>
                    <p>credentialSubject.type : """ + credential['credentialSubject'].get('type') + """ </p>
                    <p> issuer : """ + credential['issuer'] + """ </p>
                    <p> issuanceDate : """ + credential['issuanceDate'] + """</p>
                    <form action="/credible_test/credentialOffer" method="POST" >
                    <input hidden name="filename" value='""" + filename + """'></input>
                    <button  type"submit" >QR code for Offer</button></form>
                    ------------------"""
            except :
                print('filename pb = ', filename)
          
        html_string = "<html><body>" + html_string + "</body></html>"
        return render_template_string (html_string) 
    filename = request.form['filename']
    credential = json.loads(open(VC_PATH + filename, 'r').read())
    url = SERVER + "credible_test/wallet_credential/" + credential['id']
    red.set(credential['id'], filename)
    return render_template('credible_test/credential_qr.html', url=url, id=credential['id'])



def test_credential_display():  
    filename = request.args['filename']
    # mise en forme
    credential = json.loads(open(VC_PATH + filename, 'r').read())
    del credential['proof']
    credential['id'] = "urn:uuid:..."
    credential['credentialSubject']['id'] = "did:..."
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
    credential = json.loads(open(VC_PATH + filename, 'r').read())
    if request.method == 'GET':
        del credential['proof']
        credential['id'] = "urn:uuid:..."
        credential['credentialSubject']['id'] = "did:..."
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
