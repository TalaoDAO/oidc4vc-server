"""
Object data 

"""
import json
from .GETdata import getdata
from .identity import identity 
 
# TEST 
# dataId='did:talao:rinkeby:Ec0Cf3FA4158D8dd098051cfb14af7b4812d51aF:claim:e62953dae0aa57c32bf2f451d5df651b6afb0f833a679df35862f43de9ed75e0'
 
class data() :
	
	def __init__(self, dataId,mode):
		
		data=getdata(dataId,mode)
		self.dataId=dataId
		self.type=dataId.split(':')[4]
		self.issuerDid=data['data']['issuer']['id']
		self.issuerWorkspaceContract='0x'+dataId.split(':')[3]
		self.issuer=identity(self.issuerWorkspaceContract,mode)
		self.topic=data['data']['topic']
		self.expires=data['data']['expires']
		self.encrypted=data['data']['encrypted']
		self.signatureType=data['data']['signaturetype']
		self.signature=data['data']['signature']
		self.signatureCheck=data['data']['signature_check']
		self.validityCheck=data['data']['validity_check']
		
	
