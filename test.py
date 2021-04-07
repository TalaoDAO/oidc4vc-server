import environment
import constante
import os
import didkit
import json
import base64
from eth_keys import keys
from eth_utils import decode_hex
from jwcrypto import jwk
from signaturesuite import helpers

from datetime import datetime


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


method = "tz"

#pvk = "0x7f1116bdb705f3e51a299a1fe04b619e0e2516258ef187946076b04151ece8a5"
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




#did = didkit.keyToDID(method, key)
#print('did  = ', did)
did = "did:oui"
#did = "did:web:talao.co:thierry"

#DIDdocument = didkit.resolveDID(did,json.dumps({}))
#print(json.dumps(json.loads(DIDdocument), indent=4))

#verifmethod = didkit.keyToVerificationMethod(method, key)
#verifmethod = didkit.keyToVerificationMethod("ethr", key)
#verifmethod = didkit.keyToVerificationMethod("key", key)
#verifmethod = "did:ethr:0x9e98af48200c62f51ac9ebdcc41fe718d1be04fb#controller"
verifmethod = "data:oui"
#print('verfif method = ', verifmethod)

credential = { "@context": "https://www.w3.org/2018/credentials/v1",
                        "type": ["VerifiableCredential"],
                        "issuer" : did  ,
                        "issuanceDate": "2020-08-19T21:41:50Z",
                        "credentialSubject": {
                        "id": "did:example:d23dd687a7dc6787646f2eb98d0",
                        }
}


#fp=open("./verifiable_credentials/reference.jsonld", "r")
#credential = json.loads(fp.read())
credential["issuanceDate"] = "2020-08-19T21:41:50Z"
credential["issuer"] = did
#credential['id'] = "data:5656"
#credential["credentialSubject"]["id"] = "data:555"

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
credential = didkit.issueCredential(
        json.dumps(credential, ensure_ascii=False),
        didkit_options.__str__().replace("'", '"'),
        key
        )
"""

print(json.dumps(json.loads(credential), indent=4, ensure_ascii=False))
#print(didkit.verifyCredential(credential, didkit_options.__str__().replace("'", '"')))

