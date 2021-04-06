"""
method did:eth
https://github.com/decentralized-identity/ethr-did-resolver/blob/master/doc/did-method-spec.md
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
from .helpers import jwk_to_ethereum, ethereum_to_jwk256kr


def sign(credential, pvk, method="ethr"):
    """
    @method str
        default is is ethr
        tz (tz2)
    @credential is dict
    return is str
    Both curve secp256k1 and "alg" :"ES256K-R"
    """
    if not method :
        method = 'ethr'
    key = ethereum_to_jwk256kr(pvk)
    did = didkit.keyToDID(method,key )
    vm = didkit.keyToVerificationMethod(method, key)

    credential["issuer"] = did
    credential["issuanceDate"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": vm
    }
    return didkit.issueCredential(
            #credential.__str__().replace("'", '"'),
            json.dumps(credential, ensure_ascii=False),
            didkit_options.__str__().replace("'", '"'),
            key)


if __name__ == "__main__" :
    import uuid

    method = "tz"

    pvk = "0x7f1116bdb705f3e51a299a1fe04b619e0e2516258ef187946076b04151ece8a5"
    key = ethereum_to_jwk256kr(pvk)
    did = didkit.keyToDID(method,key)

    credential= json.load(open('/home/thierry/Talao/verifiable_credentials/experience.jsonld', 'r'))

    credential['credentialSubject']["id"] =  "2020-08-19T21:41:50Z"
    credential['id'] = "123123123131321:lkjh:mh"
    credential["issuer"] = did
    credential["issuanceDate"] = "2020-08-19T21:41:50Z"

    credential = sign(credential, pvk, method=method)
    print(json.dumps(json.loads(credential), indent=4))

    key = ethereum_to_jwk256kr(pvk)
    verifmethod = didkit.keyToVerificationMethod(method, key)

    didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": verifmethod
        }

    print(didkit.verifyCredential(credential, didkit_options.__str__().replace("'", '"')))


