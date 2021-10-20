from flask import jsonify, request, render_template, Response, render_template_string, redirect, url_for
import json
from datetime import timedelta, datetime
from signaturesuite import vc_signature
from components import privatekey
from github import Github
import base64
import uuid
import logging

logging.basicConfig(level=logging.INFO)

OFFER_DELAY = timedelta(seconds= 10*60)
TEST_REPO = "TalaoDAO/wallet-tools"
REGISTRY_REPO = "TalaoDAO/context"

try :
    RSA = open("/home/admin/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
    P256 = json.dumps(json.load(open("/home/admin/Talao/keys.json", "r"))['talaonet'].get('talao_P256_private_key'))
    Ed25519 = json.dumps(json.load(open("/home/admin/Talao/keys.json", "r"))['talaonet'].get('talao_Ed25519_private_key'))

except :
    RSA = open("/home/thierry/Talao/RSA_key/talaonet/0x3B1dcb1A80476875780b67b239e556B42614C7f9_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt", 'r').read()
    P256 = json.dumps(json.load(open("/home/thierry/Talao/keys.json", "r"))['talaonet'].get('talao_P256_private_key'))
    Ed25519 = json.dumps(json.load(open("/home/thierry/Talao/keys.json", "r"))['talaonet'].get('talao_Ed25519_private_key'))


did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'


# officiel did:ethr:0xE474E9a6DFD6D8A3D60A36C2aBC428Bf54d2B1E8
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
    
path = "test/CredentialOffer"

def dir_list_calculate(path) :
    dir_list=list()
    contents = test_repo.get_contents(path)
    for content_file in contents :
        if content_file.name.split('.')[1] =='jsonld' :
            dir_list.append(content_file.name)
    return dir_list




def init_app(app,red, mode) :
    app.add_url_rule('/wallet/test/create_residentcard',  view_func=test_create_residentcard, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/wallet/test/residentcard_credentialOffer_back',  view_func=test_residentcard_credentialOffer_back, methods = ['GET'])
    app.add_url_rule('/wallet/test/wallet_credential_residentcard/<id>',  view_func=test_credentialOffer_residentcard_endpoint, methods = ['GET', 'POST'], defaults={ 'red' :red})
    app.add_url_rule('/wallet/test/residentcard_offer_stream',  view_func=residentcard_offer_stream, methods = ['GET', 'POST'], defaults={'red' :red})



    global PVK, test_repo, registry_repo
    PVK = privatekey.get_key(mode.owner_talao, 'private_key', mode)
    g = Github(mode.github)
    test_repo = g.get_repo(TEST_REPO)
    registry_repo = g.get_repo(REGISTRY_REPO)
    return




######################### Credential Offer ###########

def test_create_residentcard(red, mode) :
    global did_selected
    global path
    if request.method == 'GET' :   
        return render_template("./wallet/test/create_residentcard.html") 
    else :
      
        did_selected = request.form['did_select']
        if did_selected.split(':')[1] == 'web' :
            did_issuer = 'did:web:talao.co'
        else :
            did_issuer = did_selected
        credential = json.loads(open("./verifiable_credentials/ResidentCard_demo.jsonld", 'r').read())

        credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        credential['id'] =  "urn:uuid:" + str(uuid.uuid1())
        credential['credentialSubject']['id'] = "did:..."
        credential['issuer'] = did_issuer
        credential['credentialSubject']['address'] = request.form.get("address") 
        credential['credentialSubject']['givenName'] = request.form.get("givenName") 
        credential['credentialSubject']['familyName'] = request.form.get("familyName") 
        credential['credentialSubject']["birthDate"] = request.form['birthDate']
        credential['credentialSubject']["gender"] = request.form['gender']
        credential['credentialSubject']["email"] = request.form['email']
        credential['credentialSubject']["maritalStatus"] = request.form['maritalStatus']
        credential['credentialSubject']["birthPlace"] = request.form['birthPlace']
        credential['credentialSubject']["nationality"] = request.form['nationality']

        credentialOffer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z"
        }
        url = mode.server + "wallet/test/wallet_credential_residentcard/" + credential['id']+'?issuer=' + did_issuer
        red.set(credential['id'], json.dumps(credentialOffer))
        type = credentialOffer['credentialPreview']['type'][1]
        return render_template('wallet/test/credential_residentcard_offer_qr.html',
                                url=url,
                                id=credential['id'],
                                credentialOffer=json.dumps(credentialOffer, indent=4),
                                type = type + " - " + translate(credential),
                                )


def test_credentialOffer_residentcard_endpoint(id, red):
    global did_selected
    try : 
        credentialOffer = json.loads(red.get(id).decode())
    except :
        logging.error("red get id error")
        return ('ko')
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

        print("unsigned credential = ", credential)
        # to keep the possibility to use an RSA key with did:web
        if did_selected == 'did:web:talao.co#key-2' :
            signed_credential = vc_signature.sign(credential, PVK, "did:web:talao.co", rsa=RSA)
        elif did_selected == 'did:web:talao.co#key-3' :
            signed_credential = vc_signature.sign(credential, PVK, "did:web:talao.co", P256=P256)
        elif did_selected == 'did:web:talao.co#key-4' :
            signed_credential = vc_signature.sign(credential, PVK, "did:web:talao.co", Ed25519=Ed25519)
        else :
            signed_credential = vc_signature.sign(credential, PVK, did_selected)
        
        # send event to client agent to go forward
        data = json.dumps({
                            'id' : id,
                            'check' : 'success',
                            'scope' : '',
                            'signed_credential' : signed_credential
                            })
        red.publish('create_residentcard', data)
        return jsonify(signed_credential)


def test_residentcard_credentialOffer_back():
    html_string = """
        <!DOCTYPE html>
        <html>
        <body class="h-screen w-screen flex">
        <h2>Verifiable Credential has been signed and transferd to wallet"</h2<
        <br><br><br>
        <form action="/wallet/test/credentialOffer" method="GET" >
                    <button  type"submit" >Back</button></form>
        </body>
        </html>"""
    return render_template_string(html_string)


# server event push for user agent EventSource
def residentcard_offer_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('create_residentcard')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()  
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)



