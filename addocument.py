import Talao_token_transaction
import Talao_ipfs
import hashlib
import constante
import json

# provider IPC classique
from web3 import Web3
my_provider = Web3.IPCProvider(constante.IPCProvider)
w3 = Web3(my_provider)

###################################################################
# Création de document 250000 000 gas
# @data = dictionnaire = {"user": { "ethereum_account": '123' , "ethereum_contract": '234' ,"first_name" : 'Jean' ,"last_name" : 'Pierre' }}
# @encrypted = False ou True => AES
# location engine = 1 pour IPFS, doctypeversion = 1, expire =Null, 
###################################################################
#   function createDocument(
#        uint16 _docType,
#        uint16 _docTypeVersion,
#        uint40 _expires,
#        bytes32 _fileChecksum,
#        uint16 _fileLocationEngine,
#        bytes _fileLocationHash,
#        bool _encrypted
    

def addDocument(address_from, private_key_from, address_to, doctype, data, encrypted) :
	
	
	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract_to=Talao_token_transaction.ownersToContracts(address_to)

	#envoyer la transaction sur le contrat
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)

	# calcul du nonce de l envoyeur de token . Ici le portefeuille TalaoGen
	nonce = w3.eth.getTransactionCount(address_from)  

	# stocke sur ipfs (un dictionnaire)
	hash=Talao_ipfs.IPFS_add(data)
	
	# calcul du checksum en bytes des data, conversion du dictionnaire data en chaine str
	_data= json.dumps(data)
	checksum=hashlib.md5(bytes(_data, 'utf-8')).hexdigest()
	# la conversion inverse de bytes(data, 'utf-8') est XXX.decode('utf-8')

	# Build transaction
	txn = contract.functions.createDocument(doctype,1,0,checksum,1, bytes(hash, 'utf-8'), encrypted).buildTransaction({'chainId': constante.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(constante.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash)		
	return hash
