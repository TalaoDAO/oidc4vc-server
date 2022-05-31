import hashlib
import nacl.signing
from nacl.signing import SigningKey
import nacl.encoding
from pyld import jsonld
from pyld.jsonld import JsonLdProcessor
#from jwcrypto import jwk
import base64
import json


#key = jwk.JWK.generate(kty="OKP", crv="Ed25519")
key = {"kty":"OKP","crv":"Ed25519","x":"uGA3B27sbk3MSz9cWunA7SK8Tg-nK9_BERN-C9UqlnY","d":"qsVvJ9AXveqqDajkiL9_98_JjrFLFMM8teuX_Lj_1hI"}
#key=json.loads(key.export_private())
#print(key)
mykey = base64.urlsafe_b64decode(key["d"] + '=' * (4 - len(key["d"]) % 4)).hex()
#print('ed25519 priv key = ', mykey)

# Generate a new random signing key
signing_key = SigningKey.generate()
verify_key = signing_key.verify_key

print("signing key = ", signing_key.encode().hex())
print("verify key = ", verify_key.encode().hex())

public_key = verify_key.encode().hex()


mykey = signing_key.encode().hex()
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

proof= {
    '@context':'https://w3id.org/security/v2',
    'type': 'Ed25519Signature2018',
    'created': '2020-06-03T01:05:47Z',
    "verificationMethod": "did:key:z6Mkrrz9wDNQ79zuK7JYPDYS7kqs683Q5hxpJrk9vkCERUzH#z6Mkrrz9wDNQ79zuK7JYPDYS7kqs683Q5hxpJrk9vkCERUzH",
    'proofPurpose': 'assertionMethod'
  }


jws_header       = b'{"alg":"EdDSA","b64":false,"crit":["b64"]}'
#privkey          = '826CB6B9EA7C0752F78F600805F9005ACB66CAA340B0F5CFA6BF41D470D49475'
privkey = mykey
normalized_doc   = jsonld.normalize(doc , {'algorithm': 'URDNA2015', 'format': 'application/n-quads'})
normalized_proof = jsonld.normalize(proof, {'algorithm': 'URDNA2015', 'format': 'application/n-quads'})
doc_hash         = hashlib.sha256()
proof_hash       = hashlib.sha256()

doc_hash.update(normalized_doc.encode('utf-8'))
proof_hash.update(normalized_proof.encode('utf-8'))

signing_key   = nacl.signing.SigningKey(privkey,nacl.encoding.HexEncoder)
encodedHeader = nacl.encoding.URLSafeBase64Encoder.encode(jws_header)
to_sign       = encodedHeader + b'.' + proof_hash.digest() + doc_hash.digest()
signed_data   = signing_key.sign(to_sign)
jws           = encodedHeader + b'..' + nacl.encoding.URLSafeBase64Encoder.encode(signed_data.signature)
proof['jws']  = jws.decode()[:-2]
del proof['@context']
doc['proof'] = proof
print(doc)

result = verify_key.verify(signed_data)
print(result)
# Alter the signed message text
#forged = signed_data[:-1] + bytes([int(signed_data[-1]) ^ 1])
# Will raise nacl.exceptions.BadSignatureError, since the signature check
# is failing
#verify_key.verify(forged)