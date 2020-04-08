"""
POur ajouter un certificats sous forme de claim a un user 2 claim sontnecessaires

1) le claim du certificat, le topic est calculé sur la base du nom du projet, il est signé par la société
2) le claim "certificate" emis par le socitété dans le equel on y met la liste des claims des certificats

"""

import Talao_ipfs
import ipfshttpclient
import json


#dependances
import ADDclaim
import environment
import constante


########################################################################
#           EMISSION du certificat d'experience ERC725 NEW       
########################################################################
# @certificate = dict normé

def addcertificate(address_from, private_key_from, workspace_contract_to, certificate,mode) :
	
	
	w3=mode.initProvider()
	topicname=certificate['topicname']

	# verifier la presence de la cle 3
	_key = w3.solidityKeccak(['address'], [address_from]).hex()
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	haskey=contract.functions.keyHasPurpose(_key, 3).call()
	if haskey==False :
		return False, "cet issuer a une cle 3"

	# cacul du topic value
	topicvaluestr =''
	for i in range(0, len(topicname))  :
		a = str(ord(topicname[i]))
		if int(a) < 100 :
			a='0'+a
		topicvaluestr=topicvaluestr+a

	topicvalue=int(topicvaluestr)
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	ipfshash=client.add_json(certificate)
	client.pin.add(ipfshash)
	# emission du claim
	ADDclaim.addclaim(workspace_contract_to, address_from,private_key_from, topicname, address_from, "", ipfshash,mode) 
	# calcul du claimId du claim du certificat
	newclaimId=w3.solidityKeccak(['address', 'uint256'], [address_from, topicvalue]).hex()

	# UPDATE DE LA LISTE DE CERTIFICAT (claim "certificate" -> 99101114116105102105099097116101) du user
	topicname= "certificate"
	topicvalue = 99101114116105102105099097116101
	# determination de id du claim "certificate" de l'issuer
	claimId = w3.solidityKeccak(['address', 'uint256'], [address_from, topicvalue]).hex()
	# download du claim "certificate" de l'issuer pour update
	claimdata=contract.functions.getClaim(claimId).call()
	if claimdata[4].decode('utf-8') =='' :   # premiere fois, on cré la liste et le certificat
		data=[newclaimId]
	else :	# on update
		data=json.loads(claimdata[4].decode('utf-8'))
		data.append(newclaimId)

	newdata=json.dumps(data)
	ADDclaim.addclaim(workspace_contract_to, address_from,private_key_from, topicname, address_from, newdata, "",mode) 
	link = mode.server+'certificate/did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract_to[2:]+':claim:'+newclaimId[2:]
	return  True, link


# 'http://127.0.0.1:4000/certificate/did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:c62a385057593fe473346263f3564cf6f1d46c333a6081529c1e4864cfc9f3f1'

