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
from .helpers import jwk_to_ethereum, ethereum_to_jwk256kr, ethereum_pvk_to_address, ethereum_to_jwk256k


def sign(credential, pvk, method="ethr"):
    """
    @method : str
        default is ethr -> curve secp256k1 and "alg" :"ES256K-R"
        tz (tz2) -> curve  secp256k1 and "alg" :"ES256K-R"
        web  -> curve secp256k1 and "alg" :"ES256K"
    @credential is dict
    return is str
    Both curve secp256k1 and "alg" :"ES256K-R"
    """
    if not method :
        method = 'ethr'
    if method == 'web' :
        key = ethereum_to_jwk256k(pvk)
        address = ethereum_pvk_to_address(pvk)
        did = 'did:talao:' + address
        vm = didkit.keyToVerificationMethod(method, key)
    else :
        key = ethereum_to_jwk256kr(pvk)
        did = didkit.keyToDID(method,key )
        vm = didkit.keyToVerificationMethod(method, key)


    print('did = ', did)
    print('vm = ', vm)

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
