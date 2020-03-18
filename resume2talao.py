import sys
import csv
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Protocol.KDF import PBKDF2
import http.client
import json
from datetime import datetime

# dependances
import Talao_token_transaction
import Talao_backend_transaction
import Talao_message
import Talao_ipfs
import isolanguage
import addclaim
import environment
import constante

# wallet de Talaogen
#talao_public_Key='0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b'
#talao_private_Key='0xbbfea0f9ed22445e7f5fb1c4ca780e96c73da3c74fbce9a6972c45730a855460'

# initialisation de l'environnement
mode=environment.currentMode('test', 'rinkeby')
mode.print_mode()
w3=mode.initProvider()


# deterministic RSA rand function variable
password = "suc2cane"
master_key = ""
salt = ""
# deterministic RSA rand function
def my_rand(n):
    # kluge: use PBKDF2 with count=1 and incrementing salt as deterministic PRNG
    my_rand.counter += 1
    return PBKDF2(master_key, "my_rand:%d" % my_rand.counter, dkLen=n, count=1)


# trad lang
def Language(lang) :
	return isolanguage.codeLanguage(lang)

def Proficiency(texte) :
	text=texte.lower()
	if text == 'native or bilingual' :
		return 5
	if text == 'full professional' :
		return 4
	if text == 'elementary' or text =='null' :
		return 1
	if text == 'professional working' :
		return 3
	if text == 'limited working' :
		return 2
	else :
		return False


############################################
# Creation d'un workspace from scratch
############################################

def creationworkspacefromscratch(firstname, name, email): 
		
	# creation de la wallet	
	account = w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
	eth_a=account.address
	eth_p=account.privateKey.hex()
	print('adresse = ',eth_a)
	print('private key = ', eth_p)
	
	# création de la cle RSA (bytes) deterministic
	# https://stackoverflow.com/questions/20483504/making-rsa-keys-from-a-password-in-python
	global salt
	global master_key
	salt = eth_p
	master_key = PBKDF2(password, salt, count=10000)  # bigger count = better
	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
	RSA_private = RSA_key.exportKey('PEM')
	RSA_public = RSA_key.publickey().exportKey('PEM')
		
	# création de la cle RSA (bytes), des cle public et privées
	#RSA_key = RSA.generate(2048)
	#RSA_private = RSA_key.exportKey('PEM')
	#RSA_public = RSA_key.publickey().exportKey('PEM')

	# stockage de la cle privée RSA dans un fichier du repertoire ./RSA_key/rinkeby ou ethereum
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+str(eth_a)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	fichier=open(filename,"wb")
	fichier.write(RSA_private)
	fichier.close()   

	# création de la cle AES
	AES_key = get_random_bytes(16)	

	# création du Secret
	SECRET_key = get_random_bytes(16)
	SECRET=SECRET_key.hex()
	print('SECRET = ', SECRET)
	
	# encryption de la cle AES avec la cle RSA
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted=cipher_rsa.encrypt(AES_key)
	
	# encryption du SECRET avec la cle RSA 
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted=cipher_rsa.encrypt(SECRET_key)
	
	# Transaction pour le transfert de 0.08 ethers depuis le portfeuille TalaoGen
	hash1=Talao_token_transaction.ether_transfer(eth_a, 80,mode)
	print('hash de transfert de 0.08 eth = ',hash1)
	
	# Transaction pour le transfert de 100 tokens Talao depuis le portfeuille TalaoGen
	hash2=Talao_token_transaction.token_transfer(eth_a,100,mode)
	print('hash de transfert de 100 TALAO = ', hash2)
	
	# Transaction pour l'acces dans le token Talao par createVaultAccess
	hash3=Talao_token_transaction.createVaultAccess(eth_a,eth_p,mode)
	print('hash du createVaultaccess = ', hash3)
	
	# Transaction pour la creation du workspace :
	bemail=bytes(email , 'utf-8')	
	hash4=Talao_token_transaction.createWorkspace(eth_a,eth_p,RSA_public,AES_encrypted,SECRET_encrypted,bemail,mode)
	print('hash de createWorkspace =', hash4)

	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract_address=Talao_token_transaction.ownersToContracts(eth_a,mode)
	print( 'workspace contract = ', workspace_contract_address)
	
	# Transaction pour la creation du compte sur le backend HTTP POST
	backend_Id = Talao_backend_transaction.backend_register(eth_a,workspace_contract_address,firstname, name, email, SECRET,mode)

	# envoi du message de log
	status="Identity created by resume2talao"
	Talao_message.messageLog(name, firstname, email,status,eth_a, eth_p, workspace_contract_address, backend_Id, email, SECRET, AES_key,mode)

	#ajout d'un cle 3 a la fondation pour la gestion du nameservice
	owner_foundation = mode.foundation_address	       
	contract=w3.eth.contract(workspace_contract_address,abi=constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(eth_a)  
	_key=w3.soliditySha3(['address'], [owner_foundation])
	txn = contract.functions.addKey(_key, 3, 1).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn=w3.eth.account.signTransaction(txn,eth_p)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1)		
	print("creation de cle 3 pour la fondation = ", hash1)
	
	return eth_a, eth_p, SECRET, workspace_contract_address,backend_Id, email, SECRET, AES_key

############################################################
#  Create and publish experience in one step
############################################################
# @newexperience -> dict

def createandpublishExperience(address, private_key, newexperience, email, password, workspace_contract) :

	#recuperer le bearer token sur le backend
	conn = http.client.HTTPConnection(mode.ISSUER)
	if mode.BLOCKCHAIN == 'ethereum' :
		conn = http.client.HTTPSConnection(mode.ISSUER)
	headers = {'Accept': 'application/json','Content-type': 'application/json'}
	payload = {"email" : email ,"password" : password}
	data = json.dumps(payload)
	conn.request('POST', '/login',data, headers)
	response = conn.getresponse()
	res=response.read()
	token= json.loads(res)["token"]
	
	# creation experience sur le backend
	headers = {'Accept': 'application/json','Content-type': 'application/json',  'Authorization':'Bearer '+token}
	payload=newexperience
	data = json.dumps(payload)
	conn.request('POST', '/experiences',data, headers)
	response= conn.getresponse()
	res=response.read()
	experience= json.loads(res)['experience']	
	experience_id= json.loads(res)['experience']['id']
	conn.close()

	experience_blockchain=	{"documentType": 50000,
		"version": 2,
		"recipient": {"givenName": experience['freelance']['first_name'],
			"familyName": experience['freelance']['last_name'],
			"title": experience['freelance']['title'],
			"email": experience['freelance']['email'],
			"ethereum_account": experience['freelance']['ethereum_account'],
			"ethereum_contract": experience['freelance']['ethereum_contract']},
		"issuer": {"organization": {"name" : experience['organization_name'],"email": "","url": "","image": "","ethereum_account": "","ethereum_contract": ""},
			"responsible": {"name": "","title": "","image": ""},
			"partner": {"name": "","text": ""}},
		"certificate": {"title": experience['title'],
			"description": experience['description'],
			"from": experience['from'],
			"to": experience['to'],
			"skills": experience['skills'],
			"ratings": []}
		}
 
	# upload de l experience sur la blockchain
	Talao_token_transaction.createDocument(address, private_key, 50000, experience_blockchain, False,mode)
	
	# recuperer l iD du document sur le dernier event DocumentAdded
	mycontract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	myfilter = mycontract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
	eventlist = myfilter.get_all_entries()
	l=len(eventlist)
	document_id=eventlist[l-1]['args']['id']

	# update de l experience sur la backend . on change le status et on donne le numero du doc 
	token=Talao_backend_transaction.login(email, password,mode)
	headers = {'Accept': 'application/json','Content-type': 'application/json',  'Authorization':'Bearer '+token}
	payload ={"experience":{"blockchain_experience_id":document_id,"blockchain_status":1},"action":"SET_DRAFT"}
	data = json.dumps(payload)
	conn.request('PUT', '/experiences/'+str(experience_id),data, headers)
	response= conn.getresponse()
	res=response.read()
	conn.close()
	return


##############################################################
#             MAIN
##############################################################
# tous les claims sont signe par le controller (owner) -> self claim

# Ouverture du fichier d'archive Talao_Identity.csv
fname= mode.BLOCKCHAIN +"_Talao_Identity.csv"
identityfile = open(fname, "a")
writer = csv.writer(identityfile)

# ouverture du fichier cv au format json
filename=input("Saisissez le nom du fichier de cv json ? ")
resumefile=open(filename, "r")
resume=json.loads(resumefile.read())
	
# calcul du temps de process
time_debut=datetime.now()

# CREATION DU WORKSPACE ET DU BACKEND
name = resume['profil']["name"]
firstname = resume['profil']['firstname']
email = resume['profil']['email']

# sortie immediate si l email existe deja dans le backend
if Talao_backend_transaction.canregister(email,mode) == False :
	print('email existant dans le backend')
	resumefile.close()
	identityfile.close()
	sys.exit(0)

# creation du workspace vierge
(address, private_key,password, workspace_contract,backend_Id, email, SECRET, AES_key) = creationworkspacefromscratch(firstname, name, email)
		
# UPLOAD DU PROFIL
worksFor = resume['profil']['company']
jobTitle = resume['profil']['position']
workLocation = ""
url= resume['profil']['website']
description = resume['profil']['summary']	
Talao_token_transaction.saveworkspaceProfile(address, private_key, firstname, name, jobTitle, worksFor, workLocation, url, email, description,mode)
# sauvegarde de la photo de profil
if resume["profil"]["image"] != "" :
	Talao_token_transaction.savepictureProfile(address, private_key, resume["profil"]["image"], mode)
# add claim725 pour autre info. Ces infos ne seront pas visible dans la freedapp:
if resume["profil"]["birthdate"] != "" :
	addclaim.addClaim(workspace_contract, address, private_key, "birthdate", address, resume["profil"]["birthdate"] , "",mode)
if resume["profil"]["socialsecurity"] != "" :
	addclaim.addClaim(workspace_contract, address, private_key, "socialsecurity", address, resume["profil"]["socialsecurity"], "",mode)


# UPLOAD DES EXPERIENCES
for i in range(0,len(resume['experience'])) :					
	# mise au format des skills	
	skills=resume['experience'][i]['skills']
	newskills=[]
	for s in range(0, len(skills)) :
		a = Talao_backend_transaction.getSkill(email, password, skills[s],mode)
		if a!= "ERROR" :
			newskills.append(a)
	# autres mises a jour
	organization_name = resume['experience'][i]['company']
	fromdate=resume['experience'][i]['startDate']
	todate=resume['experience'][i]['endDate']
	description = resume['experience'][i]['summary']
	title = resume['experience'][i]['position']		
	experience = { 'experience' :{ 'title' : title,
			'description' : description,
			'from' : fromdate,
			'to' : todate,
			'location' : '',
			'remote' : False,
			'organization_name' : organization_name,
			'skills' : newskills}}
	createandpublishExperience(address, private_key, experience, email, password, workspace_contract )
	print("Experience publiée = ", json.dumps(experience, indent=4))


# UPLOAD DES DIPLOMES
name =firstname+' '+name
for i in range (0,len(resume['education'])) :
	school_name = resume['education'][i]['institution']
	diploma_title = resume['education'][i]['studyType']
	diploma_description =resume['education'][i]['area']
	diploma_url = resume['education'][i]['link']	
	data = {'documentType': 40000,
		'version': 2,
		'recipient': {'name': name,
			'title': jobTitle,
			'email': email,
			'ethereum_account': address,
			'ethereum_contract': workspace_contract},
		'issuer': {'organization': {'name': school_name}},
		'diploma': {'title': diploma_title,
			'description': diploma_description,
			'from': fromdate ,
			'to': todate,
			'link': diploma_url}}
	Talao_token_transaction.createDocument(address, private_key, 40000, data, False,mode)
	print("Diplome publié = ", json.dumps(data, indent=4))


# UPLOAD DE L'EMPLOYABILITE
lang=[]
for i in range(0,len(resume['languages'])) :
	langitem={"code": Language(resume['languages'][i]['language']),"profiency": Proficiency(resume['languages'][i]['fluency'])}	
	lang.append(langitem)		
employabilite={"documentType": 10000,
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
Talao_token_transaction.createDocument(address, private_key, 10000, employabilite, False,mode)
print("Employabilite publiée = ", json.dumps(employabilite, indent=4))


# calcul de la duree de transaction et du cout
time_fin=datetime.now()
time_delta=time_fin-time_debut
print('Durée des transactions = ', time_delta)
a=w3.eth.getBalance(address)
cost=0.08-a/1000000000000000000	
print('Cout des transactions =', cost)	


# mise a jour du fichier archive Talao_Identity.csv
status="Identité créée par resume2talao"
writer.writerow(( datetime.today(),name, firstname, email,status,address, private_key, workspace_contract, backend_Id, email, SECRET, AES_key,cost) )



# fermeture des fichiers
resumefile.close()
identityfile.close()
sys.exit(0)
