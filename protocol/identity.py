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
from .nameservice import namehash, getUsername, updateName, data_from_publickey, username_to_data
from .GETresolver import getresolver
from .GETresume import getresume, getlanguage, setlanguage, get_education, get_certificate
from .ADDkey import addkey
from .ADDdocument import createdocument
from .claim import Claim
from .document import Experience, Education, File
 
class Identity() :
	
	def __init__(self, workspace_contract, mode, address=None, SECRET=None,  AES_key=None, backend_Id=None, rsa_key=None, authenticated=False):
		
		if whatisthisaddress(workspace_contract, mode)['type'] != 'workspace' :
			print("identity.py, this address is not an Identity")
			return None
		
	
		
		self.workspace_contract = workspace_contract
		self.mode = mode
		self.synchronous = True # UI synchrone par defaut, on attend les receipts des transactions blockchain
		self.AES_key = AES_key
		self.SECRET = SECRET
		self.backend_Id=backend_Id		
		self.authenticated = authenticated
		self.did = 'did:talao:'+mode.BLOCKCHAIN+':'+self.workspace_contract[2:]
		self.web_relay_activated = False			
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
		
		self.get_identity_personal()	
		
		if self.authenticated :
			self.eth = mode.w3.eth.getBalance(self.address)/1000000000000000000
			self.token = token_balance(self.address,mode)
			self.get_management_keys()
			self.get_claim_keys()
			self.get_white_keys()
			self.get_events()
			self.get_partners()				
		else :
			self.eventslist = dict()
			self.partners = []
			self.managementkeys = []
		
		if self.category  == 2001 :
			self.type = "company"
			try :
				self.name = self.personal['name']['data']
			except :
				self.name = 'Unknown'
				self.personal['name']={'data' : 'Unknown', 'id' : "", 'data' : ""}
				
		if self.category == 1001 :
			self.type = "person"
			firstname = "" if self.personal['firstname']['claim_value'] is None else self.personal['firstname']['claim_value']
			lastname = "" if self.personal['lastname']['claim_value'] is None else self.personal['lastname']['claim_value']
			self.name = firstname.capitalize() + ' ' + lastname.capitalize()
			self.get_identity_experience()
			self.get_identity_certificate()
			self.get_language()
			self.get_identity_education()
			self.picture = getpicture(self.workspace_contract, self.mode)
			if self.picture is not None :
				client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
				client.get(self.picture)
				os.system('mv '+ self.picture+' ' +'photos/'+self.picture)	
			

	# filters on external events only, always available
	def get_events(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		alert = dict()
		filter_list = [contract.events.DocumentAdded.createFilter(fromBlock= 6200000,toBlock = 'latest'),
					contract.events.ClaimAdded.createFilter(fromBlock= 6200000,toBlock = 'latest'),
					contract.events.PartnershipRequested.createFilter(fromBlock= 6200000,toBlock = 'latest'),
					contract.events.PartnershipAccepted.createFilter(fromBlock= 6200000,toBlock = 'latest')]		
		for i in range(0, len(filter_list)) :
			eventlist = filter_list[i].get_new_entries()
			for doc in eventlist :
				transactionhash = doc['transactionHash']
				transaction = self.mode.w3.eth.getTransaction(transactionhash)
				issuer = transaction['from']
				issuer_workspace_contract = ownersToContracts(issuer,self.mode)
				profil = readProfil(issuer,self.mode)
				firstname = profil.get('givenName', "")
				lastname = profil.get('familyName', "")
				issuer_name = firstname+' '+lastname
				blockNumber = transaction['blockNumber']
				block = self.mode.w3.eth.getBlock(blockNumber)
				date = datetime.fromtimestamp(block['timestamp'])			
				
				if i == 0 and issuer_workspace_contract != self.workspace_contract :
					eventType = 'DocumentAdded' 
					doc_id = 'did:talao:' + self.mode.BLOCKCHAIN+':' + issuer_workspace_contract[2:] + ':document:' + str(doc['args']['id'])
					helptext = issuer_name +' issued a new certificate'	
					alert[date] =  {'alert' : helptext, 'event' : eventType, 'doc_id' : doc_id}
				elif i == 1 and issuer_workspace_contract != self.workspace_contract :
					eventType = 'ClaimAdded' 
					doc_id = 'did:talao:' + self.mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:] + ':claim:' + str(doc['args']['claimId'].hex())
					helptext = issuer_name + ' issued a new certificate'
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
		return True
	
	
	
	
	# always available
	def get_management_keys(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(1).call()
		mymanagementkeys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			if key[2] == self.mode.relay_publickeyhex :
				self.web_relay_activated = True	
		return True
	
	
		
	# always available
	def get_claim_keys(self) :
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
		return True
	
	
	# always available
	def get_white_keys(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(5).call()
		whitekeys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			issuer = data_from_publickey(key[2].hex(), self.mode)
			if issuer is None or issuer['address'] is None or issuer['username'] is None : 
				pass
			else :	
				whitekeys.append({"address": issuer['address'],
								"publickey": key[2].hex(),
								 "workspace_contract" : issuer['workspace_contract'],
								  'username' : issuer['username'] } )
		self.whitekeys = whitekeys
		return True
		
		
	# Need web_relay_authorized = True
	def get_partners(self) :
		if not self.web_relay_activated :
			print('Identity.py, Impossible to upload partner without key 1')		
			self.partners = []			 
		else :
			contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
			acct = Account.from_key(self.mode.relay_private_key)
			self.mode.w3.eth.defaultAccount = acct.address
			partners = []
			partners_list = contract.functions.getKnownPartnershipsContracts().call()
			liste = ["Unknown","Authorized", "Pending","Rejected","Removed"] 
			print(partners_list)
			for partner_workspace_contract in partners_list :	
				authorization_index = contract.functions.getPartnership(partner_workspace_contract).call()[1]
				if authorization_index != 4 :
					partner_username = getUsername(partner_workspace_contract, self.mode)
					partner_address = contractsToOwners(partner_workspace_contract, self.mode)
					contract = self.mode.w3.eth.contract(partner_workspace_contract,abi=constante.workspace_ABI)
					my_status = contract.functions.getMyPartnershipStatus().call()
					partner_publickey = self.mode.w3.soliditySha3(['address'], [partner_address])
					partners.append({"address": partner_address,
								"publickey": partner_publickey,
								 "workspace_contract" : partner_workspace_contract,
								  'username' : partner_username,
								  'authorized' : liste[authorization_index],
								  'status' : liste[my_status] } )				
			self.partners = partners
		print(partners)
		return True
	
	def topicname2topicvalue(topicname) :
		topicvaluestr =''
		for i in range(0, len(topicname))  :
			a = str(ord(topicname[i]))
			if int(a) < 100 :
				a='0'+a
			topicvaluestr = topicvaluestr + a
		return int(topicvaluestr)
	
		# always available
	def get_identity_personal(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)	
		person = ['firstname', 'lastname','contact_email','contact_phone','birthdate',]
		company = ['name','contact_name','contact_email','contact_phone','website',]

		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		category = contract.functions.identityInformation().call()[1]	
		personal = dict()
		
		if category == 1001 : 
			for topicname in person :
				claim = Claim().relay_get(self.workspace_contract, topicname, self.mode)
				personal[topicname] = claim.__dict__
	
		if category == 2001 : 
			for topicname in company :
				claim = Claim().relay_get(self.workspace_contract, topicname, self.mode)
				personal[topicname] = claim.__dict__ 
		print('personal =', personal)
		self.personal = personal
		self.category = category
		return True
	
	# always available
	def get_language(self) :	
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
	
	# always available
	def get_identity_education(self) :
		self.education = get_education(self.workspace_contract, self.mode)
		return self.education
	
	# always available
	def get_identity_experience(self) :	
		self.experience = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in contract.functions.getDocuments().call() :
			if contract.functions.getDocument(doc_id).call()[0] in [50000, 50001, 50002] : # doctype
				experience = Experience().relay_get(self.workspace_contract, doc_id, self.mode)
				new_experience = {'id' : 'did:talao:'+ self.mode.BLOCKCHAIN+':'+ self.workspace_contract[2:]+':document:'+ str(experience.doc_id),
									'title' : experience.title,
									'doc_id' : experience.doc_id,
									'description' : experience.description,
									'start_date' : experience.start_date,
									'end_date' : experience.end_date,
									'company' : {'name' : experience.company['name'], 
												'contact_name' : experience.company['contact_name'],
												'contact_email' : experience.company['contact_email'],
												'contact_phone' : experience.company.get('contact_phone', 'unknown') # a retirer
												},
									'certificate_link' : experience.certificate_link,
									'skills' : experience.skills
									}	
				self.experience.append(new_experience)
		return True	
		
		
	# always available
	def get_identity_certificate(self) :
		self.certificate = get_certificate(self.workspace_contract, self.address, self.mode)
		return self.certificate
	
	
	# all setters need web_relay_authorized = True

	"""def deleteExperience(self, experienceId) :			
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		claimdocId=experienceId.split(':')[5]
		if experienceId.split(':')[4] == 'document' :
			deleteDocument(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key,claimdocId,self.mode)
		else :
			deleteClaim(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, '0x'+claimdocId,self.mode)
		self.getExperience()
		return True"""
		
	def uploadPicture(self,picturefile) :
		self.picture = savepictureProfile(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, picturefile,self.mode, synchronous = True)	
		return self.picture
	
	"""	# need webrelay
	def add_experience(self, experience, mydays, encrypted ) : # document type 55000 not compatible with freedapp
		return createdocument(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, 55000, experience, mydays, encrypted, self.mode, synchronous=self.wait)
	
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
		return True	"""

	# update le username
	def updateUsername(self, newusername) : 
		return updateName(self.username, newusername, self.mode)
	
	
	
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
	
	
