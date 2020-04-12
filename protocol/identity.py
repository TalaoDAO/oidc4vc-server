"""
Class identity mother of god
"""

import random
from eth_account import Account

import constante
from .Talao_token_transaction import contractsToOwners, token_balance, readProfil, getAll, addclaim, partnershiprequest, whatisthisaddress, getUsername
from .nameservice import namehash, addName
from .GETresolver import getresolver
from .GETresume import getresume

###################################################
# a la creation si les informatiosn ne sont pas données, l instance de classe va les chercher

class identity() :
	
	def __init__(self, workspace_contract,mode, SECRET=None, email=None,  AES_key=None, private_key=None, backend_Id=None, username=None):
		print("debut init")
		if whatisthisaddress(workspace_contract, mode)['type'] != 'workspace' :
			print("probleme ")
			self.islive = False
			return None	
		else :
			self.islive= True	
		self.workspace_contract = workspace_contract
		self.mode = mode
		self.private_key = private_key
		self.AES_key = AES_key
		self.SECRET = SECRET
		self.email = email
		self.address = contractsToOwners(self.workspace_contract,self.mode)
		self.did = 'did:talao:'+self.mode.BLOCKCHAIN+':'+self.workspace_contract[2:]
		self.token = token_balance(self.workspace_contract,self.mode)
		self.backend_Id=backend_Id		
		self.username = username
		self.eth = self.mode.w3.eth.getBalance(self.address)/1000000000000000000
		self.did_document = getresolver(self.workspace_contract, self.did,self.mode)
		self.resume = getresume(self.workspace_contract, self.did,self.mode)
		self.rsa_key = None
		
		# on complete dabord avec les infos de l'identité disponible sur la blockchain
		if email == None :
			self.profil=readProfil(self.address,mode)
			self.firstname=self.profil.get('givenName')
			self.lastname=self.profil.get('familyName')
			self.email=self.profil.get('email')
			
		# on complete ensuite avec les infos du fichier local si elles existent
		if private_key == None :
			(self.private_key, self.SECRET, self.AES_key) = getAll(self.workspace_contract,self.mode)						
			if self.private_key[:2]  != '0x'  : # echec lecture fichier
				print("private key is not available")
				self.private_key=None
				self.SECRET=None
				self.AES_key=None		
			else :
				print("private key is available")
		
		# lecture de la cle RSA privée
		if self.private_key != None :
			filename = "./RSA_key/"+self.mode.BLOCKCHAIN+'/'+str(self.address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
			try :
				fp =open(filename,"r")
			except :
				self.rsa_key= False
			if self.rsa_key != False :
				self.rsa_key=fp.read()	
			else :
				self.rsa_key = None
			fp.close()   
					
		# construction de la liste des partnership
		if self.private_key != None :
			contract=self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
			acct =Account.from_key(self.private_key)
			self.mode.w3.eth.defaultAccount=acct.address
			partnershiplist = contract.functions.getKnownPartnershipsContracts().call()
			self.partnershiplist=partnershiplist
		else :
			self.partnershiplist = None
		
		# username : on cherche d abord dans l'identité si on ne le trouve pas ensuite on le fabrique
		if self.username == None :	
			if self.private_key != None :	
				self.username=getUsername(self.workspace_contract,self.mode)	 
			if self.username == None : # si il n existe pas dans l identité
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
			
	def getPartnershiplist(self) : 
		contract=self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		acct =Account.from_key(self.private_key)
		self.mode.w3.eth.defaultAccount=acct.address
		partnershiplist = contract.functions.getKnownPartnershipsContracts().call()
		self.partnershiplist = partnershiplist
		return partnershiplist
		
	def getDid_document(self) :
		self.did_document= getresolver(self.workspace_contract, self.did,self.mode)
		return self.did_document
	
	def getResume(self) :
		self.resume= getresume(self.workspace_contract, self.did,self.mode)
		return self.resume
		
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
			
	def setUsername(self, username) :
		if self.private_key == None :
			return False		 
		# on verifie que username n'existe pas deja dans le registre sinon, on le modifie
		if self.mode.register.get(namehash(username.lower())) != None :
			newusername=username+str(random.randrange(9999))
		else :
			newusername=username
		self.username=newusername
		# ajout sur l identité 
		addclaim(self.workspace_contract, self.address,	self.private_key, 'nameservice', self.address, newusername, "",	self.mode)	
		# ajout au registre memoire et fichier
		addName(newusername, self.email, self.workspace_contract,self.mode) 
		return self.username
		
	def requestPartnership (self, workspace_contract_to) :
		if self.private_key == None :
			return False	
		partnershiprequest(self.workspace_contract, self.private_key, workspace_contract_to,self.mode)
		return True
		
	# ajoute le user au registre
	def addToRegister(self) :
		self.mode.register[namehash(self.username.lower())]={ 'username' : self.username, 'email_authentification' : self.email, 'workspace_contract' : self.workspace_contract, 'resolver' : self.mode.server+'resolver/api/'+self.did, 'resume' : mode.server+"talao/api/resume/"+ self.did}	
		try : 
			myfile=open(self.mode.BLOCKCHAIN+'_register.json', 'w') 
		except IOError :
			print('IOError ; impossible de stocker le fichier')
			return False
		json.dump(self.mode.register, myfile)
		myfile.close()
		return True
			
	def printIdentity(self) :		
		myidentity = vars(self)
		for i in myidentity.keys() :
			print(i,'-->', myidentity[i])
