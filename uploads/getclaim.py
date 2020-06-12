import json
import constante
from web3.auto import w3
import ipfshttpclient
from eth_account.messages import encode_defunct


#####################################################	
# read Talao claim
######################################################
def getclaim (claim_id, workspace_contract) :
# @topicname est un str
# return un objet List
# ajouter le check de validité

	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()
	claims=[]
	did="did:talao:"+constante.BLOCKCHAIN+":"+workspace_contract[2:]			
	claim=dict()
	
	# initialisation IPFS
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	claimdata=contract.functions.getClaim(claim_id).call()
	topic=constante.topic
	inv_topic=dict(map(reversed, topic.items()))
	topicname=inv_topic[claimdata[0]]
	issuer=claimdata[2]	
	data=claimdata[4]
	
	url=claimdata[5]

	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32'], [bytes(topicname, 'utf-8'), issuer, data, bytes(url, 'utf-8') ])
	message = encode_defunct(text=msg.hex())
	signature=claimdata[3]
	print(signature)
	if signature != b"" :
		signataire=w3.eth.account.recover_message(message, signature=signature)
		if signataire==issuer :
			verification=True
		else :
			verification=False	
	else :
		verification = None
	claim["did"] = did
	claim["controller"]=address
	claim['@context'] = "https://talao.io/did/claim_documentation"
	claim["issuer"] = issuer
	claim['topic']=topicname
	if claimdata[5][:1]=="Q" :
		urldata=client.get_json(claimdata[5])
	else :
		urldata=claimdata[5]
		urldata=claimdata[4].decode('utf-8')
	claim['claim'] = {'id': claim_id, 'data' : urldata}
	claim['type']=['Keccak256(topic,issuer,data, url)','ECDSA']
	claim['signature'] = claimdata[3].hex()
	claim['authenticated']=verification
	return claim


workspace_contract='0xab6d2bAE5ca59E4f5f729b7275786979B17d224b'  # pierre david houlle
print (json.dumps(getclaim('19bfefc31e99a0775e717ec255ced95f98e2975540b230ac5ab441b621dc39d4', workspace_contract), indent=4))
