import hashlib
from pyld import jsonld
from jwcrypto import jwk, jws, jwt
import base64
import base58
import json
from jwcrypto.common import json_encode
from datetime import datetime
import os
import logging
logging.basicConfig(level=logging.INFO)

"""
 https://ec.europa.eu/digital-building-blocks/wikis/display/EBSIDOC/EBSI+DID+Method
 VC/VP https://ec.europa.eu/digital-building-blocks/wikis/display/EBSIDOC/E-signing+and+e-sealing+Verifiable+Credentials+and+Verifiable+Presentations
 DIDS method https://ec.europa.eu/digital-building-blocks/wikis/display/EBSIDOC/EBSI+DID+Method
 supported signature : https://ec.europa.eu/digital-building-blocks/wikis/display/EBSIDOC/E-signing+and+e-sealing+Verifiable+Credentials+and+Verifiable+Presentations

alg value https://www.rfc-editor.org/rfc/rfc7518#page-6

   +--------------+-------------------------------+--------------------+
   | "alg" Param  | Digital Signature or MAC      | Implementation     |
   | Value        | Algorithm                     | Requirements       |
   +--------------+-------------------------------+--------------------+
   | RS256        | RSASSA-PKCS1-v1_5 using       | Recommended        |
   |              | SHA-256                       |                    |
   | RS384        | RSASSA-PKCS1-v1_5 using       | Optional           |
   |              | SHA-384                       |                    |
   | RS512        | RSASSA-PKCS1-v1_5 using       | Optional           |
   |              | SHA-512                       |                    |
   | ES256        | ECDSA using P-256 and SHA-256 | Recommended+       |
   | ES384        | ECDSA using P-384 and SHA-384 | Optional           |
   | ES512        | ECDSA using P-521 and SHA-512 | Optional           |
   | PS256        | RSASSA-PSS using SHA-256 and  | Optional           |
   |              | MGF1 with SHA-256             |                    |
   | PS384        | RSASSA-PSS using SHA-384 and  | Optional           |
   |              | MGF1 with SHA-384             |                    |
   | PS512        | RSASSA-PSS using SHA-512 and  | Optional           |
   |              | MGF1 with SHA-512             |                    |
   +--------------+-------------------------------+--------------------+
"""

def alg(key) :
  key = json.loads(key) if isinstance(key, str) else key
  if key['kty'] == 'EC' :
    if key['crv'] == "secp256k1" :
      alg = 'ES256K' 
    elif key['crv'] == "P-256" :
      alg = "ES256"
    elif key['crv'] == "P-384" :
      alg = "ES384"
    elif key['crv'] == "P-521" :
      alg = "ES512"
    else :
      raise Exception ("Curve not supported")
    return alg
  elif key['kty'] == 'RSA' :
    alg = "RS256"
  else :
    raise Exception ("Key type not supported")

def sign_jwt_vc(vc, issuer_vm , key, issuer_did, wallet_did, nonce) :
    """
    https://jwcrypto.readthedocs.io/en/latest/jwk.html
    https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims

    """
    key = json.loads(key) if isinstance(key, str) else key
    vc = json.loads(vc) if isinstance(vc, str) else vc
    issuer_key = jwk.JWK(**key) 
    header = {
        "typ" :"JWT",
        "kid": issuer_vm,
        "alg": alg(key)
    }
    payload = {
        "iss" : issuer_did,
        "nonce" : nonce,
        "iat": datetime.timestamp(datetime.now()),
        "nbf" : datetime.timestamp(datetime.now()),
        "jti" : vc['id'],
        "exp": datetime.timestamp(datetime.now()) + 1000,
        "sub" : wallet_did,
        "vc" : vc
    }  
    token = jwt.JWT(header=header,claims=payload, algs=[alg(key)])
    token.make_signed_token(issuer_key)
    return token.serialize()


def verif_proof_of_key(signer_pub_key, token) :
  # https://jwcrypto.readthedocs.io/en/latest/jwt.html#jwcrypto.jwt.JWT.validate
  a =jwt.JWT.from_jose_token(token)
  issuer_key = jwk.JWK(**signer_pub_key) 
  a.validate(issuer_key)
  return


def build_proof_of_key_ownership(key, kid, aud, signer_did, nonce) :
  key = json.loads(key) if isinstance(key, str) else key
  signer_key = jwk.JWK(**key) 
  signer_pub_key = signer_key.export(private_key=False, as_dict=True)
  header = {
        "typ" :"JWT",
        "alg": alg(key),
        "jwk" : signer_pub_key, # for natural person
        "kid" : kid
  }
  payload = {
    "iss" : signer_did,
    "nonce" : nonce,
    "iat": datetime.timestamp(datetime.now()),
    "aud" : aud
  }  
  token = jwt.JWT(header=header,claims=payload, algs=[alg(key)])
  token.make_signed_token(signer_key)
  return token.serialize()


def thumbprint(key) :
    key = json.loads(key) if isinstance(key, str) else key
    KEY = jwk.JWK(**key) 
    return KEY.thumbprint()


def generate_lp_ebsi_did() :
    """
    for legal person as issuer
    """
    return  'did:ebsi:z' + base58.b58encode(b'\x01' + os.urandom(16)).decode()


def generate_np_did(key) :
    """
    for natural person / wallet
    """
    key = json.loads(key) if isinstance(key, str) else key
    return  'did:ebsi:z' + base58.b58encode(b'\x02' + bytes.fromhex(thumbprint(key))).decode()


def verification_method(did, key) : # = kid
    key = json.loads(key) if isinstance(key, str) else key
    return did + "#" + thumbprint(key)


def did_resolve(did, key) :
  key = json.loads(key) if isinstance(key, str) else key
  did_document = {
    "@context": "https://w3id.org/did/v1",
    "id": did,
    "verificationMethod": [
      {
        "id": did + '#' +  thumbprint(key),
        "type": "JsonWebKey2020",
        "controller": did,
        "publicKeyJwk": {
          "kty": key['kty'],
          "crv": key['crv'],
          "x": key["x"],
          "y": key["y"],
          "alg": alg(key)
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
  return json.dumps(did_document)



# JSON-LD sign
def sign_jsonld_vc(credential, key, did) :
  key = json.loads(key) if isinstance(key, str) else key
  if isinstance(credential, str) :
    credential = json.loads(credential)
  proof= {
    #'@context':'https://w3id.org/security/v2',
    'type': 'EcdsaSecp256k1Signature2019',
    'created': datetime.now().replace(microsecond=0).isoformat() + "Z",
    "verificationMethod": did + '#' + thumbprint(key),
    'proofPurpose': 'assertionMethod'
  }
  h = {"alg":alg(key),"b64":False,"crit":["b64"]}
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
  jwstoken.add_signature(issuer_key, None, json_encode({"alg": alg(key)}))

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




# TEST VECTORS

key1 =  {
  'crv': 'P-256',
  'd': 'gifPl6onSK0UUcV02_FtnmPY9NEQGP2j2EUIKTDhyH8',
  'kty': 'EC',
  'x': 'zBiQktwhMspVmI14Cy0jn2mSiYi2mbXKG1ZQqt-QzKo',
  'y': 'A22Fda-NX_yTAbXfAWudpOFMJEpipNAw1y7iTWDMG78'
}

"""
did =  did:ebsi:zr1BvU3y9ybxc6ViZPoQDwYfjWGtKrMyge2ebVUkFneGh
verification method = kid  =  did:ebsi:zr1BvU3y9ybxc6ViZPoQDwYfjWGtKrMyge2ebVUkFneGh#d819023d5dd21163bfa3b943282b75c0d211b007f9adb080aca1377cf0396a4a
DID Document  =  {'@context': 'https://w3id.org/did/v1', 'id': 'did:ebsi:zr1BvU3y9ybxc6ViZPoQDwYfjWGtKrMyge2ebVUkFneGh', 'verificationMethod': [{'id': 'did:ebsi:zr1BvU3y9ybxc6ViZPoQDwYfjWGtKrMyge2ebVUkFneGh#d819023d5dd21163bfa3b943282b75c0d211b007f9adb080aca1377cf0396a4a', 'type': 'JsonWebKey2020', 'controller': 'did:ebsi:zr1BvU3y9ybxc6ViZPoQDwYfjWGtKrMyge2ebVUkFneGh', 'publicKeyJwk': {'kty': 'EC', 'crv': 'P-256', 'x': 'zBiQktwhMspVmI14Cy0jn2mSiYi2mbXKG1ZQqt-QzKo', 'y': 'A22Fda-NX_yTAbXfAWudpOFMJEpipNAw1y7iTWDMG78', 'alg': 'ES256'}}], 'authentication': ['did:ebsi:zr1BvU3y9ybxc6ViZPoQDwYfjWGtKrMyge2ebVUkFneGh#d819023d5dd21163bfa3b943282b75c0d211b007f9adb080aca1377cf0396a4a'], 'assertionMethod': ['did:ebsi:zr1BvU3y9ybxc6ViZPoQDwYfjWGtKrMyge2ebVUkFneGh#d819023d5dd21163bfa3b943282b75c0d211b007f9adb080aca1377cf0396a4a']}

"""
key2 =  {'crv': 'P-256', 'd': '-5s6EQzg8IJ7ZSNAsNcBZmXiT697L_RIyNM_b6KugCA', 'kty': 'EC', 'x': 'Q9NeTcpgzLwavEDZ5xAnK1hCpUzJq6Ghof1Q2sdhou8', 'y': 'y4XrDLh-qK5y3m2WHO-SV7Q_FFTYS2kKfG67QUYhieo'}
"""
did =  did:ebsi:zdz4PSgCAyrQKmChiLJL659imLvTx9tm3zSWcoaWnQEXk
verification method = kid  =  did:ebsi:zdz4PSgCAyrQKmChiLJL659imLvTx9tm3zSWcoaWnQEXk#2582aa43a137ca231679e01c2128ecf85d396e43332810a8befdc2e4d4625c93
DID Document  =  {'@context': 'https://w3id.org/did/v1', 'id': 'did:ebsi:zdz4PSgCAyrQKmChiLJL659imLvTx9tm3zSWcoaWnQEXk', 'verificationMethod': [{'id': 'did:ebsi:zdz4PSgCAyrQKmChiLJL659imLvTx9tm3zSWcoaWnQEXk#2582aa43a137ca231679e01c2128ecf85d396e43332810a8befdc2e4d4625c93', 'type': 'JsonWebKey2020', 'controller': 'did:ebsi:zdz4PSgCAyrQKmChiLJL659imLvTx9tm3zSWcoaWnQEXk', 'publicKeyJwk': {'kty': 'EC', 'crv': 'P-256', 'x': 'Q9NeTcpgzLwavEDZ5xAnK1hCpUzJq6Ghof1Q2sdhou8', 'y': 'y4XrDLh-qK5y3m2WHO-SV7Q_FFTYS2kKfG67QUYhieo', 'alg': 'ES256'}}], 'authentication': ['did:ebsi:zdz4PSgCAyrQKmChiLJL659imLvTx9tm3zSWcoaWnQEXk#2582aa43a137ca231679e01c2128ecf85d396e43332810a8befdc2e4d4625c93'], 'assertionMethod': ['did:ebsi:zdz4PSgCAyrQKmChiLJL659imLvTx9tm3zSWcoaWnQEXk#2582aa43a137ca231679e01c2128ecf85d396e43332810a8befdc2e4d4625c93']}
"""

key3 =  {"crv": "secp256k1", "d": "fxEWvbcF8-UaKZof4Ethng4lFiWO8YeUYHawQVHs6KU", "kty": "EC", "x": "uPSr7x3mgveGQ_xvuxO6CFIY6GG09ZsmngY5S2EixKk", "y": "mq7je_woNa3iMGoYWQ1uZKPjbDgDCskAbh12yuGAoKw", "alg": "ES256K"}



# EBSI TEST VECTORS

alice_key = {
  "kty" : "EC",
  "d" : "d_PpSCGQWWgUc1t4iLLH8bKYlYfc9Zy_M7TsfOAcbg8",
  "use" : "sig",
  "crv" : "P-256",
  "x" : "ngy44T1vxAT6Di4nr-UaM9K3Tlnz9pkoksDokKFkmNc",
  "y" : "QCRfOKlSM31GTkb4JHx3nXB4G_jSPMsbdjzlkT_UpPc",
  "alg" : "ES256",
}

alice_DID = "did:ebsi:znxntxQrN369GsNyjFjYb8fuvU7g3sJGyYGwMTcUGdzuy"



KEY_DICT = {"crv":"P-256",
            "d":"ZpntMmvHtDxw6przKSJY-zOHMrEZd8C47D3yuqAsqrw",
            "kty":"EC",
            "x":"NB1ylMveV4_PPYtx9KYEjoS1WWA8qN33SJav9opWTaM",
            "y":"UtOG2jR3NHadMMJ7wdYEq5_nHJHVfcy7QPt_OBHhBrE"}


DID = "did:ebsi:zmSKef6zQZDC66MppKLHou9zCwjYE4Fwar7NSVy2c7aya"
KID =  "did:ebsi:zmSKef6zQZDC66MppKLHou9zCwjYE4Fwar7NSVy2c7aya#lD7U7tcVLZWmqECJYRyGeLnDcU4ETX3reBN3Zdd0iTU"


"""
key = jwk.JWK.generate(kty='EC', crv='P-256')
key = jwk.JWK.generate(kty='EC', crv='secp256k1')
my_key = json.loads(key.export(private_key=True))   #doctest: +ELLIPSIS
print(my_key)
print(did_ebsi(my_key))
print(verification_method_ebsi(my_key))
"""

KEY_DICT = {'crv': 'secp256k1',
             'd': 'dBE5MSwGh1ypjymY48CGv_FaFQHQUPaZ632rhFVpZNw',
              'kty': 'EC', 'x': 'liIvy6clecfH9riQNvs1VsX7m1bYmYZ2JsHhpPJjfgY',
               'y': 'j8Q9Xfa8MIY78JiEpzMrlJzYz2vTkJY183hJBLLcKiU'}

DID = "did:ebsi:zdzaNUxpxnvTzMw8Hfnr6kg3AgJP8cXwvvKQVb61vstF1"
KID = "did:ebsi:zdzaNUxpxnvTzMw8Hfnr6kg3AgJP8cXwvvKQVb61vstF1#JaSRRiETIVHdByAG3e9N7NQ7MPXIILd1_lfyPYUWJ7g"