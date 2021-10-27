from flask import jsonify, request, render_template, Response, render_template_string, redirect, url_for
import json
from datetime import timedelta, datetime
from signaturesuite import vc_signature
from components import privatekey
from github import Github
import base64
import uuid
import logging
from flask_babel import Babel, _

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


DID_WEB = 'did:web:talao.co'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ2 = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY = 'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'

did_selected = DID_ETHR
list = dict()

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



def init_app(app,red, mode) :

    app.add_url_rule('/credentials/status/3',  view_func=credentiallist, methods = ['GET'])
    app.add_url_rule('/wallet/test/revoked_qrcode',  view_func=revoked_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/wallet/test/revoked_endpoint/<id>',  view_func=revoked_endpoint, methods = ['GET', 'POST'],defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/wallet/test/revoked_stream',  view_func=revoked_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/revoked_back',  view_func=test_revoked_back, methods = ['GET', 'POST'])

    global PVK
    PVK = privatekey.get_key(mode.owner_talao, 'private_key', mode)
    sign_credentiallist(mode)
    logging.info('credential list signed and published')
    print("mode.server = ", mode.server)
    return

def credentiallist() :
    global list
    return jsonify(list)


def sign_credentiallist (mode) :
    # sign with DID_ETHR
    global list
    unsigned_list = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://w3id.org/vc-revocation-list-2020/v1"
        ],
        "id":  mode.server + "credentials/status/3",
        "issuanceDate" : datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "type": [
            "VerifiableCredential",
            "RevocationList2020Credential"
        ],
        "credentialSubject": {
            "id" : "urn:uuid:" + str(uuid.uuid1()),
            #"id": mode.server + "credentials/status/3",
            "encodedList": "H4sIAAAAAAAAA-3OMQ0AAAgDsOHfNB72EJJWQRMAAAAAAIDWXAcAAAAAAIDHFrc4zDzUMAAA",
            "type": "RevocationList2020"
        },
        "issuer": did_selected,
    }
    list = json.loads(vc_signature.sign(unsigned_list, PVK, did_selected))



def revoked_qrcode(mode) :
    if request.method == 'GET' :
        id = str(uuid.uuid1())
        url = mode.server + "wallet/test/revoked_endpoint/" + id 
        #red.set(id,  session['email'])
        logging.info('url = %s', url)
        return render_template('wallet/test/revoked_qrcode.html', url=url, id=id)



def revoked_endpoint(id, red, mode) :
    credential = json.loads(open('./verifiable_credentials/ResidentCard.jsonld', 'r').read())
    credential["issuer"] = DID_ETHR
    credential['id'] = "urn:uuid:..."
    credential['credentialSubject']['id'] = "did:..."
    credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    credential['expirationDate'] =  (datetime.now() + timedelta(days= 365)).isoformat() + "Z"
    
    credential["credentialStatus"] ={
        #"id": mode.server + "credentials/status/3" + "#50000",
        "id" : "urn:uuid:" + str(uuid.uuid1()),
        "type": "RevocationList2020Status",
        "revocationListIndex": "50000",
        "revocationListCredential": mode.server + "credentials/status/3"
    }
    
    if request.method == 'GET': 
        # make an offer  
        credential_offer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
            "display" : {"backgroundColor" : "ffffff"},
        }
        return jsonify(credential_offer)
    elif request.method == 'POST': 
        #red.delete(id)   
        # sign credential
        credential['id'] = "urn:uuid:" + str(uuid.uuid1())
        credential['credentialSubject']['id'] = request.form.get('subject_id', 'unknown DID')
        pvk = privatekey.get_key(mode.owner_talao, 'private_key', mode)
        print('pvk = ', pvk)
        signed_credential = vc_signature.sign(credential, pvk, did_selected)
        if not signed_credential :
            message = 'credential signature failed'
            logging.error(message)
            data = json.dumps({"url_id" : id, "check" : "failed", "message" : message})
            red.publish('revoked', data)
            return jsonify({})
         # store signed credential on server
        try :
            filename = credential['id'] + '.jsonld'
            path = "./signed_credentials/"
            with open(path + filename, 'w') as outfile :
                json.dump(json.loads(signed_credential), outfile, indent=4, ensure_ascii=False)
        except :
            logging.error('signed credential not stored')
        # send event to client agent to go forward
        data = json.dumps({"url_id" : id, "check" : "success", "message" : "ok"})
        red.publish('revoked', data)
        return jsonify(signed_credential)


def test_revoked_back():
    html_string = """
        <!DOCTYPE html>
        <html>
        
        <body class="h-screen w-screen flex ">
        <p></p>
        <h2>Verifiable Credential has been signed and transfered to wallet"</h2<
        <br><br><br>
        <form action="/wallet/test/credentialOffer" method="GET" >
                    <button  type"submit" >Back</button></form>
        </body>
        </html>"""
    return render_template_string(html_string)


# server event push for javascript client event
def revoked_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('revoked')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()  
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)
