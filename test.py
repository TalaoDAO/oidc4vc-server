import environment
import constante
import os
import didkit
import json
import base64
import sys
import jwt
import requests

from eth_keys import keys
from eth_utils import decode_hex
from jwcrypto import jwk
from datetime import datetime

#from components import privatekey
#from signaturesuite import vc_signature, helpers

#key = didkit.generateEd25519Key()
#print('key Ed25519Key ', key)

#key = json.loads(didkit.generateEd25519Key())
#print(key)

#did = didkit.keyToDID("key", key)
#print('did key = ', did)


#did2 = didkit.keyToDID("tz", key)
#print('did tz = ', did2)

#vm = didkit.keyToVerificationMethod('key', key)
#print('vm = ', vm)

"""
mode = environment.currentMode('talaonet','airbox')

username = 'pascaldelorme'
for username in ['talao', 'mycompany', 'pascaldelorme', 'thierrythevenet','pauldupont', 'masociete' ] :
        address = ns.get_data_from_username(username, mode).get('address')
        privatekey.generate_store_key(address, 'Ed25519', mode)
        privatekey.generate_store_key(address, 'P-256', mode)
"""

#print('key = ', privatekey.get_key(address, 'P-256', mode))
#print('key = ', privatekey.get_key(address, 'secp256k1', mode))
#print('key = ', privatekey.get_key(address, 'Ed25519', mode))

#print('address = ', address)
#pvk = privatekey.get_key(address, 'private_key', mode)

#key = jwk.JWK.from_pem(pvk.encode())
#key = key.export_private()
#del rsa_public['kid']

#pvk = privatekey.get_key(address, 'private_key', mode)
#key = helpers.ethereum_to_jwk256k(pvk)

#pvk = "0x7f1116bdb705f3e51a299a1fe04b619e0e2516258ef187946076b04151ece8a5"
#address = helpers.ethereum_pvk_to_address(pvk)
#workspace_contract = ownersToContracts(address,mode)

#print('address = ', helpers.ethereum_pvk_to_address(pvk))
#print('workspace_contract = ', workspace_contract)

#key = helpers.ethereum_to_jwk256kr(pvk)
#did = helpers.ethereum_pvk_to_DID(pvk, method)

#key =  json.dumps({"crv": "secp256k1", "d": "fxEWvbcF8-UaKZof4Ethng4lFiWO8YeUYHawQVHs6KU", "kty": "EC", "x": "uPSr7x3mgveGQ_xvuxO6CFIY6GG09ZsmngY5S2EixKk", "y": "mq7je_woNa3iMGoYWQ1uZKPjbDgDCskAbh12yuGAoKw", "alg": "ES256K-R"})
#key = jwk.JWK.generate(kty="EC", crv="secp256k1", alg="ES256K-R")
#key = jwk.JWK.generate(kty="EC", crv="P-256")
#key = jwk.JWK.generate(kty="EC", crv="secp256k1")
#key = jwk.JWK.generate(kty="OKP", crv="Ed25519")
#key = jwk.JWK.generate(kty='RSA', size=2048)
#a = key.export_to_pem(private_key=True, password=b'test')
#print (a)
#key=key.export_private()
#print('key = ', key)
#key = '{"crv":"P-256","d":"zqojPOaQaVLmCZfHM5sYQNJ4pGqt4H8jTLUrokW04vU","kty":"EC","x":"OlhAgrdZrGbUcuoNeY8FNuUhcJGlDFkvXUv9DhvRsHc","y":"PyKwME0TRLcAQaQ1xexNkN_87bhCRseKgf5dDc261oQ"}'
#key = helpers.ethereum_to_jwk(pvk, method)
#did = helpers.jwk_to_did(method, key)

#method = "ethr"
#did = didkit.keyToDID(method, key)
#print('did = ', did)


key2 = json.dumps(
        {
        "crv": "P-256",
        "d": "HJjVZ1qx2m4NJF-ohV55VlD7UwkjOBUESo4hwCmny-Y",
        "kty" : "EC",
        "x" : "Bls7WaGu_jsharYBAzakvuSERIV_IFR2tS64e5p_Y_Q",
        "y" : "haeKjXQ9uzyK4Ind1W4SBUkR_9udjjx1OmKK4vl1jko"
        })

key3 = json.dumps({
        "crv": "secp256k1",
        "d": "WxNkSy38UZUxfAOBWbHQSynEi8pmu97fKehiojNv9mw",
        "kty": "EC",
        "x": "bjyWuKGoDtUXKD6RzbE4suxoNk0E6pKe0qZTHh1LMg4",
        "y": "O1JNLN8bO3EP23WNIiqxfGY8OwOkrcw4hmXXHzwmsGg"})


#address = mode.owner_talao
#pvk = privatekey.get_key(address, 'private_key', mode)
#key = helpers.ethereum_to_jwk256k(pvk)

key = {"crv": "secp256k1",
        "d": "8POOMms0FeS6fmIN7neX7PROjMrFE9c2q4L58R0iVXo",
        "kty": "EC",
        "x": "gmQ9LW8cvcZElSrFu-qSEtEM2KN90jVFV--Ap3cSLis",
        "y": "W7mcKtpQwZTrRxjsYkm549lQQLIcuEFo9Ts3tyopOxw",
       }

#key = jwk.JWK.generate(kty="EC", crv="secp256k1", alg="ES256K-R")
#key = jwk.JWK.generate(kty="EC", crv="P-256")
#key = jwk.JWK.generate(kty="EC", crv="secp256k1")
#key = jwk.JWK.generate(kty="OKP", crv="Ed25519")
#key=key.export_private()

print(key)
#did = didkit.keyToDID("web", json.dumps(key))
did = "did:web:talao.co"
print('did = ', did)
#did = "did:web:did.actor:mike"
#did = "did:ion:EiBgFSQI9fBXGuAam_OvZnldleL5auu1VTCp6Wzdyv98_w"
DIDdocument = didkit.resolveDID(did,'{}')
#print('DID Document = ', json.dumps(json.loads(DIDdocument), indent=4))


#vm = didkit.keyToVerificationMethod(method, key)
#print('verifmethod = ', vm)
#vm = "did:ion:EiBgFSQI9fBXGuAam_OvZnldleL5auu1VTCp6Wzdyv98_w"
#verifmethod = didkit.keyToVerificationMethod("ethr", key)
#verifmethod = didkit.keyToVerificationMethod(method, key)
#verifmethod = "did:ethr:0x9e98af48200c62f51ac9ebdcc41fe718d1be04fb#controller"
#verifmethod = did + "#key-2"
#print('verfif method = ', verifmethod)


#print(json.dumps(json.loads(presentation), indent=4))


credential ={
        "@context":  "https://www.w3.org/2018/credentials/v1",
        "issuer": did,
        "issuanceDate": "2021-05-06T14:08:28-06:00",
        "expirationDate": "2025-12-04T14:08:28-06:00",
        "type": ["VerifiableCredential"],
        "credentialSubject": {
                "id": did,
                },
        }


didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": did + "#key-3",
        }


didkit_credential = didkit.issueCredential(
        credential.__str__().replace("'", '"'),
        didkit_options.__str__().replace("'", '"'),
        json.dumps(key)
        )


print(json.dumps(json.loads(didkit_credential), indent=4))
