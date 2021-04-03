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

print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

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




pvk = "0x7f1116bdb705f3e51a299a1fe04b619e0e2516258ef187946076b04151ece8a5"


key = jwk.JWK.generate(kty="EC", crv="secp256k1", alg="ES256K-R",  b64=False, crit=["b64"])
#key = jwk.JWK.generate(kty="EC", crv="P-256")
#key = jwk.JWK.generate(kty="EC", crv="secp256k1")
#key = jwk.JWK.generate(kty="OKP", crv="Ed25519")
key=key.export_private()
print('key = ', key)
did = didkit.keyToDID("tz", key)
print('did  = ', did)

#did_key = didkit.keyToDID("key", key)
#print('did key = ', did_key)

#print(key)

verifmethod = didkit.keyToVerificationMethod("tz", key)

verifmethod = didkit.keyToVerificationMethod("ethr", key)
#verifmethod = didkit.keyToVerificationMethod("key", key)

"""
credential = { "@context": "https://www.w3.org/2018/credentials/v1",
                        "type": ["VerifiableCredential"],
                        "issuer" : did  ,
                        "issuanceDate": "2020-08-19T21:41:50Z",
                        "credentialSubject": {
                        "id": "did:example:d23dd687a7dc6787646f2eb98d0",
                        }
}
"""
fp=open("./verifiable_credentials/identity.jsonld", "r")
credential = json.loads(fp.read())
print('credential = ', credential)



didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": verifmethod
        }

credential = didkit.issueCredential(
        credential.__str__().replace("'", '"'),
        didkit_options.__str__().replace("'", '"'),
        key
        )

print(json.dumps(json.loads(credential), indent=4))

print(didkit.verifyCredential(credential, didkit_options.__str__().replace("'", '"')))
