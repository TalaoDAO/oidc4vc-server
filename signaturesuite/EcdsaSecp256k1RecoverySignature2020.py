"""
method did:eth
signature suite  with universal resolver
"""

import pytz

import didkit
import json
import base64
from eth_keys import keys
from eth_utils import decode_hex
from jwcrypto import jwk
from datetime import datetime


def jwk_to_ethereum(jwk) :
        jwk = json.loads(jwk)
        private_key = "0x" + base64.urlsafe_b64decode(jwk["d"] + '=' * (4 - len(jwk["d"]) % 4)).hex()
        priv_key_bytes = decode_hex(private_key)
        priv_key = keys.PrivateKey(priv_key_bytes)
        pub_key = priv_key.public_key
        public_key = pub_key.to_hex()
        address = pub_key.to_checksum_address()
        return private_key, public_key, address


def ethereum_to_jwk256kr(private_key) :
        priv_key_bytes = decode_hex(private_key)
        priv_key = keys.PrivateKey(priv_key_bytes)
        pub_key = priv_key.public_key
        d = private_key[2:]
        x = pub_key.to_hex()[2:66]
        y = pub_key.to_hex()[66:]

        ad = bytes.fromhex(d)
        d =  base64.urlsafe_b64encode((ad)).decode()[:-1]

        ax = bytes.fromhex(x)
        x =  base64.urlsafe_b64encode((ax)).decode()[:-1]

        ay = bytes.fromhex(y)
        y =  base64.urlsafe_b64encode((ay)).decode()[:-1]
        return json.dumps({"crv":"secp256k1","d":d,"kty":"EC","x": x,"y":y, "alg" :"ES256K-R",  "b64": False, "crit": ["b64"]})


def sign(credential, pvk):

    key = ethereum_to_jwk256kr(pvk)
    did = didkit.keyToDID("ethr",key )
    vm = didkit.keyToVerificationMethod("ethr", key)

    credential["issuer"] = did
    credential["issuanceDate"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": vm
    }

    credential = didkit.issueCredential(
        json.dumps(credential),
        didkit_options.__str__().replace("'", '"'),
        key)
    return credential

if __name__ == "__main__" :

    pvk = "0x7f1116bdb705f3e51a299a1fe04b619e0e2516258ef187946076b04151ece8a5"

    credential = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "id": "http://khgkjg/dddd",
            "type": ["VerifiableCredential", "IdentityCredential"],
            "credentialSubject": {
                "@context": ["https://schema.org/"],
                "id": "urn:uuid:123132313",
                "name" : "gggg",
                "familyName" : None,
                "givenName" : None,
                "gender" : None,
                "birthDate" : None,
                "address" : None,
                "telephone" : None,
                "email" : None,
                "image" : None
                },
            }

    credential = sign(credential, pvk)
    print(credential)


    key = ethereum_to_jwk256kr(pvk)
    verifmethod = didkit.keyToVerificationMethod("ethr", key)

    didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": verifmethod
    }
    print(didkit.verifyCredential(credential, didkit_options.__str__().replace("'", '"')))

