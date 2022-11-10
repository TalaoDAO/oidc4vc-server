from flask import jsonify, request, jsonify
import requests
import json
import uuid
import logging
from datetime import datetime
import didkit
from db_api import read_beacon_verifier
import op_constante
import beacon_activity_db_api

logging.basicConfig(level=logging.INFO)

ACCESS_TOKEN_LIFE = 1800
QRCODE_LIFE = 180
CODE_LIFE = 180
DID_VERIFIER = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
TRUSTED_ISSUER = [
    "did:tz:tz1RuLH4TvKNpLy3AqQMui6Hys6c1Dvik8J5",
    "did:tz:tz2X3K4x7346aUkER2NXSyYowG23ZRbueyse",
    "did:ethr:0x61fb76ff95f11bdbcd94b45b838f95c1c7307dbd",
    "did:web:talao.co",
    "did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250",
    "did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk",
    "did:ethr:0xd6008c16068c40c05a5574525db31053ae8b3ba7",
    "did:tz:tz1NyjrTUNxDpPaqNZ84ipGELAcTWYg6s5Du",
    "did:tz:tz2UFjbN9ZruP5pusKoAKiPD3ZLV49CBG9Ef"
]


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/beacon/verifier/<verifier_id>',  view_func=beacon_verifier, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    return


async def beacon_verifier(verifier_id, red, mode):
    try :
        verifier_data = json.loads(read_beacon_verifier(verifier_id))
    except :
        logging.error('client id not found')
        return jsonify("verifier not found"), 404
    if request.method == 'GET':
        if verifier_data.get('vc') == "ANY" :
            pattern = op_constante.model_any
        elif verifier_data.get('vc') == "DID" :
            pattern = op_constante.model_DIDAuth
        elif not verifier_data.get('vc_2') or verifier_data.get('vc_2') == "DID" :
            pattern = op_constante.model_one
            pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = verifier_data['reason']
            pattern["query"][0]["credentialQuery"][0]["example"]["type"] = verifier_data['vc']
        else :
            pattern = op_constante.model_two
            pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = verifier_data['reason']
            pattern["query"][0]["credentialQuery"][0]["example"]["type"] = verifier_data['vc']
            pattern["query"][0]["credentialQuery"][1]["reason"][0]["@value"] = verifier_data['reason_2']
            pattern["query"][0]["credentialQuery"][1]["example"]["type"] = verifier_data['vc_2']
        """else :
            pattern = op_constante.model_three
            pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = 'Select your Tezos blockchain account'
            pattern["query"][0]["credentialQuery"][0]["example"]["type"] = 'TezosAssociatedAddress'
            pattern["query"][0]["credentialQuery"][1]["reason"][0]["@value"] = verifier_data['reason']
            pattern["query"][0]["credentialQuery"][1]["example"]["type"] = verifier_data['vc']
            pattern["query"][0]["credentialQuery"][2]["reason"][0]["@value"] = verifier_data['reason_2']
            pattern["query"][0]["credentialQuery"][2]["example"]["type"] = verifier_data['vc_2']
        """
        pattern['domain'] = mode.server
        if not request.args.get('id') :
            pattern['challenge'] = str(uuid.uuid1())
        else : 
            pattern['challenge'] = request.args.get('id')
        pattern['domain'] = 'Altme.io'
        # TODO incorrect use of challenge to carry the redis data
        red.setex(pattern['challenge'], QRCODE_LIFE, json.dumps(pattern))
        return jsonify(pattern)

    if request.method == 'POST' :        
        async def check_credential(credential) :     
            result_credential = await didkit.verify_credential(json.dumps(credential), '{}')
            if json.loads(result_credential)['errors']  :       
                logging.warning("credential signature check failed")
                return False
            if  credential["credentialSubject"]['id'] != json.loads(presentation)['holder'] :
                if credential["credentialSubject"]['type'] == "AragoPass" :
                    logging.error("DID does not match in Arago pass")
                else :  
                    logging.warning("holder does not match subject.id")     
                    return False
            if credential.get('expirationDate') and credential.get('expirationDate') <  datetime.now().replace(microsecond=0).isoformat() + "Z" :
                return False
            if credential['issuer'] not in TRUSTED_ISSUER :
                logging.warning("issuer not in trusted list")
                #return manage_error("issuer not in trusted list")
            return True

        presentation = request.form['presentation'] # string
        id = json.loads(presentation)['proof']['challenge']
        pattern = red.get(id).decode()
        #result_presentation = await didkit.verify_presentation(presentation,  '{}')
        #if json.loads(result_presentation)['errors'] :
        #    return manage_error("presentation signature check failed")
        logging.info("check presentation = %s", await didkit.verify_presentation(presentation,  '{}'))

        credential = json.loads(presentation)['verifiableCredential']
        verification = True
        payload = dict()
        logging.info('API verifier credential type = %s', credential["credentialSubject"]['type'])
        if isinstance(credential, dict) :
            if credential["credentialSubject"]['type'] == "BloometaPass" :
                payload.update(credential["credentialSubject"])
            if credential["credentialSubject"]['type'] in ["TezosAssociatedAddress", "EthereumAssociatedAddress"] :
                payload['associatedAddress'] =  credential["credentialSubject"]['associatedAddress']
            if not await check_credential(credential) :
                verification = False
        else :
            for cred in credential :
                if not await check_credential(cred) :
                    verification = False
               
        vc_type = list()
        if isinstance(credential, dict) :
            vc_type.append(credential['credentialSubject']['type'])
        else :
            for cred in credential :
                vc_type.append(cred['credentialSubject']['type'])
        
        # send data to webhook       
        payload.update({ 'event' : 'VERIFICATION',
                    'id' : id,  
                    'presented' : datetime.now().replace(microsecond=0).isoformat() + "Z",
                    'vc_type' : vc_type,
                    "verification" : verification
            })
       
        headers = {
                "key" : verifier_data['client_secret'],
                "Content-Type": "application/json" 
        }   
        r = requests.post(verifier_data['webhook'],  data=json.dumps(payload), headers=headers)
        if not 199<r.status_code<300 :
            logging.error('VERIFICATION : verifier failed to call application, status code = %s', r.status_code)
        
        # send data to webhook
        if verifier_data.get('standalone', None) == 'on' :
            payload = { 'event' : 'VERIFICATION_DATA',
                        'presented' : datetime.now().replace(microsecond=0).isoformat() + "Z",
                        'vc_type' : vc_type,
                        'id' : id,
                        'vp': json.loads(request.form['presentation']),
                        'verification' : verification
            }
            headers = {
                "key" : verifier_data['client_secret'],
                "Content-Type": "application/json" 
            }       
            r = requests.post(verifier_data['webhook'],  data=json.dumps(payload), headers=headers)
            if not 199<r.status_code<300 :
                logging.error('VERIFICATION_DATA : verifier failed to call application, status code = %s', r.status_code)
        
        # record activity
        activity = {'presented' : datetime.now().replace(microsecond=0).isoformat() + "Z",
                'vc_type' : vc_type,
                'verification' : verification
        }
        beacon_activity_db_api.create(verifier_id, activity) 
        return jsonify("ok")

