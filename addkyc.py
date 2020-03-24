"""
POur ajouter un kyc a un individual

topicID = 107121099

"""

import constante
import Talao_ipfs
import ipfshttpclient
import addclaim
import environment

# SETUP
mode=environment.currentMode('test', 'rinkeby')
mode.print_mode()
w3=mode.initProvider()



private_key_onfido="0xdd6a47a3f324d8375850104c0c41a473dabdc1742666f4c63e28cb7ff0e26bbf"
address_onfido = "0xdBEcB7f4A6f322444640b0173C81f9B0DECe0E07"
workspace_contract_pierre = "0xab6d2bAE5ca59E4f5f729b7275786979B17d224b"
address_pierre = "0xe7Ff2f6c271266DC7b354c1B376B57c9c93F0d65"
private_key_pierre = "0xf73c5085c32410657f78851386d78e84042076e762c0d1360b4b972045817e2a"



workspace_contract_to= workspace_contract_pierre
address_from = address_onfido
private_key_from = private_key_onfido
issuer = address_onfido



topicname="kyc"
kyc= {
	"country" : "FRA3",
	"id" : "15CA98225",
	"surname" : "Houlle",
	"givenname" : "Pierre david",
	"sex" : "M",
	"nationality" : "Francaise",
	"date_of_birth" : "1980-1212",
	"date_of_issue" : "2012-02-13",
	"date_of-expiration" : "2022-02-12",
	"authority" : "Prefecture de Police de Paris"
}

client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
ipfshash=client.add_json(kyc)
client.pin.add(ipfshash)
print(ipfshash)

data=""

h=addclaim.addClaim(workspace_contract_to, address_from,private_key_from, topicname, issuer, data, ipfshash,mode) 

print(h)

