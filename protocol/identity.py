"""
A la creation, si les informatiosn ne sont pas données, l instance de classe va les chercher

les signatures sont réalisée par le Relay
uniquemet utilisé en lecture.


"""

import os.path
from datetime import datetime
from operator import itemgetter, attrgetter
import random
from eth_account import Account
import os
import shutil
import json

import constante
from .Talao_token_transaction import contractsToOwners, ownersToContracts,token_balance, read_workspace_info, has_vault_access, get_category
from .claim import Claim
from .Talao_token_transaction import read_profil
from .document import Document
from .file import File
from components import ns, privatekey, Talao_ipfs

import logging
logging.basicConfig(level=logging.INFO)

class Identity() :

	def __init__(self, workspace_contract, mode, authenticated=False, workspace_contract_from = None, private_key_from = None):

		self.workspace_contract = workspace_contract
		category = get_category(self.workspace_contract, mode)
		if category  == 2001 : # company
			self.type = "company"
		if category == 1001 : # person
			self.type = "person"
		self.authenticated = authenticated
		self.did = 'did:talao:' + mode.BLOCKCHAIN + ':' + self.workspace_contract[2:]
		self.address = contractsToOwners(self.workspace_contract,mode)
		self.get_all_documents(mode)
		self.get_issuer_keys(mode)
		self.get_identity_skills(mode)
		self.get_identity_certificate(mode)
		self.has_vault_access = has_vault_access(self.address, mode)

		if self.authenticated :
			self.has_relay_private_key(mode)
			if self.private_key :
				self.get_partners(mode)
			else :
				self.partners = []

			self.has_relay_rsa_key(mode)
			if self.rsa_key :
				self.get_secret(mode) # get aes and secret keys
			else :
				self.secret = 'Encrypted'
				self.aes = 'Encrypted'
			self.eth = mode.w3.eth.getBalance(self.address)/1000000000000000000
			self.token = token_balance(self.address,mode)
			self.is_relay_activated(mode)
			self.get_identity_personal(self.workspace_contract, self.private_key_value,mode)
			self.get_identity_file(self.workspace_contract, self.private_key_value,mode)
		else :
			self.partners = []
			self.private_key = False
			self.rsa_key = False
			self.relay_activated = False
			address_from = contractsToOwners(workspace_contract_from, mode)
			private_key_from = privatekey.get_key(address_from, 'private_key', mode)
			self.get_identity_file(workspace_contract_from,private_key_from,mode)
			self.get_identity_personal(workspace_contract_from, private_key_from,mode)
		if self.type == "company" :
			self.name = self.personal['name']['claim_value']
		else : # self.type == "person" :
			self.profil_title = self.personal['profil_title']['claim_value']
			self.name = self.personal['firstname']['claim_value'] + ' ' + self.personal['lastname']['claim_value']
			self.get_identity_experience(mode)
			self.get_identity_education(mode)

		#get image/logo and signature ipfs and download files to upload folder
		#self.picture = get_image(self.workspace_contract, 'picture', mode)
		self.picture = self.personal['picture']
		if not self.picture :
			self.picture = 'QmRzXTCn5LyVpdUK9Mc5kTa3VH7qH4mqgFGaSZ3fncEFaq' if self.type == "person" else 'QmXKeAgNZhLibNjYJFHCiXFvGhqsqNV2sJCggzGxnxyhJ5'
		if not os.path.exists(mode.uploads_path + self.picture) :
			Talao_ipfs.get_picture(self.picture, mode.uploads_path + self.picture)

		#self.signature = get_image(self.workspace_contract, 'signature', mode)
		self.signature = self.personal['signature']
		if not self.signature  :
			self.signature = 'QmS9TTtjw1Fr5oHkbW8gcU7TnnmDvnFVUxYP9BF36kgV7u'
		if not os.path.exists(mode.uploads_path + self.signature) :
			Talao_ipfs.get_picture(self.signature, mode.uploads_path + self.signature)


	def get_secret(self,mode) :
		(c, self.secret, self.aes) = read_workspace_info(self.address, self.rsa_key_value, mode)


	def has_relay_private_key(self,mode) :
		self.private_key_value =  privatekey.get_key(self.address, 'private_key', mode)
		self.private_key = False if not self.private_key_value else True


	def has_relay_rsa_key(self, mode) :
		self.rsa_key_value = privatekey.get_key(self.address, 'rsa_key', mode)
		self.rsa_key = False if not self.rsa_key_value else True


	# one checks if Relay has a key 1
	def is_relay_activated(self, mode):
		contract = mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		key = mode.w3.soliditySha3(['address'], [mode.relay_address])
		if 1 in contract.functions.getKeyPurposes(key).call() :
			self.relay_activated = True
			return False
		else :
			self.relay_activated = False


	# always available
	def get_management_keys(self, mode) :
		contract = mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(1).call()
		#mymanagementkeys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			if key[2] == mode.relay_publickeyhex :
				self.web_relay_activated = True


	# always available
	def get_issuer_keys(self, mode) :
		contract = mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		keylist = contract.functions.getKeysByPurpose(20002).call()
		self.issuer_keys = []
		for i in keylist :
			key = contract.functions.getKey(i).call()
			issuer = ns.get_data_from_publickey('0x' +key[2].hex(), mode) # most important part of the function.....see what it implies !
			if issuer :
				self.issuer_keys.append({"address": issuer['address'],
									"publickey": key[2].hex(),
									"workspace_contract" : issuer['workspace_contract'],
									'username' : issuer['username'] } )


	# Need web_relay_authorized = True (key 20003) and need private_key to get other partie status
	def get_partners(self,mode) :
		# on obtient la liste des partners avec le Relay qui a une cle 1
		self.partners = []
		acct = Account.from_key(mode.relay_private_key)
		mode.w3.eth.defaultAccount = acct.address
		contract = mode.w3.eth.contract(self.workspace_contract,abi=constante.workspace_ABI)
		try :
			partners_list = contract.functions.getKnownPartnershipsContracts().call()
		except :
			return False
		liste = ["Unknown","Authorized", "Pending","Rejected","Removed",]
		for partner_workspace_contract in partners_list :
			try :
				authorization_index = contract.functions.getPartnership(partner_workspace_contract).call()[1]
			except Exception as ex:
				logging.warning(ex)
				return False
			partner_username = ns.get_username_from_resolver(partner_workspace_contract, mode)
			if authorization_index != 4 and partner_username : # only if not "Removed" and parner is known in the database
				partner_address = contractsToOwners(partner_workspace_contract, mode)
				partner_publickey = mode.w3.soliditySha3(['address'], [partner_address])
				self.partners.append({'address': partner_address,
								'publickey': partner_publickey,
								'workspace_contract' : partner_workspace_contract,
								'username' : partner_username,
								'authorized' : liste[authorization_index],
								'status' : 'Not available'})
		# on met a jour le status avec un acces par le owner au partnership  dans le contract du partner
		if self.private_key :
			acct = Account.from_key(self.private_key_value)
			mode.w3.eth.defaultAccount = acct.address
			for index in range (0, len(self.partners)) :
				contract = mode.w3.eth.contract(self.partners[index]['workspace_contract'],abi=constante.workspace_ABI)
				self.partners[index]['status'] = liste[contract.functions.getMyPartnershipStatus().call()]
		else :
			logging.warning('status des partnerships impossible a obtenir, private key  not found')
		return True


	def get_identity_personal(self,workspace_contract_from, private_key_from, mode) :
		try :
			self.personal = json.loads(ns.get_personal(self.workspace_contract, mode))
		except :
			if self.type == 'person' :
				filename = mode.db_path + 'person.json'
			else :
				filename = mode.db_path + 'company.json'
			self.personal = json.load(open(filename, 'r'))
			ns.update_personal(self.workspace_contract, json.dumps(self.personal), mode)


	def get_all_documents(self, mode) :
		self.file_list = []
		self.experience_list = []
		self.education_list = []
		self.other_list = []
		self.certificate_list=[]
		self.skills_list = []
		contract = mode.w3.eth.contract(self.workspace_contract,abi = constante.workspace_ABI)
		try :
			doc_list =  contract.functions.getDocuments().call()
		except :
			logging.warning('getDocuments.call is not available yet in identity 243')
			return False
		for doc_id in doc_list :
			doctype = contract.functions.getDocument(doc_id).call()[0]
			if doctype in [30000, 30001, 30002] :
				self.file_list.append(doc_id)
			elif doctype in [50000, 50001, 50002] :
				self.experience_list.append(doc_id)
			elif doctype in [40000, 40001, 40002] :
				self.education_list.append(doc_id)
			elif doctype in [20000] :
				self.certificate_list.append(doc_id)
			elif doctype == 11000 :
				self.skills_list.append(doc_id)
			else :
				self.other_list.append(doc_id)
		return True

	def get_identity_certificate(self,mode) :
		self.certificate = []
		for doc_id in self.certificate_list  :
			certificate = Document('certificate')
			certificate.relay_get(self.workspace_contract, doc_id, mode)
			new_certificate = certificate.__dict__
			self.certificate.append(new_certificate)
		return True

	def get_identity_education(self,mode) :
		self.education = []
		for doc_id in self.education_list  :
			education = Document('education')
			education.relay_get(self.workspace_contract, doc_id, mode, loading='light')
			new_education = education.__dict__
			self.education.append(new_education)
		return True

	def get_identity_skills(self,mode) :
		if self.skills_list  != [] :
			skills = Document('skills')
			skills.relay_get(self.workspace_contract, self.skills_list[-1], mode, loading='light')
			self.skills = skills.__dict__
		else :
			self.skills = None
		return True

	def get_identity_experience(self,mode) :
		self.experience = []
		for doc_id in self.experience_list  :
			experience = Document('experience')
			experience.relay_get(self.workspace_contract, doc_id, mode, loading='light')
			new_experience = experience.__dict__
			self.experience.append(new_experience)
		return True

	def get_identity_file(self, workspace_contract_from, private_key_from, mode) :
		self.identity_file = []
		for doc_id in self.file_list :
			this_file = File()
			if this_file.get(workspace_contract_from, private_key_from, self.workspace_contract, doc_id, "", mode) :
				new_file = this_file.__dict__
				self.identity_file.append(new_file)
		return True