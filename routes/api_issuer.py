"""
def get_version() -> str: ...
def generate_ed25519_key() -> str: ...
def key_to_did(method_pattern: str, jwk: str) -> str: ...
async def key_to_verification_method(method_pattern: str, jwk: str) -> str: ...
async def issue_credential(credential: str, proof_options: str, key: str) -> str: ...
async def verify_credential(credential: str, proof_options: str) -> str: ...
async def issue_presentation(presentation: str, proof_options: str, key: str) -> str: ...
async def verify_presentation(presentation: str, proof_options: str) -> str: ...
async def resolve_did(did: str, input_metadata: str) -> str: ...
async def dereference_did_url(did_url: str, input_metadata: str) -> str: ...
async def did_auth(did: str, options: str, key: str) -> str: ...
"""

from flask import jsonify, request, render_template, Response, redirect, session
import json
from datetime import timedelta, datetime
import uuid
import didkit
import logging
from urllib.parse import urlencode
import requests
import db_api
import ebsi
import base64
import issuer_activity_db_api
import pyotp

logging.basicConfig(level=logging.INFO)
OFFER_DELAY = timedelta(seconds= 10*60)


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/issuer/<issuer_id>',  view_func=issuer_landing_page, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer_endpoint/<issuer_id>/<stream_id>',  view_func=issuer_endpoint, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/op/issuer_stream',  view_func=issuer_stream, methods = ['GET', 'POST'], defaults={'red' :red})
    app.add_url_rule('/sandbox/op/issuer_followup',  view_func=issuer_followup, methods = ['GET'])
    app.add_url_rule('/sandbox/op/login_password/<issuer_id>',  view_func=login_password, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/secret/<issuer_id>',  view_func=secret, methods = ['GET', 'POST'])
    return


def login_password(issuer_id) :
    if request.method == 'GET' :
        try :
            issuer_data = json.loads(db_api.read_issuer(issuer_id))
        except :
            logging.error('issuer id not found')
            return render_template('op_issuer_removed.html')
        return render_template ('login_password.html',
            issuer_id=issuer_id,
            page_title=issuer_data['page_title'],
            page_subtitle=issuer_data['page_subtitle'],
            page_description=issuer_data['page_description'],
            title=issuer_data['title'],
            qrcode_message=issuer_data['qrcode_message'],
            landing_page_url=issuer_data['landing_page_url'],
            privacy_url=issuer_data['privacy_url'],
            terms_url=issuer_data['terms_url'],
            mobile_message=issuer_data['mobile_message'],
            page_background_color = issuer_data['page_background_color'],
            page_text_color = issuer_data['page_text_color'],
            qrcode_background_color = issuer_data['qrcode_background_color'])
    if request.method == 'POST' :
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        session['login_password'] = True
        return redirect('/sandbox/op/issuer/' + issuer_id)

# secret and TOTP case
def secret(issuer_id) :
    try :
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
    except :
        logging.error('issuer id not found')
        return render_template('op_issuer_removed.html')
    if request.method == 'GET' :
        if issuer_data['credential_requested'] == 'totp' and request.args.get('totp') :
            totp = pyotp.TOTP(issuer_data.get('secret'), interval=int(issuer_data.get("totp_interval", "30")))
            if  totp.verify(request.args['totp']) :
                session['login_secret'] = True
                return redirect('/sandbox/op/issuer/' + issuer_id)
            else :
                logging.warning('TOTP secret is incorrect')
                session.clear()
                return render_template('secret_access_denied.html', next=issuer_data['callback'])
        return render_template ('secret.html',
            issuer_id=issuer_id,
            page_title=issuer_data['page_title'],
            page_subtitle=issuer_data['page_subtitle'],
            page_description=issuer_data['page_description'],
            title=issuer_data['title'],
            qrcode_message=issuer_data['qrcode_message'],
            landing_page_url=issuer_data['landing_page_url'],
            privacy_url=issuer_data['privacy_url'],
            terms_url=issuer_data['terms_url'],
            mobile_message=issuer_data['mobile_message'],
            page_background_color = issuer_data['page_background_color'],
            page_text_color = issuer_data['page_text_color'],
            qrcode_background_color = issuer_data['qrcode_background_color'])
    if request.method == 'POST' :
        if issuer_data['credential_requested'] == 'totp' :
            totp = pyotp.TOTP(issuer_data.get('secret', "base32secret3232"), interval=int(issuer_data.get("totp_interval", "30")))
            if  totp.verify(request.form['secret']) :
                session['login_secret'] = True
                logging.info('TOTP secret is correct')
                return redirect('/sandbox/op/issuer/' + issuer_id)
            logging.warning('secret is incorrect')
            session.clear()
            return render_template('secret_access_denied.html', next=issuer_data['callback'])
        else :
            if  request.form['secret'] == issuer_data.get('secret') :
                session['login_secret'] = True
                return redirect('/sandbox/op/issuer/' + issuer_id)
            logging.warning('secret is incorrect')
            session.clear()
            return render_template('secret_access_denied.html', next=issuer_data['callback'])
           

def issuer_landing_page(issuer_id, red, mode) :
    session['is_connected'] = True
    try :
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
    except :
        logging.error('issuer id not found')
        return render_template('op_issuer_removed.html')

    if issuer_data['credential_requested'] == "login" and not session.get('login_password') :
        session['issuer_id'] = issuer_id
        return redirect('/sandbox/op/login_password/' + issuer_id)
    
    if issuer_data['credential_requested'] in ["secret", "totp"] and not session.get('login_secret') :
        session['issuer_id'] = issuer_id
        if issuer_data['credential_requested'] == "totp" and request.args.get('totp') :
            return redirect('/sandbox/op/secret/' + issuer_id + "?totp=" + request.args['totp'])
        return redirect('/sandbox/op/secret/' + issuer_id )
    
    credential = json.load(open('./verifiable_credentials/' + issuer_data['credential_to_issue'] + '.jsonld'))
    credential['id'] = "urn:uuid:" + str(uuid.uuid1())
    credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
    credential["issuer"] ="did:ebsi:"
    credential["credentialSubject"]['id'] ="did:example:xxxxx:"
    print("credential = ", credential)
    
    try :
        credential_manifest = json.load(open('./credential_manifest/' + issuer_data['credential_to_issue'] + '_credential_manifest.json'))
    except :
        logging.error('credential manifest not found or error %s', issuer_data['credential_to_issue'])
        return render_template('op_issuer_removed.html')
    
    if issuer_data['method'] == "ebsi" :
        issuer_did =  issuer_data['did_ebsi']
    elif issuer_data['method'] == "relay" :
        issuer_did = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
    else : 
        issuer_did = didkit.key_to_did(issuer_data['method'], issuer_data['jwk'])
    
    # update credential manifest
    credential_manifest['id'] = str(uuid.uuid1())
    credential_manifest['output_descriptors'][0]['id'] = str(uuid.uuid1())
    credential_manifest['output_descriptors'][0]['schema'] = "https://github.com/TalaoDAO/wallet-tools/blob/main/test/CredentialOffer2/" + issuer_data['credential_to_issue'] + '.jsonld'
    credential_manifest['output_descriptors'][0]['display']['title']['fallback'] = issuer_data['card_title']
    credential_manifest['output_descriptors'][0]['display']['subtitle']['fallback'] = issuer_data['card_subtitle']
    credential_manifest['output_descriptors'][0]['display']['description']['fallback'] = issuer_data['card_description']
    credential_manifest['output_descriptors'][0]['styles'] = {
            'background' : {'color' : issuer_data['card_background_color']},
            'text' : { 'color' : issuer_data['card_text_color']}}
    
    credential_manifest['issuer']['id'] = issuer_did
    credential_manifest['issuer']['name'] = issuer_data['company_name']
    if issuer_data['credential_requested'] in ["DID", "login", "secret", "totp"] and issuer_data['credential_requested_2'] in ["DID", "login", "secret", "totp"] : # No credential 2 requested to issue 
        credential_manifest['presentation_definition'] = dict()
    else :
        credential_manifest['presentation_definition'] = {"id": str(uuid.uuid1()), "input_descriptors": list()}    
        if issuer_data['credential_requested'] not in ["DID", "login", "secret", "totp"] :
            input_descriptor = {"id": str(uuid.uuid1()),
                        "purpose" : issuer_data['reason'],
                        "constraints": {
                            "fields": [
                                {"path": ["$.type"],
                                "filter": {"type": "string",
                                            "pattern": issuer_data['credential_requested']}
                                }]}}
            credential_manifest['presentation_definition']['input_descriptors'].append(input_descriptor)
        
        if issuer_data.get('credential_requested_2', 'DID') not in ["DID", "login", "secret", "totp"] :  
            input_descriptor_2 = {"id": str(uuid.uuid1()),
                        "purpose" : issuer_data.get('reason_2',""),
                        "constraints": {
                            "fields": [
                                {"path": ["$.type"],
                                "filter": {"type": "string",
                                            "pattern": issuer_data['credential_requested_2']}
                                }]}}
            credential_manifest['presentation_definition']['input_descriptors'].append(input_descriptor_2)

        if issuer_data.get('credential_requested_3', 'DID') not in ["DID", "login", "secret", "totp"] :  
            input_descriptor_3 = {"id": str(uuid.uuid1()),
                        "purpose" : issuer_data.get('reason_3',""),
                        "constraints": {
                            "fields": [
                                {"path": ["$.type"],
                                "filter": {"type": "string",
                                            "pattern": issuer_data['credential_requested_3']}
                                }]}}
            credential_manifest['presentation_definition']['input_descriptors'].append(input_descriptor_3)

        if issuer_data.get('credential_requested_4', 'DID') not in ["DID", "login", "secret", "totp"] :  
            input_descriptor_4 = {"id": str(uuid.uuid1()),
                        "purpose" : issuer_data.get('reason_4',""),
                        "constraints": {
                            "fields": [
                                {"path": ["$.type"],
                                "filter": {"type": "string",
                                            "pattern": issuer_data['credential_requested_4']}
                                }]}}
            credential_manifest['presentation_definition']['input_descriptors'].append(input_descriptor_4)

    logging.info("credential manifest = %s", credential_manifest)
    if not request.args.get('id') :
        logging.warning("no id passed by application")

    credentialOffer = {
        "id" : request.args.get('id'),
        "type": "CredentialOffer",
        "challenge" : str(uuid.uuid1()),
        "domain" : "https://altme.io",
        "credentialPreview": credential,
        "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
        "credential_manifest" : credential_manifest
    }   
    #logging.info('credential offer = %s', credentialOffer)
    stream_id = str(uuid.uuid1())
    # TODO
    issuer_did = "did:tz:tz1NyjrTUNxDpPaqNZ84ipGELAcTWYg6s5Du"
    url = mode.server + "sandbox/op/issuer_endpoint/" + issuer_id + '/' + stream_id + '?issuer=' + issuer_did 
    deeplink_altme = mode.altme_deeplink + 'app/download?' + urlencode({'uri' : url })
    red.setex(stream_id, 180, json.dumps(credentialOffer))
    if issuer_data['credential_requested'] == "login" :
        red.setex(stream_id + "_login", 180, json.dumps({"username" : session['username'],
                                                         "password" : session["password"]
                                                         } ))
    if not issuer_data.get('landing_page_style') :
        qrcode_page = "op_issuer_qrcode_2.html"
    else : 
        qrcode_page = issuer_data.get('landing_page_style')
  
    return render_template(qrcode_page,
                                url=url,
                                deeplink_altme=deeplink_altme,
                                stream_id=stream_id,
                                issuer_id=issuer_id,
                                page_title=issuer_data['page_title'],
                                page_subtitle=issuer_data['page_subtitle'],
                                page_description=issuer_data['page_description'],
                                title=issuer_data['title'],
                                qrcode_message=issuer_data['qrcode_message'],
                                landing_page_url=issuer_data['landing_page_url'],
                                privacy_url=issuer_data['privacy_url'],
                                terms_url=issuer_data['terms_url'],
                                mobile_message=issuer_data['mobile_message'],
                                page_background_color = issuer_data['page_background_color'],
                                page_text_color = issuer_data['page_text_color'],
                                qrcode_background_color = issuer_data['qrcode_background_color'],
                                )


async def issuer_endpoint(issuer_id, stream_id, red):
    print('enter')
    try : 
        credentialOffer = red.get(stream_id).decode()
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
    except :
        logging.error("red.get(id) errorn offer expired")
        data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Offer expired"})
        red.publish('op_issuer', data)
        return jsonify("Unauthorized"),400 
    
    # wallet GET
    if request.method == 'GET':
        return jsonify(credentialOffer)
                        
    # wallet POST
    if request.method == 'POST':
        if not issuer_data :
            logging.error("Unhauthorized")
            data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Offer expired"})
            red.publish('op_issuer', data)
            return jsonify("Unauthorized"),400  
     
        # send data to webhook
        data_received = dict()
        if issuer_data.get('standalone', None) == 'on' :
            headers = {
                    "key" : issuer_data['client_secret'],
                    "Content-Type": "application/json" 
                    }       
            url = issuer_data['webhook']
            print('id retour wallet = ', request.form.get('id'))
            payload = { 'event' : 'ISSUANCE',
                    'vp': json.loads(request.form['presentation']),
                    "id": request.form.get('id')
                    }
            if issuer_data['credential_requested'] == 'login' :
                user_pass = json.loads(red.get(stream_id + "_login").decode())
                usrPass = (user_pass['username'] + ':' + user_pass['password']).encode()
                b64Val = base64.b64encode(usrPass) 
                headers["Authorization"] = "Basic " + b64Val.decode()

            r = requests.post(url,  data=json.dumps(payload), headers=headers)
            if not 199<r.status_code<300 :
                logging.error('issuer failed to call application, status code = %s', r.status_code)
                data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Issuer failed to call application"})
                red.publish('op_issuer', data)
                return jsonify("application error"),500    
            logging.info('status code ok')
        
            try :
                data_received = r.json()
            except :
                logging.error('aplication data are not json')
                data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : "Application data received are not json format"})
                red.publish('op_issuer', data)
                return jsonify("application error"),500

            # credential is signed by external issuer
            if issuer_data['method'] == "relay" :
                # send event to front to go forward callback
                data = json.dumps({'stream_id' : stream_id,"result" : True})
                red.publish('op_issuer', data)
                logging.info('credential signed by external signer')
                return jsonify(data_received)

        # build credential   
        credential =  json.loads(credentialOffer)['credentialPreview']

        # extract data sent by application and merge them with verifiable credential data
        if data_received and issuer_data.get('standalone', None) == 'on' :
            credential["credentialSubject"] = data_received
            logging.info("Data received from application added to credential")

        credential['id'] = "urn:uuid:" + str(uuid.uuid4())
        credential['credentialSubject']['id'] = request.form['subject_id']
        credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
        duration = issuer_data.get('credential_duration', "365")
        credential['expirationDate'] =  (datetime.now().replace(microsecond=0) + timedelta(days= int(duration))).isoformat() + "Z"
        
        if issuer_data['credential_to_issue'] == 'Pass' :
            credential['credentialSubject']['issuedBy']['name'] = issuer_data.get('company_name', 'Unknown')
            credential['credentialSubject']['issuedBy']['issuerId'] = issuer_id
       
        # sign credential
        if issuer_data['method'] == "ebsi" :
            logging.warning("EBSI issuer")
            credential["issuer"] = issuer_data['did_ebsi']
            signed_credential = ebsi.lp_sign(credential, issuer_data['jwk'], issuer_data['did_ebsi'])
            logging.info("credential signed by EBSI")
        else :
            credential["issuer"] = didkit.key_to_did(issuer_data['method'], issuer_data['jwk'])  
            didkit_options = {
                "proofPurpose": "assertionMethod",
                "verificationMethod": await didkit.key_to_verification_method(issuer_data['method'], issuer_data['jwk'])
            }
            try :
                signed_credential =  await didkit.issue_credential(
                json.dumps(credential),
                didkit_options.__str__().replace("'", '"'),
                issuer_data['jwk']
                )
                logging.info("credential signed by %s", credential["issuer"])
            except :
                message = 'Signature failed, application failed to return correct data'
                logging.error(message)
                logging.error("credential to sign = %s", credential)
                data = json.dumps({'stream_id' : stream_id,
                            "result" : False,
                            "message" : message})
                red.publish('op_issuer', data)
                return jsonify("server error, signature failed"),500
                
            logging.info('signature ok')
       
        # transfer credential signed and credential recieved to application
        if issuer_data.get('standalone', None) == 'on' :
            headers = {
                    "key" : issuer_data['client_secret'],
                    "Content-Type": "application/json" 
                    }      
            url = issuer_data['webhook']
            payload = { 'event' : 'SIGNED_CREDENTIAL',
                    'vc': json.loads(signed_credential),
                    'vp' : json.loads(request.form['presentation']),
                    "id": request.form.get('id')
                    }
            r = requests.post(url,  data=json.dumps(payload), headers=headers)
            if not 199<r.status_code<300 :
                logging.error('issuer failed to send signed credential to application, status code = %s', r.status_code)
            else :
                logging.info('signed credential sent to application')
        
        # send event to front to go forward callback and send credential to wallet
        data = json.dumps({'stream_id' : stream_id,"result" : True})
        red.publish('op_issuer', data)
        
        # record activity
        activity = {"presented" : datetime.now().replace(microsecond=0).isoformat() + "Z",
                "wallet_did" : request.form['subject_id'],
                "vp" : json.loads(request.form['presentation'])
        }
        issuer_activity_db_api.create(issuer_id, activity) 
        return jsonify(signed_credential)
        

def issuer_followup():  
    if not session.get('is_connected') :
        logging.error('user is not connectd')
        return render_template('op_issuer_removed.html',next = issuer_data['issuer_landing_page'])
    session.clear()
    issuer_id = request.args.get('issuer_id')
    issuer_data = json.loads(db_api.read_issuer(issuer_id))
    if request.args.get('message') :
        return render_template('op_issuer_failed.html', next = issuer_data['issuer_landing_page'])
    try :
        issuer_data = json.loads(db_api.read_issuer(issuer_id))
    except :
        return render_template('op_issuer_removed.html',next = issuer_data['issuer_landing_page'])
    return redirect (issuer_data['callback'])
    
    
# server event push for user agent EventSource
def issuer_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('op_issuer')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()  
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)



