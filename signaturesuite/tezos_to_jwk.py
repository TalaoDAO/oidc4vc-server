

"""
From Tezos tz1 private key (Ed25519 curve) to JWK

"""
from datetime import datetime, timedelta
import uuid
import base58
import base64
import json
import didkit

# Tezos lib , we do not mind which one, just need to get the secret key, private key and address
from pytezos.crypto.key import Key

# This Input is taken from the Temple wallet through a QR code or a manual paste/coppy. It is en encoded secret key
temple_private_key = "edskRzfJzQnyKWr4qP4rUipDfTNCXJGxBW91m5HtgTYS92MmWo1tUge6nXkumkrNqDa767qPgqiJQaqNfmjebFJUc96JmuBLQn"
# For information : this the address read on Temple associated with the previous encoded secret key  -> tz1Q7zwo7fmRNyCL7jdz6hcPSsYukkWY66Q3

# Thank to the Tezos lib, one can also check that the address calculated from the encoded private key is the same as the one read on Temple
_key = Key.from_encoded_key(temple_private_key.encode())
secret_key = _key.secret_key()
public_key = _key.public_key()
#address =  _key.public_key_hash()

# we change the format of the private key and public key from Base58 to Base64
# one removes the first 4 bytes (prefix) and the 4 last bytes (checking digest)

# the secret key from base58 to base64 url safe
d_bytes =  base58.b58decode(secret_key.encode())[4:-4]
d = base64.urlsafe_b64encode(d_bytes)
# we do the same with the public key
x_bytes = base58.b58decode(public_key.encode())[4:-4]

x = base64.urlsafe_b64encode(x_bytes)
# bytes to string
d = d.decode()
x = x.decode()

# this is the final JWK for a Ed25519 tezos address (tz1)
JWK =  {
        "crv":"Ed25519",
        "d": d,
        "kty":"OKP",
        "x": x
        }
#print('JWK = ', JWK)




"""
####################### TEST

# one checks with didkit that everything is ok
DID = didkit.keyToDID('tz', json.dumps(JWK))
print('Tezos DID  = ', DID)
vm = didkit.keyToVerificationMethod('tz', json.dumps(JWK))
print("vm = ", vm)

# one setups a VC to sign and then to check the signature
DELAY = timedelta(seconds= 12*24*60*60)
credential = json.load(open('./verifiable_credentials/EmailPass.jsonld', 'r'))
credential["issuer"] = DID
credential['credentialSubject']['id'] = "did:tz:tz2E4kuaB9zHa1C3LqNeZncvZogYjQsXxvxz"
credential['issuanceDate'] = datetime.now().replace(microsecond=0).isoformat() + "Z"
credential['expirationDate'] = (datetime.now() +  DELAY).replace(microsecond=0).isoformat() + "Z"
credential['id'] = "urn:uuid:" + str(uuid.uuid4())
didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": vm,
        }
signed_credential =  didkit.issueCredential(
        json.dumps(credential),
        didkit_options.__str__().replace("'", '"'),
        json.dumps(JWK)
        )

result = didkit.verifyCredential(signed_credential, '{}')
print('signature check = ', result)

Test vectors 

edskRzfJzQnyKWr4qP4rUipDfTNCXJGxBW91m5HtgTYS92MmWo1tUge6nXkumkrNqDa767qPgqiJQaqNfmjebFJUc96JmuBLQn
JWK =  {'crv': 'Ed25519', 'd': 'rRsH4WNxjh6E_XzEBJxiBi-nsR1QPMINu6Ciri2XhZ8=', 'kty': 'OKP', 'x': 'ZfeZIUWmL61MbAqP9kPDfWBeqAZmV-josXNft__RkLI='}
did:tz:tz1Q7zwo7fmRNyCL7jdz6hcPSsYukkWY66Q3

edskRxpqPEttt82HJeWsxFKH4PGySjyJo2oX285PyCVEYgueZ3FUa81fcWprPhtx7nDb5FkZ3LNPLtVqL8wQhjxYh6rFpoE9oS
JWK =  {'crv': 'Ed25519', 'd': 'nxLS92GgP_7mEo_ZEiJhhiY6wB4YM2_JkboSl0YXWRY=', 'kty': 'OKP', 'x': '9DxX1rfCjP7dBO115_bQoVsYSWq1uo5Lw1F1OgU3png='}
did:tz:tz1NJrXkEhwcqNxkARvb44psCCb4VyJ4Qh1b

edskSBTjP6S9bUYtbmSW3EmdVK71Dt3fyk32FVyvKsAKvPTVeEMTYPPeVhZLVHdmWfqPbnNDxhjvnu9mAphHETciMmPktrKAcN
JWK =  {'crv': 'Ed25519', 'd': '_6i8-m3SDp1cpp1ghuiJlt2Nj2kMHiZY9IixqstJRuY=', 'kty': 'OKP', 'x': 'i4khU1t8RUpULxCf6ybA-Q3y0JClOHkNF4wNDuGxzDs='}
did:tz:tz1Ve9tKqvJLHdn412xorB1mA7g2FGMuYA2k

"""
