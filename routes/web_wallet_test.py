from flask import jsonify, request, render_template, Response, render_template_string, redirect, url_for
import json
from datetime import timedelta, datetime
from signaturesuite import vc_signature
from github import Github
import base64
import uuid
import didkit
import logging
from urllib.parse import urlencode
import ebsi


logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)
REGISTRY_REPO = "TalaoDAO/context"
DID_WEB = 'did:web:talao.co'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ2 = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY =  'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'        
DID_TZ1 = "did:tz:tz1NyjrTUNxDpPaqNZ84ipGELAcTWYg6s5Du"

did_selected = DID_TZ1

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
    Secp256kr  = json.dumps(json.load(open("/home/admin/sandbox/keys.json", "r"))['talao_secp256kr'])
    P256 = json.dumps(json.load(open("/home/admin/sandbox/keys.json", "r"))['talao_P256_private_key'])
    Ed25519 = json.dumps(json.load(open("/home/admin/sandbox/keys.json", "r"))['talao_Ed25519_private_key'])

except :
    Secp256kr  = json.dumps(json.load(open("/home/thierry/sandbox/keys.json", "r"))['talao_secp256kr'])
    P256 = json.dumps(json.load(open("/home/thierry/sandbox/keys.json", "r"))['talao_P256_private_key'])
    Ed25519 = json.dumps(json.load(open("/home/thierry/sandbox/keys.json", "r"))['talao_Ed25519_private_key'])
    

def dir_list_calculate() :
    dir_list=list()
    contents = registry_repo.get_contents("context")
    for content_file in contents :
        if content_file.name.split('.')[1] =='jsonld' :
            dir_list.append(content_file.name)
    return dir_list


def credential_from_filename(path, filename) :
    file = registry_repo.get_contents(path  + '/' + filename)
    encoded_content = file.__dict__['_rawData']['content']
    return json.loads(base64.b64decode(encoded_content).decode())
      

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/credentialOffer',  view_func=test_credentialOffer_qrcode, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/credentialOffer2',  view_func=test_credentialOffer2_qrcode, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/credentialOffer_back',  view_func=test_credentialOffer_back, methods = ['GET'])
    app.add_url_rule('/sandbox/wallet_credential/<id>',  view_func=test_credentialOffer_endpoint, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/offer_stream',  view_func=offer_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    #app.add_url_rule('/sandbox/display',  view_func=test_credential_display, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/direct_offer',  view_func=test_direct_offer, methods = ['GET'], defaults={'red' :red, 'mode' : mode})

    # Test QueryByExample test
    app.add_url_rule('/sandbox/presentationRequest',  view_func=test_presentationRequest_qrcode, methods = ['GET', 'POST'], defaults={'red' : red, 'mode' : mode})
    app.add_url_rule('/sandbox/wallet_presentation/<stream_id>',  view_func=test_presentationRequest_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    app.add_url_rule('/sandbox/presentation_display',  view_func=test_presentation_display, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/presentation_stream',  view_func=presentation_stream, defaults={ 'red' : red})

    # Playground screen
    app.add_url_rule('/sandbox',  view_func=sandbox, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/playground',  view_func=playground, methods = ['GET', 'POST'])

    global registry_repo
    g = Github(mode.github)
    registry_repo = g.get_repo(REGISTRY_REPO)
    return



def sandbox() :
    global status
    return redirect("/sandbox/saas4ssi")

def playground() :
    global status
    return render_template("playground.html")


######################### Credential Offer ###########

def test_credentialOffer2_qrcode() :
    return redirect(url_for("test_credentialOffer_qrcode", path="context"))


"""
Direct access to one VC with filename passed as an argument
"""
def test_direct_offer(red, mode) :
    try :
        VC_filename= request.args['VC']
    except :
        return jsonify("Request malformed"), 400
    try :
        credential = credential_from_filename("context", VC_filename)
    except :
        return jsonify("Verifiable Credential not found"), 500
    if request.args.get('method') == "ethr" :
        credential['issuer'] = DID_ETHR
    elif request.args.get('method') == "key" :
        credential['issuer'] = DID_KEY
    else :
        credential['issuer'] = DID_TZ1
    credential['issuanceDate'] = datetime.utcnow().isoformat() + "Z"
    credential['expirationDate'] =  (datetime.now() + timedelta(days= 365)).isoformat() + "Z"
    credential['credentialSubject']['id'] = "did:..."
    credential['id'] = "urn:uuid:" + str(uuid.uuid1())

    if VC_filename == "VerifiableDiploma.jsonld" :
        credential["issuer"] ="did:ebsi:zdRvvKbXhVVBsXhatjuiBhs"
        credential["issued"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        credential["validFrom"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    
    credentialOffer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z"
        }
    
    if VC_filename == "TezLoyaltyCard_1.jsonld" :
        filename = "./credential_manifest/loyaltycard_credential_manifest.json"
    
    # EBSI signer
    elif VC_filename == "VerifiableDiploma.jsonld" :
        filename = "./credential_manifest/VerifiableDiploma_credential_manifest.json"
    
    elif VC_filename == "VerifiableId.jsonld" :
        filename = "./credential_manifest/verifiableid_credential_manifest.json"

    elif VC_filename == "TezVoucher_1.jsonld" :
        filename = "./credential_manifest/voucher_credential_manifest.json"

    elif VC_filename == "compellio_ticket.jsonld" :
        filename = "./credential_manifest/compellio_ticket_cm.json"
    
    elif VC_filename == "AragoPass.jsonld" :
        filename = "./credential_manifest/AragoPass_credential_manifest.json"
    
    elif VC_filename == "CustomType.jsonld" :
        filename = "./credential_manifest/CustomType_credential_manifest.json"

    elif VC_filename == "GamerPass.jsonld" :
        filename = "./credential_manifest/GamerPass_credential_manifest.json"

    elif VC_filename == "LoyaltyCard.jsonld" :
        filename = "./credential_manifest/LoyaltyCard_credential_manifest.json"
    
    elif VC_filename == "PCDSAgentCertificate.jsonld" :
        filename = "./credential_manifest/PCDSAgentCertificate_credential_manifest.json"
    
    elif VC_filename == "Test.jsonld" :
        filename = "./credential_manifest/Test_credential_manifest.json"

    elif VC_filename == "MembershipCard_1.jsonld" :
        filename = "./credential_manifest/MembershipCard_1_credential_manifest.json"
    
    else : 
        filename = None
        credential_manifest = "{}" 

    if filename :
        with open(filename, "r") as f:
            credential_manifest = f.read()
    
    credentialOffer['credential_manifest'] = json.loads(credential_manifest)

    id =  str(uuid.uuid1())
    url = mode.server + "sandbox/wallet_credential/" + id + '?issuer=' + did_selected
    deeplink_talao = mode.deeplink_talao + 'app/download?' + urlencode({'uri' : url })
    deeplink_altme = mode.deeplink_altme + 'app/download?' + urlencode({'uri' : url })
    red.set(id, json.dumps(credentialOffer))
    mytype = credentialOffer['credentialPreview']['type'][1]
    return render_template('credential_offer_qr_2.html',
                                url=url,
                                deeplink=deeplink_talao,
                                altme_deeplink=deeplink_altme,
                                id=id,
                                credential_manifest = json.dumps(credentialOffer['credential_manifest'],indent=4),
                                )


def test_credentialOffer_qrcode(red, mode) :
    global did_selected 
    if request.method == 'GET' :   
        # list all the files of github directory 
        dir_list = dir_list_calculate()
        path = "context"
        html_string = str()
        for filename in dir_list :
            try :
                credential = credential_from_filename("context", filename)
                credential['issuer'] = ""
                html_string += """
                    <p>credentialSubject.type : <strong>""" + credential['credentialSubject'].get('type', "Not indicated") +  """</strong> </p>
                    <form action="/sandbox/credentialOffer" method="POST" >
                    
                    Issuer : <select name="did_select">
                        <option selected value="""+ DID_TZ1 + """>""" + DID_TZ1 + """</option>
                        <option value="""+ DID_TZ2 + """>""" + DID_TZ2 + """</option>
                        <option value=""" + DID_ETHR + """>""" + DID_ETHR + """</option>
                        <option value=""" + DID_KEY + """>""" + DID_KEY + """</option>
                        </select><br><br>
                        <input hidden name="path" value=""" + path + """> 
                        <input hidden name="filename" value='""" + filename + """'> 
                        <br><button  type"submit" > Generate QR code for a Credential Offer</button>
                    </form>
                    <hr>"""
            except :
                logging.info("credential mal formaté %s", filename)
                pass
        html_string = """<html><head>{% include 'head.html' %}</head>
                        <body> {% include 'sandbox_nav_bar.html' %}
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
        try : 
            credential = credential_from_filename(path, filename)
        except :
            return redirect ('/playground')
        credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        credential['credentialSubject']['id'] = "did:..."
        credential['issuer'] = did_issuer
        credentialOffer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
        }
        url = mode.server + "sandbox/wallet_credential/" + credential['id'] + '?' + urlencode({'issuer' : did_issuer})
        deeplink_talao = mode.deeplink_talao + 'app/download?' + urlencode({'uri' : url })
        deeplink_altme = mode.deeplink_altme + 'app/download?' + urlencode({'uri' : url })
        red.set(credential['id'], json.dumps(credentialOffer))
        type = credentialOffer['credentialPreview']['type'][1]
        return render_template('credential_offer_qr.html',
                                url=url,
                                deeplink=deeplink_talao,
                                altme_deeplink=deeplink_altme,
                                id=credential['id'],
                                credentialOffer=json.dumps(credentialOffer, indent=4),
                                simulator='Verifier Simulator' 
                                )


def test_credential_display():  
    filename = request.args['filename']
    try :
        credential = credential_from_filename("context", filename)
    except :
        logging.warning("credential mal formaté %s", filename)
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


async def test_credentialOffer_endpoint(id, red):
    try : 
        credentialOffer = red.get(id).decode()
    except :
        logging.error("red.get(id) error")
        return jsonify('server error'), 500
    # wallet GET
    if request.method == 'GET':
        return Response(json.dumps(credentialOffer, separators=(':', ':')),
                        headers={ "Content-Type" : "application/json"},
                        status=200)
                        
    # wallet POST
    else :
        credential =  json.loads(credentialOffer)['credentialPreview']
        red.delete(id)
      
        credential['credentialSubject']['id'] = request.form['subject_id']
        presentation = json.loads(request.form['presentation'])
    
        # to keep the possibility to use an RSA key with did:web

        global did_selected
        if  credential["issuer"][:8] == "did:ebsi" :
            logging.info("ebsi signer")
            signed_credential = ebsi.lp_sign(credential, Secp256kr, credential["issuer"])
            #filename = './signed_credentials/verifiablediploma' + '.jsonld'
            #with open(filename, 'w') as outfile :
            #    outfile.write(json.dumps(signed_credential, indent=4, ensure_ascii=False))
        else :
            if did_selected == 'did:web:talao.co#key-1' :
                signed_credential = vc_signature.sign(credential, Secp256kr, "did:web:talao.co") 
            elif did_selected == 'did:web:talao.co#key-3' :
                signed_credential = vc_signature.sign(credential, Secp256kr, "did:web:talao.co", P256=P256)
            elif did_selected == 'did:web:talao.co#key-4' :
                signed_credential = vc_signature.sign(credential, Secp256kr, "did:web:talao.co", Ed25519=Ed25519)
            elif did_selected == DID_TZ1 :
                didkit_options = {
                    "proofPurpose": "assertionMethod",
                    "verificationMethod": await didkit.key_to_verification_method('tz', Ed25519)
                    }
                signed_credential =  await didkit.issue_credential(
                json.dumps(credential),
                didkit_options.__str__().replace("'", '"'),
                Ed25519)
            else :
                signed_credential = vc_signature.sign(credential, Secp256kr, credential['issuer'])
        
        # send event to client agent to go forward
        data = json.dumps({
                            'id' : id,
                            'check' : 'success',
                            'scope' : '',
                            'signed_credential' : signed_credential
                            })
        red.publish('wallet_test', data)
        return jsonify(signed_credential)
        


def test_credentialOffer_back():
    return render_template("credential_offer_back.html")


# server event push for user agent EventSource
def offer_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('wallet_test')
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
        return render_template('credential_presentation.html', simulator='Verifier simulator with query types' )
							
    else :
        stream_id = str(uuid.uuid1())
        if request.form['query'] == 'DIDAuth' :
            pattern = DIDAuth
        else :
            pattern =  QueryBYExample
            pattern['query'][0]["credentialQuery"] = list()
            for i in['_1', '_2', '_3'] :          
                if request.form.get('trustedIssuer'+ i) or request.form.get('type' + i) or request.form.get('credentialSchema' + i) : 
                    MycredentialQuery = dict()
                    MycredentialQuery["required"] = True
                    if request.form.get('reason' + i) :
                        MycredentialQuery['reason'] = request.form['reason' + i] 
                    MycredentialQuery['example'] = dict()
                    if request.form.get('type' + i) :
                        MycredentialQuery['example']['type'] =  request.form['type' + i]
                    if request.form.get('trustedIssuer' + i) :
                        MycredentialQuery['example']['trustedIssuer'] = list()
                        for issuer in [key.replace(" ", "") for key in request.form['trustedIssuer' + i].split(',')] :
                            MycredentialQuery['example']['trustedIssuer'].append({"required" : True, "issuer" : issuer})   
                    pattern['query'][0]['credentialQuery'].append(MycredentialQuery)
        pattern['challenge'] = str(uuid.uuid1())
        pattern['domain'] = mode.server
        red.set(stream_id,  json.dumps(pattern))
        url = mode.server + 'sandbox/wallet_presentation/' + stream_id +'?issuer=' + DID_TZ2
        return render_template('credential_presentation_qr.html',
							url=url,
							stream_id=stream_id, 
                            pattern=json.dumps(pattern, indent=4),
                            simulator='Verifier simulator with query types')


async def test_presentationRequest_endpoint(stream_id, red):
    if request.method == 'GET':
        try : 
            my_pattern = json.loads(red.get(stream_id).decode())
        except :
            logging.error("red get id error")
            return jsonify('ko'), 500
        return jsonify(my_pattern)
    elif request.method == 'POST' :
        red.delete(stream_id)
        red.set(stream_id,  request.form['presentation'])
        event_data = json.dumps({"stream_id" : stream_id,
			                    "message" : "ok"})           
        red.publish('wallet_presentation', event_data)
        return jsonify("ok")


def presentation_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('wallet_presentation')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
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
         <form action="/sandbox/presentationRequest" method="GET" >
                    <button  type"submit" >QR code for Request</button></form>
                    <br>---------------------------------------------------<br>
        <pre class="whitespace-pre-wrap m-auto">""" + credential + """</pre>
        </body>
        </html>"""
    return render_template_string(html_string)


