from flask import jsonify, request, render_template, session, redirect, flash, Response
import json
from components import privatekey
import uuid
import secrets
from datetime import timedelta, datetime
import logging
logging.basicConfig(level=logging.INFO)
from signaturesuite import vc_signature
from flask_babel import _
import secrets
import os

OFFER_DELAY = timedelta(seconds= 10*60)
DID_WEB = 'did:web:talao.cp'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID = DID_TZ

IMAGE_PATH = 'static/directory/'
PATH = 'loyalty_cards/'

def init_app(app,red, mode) :
    app.add_url_rule('/loyaltycard',  view_func=loyaltycard, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/loyaltycard/qrcode',  view_func=loyaltycard_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode, 'red' : red})
    app.add_url_rule('/loyaltycard/offer/<id>',  view_func=loyaltycard_offer, methods = ['GET', 'POST'], defaults={'mode' : mode, 'red' : red})
    app.add_url_rule('/loyaltycard/stream',  view_func=loyaltycard_stream, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/loyaltycard/end',  view_func=loyaltycard_end, methods = ['GET', 'POST'])
    return

"""
loyaltycard : credential offer for a Member Card
VC is signed by Talao
https://www.onlinelabels.com/clip-art?tag=musical
"""

def loyaltycard(mode) :
    loyalty_list = [ json.load(open(PATH + filename, 'r')) for filename in os.listdir(PATH)]
    if request.method == 'GET' :
        caroussel = """
            <div class="carousel-item active">
                <img class="card-img-top " src='""" + IMAGE_PATH + loyalty_list[0]['image'] + """' >
                <div class="text-center"><h4 class="text-dark m-2" >""" + loyalty_list[0]['name'] + _(' Card') + """</h4></div>
                <div class="text-center"><h6 class="text-dark m-2" >""" + loyalty_list[0]['avantages'] + """</h6></div>
            </div>"""           
        for i in range(1, len(loyalty_list)) :
            caroussel +="""
                <div class="carousel-item">
                    <img class="card-img-top " src='""" + IMAGE_PATH + loyalty_list[i]['image'] + """' >
                    <div class="text-center"><h4 class="text-dark m-2">""" + loyalty_list[i]['name'] + _(' Card') + """</h4></div>
                    <div class="text-center"><h6 class="text-dark m-2" >""" + loyalty_list[i]['avantages'] + """</h6></div>
                </div>"""                    
        return render_template('loyaltycard/loyaltycard.html', caroussel=caroussel)
    if request.method == 'POST' :
        session['memberOf_name'] = loyalty_list[int(request.form['selected_issuer'])]['name']
        session['memberOf_logo'] = mode.ipfs_gateway + loyalty_list[int(request.form['selected_issuer'])].get('image', "")
        session['programName'] = loyalty_list[int(request.form['selected_issuer'])].get('programName', "")
    return redirect ('loyaltycard/qrcode')


def loyaltycard_qrcode(red, mode) :
    if request.method == 'GET' :
        id = str(uuid.uuid1())
        url = mode.server + "loyaltycard/offer/" + id 
        data = {'memberOf_name' : session['memberOf_name'],
                'programName' : session['programName'],
                'memberOf_logo' : session['memberOf_logo']
                }
        red.set(id,  json.dumps(data))
        logging.info('url = %s', url)
        return render_template('loyaltycard/loyaltycard_qrcode.html', url=url, id=id)
   

def loyaltycard_offer(id, red, mode):
    """ Endpoint for wallet
        Offer with profil sent by wallet
    """
    data = json.loads(red.get(id).decode())
    credential = json.loads(open('./verifiable_credentials/LoyaltyCard.jsonld', 'r').read())
    credential["issuer"] = DID
    credential['issuanceDate'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    credential['credentialSubject']['memberOf'] = { "name" : data['memberOf_name'],
                                                    "logo" : data['memberOf_logo']}
    if data['programName'] :
        credential['credentialSubject']['programName'] = data['programName']
    credential['credentialSubject']['expires'] = (datetime.now() + timedelta(days= 365)).replace(microsecond=0).isoformat() + "Z"
    if request.method == 'GET': 
        # make an offer  
        credential_offer = {
            "type": "CredentialOffer",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z"
        }
        return jsonify(credential_offer)
    elif request.method == 'POST': 
        red.delete(id)   
        # sign credential
        credential['id'] = "urn:uuid:" + str(uuid.uuid1())
        credential['credentialSubject']['id'] = request.form['subject_id']
        profil = request.form.get('profil', {})
        if profil.get('givenName') :
            credential['credentialSubject']['givenName'] = profil['givenName']
        if profil.get('familyName') :
            credential['credentialSubject']['familyName'] = profil['familyName']
        if profil.get('address') :
            credential['credentialSubject']['address'] = profil['address']
        if profil.get('email') :
            credential['credentialSubject']['email'] = profil['email']
        if profil.get('telephone') :
            credential['credentialSubject']['telephone'] = profil['telephone']
        pvk = privatekey.get_key(mode.owner_talao, 'private_key', mode)
        signed_credential = vc_signature.sign(credential, pvk, DID)
        if not signed_credential :
            logging.error('credential signature failed')
            data = json.dumps({"url_id" : id, "check" : "failed"})
            red.publish('credible', data)
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
        data = json.dumps({"url_id" : id, "check" : "success"})
        red.publish('loyaltycard', data)
        return jsonify(signed_credential)
 

def loyaltycard_end() :
    if request.args['followup'] == "success" :
        message = _('Great ! you have now a new Loyalty Card.')
    elif request.args['followup'] == 'expired' :
        message = _('Delay expired.')
    return render_template('loyaltycard/loyaltycard_end.html', message=message)


# server event push 
def event_stream(red):
    pubsub = red.pubsub()
    pubsub.subscribe('loyaltycard')
    for message in pubsub.listen():
        if message['type']=='message':
            yield 'data: %s\n\n' % message['data'].decode()


def loyaltycard_stream(red):
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)
