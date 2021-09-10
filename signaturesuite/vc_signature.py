import didkit
import json
from jwcrypto import jwk
import logging
logging.basicConfig(level=logging.INFO)
from .helpers import ethereum_to_jwk256kr, ethereum_pvk_to_address, ethereum_to_jwk256k




def sign(credential, pvk, did, rsa=None, options=None):
    """ sign credential for did:ethr, did:tz, did:web

    @method is str
        ethr (default method) -> curve secp256k1 and "alg" :"ES256K-R"
        tz (tz2) -> curve  secp256k1 with "alg" :"ES256K-R"
        web  -> curve secp256k1 with "alg" :"ES256K" or RSA

    @credential is dict
    return is str

    """
    method = did.split(':')[1]

    if method == 'web' and not rsa :
        key = ethereum_to_jwk256k(pvk)
        vm = did + "#key-1"

    elif method == 'web' and rsa :
        key = jwk.JWK.from_pem(rsa.encode())
        key = key.export_private()
        vm = did + "#key-2"

    elif method == 'ethr' :
        key = ethereum_to_jwk256kr(pvk)
        vm = did + "#controller"

    elif method == 'tz' :
        key = ethereum_to_jwk256kr(pvk)
        vm = did + "#blockchainAccountId"

    else :
        logging.error('method not supported')
        return None

    if not options :
        didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": vm
        }
    else :
        didkit_options = options

    signed_credential = didkit.issueCredential(json.dumps(credential,ensure_ascii=False),
                                    didkit_options.__str__().replace("'", '"'),
                                     key)

    # verify credential before leaving
    test =  json.loads(didkit.verifyCredential(signed_credential, '{}'))
    logging.info('test signature = %s', test)

    return signed_credential

def verify (credential) :
    """
    credential  str
    return list
    """
    try :
        result = didkit.verifyCredential(credential, '{}')
    except:
        return "Failed : JSON-LD malformed"

    if not json.loads(result)['errors'] :
        return "Signature verified : " + result
    else :
        return "Signature rejected : " + result
