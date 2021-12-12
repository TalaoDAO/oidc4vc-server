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

DID_KEY = 'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'

did_selected = DID_KEY
list = dict()
status = "Active"
PVK=""

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
    app.add_url_rule('/credentials/status/3',  view_func=credentiallist, methods = ['GET', 'POST'])

    app.add_url_rule('/wallet/test/revoked_qrcode',  view_func=revoked_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/wallet/test/revoked_endpoint/<id>',  view_func=revoked_endpoint, methods = ['GET', 'POST'],defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/wallet/test/revoked_stream',  view_func=revoked_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/wallet/test/revoked_back',  view_func=test_revoked_back, methods = ['GET', 'POST'])
    app.add_url_rule('/wallet/test/revoke',  view_func=revoke, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/wallet/test/unrevoke',  view_func=unrevoke, methods = ['GET', 'POST'], defaults={'mode' : mode})

    app.add_url_rule('/wallet/playground',  view_func=playground, methods = ['GET', 'POST'])
    app.add_url_rule('/playground',  view_func=playground, methods = ['GET', 'POST'])

    global PVK
    PVK = privatekey.get_key(mode.owner_talao, 'private_key', mode)
    logging.info('credential list signed and published')
    return


def playground() :
    global status
    print('status = ', status)
    return render_template("./wallet/test/playground.html", status=status)


def credentiallist() :
    credential_list=json.load(open('credential_list_signed.json', 'r'))
    return jsonify(credential_list)


def revoke(mode):
    credential_revoke(mode)
    return render_template("./wallet/test/playground.html", status=status)


def unrevoke(mode):
    credential_unrevoke(mode)
    return render_template("./wallet/test/playground.html", status=status)


def credential_revoke (mode) :
    global list, status
    if status == "Revoked" :
        return True
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
            "encodedList": "H4sIAAAAAAAAA-3OMQ0AAAgDsOHfNB72EJJWQRMAAAAAAIDWXAcAAAAAAIDHFrc4zDzUMAAA",
            "type": "RevocationList2020"
        },
        "issuer": did_selected,
    }
    status = 'Revoked'
    logging.info("Credential is now Revoked")
    with open('credential_list_signed.json', 'w') as outfile :
       outfile.write(vc_signature.sign(unsigned_list, PVK, did_selected))
    return True


def credential_unrevoke(mode) :
    global list, status
    if status == "Active" :
        return True
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
            "encodedList": "H4sIAAAAAAAAA-3BMQEAAADCoPVPbQsvoAAAAAAAAAAAAAAAAP4GcwM92tQwAAA",
            "type": "RevocationList2020"
        },
        "issuer": did_selected,
    }
    status = 'Active'
    logging.info("Credential is now Revoked")
    with open('credential_list_signed.json', 'w') as outfile :
       outfile.write(vc_signature.sign(unsigned_list, PVK, did_selected))
    return True


def revoked_qrcode(mode) :
    if request.method == 'GET' :
        id = str(uuid.uuid1())
        url = mode.server + "wallet/test/revoked_endpoint/" + id + '?issuer=' + did_selected
        logging.info('url = %s', url)
        return render_template('wallet/test/revoked_qrcode.html', url=url, id=id)


def revoked_endpoint(id, red, mode) :
    credential = json.loads(open('./verifiable_credentials/ResidentCard.jsonld', 'r').read())
    credential["issuer"] = did_selected
    credential['id'] = "urn:uuid:..."
    credential['credentialSubject']['id'] = "did:..."
    credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    credential['expirationDate'] =  (datetime.now() + timedelta(days= 365)).isoformat() + "Z"
    credential["credentialStatus"] ={
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
        signed_credential = vc_signature.sign(credential, pvk, did_selected)
        if not signed_credential :
            message = 'credential signature failed'
            logging.error(message)
            data = json.dumps({"url_id" : id, "check" : "failed", "message" : message})
            red.publish('revoked', data)
            return jsonify({'server error'}), 500
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
        credential_unrevoke(mode)
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

