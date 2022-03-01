from flask import jsonify, request, render_template, Response, render_template_string, redirect, url_for
import json
from datetime import timedelta, datetime
from signaturesuite import vc_signature
from components import privatekey
from github import Github
import base64
import uuid
import logging
from flask_babel import _
from urllib.parse import urlencode


logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)
TEST_REPO = "TalaoDAO/wallet-tools"
REGISTRY_REPO = "TalaoDAO/context"
DID_WEB = 'did:web:talao.co'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ2 = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY =  'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'        

did_selected = DID_ETHR

QueryBYExample = {
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

pattern = QueryBYExample

try :
    RSA = open("/home/admin/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
    P256 = json.dumps(json.load(open("/home/admin/Talao/keys.json", "r"))['talaonet'].get('talao_P256_private_key'))
    Ed25519 = json.dumps(json.load(open("/home/admin/Talao/keys.json", "r"))['talaonet'].get('talao_Ed25519_private_key'))

except :
    RSA = open("/home/thierry/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
    P256 = json.dumps(json.load(open("/home/thierry/Talao/keys.json", "r"))['talaonet'].get('talao_P256_private_key'))
    Ed25519 = json.dumps(json.load(open("/home/thierry/Talao/keys.json", "r"))['talaonet'].get('talao_Ed25519_private_key'))


def translate(credential) : 
    credential_name = ""
    try : 
        for name in credential['name'] :
            if name['@language'] == 'fr' :
                credential_name = name['@value']
                break
    except :
        pass
    return credential_name
    

def dir_list_calculate(path) :
    dir_list=list()
    contents = test_repo.get_contents(path)
    for content_file in contents :
        if content_file.name.split('.')[1] =='jsonld' :
            dir_list.append(content_file.name)
    return dir_list


def credential_from_filename(path, filename) :
    file = test_repo.get_contents(path + "/" + filename)
    encoded_content = file.__dict__['_rawData']['content']
    return json.loads(base64.b64decode(encoded_content).decode())


def init_app(app,red, mode) :
    app.add_url_rule('/wallet/test/credentialOffer',  view_func=test_credentialOffer_qrcode, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/wallet/test/credentialOffer2',  view_func=test_credentialOffer2_qrcode, methods = ['GET', 'POST'])
    app.add_url_rule('/wallet/test/credentialOffer_back',  view_func=test_credentialOffer_back, methods = ['GET'])
    app.add_url_rule('/wallet/test/wallet_credential/<id>',  view_func=test_credentialOffer_endpoint, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/offer_stream',  view_func=offer_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/display',  view_func=test_credential_display, methods = ['GET', 'POST'])
    app.add_url_rule('/wallet/test/direct_offer',  view_func=test_direct_offer, methods = ['GET'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/wallet/test/presentationRequest',  view_func=test_presentationRequest_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/wallet/test/wallet_presentation/<stream_id>',  view_func=test_presentationRequest_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    app.add_url_rule('/wallet/test/presentation_display',  view_func=test_presentation_display, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/presentation_stream',  view_func=presentation_stream, defaults={ 'red' : red})

    app.add_url_rule('/wallet/playground',  view_func=playground, methods = ['GET', 'POST'])
    app.add_url_rule('/playground',  view_func=playground, methods = ['GET', 'POST'])
    app.add_url_rule('/playground/prosoon',  view_func=playground_prosoon, methods = ['GET', 'POST'])
    app.add_url_rule('/playground/grant',  view_func=playground_grant, methods = ['GET', 'POST'])
    app.add_url_rule('/playground/new',  view_func=playground_new, methods = ['GET', 'POST'])

    global PVK, test_repo, registry_repo
    PVK = privatekey.get_key(mode.owner_talao, 'private_key', mode)
    g = Github(mode.github)
    test_repo = g.get_repo(TEST_REPO)
    registry_repo = g.get_repo(REGISTRY_REPO)
    return



########################  playground ##########################""
def playground() :
    global status
    return render_template("./wallet/test/playground.html")

def playground_prosoon() :
    global status
    return render_template("./wallet/test/prosoon.html")

def playground_grant() :
    global status
    return render_template("./wallet/test/grant.html")

def playground_new() :
    global status
    return render_template("./wallet/test/playground_new.html")


######################### Credential Offer ###########
def test_credentialOffer2_qrcode() :
    return redirect(url_for("test_credentialOffer_qrcode", path="test/CredentialOffer2"))

"""
Direct access to one VC with filename passed as an argument
"""
def test_direct_offer(red, mode) :
    try :
        VC_filename= request.args['VC']
    except :
        return jsonify("Request malformed"), 400
    try :
        credential = credential_from_filename("test/CredentialOffer2", VC_filename)
    except :
        return jsonify("Verifiable Credential not found"), 405
    if request.args.get('method') == "ethr" :
        credential['issuer'] = DID_ETHR
    elif request.args.get('method') == "key" :
        credential['issuer'] = DID_KEY
    else :
        credential['issuer'] = DID_TZ2
    credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    credential['credentialSubject']['id'] = "did:..."
    backgroundColor = "ffffff"
    shareLink = ""
    if VC_filename == "visa_card.jsonld" :
        backgroundColor = "fea235"
    elif VC_filename == "amex_card.jsonld" :
        backgroundColor = "a9afaf"
    elif VC_filename == "LoyaltyCard.jsonld" :
        shareLink = "https://www.leroymerlin.fr/ma-carte-maison.html"
    else :
        pass
    credentialOffer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
            "shareLink" : shareLink,
            "display" : { "backgroundColor" : backgroundColor}
        }
    """ later 
    try :
        key = helpers.ethereum_to_jwk256k(PVK)
        registration = didkit.did_auth(did_selected, '{}' , key)
    except:
        registration = "" 
    url = mode.server + "wallet/test/wallet_credential/" + credential['id'] + '?' + urlencode({'registration' : registration})
    """
    url = mode.server + "wallet/test/wallet_credential/" + credential['id'] + '?issuer=' + did_selected

    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
    red.set(credential['id'], json.dumps(credentialOffer))
    type = credentialOffer['credentialPreview']['type'][1]
    return render_template('wallet/test/credential_offer_qr_2.html',
                                url=url,
                                deeplink=deeplink,
                                id=credential['id'],
                                type = type + " - " + translate(credential)
                                )


def test_credentialOffer_qrcode(red, mode) :
    global did_selected 
    if request.method == 'GET' :   
        try :
            path = request.args['path']
        except :
            path = "test/CredentialOffer"
        # list all the files of github directory 
        dir_list = dir_list_calculate(path)
        html_string = """
                    <p> type : EmailPass</p>
                    <p>  name : <strong>Proof of email / Preuve d"email (personalisée) </strong></p>
                    <form action="/wallet/test/credentialOffer" method="POST" >
                    
                    Issuer : <select name="did_select">
                        <option value=""" + DID_TZ2 + """>""" + DID_TZ2 + """</option>
                        <option selected value=""" + DID_ETHR + """>""" + DID_ETHR + """</option>
                        <option value="did:web:talao.co#key-1">did:web:talao.co#key-1 (Secp256k1)</option>
                        <option value="did:web:talao.co#key-2">did:web:talao.co#key-2 (RSA)</option>
                         <option value="did:web:talao.co#key-3">did:web:talao.co#key-3 (Ed25519)</option>
                          <option value="did:web:talao.co#key-4">did:web:talao.co#key-4 (P-256)</option>
                        <option value=""" + DID_KEY + """>""" + DID_KEY + """</option>
                        </select><br>
                        <input hidden name="path" value=""" + path + """> 
                        <input hidden name="filename" value=""" + "talaoemailpass" + """>
                        <br><button  type"submit" > Generate a QR code for this Credential Offer</button>
                    </form><hr>

                      <p> type : PhonePass</p>
                    <p>  name : <strong>Proof of telephone number / Preuve de numéro de téléphone (personalisée) </strong></p>
                    <form action="/wallet/test/credentialOffer" method="POST" >
                    
                      Issuer : <select name="did_select">
                      <option selected value=""" + DID_TZ2 + """>""" + DID_TZ2 + """</option>
                        <option value="""+ DID_ETHR + """>""" + DID_ETHR + """</option>
                        <option value="did:web:talao.co#key-1">did:web:talao.co#key-1 (Secp256k1)</option>
                        <option value="did:web:talao.co#key-2">did:web:talao.co#key-2 (RSA)</option>
                         <option value="did:web:talao.co#key-3">did:web:talao.co#key-3 (Ed25519)</option>
                          <option value="did:web:talao.co#key-4">did:web:talao.co#key-4 (P-256)</option>
                        <option value=""" + DID_KEY + """>""" + DID_KEY + """</option>
                        
                        </select><br>
                        <input hidden name="path" value=""" + path + """> 
                         <input hidden name="filename" value=""" + "talaophonepass" + """>
                        <br><button  type"submit" > Generate a QR code for this Credential Offer</button>
                    </form><hr>"""
        for filename in dir_list :
            credential = credential_from_filename(path, filename)
            credential['issuer'] = ""
            credential_name = translate(credential)
            html_string += """
                    <p> Credential preview : <a href='/wallet/test/display?path="""+ path + """&filename=""" + filename + """'>""" + filename + """</a></p>
                    <p> id : """ + credential.get("id", "") + """</p> 
                    <p> type : """ + ", ".join(credential.get("type", "")) + """</p>
                    <p>credentialSubject.type : <strong>""" + credential['credentialSubject'].get('type', "") + """ / """ + credential_name + """</strong> </p>
                    <form action="/wallet/test/credentialOffer" method="POST" >
                    
                    Issuer : <select name="did_select">
                    <option value="""+ DID_TZ2 + """>""" + DID_TZ2 + """</option>
                        <option selected value=""" + DID_ETHR + """>""" + DID_ETHR + """</option>
                        <option value="did:web:talao.co#key-1">did:web:talao.co#key-1 (Secp256k1)</option>
                        <option value="did:web:talao.co#key-2">did:web:talao.co#key-2 (RSA)</option>
                         <option value="did:web:talao.co#key-3">did:web:talao.co#key-3 (Ed25519)</option>
                          <option value="did:web:talao.co#key-4">did:web:talao.co#key-4 (P-256)</option>
                        <option value=""" + DID_KEY + """>""" + DID_KEY + """</option>
                        </select><br><br>
                        <input hidden name="path" value=""" + path + """> 
                        <input hidden name="filename" value='""" + filename + """'> 
                        <p>backgroundColor : <input value="#ffffff" type="color" name="backgroundColor" ></p>
                        <p>shareLink : <input type="text" name="shareLink" ></p>
                        <input hidden name="filename" value=""" + "talaophonepass" + """>
                        <input hidden name="path" value=""" + path + """> 
                        <br><button  type"submit" > Generate QR code for a Credential Offer</button>
                    </form>
                    <hr>"""
        html_string = """<html><head>{% include 'head.html' %}</head>
                        <body> {% include '/wallet/test/simulator_nav_bar.html' %}
                            <div class="m-5">
                                <br><br>""" + html_string + """
                            </div>
                            <script src="{{ url_for('static', filename='jquery-3.5.1.slim.min.js') }}"></script>
                            <script src="{{ url_for('static', filename='bs-init.js') }}"></script>
                            <script src="{{ url_for('static', filename='bootstrap.min.js') }}"></script>
                            <script src="{{ url_for('static', filename='in_progress_button.js') }}"></script>
                        </body></html>"""

        return render_template_string (html_string,simulator="Issuer simulator") 
    else :   
        path = request.form['path']   
        if request.form['did_select'].split(':')[1] == 'web' :
            did_selected = request.form['did_select']
            did_issuer = 'did:web:talao.co'
        else :
            did_issuer = request.form['did_select']
        filename = request.form['filename']
        if filename == "talaoemailpass" :
            return redirect('/emailpass')
        if filename == "talaophonepass" :
            return redirect('/phonepass')
        credential = credential_from_filename(path, filename)
        credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        credential['credentialSubject']['id'] = "did:..."
        credential['issuer'] = did_issuer
        scope = ["subject_id"]
        #if request.form.get("address") :
        #    scope.append("address")
        #if request.form.get("telephone") :
        #    scope.append("telephone")
        #if request.form.get("givenName") :
        #    scope.append("givenName")
        #if request.form.get("familyName") :
        #    scope.append("familyName")
        #if request.form.get("email") :
        #    scope.append("email")
        display = dict()
        if request.form.get('backgroundColor') :
            display['backgroundColor'] = request.form['backgroundColor'][1:]
        #if request.form.get('icon') :
        #    display['icon'] = request.form['icon']
        #if request.form.get('nameFallback') :
        #    display['nameFallback'] = request.form['nameFallback']
        #if request.form.get('descriptionFallback') :
        #    display['descriptionFallback'] = request.form['descriptionFallback']
        credentialOffer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
            "scope" : scope,
            "display" : display
        }
        if request.form.get('shareLink') :
            credentialOffer['shareLink'] = request.form['shareLink']
        url = mode.server + "wallet/test/wallet_credential/" + credential['id'] + '?' + urlencode({'issuer' : did_issuer})
        deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url })
        red.set(credential['id'], json.dumps(credentialOffer))
        type = credentialOffer['credentialPreview']['type'][1]
        return render_template('wallet/test/credential_offer_qr.html',
                                url=url,
                                deeplink=deeplink,
                                id=credential['id'],
                                credentialOffer=json.dumps(credentialOffer, indent=4),
                                type = type + " - " + translate(credential),
                                simulator='Verifier Simulator' 
                                )


def test_credential_display():  
    path = request.args['path']
    filename = request.args['filename']
    try :
        credential = credential_from_filename(path, filename)
    except :
        return jsonify('Credential not found'), 400
    credential['credentialSubject']['id'] = "did:..."
    credential['issuer'] = ""
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
    try : 
        credentialOffer = red.get(id).decode()
    except :
        logging.error("red.get(id) error")
        return jsonify('server error'), 500
    if request.method == 'GET':
        return Response(json.dumps(credentialOffer, separators=(':', ':')),
                        headers={ "Content-Type" : "application/json"},
                        status=200)
                        
    else :
        credential =  json.loads(credentialOffer)['credentialPreview']
        red.delete(id)
        try :
            credential['credentialSubject']['id'] = request.form['subject_id']
        except :
            logging.error("wallet error")
            return jsonify('wallet error'), 400
        # to keep the possibility to use an RSA key with did:web
        global did_selected
        if did_selected == 'did:web:talao.co#key-2' :
            signed_credential = vc_signature.sign(credential, PVK, "did:web:talao.co", rsa=RSA)
        elif did_selected == 'did:web:talao.co#key-3' :
            signed_credential = vc_signature.sign(credential, PVK, "did:web:talao.co", P256=P256)
        elif did_selected == 'did:web:talao.co#key-4' :
            signed_credential = vc_signature.sign(credential, PVK, "did:web:talao.co", Ed25519=Ed25519)
        else :
            signed_credential = vc_signature.sign(credential, PVK, credential['issuer'])
        # send event to client agent to go forward
        data = json.dumps({
                            'id' : id,
                            'check' : 'success',
                            'scope' : '',
                            'signed_credential' : signed_credential
                            })
        red.publish('credible', data)
        return Response(json.dumps(signed_credential, separators=(':', ',')),
                        headers={ "Content-Type" : "application/json"},
                        status=200)


def test_credentialOffer_back():
    html_string = """
        <!DOCTYPE html>
        <html>
        
        <body class="h-screen w-screen flex ">
        <p></p>
        <h2>Verifiable Credential has been signed and transfered to wallet"</h2<
        <br><br><br>
        <form action="/playground" method="GET" >
                    <button  type"submit" >Back Playground </button></form>
        <form action="/playground/prosoon" method="GET" >
                    <button  type"submit" >Back Prosoon</button></form>
        <form action="/playground/new" method="GET" >
                    <button  type"submit" >Back Playground/New</button></form>
        </body>
        </html>"""
    return render_template_string(html_string)


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
           "query": [
               {
                    "type" : "DIDAuth"
                }
           ],
           "challenge": "",
           "domain" : ""
            }
 


def test_presentationRequest_qrcode(red, mode):
    if request.method == 'GET' :
        return render_template('wallet/test/credential_presentation.html', simulator='Verifier Simulator' )
							
    else :
        stream_id = str(uuid.uuid1())
        if request.form['query'] == 'DIDAuth' :
            pattern = DIDAuth
        else :
            pattern =  QueryBYExample
            pattern['query'][0]["credentialQuery"] = list()
            for q in ["1","2","3"] :
                if request.form.get('trustedIssuer' + q) or request.form.get('type' + q) or request.form.get('credentialSchema' + q) : 
                    MycredentialQuery = dict()
                    if request.form.get('reason' + q) :
                        MycredentialQuery['reason'] = [
                                                {"@value": "Text in English", "@language": "en"},
                                                {"@value" : request.form['reason' + q], "@language" : "fr"},
                                                {"@value" : "text in German", "@language": "De"}
                                                ]
                    MycredentialQuery['example'] = dict()
                    if request.form.get('type' + q) :
                        MycredentialQuery['example']['type'] =  request.form['type' + q]
                    if request.form.get('trustedIssuer' + q) :
                        MycredentialQuery['example']['trustedIssuer' + q] = list()
                        for issuer in [key.replace(" ", "") for key in request.form['trustedIssuer' + q].split(',')] :
                            MycredentialQuery['example']['trustedIssuer'].append({"issuer" : issuer})   
                    if request.form.get('credentialSchema' + q) :
                        MycredentialQuery['example']['credentialSchema'] = {'type' : request.form['credentialSchema' + q]}
                    pattern['query'][0]['credentialQuery'].append(MycredentialQuery)
        pattern['challenge'] = str(uuid.uuid1())
        pattern['domain'] = mode.server
        red.set(stream_id,  json.dumps(pattern))
        url = mode.server + 'wallet/test/wallet_presentation/' + stream_id +'?issuer=' + DID_TZ2
        return render_template('wallet/test/credential_presentation_qr.html',
							url=url,
							stream_id=stream_id, 
                            pattern=json.dumps(pattern, indent=4),
                            simulator="Verifier Simulator")


def test_presentationRequest_endpoint(stream_id, red):
    try : 
        my_pattern = json.loads(red.get(stream_id).decode())
    except :
        logging.error("red get id error")
        return jsonify('ko'), 500
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
            red.publish('credible', event_data)
            return jsonify("presentation is not correct"), 400
        if response_domain != domain or response_challenge != challenge :
            logging.warning('challenge or domain failed')
            logging.warning("domain = %s", response_domain)
            logging.warning('challenge = %s', response_challenge)
            #event_data = json.dumps({"stream_id" : stream_id, "message" : "The presentation challenge failed."})
            #red.publish('credible', event_data)
            #return jsonify("challenge or domain failed"), 401
        # we just display the presentation VC
        red.set(stream_id,  request.form['presentation'])
        event_data = json.dumps({"stream_id" : stream_id,
			                        "message" : "ok"})           
        red.publish('credible', event_data)
        return jsonify("ok"), 200


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
        if not presentation.get('verifiableCredential') :
            nb_credentials = "0"
            issuers= "issued by me !"
            types = "DID_Auth"
        elif isinstance(presentation['verifiableCredential'], dict) :
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
        credential = json.dumps(presentation, indent=4, ensure_ascii=False)
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


