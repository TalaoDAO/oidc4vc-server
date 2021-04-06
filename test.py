import environment
import constante
import os
import didkit
import json
import base64
from eth_keys import keys
from eth_utils import decode_hex
from jwcrypto import jwk
from signaturesuite import helpers

from datetime import datetime


#key = didkit.generateEd25519Key()
#print('key Ed25519Key ', key)

#key = json.loads(didkit.generateEd25519Key())
#print(key)

#did = didkit.keyToDID("key", key)
#print('did key = ', did)


#did2 = didkit.keyToDID("tz", key)
#print('did tz = ', did2)

#vm = didkit.keyToVerificationMethod('key', key)
#print('vm = ', vm)


method = "ethr"

pvk = "0x7f1116bdb705f3e51a299a1fe04b619e0e2516258ef187946076b04151ece8a5"
key = helpers.ethereum_to_jwk256kr(pvk)
did = helpers.ethereum_pvk_to_DID(pvk, method)

#key =  json.dumps({"crv": "secp256k1", "d": "fxEWvbcF8-UaKZof4Ethng4lFiWO8YeUYHawQVHs6KU", "kty": "EC", "x": "uPSr7x3mgveGQ_xvuxO6CFIY6GG09ZsmngY5S2EixKk", "y": "mq7je_woNa3iMGoYWQ1uZKPjbDgDCskAbh12yuGAoKw", "alg": "ES256K-R"})
#key = jwk.JWK.generate(kty="EC", crv="secp256k1", alg="ES256K-R")
#key = jwk.JWK.generate(kty="EC", crv="P-256")
#key = jwk.JWK.generate(kty="EC", crv="secp256k1")
#key = jwk.JWK.generate(kty="OKP", crv="Ed25519")
#key=key.export_private()
#print('key = ', key)

#did = didkit.keyToDID(method, key)
#print('did  = ', did)

#did = "did:web:talao.co:thierry"

#DIDdocument = didkit.resolveDID(did,json.dumps({}))
#print(json.dumps(json.loads(DIDdocument), indent=4))

verifmethod = didkit.keyToVerificationMethod(method, key)
#verifmethod = didkit.keyToVerificationMethod("ethr", key)
#verifmethod = didkit.keyToVerificationMethod("key", key)
#verifmethod = "did:ethr:0x9e98af48200c62f51ac9ebdcc41fe718d1be04fb#controller"

#print('verfif method = ', verifmethod)

credential = { "@context": "https://www.w3.org/2018/credentials/v1",
                        "type": ["VerifiableCredential"],
                        "issuer" : did  ,
                        "issuanceDate": "2020-08-19T21:41:50Z",
                        "credentialSubject": {
                        "id": "did:example:d23dd687a7dc6787646f2eb98d0",
                        }
}

credential = {
  '@context': [
    'https://www.w3.org/2018/credentials/v1'
  ],
  'id': 'data:d8408e54-96cb-11eb-95e4-d85de28ad6c7',
  'type': [
    'VerifiableCredential'
        ],
  'issuer': 'did:tz:tz2WjYARTRvLPTEESp98utDxtCtWRH5e6Ujr',
  'issuanceDate': '04/06/2021 13:33:01',
  'credentialSubject': {
    '@context': [
      'https://schema.org/'
        ],
    'id': 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250',
    'credentialCategory': 'reference',
    'offers': {
      '@type': 'Offer',
      'title': "Conception et réalisation d'un serveur OpenID COnnect",
      'description': "OpenID Connect (OIDC) spécifie une interface HTTP Restful d’authentification et se base sur le protocole OAuth2 pour faire de la délégation d’autorisation, c’est à dire que dans la grande majorité des cas, l’utilisateur final n’aura plus besoin de fournir directement ses informations d’identification à une application tierce. OIDC utilise également le formalisme d’échange JWT (JSON Web Token) pour transmettre l’identité des utilisateurs aux applications, ainsi que leurs rôles/habilitations. ",
      'location': '',
      'startDate': '2020-10-01',
      'endDate': '2021-01-30',
      'price': '50000',
      'priceCurrency': 'EUR'
                },
    'review': {
      '@type': 'Review',
      'author': '',
      'datePublished': '',
      'reviewBody': "Contrairement à nos expériences précédentes, nous avons rapidement réussi à créer une relation de confiance avec les équipes de Talao. Notre chef de projet, Raphaël, a été un des facteurs de la réussite du projet tant par sa réactivité, que par sa totale transparence. On attend pas un mois avant d’avoir une réponse ce qui est très agréable. Il nous aide au quotidien à trouver des solutions ou à contourner un obstacle quand cela est possible."
                },
    'companyLogo': 'QmXKeAgNZhLibNjYJFHCiXFvGhqsqNV2sJCggzGxnxyhJ5',
    'managerSignature': 'QmS9TTtjw1Fr5oHkbW8gcU7TnnmDvnFVUxYP9BF36kgV7u',
    'companyName': 'MyCompany',
    'managerName': 'Director'
  }
}

#fp=open("./verifiable_credentials/reference.jsonld", "r")
#credential = json.loads(fp.read())
credential["issuanceDate"] = "2020-08-19T21:41:50Z"
credential["issuer"] = did
#credential['id'] = "data:5656"
#credential["credentialSubject"]["id"] = "data:555"

didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": verifmethod
        }

"""
credential = didkit.issueCredential(
        credential.__str__().replace("'", '"'),
        didkit_options.__str__().replace("'", '"'),
        key
        )
"""
credential = didkit.issueCredential(
        json.dumps(credential, ensure_ascii=False),
        didkit_options.__str__().replace("'", '"'),
        key
        )

print(json.dumps(json.loads(credential), indent=4, ensure_ascii=False))
print(didkit.verifyCredential(credential, didkit_options.__str__().replace("'", '"')))

