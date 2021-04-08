import json
import base64
from eth_keys import keys
from eth_utils import decode_hex
from jwcrypto import jwk
from datetime import datetime
import requests
import didkit
import logging
logging.basicConfig(level=logging.INFO)

class ClientWebResolver:
    def __init__(self, config):
        pass

    def resolve(self, did):
        lines = ["https://uniresolver.io/1.0/identifiers"]

        try:
            for line in lines:
                if not line.endswith('/'):
                    line += '/'
                url = line + did
                httpResponse = requests.get(url) 
                if httpResponse.status_code == 200:
                    return httpResponse.json()
            raise TypeError
        except TypeError:
             print("All web services tested. Please add a working web resolver to the config file and try again.")

    def modifier(self, did):
        pass

"""
webResolver = ClientWebResolver("")
response = webResolver.resolve(did)
print(response)
"""


def ethereum_pvk_to_DID(pvk, method, address=None) :
    if not method :
        method = 'ethr'
    if method == 'web' and address :
        return "did:web:talao.co:" + address
    key = ethereum_to_jwk256kr(pvk)
    return didkit.keyToDID(method,key)

def ethereum_pvk_to_address(pvk) :
    priv_key_bytes = decode_hex(pvk)
    priv_key = keys.PrivateKey(priv_key_bytes)
    pub_key = priv_key.public_key
    return pub_key.to_checksum_address()

def jwk_to_ethereum(jwk) :
    jwk = json.loads(jwk)
    private_key = "0x" + base64.urlsafe_b64decode(jwk["d"] + '=' * (4 - len(jwk["d"]) % 4)).hex()
    priv_key_bytes = decode_hex(private_key)
    priv_key = keys.PrivateKey(priv_key_bytes)
    pub_key = priv_key.public_key
    public_key = pub_key.to_hex()
    address = pub_key.to_checksum_address()
    return private_key, public_key, address

def ethereum_to_jwk256k(private_key) :
    return _ethereum_to_jwk256k(private_key, "ES256K")

def ethereum_to_jwk256kr(private_key) :
    return _ethereum_to_jwk256k(private_key, "ES256K-R")

def ethereum_to_jwk(private_key, method) :
    if method == "web" :
        return  ethereum_to_jwk256k(private_key)
    else :
        return ethereum_to_jwk256kr(private_key)

def _ethereum_to_jwk256k(private_key, alg) :
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