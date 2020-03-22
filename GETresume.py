import Talao_ipfs
import constante
import json
import datetime
import sys
import isolanguage
import ipfshttpclient
from eth_account.messages import encode_defunct




##############################################
# detrmination de la nauter de l addresse
##############################################
# @thisaddress, address
# return dictionnaire

def whatisthisaddress(thisaddress,mode) :

	w3=mode.initProvider()

	# est ce une addresse Ethereum ?
	if w3.isAddress(thisaddress) == False :
		category = False
		owner = None
		workspace= None	
	else :
		
		# test sur la nature de thisaddress
		contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
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

def readProfil (address, workspace_contract, mode) :

	w3=mode.initProvider()

	# setup constante
	givenName = 103105118101110078097109101 # = firstname
	familyName = 102097109105108121078097109101 # = lastname
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
		topicvalue =[givenName,url,email,contact, adresse]
		topicname =['name', 'website', 'email', 'contact','address']
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

def getDocumentIndex(address, doctype, workspace_contract,mode) :

	w3=mode.initProvider()

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
def getDocument(address,index, workspace_contract, mode) :
	w3=mode.initProvider()

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
# creation de CV/fiche au format json a parir du workspace Talao
#############################################################
# utilisation geth local et IPC en light mode
# /usr/local/bin/geth --rinkeby --syncmode 'light' --rpc
#from web3 import Web3

def getresume(did, mode) :
	w3=mode.initProvider()

	didsplit=did.split(':')
	workspace_contract='0x'+didsplit[3]
	
	# calcul de l addresse du oner
	contract=w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()		
		
	# determination du profil
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	(profile, category)=readProfil(address, workspace_contract,mode)
	
	
##################################################################################	
#                                INDIVIDUAL
##################################################################################
	if category==1001 :
		
		# initialisation du cv
		cv={'id' : did,
			'endpoint' : mode.server+'resolver/'+did,
			'methods' : ['GET'],
			'value' :{"profil": {},
				"nationalidentity" : {"passport" : None, "kyc" : None, "driving_license" : None},
				"experience": [],
				"education": [],
				"skills": [{"keywords": []}],
				"languages": [],
				"availability" : {},
				"mobility" : {},
				"rate" : {}}}


		# KYC
		
		# setup variable
		kyc=dict()
		# initialisation IPFS
		client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	
		# download du claim du kyc 107121099 => le dernier efface  le precedent si eme issuer
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claim=contract.functions.getClaimIdsByTopic(107121099).call()
		if len(claim) == 0 : # pas de KBIS
			cv['value']['nationalidentity']["kyc"]=None 
		else : 			
			
			claimId=claim[len(claim)-1].hex() # ???? le seul ????
			claimdata = contract.functions.getClaim(claimId).call()
			issuer=claimdata[2]	
			data=claimdata[4]
			url=claimdata[5]
			# determination du profil de l issuer du KYC
			(issuerprofile,X)=readProfil(whatisthisaddress(issuer,mode)["owner"], whatisthisaddress(issuer,mode)["workspace"],mode)
			# verification de la signature du KYC
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
			# mise en forme du KYC
			if claimdata[5][:1]=="Q" :
				data=client.get_json(claimdata[5])
			else :
				url=claimdata[5]
				data=claimdata[4].decode('utf-8')
			kyc['data']=data
			if claimdata[5]=="" :
				kyc['value']['url']=None
			else :
				kyc['url']=claimdata[5]
			
			cv['value']['nationalidentity']["kyc"]={'id' :did+':claim:'+claimId, 'endpoint' : mode.server+'data/'+did+':claim:'+claimId, "methods" : ["GET"],"value" : data}
		


		# experiences
		experienceIndex=getDocumentIndex(address, 50000, workspace_contract,mode)
		for i in experienceIndex:
			doc=contract.functions.getDocument(i).call()
			ipfs_hash=doc[6].decode('utf-8')
			experience=Talao_ipfs.IPFS_get(ipfs_hash)
			new_experience = {
		'id' : did+':document:'+str(i),
		'endpoint' : mode.server+'talao/api/data/'+did+':document:'+str(i),
		'methods' : ['GET'],
		'value' : {'title' : experience['certificate']['title'],
		'description' : experience['certificate']['description'],
		 'from' : experience['certificate']['from'],
		 'to' : experience['certificate']['to'],
		 'organization' : experience['issuer']['organization']}}
			del new_experience['value']['organization']['ethereum_contract']
			del new_experience['value']['organization']['ethereum_account']
			cv['value']["experience"].append(new_experience)

		# certificates
		experienceIndex=getDocumentIndex(address, 60000, workspace_contract, mode)
		for i in experienceIndex:
			doc=contract.functions.getDocument(i).call()
			ipfs_hash=doc[6].decode('utf-8')
			experience=Talao_ipfs.IPFS_get(ipfs_hash)
			new_experience = {
		'id' : did+':document:'+str(i),
		'endpoint' : mode.server+'talao/api/data/'+did+':document:'+str(i),
		'methods' : ['GET'],
		'value' : {'title' : experience['certificate']['title'],
		'description' : experience['certificate']['description'],
		 'from' : experience['certificate']['from'],
		 'to' : experience['certificate']['to'],
		 'organization' : experience['issuer']['organization']}}
			del new_experience['value']['organization']['ethereum_contract']
			del new_experience['value']['organization']['ethereum_account']
			cv['value']["experience"].append(new_experience)
		
		# mise a jour des formations 
		educationIndex=getDocumentIndex(address, 40000, workspace_contract,mode)
		for i in educationIndex:
			doc=contract.functions.getDocument(i).call()
			ipfs_hash=doc[6].decode('utf-8')
			education=Talao_ipfs.IPFS_get(ipfs_hash)	
			cv['value']["education"].append({'id' : did+':document:'+str(i),
			'endpoint' : mode.server+'talao/api/data/'+did+':document:'+str(i),
			'methods' : ['GET'],
			'value' : {	"organization" : education["issuer"]["organization"]["name"],
			"endDate" : education["diploma"]["to"], 
			"startDate" : education["diploma"]["from"],
			"studyType" : education["diploma"]["title"],
			"area" : education["diploma"]["description"],
			"link" : education["diploma"]["link"]}})

		# mise a jour des "skills", les skills Talao sont extraits des experiences et assemblés dans un seul dict du resume json
		experienceIndex=getDocumentIndex(address, 50000, workspace_contract,mode)
		skills=[]
		for i in experienceIndex :
			skills.extend(getDocument(address,i, workspace_contract,mode)['certificate']['skills'])
		skillsarray=[]
		for j in range (0, len(skills)) :
			skillsarray.append(skills[j]['name'])
		# elimination des doublons
		cv['value']["skills"]=list(set(skillsarray))
	
		# mise a jour de la disponibilité, du TJM , de la mobilité et des langues
		docIndex=getDocumentIndex(address, 10000, workspace_contract,mode)
		if docIndex != [] :
			doc=getDocument(address, docIndex[0], workspace_contract,mode)
			
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
		cv['value']["profil"]={"id" : did+':claim:'+claimid, 'endpoint' : mode.server+'talao/api/data/'+did+':claim:'+claimid, "methods" : ["GET"],"value" : profile}
	
		return cv	
	
##################################################################################################	
#                                   COMPANY
##################################################################################################
	else :	
		
		# initialisation du cv
		fiche={'id' : did,'endpoint' : mode.server+'resolver/'+did, 'value' : {"profil": {}, 'kbis' : {}}}

		# kbis
		
		# setup variable
		kbis=dict()
		
		# initialisation IPFS
		client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	
		# download du claim du dernier KBIS 107098105115) => le dernier est supposé etre le bon ...................a discuter !!!!
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claim=contract.functions.getClaimIdsByTopic(107098105115).call()
		if len(claim) == 0 : # pas de KBIS
			fiche['value']['kbis'] = {}
		else : 			
			claimId=claim[len(claim)-1].hex()
			claimdata = contract.functions.getClaim(claimId).call()
			issuer=claimdata[2]	
			data=claimdata[4]
			url=claimdata[5]
			# determination du profil de l issuer du KBIS
			(issuerprofile,X)=readProfil(whatisthisaddress(issuer,mode)["owner"], whatisthisaddress(issuer,mode)["workspace"],mode)
			# verification de la signature du KBIS
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
			# mise en forme du KBIS
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
			
			fiche['value']['kbis']={'id' :did+':claim:'+claimId, 'endpoint' : mode.server+'talao/api/data/'+did+':claim:'+claimId, "methods" : ["GET"],"value" : data}
		
		
		
		# mise en forme de la fiche company
		contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claim=contract.functions.getClaimIdsByTopic(101109097105108).call()
		claimid=claim[0].hex()
		fiche['value']["profil"]={"id" : did+':claim:'+claimid, 'endpoint' : mode.server+'talao/api/data/'+did+':claim:'+claimid, "methods" : ["GET"], "value" : profile}
	
	return fiche
