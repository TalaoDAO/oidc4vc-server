import json
import constante
from web3.auto import w3
from eth_account.messages import encode_defunct
import ipfshttpclient

#################################################
#  add self claim
#################################################
# @data : str
# @topicname : type str , 'contact'
# @ipfshash = str exemple  b'qlkjglgh'.decode('utf-8') 
# signature cf https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message

def addclaim(workspace_contract, private_key, topicname, issuer, data, ipfshash) :
	
	
	topicvalue=constante.topic[topicname]
	
	# calcul du nonce de l envoyeur de token . Ici le caller
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	nonce = w3.eth.getTransactionCount(address)  

	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=private_key)
	signature=signed_message['signature']
	
	# Build transaction
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	txn=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).buildTransaction({'chainId': constante.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(constante.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	return hash1


issuer='0xc883Eb9D7DA8f041B9085749E75dd371eBA07640'
ipfshash="mlkjmklj"
private_key='0xf73c5085c32410657f78851386d78e84042076e762c0d1360b4b972045817e2a'
workspace_contract='0xab6d2bAE5ca59E4f5f729b7275786979B17d224b'  # pierre david houlle
address={'name' : 'Thierry', 'street' : '16 rue de Wattignies', 'city' : 'Paris', 'city code' : '75012'}
client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
ipfshash=client.add_json(address)
client.pin.add(ipfshash)

print (addclaim(workspace_contract, private_key, 'address', issuer, "", ipfshash) )
