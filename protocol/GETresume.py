import json
import datetime
from datetime import datetime
import sys
import ipfshttpclient
from eth_account.messages import encode_defunct

#dependances
import isolanguage
import Talao_ipfs
import constante
from .Talao_token_transaction import isdid, contractsToOwners, createDocument
from .document import Experience
from .ADDdocument import getdocument
from .claim import Claim

#####################################################	
# read contenu du claim stocké sur IPFS
######################################################
def getclaimipfs (claim_id, workspace_contract, mode) :
# @topicname est un str
# return un objet List
	
	
	w3=mode.initProvider()
	
	# initialisation
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	claimdata=contract.functions.getClaim(claim_id).call()

	if claimdata[5]!="" :
		data=client.get_json(claimdata[5])
		return data
	else :
		return False

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

def readProfil (workspace_contract, mode) :

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
	profil = dict()
		
	# determination de la category
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	category = contract.functions.identityInformation().call()[1]	
	
	# si profil d un individu
	if category == 1001 : 
		topicvalue = [givenName, familyName, jobTitle, worksFor, workLocation, url, email, description]
		topicname = ['firstname', 'lastname', 'jobtitle', 'company', 'location', 'url', 'email', 'description']
		for i in range (0, len(topicvalue)) :
			try :
				claim=contract.functions.getClaimIdsByTopic(topicvalue[i]).call()
			except :
				claim = []
			if len(claim) != 0 :
				claimId = claim[-1].hex()
				data = contract.functions.getClaim(claimId).call()
				if data[4].decode('utf-8') == "" or data[4].decode('utf-8')==" " :
					profil[topicname[i]] = None
				else :
					profil[topicname[i]]=data[4].decode('utf-8')			
			else :
				profil[topicname[i]] = None		
	
	# si profil d une company
	else :
		topicvalue = [givenName,url,email,contact, adresse]
		topicname = ['name', 'website', 'email', 'contact','address']
		for i in range (0, len(topicvalue)) :
			try :
				claim = contract.functions.getClaimIdsByTopic(topicvalue[i]).call()
			except :
				claim = []
			if len(claim) != 0 :
				claimId = claim[-1].hex()
				data = contract.functions.getClaim(claimId).call()
				if data[4].decode('utf-8') == "" or data[4].decode('utf-8')==" " :
					profil[topicname[i]] = None
				else :
					profil[topicname[i]] = data[4].decode('utf-8')										
			else :
				profil[topicname[i]] = None				
	return profil,category 

################################################################
# return un tableau des identifiants documents
################################################################
# doctype : integer, 10000, 40000, 50000, 15000

def getDocumentIndex(doctype, workspace_contract,mode) :

	w3 = mode.initProvider()

	contract = w3.eth.contract(workspace_contract,abi = constante.workspace_ABI)
	docindex = contract.functions.getDocuments().call()
	newdocindex = []
	for i in docindex :
		doc = contract.functions.getDocument(i).call()
		if doc[0] == doctype :
			newdocindex.append(i)			
	return newdocindex

#############################################################
# return le document au format dict
###############################################################
def getDocument(address,index, workspace_contract, mode) :
	
	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	doc = contract.functions.getDocument(index).call()
	ipfs_hash = doc[6].decode('utf-8')
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

def getresume(workspace_contract,did, mode) :
	
	w3=mode.w3
	
	# address validity
	category = whatisthisaddress(workspace_contract,mode)["type"]
	if category != 'workspace' :
		return False
	
	# owner address
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	address = contract.functions.contractsToOwners(workspace_contract).call()		
	
	# profil
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	(profile, category)=readProfil( workspace_contract,mode)
	del profile['email']
	
	
#  individual 
	if category == 1001 :
		
		# general cv setup
		cv={'id' : did,
			'DID_Document' : mode.server+'resolver/'+did,
			'data' :{"personal": [],
				"experience": [],
				"education": [],
				"skills": [{"keywords": []}],
				"languages": [],
				"availability" : {},
				"mobility" : {},
				"rate" : {}}}


		# Personal data	
		thistopic = {'firstname' :103105118101110078097109101 ,
				'lastname' : 102097109105108121078097109101,
				'jobtitle' : 106111098084105116108101,
				'company' : 119111114107115070111114,
				'location' : 119111114107076111099097116105111110,
				'url' : 117114108,
				'email' : 101109097105108,
				'description' : 100101115099114105112116105111110,
				'picture' : 105109097103101 	}
		for key in profile :				
			contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
			claim = contract.functions.getClaimIdsByTopic(thistopic[key]).call() # topic = name
			isKey = True
			try :
				claimid = claim[len(claim)-1].hex()
			except :
				isKey = False
			if isKey :
				cv['data']["personal"].append({key : {"id" : did+':claim:'+claimid, 'endpoint' : mode.server+'talao/data/'+did+':claim:'+claimid,"data" : profile.get(key)}})
		
		# Contact cf ADDdocument , document de type 15000, crypté ou pas mais on ne passe pas la cle pour decrypter		
		contactIndex = getDocumentIndex(15000, workspace_contract,mode)
		for i in contactIndex:
			contact = getdocument(workspace_contract, '0x0', workspace_contract, i, mode)		
			if contact == None :
				contact = { 'email' : 'encrypted', 'phone' : 'encrypted', 'twitter' : 'encrypted'}
			cv['data']['personal'].append({"contact" : {"id" : did+':document:'+str(i), 'endpoint' : mode.server+'talao/data/'+did+':document:'+str(i),"data" : contact}})
		
		# KYC data
		# setup variable
		kyc = dict()
		# initialisation IPFS
		client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	
		# download du claim du kyc 107121099 => le dernier efface  le precedent si eme issuer
		contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claim = contract.functions.getClaimIdsByTopic(107121099).call()
		if len(claim) != 0 : # il y a un  KBIS
			
			claimId = claim[len(claim)-1].hex() # ???? le seul ????
			claimdata = contract.functions.getClaim(claimId).call()
			issuer = claimdata[2]	
			data = claimdata[4]
			url = claimdata[5]
			# determination du profil de l issuer du KYC
			(issuerprofile,X) = readProfil( whatisthisaddress(issuer,mode)["workspace"],mode)
			# verification de la signature du KYC
			msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32'], [bytes('kbis', 'utf-8'), issuer, data, bytes(url, 'utf-8') ])
			message = encode_defunct(text=msg.hex())
			signature = claimdata[3]
			if signature != b"" :
				signataire = w3.eth.account.recover_message(message, signature=signature)
				signature = claimdata[3].hex()
				if signataire == issuer :
					verification = True
				else :
					verification = False	
			else :
				signature = None
				verification = False
			# mise en forme du KYC
			if claimdata[5][:1] == "Q" :
				data = client.get_json(claimdata[5])
			else :
				url = claimdata[5]
				data = claimdata[4].decode('utf-8')
			kyc['id'] = did + ':claim:' + claimId
			kyc['endpoint'] = mode.server + 'talao/data/' + did + ':claim:' + claimId
			kyc['data'] = data
			cv['data']['personal'].append({"kyc" : kyc})

		# basic experiences = document 50000
		experienceIndex = getDocumentIndex(50000, workspace_contract,mode)
		for i in experienceIndex:
			doc = contract.functions.getDocument(i).call()
			ipfs_hash=doc[6].decode('utf-8')
			experience = Talao_ipfs.IPFS_get(ipfs_hash)
			new_experience = {
				'id' : did+':document:'+str(i),
				'endpoint' : mode.server+'talao/data/'+did+':document:'+str(i),
				'data' : {'title' : experience['certificate']['title'],
				'description' : experience['certificate']['description'],
				'from' : experience['certificate']['from'],
				'to' : experience['certificate']['to'],
				'organization' : {"name" : None, 
						"contact_name" : experience['issuer']['responsible']["name"],
						"contact_email" : experience["issuer"]["organization"]["email"]
						},
				"certification_link" : None
				}}			
			cv['data']["experience"].append(new_experience)
	
		# experiences certified = document 60000
		experienceIndex = getDocumentIndex(60000, workspace_contract, mode)
		for i in experienceIndex:
			doc = contract.functions.getDocument(i).call()
			ipfs_hash = doc[6].decode('utf-8')
			experience = Talao_ipfs.IPFS_get(ipfs_hash)
			new_experience = {
				'id' : did+':document:'+str(i),
				'endpoint' : mode.server+'talao/data/'+did+':document:'+str(i),
				'data' : {'title' : experience['certificate']['title'],
				'description' : experience['certificate']['description'],
				'from' : experience['certificate']['from'],
				'to' : experience['certificate']['to'],
				'organization' : {"name" : None, 
						"contact_name" : experience['issuer']['responsible']["name"],
						"contact_email" : experience["issuer"]["organization"]["email"]
						},
				"certification_link" : None
				}}
			cv['data']["experience"].append(new_experience)
		
		# experiences certified with  claim725		
		# download claim "certificate"->  99101114116105102105099097116101 du user
		claimlist = contract.functions.getClaimIdsByTopic(99101114116105102105099097116101).call()
		for claimId in claimlist : #pour chaque issuer
			claimdata = contract.functions.getClaim(claimId).call()
			if claimdata[4].decode('utf-8') != '' :   # il existe des certificats
				certificatelist=json.loads(claimdata[4].decode('utf-8'))
				for certificateId in certificatelist :
					certificate = getclaimipfs(certificateId, workspace_contract,mode)
					if certificate != False : # on evite dans le cas ou le certificat a été effacé mais pas retiré de la lsite
						new_certificate = {'id' : did+':claim:'+certificateId[2:],
											'endpoint' : mode.server+'talao/data/'+did+':claim:'+certificateId[2:],
											'data' : {'title' : certificate['position'],
											'description' : certificate['summary'],
											'from' : certificate['startDate'],
											'to' : certificate['endDate'],
											'organization' : { "name" : certificate['company']['name'],
																"contact_name" : certificate['company']['manager'],
																"contact_email" : certificate['company'].get('manager_email')
											},
						'certificate_link' : mode.server+'certificate/'+did+':claim:'+certificateId[2:]}}												
						cv['data']["experience"].append(new_certificate)
		
		# education = document 40000 
		educationIndex = getDocumentIndex(40000, workspace_contract,mode)
		for i in educationIndex:
			doc = contract.functions.getDocument(i).call()
			ipfs_hash = doc[6].decode('utf-8')
			education = Talao_ipfs.IPFS_get(ipfs_hash)	
			cv['data']["education"].append({'id' : did+':document:'+str(i),
			'endpoint' : mode.server+'talao/data/'+did+':document:'+str(i),
			'data' : {	"organization" : education["issuer"]["organization"]["name"],
			"endDate" : education["diploma"]["to"], 
			"startDate" : education["diploma"]["from"],
			"studyType" : education["diploma"]["title"],
			"area" : education["diploma"]["description"],
			"certificate_link" : education["diploma"]["link"]}})

		# mise a jour des "skills", les skills Talao sont extraits des experiences et assemblés dans un seul dict du resume json
		experienceIndex = getDocumentIndex(50000, workspace_contract,mode)
		skills = []
		for i in experienceIndex :
			skills.extend(getDocument(address,i, workspace_contract,mode)['certificate']['skills'])
		skillsarray = []
		for j in range (0, len(skills)) :
			skillsarray.append(skills[j]['name'])
		# elimination des doublons
		cv['data']["skills"] = list(set(skillsarray))
	
		# mise a jour de la disponibilité, du TJM , de la mobilité et des langues
		docIndex = getDocumentIndex(10000, workspace_contract,mode)
		if docIndex != [] :
			doc=getDocument(address, docIndex[0], workspace_contract,mode)
			
			# disponibilité
			cv['data']["availability"] = {"update" : doc["availability"]["dateCreated"],
	"availabilitywhen" : doc["availability"]["availabilityWhen"],
	"availabilityfulltime" : doc["availability"]["availabilityFulltime"]}
			# tjm
			cv['data']["rate"] = {"rateprice" : doc["availability"]["ratePrice"],
	"ratecurrency" : doc["availability"]["rateCurrency"]}
			# mobilité
			cv['data']["mobility"] = {"mobilityremote" : doc["availability"]["mobilityRemote"],
	"mobilityinternational" : doc["availability"]["mobilityInternational"], 
	"mobilityareas" : doc["availability"]["mobilityAreas"],
	"mobilityareaslist" : doc["availability"]["mobilityAreasList"]}
			# langues
			lang = doc["availability"]["languages"]
			for i in range (0, len(lang)) :
				cv['data']["languages"].append({"language" : isolanguage.Language(lang[i]["code"]),
		"fluency" : Proficiency(lang[i]["profiency"])})
	
	
		return cv	
	
##################################################################################################	
#                                   COMPANY
##################################################################################################
	else :	
		
		# initialisation de la fiche
		fiche = {'id' : did,'DID_Document' : mode.server+'resolver/'+did, 'data' : {"legal" : []}}

		
		# Profil
		contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claim = contract.functions.getClaimIdsByTopic(101109097105108).call()
		claimid = claim[0].hex()
		fiche['data']["legal"].append({"profil" : {"id" : did+':claim:'+claimid, 'endpoint' : mode.server+'talao/data/'+did+':claim:'+claimid, "data" : profile}})

		# kbis
		# setup variable
		kbis=dict()
		
		# initialisation IPFS
		client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	
		# download du claim du dernier KBIS 107098105115) => le dernier est supposé etre le bon ...................a discuter !!!!
		contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
		claim = contract.functions.getClaimIdsByTopic(107098105115).call()
		if len(claim) == 0 : # pas de KBIS
			fiche['data']['kbis'] = {}
		else : 			
			claimId = claim[len(claim)-1].hex()
			claimdata = contract.functions.getClaim(claimId).call()
			issuer = claimdata[2]	
			data = claimdata[4]
			url = claimdata[5]
			# determination du profil de l issuer du KBIS
			(issuerprofile,X) = readProfil(whatisthisaddress(issuer,mode)["workspace"],mode)
			# verification de la signature du KBIS
			msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32'], [bytes('kbis', 'utf-8'), issuer, data, bytes(url, 'utf-8') ])
			message = encode_defunct(text=msg.hex())
			signature = claimdata[3]
			if signature != b"" :
				signataire = w3.eth.account.recover_message(message, signature=signature)
				signature = claimdata[3].hex()
				if signataire == issuer :
					verification = True
				else :
					verification = False	
			else :
				signature = None
				verification = False
			# mise en forme du KBIS
			if claimdata[5][:1] == "Q" :
				data = client.get_json(claimdata[5])
			else :
				url = claimdata[5]
				data = claimdata[4].decode('utf-8')
			kbis['data'] = data
			if claimdata[5] == "" :
				kbis['data']['url'] = None
			else :
				kbis['url'] = claimdata[5]
			
			fiche['data']["legal"].append({'kbis' :{'id' :did+':claim:'+claimId, 'endpoint' : mode.server+'talao/data/'+did+':claim:'+claimId,"data" : data}})
	
	return fiche


#######################################################
# mise a jour de la disponibilité, du TJM , de la mobilité et des langues

def getlanguage (workspace_contract, mode) :

		w3 = mode.w3
		address = contractsToOwners(workspace_contract, mode)
		docIndex = getDocumentIndex(10000, workspace_contract,mode)
		data = dict()
		if docIndex != [] :
			doc = getDocument(address, docIndex[len(docIndex)-1], workspace_contract,mode)
			
			# disponibilité
			data["availability"] = {"update" : doc["availability"]["dateCreated"],
	"availabilitywhen" : doc["availability"]["availabilityWhen"],
	"availabilityfulltime" : doc["availability"]["availabilityFulltime"]}
			# tjm
			data["rate"] = {"rateprice" : doc["availability"]["ratePrice"],
	"ratecurrency" : doc["availability"]["rateCurrency"]}
			# mobilité
			data["mobility"] = {"mobilityremote" : doc["availability"]["mobilityRemote"],
	"mobilityinternational" : doc["availability"]["mobilityInternational"], 
	"mobilityareas" : doc["availability"]["mobilityAreas"],
	"mobilityareaslist" : doc["availability"]["mobilityAreasList"]}
			# langues
			lang = doc["availability"]["languages"]
			data['languages'] = []
			for i in range (0, len(lang)) :
				data["languages"].append({"language" : isolanguage.Language(lang[i]["code"]),
		"fluency" : lang[i]["profiency"]})
			return data['languages']	
		else :
			return None
			

#####################################################################################
def setlanguage(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, language, mode, synchronous=True) :
	lang = []
	for i in range(0,len(language)) :
		langitem = {"code": isolanguage.codeLanguage(language[i]['language']),"profiency": language[i]['fluency']}	
		lang.append(langitem)	
		# a voir utilite de donner les bonnes valeur suivantes
		name = ""
		email = ""
		jobTitle = ""	
	employabilite = {"documentType": 10000,
		"version": 1,
		"recipient": {"name": name,
			"title": jobTitle,
			"email": email,
			"ethereum_account": address,
			"ethereum_contract": workspace_contract},
		"availability": {"dateCreated": str(datetime.today()),
			"availabilityWhen": "",
			"availabilityFulltime": True,
			"mobilityRemote": False,
			"mobilityAreas": False,
			"mobilityInternational": False,
			"mobilityAreasList": [],
			"rateCurrency": "",
			"ratePrice": "",
			"languages": lang}}	
	hash1 = createDocument(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, 10000, employabilite, False,mode, synchronous)	
	return hash1

"""
#########################################################################################

def getexperience(workspace_contract,address, mode) : 
	
	w3 = mode.w3
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)

	userexperience = []
	# experiences de type document 50000 compatible freedapp
	experienceIndex = getDocumentIndex(50000, workspace_contract,mode)
	for i in experienceIndex:
		doc = contract.functions.getDocument(i).call()
		ipfs_hash = doc[6].decode('utf-8')
		experience = Talao_ipfs.IPFS_get(ipfs_hash)
		new_experience = {'id' : 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]+':document:'+str(i), 'title' : experience['certificate']['title'],
				'description' : experience['certificate']['description'],
				'from' : experience['certificate']['from'],
				'to' : experience['certificate']['to'],
				'organization' : {"name" : "", 
						"contact_name" : experience['issuer']['responsible']["name"],
						"contact_email" : experience["issuer"]["organization"]["email"]
						},
				"certification_link" : ""
				}	
		skills = experience['certificate']['skills']
		skillsarray = ""
		for j in range (0, len(skills)) :
			skillsarray = skillsarray+' '+skills[j]['name']			
		new_experience['skills'] = skillsarray
		userexperience.append(new_experience)

	# experiences de type document 55000 non compatibles freedapp
	experienceIndex = getDocumentIndex(55000, workspace_contract,mode)
	for i in experienceIndex:
		doc = contract.functions.getDocument(i).call()
		if doc[7] == True : # doc encrypted
			 new_experience = {'id' : 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]+':document:'+str(i), 'title' : 'Encrypted',
				'description' : 'Encrypted',
				'from' : 'Encrypted',
				'to' : 'Encrypted',
				'organization' : {"name" : "Encrypted", 
						"contact_name" : 'Encrypted',
						"contact_email" : 'Encrypted'
						},
				"certification_link" : ""
				}	
		elif doc[7] == False :
			ipfs_hash = doc[6].decode('utf-8')
			experience = Talao_ipfs.IPFS_get(ipfs_hash)
			new_experience = {'id' : 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]+':document:'+str(i), 'title' : experience['certificate']['title'],
				'description' : experience['certificate']['description'],
				'from' : experience['certificate']['from'],
				'to' : experience['certificate']['to'],
				'organization' : {"name" : experience['issuer']['organization']['name'], 
						"contact_name" : experience['issuer']['responsible']["name"],
						"contact_email" : experience["issuer"]["organization"]["email"]
						},
				"certification_link" : ""
				}	
			skills = experience['certificate']['skills']
			skillsarray = ""
			for skill in skills :
				skillsarray = skillsarray + ' ' + skill			
			new_experience['skills'] = skillsarray
		else :
			print('Error getresume.getexperince, encrypted problem')
			return None			
		userexperience.append(new_experience)

	# experiences certifies de type document 60000
	experienceIndex = getDocumentIndex(60000, workspace_contract, mode)
	for i in experienceIndex:
		doc = contract.functions.getDocument(i).call()
		ipfs_hash = doc[6].decode('utf-8')
		experience = Talao_ipfs.IPFS_get(ipfs_hash)
		new_experience = {'id' : 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]+':document:'+str(i), 'title' : experience['certificate']['title'],
				'description' : experience['certificate']['description'],
				'from' : experience['certificate']['from'],
				'to' : experience['certificate']['to'],
				'organization' : {"name" : "", 
						"contact_name" : experience['issuer']['responsible']["name"],
						"contact_email" : experience["issuer"]["organization"]["email"]
						},
				"certification_link" : "",
				"skills": ""

				
				}
		userexperience.append(new_experience)

	return userexperience
"""				
	
	
	


#########################################################################################

def getexperience(workspace_contract,address, mode) : 
	
	w3 = mode.w3
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)

	userexperience = []
	# experiences de type document 50000 
	experienceIndex = getDocumentIndex(50000, workspace_contract,mode)
	for e in experienceIndex:
		experience = Experience().relay_get(workspace_contract, e, mode)
		new_experience = {'id' : 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]+':document:'+ str(experience.doc_id) , 'title' : experience.title,
				'doc_id' : experience.doc_id,
				'description' : experience.description,
				'start_date' : experience.start_date,
				'end_date' : experience.end_date,
				'company' : {"name" : experience.company['name'], 
						"contact_name" : experience.company["contact_name"],
						"contact_email" : experience.company["contact_email"],
						"contact_phone" : experience.company.get('contact_phone', 'unknown') # a retirer
						},
				"certificate_link" : experience.certificate_link,
				'skills' : experience.skills
				}	
		userexperience.append(new_experience)

	# experiences de type document 55000 non compatibles freedapp
	experienceIndex = getDocumentIndex(55000, workspace_contract,mode)
	for i in experienceIndex:
		doc = contract.functions.getDocument(i).call()
		if doc[7] == True : # doc encrypted
			 new_experience = {'id' : 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]+':document:'+str(i), 'title' : 'Encrypted',
				'description' : 'Encrypted',
				'from' : 'Encrypted',
				'to' : 'Encrypted',
				'organization' : {"name" : "Encrypted", 
						"contact_name" : 'Encrypted',
						"contact_email" : 'Encrypted'
						},
				"certification_link" : ""
				}	
		elif doc[7] == False :
			ipfs_hash = doc[6].decode('utf-8')
			experience = Talao_ipfs.IPFS_get(ipfs_hash)
			new_experience = {'id' : 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]+':document:'+str(i), 'title' : experience['certificate']['title'],
				'description' : experience['certificate']['description'],
				'from' : experience['certificate']['from'],
				'to' : experience['certificate']['to'],
				'organization' : {"name" : experience['issuer']['organization']['name'], 
						"contact_name" : experience['issuer']['responsible']["name"],
						"contact_email" : experience["issuer"]["organization"]["email"]
						},
				"certification_link" : ""
				}	
			skills = experience['certificate']['skills']
			skillsarray = ""
			for skill in skills :
				skillsarray = skillsarray + ' ' + skill			
			new_experience['skills'] = skillsarray
		else :
			print('Error getresume.getexperince, encrypted problem')
			return None			
		userexperience.append(new_experience)

	# experiences certifies de type document 60000
	experienceIndex = getDocumentIndex(60000, workspace_contract, mode)
	for i in experienceIndex:
		doc = contract.functions.getDocument(i).call()
		ipfs_hash = doc[6].decode('utf-8')
		experience = Talao_ipfs.IPFS_get(ipfs_hash)
		new_experience = {'id' : 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]+':document:'+str(i), 'title' : experience['certificate']['title'],
				'description' : experience['certificate']['description'],
				'from' : experience['certificate']['from'],
				'to' : experience['certificate']['to'],
				'organization' : {"name" : "", 
						"contact_name" : experience['issuer']['responsible']["name"],
						"contact_email" : experience["issuer"]["organization"]["email"]
						},
				"certification_link" : "",
				"skills": ""

				
				}
		userexperience.append(new_experience)

	return userexperience
			
		
	
	
############################################################################	
def get_certificate(workspace_contract, address, mode) :
	
	
	w3 = mode.w3
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)

	user_certificate = []		
	# experiences avec certificats implements avec des claim725		
	# download des claim "certificate"->  99101114116105102105099097116101 du user
	claimlist = contract.functions.getClaimIdsByTopic(99101114116105102105099097116101).call()
	for claimId in claimlist : #pour chaque issuer du claim "certificate"
		claimdata = contract.functions.getClaim(claimId).call()
		if claimdata[4].decode('utf-8') != '' :   # il existe des certificats
			certificatelist = json.loads(claimdata[4].decode('utf-8'))
			for certificateId in certificatelist :
				certificate = getclaimipfs(certificateId, workspace_contract,mode)
				if certificate != False : # on evite ceux qu ont ete effacés mais pas retirés de la certificatelist
					new_certificate = {'id' : 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]+':claim:'+certificateId[2:], 'title' : certificate['position'],
					'description' : certificate['summary'],
					'from' : certificate['startDate'],
					'to' : certificate['endDate'],
					'organization' : { "name" : certificate['company']['name'],
							"contact_name" : certificate['company']['manager'],
							"contact_email" : certificate['company'].get('manager_email')
							},
					'certificate_link' : certificateId[2:],
					'skills' : ""}		
					user_certificate.append(new_certificate)
	
	return user_certificate
	
	
"""	
############################################################################	
def getpersonal(workspace_contract, mode) :
	
	w3 = mode.w3
	did = 'did:talao:'+mode.BLOCKCHAIN+':'+workspace_contract[2:]
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	
	person= {'firstname' : 102105114115116110097109101,
			'lastname' : 108097115116110097109101
		#	'url' : 117114108,
		#	'email' : 101109097105108
			}
	company = {'name' : 110097109101,
				'contact_name' : 99111110116097099116095110097109101,
				'contact_email' : 99111110116097099116095101109097105108,
				'contact_phone' : 99111110116097099116095112104111110101
			#	'website' : 119101098115105116101,
			#	'email' : 101109097105108
				}

	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	category = contract.functions.identityInformation().call()[1]	
	personal = dict()
	if category == 1001 : 
		for topicname, topic in person.items() :
			claim = Claim().relay_get(workspace_contract, topicname, mode)
			personal[topicname] = claim.__dict__
	
	if category == 2001 : 
		for topicname, topic in company.items() :
			claim = Claim().relay_get(workspace_contract, topicname, mode)
			personal[topicname] = claim.__dict__ 
	print('personal =', personal)
	return personal, category
"""

# education = document 40000 
def get_education (workspace_contract, mode) :
	
	w3 = mode.w3
	did = 'did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract[2:]
	education_list = getDocumentIndex(40000, workspace_contract,mode)
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)	
	user_education = []
	for i in education_list:
		doc = contract.functions.getDocument(i).call()
		ipfs_hash = doc[6].decode('utf-8')
		education = Talao_ipfs.IPFS_get(ipfs_hash)	
		user_education.append({'id' : did+':document:'+str(i),
			'endpoint' : mode.server+'talao/data/'+did+':document:'+str(i),
			'data' : {	"organization" : education["issuer"]["organization"]["name"],
			"endDate" : education["diploma"]["to"], 
			"startDate" : education["diploma"]["from"],
			"studyType" : education["diploma"]["title"],
			"area" : education["diploma"]["description"],
			"certificate_link" : education["diploma"]["link"]}})
	return user_education		
			
