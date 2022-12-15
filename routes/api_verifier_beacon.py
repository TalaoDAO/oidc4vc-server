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
from altme_on_chain import register_tezid, issue_sbt

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
        if verifier_data.get('vc') == "DID" :
            pattern = op_constante.model_one
            pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = 'Select your Tezos blockchain account'
            pattern["query"][0]["credentialQuery"][0]["example"]["type"] = 'TezosAssociatedAddress'
        elif not verifier_data.get('vc_2') or verifier_data.get('vc_2') == "DID" :
            pattern = op_constante.model_two
            pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = 'Select your Tezos blockchain account'
            pattern["query"][0]["credentialQuery"][0]["example"]["type"] = 'TezosAssociatedAddress'
            pattern["query"][0]["credentialQuery"][1]["reason"][0]["@value"] = verifier_data['reason']
            pattern["query"][0]["credentialQuery"][1]["example"]["type"] = verifier_data['vc']
        else :
            pattern = op_constante.model_three
            pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = 'Select your Tezos blockchain account'
            pattern["query"][0]["credentialQuery"][0]["example"]["type"] = 'TezosAssociatedAddress'
            pattern["query"][0]["credentialQuery"][1]["reason"][0]["@value"] = verifier_data['reason']
            pattern["query"][0]["credentialQuery"][1]["example"]["type"] = verifier_data['vc']
            pattern["query"][0]["credentialQuery"][2]["reason"][0]["@value"] = verifier_data['reason_2']
            pattern["query"][0]["credentialQuery"][2]["example"]["type"] = verifier_data['vc_2']    
        pattern['domain'] = mode.server
       
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
                logging.warning("holder does not match subject.id")     
                return False
            if credential.get('expirationDate') and credential.get('expirationDate') <  datetime.now().replace(microsecond=0).isoformat() + "Z" :
                logging.warning("Credential expired")     
                return False
            if credential['issuer'] not in TRUSTED_ISSUER :
                logging.warning("Issuer not in trusted issuer registry")
            return True
        
        presentation = request.form['presentation']
        verification = True
        # one cannot do more than check that 
        try :
            id = json.loads(presentation)['proof']['challenge']
            pattern = red.get(id).decode()
        except :
            verification = False
        if json.loads(pattern)['challenge'] != id :
            logging.warning('challenge does not match')
            verification = False
        result_presentation = await didkit.verify_presentation(presentation,  '{}')
        if json.loads(result_presentation)['errors'] :   
            logging.warning("check presentation = %s", result_presentation)
        credential_list = json.loads(presentation)['verifiableCredential']
        vc_type = list()
        if isinstance(credential_list, dict) :
            credential_list = list(credential_list)
        for credential in credential_list :
            vc_type.append(credential['credentialSubject']['type'])
            if not await check_credential(credential) :
                verification = False
            if credential['credentialSubject']['type'] not in ['TezosAssociatedAddress', verifier_data.get('vc'), verifier_data.get('vc_2')] :
                verification = False
            if credential['credentialSubject']['type'] == 'TezosAssociatedAddress' :
                associatedAddress = credential['credentialSubject']['associatedAddress']
        if not verification :
            logging.warning('Access denied')
            return jsonify('Unhautorized'), 403
        
        # send digest data to webhook       
        payload = { 'event' : 'VERIFICATION',
                    'id' : id,  
                    'address' : associatedAddress, 
                    'presented' : datetime.now().replace(microsecond=0).isoformat() + "Z",
                    'vc_type' : vc_type,
                    "verification" : verification
            }
        headers = {
                "key" : verifier_data['client_secret'],
                "Content-Type": "application/json" 
        }   
        r = requests.post(verifier_data['webhook'],  data=json.dumps(payload), headers=headers)
        if not 199<r.status_code<300 :
            logging.error('VERIFICATION : verifier failed to call application, status code = %s', r.status_code)
        else :
            logging.info('VERIFICATION event sent')
        
        # send credentials to webhook
        payload = { 'event' : 'VERIFICATION_DATA',
                    'address' : associatedAddress, 
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
            logging.error('VERIFICATION_DATA : verifier failed to send data to webhook, status code = %s', r.status_code)
        else :
            logging.info('VERIFICATION_DATA event sent')
        
        # TezID whitelisting register in whitelist on ghostnet KT1K2i7gcbM9YY4ih8urHBDbmYHLUXTWvDYj
        if verifier_data.get("tezid_proof_type", None) and verifier_data.get('tezid_network') not in  ['none', None] :
            register_tezid(associatedAddress, verifier_data["tezid_proof_type"], verifier_data['tezid_network'], mode) 
            logging.info('Whitelisting done')
        
        # issue SBT
        # https://tzip.tezosagora.org/proposal/tzip-21/#creators-array
        if verifier_data.get('sbt_network') not in  ['none', None] :
            metadata = {
                "name": verifier_data['sbt_name'],
                "symbol":"ALTMESBT",
                "creators":["Altme.io","did:web:altme.io:did:web:app.altme.io:issuer"],
                "decimals":"0",
                "identifier" :  credential['id'],
                "displayUri":verifier_data['sbt_display_url'],
                "publishers":["compell.io"],
                "minter": "KT1JwgHTpo4NZz6jKK89rx3uEo9L5kLY1FQe",
                "rights": "No License / All Rights Reserved",
                "artifactUri": verifier_data['sbt_display_uri'],
                "description": verifier_data['sbt_description'],
                "thumbnailUri": verifier_data['sbt_thumbnail_uri'],
                "is_transferable":False,
                "shouldPreferSymbol":False
            }
            if issue_sbt(associatedAddress, metadata, credential['id'], mode) :
                logging.info("SBT sent")

        # record activity
        activity = {
            'presented' : datetime.now().replace(microsecond=0).isoformat() + "Z",
            'vc_type' : vc_type,
            'verification' : verification,
            'blockchainAddress' : associatedAddress
        }
        beacon_activity_db_api.create(verifier_id, activity) 
        return jsonify("ok")

