
import constante
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import Talao_token_transaction
import csv
import http.client, urllib.parse
import json
import datetime
import Talao_backend_transaction
import Talao_ipfs
import GETresume
import createidentity
import environment
import nameservice

# SETUP
mode=environment.currentMode('test', 'rinkeby')
#mode.print_mode()
w3=mode.initProvider()

# données des test
#data ='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:document:10' # David Houlle
#data='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:b34c2a6837a9e89da5ef886d18763fb13a12615814d50a5b73ae403cb547d788'
data='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b' # david houlle
#data= 'did:talao:rinkeby:29f880c177cD3017Cf05576576807d1A0dc87417' # TTF
#data = 'did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:b34c2a6837a9e89da5ef886d18763fb13a12615814d50a5b73ae403cb547d788'
#data = 'antoine.keriven@talao.io'

data='did:talao:rinkeby:7B47122cb8caa6d3c174BBCd067b361e011446f5' #AXA


#did='did:talao:rinkeby:29f880c177cD3017Cf05576576807d1A0dc87417' #TTF

firstname = "Alberta"
name = "Pudrey"
email = "Albert.Paudrey2@talao.io"




print(createidentity.creationworkspacefromscratch(firstname, name, email, mode)	)





print(nameservice.address(email, mode.register))

