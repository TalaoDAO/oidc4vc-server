import Talao_ipfs
import constante
import json
import datetime
from web3 import Web3
import sys

import isolanguage

# return profil comme dictionnaire {'givenName' ; 'Jean', 'familyName' ; 'Pascal'.....
def readProfil (address, workspace_contract) :
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
	
# return workspace address
def ownersToContracts(address) :
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	workspace_address = contract.functions.ownersToContracts(address).call()
	return workspace_address

# return un array des docs valides
def getDocumentIndex(address, doctype, workspace_contract) :
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	docindex=contract.functions.getDocuments().call()
	newdocindex=[]
	for i in docindex :
		doc=contract.functions.getDocument(i).call()
		if doc[0]==doctype :
			newdocindex.append(i)			
	return newdocindex

# return le doc au format json
def getDocument(address,index, workspace_contract) :
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	doc=contract.functions.getDocument(index).call()
	ipfs_hash=doc[6].decode('utf-8')
	return Talao_ipfs.IPFS_get(ipfs_hash)

# retourne le langage
def codeLanguage(code) :
	return isolanguage.Language(code)
		
		
def Proficiency(val) :
	if val == '5' or  val == 5 :
		return 'Native or Bilingual'
	if val == '4' or val== 4 :
		return 'Full Professional' 
	if val == '1'  or val == 1 :
		return 'Elementary' 
	if val == '3' or val == 3 :
		return 'Professional Working' 
	if val == '2' or val== 2 :
		return 'Limited Working' 
	else :
		return None

#############################################################
# MAIN creation de CV au format json a parir du workspace Talao
#############################################################
# cv inspiré du format resume.json : https://jsonresume.org/schema/

# utilisation geth local et IPC en light mode
# /usr/local/bin/geth --rinkeby --syncmode 'light' --rpc
if constante.BLOCKCHAIN == 'rinkeby' :
	my_provider = Web3.IPCProvider('/home/thierry/.ethereum/rinkeby/geth.ipc')
else :
	print('Erreur de reseau')
	sys.exit()
w3 = Web3(my_provider)

# cv est un objet python de type dict
cv={"did": {},"basics": {},"work": [],"education": [],"skills": [{"keywords": []}],"languages": [],"availability" : {},"mobility" : {},"rate" : {}}

# Saisie de l'adresse du DID
address=input("Adresse = ")
try :
	workspace_contract=ownersToContracts(address)		
except  :
    print ("Cette adresse n'est pas celle d'une identité")
    sys.exit()
print("did = ", "did:erc725:"+constante.BLOCKCHAIB+":0x"+address[2:]	
	
# mise a jour du DID dans le resume json
# did:erc725:rinkeby:2F2B37C890824242Cb9B0FE5614fA2221B79901E
# https://w3id.org/did/v1
cv["id"]={"@context" : "https://w3id.org/did/v1",
	"did" : "did:erc725:"+constante.BLOCKCHAIN+":"+workspace_contract[2:],
	"protocol" : "Talao",
	"owner" : address,
	"workspace_link" : constante.WORKSPACE_LINK+workspace_contract}


# mise a jour des informatons "basics" avec le profil de Talao et ajout du prénom dans le resume json
profile=readProfil(address, workspace_contract)
cv["basics"]={"name" : profile["familyName"],
	"firstname" : profile["givenName"],
	"email" : profile["email"],
	"website" : profile["url"],
	"summary" : profile["description"],
	"picture" : ''}


# mise a jour des experiences
# ATTENTION l'employeur (company) n'est pas dans l experience Talao...alors on l ajoute ["organization"]["name"]
# experience 0 = emploi actuel,obtenu du profil
cv["work"].append({"company" : profile["worksFor"],
	"position" : profile["jobTitle"],
	"endDate" : str(datetime.date.today()),
	"startDate" : str(datetime.date.today()),
	"summary" : "",
	"website" : ""})
# autres experiences
experienceIndex=getDocumentIndex(address, 50000, workspace_contract)
for i in experienceIndex:
	experience=getDocument(address,i, workspace_contract)
	cv["work"].append({"company" : experience["issuer"]["organization"]["name"],
	"position" : experience["certificate"]["title"],
	"endDate" : experience["certificate"]["to"],
	"startDate" : experience["certificate"]["from"],	
	"summary" : experience["certificate"]["description"],
	"website" : experience["issuer"]["organization"]["url"]})	


# mise a jour des formations 
educationIndex=getDocumentIndex(address, 40000, workspace_contract)
for i in educationIndex:
	education=getDocument(address,i, workspace_contract)
	cv["education"].append({"institution" : education["issuer"]["organization"]["name"],
	 "endDate" : education["diploma"]["to"], 
	 "startDate" : education["diploma"]["from"],
	"studyType" : education["diploma"]["title"],
	 "area" : education["diploma"]["description"],
	 "link" : education["diploma"]["link"]})



# mise a jour des "skills", les skills Talao sont extraits des experiences et assemblés dans un seul dict du resume json
experienceIndex=getDocumentIndex(address, 50000, workspace_contract)
skills=[]
for i in experienceIndex :
	skills.extend(getDocument(address,i, workspace_contract)['certificate']['skills'])
skillsarray=[]
for j in range (0, len(skills)) :
	skillsarray.append(skills[j]['name'])
# elimination des doublons
new_skillsarray=list(set(skillsarray))
cv["skills"]=[{"keywords" : new_skillsarray }]


# mise a jour de la disponibilité, du TJM , de la mobilité et des langues
docIndex=getDocumentIndex(address, 10000, workspace_contract)
if docIndex != [] :
	doc=getDocument(address, docIndex[0], workspace_contract)
	cv["availability"]={"update" : doc["availability"]["dateCreated"],
	"availabilitywhen" : doc["availability"]["availabilityWhen"],
	"availabilityfulltime" : doc["availability"]["availabilityFulltime"]}
	cv["rate"]= {"rateprice" : doc["availability"]["ratePrice"],
	"ratecurrency" : doc["availability"]["rateCurrency"]}
	cv["mobility"]={"mobilityremote" : doc["availability"]["mobilityRemote"],
	"mobilityinternational" : doc["availability"]["mobilityInternational"], 
	"mobilityareas" : doc["availability"]["mobilityAreas"],
	"mobilityareaslist" : doc["availability"]["mobilityAreasList"]}
	lang=doc["availability"]["languages"]
	for i in range (0, len(lang)) :
		cv["languages"].append({"language" : codeLanguage(lang[i]["code"]),
		"fluency" : Proficiency(lang[i]["profiency"])})


# serialisation du cv ("cv" -> type dict ) au format json ("cvjson" -> type str)
cvjson=json.dumps(cv,indent=4)

# print pour test
print(cvjson)

# stockage du cv au format json dans le repertoire ./json/rinkeby ou ./json/ethereum
filename = "./json/"+constante.BLOCKCHAIN+'/'+address+".json"
fichier=open(filename,"w")
fichier.write(cvjson)
fichier.close()   
