from flask import jsonify, request, jsonify
import requests
import json
import uuid
import logging
from datetime import datetime
import didkit
from db_api import read_tezid_verifier
import op_constante
import tezid_activity_db_api

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
    app.add_url_rule('/sandbox/op/tezid/verifier/<verifier_id>',  view_func=tezid_verifier, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    return


async def tezid_verifier(verifier_id, red, mode):
    try :
        verifier_data = json.loads(read_tezid_verifier(verifier_id))
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
                return False
            if credential['issuer'] not in TRUSTED_ISSUER :
                logging.warning("issuer not in trusted list")
                #return False
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
            #verification = False
        credential_list = json.loads(presentation)['verifiableCredential']
        if isinstance(credential_list, dict) :
            credential_list = list(credential_list)
        for credential in credential_list :
            if not await check_credential(credential) :
                verification = False
            if credential['credentialSubject']['type'] not in ['TezosAssociatedAddress', verifier_data.get('vc'), verifier_data.get('vc_2')] :
                verification = False
            if credential['credentialSubject']['type'] == 'TezosAssociatedAddress' :
                associatedAddress = credential['credentialSubject']['associatedAddress']
        if not verification :
            logging.warning('Access denied')
            return jsonify('Unhautorized'), 403
        if not register_tezid(associatedAddress, verifier_id, mode) :
            return jsonify ('Server error'), 500
        # record activity
        vc_type_list = list()
        for credential in credential_list :
            vc_type_list.append(credential['credentialSubject']['type'])
        activity = {'presented' : datetime.now().replace(microsecond=0).isoformat() + "Z",
                'blockchainAddress' : associatedAddress,
                'vc_type' : vc_type_list,
                'verification' : verification
        }
        tezid_activity_db_api.create(verifier_id, activity) 
        return jsonify("ok")


# curl -XPOST https://tezid.net/api/ghostnet/issuer/altme -H 'tezid-issuer-key:p3hMf9V/OaiJjPOC2Va9uzDg6uj02E1YpCD9xdTB63Q=' -H 'Content-Type: application/json' --data '{ "address": "tz1UVNksAzMyR3HDnKDjrF7N4BCw7m6Bgs6J", "prooftype": "test_type", "register": true }'

def register_tezid(address, id, mode) :
    url = "https://tezid.net/api/ghostnet/proofs/" + address
    r = requests.get(url)
    if not 199<r.status_code<300 :
        logging.error("API call to TezID rejected %s", r.status_code)
        return False
    logging.info('existing Proof types = %s', r.json())
    if not r.json() and not register_proof_type(address, id, mode) :
        return False
    else :
        proof_registered = False
        for proof in r.json() :
            if proof['id'] == id and proof['verified'] :
                proof_registered = True
                logging.info('proof exists on TezID')
                break
        if not proof_registered and not register_proof_type(address, id, mode) :
            return False
    return True

def register_proof_type(address, proof_type, mode) :
    #[{"id":"test_type","label":"Test_type","meta":{"issuer":"altme"},"verified":true,"register_date":"2022-12-03T11:16:30Z"}]
    url = 'https://tezid.net/api/ghostnet/issuer/altme'
    headers = {
        'Content-Type' : 'application/json',
        'tezid-issuer-key' : mode.tezid_issuer_key     
    }
    data = {
        "address": address,
        "prooftype": proof_type,
        "register": True
    }
    r = requests.post(url, headers=headers, data=json.dumps(data))
    logging.info("status code = %s", r.status_code)
    if not 199<r.status_code<300 :
        logging.error("API call to TezID rejected %s", r.status_code)
        return False
    logging.info('User has been registered on TezID')
    return True