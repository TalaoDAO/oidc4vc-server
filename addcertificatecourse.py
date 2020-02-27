# add certificate for courses

import sys
import csv
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import http.client
import json
from datetime import datetime

# import des fonctions custom
import Talao_token_transaction
import Talao_backend_transaction
import Talao_message
import Talao_ipfs

from web3 import Web3
my_provider = Web3.IPCProvider('/home/thierry/.ethereum/rinkeby/geth.ipc')
w3 = Web3(my_provider)

import constante

# wallet de Talaogen
talao_public_Key='0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b'
talao_private_Key='0xbbfea0f9ed22445e7f5fb1c4ca780e96c73da3c74fbce9a6972c45730a855460'

		

###############################################################
# read Talao profil
###############################################################
# return a dictionnaire {'givenName' ; 'Jean', 'familyName' ; 'Pascal'.....


def readProfil (address) :
	givenName = 103105118101110078097109101
	familyName = 102097109105108121078097109101
	jobTitle = 106111098084105116108101
	worksFor = 119111114107115070111114
	workLocation = 119111114107076111099097116105111110
	url = 117114108
	email = 101109097105108
	description = 100101115099114105112116105111110
	
	topicvalue =[givenName, familyName, jobTitle, worksFor, workLocation, url, email, description]
	topicname =['givenName', 'familyName', 'jobTitle', 'worksFor', 'workLocation', 'url', 'email', 'description']
	
	workspace_contract=Talao_token_transaction.ownersToContracts(address)
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	profil=dict()
	index=0
	for i in topicvalue :
		claim=contract.functions.getClaimIdsByTopic(i).call()
		claimId=claim[0].hex()
		data = contract.functions.getClaim(claimId).call()
		profil[topicname[index]]=data[4].decode('utf-8')
		index=index+1
	return profil


##############################################################
#             MAIN
##############################################################


# ouverture du fichier cerificate au format json
# cv inspiré du format resume.json : https://jsonresume.org/schema/
# cv={"basics": {},"work": [],"education": [],"skills": [{"keywords": []}],"languages": [],"availability" : {},"mobility" : {},"rate" : {}}
# donnez exemple ici...............
filename=input("Saisissez le nom du fichier de eertifica json ?")
resumefile=open(filename, "r")
resume=json.loads(resumefile.read())

	
# calcul du temps de process
time_debut=datetime.now()

# lecture de l addresse dans le json
address= resume["did"]["owner"]

# acces a la base de cle privée en lecture
fichiercsv= constante.BLOCKCHAIN +"_Talao_Identity.csv"
with open(fichiercsv,newline='') as csvfile:
	reader = csv.DictReader(csvfile)
	private_key="ERROR"
	# pour chaque ligne du fichier = chaque identité/workspace
	for row in reader:
		if row["ethereum_address"]==address :
			private_key=row["private_key"]
csvfile.close()
if private_key=="ERROR" :
	print("la cle  n'existe pas")
	sys.exit()	


# lecture du did
if constante.BLOCKCHAIN=='rinkeby' :
	workspace_contract="0x"+resume["did"]["did"][19:]
else :
	workspace_contract="0x"+resume["did"]["did"][21:]
print("workspace_contract =", workspace_contract)

 
# download des données du profil 
profil=readProfil(address)


# UPLOAD DES DIPLOMES
for i in range (0,len(resume['education'])) :
	data = {'documentType': 40000,
		'version': 2,
		'recipient': {'name': profil["givenName"]+' '+profil["familyName"],
		'title': profil["jobTitle"],
		'email': profil["email"],
		'ethereum_account': address,
		'ethereum_contract': workspace_contract},
		'issuer': {'organization': {'name': resume['education'][i]['institution']}},
		'diploma': {'title': resume['education'][i]['studyType'],
			'description':resume['education'][i]['area'],
			'from': resume['education'][i]['startDate'] ,
			'to': resume['education'][i]['startDate'],
			'link': resume['education'][i]['link']}}
	print("data avant transaction", json.dumps(data,indent=4))		
	Talao_token_transaction.createDocument(address, private_key, 40000, data, False)


# calcul du temps
time_fin=datetime.now()
time_delta=time_fin-time_debut
print('Durée des transactions = ', time_delta)
print('')

# fermeture des fichiers
resumefile.close()
sys.exit(0)
