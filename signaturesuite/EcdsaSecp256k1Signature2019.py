
import didkit
import json
from authlib.jose import jwk
import base64
from eth_keys import keys
from eth_utils import decode_hex
from jwcrypto import jwk


key = jwk.JWK.generate(kty="EC", crv="secp256k1")

key=key.export_private()
print('jwk =', key)


d = json.loads(key)["d"]
private_key = "0x" + base64.urlsafe_b64decode(d + '=' * (4 - len(d) % 4)).hex()
print("private key = ", private_key)
priv_key_bytes = decode_hex(private_key)
priv_key = keys.PrivateKey(priv_key_bytes)
pub_key = priv_key.public_key
print("public key ", pub_key.to_hex()) 
print("address = ", pub_key.to_checksum_address())


did = "did:key:" + pub_key.to_checksum_address()[2:]
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


print(didkit.verifyCredential(credential, didkit_options.__str__().replace("'", '"')))

