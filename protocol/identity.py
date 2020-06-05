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
import csv 
# dependances
import constante

from .Talao_token_transaction import contractsToOwners, ownersToContracts,token_balance, addclaim, partnershiprequest, whatisthisaddress
from .Talao_token_transaction import  updateSelfclaims, savepictureProfile, getpicture, deleteDocument, deleteClaim, read_workspace_info
from .nameservice import namehash, getUsername, updateName, data_from_publickey, username_to_data
#from .GETresolver import getresolver
#from .GETresume import getresume, getlanguage, setlanguage, get_education, get_certificate
from .key import addkey
#from .ADDdocument import createdocument
from .claim import Claim
from .document import Experience, Education, Kbis, Certificate, Kyc, read_profil
from .file import File
 
 
class Identity() :
	
	def __init__(self, workspace_contract, mode, authenticated=False):
			
		self.workspace_contract = workspace_contract
		
		self.mode = mode
		self.synchronous = True # UI synchrone par defaut, on attend les receipts des transactions blockchain
		self.authenticated = authenticated
		self.did = 'did:talao:'+mode.BLOCKCHAIN + ':' + self.workspace_contract[2:]
		self.address = contractsToOwners(self.workspace_contract,mode)
				
		#self.get_management_keys()
		self.get_identity_personal()	
		
		self.picture = getpicture(self.workspace_contract, self.mode)
		if self.picture is not None :
			client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
			client.get(self.picture)
			os.system('mv '+ self.picture+' ' +'photos/'+self.picture)	
		
		self.get_all_documents()
		
		self.get_identity_file()
				
		if self.authenticated :
			self.has_relay_rsa_key()
			
			if self.rsa_key :
				self.get_email_secret()
			else :
				self.email = 'Encrypted'
				self.secret = 'Encrypted'
					
			self.has_relay_private_key()
			self.eth = mode.w3.eth.getBalance(self.address)/1000000000000000000
			self.token = token_balance(self.address,mode)
			self.is_relay_activated()
			self.get_issuer_keys()
			self.get_white_keys()
			self.get_events()
			self.get_partners()				
		else :
			self.eventslist = dict()
			self.partners = []
			self.private_key = False
			self.rsa_key = False
			self.relay_activated = False
		
		if self.category  == 2001 :
			self.type = "company"
			self.name = self.personal['name']['claim_value']			
			self.get_identity_kbis()
			
		if self.category == 1001 :
			self.type = "person"
			firstname = "" if self.personal['firstname']['claim_value'] is None else self.personal['firstname']['claim_value']
			lastname = "" if self.personal['lastname']['claim_value'] is None else self.personal['lastname']['claim_value']
			self.name = firstname.capitalize() + ' ' + lastname.capitalize()
			self.get_identity_experience()
			self.get_identity_certificate()
			#self.get_language()
			self.get_identity_education()
			self.get_identity_kyc()
			self.get_identity_certificate()
	
	def get_email_secret(self) :
		(workspace_contract, category, self.email , self.secret, self.aes) = read_workspace_info (self.address, self.rsa_key_value, self.mode)
		return
					
	def has_relay_private_key(self) :
		fname = self.mode.BLOCKCHAIN +"_Talao_Identity.csv"
		identity_file = open(fname, newline='')
		reader = csv.DictReader(identity_file)
		for row in reader :
			if row['ethereum_address'] == self.address :
				self.private_key = False if row.get('private_key', '')[:2] != '0x'  else True				
				if self.private_key :
					self.private_key_value = row['private_key'] 
				
	def has_relay_rsa_key(self) :
		filename = "./RSA_key/" + self.mode.BLOCKCHAIN + '/' + str(self.address) + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
		try :
			fp = open(filename,"r")
			rsa_key = fp.read()
			self.rsa_key = True	
			fp.close()  
			self.rsa_key_value = rsa_key 
		except IOError :
			self.rsa_key = False		
				
	# filters on external events only, always available
	def get_events(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		alert = dict()
		filter_list = [	contract.events.PartnershipRequested.createFilter(fromBlock= 6200000,toBlock = 'latest'),
					contract.events.PartnershipAccepted.createFilter(fromBlock= 6200000,toBlock = 'latest')]		
		for i in range(0, len(filter_list)) :
			eventlist = filter_list[i].get_all_entries()
			for doc in eventlist :
				transactionhash = doc['transactionHash']
				transaction = self.mode.w3.eth.getTransaction(transactionhash)
				issuer = transaction['from']
				issuer_workspace_contract = ownersToContracts(issuer,self.mode)
				profil, category = read_profil(issuer_workspace_contract, self.mode)
				
				if category == 1001:
					firstname = "Unnknown" if profil['firstname'] is None else profil['firstname']					
					lastname = "Unknown" if profil['lastname'] is None else profil['lastname']
					issuer_name = firstname + ' ' + lastname
				if category == 2001 :				
					issuer_name = 'unknown' if  profil['name'] is None else profil['name']
				blockNumber = transaction['blockNumber']
				block = self.mode.w3.eth.getBlock(blockNumber)
				date = datetime.fromtimestamp(block['timestamp'])			
				
				if i == 0 and issuer_workspace_contract != self.workspace_contract :
					eventType = 'PartnershipRequested' 					
					doc_id = None
					helptext= 'Request for partnership from ' + issuer_name
					alert[date] =  {'alert' : helptext, 'event' : eventType, 'doc_id' : doc_id}
				elif i == 1 and issuer_workspace_contract != self.workspace_contract :
					eventType = 'PartnershipAccepted' 					
					doc_id = None
					helptext= 'Partnership accepted by ' + issuer_name
					alert[date] =  {'alert' : helptext, 'event' : eventType, 'doc_id' : doc_id}
				else :
					pass								
		self.eventslist = alert
		return True
	
	
	def is_relay_activated(self):
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		key = self.mode.w3.soliditySha3(['address'], [self.mode.relay_address])
		if 1 in contract.functions.getKeyPurposes(key).call() :
			self.relay_activated = True
		else :
			self.relay_activated = False
		return
	
	# Not used today
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
	def get_issuer_keys(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(20002).call()
		issuer_keys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			issuer = data_from_publickey(key[2].hex(), self.mode)
			if issuer is None or issuer['address'] is None or issuer['username'] is None : 
				pass
			else :	
				issuer_keys.append({"address": issuer['address'], 	"publickey": key[2].hex(), "workspace_contract" : issuer['workspace_contract'] , 'username' : issuer['username'] } )
		self.issuer_keys = issuer_keys
		return True
	
	
	# always available
	def get_white_keys(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(5).call()
		white_keys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			issuer = data_from_publickey(key[2].hex(), self.mode)
			if issuer is None or issuer['address'] is None or issuer['username'] is None : 
				pass
			else :	
				white_keys.append({"address": issuer['address'],
								"publickey": key[2].hex(),
								 "workspace_contract" : issuer['workspace_contract'],
								  'username' : issuer['username'] } )
		self.white_keys = white_keys
		return True
		
		
	# Need web_relay_authorized = True (key 20003) and need private_key to get other parye status
	def get_partners(self) :
		# on obtient la liste des partners avec le Relay qui a une cle 1
		self.partners = []
		acct = Account.from_key(self.mode.relay_private_key)
		self.mode.w3.eth.defaultAccount = acct.address
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		partners_list = contract.functions.getKnownPartnershipsContracts().call()
		liste = ["Unknown","Authorized", "Pending","Rejected","Removed",] 
		for partner_workspace_contract in partners_list :	 
			try :
				authorization_index = contract.functions.getPartnership(partner_workspace_contract).call()[1]
			except Exception as ex:
				print(ex)
			partner_username = getUsername(partner_workspace_contract, self.mode)
			partner_address = contractsToOwners(partner_workspace_contract, self.mode)	
			partner_publickey = self.mode.w3.soliditySha3(['address'], [partner_address])
			self.partners.append({"address": partner_address,
								"publickey": partner_publickey,
								 "workspace_contract" : partner_workspace_contract,
								  'username' : partner_username,
								  'authorized' : liste[authorization_index],
								  'status' : 'Not available'})
		# on met a jour le status avec un acces par le owner au parnership  dand le contract du partner
		if self.private_key :
			acct = Account.from_key(self.private_key_value)
			self.mode.w3.eth.defaultAccount = acct.address	
			for index in range (0, len(self.partners)) :		
				contract = self.mode.w3.eth.contract(self.partners[index]['workspace_contract'],abi=constante.workspace_ABI)
				self.partners[index]['status'] = liste[contract.functions.getMyPartnershipStatus().call()]			
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
		person = ['firstname', 'lastname','contact_email','contact_phone','birthdate','postal_address']
		company = ['name','contact_name','contact_email','contact_phone','website',]

		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		category = contract.functions.identityInformation().call()[1]	
		personal = dict()
		
		if category == 1001 : 
			for topicname in person :
				claim = Claim()
				claim.get_by_topic_name(self.workspace_contract, topicname, self.mode)
				personal[topicname] = claim.__dict__
	
		if category == 2001 : 
			for topicname in company :
				claim = Claim()
				claim.get_by_topic_name(self.workspace_contract, topicname, self.mode)
				personal[topicname] = claim.__dict__ 
		
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
	
	
	def get_all_documents(self) :
		self.file_list = []
		self.experience_list = []
		self.education_list = []
		self.other_list = []
		self.kbis_list = []
		self.kyc_list = []
		self.certificate_list=[]
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in contract.functions.getDocuments().call() :
			doctype = contract.functions.getDocument(doc_id).call()[0]
			if doctype in [30000, 30001, 30002] :
				self.file_list.append(doc_id)
			elif doctype in [50000, 50001, 50002] :
				self.experience_list.append(doc_id)
			elif doctype in [40000, 40001, 40002] :
				self.education_list.append(doc_id)
			elif doctype == 10000 :
				self.kbis_list.append(doc_id)	
			elif doctype == 15000 :
				self.kyc_list.append(doc_id)
			elif doctype == 20000 :
				self.certificate_list.append(doc_id)
			else :
				self.other_list.append(doc_id)
		return
	
	def get_identity_kyc(self) :
		self.kyc = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.kyc_list  :
			kyc = Kyc()
			kyc.relay_get_kbis(self.workspace_contract, doc_id, self.mode)
			new_kyc = {'id' : 'did:talao:'+ self.mode.BLOCKCHAIN+':'+ self.workspace_contract[2:]+':document:'+ str(kbis.doc_id),
									'country' : kyc.country,
									'doc_id' : kyc.doc_id,
									'firstname' : kyc.firstname,
									'lastname' : kyc.lastname,
									'sex' : kyc.sex,
									'date_of_birth' : kyc.date_of_birth,
									'date_of_issue' : kyc.date_of_issue,									
									'date_of_expiration' : kyc.date_of_expiration,
									'authority' : kyc.authority
									}	
			self.kyc.append(new_kyc)
		return True	
	
	
	def get_identity_certificate(self) :
		self.certificate = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.certificate_list  :
			certificate = Certificate()
			certificate.relay_get_kbis(self.workspace_contract, doc_id, self.mode)
			new_certificate = {'id' : 'did:talao:'+ self.mode.BLOCKCHAIN+':'+ self.workspace_contract[2:]+':document:'+ str(certificate.doc_id),
									'type' : certificate.type,
									'doc_id' : certificate.doc_id,
									'firstname' : certificate.firstname,
									'lastname' : certificate.lastname,
									'logo' : certificate.logo,
									'signature' : certificate.signature,
									'start_date' : certificate.star_date,									
									'end_date' : certificate.end_date,
									'company' : {'name' : certificate.company['name'], 
												'contact_name' : certificate.company['contact_name'],
												'contact_email' : certificate.company['contact_email'],
												'contact_phone' : certificate.company['contact_phone']
												},
									'manager' : certificate.manager,
									'title' : certiificate.title,
									'description' : certificate.description,
									'skills' : certificate.skills,
									'score_delivery' : certificate.score_delivery,
									'score_recommendation' : certificate.score_recommendation,
									'score_communication' : certificate.score_communication,
									'score_schedule' : certificate.score_schedule
									 }	
			self.certificate.append(new_certificate)
		return True	
	

	
	
	def get_identity_kbis(self) :
		self.kbis = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.kbis_list  :
			kbis = Kbis()
			kbis.relay_get_kbis(self.workspace_contract, doc_id, self.mode)
			new_kbis = {'id' : 'did:talao:'+ self.mode.BLOCKCHAIN+':'+ self.workspace_contract[2:]+':document:'+ str(kbis.doc_id),
									'siret' : kbis.siret,
									'doc_id' : kbis.doc_id,
									'name' : kbis.name,
									'date' : kbis.date,
									'legal_form' : kbis.legal_form,
									'namf' : kbis.naf,
									'capital' : kbis.capital,
									'address' : kbis.address,
									'activity' : kbis.activity,
									'ceo' : kbis.ceo,
									'managing_director' : kbis.managing_director
									}	
			self.kbis.append(new_kbis)
		return True	
	
	
	
	# always available
	def get_identity_education(self) :
		self.education = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.education_list  :
			education = Education()
			education.relay_get_education(self.workspace_contract, doc_id, self.mode)
			new_education = {'id' : 'did:talao:'+ self.mode.BLOCKCHAIN+':'+ self.workspace_contract[2:]+':document:'+ str(education.doc_id),
									'title' : education.title,
									'doc_id' : education.doc_id,
									'description' : education.description,
									'start_date' : education.start_date,
									'end_date' : education.end_date,
									'organization' : {'name' : education.organization['name'], 
												'contact_name' : education.organization['contact_name'],
												'contact_email' : education.organization['contact_email'],
												'contact_phone' : education.organization['contact_phone'],
												},
									'certificate_link' : education.certificate_link,
									'skills' : education.skills
									}	
			self.education.append(new_education)
		return True	
		
	
	# always available
	def get_identity_experience(self) :	
		self.experience = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.experience_list  :
			experience = Experience()
			experience.relay_get_experience(self.workspace_contract, doc_id, self.mode)
			new_experience = experience.__dict__ 
			"""
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
									}"""	
			self.experience.append(new_experience)
		return True	
	
	
		
	def get_identity_file(self) :	
		self.identity_file = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.file_list :
			this_file = File()
			this_file.get(self.workspace_contract, doc_id, "", self.mode)			
			new_file = {'id' : 'did:talao:'+ self.mode.BLOCKCHAIN+':'+ self.workspace_contract[2:]+':document:'+ str(this_file.doc_id),
									'filename' : this_file.filename,
									'doc_id' : this_file.doc_id,
									'created' : this_file.created,
									'privacy' : this_file.privacy,
									'doctype' : this_file.doctype,
									'issuer' : this_file.issuer,
									'transaction_hash' : this_file.transaction_hash
									}	
			self.identity_file.append(new_file)
		return True		
	
	
	
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
	"""
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
	"""
	
