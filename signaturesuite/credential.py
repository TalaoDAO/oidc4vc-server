import didkit
import json
from jwcrypto import jwk
import logging
logging.basicConfig(level=logging.INFO)
from .helpers import ethereum_to_jwk256kr, ethereum_pvk_to_address, ethereum_to_jwk256k

def sign(credential, pvk, method="ethr", rsa=None):
    """ sign credential for did:ethr, did:tz and did:web

    @method is str
        ethr (default method) -> curve secp256k1 and "alg" :"ES256K-R"
        tz (tz2) -> curve  secp256k1 with "alg" :"ES256K-R"
        web  -> curve secp256k1 with "alg" :"ES256K" or RSA 
    @credential is dict
    return is str

    """
    if not method :
        method = 'ethr'
    if method == 'web' and not rsa :
        key = ethereum_to_jwk256k(pvk)
        did = 'did:web:talao.co:' + ethereum_pvk_to_address(pvk)
        vm = did + "#key-1"
    elif method == 'web' and rsa :
        key = jwk.JWK.from_pem(rsa.encode())
        key = key.export_private()
        #del key['kid']
        did = 'did:web:talao.co:' + ethereum_pvk_to_address(pvk)
        vm = did + "#key-2"
    else :
        key = ethereum_to_jwk256kr(pvk)
        did = didkit.keyToDID(method,key )
        vm = didkit.keyToVerificationMethod(method, key)

    logging.info('key = %s', key)
    logging.info('did = %s', did)
    logging.info('vm = %s', vm)

    didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": vm
    }
    return didkit.issueCredential(
            #credential.__str__().replace("'", '"'),
            json.dumps(credential, ensure_ascii=False),
            didkit_options.__str__().replace("'", '"'),
            key)
