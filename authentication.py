import json
from datetime import datetime
import ipfshttpclient
from web3.auto import w3
from eth_account.messages import encode_defunct


"""
# pour les tests d authentication

address = '0xe7Ff2f6c271266DC7b354c1B376B57c9c93F0d65'
private_key='0xf73c5085c32410657f78851386d78e84042076e762c0d1360b4b972045817e2a'

# saisie du fichier json
filename=input("Saisissez le nom du fichier json a authentifier ?")
jsonfile=open(filename, "r")
docjson=jsonfile.read()

auth_docjson = authenticate(docjson, address, private_key)
print(auth_docjson)

newjsonfile=open('auth_'+filename,"w")
newjsonfile.write(auth_docjson)
newjsonfile.close()   

# pour decoder
# message = encode_defunct(text=msg)
# address=w3.eth.account.recover_message(message, signature=signature)
# https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message
"""

