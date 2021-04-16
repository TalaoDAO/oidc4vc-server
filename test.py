import environment
import constante
import os
import didkit
import json
import base64
import sys

import requests

from eth_keys import keys
from eth_utils import decode_hex
from jwcrypto import jwk
from signaturesuite import helpers
from protocol import ownersToContracts
from datetime import datetime
from components import privatekey, ns

from components import privatekey
from signaturesuite import credential, helpers

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

key =  json.dumps({"crv": "secp256k1", "d": "fxEWvbcF8-UaKZof4Ethng4lFiWO8YeUYHawQVHs6KU", "kty": "EC", "x": "uPSr7x3mgveGQ_xvuxO6CFIY6GG09ZsmngY5S2EixKk", "y": "mq7je_woNa3iMGoYWQ1uZKPjbDgDCskAbh12yuGAoKw", "alg": "ES256K-R"})
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

method = "tz"
#key = helpers.ethereum_to_jwk(pvk, method)
#did = helpers.jwk_to_did(method, key)

did = didkit.keyToDID(method, key)
#print('did = ', did)


#print('did  = ', did)
#did = "did:web:talao.co:thierrythevenet"
#did = "did:web:did.actor:mike"

DIDdocument = didkit.resolveDID(did,'{}')
#print(json.dumps(json.loads(DIDdocument), indent=4))

verifmethod = didkit.keyToVerificationMethod(method, key)
#verifmethod = didkit.keyToVerificationMethod("ethr", key)
#verifmethod = didkit.keyToVerificationMethod("key", key)
#verifmethod = "did:ethr:0x9e98af48200c62f51ac9ebdcc41fe718d1be04fb#controller"
#verifmethod = did + "#key-2"
#print('verfif method = ', verifmethod)

# step 1 contact endpoint to get challenge
response = requests.get("http://127.0.0.1:10000/repository/authn")
challenge = response.json()['challenge']

# step 2 response with DID signature
verificationPurpose = {
            "proofPurpose": "authentication",
            "verificationMethod": verifmethod,
            "challenge" : challenge
        }
presentation = didkit.DIDAuth(
            did,
            verificationPurpose.__str__().replace("'", '"'),
            key
        )
response = requests.post("http://127.0.0.1:10000/repository/authn", json = json.loads(presentation))
token = response.json()['token']

# step 3 call an endpoint
credential = {'test' : 123 }
data = {"token" : token, "credential" : credential }
response = requests.post("http://127.0.0.1:10000/repository/publish", json = data)



"""
verifyResult = json.loads(didkit.verifyPresentation(
            presentation,
            verificationPurpose.__str__().replace("'", '"')))

print(verifyResult)

cred = { "@context": "https://www.w3.org/2018/credentials/v1",
                "type": ["VerifiableCredential"],
                "issuer" : did  ,
                "issuanceDate": "2020-08-19T21:41:50Z",
                "credentialSubject": {
                "id": "did:example:d23dd687a7dc6787646f2eb98d0",
                        }
        }
"""
#print(credential.sign(cred, pvk, method))


#fp=open("./verifiable_credentials/reference.jsonld", "r")
#credential = json.loads(fp.read())

#credential["issuanceDate"] = "2020-08-19T21:41:50Z"
#credential["issuer"] = did

#credential['id'] = "data:5656"
#credential["credentialSubject"]["id"] = "data:555"

"""
didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": verifmethod
        }

credential = didkit.issueCredential(
        credential.__str__().replace("'", '"'),
        didkit_options.__str__().replace("'", '"'),
        key
        )
"""

"""
credential = didkit.issueCredential(
        json.dumps(credential, ensure_ascii=False),
        didkit_options.__str__().replace("'", '"'),
        key
        )
"""

#print(json.dumps(json.loads(credential), indent=4, ensure_ascii=False))
#print(didkit.verifyCredential(credential, didkit_options.__str__().replace("'", '"')))


