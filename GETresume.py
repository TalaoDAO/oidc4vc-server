import Talao_ipfs
import constante
import json
import datetime
import sys
import isolanguage
import GETresume
from web3.auto import w3


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

# return le doc au format json (str)
def getDocument(address,index, workspace_contract) :
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	doc=contract.functions.getDocument(index).call()
	ipfs_hash=doc[6].decode('utf-8')
	return Talao_ipfs.IPFS_get(ipfs_hash)

# retourne le langage
def codeLanguage(code) :
	return isolanguage.Language(code)
		
# retourne le libéllé correspondant au code		
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



def getresume(workspace_contract) :
#############################################################
# MAIN creation de CV au format json a parir du workspace Talao
#############################################################
# cv inspiré du format resume.json : https://jsonresume.org/schema/

# utilisation geth local et IPC en light mode
# /usr/local/bin/geth --rinkeby --syncmode 'light' --rpc
#from web3 import Web3

	
	did='did:talao:rinkeby:'+workspace_contract[2:]	
	# cv est un Dict
	cv={"basics": {},"experience": [],"education": [],"skills": [{"keywords": []}],"languages": [],"availability" : {},"mobility" : {},"rate" : {}}
	
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()		
	
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	# mise a jour des informatons "basics" avec le profil de Talao et ajout du prénom dans le resume json
	profile=readProfil(address, workspace_contract)
	cv["basics"]={"name" : profile["familyName"],
	"firstname" : profile["givenName"],
	"email" : profile["email"],
	"website" : profile["url"],
	"summary" : profile["description"],
	"image" : '',
	"company" : profile["worksFor"],
	"position" : profile["jobTitle"],
	"startdate" : "unknown",
	"summary" : "",
	"website" : ""}
	
	
	# experiences
	experienceIndex=getDocumentIndex(address, 50000, workspace_contract)
	for i in experienceIndex:
		doc=contract.functions.getDocument(i).call()
		ipfs_hash=doc[6].decode('utf-8')
		experience=Talao_ipfs.IPFS_get(ipfs_hash)
		new_experience = {
		'id' : did+':document:'+str(i),
		'value' : {'title' : experience['certificate']['title'],
		'description' : experience['certificate']['description'],
		 'from' : experience['certificate']['from'],
		 'to' : experience['certificate']['to'],
		 'organization' : experience['issuer']['organization']}}
		del new_experience['value']['organization']['ethereum_contract']
		del new_experience['value']['organization']['ethereum_account']
		cv["experience"].append(new_experience)


	# mise a jour des formations 
	educationIndex=getDocumentIndex(address, 40000, workspace_contract)
	for i in educationIndex:
		doc=contract.functions.getDocument(i).call()
		ipfs_hash=doc[6].decode('utf-8')
		education=Talao_ipfs.IPFS_get(ipfs_hash)	
		cv["education"].append({'id' : did+':document:'+str(i),
	'value' : {	"organization" : education["issuer"]["organization"]["name"],
	 "endDate" : education["diploma"]["to"], 
	 "startDate" : education["diploma"]["from"],
	"studyType" : education["diploma"]["title"],
	 "area" : education["diploma"]["description"],
	 "link" : education["diploma"]["link"]}})


	# mise a jour des "skills", les skills Talao sont extraits des experiences et assemblés dans un seul dict du resume json
	experienceIndex=getDocumentIndex(address, 50000, workspace_contract)
	skills=[]
	for i in experienceIndex :
		skills.extend(getDocument(address,i, workspace_contract)['certificate']['skills'])
	skillsarray=[]
	for j in range (0, len(skills)) :
		skillsarray.append(skills[j]['name'])
	# elimination des doublons
	cv["skills"]=list(set(skillsarray))
	

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
	return cv
