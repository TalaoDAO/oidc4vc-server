import datetime
import json
from datetime import datetime
import Talao_backend_transaction
import constante
import Talao_token_transaction
import Talao_ipfs
import ipfshttpclient
import GETresolver
import GETdata
import sys
import GETresume
import nameservice
import addclaim
import random
from Crypto.Random import get_random_bytes
import Talao_message
import Talao_token_transaction
import environment

# SETUP
mode=environment.currentMode('test', 'rinkeby')
#mode.print_mode()
w3=mode.initProvider()



private_key_onfido="0xdd6a47a3f324d8375850104c0c41a473dabdc1742666f4c63e28cb7ff0e26bbf"
address_onfido = "0xdBEcB7f4A6f322444640b0173C81f9B0DECe0E07"
workspace_contract_pierre = "0xab6d2bAE5ca59E4f5f729b7275786979B17d224b"
address_pierre = "0xe7Ff2f6c271266DC7b354c1B376B57c9c93F0d65"
private_key_pierre = "0xf73c5085c32410657f78851386d78e84042076e762c0d1360b4b972045817e2a"
address_thales="0x60f6876F2880fB5c92Caad1C3002356d2F33b770"


workspace_contract_from= workspace_contract_pierre
address_from = address_pierre
private_key_from= private_key_pierre 
address_to=address_thales

# AJOUT CLE 3 
owner_foundation = address_onfido	       
#envoyer la transaction sur le contrat
contract=w3.eth.contract(workspace_contract_from,abi=constante.workspace_ABI)
# calcul du nonce de l envoyeur de token . Ici le owner
nonce = w3.eth.getTransactionCount(address_from)  
# calcul du keccak de address_to
_key=w3.soliditySha3(['address'], [address_to])
# Build transaction
txn = contract.functions.addKey(_key, 3, 1).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
#sign transaction
signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
# send transaction	
w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
w3.eth.waitForTransactionReceipt(hash1)		
print("creation de cle 3  = ", hash1)


