"""
A la creation, si les informatiosn ne sont pas données, l instance de classe va les chercher


"""

import threading
import random
from eth_account import Account

# dependances
import constante
from .Talao_token_transaction import contractsToOwners, token_balance, readProfil, getAll, addclaim, partnershiprequest, whatisthisaddress, updateSelfclaims
from .nameservice import namehash, addName,getUsername
from .GETresolver import getresolver
from .GETresume import getresume
 
exporting_threads = {}
	
# Multithreading
class UserSettingsThread(threading.Thread):
	def __init__(self, address, private_key,firstname, lastname, email, mode):
		super().__init__()
		self.address= address
		self.private_key=private_key
		self.firstname=firstname
		self.lastname=lastname
		self.email=email
		self.mode=mode
		self.chaine=firstname+lastname+email
		self.topic=[ 103105118101110078097109101,102097109105108121078097109101,101109097105108]
		self.offset=[ len(firstname), len(lastname), len(email)]

	def run(self):
		hash1=updateSelfclaims(self.address, self.private_key, self.topic,self.chaine, self.offset, self.mode)

class DescriptionThread(threading.Thread):
	def __init__(self, workspace_contract, address, private_key,description, mode):
		super().__init__()
		self.address=address
		self.workspace_contract= workspace_contract
		self.private_key=private_key
		self.description=description
		self.mode=mode

	def run(self):
		hash1=addclaim(self.workspace_contract, self.address,self.private_key, 'description', self.address, self.description, "",self.mode)
 
class identity() :
	
	def __init__(self, workspace_contract,mode, SECRET=None, email=None,  AES_key=None, private_key=None, backend_Id=None, username=None, rsa_key=None):
		if whatisthisaddress(workspace_contract, mode)['type'] != 'workspace' :
			print("probleme identity workspace_contract address")
			self.islive = False
		else :
			self.islive= True	
		self.mode=mode
		self.workspace_contract = workspace_contract
		self.private_key = private_key
		self.AES_key = AES_key
		self.SECRET = SECRET
		self.email = email
		self.address = contractsToOwners(self.workspace_contract,mode)
		self.did = 'did:talao:'+mode.BLOCKCHAIN+':'+self.workspace_contract[2:]
		self.token = token_balance(self.workspace_contract,mode)
		self.backend_Id=backend_Id		
		self.username = username
		self.eth = mode.w3.eth.getBalance(self.address)/1000000000000000000
		self.rsa_key = rsa_key
		
		# on complete dabord avec les infos de l'identité disponible sur la blockchain
		if email == None :
			profil=readProfil(self.address,mode)
			self.firstname=profil.get('givenName')
			self.lastname=profil.get('familyName')
			self.email=profil.get('email')
			self.description=profil.get('description')
							
		# username 
		if self.username == None :	
			self.username=getUsername(self.workspace_contract,mode)	 
			if self.username == None : # si il n existe pas dans le registre nameservice, on le fabrique
				if self.firstname == None :
					a=''					
				else :
					a =self.firstname
				if self.lastname == None :
					b = ''
				else :
					b = self.lastname	
				username=a+'.'+b
				setUsername(self, username)		
		
		# on complete ensuite avec les infos du fichier local si elles existent
		if self.private_key == None :
			(self.private_key, self.SECRET, self.AES_key) = getAll(self.workspace_contract,self.mode)						
			if self.private_key[:2]  != '0x'  : # echec lecture fichier
				self.private_key=None
				self.SECRET=None
				self.AES_key=None		
			else :
				pass
		
	#########################################	
		
	def getPartnershiplist(self) :
		# construction de la liste des partnership
		if self.private_key != None :
			contract=self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
			acct =Account.from_key(self.private_key)
			self.mode.w3.eth.defaultAccount=acct.address
			partnershiplist = contract.functions.getKnownPartnershipsContracts().call()
			self.partnershiplist=partnershiplist
		else :
			self.partnershiplist = None
		return self.partnershiplist
	
	def getRsa_key(self) :
		filename = "./RSA_key/"+self.mode.BLOCKCHAIN+'/'+str(self.address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
		try :
			fp =open(filename,"r")
		except :
			self.rsa_key= None
			return None
		self.rsa_key=fp.read()	
		fp.close()   
		return self.ras_key
		
	def getResolver(self) : # a voir si on le laisse ici !!!!
		return getresolver(self.workspace_contract, self.did,self.mode)
		
	def getResume(self) : # a voir si on le laisse ici !!!!
		return getresume(self.workspace_contract, self.did,self.mode)
			
	def getPartnershiplist(self) : 
		contract=self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		acct =Account.from_key(self.private_key)
		self.mode.w3.eth.defaultAccount=acct.address
		partnershiplist = contract.functions.getKnownPartnershipsContracts().call()
		self.partnershiplist = partnershiplist
		return partnershiplist
		
	def getDid_document(self) :
		self.did_document= getresolver(self.workspace_contract, self.did, self.mode)
		return self.did_document
	
	def getResume(self) :
		self.resume= getresume(self.workspace_contract, self.did,self.mode)
		return self.resume
	
	
	""" Setter	"""
	def setUserSettings(self, firstname, lastname, email) :
		if self.private_key == None :
			return False	
		self.firstname=firstname
		self.lastname=lastname
		self.email=email
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = UserSettingsThread(self.address, self.private_key,firstname, lastname, email, self.mode)
		exporting_threads[thread_id].start()
		return True
		
	def setLastname(self, lastname) :
		if self.private_key == None :
			return False		
		addclaim(self.workspace_contract, self.address,self.private_key, 'familyName', self.address, lastname, "",self.mode)
		self.lastname=lastname
		return self.lastname
		
	def setFirstname(self, firstname) :	
		if self.private_key == None :
			return False					
		addclaim(self.workspace_contract, self.address,self.private_key, 'givenName', self.address, firstname, "",self.mode)
		self.firstname=firstname
		return self.firstname
	
	def setDescription(self, description) :	
		if self.private_key == None :
			return False
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = DescriptionThread(self.workspace_contract, self.address, self.private_key,description, self.mode)
		exporting_threads[thread_id].start()						
		self.description=description
		return self.description		
			
	def setUsername(self, username) :
		if self.private_key == None :
			return False		 
		# on verifie que username n'existe pas deja dans le registre sinon, on le modifie
		if self.mode.register.get(namehash(username.lower())) != None :
			newusername=username+str(random.randrange(9999))
		else :
			newusername=username
		self.username=newusername
		# ajout au registre memoire et fichier
		addName(self.username, self.email, self.workspace_contract,self.mode) 
		return self.username
	
	""" Parnership management""" 	
	def requestPartnership (self, workspace_contract_to) :
		if self.private_key == None :
			return False	
		partnershiprequest(self.workspace_contract, self.private_key, workspace_contract_to,self.mode)
		return True
	
	def authorizePartnership (self, workspace_partner_from) :
		if self.private_key == None :
			return False
		authorizepartnership(workspace_contract_partner, self.workspace_contract, self.private_key,self.mode) 
		return True
	
	# liste des nouvaux workspace_contract demandant un partnership
	def partnershipRequested(self) :
		contract=self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		myfilter = contract.events.PartnershipRequested.createFilter(fromBlock= 5800000,toBlock = 'latest')
		eventlist = myfilter.get_all_entries()
		partnershipRequestedList=[]
		for event in range(0, len(eventlist)) :
			transactionhash =eventlist[event]['transactionHash']
			transaction=self.mode.w3.eth.getTransaction(transactionhash)
			partner=transaction['to']
			partnershipRequestedList.append(partner)
		return list(set(partnershipRequestedList)-set(self.partnershiplist))	
		
	# ajoute le username au registre
	def addToRegister(self) :
		return addName(self.username, self.email, self.workspace_contract, self.mode)
		
	# update le username
	def updateUsername(self, newusername) : 
		return updateName(self.username, newusername, self.mode)
		
	# destroy Identity and removre it from register
	def killIdentity(self) :
		if self.private_key == None :
			return False		
		deleteName(self.username, self.mode) 
		destroyWorkspace(self.workspace_contract, self.private_key, self.mode)
		return True
		
	# TEST : renvoi le contenu de l identité		
	def printIdentity(self) :		
		myidentity = vars(self)
		for i in myidentity.keys() :
			print(i,'-->', myidentity[i])
