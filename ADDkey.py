# dependances
import constante


#######################################################################
# ajout d'un cle avec purpose
#######################################################################
# @purpose = int, 1,2,3,4, 20002(create doc), 2003(acces to partnership)
# si a cle existe deja on ajoute simplement le purpose
# si la cle n existe pas on cre la cle avec le purpose
#
def addkey(workspace_contract_from, private_key_from, workspace_contract_to, purpose,mode) :

	w3=mode.initProvider()

	# determination des address
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address_from = contract.functions.contractsToOwners(workspace_contract_from).call()	
	address_to = contract.functions.contractsToOwners(workspace_contract_to).call()
	
	#envoyer la transaction sur le contrat
	contract=w3.eth.contract(workspace_contract_from,abi=constante.workspace_ABI)

	# calcul du nonce de l issuer de la cle
	nonce = w3.eth.getTransactionCount(address_from)  
	# calcul du keccak de l address de celui pour qui la cle est emise 
	key=w3.soliditySha3(['address'], [address_to])
	print(" key = ", key.hex())

	# on verifie si la cle et le purpose existe deja
	keydescription = contract.functions.getKey(key).call()
	keylist=keydescription[0]
	
	if len(keylist) != 0 : # la cle existe dejà
		
		if purpose not in keylist : # si purpose n' existe pas déja, on ajoute le purpose
			
			print(" cle existe, purpose n existe pas")
			# Build transaction
			txn = contract.functions.addPurpose(key, purpose).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
			#sign transaction
			signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
			# send transaction	
			w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
			hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
			w3.eth.waitForTransactionReceipt(hash1)		
			print("hash = ", hash1)		
			
			return True
		
		else : # purpose existe
			print("purpose existe")
			
			return False
	
	else : # on cre la cle avec le purpose
		
		print("cle n existe pas")
		# Build transaction
		txn = contract.functions.addKey(key, purpose, 1).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
		#sign transaction
		signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
		# send transaction	
		w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
		hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
		w3.eth.waitForTransactionReceipt(hash1)
		print("hash = ", hash1)		
		
		return True


