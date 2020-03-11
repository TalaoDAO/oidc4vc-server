import constante
from eth_account.messages import encode_defunct


# nameservice est géré par la fondation
foundation_private_key =   '0x478D1C254ABAB360462B114FBDB868653BB6DAEBECE7F753AEBDFFD3D00C9EB5'
foundation_address = '0x2aaF9517227A4De39d7cd1bb2930F13BdB89A113'
foundation_workspace_contract = '0xde4cF27d1CEfc4a6fA000a5399c59c59dA1BF253'

# pour faire un call a la fonction getContractIndex qui a un "only owner", il faut passer par une addresse importée en local au node
# utiliser le provider http pour l acces
#  /usr/local/bin/geth --rinkeby --syncmode 'light'  --rpcapi="db,eth,net,web3,personal,web3" --cache=4096 --rpc
#
# pour importer une private key dans le node
#a= w3.geth.personal.importRawKey(foundation_privatekey, 'the-passphrase')
#
# pour unlocker le compte dans le node : attention il faut arreter le http, docn enlever --rpc au lancement de geth
#a=w3.geth.personal.unlockAccount(address, 'the-passphrase')
#
# utiliser le provider http (--rpc)  et les api (--rpcapi="db,eth,net,web3,personal,web3") pour l acces
#  /usr/local/bin/geth --rinkeby --syncmode 'light'  --rpcapi="db,eth,net,web3,personal,web3" --cache=4096 --rpc


def buildregister() :
	
	
	# provider IPC classique
	from web3 import Web3
	my_provider = Web3.IPCProvider('/home/thierry/.ethereum/rinkeby/geth.ipc')
	w3 = Web3(my_provider)
	
	# pour choisir l address par defaut du node
	address = '0x2aaF9517227A4De39d7cd1bb2930F13BdB89A113'
	w3.eth.defaultAccount=address
	
	# lecture de la liste des contracts dans la fondation
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	contractlist = contract.functions.getContractsIndex().call()
	contractlist.reverse()
	
	# ATTENTION construction du registre sur la base du claim "email" 
	register=dict()
	for i in contractlist :
		contract=w3.eth.contract(i,abi=constante.workspace_ABI)
		claimId=contract.functions.getClaimIdsByTopic(101109097105108).call()[0].hex()
		emaillist = contract.functions.getClaim(claimId).call()[4].decode('utf-8')
		register[emaillist]=i
		
	return register	


def email2contract(emailsearch, register) :
	return register.get(emailsearch)


#################################################
#  write auth claim
#################################################
# @data : str
# @topicname : type str , 'contact'
# @ipfshash = str exemple  b'qlkjglgh'.decode('utf-8') 
# signature cf https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message
#	auth_email Topic : 97117116104095101109097105108
#	auth_phone Topic : 97117116104095112104111110101

	
def writeauth(auth_email, auth_phone, workspace_contract) :

	# nameservice est géré par la fondation
	#foundation_private_key =   '0x478D1C254ABAB360462B114FBDB868653BB6DAEBECE7F753AEBDFFD3D00C9EB5'
	
	foundation_private_key = '0x84AFF8F2CA153F4CADC6A5D52EAB0FD6DCE8FEB6E2AE1F1F48AD11A5D16E4A73'
	foundation_address = '0x2aaF9517227A4De39d7cd1bb2930F13BdB89A113'
	foundation_workspace_contract = '0xde4cF27d1CEfc4a6fA000a5399c59c59dA1BF253'	
	

	# provider IPC classique
	from web3 import Web3
	my_provider = Web3.IPCProvider('/home/thierry/.ethereum/rinkeby/geth.ipc')
	w3 = Web3(my_provider)
	
	# auth_email
	issuer = foundation_address
	data=auth_email
	topicname='auth_email'
	topicvalue=97117116104095101109097105108
	ipfshash=""
	nonce = w3.eth.getTransactionCount(foundation_address)  	
	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=foundation_private_key)
	signature=signed_message['signature']	
	
	# Build transaction
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	txn=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).buildTransaction({'chainId': constante.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(constante.GASPRICE, 'gwei'),'nonce': nonce,})	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,foundation_private_key)
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	
	# auth_phone
	issuer = foundation_address
	data=auth_phone
	topicname='auth_phone'
	topicvalue=97117116104095112104111110101
	ipfshash=""
	nonce = w3.eth.getTransactionCount(foundation_address)  	
	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=foundation_private_key)
	signature=signed_message['signature']	

	# Build transaction
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	txn=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).buildTransaction({'chainId': constante.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(constante.GASPRICE, 'gwei'),'nonce': nonce,})	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,foundation_private_key)
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash2= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash2, timeout=2000, poll_latency=1)	
	
	return hash1, hash1



#################################################
#  write auth_email claim
#################################################
# @data : str
# @topicname : type str , 'contact'
# @ipfshash = str exemple  b'qlkjglgh'.decode('utf-8') 
# signature cf https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message
#	auth_email Topic : 97117116104095101109097105108
#	auth_phone Topic : 97117116104095112104111110101

	
def writeauthemail(auth_email, workspace_contract) :

	# nameservice est géré par la fondation
	#foundation_private_key =   '0x478D1C254ABAB360462B114FBDB868653BB6DAEBECE7F753AEBDFFD3D00C9EB5'
	
	foundation_private_key = '0x84AFF8F2CA153F4CADC6A5D52EAB0FD6DCE8FEB6E2AE1F1F48AD11A5D16E4A73'
	foundation_address = '0x2aaF9517227A4De39d7cd1bb2930F13BdB89A113'
	foundation_workspace_contract = '0xde4cF27d1CEfc4a6fA000a5399c59c59dA1BF253'	
	

	# provider IPC classique
	from web3 import Web3
	my_provider = Web3.IPCProvider('/home/thierry/.ethereum/rinkeby/geth.ipc')
	w3 = Web3(my_provider)
	
	# auth_email
	issuer = foundation_address
	data=auth_email
	topicname='auth_email'
	topicvalue=97117116104095101109097105108
	ipfshash=""
	nonce = w3.eth.getTransactionCount(foundation_address)  	
	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=foundation_private_key)
	signature=signed_message['signature']	
	
	# Build transaction
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	txn=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).buildTransaction({'chainId': constante.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(constante.GASPRICE, 'gwei'),'nonce': nonce,})	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,foundation_private_key)
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	
	
	return hash1




#####################################################	
# read les claim d authentification
######################################################
def getauth (workspace_contract) :
# retourne un couple email,phone
# ou None, None	
#	auth_email Topic : 97117116104095101109097105108
#	auth_phone Topic : 97117116104095112104111110101
# ces 3 claims sont initialisés a la creation ou par la fondation dans nameservice
	
	
	# provider IPC classique
	from web3 import Web3
	my_provider = Web3.IPCProvider('/home/thierry/.ethereum/rinkeby/geth.ipc')
	w3 = Web3(my_provider)
	
	# doownload de la liste des claims auth_phone, auth_email et auth_website
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	claim_email=contract.functions.getClaimIdsByTopic(97117116104095101109097105108).call()
	claim_phone=contract.functions.getClaimIdsByTopic(97117116104095112104111110101).call()
	claim_website=contract.functions.getClaimIdsByTopic(97117116104095119101098115105116101).call()

	# determination de auth_email
	if len(claim_email) == 0 :  # si il n existe pas on prend l email de base du profil
		claim_email=contract.functions.getClaimIdsByTopic(101109097105108).call()
		claimdata_email=contract.functions.getClaim(claim_email[0]).call()
		auth_email = claimdata_email[4].decode('utf-8')
	else :
		claimdata_email=contract.functions.getClaim(claim_email[0]).call()
		auth_email = claimdata_email[4].decode('utf-8')
	
	# determination de auth_phone
	if len(claim_phone) == 0 :		
		auth_phone = None
	else :
		claimdata_phone=contract.functions.getClaim(claim_phone[0]).call()
		auth_phone= claimdata_phone[4].decode('utf-8')
	
	# determination de auth_website
	if len(claim_website) == 0 :
		auth_website = None
	else :
		claimdata_website=contract.functions.getClaim(claim_website[0]).call()
		auth_website= claimdata_website[4].decode('utf-8')
	
	
	return auth_email, auth_phone, auth_website
	


"""
le 19 fevrier  0x84AFF8F2CA153F4CADC6A5D52EAB0FD6DCE8FEB6E2AE1F1F48AD11A5D16E4A73 owner Fondation

le 3 mars     0x478D1C254ABAB360462B114FBDB868653BB6DAEBECE7F753AEBDFFD3D00C9EB5

"""
