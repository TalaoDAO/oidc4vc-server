import Talao_ipfs
import constante
import json
import resumejson


from web3 import Web3
my_provider = Web3.IPCProvider('/home/thierry/.ethereum/rinkeby/geth.ipc')
w3 = Web3(my_provider)

# return profil comme dictionnaire {'givenName' ; 'Jean', 'familyName' ; 'Pascal'.....
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
	
	workspace_contract=ownersToContracts(address)
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
def getDocumentIndex(address, doctype) :
	workspace_contract=ownersToContracts(address)
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	docindex=contract.functions.getDocuments().call()
	newdocindex=[]
	for i in docindex :
		doc=contract.functions.getDocument(i).call()
		if doc[0]==doctype :
			newdocindex.append(i)			
	return newdocindex

# return le doc au format json
def getDocument(address,index) :
	workspace_contract=ownersToContracts(address)
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	doc=contract.functions.getDocument(index).call()
	ipfs_hash=doc[6].decode('utf-8')
	return Talao_ipfs.IPFS_get(ipfs_hash)

def codeLanguage(code) :
	if code == 'fr' :
		return "French"
	elif code == "en" :
		return "English"
	elif code == "ge" :
		return "German"
	elif code == "da" :
		return "Danish"
	elif code=="sp" :
		return "Spanish"
	elif code=="ch" :
		return "Chineese"		
	elif code == "it" :
		return "Italian"	
	elif code== "ru" :
		return "Russian"
	elif code == "ja" :
		return "Japanese"
	elif code == "ar" :
		return "Arabic"
	elif code == "po" :
		return "Polish"
	elif code == "du" :
		return "Dutch"
	elif code == "sw" :
		return "Swedish"				
	else :
		return "unknown"	
		
		
def Proficiency(val) :
	if val == 5 :
		return 'Native or Bilingual'
	if val == 4 :
		return 'Full Professional' 
	if val == 1 :
		return 'Elementary' 
	if val == 3 :
		return 'Professional Working' 
	if val == 2 :
		return 'Limited Working' 

#############################################################
# MAIN creation de CV au format json 
#############################################################

# cv au format resume.json
# https://jsonresume.org/schema/
# legere modif pour ajouter le DID, la mobilité, la disponibilit et la TJM
# cv est un objet python de type dict
cv= resumejson.resume


address=input("Adresse = ")

# mise a jour du DID dans le resume json
private_key=ownersToContracts(address)
cv["did"]["address"]=address
cv["did"]["chain"]=constante.BLOCKCHAIN
cv["did"]["url"]=constante.WORKSPACE_LINK+private_key


# mise a jour des informatons "basics" avec le profil de Talao et ajout du prénom dans le resume json
profile=readProfil(address)
cv["basics"]["name"]=profile["familyName"]
cv["basics"]["firstname"]=profile["givenName"]
cv["basics"]["email"]=profile["email"]
cv["basics"]["website"]=profile["url"]
cv["basics"]["summary"]=profile["description"]
cv["work"][0]["company"]=profile["worksFor"]
cv["work"][0]["position"]=profile["jobTitle"]
cv["work"][0]["endDate"]="Current"



# mise a jour des "work" avec les experiences Talao
# ATTENTION la "company" n est pas dans l experience Talao...alors on l ajoute ["organization"]["name"]
# a verifier avec Guillaume
experienceIndex=getDocumentIndex(address, 50000)
for i in experienceIndex:
	experience=getDocument(address,i)
	cv["work"].append({"position" : experience["certificate"]["title"], "endDate" : experience["certificate"]["to"], "startDate" : experience["certificate"]["from"],
	"website" : experience["issuer"]["organization"]["url"], "company" : experience["issuer"]["organization"]["name"],"summary" : experience["certificate"]["description"]})
	


# mise a jour des "education"
educationIndex=getDocumentIndex(address, 40000)
for i in educationIndex:
	education=getDocument(address,i)
	cv["education"].append({"institution" : education["issuer"]["organization"]["name"], "endDate" : education["diploma"]["to"], "startDate" : education["diploma"]["from"],
	"studyType" : education["diploma"]["title"], "area" : education["diploma"]["description"]})


# mise a jour des skills, les skills Talao sont extraits des experiences et assemblés dans un seul dict du resume json
experienceIndex=getDocumentIndex(address, 50000)
skills=[]
for i in experienceIndex :
	skills.extend(getDocument(address,i)['certificate']['skills'])
skillsarray=[]
for j in range (0, len(skills)) :
	skillsarray.append(skills[j])

# elimination des doublons
new_skillsarray=[]
if len(skillsarray) > 0 :
	new_skillsarray.append(skillsarray[0])
	for i in range (1, len(skillsarray)) :
		j=0
		while j < len(new_skillsarray):
			if skillsarray[i]['name'] != new_skillsarray[j]['name'] and j== len(new_skillsarray)-1 :
				new_skillsarray.append(skillsarray[i])
			else :
				j=j+1	
	
cv["skills"]=[{"name" : "", "level" : "", "keywords" : new_skillsarray }]


# mise a jour des langages, availability, rate et mobility
docIndex=getDocumentIndex(address, 10000)
if docIndex != [] :
	doc=getDocument(address, docIndex[0])
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
		cv["languages"].append({"language" : codeLanguage(lang[i]["code"]), "fluency" : Proficiency(lang[i]["profiency"])})


# print du cv ("cv" type dict ) au format json ("cvjson" type str)
cvjson=json.dumps(cv,indent=4, sort_keys=True)
print(cvjson)

# stockage du cv au format json dans un fichier du repertoire ./json/rinkeby ou ethereum
filename = "./json/"+constante.BLOCKCHAIN+'/'+address+".json"
fichier=open(filename,"w")
fichier.write(cvjson)
fichier.close()   
