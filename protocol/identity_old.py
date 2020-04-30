"""
A la creation, si les informatiosn ne sont pas données, l instance de classe va les chercher


"""
from datetime import datetime
from operator import itemgetter, attrgetter
import random
from eth_account import Account

# dependances
import constante

from .Talao_token_transaction import contractsToOwners, ownersToContracts,token_balance, readProfil, getAll, addclaim, partnershiprequest, whatisthisaddress
from .Talao_token_transaction import  updateSelfclaims, savepictureProfile, getpicture, deleteDocument, deleteClaim
from .nameservice import namehash, addName,getUsername, updateName
from .GETresolver import getresolver
from .GETresume import getresume, getlanguage, setlanguage, getexperience
from .ADDkey import addkey
 
class identity() :
	
	def __init__(self, workspace_contract,mode, SECRET=None, email=None,  AES_key=None, private_key=None, backend_Id=None, username=None, rsa_key=None):
		if whatisthisaddress(workspace_contract, mode)['type'] != 'workspace' :
			print("probleme identity workspace_contract address")
			self.islive = False
		else :
			self.islive= True	
		
		self.endpoint=mode.server+'talao/api/data/'+workspace_contract[2:]
		self.wait= True # UI synchrone par defaut, on attend les receipts des transactions blockchain
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
		self.picture = getpicture(self.workspace_contract, self.mode)
		self.eth = mode.w3.eth.getBalance(self.address)/1000000000000000000
		self.rsa_key = rsa_key
		
		# on complete dabord avec les infos de l'identité disponible sur la blockchain
		if email == None :
			profil=readProfil(self.address,mode)
			if profil.get('givenName') == None :
				self.firstname = ""
			else :
				self.firstname=profil.get('givenName')
			if profil.get('familyName') == None :
				self.lastname = ""
			else :
				self.lastname=profil.get('familyName')
			self.name=self.firstname+' '+self.lastname
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
		
	def getAlerts(self) :
		contract=self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		alert=[]
		
		filterList= [contract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest'),
					contract.events.ClaimAdded.createFilter(fromBlock= 5800000,toBlock = 'latest'),
					contract.events.DocumentRemoved.createFilter(fromBlock= 5800000,toBlock = 'latest'),
					contract.events.ClaimRemoved.createFilter(fromBlock= 5800000,toBlock = 'latest')]		
		
		for i in range(0,len(filterList)) :
			eventlist=filterList[i].get_all_entries()
			for doc in eventlist :
				transactionhash =doc['transactionHash']
				transaction=self.mode.w3.eth.getTransaction(transactionhash)
				issuer=transaction['from']
				issuer_workspace_contract=ownersToContracts(issuer,self.mode)
				profil=readProfil(issuer,self.mode)
				firstname=profil.get('givenName', "")
				lastname=profil.get('familyName', "")
				issuer_name = firstname+' '+lastname
				blockNumber=transaction['blockNumber']
				block=self.mode.w3.eth.getBlock(blockNumber)
				date = datetime.fromtimestamp(block['timestamp'])			
				
				if i == 0 :
					eventType='DocumentAdded' 
					doc_id= 'did:talao:'+self.mode.BLOCKCHAIN+':'+issuer_workspace_contract[2:]+':document:'+str(doc['args']['id'])
					helptext = 'A new document #'+str(doc['args']['id'])+' has been issued by ' + issuer_name				
				elif i == 1 :
					eventType = 'ClaimAdded' 
					doc_id='did:talao:'+self.mode.BLOCKCHAIN+':'+issuer_workspace_contract[2:]+':claim:'+str(doc['args']['claimId'].hex())
					helptext= 'A new claim has been issued by '+issuer_name	
				elif i == 2 :
					eventType = 'DocumentRemoved' 					
					doc_id = None
					helptext= 'You have removed the document #'+str(doc['args']['id'])
				
				elif i == 3 :
					eventType = 'ClaimRemoved' 					
					doc_id = None
					helptext= 'You have removed the document #'+str(doc['args']['claimId'].hex())
				
				
				else :
					pass
				
				alert.append({'date' : str(date), 
						'alert' : helptext,
						'event' : eventType, 
						'doc_id' : doc_id}) 
	
		newlist= sorted(alert, key=itemgetter('date')) 	 
		newlist.reverse()

		return newlist
		
	
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
		
	def getLanguage(self) :	
		lang = getlanguage(self.workspace_contract, self.mode)
		print('lang = ', lang)
		if lang == None :
			return {}, '', '', ''
		context=dict()
		lang1 =''
		lang2=''
		lang3=''
		for i in range (0, len(lang)) :
			if i == 0:
				lang1 = lang[i]['language']
			elif i == 1 :
				lang2 = lang[i]['language']
			else :
				lang3 = lang[i]['language']	
					 
			if lang[i]['fluency']== '5' :		
				context['radio'+str(i+1)+'1']="checked"
			elif lang[i]['fluency'] == '4' :
				context['radio'+str(i+1) + '2']= "checked"
			elif lang[i]['fluency'] == '3' :
				context['radio'+str(i+1) + '3']= "checked"
			else :
				context['radio'+str(i+1) + '4']= "checked"
		print ('context = ',context)
		return context, lang1, lang2, lang3
		
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
	
	def getExperience(self) :
		self.experience =getexperience(self.workspace_contract, self.address, self.mode)
		return self.experience
		
	def getResume(self) :
		self.resume= getresume(self.workspace_contract, self.did,self.mode)
		return self.resume
	
	
	""" SETTER	"""
	
	def deleteExperience(self, experienceId) :
		if self.private_key == None :
			return False	
		contract=self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		claimdocId=experienceId.split(':')[5]
		if experienceId.split(':')[4] == 'document' :
			deleteDocument(self.workspace_contract, self.private_key,claimdocId,self.mode)
		else :
			deleteClaim(self.workspace_contract, self.private_key, '0x'+claimdocId,self.mode)
		self.getExperience()
		return True
		
	def uploadPicture(self,picturefile) :
		self.picture = savepictureProfile(self.address, self.private_key, picturefile,self.mode, synchronous = True)	
		return self.picture
		
	def setLanguage(self, language) :
#		language= [{"language": 'English',"fluency": '1'}]
		usr.language=language
		setlanguage(self.address, self.workspace_contract,self.private_key, language, self.mode, synchronous=self.wait)
		return 
		
	def setUserSettings(self, firstname, lastname, email) :
		if self.private_key == None :
			return False	
		self.firstname=firstname
		self.lastname=lastname
		self.email=email
		chaine=firstname+lastname+email
		topic=[ 103105118101110078097109101,102097109105108121078097109101,101109097105108]
		offset=[ len(firstname), len(lastname), len(email)]
		updateSelfclaims(self.address, self.private_key, topic,chaine, offset, self.mode,synchronous=self.wait)
		return True	
	
	def setDescription(self, description) :	
		if self.private_key == None :
			return False
		thread_id = str(random.randint(0,10000 ))
		addclaim(self.workspace_contract, self.address,self.private_key, 'description', self.address, description, "",self.mode, asynchronous=self.wait)
		self.description=description
		return True	
		
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
	
		
	def updateUsername(self,newusername) :
		updateName(self.username, newusername,self.mode)
		return
	
	""" Key Management  """
	def addKey(self, workspace_contract_to, purpose) :
		if self.private_key == None :
			return False
		return addkey(self.workspace_contract, self.private_key, workspace_contract_to, purpose,self.mode, synchronous=self.wait)	
		
	
	""" Parnership management""" 	
	def requestPartnership (self, workspace_contract_to) :
		if self.private_key == None :
			return False	
		partnershiprequest(self.workspace_contract, self.private_key, workspace_contract_to,self.mode, synchronous=self.wait)
		return True
	
	def authorizePartnership (self, workspace_partner_from) :
		if self.private_key == None :
			return False
		authorizepartnership(workspace_contract_partner, self.workspace_contract, self.private_key,self.mode, synchronous=self.wait) 
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
