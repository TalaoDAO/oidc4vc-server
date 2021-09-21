import didkit
import json
from jwcrypto import jwk
import logging
logging.basicConfig(level=logging.INFO)
from .helpers import ethereum_to_jwk256kr, ethereum_to_jwk256k




def sign(credential, pvk, did, rsa=None, didkit_options=None):
    """ sign credential for did:ethr, did:tz, did:web

    @did is str
        ethr (default method) -> curve secp256k1 and "alg" :"ES256K-R"
        tz (tz2) -> curve  secp256k1 with "alg" :"ES256K-R"
        web  -> curve secp256k1 with "alg" :"ES256K" or RSA
    
    @didkit_options is dict

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
    
    elif method == 'key' :
        key = ethereum_to_jwk256k(pvk)
        vm = didkit.key_to_verification_method('key', key)

    else :
        logging.error('method not supported by Talao')
        return None
  
    if not didkit_options :
        didkit_options = {
            "proofPurpose": "assertionMethod",
            "verificationMethod": vm
        }

    signed_credential = didkit.issue_credential(json.dumps(credential,ensure_ascii=False),
                                    didkit_options.__str__().replace("'", '"'),
                                     key)

    # verify credential before leaving
    result =  json.loads(didkit.verify_credential(signed_credential, '{}'))
    print('test signature = %s', result)

    return signed_credential

def verify (credential) :
    """
    credential  str
    return list
    """
    try :
        result = didkit.verify_credential(credential, '{}')
    except:
        return "Failed : JSON-LD malformed"

    if not json.loads(result)['errors'] :
        return "Signature verified : " + result
    else :
        return "Signature rejected : " + result
