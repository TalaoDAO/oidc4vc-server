"""
POur ajouter un certificats sous forme de claim a un user 2 claim sontnecessaires

1) le claim du certificat, le topic est calculé sur la base du nom du projet, il est signé par la société
2) le claim "certificate" emis par le socitété dans le equel on y met la liste des claims des certificats






"""

import constante
import Talao_ipfs
import ipfshttpclient
import addclaim
import environment
import json
import http.client, urllib.parse





########################################################################
#           EMISSION du certificat d'experience ERC725 NEW       
########################################################################
# @certificate = dict normé

def addcertificate(address_from, private_key_from, workspace_contract_to, certificate) :

	topicname=certificate['topicname']

	# verifier la presence de la cle 3
	_key = w3.solidityKeccak(['address'], [address_from]).hex()
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	haskey=contract.functions.keyHasPurpose(_key, 3).call()
	if haskey==False :
		return {"ERROR" : "cet issuer a une cle 3"}

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
	h=addclaim.addClaim(workspace_contract_to, address_from,private_key_from, topicname, issuer, "", ipfshash,mode) 

	# calcul du claimId du claim du certificat
	newclaimId=w3.solidityKeccak(['address', 'uint256'], [address_from, topicvalue]).hex()

	# UPDATE DE LA LISTE DE CERTIFICAT (claim "certificate" -> 99101114116105102105099097116101) du user
	topicname= "certificate"
	topicvalue = 99101114116105102105099097116101

	# determination de id du claim "certificate" de l'issuer
	claimId = w3.solidityKeccak(['address', 'uint256'], [address_from, topicvalue]).hex()

	# download du claim "certificate" de l'issuer
	claimdata=contract.functions.getClaim(claimId).call()
	if claimdata[4].decode('utf-8') =='' :   # premiere fois, on cré la liste et le certificat
		data=[newclaimId]
	else :	# on update
		data=json.loads(claimdata[4].decode('utf-8'))
		data.append(newclaimId)

	newdata=json.dumps(data)
	addclaim.addClaim(workspace_contract_to, address_from,private_key_from, topicname, address_from, newdata, "",mode) 

	return  True






# SETUP
mode=environment.currentMode('test', 'rinkeby')
w3=mode.initProvider()


# pour les test
private_key_onfido="0xdd6a47a3f324d8375850104c0c41a473dabdc1742666f4c63e28cb7ff0e26bbf"
address_onfido = "0xdBEcB7f4A6f322444640b0173C81f9B0DECe0E07"

workspace_contract_pierre = "0xab6d2bAE5ca59E4f5f729b7275786979B17d224b"
address_pierre = "0xe7Ff2f6c271266DC7b354c1B376B57c9c93F0d65"
private_key_pierre = "0xf73c5085c32410657f78851386d78e84042076e762c0d1360b4b972045817e2a"

address_thales="0x60f6876F2880fB5c92Caad1C3002356d2F33b770"
private_key_thales="0xe194d61bff666d67ca98e89bd8e266c0ca2dd7ba16d2b2256a2c0463e1b67070"

workspace_contract_to= workspace_contract_pierre
address_from = address_thales
private_key_from = private_key_thales
issuer = address_thales
address_to ='0xe7Ff2f6c271266DC7b354c1B376B57c9c93F0d65'



certificate={"did_issuer" : "did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b", 
	"did_user" : "",
	"topicname" : "Projet Opto Meganne",
	"type" : "experience",	
	"firstname" : "David",
	"name" : "Houlle",
	"company" : {"name" : "Thales", "manager" : "Jean Permet", "managersignature" : "experingsignature.png",
		"companylogo" : "thaleslogo.jpeg", 'manager_email' : "jean.permet@thales.com"},
	"startDate" : "2018-06-01",
	"endDate" :"2018-10-01",
	"summary" :  "New SUV Project. Development of a new large-dimension hybrid vehicle SUV for the premium automotive segment. Technical, economic and human challenge with the setup of a new production plant in North America",
	"skills" : "Optoelectronics			IRST system		CAO/DAO",
	"position" : "Manager for SUV project",
	"score_recommendation" : 2,
	"score_delivery" : 3,
	"score_schedule" : 3,
	"score_communication" : 5}


#print (addcertificate(address_from, private_key_from, workspace_contract_to, certificate))



conn = http.client.HTTPConnection('localhost:5000')
headers = {'Accept': 'application/json','Content-type': 'application/json', "Authorization" : "Bearer sdsdsds"}
payload = certificate
data = json.dumps(payload)
conn.request('POST', '/certificate/',data, headers)
response = conn.getresponse()
res=response.read()
#print(json.loads(res))
