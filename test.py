import environment
import constante
import os
import didkit
import json
import base64
import sys

import requests

from eth_keys import keys
from eth_utils import decode_hex
from jwcrypto import jwk
from signaturesuite import helpers
from protocol import ownersToContracts
from datetime import datetime
from components import privatekey, ns

from components import privatekey
from signaturesuite import vc_signature, helpers

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

"""
mode = environment.currentMode('talaonet','airbox')

username = 'pascaldelorme'
for username in ['talao', 'mycompany', 'pascaldelorme', 'thierrythevenet','pauldupont', 'masociete' ] :
        address = ns.get_data_from_username(username, mode).get('address')
        privatekey.generate_store_key(address, 'Ed25519', mode)
        privatekey.generate_store_key(address, 'P-256', mode)
"""

#print('key = ', privatekey.get_key(address, 'P-256', mode))
#print('key = ', privatekey.get_key(address, 'secp256k1', mode))
#print('key = ', privatekey.get_key(address, 'Ed25519', mode))



#print('address = ', address)
#pvk = privatekey.get_key(address, 'private_key', mode)

#key = jwk.JWK.from_pem(pvk.encode())
#key = key.export_private()
#del rsa_public['kid']


#pvk = privatekey.get_key(address, 'private_key', mode)
#key = helpers.ethereum_to_jwk256k(pvk)


#pvk = "0x7f1116bdb705f3e51a299a1fe04b619e0e2516258ef187946076b04151ece8a5"
#address = helpers.ethereum_pvk_to_address(pvk)
#workspace_contract = ownersToContracts(address,mode)

#print('address = ', helpers.ethereum_pvk_to_address(pvk))
#print('workspace_contract = ', workspace_contract)

#key = helpers.ethereum_to_jwk256kr(pvk)
#did = helpers.ethereum_pvk_to_DID(pvk, method)

#key =  json.dumps({"crv": "secp256k1", "d": "fxEWvbcF8-UaKZof4Ethng4lFiWO8YeUYHawQVHs6KU", "kty": "EC", "x": "uPSr7x3mgveGQ_xvuxO6CFIY6GG09ZsmngY5S2EixKk", "y": "mq7je_woNa3iMGoYWQ1uZKPjbDgDCskAbh12yuGAoKw", "alg": "ES256K-R"})
#key = jwk.JWK.generate(kty="EC", crv="secp256k1", alg="ES256K-R")
#key = jwk.JWK.generate(kty="EC", crv="P-256")
#key = jwk.JWK.generate(kty="EC", crv="secp256k1")
#key = jwk.JWK.generate(kty="OKP", crv="Ed25519")
#key = jwk.JWK.generate(kty='RSA', size=2048)
#a = key.export_to_pem(private_key=True, password=b'test')
#print (a)
#key=key.export_private()
#print('key = ', key)
#key = '{"crv":"P-256","d":"zqojPOaQaVLmCZfHM5sYQNJ4pGqt4H8jTLUrokW04vU","kty":"EC","x":"OlhAgrdZrGbUcuoNeY8FNuUhcJGlDFkvXUv9DhvRsHc","y":"PyKwME0TRLcAQaQ1xexNkN_87bhCRseKgf5dDc261oQ"}'
#key = helpers.ethereum_to_jwk(pvk, method)
#did = helpers.jwk_to_did(method, key)

method = "ethr"
#did = didkit.keyToDID(method, key)
#print('did = ', did)

key1 = json.dumps({
        #"alg":"ES256K", 
        "crv":"secp256k1", 
        "d":"fL7tbHq_cPJ9HuElbbw5OVZS4Bk1iFPW1DByKwrUm_U", 
        "kty":"EC", 
        #"crit":["b64"],
        #"b64" : False,
        "x":"--eKPRDS_bk5Pm_Wy6LaAn6btTyB-mY_J3JgL7CV8Uk", 
        "y":"tjx_FsTCaAU2sYIICkf73CS0yBAlWvQOHLo8e1c9qt4"})

key2 = json.dumps(
        {
        "crv": "P-256",
        "d": "HJjVZ1qx2m4NJF-ohV55VlD7UwkjOBUESo4hwCmny-Y",
        "kty" : "EC",
        "x" : "Bls7WaGu_jsharYBAzakvuSERIV_IFR2tS64e5p_Y_Q",
        "y" : "haeKjXQ9uzyK4Ind1W4SBUkR_9udjjx1OmKK4vl1jko"
        })

key3 = json.dumps({
        "crv": "secp256k1",
        "d": "WxNkSy38UZUxfAOBWbHQSynEi8pmu97fKehiojNv9mw",
        "kty": "EC",
        "x": "bjyWuKGoDtUXKD6RzbE4suxoNk0E6pKe0qZTHh1LMg4",
        "y": "O1JNLN8bO3EP23WNIiqxfGY8OwOkrcw4hmXXHzwmsGg"})


did = didkit.keyToDID(method, key1)
print('did  = ', did)
#did = "did:web:talao.co:thierrythevenet"

#did = "did:web:did.actor:mike"
#did = "did:ion:EiBgFSQI9fBXGuAam_OvZnldleL5auu1VTCp6Wzdyv98_w"
DIDdocument = didkit.resolveDID(did,'{}')
print('DID Document = ', json.dumps(json.loads(DIDdocument), indent=4))


#vm = didkit.keyToVerificationMethod(method, key)
#print('verifmethod = ', vm)
#vm = "did:ion:EiBgFSQI9fBXGuAam_OvZnldleL5auu1VTCp6Wzdyv98_w"
#verifmethod = didkit.keyToVerificationMethod("ethr", key)
#verifmethod = didkit.keyToVerificationMethod(method, key)
#verifmethod = "did:ethr:0x9e98af48200c62f51ac9ebdcc41fe718d1be04fb#controller"
#verifmethod = did + "#key-2"
#print('verfif method = ', verifmethod)

"""
# create
response = requests.get("http://127.0.0.1:3000/repository/create?did=" + did)
print(response.json())
if response.status_code != 200 :
        sys.exit()
sys.exit()
"""

#topicvalue =  349369237269256357346239253356
#claim_id =  0x83aa3ce4876fcb7eabaa9516025f08489af936f03369aa8ba271df66bf185c2e

#127.0.0.1:3000/certificate/?certificate_id=did:tz:tz2JKnkcJ4FswZkWUUxsihboc9CeQPnovgy8:claim:0x83aa3ce4876fcb7eabaa9516025f08489af936f03369aa8ba271df66bf185c2e


"""
# step 1 
verificationPurpose = {
            "proofPurpose": "authentication",
            "verificationMethod": verifmethod,
            "domain" : "https://talao.co/repository"
        }
presentation = didkit.DIDAuth(
            did,
            verificationPurpose.__str__().replace("'", '"'),
            key
        )
response = requests.post("http://127.0.0.1:3000/repository/authn", json = json.loads(presentation))
print(response.json())
if response.status_code != 200 :
        sys.exit()
token = response.json()['token']


# step 2 call an endpoint
credential = open('./signed_credentials/data:05c2f36c-96f4-11eb-99ea-3ca82aaebc39_credential.jsonld').read()
data = {"token" : token, "credential" : credential }
response = requests.post("http://127.0.0.1:3000/repository/publish", json = data)
print(response.json())
if response.status_code != 200 :
        sys.exit()




# step 1 
verificationPurpose = {
            "proofPurpose": "authentication",
            "verificationMethod": verifmethod,
            "domain" : "https://talao.co/repository",
            "challenge" : "123456"
        }
presentation = didkit.DIDAuth(
            did,
            verificationPurpose.__str__().replace("'", '"'),
            key
        )

#print(json.dumps(json.loads(presentation), indent=4))

response = requests.post("http://127.0.0.1:3000/repository/authn", json = json.loads(presentation))
if response.status_code != 200 :
        sys.exit()
token = response.json()['token']


# step 2 call an endpoint
credential = open('./signed_credentials/data:05c2f36c-96f4-11eb-99ea-3ca82aaebc39_credential.jsonld').read()
credential_id = "data:05c2f36c-96f4-11eb-99ea-3ca82aaebc39"
data = {"token" : token, "credential_id" : credential_id }
response = requests.post("http://127.0.0.1:3000/repository/get", json = data)
print(response.json())
if response.status_code != 200 :
        sys.exit()




verifyResult = json.loads(didkit.verifyPresentation(
            presentation,
            verificationPurpose.__str__().replace("'", '"')))

print(verifyResult)
"""
credential = { "@context": "https://www.w3.org/2018/credentials/v1",
                "type": ["VerifiableCredential"],
                "issuer" : did  ,
                "issuanceDate": "2020-08-19T21:41:50Z",
                "credentialSubject": {
                "id": "did:example:d23dd687a7dc6787646f2eb98d0"

                        }
        }

#print(credential.sign(cred, pvk, method))


#fp=open("./verifiable_credentials/reference.jsonld", "r")
#credential = json.loads(fp.read())

#credential["issuanceDate"] = "2020-08-19T21:41:50Z"
#credential["issuer"] = did

#credential['id'] = "data:5656"
#credential["credentialSubject"]["id"] = "data:555"

"""
didkit_options = {
        "proofPurpose": "assertionMethod",
        "verificationMethod": "JwsVerificationKey2020",
        }

credential = didkit.issueCredential(
        credential.__str__().replace("'", '"'),
        didkit_options.__str__().replace("'", '"'),
        key
        )



credential = didkit.issueCredential(
        json.dumps(credential, ensure_ascii=False),
        didkit_options.__str__().replace("'", '"'),
        key
        )


print(json.dumps(json.loads(credential), indent=4, ensure_ascii=False))
#print(didkit.verifyCredential(credential, didkit_options.__str__().replace("'", '"')))



eyJhbGciOiJFUzI1NksifQ.IjEyMzQ1NiI.hPxkRQ9mGbZigHc3wnFeFlnx0OFTqkGoBaloeQoOZB4YFnceSg1yvOPd-Dv4bn9KAPUeYXk5S2_Yn-gYZwKaBw
eyJhbGciOiJFUzI1NksiLCJjcml0IjpbImI2NCJdLCJiNjQiOmZhbHNlfQ..f1R-I8DkxE6cdBFaqK4Z3HHrunxr0FoXS7GIVL2-LGM7QT9Ez4AqJdG-elibOZbX1s2gAKsiHlp2iAgElUI4yQ"

"""