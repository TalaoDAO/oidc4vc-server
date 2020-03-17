"""

le name service permet de creer un lien entre un identifiant et un did.
la donn&e est gérée par la fondation, les données sont stockées sur la blockchain
le regsitre identifiant => did est cnstruit dynamiquement
ex : monidentifiant.TalentConnect est stocké dans la workspace a la creation et par la fondation ou le owner 

1) creer un claim "nameservice" 110097109101115101114118105099101 par le owner ou par la fondation avec la valeur "name" publique
2) creer le registre dynamique "did:name" par la fondation

#  /usr/local/bin/geth --rinkeby --syncmode 'light'  --rpcapi="db,eth,net,web3,personal,web3" --cache=4096 --rpc


Pour faire un call a la fonction getContractIndex qui a un "only owner", il faut passer par une addresse importée en local au node

1) pour importer une private key dans le node
a= w3.geth.personal.importRawKey(foundation_privatekey, 'the-passphrase')

2) pour unlocker le compte dans le node : attention il faut arreter le http, docn enlever --rpc au lancement de geth
a=w3.geth.personal.unlockAccount(address, 'the-passphrase')

# utiliser le provider http (--rpc)  et les api (--rpcapi="db,eth,net,web3,personal,web3") pour l acces
#  /usr/local/bin/geth --rinkeby --syncmode 'light'  --rpcapi="db,eth,net,web3,personal,web3" --cache=4096 --rpc


normalisation:
http://unicode.org/reports/tr46/

"""


import constante
from eth_account.messages import encode_defunct
import hashlib




####################################################
# Nanehash
####################################################
# cf https://docs.ens.domains/dapp-developer-guide/resolving-names

def sha3(key) :
	bkey=bytes(key, 'utf-8')
	m=hashlib.sha3_256()
	m.update(bkey)
	return m.digest().hex()

def namehash(name) :
	bname=bytes(name, 'utf-8')	
	if name == '':
		return '0x00000000000000000000000000000000000'
	else:
		label, _, remainder = name.partition('.')
		a =sha3( namehash(remainder) + sha3(label) )
		return a

#################################################
#  construction dynamise du registre 
#################################################
# le regsitre est un dict {hashname : address}

def buildregister(mode) :

	w3=mode.initProvider()
	
	# pour choisir l address par defaut du node necessaire a la lecture de l index du smart contract de la fondation
	address = mode.foundation_address
	w3.eth.defaultAccount=address
	#w3.geth.personal.unlockAccount(address, 'suc2cane')
	
	# lecture de la liste des contracts dans la fondation
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	contractlist = contract.functions.getContractsIndex().call() 
	contractlist.reverse()
	
	# ATTENTION construction du registre sur la base du claim "nameservice" ET "email'
	register=dict()	
	for workspace_contract in contractlist :
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		"""
		if len(contract.functions.getClaimIdsByTopic(110097109101115101114118105099101).call()) != 0 :
			claimId=contract.functions.getClaimIdsByTopic(110097109101115101114118105099101).call()[0].hex()
			hashname = contract.functions.getClaim(claimId).call()[4].decode('utf-8')
			register[hashname]=workspace_contract
	"""
		if len(contract.functions.getClaimIdsByTopic(101109097105108).call()) != 0 :
			claimId=contract.functions.getClaimIdsByTopic(101109097105108).call()[0].hex()
			email = contract.functions.getClaim(claimId).call()[4].decode('utf-8')
			register[namehash(email)]=workspace_contract
	
	return register	


#################################################
#  setup name pour une address de workspace par la fondation
#################################################
# @name : str
# cf https://docs.ens.domains/dapp-developer-guide/managing-names
# signature cf https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message
# le namehash de name est stocké dans le workpace avec un claim 'nameservice'
	
def setup_address(name, workspace_contract,mode) :
		
	w3=mode.initProvider()

	issuer = mode.foundation_address	
	data=namehash(name)	
	topicname='nameservice'
	topicvalue= 110097109101115101114118105099101
	ipfshash=""
	nonce = w3.eth.getTransactionCount(mode.foundation_address)  	
	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=mode.foundation_private_key)
	signature=signed_message['signature']	
	
	# build, sign and send avec une addresse dans le node "defaultAccount
	w3.eth.defaultAccount=mode.foundation_address
	hash1=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).transact({'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce})	
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	
	return hash1.hex()
"""	
	# Build transaction
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	txn=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,mode.foundation_private_key)
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	

	
	return hash1
"""

#####################################################	
# obtenir l address depuis un nom
######################################################
def address(name,register) :
	return register.get(namehash(name))

