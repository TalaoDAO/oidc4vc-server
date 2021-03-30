import environment
import constante
import os
import didkit
import json
from authlib.jose import jwk
from components import privatekey
import base64


#key = didkit.generateEd25519Key()
#print('key Ed25519Key ', key)

#key = json.loads(didkit.generateEd25519Key())
#print(key)

#did = didkit.keyToDID("key", key)
#print('did = ', did)

#vm = didkit.keyToVerificationMethod('key', key)
#print('vm = ', vm)



from eth_keys import keys
from eth_utils import decode_hex
from jwcrypto import jwk
pvk = "0x7f1116bdb705f3e51a299a1fe04b619e0e2516258ef187946076b04151ece8a5"


#key = jwk.JWK.generate(kty="EC", crv="secp256k1",  alg="ES256K-R",  b64 = False, crit = ["b64"])
#key = jwk.JWK.generate(kty="OKP", crv="Ed25519")
#key=key.export_private()

#print(key)

def jwk_to_ethereum(jwk) :
        jwk = json.loads(jwk)
        private_key = "0x" + base64.urlsafe_b64decode(jwk["d"] + '=' * (4 - len(jwk["d"]) % 4)).hex()
        priv_key_bytes = decode_hex(private_key)
        priv_key = keys.PrivateKey(priv_key_bytes)
        pub_key = priv_key.public_key
        public_key = pub_key.to_hex()
        address = pub_key.to_checksum_address()
        return private_key, public_key, address


def ethereum_to_jwk256kr(private_key) :
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

        return json.dumps({"crv":"secp256k1","d":d,"kty":"EC","x": x,"y":y, "alg" :"ES256K-R",  "b64": False, "crit": ["b64"]})

key = ethereum_to_jwk256kr(pvk)
did = didkit.keyToDID("ethr",key )
print("did = ", did)


verifmethod = didkit.keyToVerificationMethod("ethr", key)
print("verifimethod = ", verifmethod)

credential = { "@context": "https://www.w3.org/2018/credentials/v1",
                "type": ["VerifiableCredential"],
                 "issuer" : did,
                   "issuanceDate": "2020-08-19T21:41:50Z",
                "credentialSubject": {
                "id": "did:example:d23dd687a7dc6787646f2eb98d0",
               }
                }

didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": verifmethod
    }

credential = didkit.issueCredential(
        credential.__str__().replace("'", '"'),
        didkit_options.__str__().replace("'", '"'),
        key)

print(credential)

print(didkit.verifyCredential(credential, didkit_options.__str__().replace("'", '"')))

