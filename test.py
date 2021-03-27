import environment
import constante
import os
import didkit
import json
from authlib.jose import jwk
from components import privatekey

rsa_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAmz3frh5cMQw79IA/tqvb738FkZk0D10YiezTkj+Pg5CIg5Vj
oe25koakQarsBeaMcVZF5dl48bFCUH9nRZq7Txv4IdxUAzm/3udvCOLSSLxKmzmw
T7u3W3EMKy2pqJ1jKK4I+SuFNW+lQP7RWPqD97K/bxJGjQRUdeyj4Lmi8N8ahd4q
OSRmoyBg6Z4tv9SNvp+8Z/9eyIBGThkN8HNwnJoGs9YNYWRNsp67taJNU5em6bRW
9eae/FVB20YzaHxfOLni6NZY5xw3THdDsMSGBwTS9HJloM8oTqObLXa/FX6xp6K0
WbXdOfYVcLIKn6GwqaEoHuKf7BB4dRsDwVN6EwIDAQABAoIBAA3TNsy+bp6Xl+2w
T8kO1dyNE78U3upqjTlLQMdxDaQKOeR6zo91jxjNENFTgKCnfxf6abZZTBU9U5bw
bnWbNm8j7upLdHGAS39B93hAUVKhu7f5k6M/wZaAVmfjl/MomqB2z0NeOTpT1QQZ
LVk4bIqhZCPNUHPvT/sO6SrZA8Yux+dPewtaxQfHDryXPAEIMQ39cVpL37f14LwM
Hvjw5Kj3v1Ssin8ie2+Z8FXu+ryV0zINN1Jx6R2UNxmrDr48b3K9EZk56YG6J0h7
gc6M7ucV0VvOAs8Ow1w4uEhidlOahGdkBKYZ2butaKnwoHaAixYMoi+ltLar2UXL
EAHBi0ECgYEAwMuApDDPFV0g+kLndjQKDQt+3FoBtmYdGEUYSkES11npTV0RsO9E
W4NEZcpDiHEyxuFJS+Kh5ATHrr0s8RconTE3Lg2ODrEaRhw4+jyVSWhfoq04B9sr
SPSRJu8yiq0cjtJzWkRETbR9Z9V00cTeMKNSVOUmhZcl6Ub3WwOnIkMCgYEAziKu
IKfX9WsnfIcdySHPbdkt7CeWgnoJz1SIM9/Ovxx+kS1mwm6Spe4zTPWhBmGxpPbN
aSqwkGPV3Zn6OKnuQYxJVj2b3CYpaMhk/wZxWmAVQ7eYv9ZPJYYkSvbBUowaaVmz
rM2yjgiAHq2EYn358WRzEBg1/XiYhWNkMtrV0/ECgYAUqDlaXlhx446bAfwm8CB7
kVXAamxwjLRlW1Hk8t//7wROY8B3gsuCOqhjd66QugBEyvK9jMTn15NFp8Ne+apC
XXmaF522+UblaDS6qy8btHE6zvCH9vXGVV4QG+UActfyfZ4ad+IRqVseewKPT1a3
Q2iY7Ayal71aJ15thBCuXQKBgQCpTCBY36DlhlES3GHhK+yR2nn153mcxaBC8LlA
aYMCwONOVsx7yZaVwvHNNjs+44Oj6bNAuXfzzpr6epjgaugsW4xr0QOuJoWB8nvI
XEFCqYEtcZ95hwjP18D89HZIVprmhW6k8PfB4UdgasA8qBxcXlSGFmxZNe+GNeA4
SDSv8QKBgFCSDY9Ui06bHHJ4rjxHZkcKTTTRRguk7TdPs3Hext3PLs4tJYhgazwl
YTnvfHfbTabqdIJN4sudD5a4/NxPl1kX11wBJy+JQcsAoy/lMHgnGt53zuSm2XfT
KhF6aDCN+u79a2RngmoZlBiySDO7TBe3xgngCr2M62hq2nnbivrB
-----END RSA PRIVATE KEY-----"""


# Generate JWK from rsa key
key = jwk.dumps(rsa_key).__str__().replace("'", '"')
print('type de rsa = ', type(key))


key = didkit.generateEd25519Key()
print('key Ed25519Key ', key)

#key = json.loads(didkit.generateEd25519Key())
#print(key)

did = didkit.keyToDID("key", key)
print('did = ', did)

#vm = didkit.keyToVerificationMethod('key', key)
#print('vm = ', vm)

#credential = { "@context": "https://www.w3.org/2018/credentials/v1",
#                "type": ["VerifiableCredential"],
#                 "issuer" : "did:example:d23dd687a7dc6787646f2eb98d0",
#                   "issuanceDate": "2020-08-19T21:41:50Z",
#                "credentialSubject": {
#                "id": "did:example:d23dd687a7dc6787646f2eb98d0",
#               }
#                }

#didkit_options = {
#        "proofPurpose": "assertionMethod",
#        "verificationMethod": "verification_method",
#    }

#credential = didkit.issueCredential(
#        credential.__str__().replace("'", '"'),
#        didkit_options.__str__().replace("'", '"'),
#        key)

#auth = didkit.DIDAuth(did, didkit_options.__str__().replace("'", '"'), key)
#print('authn = ', auth)

#print(credential)