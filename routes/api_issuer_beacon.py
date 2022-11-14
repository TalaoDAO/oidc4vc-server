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

from flask import jsonify, request, render_template
import json
from datetime import timedelta, datetime
import uuid
import didkit
import logging
import requests
import db_api
import ebsi
import beacon_activity_db_api

logging.basicConfig(level=logging.INFO)
OFFER_DELAY = timedelta(seconds= 10*60)
DID_issuer = "did:tz:tz1NyjrTUNxDpPaqNZ84ipGELAcTWYg6s5Du"


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/beacon/<issuer_id>',  view_func=beacon_landing, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    return


def update_credential_manifest(reason, credential_requested, credential_manifest) :
    input_descriptor = {"id": str(uuid.uuid1()),
                        "purpose" : reason,
                        "constraints": {
                            "fields": [
                                {"path": ["$.type"],
                                "filter": {"type": "string",
                                            "pattern": credential_requested}
                                }]}}
    credential_manifest['presentation_definition']['input_descriptors'].append(input_descriptor)
    return credential_manifest


def update_credntial_manifest_all_address(reason, credential_manifest) :
    input_descriptor = {"id": str(uuid.uuid1()),
                        "purpose" : reason,
                        "constraints": {
                            "fields": [
                                {"path": ["$.credentialSubject.associatedAddress"]}
                                ]}}
    credential_manifest['presentation_definition']['input_descriptors'].append(input_descriptor)
    return credential_manifest


async def beacon_landing(issuer_id, red, mode) :
    try :
        issuer_data = json.loads(db_api.read_beacon(issuer_id))
    except :
        logging.error('issuer id not found')
        return jsonify("issuer not found"), 404

    if request.method == 'GET':
        credential = json.load(open('./verifiable_credentials/' + issuer_data['credential_to_issue'] + '.jsonld'))
        credential['id'] = "urn:uuid:" + str(uuid.uuid1())
        credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
        credential["issuer"] ="did:ebsi:"
        credential["credentialSubject"]['id'] ="did:example:xxxxx:"    
        try :
            credential_manifest = json.load(open('./credential_manifest/' + issuer_data['credential_to_issue'] + '_credential_manifest.json'))
        except :
            logging.error('credential manifest not found or error %s', issuer_data['credential_to_issue'] + '_credential_manifest.json')
            return render_template('op_issuer_removed.html')
        if issuer_data['method'] == "ebsi" :
            issuer_did =  issuer_data['did_ebsi']
        elif issuer_data['method'] == "relay" :
            issuer_did = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
        else : 
            issuer_did = didkit.key_to_did(issuer_data['method'], issuer_data['jwk'])
    
        # update credential manifest
        
        credential_manifest['id'] = str(uuid.uuid1())
        try :
            credential_manifest['output_descriptors'][0]['id'] = str(uuid.uuid1())
            credential_manifest['output_descriptors'][0]['schema'] = "https://github.com/TalaoDAO/wallet-tools/blob/main/test/CredentialOffer2/" + issuer_data['credential_to_issue'] + '.jsonld'
            credential_manifest['output_descriptors'][0]['display']['title']['fallback'] = issuer_data.get('card_title', "Unknown")
            credential_manifest['output_descriptors'][0]['display']['subtitle']['fallback'] = issuer_data.get('card_subtitle', "Unknown")
            credential_manifest['output_descriptors'][0]['display']['description']['fallback'] = issuer_data.get('card_description', "Unkwon")
            credential_manifest['output_descriptors'][0]['styles'] = {
                'background' : {'color' : issuer_data['card_background_color']},
                'text' : { 'color' : issuer_data.get('card_text_color', "#000000")}}
        except :
            pass
        credential_manifest['issuer']['id'] = issuer_did
        credential_manifest['issuer']['name'] = issuer_data['company_name']
        if issuer_data['credential_requested'] == "DID" : 
            credential_manifest['presentation_definition'] = dict()
        else :
            credential_manifest['presentation_definition'] = {"id": str(uuid.uuid1()), "input_descriptors": list()}    
            
            if issuer_data['credential_requested'] == "AllAddress" :
                credential_manifest = update_credntial_manifest_all_address(issuer_data['reason'], credential_manifest)
            elif issuer_data['credential_requested'] != "DID":
                credential_manifest = update_credential_manifest(issuer_data['reason'], issuer_data['credential_requested'], credential_manifest)
            
            if issuer_data['credential_requested_2'] == "AllAddress" :
                credential_manifest = update_credntial_manifest_all_address(issuer_data['reason_2'], credential_manifest)
            elif issuer_data.get('credential_requested_2', 'DID') != "DID" :  
                credential_manifest = update_credential_manifest(issuer_data['reason_2'], issuer_data['credential_requested_2'], credential_manifest)
            
            if issuer_data['credential_requested_3'] == "AllAddress" :
                credential_manifest = update_credntial_manifest_all_address(issuer_data['reason_3'], credential_manifest)
            elif issuer_data.get('credential_requested_3', 'DID') != "DID" :  
                credential_manifest = update_credential_manifest(issuer_data['reason_3'], issuer_data['credential_requested_3'], credential_manifest)
            
            if issuer_data['credential_requested_4'] == "AllAddress" :
                credential_manifest = update_credntial_manifest_all_address(issuer_data['reason_4'], credential_manifest)
            elif issuer_data.get('credential_requested_4', 'DID') != "DID" :  
                credential_manifest = update_credential_manifest(issuer_data['reason_4'], issuer_data['credential_requested_4'], credential_manifest)

        #logging.info("credential manifest = %s", credential_manifest)
        if not request.args.get('id') :
            logging.warning("no id passed by application")
            id = str(uuid.uuid1())
        else :
            id = request.args.get('id')
        
        credentialOffer = {
            "id" : id,
            "type": "CredentialOffer",
            "challenge" : str(uuid.uuid1()),
            "domain" : "https://altme.io",
            "credentialPreview": credential,
            "expires" : (datetime.now() + OFFER_DELAY).replace(microsecond=0).isoformat() + "Z",
            "credential_manifest" : credential_manifest
        }
        logging.info("credential Offer sent")
        red.set(id, json.dumps(credentialOffer))   
        return jsonify(credentialOffer)
                        
    # wallet POST
    if request.method == 'POST':
        # send data to webhook
        data_received = dict()
        logging.info("standalone = %s", issuer_data.get('standalone', None))
        if issuer_data.get('standalone', None) == 'on' :
            headers = {
                "key" : issuer_data['client_secret'],
                "Content-Type": "application/json" 
                }       
            url = issuer_data['webhook']
            payload = { 'event' : 'ISSUANCE',
                'vp': json.loads(request.form['presentation']),
                "id": request.form.get('id'),
                'vc_type' : issuer_data['credential_to_issue']
                }
            logging.info("event ISSUANCE sent to webhook")
            r = requests.post(url,  data=json.dumps(payload), headers=headers)
            if not 199<r.status_code<300 :
                logging.error('issuer failed to call application, status code = %s', r.status_code)
                return jsonify("application error"),500            
            try :
                data_received = r.json()
            except :
                logging.error('aplication data are not json')
                return jsonify("application error"),500
            logging.info('aplication data received from Webhook')

        # get credential
        credentialOffer = json.loads(red.get(request.form['id']).decode())  
        credential =  credentialOffer['credentialPreview']

        # extract data sent by application and merge them with verifiable credential data
        if data_received and issuer_data.get('standalone', None) == 'on' :
            credential["credentialSubject"] = data_received
            logging.info("Data received from application added to credential = %s", data_received)
            logging.info("credential subject = %s ", credential["credentialSubject"])

        credential['id'] = "urn:uuid:" + str(uuid.uuid4())
        credential['credentialSubject']['id'] = request.form['subject_id']
        credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
        duration = issuer_data.get('credential_duration', "365")
        credential['expirationDate'] =  (datetime.now().replace(microsecond=0) + timedelta(days= int(duration))).isoformat() + "Z"
        
        if issuer_data['credential_to_issue'] == 'Pass' :
            credential['credentialSubject']['issuedBy']['name'] = issuer_data.get('company_name', 'Unknown')
            #credential['credentialSubject']['issuedBy']['issuerId'] = issuer_id
      
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
            logging.error('Signature failed, application failed to return correct data')
            return jsonify("server error, signature failed"),500
        
        logging.info('signature ok')
       
        # transfer credential signed and credential recieved to application
        #if issuer_data.get('standalone', None) == 'on' :
        event_signed_credential(issuer_data, signed_credential, request.form.get('id'), issuer_data['credential_to_issue'])
        
        # record activity
        activity = {"presented" : datetime.now().replace(microsecond=0).isoformat() + "Z",
                "wallet_did" : request.form['subject_id'],
                "vp" : json.loads(request.form['presentation'])
        }
        beacon_activity_db_api.create(issuer_id, activity) 

        return jsonify(signed_credential)
 

def event_signed_credential(issuer_data, signed_credential, id, vc_type) :
    headers = {
                "key" : issuer_data['client_secret'],
                "Content-Type": "application/json" 
    }      
    url = issuer_data['webhook']
    payload = { 'event' : 'SIGNED_CREDENTIAL',
                'vc': json.loads(signed_credential),
                "vc_type" : vc_type,
                'vp' : json.loads(request.form['presentation']),
                "id": id
                }
    logging.info("event SIGNED_CREDENTIAL sent to webbhook")
    r = requests.post(url,  data=json.dumps(payload), headers=headers)
    if not 199<r.status_code<300 :
        logging.error('issuer failed to send signed credential to webhook, status code = %s', r.status_code)
   

