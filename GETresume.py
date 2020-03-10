import Talao_ipfs
import constante
import json
import datetime
import sys
import isolanguage
import ipfshttpclient
from eth_account.messages import encode_defunct

from web3.auto import w3



##############################################
# detrmination de la nauter de l addresse
##############################################
# @thisaddress, address
# return dictionnaire

def whatisthisaddress(thisaddress) :

	# est ce une addresse Ethereum ?
	if w3.isAddress(thisaddress) == False :
		category = False
		owner = None
		workspace= None	
	else :
		
		# test sur la nature de thisaddress
		contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
		address = contract.functions.contractsToOwners(thisaddress).call()
		workspace=contract.functions.ownersToContracts(thisaddress).call()
		
		# thisaddress est un owner
		if address == '0x0000000000000000000000000000000000000000' and workspace != '0x0000000000000000000000000000000000000000' :
			category = "owner"
			owner = thisaddress
			workspace=workspace
			
		# thisaddress est un workspace
		if address != '0x0000000000000000000000000000000000000000' and workspace == '0x0000000000000000000000000000000000000000' :
			category = 'workspace'
			owner=address
			workspace=thisaddress
		
		# thisaddressn est une addresse ethereum standard
		if address == '0x0000000000000000000000000000000000000000' and workspace == '0x0000000000000000000000000000000000000000' :
			category = 'unknown'
			owner = None
			workspace = None
			
	return {"type" : category, "owner" : owner, 'workspace' : workspace}




#########################################################################################
# return profil comme dictionnaire {'givenName' ; 'Jean', 'familyName' ; 'Pascal'.....
###########################################################################################
# return un couple (dict dictionaire,int category)

def readProfil (address, workspace_contract) :

	# setup constante
	givenName = 103105118101110078097109101
	familyName = 102097109105108121078097109101
	jobTitle = 106111098084105116108101
	worksFor = 119111114107115070111114
	workLocation = 119111114107076111099097116105111110
	url = 117114108
	email = 101109097105108
	description = 100101115099114105112116105111110
	SIRET = 83073082069084	
	adresse = 97100100114101115115
	contact = 99111110116097099116

	# initialisation de la reponse
	profil=dict()
		
	# determination de la category
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	category = contract.functions.identityInformation().call()[1]	
	
	# si profil d un individu
	if category ==1001 : 
		topicvalue =[givenName, familyName, jobTitle, worksFor, workLocation, url, email, description]
		topicname =['firstname', 'lastname', 'jobtitle', 'company', 'location', 'url', 'email', 'description']
		for i in range (0, len(topicvalue)) :
			claim=contract.functions.getClaimIdsByTopic(topicvalue[i]).call()
			if len(claim) != 0 :
				claimId=claim[0].hex()
				data = contract.functions.getClaim(claimId).call()
				if data[4].decode('utf-8') == "" or data[4].decode('utf-8')==" " :
					profil[topicname[i]]=None
				else :
					profil[topicname[i]]=data[4].decode('utf-8')			
			else :
				profil[topicname[i]]=None		
	
	# si profil d une company
	else :
		topicvalue =[givenName,url,email,contact, adresse, SIRET]
		topicname =['name', 'website', 'email', 'contact','address','SIRET']
		for i in range (0, len(topicvalue)) :
			claim=contract.functions.getClaimIdsByTopic(topicvalue[i]).call()
			if len(claim) != 0 :
				claimId=claim[0].hex()
				data = contract.functions.getClaim(claimId).call()
				if data[4].decode('utf-8') == "" or data[4].decode('utf-8')==" " :
					profil[topicname[i]]=None
				else :
					profil[topicname[i]]=data[4].decode('utf-8')										
			else :
				profil[topicname[i]]=None			
	
	return profil,category 


################################################################
# return un tableau des identifiants documents
################################################################
# doctype : integer, 10000, 40000, 50000

def getDocumentIndex(address, doctype, workspace_contract) :
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	docindex=contract.functions.getDocuments().call()
	newdocindex=[]
	for i in docindex :
		doc=contract.functions.getDocument(i).call()
		if doc[0]==doctype :
			newdocindex.append(i)			
	return newdocindex

#############################################################
# return le document au format json (str)
###############################################################
def getDocument(address,index, workspace_contract) :
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	doc=contract.functions.getDocument(index).call()
	ipfs_hash=doc[6].decode('utf-8')
	return Talao_ipfs.IPFS_get(ipfs_hash)


#######################################################
# libéllé correspondant au code		
########################################################
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
# creation de CV au format json a parir du workspace Talao
#############################################################
# utilisation geth local et IPC en light mode
# /usr/local/bin/geth --rinkeby --syncmode 'light' --rpc
#from web3 import Web3

#   did:talao:rinkeby:6FD4Cb70c7894fd84AF0708aa12636CCfEf99Ecb
def getresume(did) :
	
	didsplit=did.split(':')
	workspace_contract='0x'+didsplit[3]
	
	# calcul de l addresse du oner
	contract=w3.eth.contract(constante.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()		
		
	# determination du profil
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	(profile, category)=readProfil(address, workspace_contract)
	
	# c est un individu
	if category==1001 :
		
		# initialisation du cv
		cv={'id' : did, 'endpoint' : constante.endpoint+'resolver/'+did, 'value' :{"profil": {},"experience": [],"education": [],"skills": [{"keywords": []}],"languages": [],"availability" : {},"mobility" : {},"rate" : {}}}

		# experiences
		experienceIndex=getDocumentIndex(address, 50000, workspace_contract)
		for i in experienceIndex:
			doc=contract.functions.getDocument(i).call()
			ipfs_hash=doc[6].decode('utf-8')
			experience=Talao_ipfs.IPFS_get(ipfs_hash)
			new_experience = {
		'id' : did+':document:'+str(i),
		'endpoint' : constante.endpoint+'data/'+did+':document:'+str(i),
		'value' : {'title' : experience['certificate']['title'],
		'description' : experience['certificate']['description'],
		 'from' : experience['certificate']['from'],
		 'to' : experience['certificate']['to'],
		 'organization' : experience['issuer']['organization']}}
			del new_experience['value']['organization']['ethereum_contract']
			del new_experience['value']['organization']['ethereum_account']
			cv['value']["experience"].append(new_experience)

		# mise a jour des formations 
		educationIndex=getDocumentIndex(address, 40000, workspace_contract)
		for i in educationIndex:
			doc=contract.functions.getDocument(i).call()
			ipfs_hash=doc[6].decode('utf-8')
			education=Talao_ipfs.IPFS_get(ipfs_hash)	
			cv['value']["education"].append({'id' : did+':document:'+str(i),
			'endpoint' : constante.endpoint+'data/'+did+':document:'+str(i),
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
		cv['value']["skills"]=list(set(skillsarray))
	
		# mise a jour de la disponibilité, du TJM , de la mobilité et des langues
		docIndex=getDocumentIndex(address, 10000, workspace_contract)
		if docIndex != [] :
			doc=getDocument(address, docIndex[0], workspace_contract)
			
			# disponibilité
			cv['value']["availability"]={"update" : doc["availability"]["dateCreated"],
	"availabilitywhen" : doc["availability"]["availabilityWhen"],
	"availabilityfulltime" : doc["availability"]["availabilityFulltime"]}
			# tjm
			cv['value']["rate"]= {"rateprice" : doc["availability"]["ratePrice"],
	"ratecurrency" : doc["availability"]["rateCurrency"]}
			# mobilité
			cv['value']["mobility"]={"mobilityremote" : doc["availability"]["mobilityRemote"],
	"mobilityinternational" : doc["availability"]["mobilityInternational"], 
	"mobilityareas" : doc["availability"]["mobilityAreas"],
	"mobilityareaslist" : doc["availability"]["mobilityAreasList"]}
			# langues
			lang=doc["availability"]["languages"]
			for i in range (0, len(lang)) :
				cv['value']["languages"].append({"language" : isolanguage.Language(lang[i]["code"]),
		"fluency" : Proficiency(lang[i]["profiency"])})
	
	
		# mise en forme de la reponse
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claim=contract.functions.getClaimIdsByTopic(101109097105108).call()
		claimid=claim[0].hex()
		cv['value']["profil"]={"id" : did+':claim:'+claimid, 'endpoint' : constante.endpoint+'data/'+did+':claim:'+claimid, "value" : profile}
	
		return cv
	
	
	
	# c est une company
	else :	
		
		# initialisation du cv
		fiche={'id' : did,'endpoint' : constante.endpoint+'resolver/'+did, 'value' : {"profil": {}, 'kbis' : {}}}

		# kbis
		
		# setup variable
		kbis=dict()
		
		# initialisation IPFS
		client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	
		# doownload du claim
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claim=contract.functions.getClaimIdsByTopic(107098105115).call()
		claimId=claim[0].hex()
		claimdata = contract.functions.getClaim(claimId).call()
		issuer=claimdata[2]	
		data=claimdata[4]
		url=claimdata[5]
			
		# determination du profil de l issuer
		(issuerprofile,X)=readProfil(whatisthisaddress(issuer)["owner"], whatisthisaddress(issuer)["workspace"])

		# verification de la signature
		msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32'], [bytes('kbis', 'utf-8'), issuer, data, bytes(url, 'utf-8') ])
		message = encode_defunct(text=msg.hex())
		signature=claimdata[3]
		if signature != b"" :
			signataire=w3.eth.account.recover_message(message, signature=signature)
			signature=claimdata[3].hex()
			if signataire==issuer :
				verification=True
			else :
				verification=False	
		else :
			signature= None
			verification = False
	
	# mise en forme de la reponse
		if claimdata[5][:1]=="Q" :
			data=client.get_json(claimdata[5])
		else :
			url=claimdata[5]
			data=claimdata[4].decode('utf-8')
		kbis['data']=data
		if claimdata[5]=="" :
			kbis['value']['url']=None
		else :
			kbis['url']=claimdata[5]
		fiche['value']['kbis']={'id' :did+':claim:'+claimId, 'endpoint' : constante.endpoint+'data/'+did+':claim:'+claimId, "value" : data['KBIS']}
		
		# mise en forme de la reponse
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claim=contract.functions.getClaimIdsByTopic(101109097105108).call()
		claimid=claim[0].hex()
		fiche['value']["profil"]={"id" : did+':claim:'+claimid, 'endpoint' : constante.endpoint+'data/'+did+':claim:'+claimid, "value" : profile}
		print(fiche)	
	return fiche
