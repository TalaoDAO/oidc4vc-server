import json
import base64
from eth_keys import keys
from eth_utils import decode_hex
from jwcrypto import jwk
import didkit
from pytezos.crypto.encoding import base58_encode
from pytezos.crypto.key import Key



"""
Pour did:ethr et did:tz(2) utilser ES256K-R pour avoir la suite de signature "EcdsaSecp256k1RecoverySignature2020"

pour did:web utiliser ES256K et la suite de signature EcdsaSecp256k1VerificationKey2019 with  "publicKeyJwk" : {}


"""

def ethereum_pvk_to_DID(pvk, method) :
    if method in ['ethr', 'tz'] :
        return didkit.keyToDID(method, ethereum_to_jwk256kr(pvk))
    else :
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
    jwk = json.loads(jwk)
    private_key = "0x" + base64.urlsafe_b64decode(jwk["d"] + '=' * (4 - len(jwk["d"]) % 4)).hex()
    priv_key_bytes = decode_hex(private_key)
    priv_key = keys.PrivateKey(priv_key_bytes)
    pub_key = priv_key.public_key
    public_key = pub_key.to_hex()
    address = pub_key.to_checksum_address()
    return private_key, public_key, address


def jwk_to_tezos(jwk) :
    """
    jwk is string
    must be and ethereum address
    """
    if json.loads(jwk)['crv'] == 'secp256k1' :
        eth_pvk = jwk_to_ethereum(jwk)[0]
        tez_pvk = base58_encode(bytes.fromhex(eth_pvk[2:]), prefix = b'spsk')
        sk = Key.from_encoded_key(tez_pvk.decode())
        pbk = sk.public_key()
        address = sk.public_key_hash()
        return tez_pvk, pbk, address
    else :
        print('not implemented')
        return None


def ethereum_to_tezos(eth_pvk) :
    """
    @param : eth_pvk = "0X....."
    """
    tez_pvk = base58_encode(bytes.fromhex(eth_pvk[2:]), prefix = b'spsk')
    sk = Key.from_encoded_key(tez_pvk.decode())
    pbk = sk.public_key()
    address = sk.public_key_hash()
    return tez_pvk.decode(), pbk, address


def ethereum_to_jwk256k(private_key) :
    return _ethereum_to_jwk256k(private_key, "ES256K")


def ethereum_to_jwk256kr(private_key) :
    """ pour did:ethr et did:tz2  """
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

    return json.dumps({"crv":"secp256k1","d":d,"kty":"EC","x": x,"y":y, "alg" :alg})