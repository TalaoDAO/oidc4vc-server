import didkit
import json
from jwcrypto import jwk
import logging
logging.basicConfig(level=logging.INFO)
from .helpers import ethereum_to_jwk256kr, ethereum_to_jwk256k


def sign(credential, pvk, did, rsa=None, P256=None, Ed25519=None, didkit_options=None):
    """ sign credential for did:ethr, did:tz, did:web

    @did is str
        ethr (default method) -> curve secp256k1 and "alg" :"ES256K-R"
        tz (tz2) -> curve  secp256k1 with "alg" :"ES256K-R"
        web  -> curve secp256k1 with "alg" :"ES256K" or RSA(key-2), P256(key-3), Ed25519(key-4)
        key

    @P256 and Ed25519 are json string
    
    @didkit_options is dict

    @credential is dict
    return is str

    """
  
    method = did.split(':')[1]

    if method == 'web' and not rsa and not P256 and not Ed25519:
        key = ethereum_to_jwk256k(pvk)
        vm = did + "#key-1"

    elif method == 'web' and rsa :
        key = jwk.JWK.from_pem(rsa.encode())
        key = key.export_private()
        vm = did + "#key-2"
    
    elif method == 'web' and P256 :
        key = P256
        vm = did + "#key-3"
    
    elif method == 'web' and Ed25519 :
        key = Ed25519
        vm = did + "#key-4"

    elif method == 'ethr' :
        key = ethereum_to_jwk256kr(pvk)      
        vm = didkit.keyToVerificationMethod('ethr', key)

    elif method == 'tz'  :
        key = ethereum_to_jwk256kr(pvk)
        vm = didkit.keyToVerificationMethod('tz', key)
    
    elif method == 'key' :
        key = ethereum_to_jwk256k(pvk)
        vm = didkit.keyToVerificationMethod('key', key)

    else :
        logging.error('method not supported by Talao')
        return None
    if not didkit_options :
        didkit_options = {
            "proofPurpose": "assertionMethod",
            "verificationMethod": vm
        }
    logging.info('sign with did = %s' , did)
    logging.info('sign with key = %s' , key)
    logging.info('sign with vm = %s' , vm)
  
    signed_credential = didkit.issueCredential(json.dumps(credential,ensure_ascii=False),
                                    didkit_options.__str__().replace("'", '"'),
                                     key)
    # verify credential before leaving
    result =  json.loads(didkit.verifyCredential(signed_credential, '{}'))
    logging.info('test signature = %s', result)
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
