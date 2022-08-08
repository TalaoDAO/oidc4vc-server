import hashlib
from pyld import jsonld
from jwcrypto import jwk, jws
import base64
import base58
import json
from jwcrypto.common import json_encode
from datetime import datetime
import os

# for testuing purpose
"""
key =  json.dumps({"crv": "secp256k1", "d": "fxEWvbcF8-UaKZof4Ethng4lFiWO8YeUYHawQVHs6KU", "kty": "EC", "x": "uPSr7x3mgveGQ_xvuxO6CFIY6GG09ZsmngY5S2EixKk", "y": "mq7je_woNa3iMGoYWQ1uZKPjbDgDCskAbh12yuGAoKw", "alg": "ES256K"})
doc = {
  "@context": [
    "https://www.w3.org/2018/credentials/v1"
  ],
  "id": "urn:uuid:4efc62e3-c209-49ad-a81b-d2859cc2526c",
  "type": [
    "VerifiableCredential"
  ],
  "credentialSubject": {
    "id": "did:tz:tz2E4kuaB9zHa1C3LqNeZncvZogYjQsXxvxz"
  },
  "issuer": "did:key:z6Mkrrz9wDNQ79zuK7JYP......",
  "issuanceDate": "2021-11-29T21:34:01Z",
}

"""

#https://ec.europa.eu/digital-building-blocks/wikis/display/EBSIDOC/EBSI+DID+Method

def thumbprint(jwk) :
    JWK = json.dumps({"alg": "ES256K", "crv":"secp256k1","kty":"EC","use" : "sig", "x":jwk["x"],"y":jwk["y"]}).replace(" ","")
    m = hashlib.sha256()
    m.update(JWK.encode())
    return m.hexdigest()


def generate_lp_ebsi_did() :
    return  'did:ebsi:z' + base58.b58encode(b'\x01' + os.urandom(16)).decode()


def did_resolve(did, key) :
  if isinstance(key, str) :
    key = json.loads(key)
  did_doc = {
  "@context": "https://w3id.org/did/v1",
  "id": did,
  "verificationMethod": [
    {
      "id": did + '#' +  thumbprint(key),
      "type": "JsonWebKey2020",
      "controller": did,
      "publicKeyJwk": {
        "kty": "EC",
        "crv": "secp256k1",
        "x": key["x"],
        "y": key["y"],
        "alg": "ES256K"
      }
    }
  ],
  "authentication": [
    did + '#' +  thumbprint(key)
  ],
  "assertionMethod": [
    did + '#' +  thumbprint(key)
    ]
  }
  return json.dumps(did_doc)


def lp_sign(credential, key, did) :
  if isinstance(key, str) :
    key = json.loads(key)
  if isinstance(credential, str) :
    credential = json.loads(credential)
  proof= {
    #'@context':'https://w3id.org/security/v2',
    'type': 'EcdsaSecp256k1Signature2019',
    'created': datetime.now().replace(microsecond=0).isoformat() + "Z",
    "verificationMethod": did + '#' + thumbprint(key),
    'proofPurpose': 'assertionMethod'
  }
  
  h = {"alg":"ES256K","b64":False,"crit":["b64"]}
  jws_header = json.dumps(h).encode()

  normalized_doc   = jsonld.normalize(credential , {'algorithm': 'URDNA2015', 'format': 'application/n-quads'})
  normalized_proof = jsonld.normalize(proof, {'algorithm': 'URDNA2015', 'format': 'application/n-quads'})
  doc_hash         = hashlib.sha256()
  proof_hash       = hashlib.sha256()

  doc_hash.update(normalized_doc.encode('utf-8'))
  proof_hash.update(normalized_proof.encode('utf-8'))

  encodedHeader = base64.urlsafe_b64encode(jws_header)
  to_sign = encodedHeader + b'.' + proof_hash.digest() + doc_hash.digest()

  issuer_key = jwk.JWK(**key) 
  jwstoken = jws.JWS(to_sign)
  jwstoken.add_signature(issuer_key, None, json_encode({"alg": "ES256K"}))

  sig = json.loads(jwstoken.serialize())['signature']
  proof_jws =encodedHeader + b'..' + base64.urlsafe_b64encode(sig.encode())

  #TODO check that
  #proof['jws']  = proof_jws.decode()[:-2] 
  proof['jws']  = proof_jws.decode()

  try :
    del proof['@context']
  except :
    pass
  credential['proof'] = proof
  return json.dumps(credential)

# test
#did = generate_lp_ebsi_did()
#print( lp_sign(doc, key, did))