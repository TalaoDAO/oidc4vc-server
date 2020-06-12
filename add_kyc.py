"""
POur ajouter un kyc a un individual

topicID = 107121099

"""

import constante
import environment
from protocol import Kyc, addkey


# environment setup
mode=environment.currentMode()
w3=mode.w3

identity_workspace_contract = '0xEc0Cf3FA4158D8dd098051cfb14af7b4812d51aF' # pascalet
identity_address = '0x048D19e72030a9D7a949517D5a9E3844b4533fc2'
identity_private_key = '0xbde83886a9830b00616cd4877e434f61bab8307a050e0d081fa869f41073de62'

# add key 20002 to talao

addkey(identity_address, identity_workspace_contract, identity_address, identity_workspace_contract, identity_private_key, mode.owner_talao, 20002,mode)

topicname="kyc"

kyc_jean = Kyc()

kyc= {
	"country" : "FRA3",
	"card_id" : "15CA98365",
	"firstname" : "Jean",
	"lastname" : "Pascalet",
	"sex" : "M",
	"nationality" : "Francaise",
	"birthdate" : "1972/12/12",
	"date_of_issue" : "2012/02/13",
	"date_of_expiration" : "2022/02/12",
	"authority" : "Prefecture de Police de Paris"
}

kyc_jean.talao_add(identity_workspace_contract, kyc, mode) 
