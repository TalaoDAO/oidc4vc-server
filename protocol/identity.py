"""
A la creation, si les informatiosn ne sont pas données, l instance de classe va les chercher

les signatures sont réalisée par le Relay
uniquemet utilisé en lecture.


"""

import os.path
from os import path
from datetime import datetime
from operator import itemgetter, attrgetter
import random
from eth_account import Account
import os
import csv 
import requests
import shutil

import constante
from .Talao_token_transaction import contractsToOwners, ownersToContracts,token_balance, get_image,  read_workspace_info
from .claim import Claim
from .document import Document, read_profil
from .file import File
 
import ns
import privatekey
 
class Identity() :
	
	def __init__(self, workspace_contract, mode, authenticated=False, workspace_contract_from = None, private_key_from = None):
			
		self.workspace_contract = workspace_contract
		
		self.mode = mode
		self.synchronous = True # UI synchrone par defaut, on attend les receipts des transactions blockchain
		self.authenticated = authenticated
		self.did = 'did:talao:'+mode.BLOCKCHAIN + ':' + self.workspace_contract[2:]
		self.address = contractsToOwners(self.workspace_contract,mode)
		self.get_all_documents()
		self.get_issuer_keys()
		
		if self.authenticated :		
			self.has_relay_rsa_key()
			if self.rsa_key :
				self.get_secret()
			else :
				self.secret = 'Encrypted'
				self.aes = 'Encrypted'
					
			self.has_relay_private_key()
			print('rsa  key = ', self.rsa_key)
			print('private key = ', self.private_key)
			if self.private_key :
				self.get_partners()	
			else :
				self.partners = []
			
			self.eth = mode.w3.eth.getBalance(self.address)/1000000000000000000
			self.token = token_balance(self.address,mode)
			self.is_relay_activated()			
			self.get_white_keys()
			self.get_identity_personal(self.workspace_contract, self.private_key_value)	
			self.get_identity_file(self.workspace_contract, self.private_key_value)
		else :
			self.partners = []
			self.private_key = False
			self.rsa_key = False
			self.relay_activated = False
			self.get_identity_file(workspace_contract_from,private_key_from)
			self.get_identity_personal(workspace_contract_from, private_key_from)
		
		if self.category  == 2001 : # company 
			self.type = "company"
			self.name = self.personal['name']['claim_value']			
			self.get_identity_kbis()
			
		if self.category == 1001 : # person
			self.profil_title = "" if self.personal['profil_title']['claim_value'] is None else self.personal['profil_title']['claim_value']
			self.type = "person"
			firstname = "" if self.personal['firstname']['claim_value'] is None else self.personal['firstname']['claim_value']
			lastname = "" if self.personal['lastname']['claim_value'] is None else self.personal['lastname']['claim_value']
			self.name = firstname + ' ' + lastname
			self.get_identity_experience()
			self.get_identity_certificate()
			self.get_identity_education()
			self.get_identity_kyc()
			self.get_identity_certificate()
			self.get_identity_skills()	
			
		#download pictures on server dir /uploads/ fill with anonymous if None
		self.picture = get_image(self.workspace_contract, 'picture', self.mode)
		if self.picture is None :
			self.picture = 'QmRzXTCn5LyVpdUK9Mc5kTa3VH7qH4mqgFGaSZ3fncEFaq' if self.type == "person" else 'QmXKeAgNZhLibNjYJFHCiXFvGhqsqNV2sJCggzGxnxyhJ5'	
		
		self.signature = get_image(self.workspace_contract, 'signature', self.mode)
		if self.signature is None :
			self.signature = 'QmS9TTtjw1Fr5oHkbW8gcU7TnnmDvnFVUxYP9BF36kgV7u' 
		
	
	def get_secret(self) :
		(self.category, self.secret, self.aes) = read_workspace_info (self.address, self.rsa_key_value, self.mode)
		return
					
	def has_relay_private_key(self) :
		self.private_key_value =  privatekey.get_key(self.address, 'private_key', self.mode)
		self.private_key = False if self.private_key_value is None else True
		return			
					
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
			self.rsa_key_value = None
	
	# one checks if Relay has a key 1
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
		self.issuer_keys = []
		for i in keylist :		
			key = contract.functions.getKey(i).call()
			issuer = ns.get_data_from_publickey('0x' +key[2].hex(), self.mode) # most important part of the function.....see what it implies ! 
			if issuer is None : 
				pass
			else :	
				self.issuer_keys.append({"address": issuer['address'],
									"publickey": key[2].hex(),
									"workspace_contract" : issuer['workspace_contract'],
									'username' : issuer['username'] } )
		return True
	
	
	# always available	
	def get_white_keys(self) :
		self.white_keys = []
		contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(5).call()
		white_keys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			issuer = ns.get_data_from_publickey('0x' + key[2].hex(), self.mode)
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
		print('private key = ', self.private_key_value)
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
				return False
			partner_username = ns.get_username_from_resolver(partner_workspace_contract, self.mode)
			
			#if partner_username is not None :
			partner_username = "Unknown" if partner_username is None else partner_username
			partner_address = contractsToOwners(partner_workspace_contract, self.mode)	
			partner_publickey = self.mode.w3.soliditySha3(['address'], [partner_address])
			self.partners.append({"address": partner_address,
								"publickey": partner_publickey,
								 "workspace_contract" : partner_workspace_contract,
								  'username' : partner_username,
								  'authorized' : liste[authorization_index],
								  'status' : 'Not available'})
		# on met a jour le status avec un acces par le owner au partnership  dans le contract du partner
		if self.private_key :
			acct = Account.from_key(self.private_key_value)
			self.mode.w3.eth.defaultAccount = acct.address	
			for index in range (0, len(self.partners)) :		
				contract = self.mode.w3.eth.contract(self.partners[index]['workspace_contract'],abi=constante.workspace_ABI)
				self.partners[index]['status'] = liste[contract.functions.getMyPartnershipStatus().call()]			
		else :
			print('status des partnerships impossible a obtenir, private key  not found')
		return True
	
	def topicname2topicvalue(topicname) :
		topicvalue_str =''
		for i in range(0, len(topicname))  :
			a = str(ord(topicname[i]))
			a = '0'+ a  if int(a) < 100 else a
			topicvalue_str += a
		return int(topicvalue_str)
	
		# always available
	def get_identity_personal(self,workspace_contract_from, private_key_from) :
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
			claim.get_by_topic_name(workspace_contract_from, private_key_from, self.workspace_contract, topicname, self.mode)
			self.personal[topicname] = claim.__dict__
		return True
	
	
	def get_all_documents(self) :
		self.file_list = []
		self.experience_list = []
		self.education_list = []
		self.other_list = []
		self.kbis_list = []
		self.kyc_list = []
		self.certificate_list=[]
		self.skills_list = []
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
			elif doctype == 11000 :
				self.skills_list.append(doc_id)
			else :
				self.other_list.append(doc_id)
		return
	
	def get_identity_kyc(self) :
		self.kyc = []
		#contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.kyc_list  :
			kyc = Document('kyc')
			kyc.relay_get(self.workspace_contract, doc_id, self.mode, loading='light')
			new_kyc = kyc.__dict__
			self.kyc.append(new_kyc)
		return True	
	
	
	def get_identity_certificate(self) :
		self.certificate = []
		#contract = self.mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		for doc_id in self.certificate_list  :
			certificate = Document('certificate')
			certificate.relay_get(self.workspace_contract, doc_id, self.mode, loading='light')
			new_certificate = certificate.__dict__
			self.certificate.append(new_certificate)
		return True	
	
	
	def get_identity_kbis(self) :
		self.kbis = []
		for doc_id in self.kbis_list  :
			kbis = Document('kbis')
			kbis.relay_get(self.workspace_contract, doc_id, self.mode, loading='light')
			new_kbis = kbis.__dict__
			self.kbis.append(new_kbis)
		return True	
	
	
	def get_identity_education(self) :
		self.education = []
		for doc_id in self.education_list  :
			education = Document('education')
			education.relay_get(self.workspace_contract, doc_id, self.mode, loading='light')
			new_education = education.__dict__
			self.education.append(new_education)
		return True	
		
	def get_identity_skills(self) :
		if self.skills_list  != [] :
			skills = Document('skills')
			skills.relay_get(self.workspace_contract, self.skills_list[-1], self.mode, loading='light')
			self.skills = skills.__dict__		
		else :
			self.skills = None
		return True	
		
	def get_identity_experience(self) :	
		self.experience = []
		for doc_id in self.experience_list  :
			experience = Document('experience')
			experience.relay_get(self.workspace_contract, doc_id, self.mode, loading='light')
			new_experience = experience.__dict__ 
			self.experience.append(new_experience)
		return True	
	
	def get_identity_file(self, workspace_contract_from, private_key_from) :	
		self.identity_file = []
		for doc_id in self.file_list :
			this_file = File()
			if this_file.get(workspace_contract_from, private_key_from, self.workspace_contract, doc_id, "", self.mode) :
				new_file = this_file.__dict__
				self.identity_file.append(new_file)
		print ('get identity file = ', self.identity_file)
		return True
		
	def uploadPicture(self,picturefile) :
		self.picture = savepictureProfile(self.mode.relay_address, self.mode.relay_workspace_contract, self.address, self.workspace_contract, self.mode.relay_private_key, picturefile,self.mode, synchronous = True)	
		return self.picture

	
	
