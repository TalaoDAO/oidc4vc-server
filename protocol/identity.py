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
from .nameservice import namehash, getUsername, updateName, data_from_publickey
from .GETresolver import getresolver
from .GETresume import getresume, getlanguage, setlanguage, getexperience, getpersonal, getcontact, get_education
from .ADDkey import addkey
 
class Identity() :
	
	def __init__(self, workspace_contract,mode, address=None, SECRET=None,  AES_key=None, backend_Id=None, username=None, rsa_key=None):
		
		if whatisthisaddress(workspace_contract, mode)['type'] != 'workspace' :
			print("identity.py, this address is not an Identity")
			return None
		
		self.workspace_contract = workspace_contract
		self.mode = mode
		self.synchronous = True # UI synchrone par defaut, on attend les receipts des transactions blockchain
		self.AES_key = AES_key
		
		if address is None :
			self.address = contractsToOwners(self.workspace_contract,mode)
		else :
			self.address = address
		
		if rsa_key is None :
			filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+str(self.address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
			try :
				fp = open(filename,"r")
				self.rsa_key = fp.read()	
				fp.close()   
			except IOError :
				self.rsa_key = None			 
		
		self.SECRET = SECRET
		self.eth = mode.w3.eth.getBalance(self.address)/1000000000000000000
		self.did = 'did:talao:'+mode.BLOCKCHAIN+':'+self.workspace_contract[2:]
		self.token = token_balance(self.address,mode)
		self.backend_Id=backend_Id		
		self.web_relay_authorized = False	
		self.getPersonal()
		self.name = self.personal['firstname']['data']+' '+self.personal['lastname']['data']
		self.getContact()
		self.getExperience()
		self.getLanguage()
		self.getManagementKeys()
		self.getClaimKeys()
		self.getEducation()
		self.picture = getpicture(self.workspace_contract, self.mode)

		if self.picture is not None :
			client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
			client.get(self.picture)
			os.system('mv '+ self.picture+' ' +'photos/'+self.picture)	
		
		self.getPartners()
		self.getEvents()				
		
		if username is None :	
			self.username = getUsername(self.workspace_contract,mode)		
		
		self.endpoint=mode.server+'user/?username='+self.username

	# filters on external events only, always available
	def getEvents(self) :
		contract=self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		alert=dict()
		filterList= [contract.events.DocumentAdded.createFilter(fromBlock= 6200000,toBlock = 'latest'),
					contract.events.ClaimAdded.createFilter(fromBlock= 6200000,toBlock = 'latest'),
					contract.events.PartnershipRequested.createFilter(fromBlock= 6200000,toBlock = 'latest'),
					contract.events.PartnershipAccepted.createFilter(fromBlock= 6200000,toBlock = 'latest')]		
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
				
				if i == 0 and issuer_workspace_contract != self.workspace_contract :
					eventType='DocumentAdded' 
					doc_id= 'did:talao:'+self.mode.BLOCKCHAIN+':'+issuer_workspace_contract[2:]+':document:'+str(doc['args']['id'])
					helptext = issuer_name +' issued a new certificate'	
					alert[date] =  {'alert' : helptext, 'event' : eventType, 'doc_id' : doc_id}
				elif i == 1 and issuer_workspace_contract != self.workspace_contract :
					eventType = 'ClaimAdded' 
					doc_id='did:talao:'+self.mode.BLOCKCHAIN+':'+issuer_workspace_contract[2:]+':claim:'+str(doc['args']['claimId'].hex())
					helptext= issuer_name + ' issued a new certificate'
					alert[date] =  {'alert' : helptext,'event' : eventType, 'doc_id' : doc_id}
				elif i == 2 and issuer_workspace_contract != self.workspace_contract :
					eventType = 'PartnershipRequested' 					
					doc_id = None
					helptext= 'Request for partnership from ' + issuer_name
					alert[date] =  {'alert' : helptext, 'event' : eventType, 'doc_id' : doc_id}
				elif i == 3 and issuer_workspace_contract != self.workspace_contract :
					eventType = 'PartnershipAccepted' 					
					doc_id = None
					helptext= 'Partnership accepted by ' + issuer_name
					alert[date] =  {'alert' : helptext, 'event' : eventType, 'doc_id' : doc_id}
				else :
					pass								
		self.eventslist = alert
		return self.eventslist
	
	# always available
	def getManagementKeys(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(1).call()
		mymanagementkeys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			print(self.mode.relay_publickeyhex)
			print(key)
			if key[2] == self.mode.relay_publickeyhex :
				self.web_relay_authorized = True	
			controller = data_from_publickey(key[2].hex(), self.mode)
			if controller is None or controller['address'] is None or controller['username'] is None :
				pass
			else :
				mymanagementkeys.append({"address": controller['address'], "publickey": key[2].hex(), "workspace_contract" : controller['workspace_contract'] , 'username' : controller['username'] } )
		self.managementkeys = mymanagementkeys
		return self.managementkeys

	# always available
	def getClaimKeys(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(3).call()
		claimkeys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			issuer = data_from_publickey(key[2].hex(), self.mode)
			if issuer is None or issuer['address'] is None or issuer['username'] is None : 
				pass
			else :	
				claimkeys.append({"address": issuer['address'], 	"publickey": key[2].hex(), "workspace_contract" : issuer['workspace_contract'] , 'username' : issuer['username'] } )
		self.claimkeys = claimkeys
		return self.claimkeys
	
	# Need web_relay_authorized = True
	def getPartners(self) :
		if not self.web_relay_authorized :
			print('Identity.py, Impossible to upload partner without key 1')		
			self.partners = []
			return   
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		acct = Account.from_key(self.mode.relay_private_key)
		self.mode.w3.eth.defaultAccount = acct.address
		partners = []
		partners_list = contract.functions.getKnownPartnershipsContracts().call()
		for partner_workspace_contract in partners_list :			
			partners.append({"workspace_contract" : partner_workspace_contract , 'username' : getUsername(partner_workspace_contract,self.mode) } )
		self.partners = partners
		return self.partners
	
	"""
	def getRsa_key(self) :
		filename = "./RSA_key/"+self.mode.BLOCKCHAIN+'/'+str(self.address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
		try :
			fp =open(filename,"r")
		except :
			self.rsa_key is None
			return None
		self.rsa_key = fp.read()	
		fp.close()   
		return self.ras_key
	"""
		
	def getPersonal(self) :
		self.personal = getpersonal(self.workspace_contract, self.mode)
		return self.personal
			
	def getContact(self) :
		self.contact = getcontact(self.mode.relay_workspace_contract, self.mode.relay_private_key, self.workspace_contract, self.mode)
		return self.contact		
	
	"""contact = {
  'id': 'did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:document:15',
  'endpoint': 'http://127.0.0.1:4000/talao/data/did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:document:15',
  'data': {
    'email': 'pierre@talao.io',
    'phone': '0607182594',
    'twitter': '@pierredavid'
  }
}"""
	
	
	def getLanguage(self) :	
		lang = getlanguage(self.workspace_contract, self.mode)		
		if lang is None :
			self.language = ( {}, '', '', '')
			return self.language
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
	
		self.language = (context, lang1, lang2, lang3)
		return self.language
	
	def getEducation(self) :
		self.education = get_education(self.workspace_contract, self.mode)
		return self.education
	
	def getExperience(self) :
		self.experience = getexperience(self.workspace_contract, self.address, self.mode)
		return self.experience
	
	
	# all setters need web_relay_authorized = True

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
	
	""" Only Owner 
	# destroy Identity and remove it from register
	def killIdentity(self) :				
		deleteName(self.username, self.mode) 
		destroyWorkspace(self.workspace_contract, self.private_key, self.mode)
		return True	
	
	# def changeOwner(self, address_new_owner ) :  """
	
	
	
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
	
	
