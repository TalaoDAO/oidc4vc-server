import json
import hashlib
import base64
import base58
from eth_keys import keys
from eth_utils import decode_hex
import didkit
from pytezos.crypto.encoding import base58_encode
from pytezos.crypto.key import Key

import logging
logging.basicConfig(level=logging.INFO)


"""
Pour did:ethr et did:tz(2) utilser ES256K-R pour avoir la suite de signature "EcdsaSecp256k1RecoverySignature2020"
pour did:web utiliser ES256K et la suite de signature EcdsaSecp256k1VerificationKey2019 with  "publicKeyJwk" : {}
"""

def ethereum_pvk_to_DID(pvk, method) :
    if method in ['ethr', 'tz'] :
        return didkit.key_to_did(method, ethereum_to_jwk256kr(pvk))
    elif method == 'key' :
        return didkit.key_to_did(method, ethereum_to_jwk256k(pvk))
    else :
        logging.error('DID method not supported')
        return None

def ethereum_pvk_to_address(pvk) :
    priv_key_bytes = decode_hex(pvk)
    priv_key = keys.PrivateKey(priv_key_bytes)
    pub_key = priv_key.public_key
    return pub_key.to_checksum_address()


def ethereum_pvk_to_pub(pvk) :
    priv_key_bytes = decode_hex(pvk)
    priv_key = keys.PrivateKey(priv_key_bytes)
    return priv_key.public_key


def jwk_to_ethereum(jwk) :
    if isinstance(jwk, str) :
        jwk = json.loads(jwk)
    private_key = "0x" + base64.urlsafe_b64decode(jwk["d"] + '=' * (4 - len(jwk["d"]) % 4)).hex()
    priv_key_bytes = decode_hex(private_key)
    priv_key = keys.PrivateKey(priv_key_bytes)
    pub_key = priv_key.public_key
    public_key = pub_key.to_hex()
    address = pub_key.to_checksum_address()
    return private_key, public_key, address


def jwk_to_tezos(jwk) :
    if isinstance(jwk, str) :
        jwk = json.loads(jwk)
    if jwk['crv'] == 'secp256k1' :
        prefix = b'spsk'
    elif jwk['crv'] == "Ed25519" :
        prefix = b'edsk'
    else :
        logging.error('curve not implemented')
        return None
    # Decode the key (d) from b64 to hex and complete to have a 32 bytes key with "=" at the end
    private_key = base64.urlsafe_b64decode(jwk["d"] + '=' * (4 - len(jwk["d"]) % 4)).hex()
    # add the prefix and encode in b58 
    tez_pvk = base58_encode(bytes.fromhex(private_key), prefix = prefix)
    # Get public key and address from provate key
    sk = Key.from_encoded_key(tez_pvk.decode())
    pbk = sk.public_key()
    pkh = sk.public_key_hash()
    return tez_pvk, pbk, pkh


def ethereum_to_tezos(eth_pvk) :
    """
    @param : eth_pvk = "0X....."
    """
    tez_pvk = base58_encode(bytes.fromhex(eth_pvk[2:]), prefix = b'spsk')
    sk = Key.from_encoded_key(tez_pvk.decode())
    pbk = sk.public_key()
    pkh = sk.public_key_hash()
    return tez_pvk.decode(), pbk, pkh


def ethereum_to_jwk256k(private_key) :
    """ pour did:key """
    return _ethereum_to_jwk256k(private_key, "ES256K")


def ethereum_to_jwk256kr(private_key) :
    """ pour did:ethr et did:tz2  
    return string 
    """
    return _ethereum_to_jwk256k(private_key, "ES256K-R")


def ethereum_to_jwk(private_key, method) :
    if method == "web" :
        return  ethereum_to_jwk256k(private_key)
    else :
        return ethereum_to_jwk256kr(private_key)


def _ethereum_to_jwk256k(private_key, alg) :
    """
    return json
    """
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

    return json.dumps({"crv":"secp256k1","d":d,"kty":"EC","x":x,"y":y,"alg":alg})


def thumbprint(jwk) :
    """
    Curve secp256k1
    return hex string without 0x
    https://www.rfc-editor.org/rfc/rfc7638.html
    """
    if isinstance(jwk, str) :
        jwk = json.loads(jwk)
    if jwk["crv"] != "secp256k1" :
        print("error key type")
        return False
    JWK = json.dumps({"crv":"secp256k1",
                    "kty":"EC",
                    "x":jwk["x"],
                    "y":jwk["y"]
                    }).replace(" ","")
    m = hashlib.sha256()
    m.update(JWK.encode())
    return m.hexdigest()


def eth_pub_key_to_jwk(pub_key) :
    """
    return json
    """
    if pub_key[:2] == "0x" :
        pub_key = pub_key[2:]
    x = pub_key[:64]
    y = pub_key[64:]
    ax = bytes.fromhex(x)
    x =  base64.urlsafe_b64encode((ax)).decode()[:-1]
    ay = bytes.fromhex(y)
    y =  base64.urlsafe_b64encode((ay)).decode()[:-1]
    return json.dumps({"crv":"secp256k1","kty":"EC","x": x,"y":y}).replace(" ", "")


def ebsi_from_jwk(jwk) :
    """
    for legal person only version = b'\x02' 
    subject_identier = thumbprint of public key
    reference https://ec.europa.eu/digital-building-blocks/wikis/display/EBSIDOC/EBSI+DID+Method
    """
    if isinstance(jwk, str) :
        jwk = json.loads(jwk)
    ebsi_did = 'z' + base58.b58encode(b'\x02' + bytes.fromhex(thumbprint(jwk))).decode()
    ebsi_verificationMethod = ebsi_did + '#keys-1'
    did_doc = {
        "@context": "https://w3id.org/did/v1",
        "id": ebsi_did,
        "verificationMethod": [
        {
            "id": ebsi_verificationMethod,
            "type": "EcdsaSecp256k1VerificationKey2019",
            "controller": ebsi_did,
            "publicKeyJwk": {
                "kty": "EC",
                "crv": "secp256k1",
                "x": jwk["x"],
                "y": jwk["y"],
            }
        }
        ],
        "authentication": [ebsi_verificationMethod],
        "assertionMethod": [ebsi_verificationMethod]
    }
    return ebsi_did, ebsi_verificationMethod, did_doc