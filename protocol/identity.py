"""
A la creation, si les informatiosn ne sont pas données, l instance de classe va les chercher

les signatures sont réalisée par le Relay

"""
from datetime import datetime
from operator import itemgetter, attrgetter
import random
from eth_account import Account
import ipfshttpclient
import os

# dependances
import constante

from .Talao_token_transaction import contractsToOwners, ownersToContracts,token_balance, readProfil, getAll, addclaim, partnershiprequest, whatisthisaddress
from .Talao_token_transaction import  updateSelfclaims, savepictureProfile, getpicture, deleteDocument, deleteClaim
from .nameservice import namehash, addName,getUsername, updateName
from .GETresolver import getresolver
from .GETresume import getresume, getlanguage, setlanguage, getexperience, getpersonal
from .ADDkey import addkey
 
class identity() :
	
	def __init__(self, workspace_contract,mode, address=None, private_key=None, SECRET=None,  AES_key=None, backend_Id=None, username=None, rsa_key=None):
		
		if whatisthisaddress(workspace_contract, mode)['type'] != 'workspace' :
			print("probleme identity workspace_contract address")
			return False	
		self.workspace_contract = workspace_contract
		self.mode=mode
		self.wait= True # UI synchrone par defaut, on attend les receipts des transactions blockchain
		self.AES_key = AES_key
		self.rsa_key = rsa_key
		self.SECRET = SECRET
		self.private_key=private_key # uniquement utilisée pour destroy et change owner
		if address == None :
			self.address = contractsToOwners(self.workspace_contract,mode)
		else :
			self.address=address
		self.eth = mode.w3.eth.getBalance(self.address)/1000000000000000000
		self.did = 'did:talao:'+mode.BLOCKCHAIN+':'+self.workspace_contract[2:]
		self.token = token_balance(self.workspace_contract,mode)
		self.backend_Id=backend_Id	
		
		""" personal  """
		self.getPersonal()
		self.name = self.personal['firstname']['data']+' '+self.personal['lastname']['data']

		""" experience """
		self.getExperience()

		""" picture """
		self.picture = getpicture(self.workspace_contract, self.mode)
		if self.picture != None :
			client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
			client.get(self.picture)
			os.system('mv '+ self.picture+' ' +'photos/'+self.picture)			
		
		""" username  """
		if username == None :	
			self.username=getUsername(self.workspace_contract,mode)	
		else :
			self.username=username
		if self.username == None : # si il n existe pas on fabrique le username de type "prenom.nom"
			if self.firstname == None :
				a=''					
			else :
				a =self.firstname
			if self.lastname == None :
				b = ''
			else :
				b = self.lastname	
			username=a+'.'+b
			self.username=username.lower()
			if self.mode.register.get(namehash(self.username)) != None :
				self.username=self.username+str(random.randrange(9999))
			else :
				pass
			# ajout au registre memoire et fichier
			addName(self.username, self.email, self.address, self.workspace_contract,self.mode) 		
		self.endpoint=mode.server+'user/?username='+self.username

		
	#########################################	
		
	def getAlerts(self) :
		contract=self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		alert=[]
		
		filterList= [contract.events.DocumentAdded.createFilter(fromBlock= 6200000,toBlock = 'latest'),
					contract.events.ClaimAdded.createFilter(fromBlock= 6200000,toBlock = 'latest'),
					contract.events.DocumentRemoved.createFilter(fromBlock= 6200000,toBlock = 'latest'),
					contract.events.ClaimRemoved.createFilter(fromBlock= 6200000,toBlock = 'latest')]		
		
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
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		acct = Account.from_key(self.mode.relay_private_key)
		self.mode.w3.eth.defaultAccount=acct.address
		partnershiplist = contract.functions.getKnownPartnershipsContracts().call()
		self.partnershiplist = partnershiplist
		return self.partnershiplist
	
	def getRsa_key(self) :
		filename = "./RSA_key/"+self.mode.BLOCKCHAIN+'/'+str(self.address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
		try :
			fp =open(filename,"r")
		except :
			self.rsa_key = None
			return None
		self.rsa_key = fp.read()	
		fp.close()   
		return self.ras_key
		
	def getResolver(self) : # a voir si on le laisse ici !!!!
		return getresolver(self.workspace_contract, self.did,self.mode)
		
	def getResume(self) : # a voir si on le laisse ici !!!!
		return getresume(self.workspace_contract, self.did,self.mode)
	
	def getPersonal(self) :
		self.personal = getpersonal(self.workspace_contract, self.mode)
		return self.personal
			
	def getLanguage(self) :	
		lang = getlanguage(self.workspace_contract, self.mode)
		
		if lang == None :
			return {}, '', '', ''
		context=dict()
		lang1 = ''
		lang2 = ''
		lang3 = ''
		for i in range (0, len(lang)) :
			if i == 0:
				lang1 = lang[i]['language']
			elif i == 1 :
				lang2 = lang[i]['language']
			else :
				lang3 = lang[i]['language']	
					 
			if lang[i]['fluency'] == '5' :		
				context['radio'+str(i+1)+'1'] = "checked"
			elif lang[i]['fluency'] == '4' :
				context['radio'+str(i+1) + '2'] = "checked"
			elif lang[i]['fluency'] == '3' :
				context['radio'+str(i+1) + '3'] = "checked"
			else :
				context['radio'+str(i+1) + '4'] = "checked"
	
		return context, lang1, lang2, lang3
		
	def getPartnershiplist(self) : 
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		acct = Account.from_key(self.private_key)
		self.mode.w3.eth.defaultAccount=acct.address
		partnershiplist = contract.functions.getKnownPartnershipsContracts().call()
		self.partnershiplist = partnershiplist
		return partnershiplist
		
	def getDid_document(self) :
		self.did_document = getresolver(self.workspace_contract, self.did, self.mode)
		return self.did_document
	
	def getExperience(self) :
		self.experience = getexperience(self.workspace_contract, self.address, self.mode)
		return self.experience
		
	
	
	
	""" SETTER	"""

	def deleteExperience(self, experienceId) :			
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		claimdocId=experienceId.split(':')[5]
		if experienceId.split(':')[4] == 'document' :
			deleteDocument(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key,claimdocId,self.mode)
		else :
			deleteClaim(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, '0x'+claimdocId,self.mode)
		self.getExperience()
		return True
		
	def uploadPicture(self,picturefile) :
		self.picture = savepictureProfile(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, picturefile,self.mode, synchronous = True)	
		return self.picture
		
	def setLanguage(self, language) :
#		language= [{"language": 'English',"fluency": '1'}]
		user.language = language
		setlanguage(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, language, self.mode, synchronous=self.wait)
		return 
	
	def setEmail(self, email) :
		addclaim(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, 'email', self.mode.relay_address, email, "",self.mode, synchronous=self.wait)
		self.firstname = firstname
		return True	
	
	def setFirstname(self, firstname) :
		addclaim(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, 'givenName', self.mode.relay_address, firstname, "",self.mode, synchronous=self.wait)
		self.firstname = firstname
		return True
		
	def setLastname(self, lastname) :
		addclaim(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, 'familyName', self.mode.relay_address, lastname, "",self.mode, synchronous=self.wait)
		self.lastname = lastname
		return True	
	
	def setDescription(self, description) :	
		addclaim(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, 'description', self.mode.relay_address, description, "",self.mode, synchronous=self.wait)
		self.description = description
		return True	
	
	def setUrl(self, url) :	
		addclaim(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, 'url', self.mode.relay_address, url, "",self.mode, synchronous=self.wait)
		self.url = url
		return True	
		
	def setAddress(self, address) :	
		addclaim(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, 'address', self.mode.relay_address, address, "",self.mode, synchronous=self.wait)
		self.url = url
		return True	
		
	def setContact(self, contact) :	
		addclaim(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, 'contact', self.mode.relay_address, contact, "",self.mode, synchronous=self.wait)
		self.url = url
		return True	

	""" Name Service """		
	# update le username
	def updateUsername(self, newusername) : 
		return updateName(self.username, newusername, self.mode)
	
	""" Only Owner """	
	# destroy Identity and remove it from register
	def killIdentity(self) :				
		deleteName(self.username, self.mode) 
		destroyWorkspace(self.workspace_contract, self.private_key, self.mode)
		return True	
	
	# def changeOwner(self, address_new_owner ) :  
	
	
	
	""" Key Management  """
	def addKey(self, address_partner, purpose) :
		return addkey(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, address_partner,purpose,self.mode, synchronous=self.wait)	
		
	""" Parnership management""" 	
	def requestPartnership (self, workspace_contract_partner) : 
		partnershiprequest(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key,workspace_contract_partner,self.mode, synchronous=self.wait)
		return True
	
	def authorizePartnership (self, workspace_contract_partner) :
		authorizepartnership(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key,workspace_contract_partner,self.mode, synchronous=self.wait) 
		return True
	
	# liste des nouvaux workspace_contract demandant un partnership
	def partnershipRequested(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		myfilter = contract.events.PartnershipRequested.createFilter(fromBlock= 5800000,toBlock = 'latest')
		eventlist = myfilter.get_all_entries()
		partnershipRequestedList = []
		for event in range(0, len(eventlist)) :
			transactionhash = eventlist[event]['transactionHash']
			transaction = self.mode.w3.eth.getTransaction(transactionhash)
			partner = transaction['to']
			partnershipRequestedList.append(partner)
		return list(set(partnershipRequestedList)-set(self.partnershiplist))	
	
	
