from flask import jsonify
import json
import requests
from components import privatekey
from github import Github
import base64
import logging

logging.basicConfig(level=logging.INFO)
REGISTRY_REPO = "TalaoDAO/context"
DID_WEB = 'did:web:talao.co'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ2 = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY = 'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'
did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
LIST_TRUSTED_ISSUER_REGISTRY_API = 'http://192.103.2.28:1234/tmd/get_did_issuer/'

def init_app(app,red, mode) :

    app.add_url_rule('/trusted-issuers-registry/v1/issuers/<did>',  view_func=tir_api, methods = ['GET'])

    global PVK, test_repo, registry_repo
    g = Github(mode.github)
    PVK = privatekey.get_key(mode.owner_talao, 'private_key', mode)
    registry_repo = g.get_repo(REGISTRY_REPO)
    return

    #/trusted-issuers-registry/v1/issuers/did:ethr:0xd6008c16068c40c05a5574525db31053ae8b3ba7

def tir_api(did) :
    """
    Issuer Registry public JSON API GET:
    https://ec.europa.eu/cefdigital/wiki/display/EBSIDOC/1.3.2.4.+Trusted+Registries+ESSIF+v2#id-1.3.2.4.TrustedRegistriesESSIFv2-TrustedIssuerRegistryEntry-TIR(generic)
    https://ec.europa.eu/cefdigital/wiki/display/EBSIDOC/Trusted+Issuers+Registry+API

    """
    
    try : 
        r = requests.get(LIST_TRUSTED_ISSUER_REGISTRY_API + did)
        if r.status_code == 200 :
            logging.info("OK, retour List = ", r.json())
            return r.json()
        elif r.status_code == 404 :
            logging.info('Issuer not found on the List server')
        else :
            logging.info('Erreur serveur List =', r.status_code  )
    except :
        logging.error('probleme de connexion sur List')
    if did in [DID_WEB, DID_TZ2, DID_ETHR, DID_KEY] :
        logging.info('Internal TIAR / Talao')
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
    elif did == 'did:ethr:0xbf4dfdd84c24539349e0d06f3eac16edffc9d88f' :
        logging.info('Internal TIAR / MyCompany')
        return jsonify({
            "issuer": {
                "preferredName": "My Company",
                "did": ['did:ethr:0xbf4dfdd84c24539349e0d06f3eac16edffc9d88f'],
                "eidasCertificatePem": [{}],
                "serviceEndpoints": [{}, {}],
                "organizationInfo": {
                    "id": "",
                    "legalName": "My Company",
                    "currentAddress": "1 Rue Beaumont, L-1631 Luxembourg, Luxembourg",
                    "vatNumber": "",
                    "website": "https://mycompany.io",
                    "issuerDomain" : ["talao.co"]
                }
            }
        })
    elif did == 'did:tz:tz2PLg4sKFGZUo8YW1m11P9iD5X3uCcNLZq8' :
        logging.info('Internal TIAR / New Indus')
        return jsonify({
            "issuer": {
                "preferredName": "New Indus",
                "did": ['did:tz:tz2PLg4sKFGZUo8YW1m11P9iD5X3uCcNLZq8'],
                "eidasCertificatePem": [{}],
                "serviceEndpoints": [{}, {}],
                "organizationInfo": {
                    "id": "",
                    "legalName": "New Indus",
                    "currentAddress": "1 Rue Beaumont, L-1631 Luxembourg, Luxembourg",
                    "vatNumber": "",
                    "website": "https://newindus.io",
                    "issuerDomain" : ["talao.co"]
                }
            }
        })
    else :
        #registry_file = registry_repo.get_contents("test/registry/talao_issuer_registry.json")
        #b64encoded_registry = registry_file.__dict__['_rawData']['content']
        #issuer_registry = json.loads(base64.b64decode(b64encoded_registry).decode())
        issuer_registry = json.load(open("talao_trusted_issuer_registry.json", 'r' ))
        for item in issuer_registry :
            if did in item['issuer']["did"] :
                return jsonify(item)
        return jsonify("DID not found") , 404

