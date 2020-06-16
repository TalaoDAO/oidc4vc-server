"""
A la creation, si les informatiosn ne sont pas données, l instance de classe va les chercher

les signatures sont réalisée par le Relay
uniquemet utilisé en lecture.


"""
from datetime import datetime
from operator import itemgetter, attrgetter
import random
from eth_account import Account
import ipfshttpclient
import os
import csv 

import constante
from .Talao_token_transaction import contractsToOwners, ownersToContracts,token_balance, get_image,  read_workspace_info
from .claim import Claim
from .document import Document, read_profil
from .file import File
 
import ns
 
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
		
		#donload pictures on server
		self.picture = get_image(self.workspace_contract, 'picture', self.mode)
		if self.picture is not None :
			client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
			client.get(self.picture)
			os.system('mv '+ self.picture + ' ' + 'photos/' + self.picture)	
		self.signature = get_image(self.workspace_contract, 'signature', self.mode)
		if self.signature is not None :
			client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
			client.get(self.signature)
			os.system('mv '+ self.signature + ' ' + 'photos/' + self.picture)	
		
		
		self.get_all_documents()
		
		self.get_identity_file()
				
		if self.authenticated :
			self.has_relay_rsa_key()
			if self.rsa_key :
				self.get_email_secret()
			else :
				self.email = 'Encrypted'
				self.secret = 'Encrypted'
				self.aes = 'Encrypted'
					
			self.has_relay_private_key()
			if self.private_key :
				self.get_partners()				
			else :
				self .partners = []
				
			self.eth = mode.w3.eth.getBalance(self.address)/1000000000000000000
			self.token = token_balance(self.address,mode)
			self.is_relay_activated()
			self.get_issuer_keys()
			self.get_white_keys()
			self.get_events()
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
			self.profil_title = "" if self.personal['profil_title']['claim_value'] is None else self.personal['profil_title']['claim_value']
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
		self.private_key = False
		self.private_key_value = None
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
				profil, category = read_profil(issuer_workspace_contract, self.mode, loading='light')
				
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
			return False
		else :
			self.relay_activated = False
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
	def get_issuer_keys(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(20002).call()
		issuer_keys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			issuer = ns.get_data_from_publickey(key[2].hex(), self.mode) # most important part of the function.....see what it implies ! 
			if issuer is None or issuer['address'] is None or issuer['username'] is None : 
				pass
			else :	
				issuer_keys.append({"address": issuer['address'],
									"publickey": key[2].hex(),
									"workspace_contract" : issuer['workspace_contract'],
									'username' : issuer['username'] } )
		self.issuer_keys = issuer_keys
		return True
	
	
	# always available	
	def get_white_keys(self) :
		self.white_keys = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(5).call()
		white_keys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			issuer = ns.get_data_from_publickey(key[2].hex(), self.mode)
			if issuer is None :
				pass
			else :	
				self.white_keys.append({"address": issuer['address'],
									"publickey": key[2].hex(),
									"workspace_contract" : issuer['workspace_contract'],
									'username' : issuer['username'] } )
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
			partner_username = ns.get_username_from_resolver(partner_workspace_contract)
			if partner_username is not None :
				partner_address = contractsToOwners(partner_workspace_contract, self.mode)	
				partner_publickey = self.mode.w3.soliditySha3(['address'], [partner_address])
				self.partners.append({"address": partner_address,
								"publickey": partner_publickey,
								 "workspace_contract" : partner_workspace_contract,
								  'username' : partner_username,
								  'authorized' : liste[authorization_index],
								  'status' : 'Not available'})
		# on met a jour le status avec un acces par le owner au parnership  dans le contract du partner
		if self.private_key :
			acct = Account.from_key(self.private_key_value)
			self.mode.w3.eth.defaultAccount = acct.address	
			for index in range (0, len(self.partners)) :		
				contract = self.mode.w3.eth.contract(self.partners[index]['workspace_contract'],abi=constante.workspace_ABI)
				self.partners[index]['status'] = liste[contract.functions.getMyPartnershipStatus().call()]			
		return True
	
	def topicname2topicvalue(topicname) :
		topicvalue_str =''
		for i in range(0, len(topicname))  :
			a = str(ord(topicname[i]))
			a = '0'+ a  if int(a) < 100 else a
			topicvalue_str += a
		return int(topicvalue_str)
	
		# always available
	def get_identity_personal(self) :
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)	
		person = ['firstname', 'lastname','contact_email','contact_phone','birthdate','postal_address', 'about', 'profil_title', 'education']
		company = ['name','contact_name','contact_email','contact_phone','website', 'about']

		contract = self.mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		self.category = contract.functions.identityInformation().call()[1]	
		self.personal = dict()
		
		if self.category == 1001 : 
			topiclist = person
		if self.category == 2001 :
			topiclist = company	
		for topicname in topiclist :
			claim = Claim()
			claim.get_by_topic_name(self.workspace_contract, topicname, self.mode)
			self.personal[topicname] = claim.__dict__
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
			kyc = Document('kyc')
			kyc.relay_get(self.workspace_contract, doc_id, self.mode, loading='light')
			new_kyc = kyc.__dict__
			self.kyc.append(new_kyc)
		return True	
	
	
	def get_identity_certificate(self) :
		self.certificate = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.certificate_list  :
			certificate = Document('certificate')
			certificate.relay_get(self.workspace_contract, doc_id, self.mode, loading='light')
			new_certificate = certificate.__dict__
			self.certificate.append(new_certificate)
		return True	
	
	
	def get_identity_kbis(self) :
		self.kbis = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.kbis_list  :
			kbis = Document('kbis')
			kbis.relay_get(self.workspace_contract, doc_id, self.mode, loading='light')
			new_kbis = kbis.__dict__
			self.kbis.append(new_kbis)
		return True	
	
	
	def get_identity_education(self) :
		self.education = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.education_list  :
			education = Document('education')
			education.relay_get(self.workspace_contract, doc_id, self.mode, loading='light')
			new_education = education.__dict__
			self.education.append(new_education)
		return True	
		
	
	def get_identity_experience(self) :	
		self.experience = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.experience_list  :
			experience = Document('experience')
			experience.relay_get(self.workspace_contract, doc_id, self.mode, loading='light')
			new_experience = experience.__dict__ 
			self.experience.append(new_experience)
		return True	
	
	
	def get_identity_file(self) :	
		self.identity_file = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.file_list :
			this_file = File()
			this_file.get(self.workspace_contract, doc_id, "", self.mode)			
			new_file = this_file.__dict__
			self.identity_file.append(new_file)
		return True		
	

		
	def uploadPicture(self,picturefile) :
		self.picture = savepictureProfile(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, picturefile,self.mode, synchronous = True)	
		return self.picture

	
	
