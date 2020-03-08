
# pour faire un call a la fonction getContractIndex qui a un "only owner", il faut passer par une addresse importée en local au node

# utiliser le provider http pour l acces
#  /usr/local/bin/geth --rinkeby --syncmode 'light'  --rpcapi="db,eth,net,web3,personal,web3" --cache=4096 --rpc

# pour importer une private key dans le node
#a= w3.geth.personal.importRawKey(foundation_privatekey, 'the-passphrase')

# pour unlocker le compte dans le node : attention il faut arreter le http, docn enlever --rpc au lancement de geth
#a=w3.geth.personal.unlockAccount(address, 'the-passphrase')


# utiliser le provider http (--rpc)  et les api (--rpcapi="db,eth,net,web3,personal,web3") pour l acces
#  /usr/local/bin/geth --rinkeby --syncmode 'light'  --rpcapi="db,eth,net,web3,personal,web3" --cache=4096 --rpc


def email2contract(emailsearch) :

	# provider IPC classique
	from web3 import Web3
	my_provider = Web3.IPCProvider('/home/thierry/.ethereum/rinkeby/geth.ipc')
	w3 = Web3(my_provider)

	# pour ethereum
	#address ='0x2F8aE6474C37e11291C57ee06aA701b84c0d4C46'
	#foundation_privatekey =   '0x478D1C254ABAB360462B114FBDB868653BB6DAEBECE7F753AEBDFFD3D00C9EB5'

	# pour rinkeby
	address = '0x2aaF9517227A4De39d7cd1bb2930F13BdB89A113'
	#foundation_privatekey =  '0x84AFF8F2CA153F4CADC6A5D52EAB0FD6DCE8FEB6E2AE1F1F48AD11A5D16E4A73'

	# pour choisir l address par defaut du node
	w3.eth.defaultAccount=address
	
	# lecture de la liste des contracts dans la fondation
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	contractlist = contract.functions.getContractsIndex().call()

	# recherche du workspace qui a le meme email
	for i in contractlist :
		contract=w3.eth.contract(i,abi=constante.workspace_ABI)
		claimId=contract.functions.getClaimIdsByTopic(101109097105108).call()[0].hex()
		emaillist = contract.functions.getClaim(claimId).call()[4].decode('utf-8')
		if emaillist == emailsearch :
			return i
	
	return False		


