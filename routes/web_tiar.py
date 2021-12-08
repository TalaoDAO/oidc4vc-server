from flask import jsonify
import json
import requests
import logging

logging.basicConfig(level=logging.INFO)
DID_WEB = 'did:web:talao.co'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ2 = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY = 'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'
#LIST_TRUSTED_ISSUER_REGISTRY_API = 'http://192.103.2.28:1234/tmd/get_data_issuer/'
LIST_TRUSTED_ISSUER_REGISTRY_API = 'https://tmd.list.lu:1234/tmd/get_data_issuer/'

def init_app(app) :
    app.add_url_rule('/trusted-issuers-registry/v1/issuers/<did>',  view_func=tir_api, methods = ['GET'])
    return
    #/trusted-issuers-registry/v1/issuers/did:ethr:0xd6008c16068c40c05a5574525db31053ae8b3ba7

def tir_api(did) :
    """
    Issuer Registry public JSON API GET:
    https://ec.europa.eu/cefdigital/wiki/display/EBSIDOC/1.3.2.4.+Trusted+Registries+ESSIF+v2#id-1.3.2.4.TrustedRegistriesESSIFv2-TrustedIssuerRegistryEntry-TIR(generic)
    https://ec.europa.eu/cefdigital/wiki/display/EBSIDOC/Trusted+Issuers+Registry+API

    """
    logging.info("Registry look up for DID = %s", did)
    
    if did in [DID_WEB, DID_TZ2, DID_KEY] :
        logging.info('Issuer found on the Talao Trusted Issuer Internal List')
        return jsonify({
            "issuer": {
                "preferredName": "Talao",
                "did": ["did:web:talao.co","did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250","did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk"],
                "eidasCertificatePem": [{}],
                "serviceEndpoints": [{}, {}],
                "organizationInfo": {
                    "id": "837674480",
                    "legalName": "Talao SAS",
                    "currentAddress": "Talao, 16 rue de Wattignies, 75012 Paris, France",
                    "vatNumber": "FR26837674480",
                    "website": "https://talao.co",
                    "issuerDomain" : ["talao.co", "talao.io"]
                }
            }
        })
    else :
        # proxy LIST server for LUX prototype
        try : 
            r = requests.get(LIST_TRUSTED_ISSUER_REGISTRY_API + did)           
        except :
            logging.info('Erreur serveur LIST =', r.status_code  )
            return jsonify("Erreur request server list") , 404
        if r.status_code == 200 :
            print("OK, retour LIST = ", r.json(), type(r.json()))
            issuer_json = r.json['issuer']
            issuer = json.loads(issuer_json)
            print("issuer = ", issuer)
            return jsonify({"issuer" : issuer})
        else :
            logging.info('DID not found =')
            return jsonify("DID not found") , 404

