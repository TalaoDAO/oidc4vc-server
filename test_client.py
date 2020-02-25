
from web3.auto import w3
import constante
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import Talao_token_transaction
import csv
import http.client, urllib.parse
import json
import sys
import Talao_message
from eth_account.messages import encode_defunct



# adresse de Jean Pascal sur rinkeby
key='0x9A1D7ee6CcF5588c7f74E34a49308da9AbC27Bf8'
#key='0x868194C09990FdB869F51871bBB005934a5905f8'
private_key='0xb152e156901c7b0d24607aede258aab6c2d72572c4ed766294e8a36fa1f7959b'
purpose=10
keytype=1
actuor="none"
data="temperature"

"""
print('address = ', key)

# constituer le message et le signé
msg=key+data+actuor
message = encode_defunct(text=msg)
signed_message = w3.eth.account.sign_message(message, private_key=private_key)
signature=signed_message.signature.hex()
"""



conn = http.client.HTTPConnection('217.128.135.206:4000')
headers = {'Accept': 'application/json','Content-type': 'application/json'}
payload = {"address": key}
data = json.dumps(payload)
conn.request('GET', '/api/v1.0/experience',data, headers)

response = conn.getresponse()
print('analyse de la reponse =',response.status, response.reason)
res=response.read()
print(json.loads(res))




