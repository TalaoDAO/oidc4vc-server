import json
import constante
from eth_account.messages import encode_defunct
import ipfshttpclient


# provider IPC classique
from web3 import Web3
my_provider = Web3.IPCProvider(constante.IPCProvider)
w3 = Web3(my_provider)

#################################################
#  add claim
#################################################
# @data : str
# @topicname : type str , 'contact'
# @ipfshash = str exemple  b'qlkjglgh'.decode('utf-8') 
# signature cf https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message

def addClaim(workspace_contract_to, address_from,private_key_from, topicname, issuer, data, ipfshash) :
	
	
	topicvalue=constante.topic[topicname]
	
	nonce = w3.eth.getTransactionCount(address_from)  
	
	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=private_key_from)
	signature=signed_message['signature']
	
	# Build transaction
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	txn=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).buildTransaction({'chainId': constante.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(constante.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	return hash1
"""

issuer='0xc883Eb9D7DA8f041B9085749E75dd371eBA07640'
private_key='0xf73c5085c32410657f78851386d78e84042076e762c0d1360b4b972045817e2a'
workspace_contract='0xab6d2bAE5ca59E4f5f729b7275786979B17d224b'  # pierre david houlle
address={'name' : 'Thierry', 'street' : '16 rue de Wattignies', 'city' : 'Paris', 'city code' : '75012'}
client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
ipfshash=client.add_json(address)
client.pin.add(ipfshash)

print (addclaim(workspace_contract, private_key, 'address', issuer, "", ipfshash) )
"""
