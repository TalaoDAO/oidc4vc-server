# dependancies
import constante


#######################################################################
# Add key with one purpose
#######################################################################
# @purpose = int, 1,2,3,4, 2002(create doc), 2003(acces to partnership)
#address_from : address which signs
# address_to : key issuer
# address_partner = key receiver

def addkey(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, address_partner,purpose,mode, synchronous=True) :
		
	w3 = mode.w3
	
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)  
	
	# keccak (publickey)
	key = w3.soliditySha3(['address'], [address_partner])
	print(" key = ", key.hex())

	# one checks if key with purpose exists
	key_description = contract.functions.getKey(key).call()
	purpose_list = key_description[0]
	
	# key already exists
	if len(purpose_list) != 0 : 
		if purpose not in purpose_list : 
			# key exists without this purpose, one adds this purpose
			print(" key exists, purpose does not exist")
			# Build, sign and send transaction
			txn = contract.functions.addPurpose(key, purpose).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
			signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
			w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
			hash_transaction = w3.toHex(w3.keccak(signed_txn.rawTransaction))
			if synchronous :
				w3.eth.waitForTransactionReceipt(hash_transaction)		
			print("hash = ", hash_transaction)		
			return True
		else : # purpose exists
			print("purpose and key already exists")
			return False
	
	else : 
		print("key does not exist")
		# Build, sign and send transaction
		txn = contract.functions.addKey(key, purpose, 1).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
		signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
		w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
		hash_transaction = w3.toHex(w3.keccak(signed_txn.rawTransaction))
		if synchronous :
			w3.eth.waitForTransactionReceipt(hash_transaction)
		print("hash = ", hash_transaction)		
		return True


def delete_key(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, address_partner, purpose, mode, synchronous=True) :

	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)  

	key = w3.soliditySha3(['address'], [address_partner])
		
	# one checks if this key with this purpose exists
	key_description = contract.functions.getKey(key).call()
	purpose_list = key_description[0]
	if purpose not in purpose_list :
		print('key does not exist or purpose dies not exist')
		return False 
	else :
		# build, sign and send transaction
		txn = contract.functions.removeKey(key, purpose).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
		signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
		w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
		hash_transaction = w3.toHex(w3.keccak(signed_txn.rawTransaction))
		if synchronous :
			w3.eth.waitForTransactionReceipt(hash_transaction)
		print("hash = ", hash_transaction)		
		return True
