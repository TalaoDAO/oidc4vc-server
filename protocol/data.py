"""
Object data 

"""
import json
from .GETdata import getdata
from .identity import identity 
import constante
from .Talao_token_transaction import ownersToContracts
from datetime import datetime
from .nameservice import getUsername

# TEST 
# dataId='did:talao:rinkeby:Ec0Cf3FA4158D8dd098051cfb14af7b4812d51aF:claim:e62953dae0aa57c32bf2f451d5df651b6afb0f833a679df35862f43de9ed75e0'
 
class Data() :
	
	def __init__(self, thisdata, mode):
		
		mydata = getdata(thisdata,mode)
		print(mydata)
		if mydata == False :
			print('This data does not exist')
			return None
		self.id = thisdata
		self.mode = mode
		self.type = thisdata.split(':')[4]
		if self.type == 'claim' :
			self.docId = '0x'+thisdata.split(':')[5]
		else :
			self.docId = thisdata.split(':')[5]		
		self.identity_workspace_contract = '0x' +  thisdata.split(':')[3]
		self.issuer_id = mydata['data']['issuer']['id']
		self.issuer_workspace_contract = '0x'+ self.issuer_id.split(':')[3]
		self.issuer_firstname = mydata['data']['issuer']['data']['firstname']
		self.issuer_lastname = mydata['data']['issuer']['data']['lastname']
		self.issuer_endpoint = mydata['data']['issuer']['endpoint']		
		self.issuer_name = self.issuer_firstname + ' ' + self.issuer_lastname
		self.issuer_username = getUsername(self.issuer_workspace_contract,self.mode)
		
		self.topic = mydata['data']['topic']
		self.value = mydata['data']['value']
		self.expires = mydata['data']['expires']
		self.encrypted = mydata['data']['encrypted']
		self.datalocation = mydata['data']['location']
		self.signatureType = mydata['data']['signaturetype']
		self.signature = mydata['data']['signature']
		self.signatureCheck = mydata['data']['signature_check']
		
		if self.type == 'claim' :
			contract = self.mode.w3.eth.contract(self.identity_workspace_contract,abi=constante.workspace_ABI)
			claimfilter = contract.events.ClaimAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
			eventlist = claimfilter.get_all_entries()
			for doc in eventlist :
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
			claimfilter = contract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
			eventlist = claimfilter.get_all_entries()
			for doc in eventlist :
				if doc['args']['id'] == int(self.id.split(':')[5]) :
					transactionhash = doc['transactionHash']
					self.transactionHash = transactionhash.hex()
					transaction = self.mode.w3.eth.getTransaction(transactionhash)
					blocknumber = transaction['blockNumber']
					self.blockNumber = blocknumber
					block = self.mode.w3.eth.getBlock(blocknumber)
					date = datetime.fromtimestamp(block['timestamp'])	
					self.created=date.strftime("%y/%m/%d")
					return None
		else :
			print('erreur dataId')
			return None
