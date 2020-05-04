
import json
from .GETdata import getdata
from datetime import datetime

#from .identity import Identity 
import constante
from .Talao_token_transaction import ownersToContracts
from .nameservice import getUsername

# TEST 
# dataId='did:talao:rinkeby:Ec0Cf3FA4158D8dd098051cfb14af7b4812d51aF:claim:e62953dae0aa57c32bf2f451d5df651b6afb0f833a679df35862f43de9ed75e0'
 
class Data() :
	
	def __init__(self, this_data, mode):
		
		my_data = getdata(this_data,mode)
		if not my_data :
			print('This data does not exist')
			return None
		self.id = this_data
		self.mode = mode
		self.type = this_data.split(':')[4]
		
		if self.type == 'claim' :
			self.docId = '0x'+this_data.split(':')[5]
		else :
			self.docId = this_data.split(':')[5]		
		self.identity_workspace_contract = '0x' +  this_data.split(':')[3]
		self.issuer_id = my_data['data']['issuer']['id']
		self.issuer_type = my_data['data']['issuer']['type']
		self.issuer_workspace_contract = '0x'+ self.issuer_id.split(':')[3]
		self.issuer_endpoint = my_data['data']['issuer']['endpoint']		
		self.issuer_type = my_data['data']['issuer']['type']
		
		if self.issuer_type == 'person' :			
			self.issuer_firstname = my_data['data']['issuer']['data']['firstname']
			self.issuer_lastname = my_data['data']['issuer']['data']['lastname']
			self.issuer_name = self.issuer_firstname + ' ' + self.issuer_lastname
			self.issuer_jobtitle = my_data['data']['issuer']['data']['jobtitle']
			self.issuer_description = my_data['data']['issuer']['data']['description']	
			self.issuer_url = my_data['data']['issuer']['data']['url']
			self.issuer_location = my_data['data']['issuer']['data']['location']		
		else :
			self.issuer_name = my_data['data']['issuer']['data']['name']
			self.issuer_website = my_data['data']['issuer']['data']['website']
			self.issuer_email = my_data['data']['issuer']['data']['email']
			self.issuer_contact = my_data['data']['issuer']['data']['contact']
			self.issuer_address = my_data['data']['issuer']['data']['address']		
		
		self.issuer_username = getUsername(self.issuer_workspace_contract,self.mode)
		self.topic = my_data['data']['topic']
		self.value = my_data['data']['value']
		self.expires = my_data['data']['expires']
		self.encrypted = my_data['data']['encrypted']
		self.datalocation = my_data['data']['location']
		self.signatureType = my_data['data']['signaturetype']
		self.signature = my_data['data']['signature']
		self.signatureCheck = my_data['data']['signature_check']
		
		if self.type == 'claim' :
			contract = self.mode.w3.eth.contract(self.identity_workspace_contract,abi=constante.workspace_ABI)
			claim_filter = contract.events.ClaimAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
			event_list = claim_filter.get_all_entries()
			for doc in event_list :
				if doc['args']['claimId'].hex() == self.id.split(':')[5] :
					transactionhash = doc['transactionHash']
					self.transactionHash = transactionhash.hex()
					transaction = self.mode.w3.eth.getTransaction(transactionhash)
					blocknumber = transaction['blockNumber']
					self.blockNumber = str(blocknumber)
					block = self.mode.w3.eth.getBlock(blocknumber)
					date = datetime.fromtimestamp(block['timestamp'])	
					self.created = date.strftime("%y/%m/%d")
					return None
		
		elif self.type == 'document' :
			contract = self.mode.w3.eth.contract(self.identity_workspace_contract,abi=constante.workspace_ABI)
			claim_filter = contract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
			event_list = claim_filter.get_all_entries()
			for doc in event_list :
				if doc['args']['id'] == int(self.id.split(':')[5]) :
					transactionhash = doc['transactionHash']
					self.transactionHash = transactionhash.hex()
					transaction = self.mode.w3.eth.getTransaction(transactionhash)
					blocknumber = transaction['blockNumber']
					self.blockNumber = blocknumber
					block = self.mode.w3.eth.getBlock(blocknumber)
					date = datetime.fromtimestamp(block['timestamp'])	
					self.created = date.strftime("%y/%m/%d")
					return None
		else :
			print('erreur dataId')
			return None
