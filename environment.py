"""

initialisation des variables d'environnement 
initialisation du provider
construction du registre nameservice
unlock des addresses du node
check de geth

"""
from web3.middleware import geth_poa_middleware
from web3 import Web3
import json
import sys

# test(avec acces smartphone) ou airbox(pour wireless) ou prod ou aws



class currentMode() :
	
	def __init__(self, mychain='talaonet', myenv='aws'):
		
		self.admin = 'thierry.thevenet@talao.io'
		self.test = True
		self.myenv = myenv
		self.password = 'suc2cane'
		self.BLOCKCHAIN = mychain

		if self.BLOCKCHAIN == 'talaonet' and self.myenv == 'aws ':
			self.db_path = '/home/admin/db/talaonet/'
			self.IPCProvider = '/home/admin/Talaonet/node2/geth.ipc'
			self.w3 = Web3(Web3.IPCProvider("/home/admin/Talaonet/node2/geth.ipc", timeout=20))
			self.uploads_path = '/home/admin/Talao/uploads/'
			self.IP = '18.190.21.227' # external talao.co
			self.server = 'http://talao.co:6000/' # external
			#self.port = 4000
			#self.flaskserver = "127.0.0.1"
			self.debug = False	

		if self.BLOCKCHAIN == 'talaonet' and self.myenv == 'airbox' :
			self.db_path = '/home/thierry/db/talaonet/'
			self.IPCProvider = '/mnt/ssd/talaonet/geth.ipc"'
			self.w3 = Web3(Web3.IPCProvider('/mnt/ssd/talaonet/geth.ipc', timeout=20))
			self.uploads_path = '/home/thierry/Talao/uploads/'				
			self.server = 'http://127.0.0.1:3000/' # external
			self.flaskserver = "127.0.0.1"
			self.port = 3000
			self.debug = True

		if self.BLOCKCHAIN == 'talaonet' and self.myenv == 'livebox' :
			self.db_path = '/home/thierry/db/talaonet/'
			self.IPCProvider = '/mnt/ssd/talaonet/geth.ipc"'
			self.w3 = Web3(Web3.IPCProvider('/mnt/ssd/talaonet/geth.ipc', timeout=20))
			self.uploads_path = '/home/thierry/Talao/uploads/'				
			self.server = 'http://192.168.0.6:3000/' 
			self.flaskserver = "192.168.0.6"
			self.port = 3000
			self.debug = True

		if self.BLOCKCHAIN == 'rinkeby' and self.myenv == 'aws':	
			self.db_path = '/home/admin/db/rinkeby/'
			self.w3 = Web3(Web3.IPCProvider('/home/admin/rinkeby/geth.ipc', timeout=20))
			self.IPCProvider = '/home/admin/rinkeby/geth.ipc'
			self.uploads_path = '/home/admin/Talao/uploads/'
			self.IP = '18.190.21.227' # external talao.co
			self.server = 'http://talao.co:5000/' # external
			#self.port = 4000
			#self.flaskserver = "127.0.0.1"
			self.debug = False	

		# sur PC portable thierry avec acces internet par reseau (pour les test depuis un smartphone)
		if self.BLOCKCHAIN == 'rinkeby' and self.myenv == 'livebox' :		
			self.db_path = '/home/thierry/db/rinkeby/'
			self.IPCProvider = "/mnt/ssd/rinkeby/geth.ipc"
			self.w3 = Web3(Web3.IPCProvider("/mnt/ssd/rinkeby/geth.ipc", timeout=20))	
			self.uploads_path = '/home/thierry/Talao/uploads/'				
			self.server = 'http://192.168.0.6:3000/' 
			self.flaskserver = "192.168.0.6"
			self.port = 3000
			self.debug = True

		# sur PC portable thierry connecté avec airbox
		if self.BLOCKCHAIN == 'rinkeby' and self.myenv == 'airbox' :		
			self.db_path = '/home/thierry/db/rinkeby/'
			self.IPCProvider = "/mnt/ssd/rinkeby/geth.ipc"
			self.w3 = Web3(Web3.IPCProvider("/mnt/ssd/rinkeby/geth.ipc", timeout=20))	
			self.uploads_path = '/home/thierry/Talao/uploads/'				
			self.server = 'http://127.0.0.1:3000/' # external
			self.flaskserver = "127.0.0.1"
			self.port = 3000
			self.debug = True
		
		if self.BLOCKCHAIN == 'rinkeby' :
			self.start_block = 6400000
			self.ether2transfer = 40	
			self.talao_to_transfer = 101
			self.talao_bonus = 10
			self.fromBlock= 5800000
			self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
			self.BLOCKCHAIN = "rinkeby"		
			self.Talao_token_contract = '0xb8a0a9eE2E780281637bd93C13076cc5E342c9aE' # Talao token
			self.CHAIN_ID = 4
			# Talaogen  
			self.Talaogen_public_key = '0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b' # talaogen, uniquement pour le tranfer d'ether et de token
			self.Talaogen_private_key = '0xbbfea0f9ed22445e7f5fb1c4ca780e96c73da3c74fbce9a6972c45730a855460' #talaogen a retirer mais voir pb de send ether vs transaction sur chain POA
			# Foundation and factory """
			self.foundation_contract = '0xde4cF27d1CEfc4a6fA000a5399c59c59dA1BF253'
			self.foundation_address ='0x2aaF9517227A4De39d7cd1bb2930F13BdB89A113'
			self.workspacefactory_contract = '0x22d0E5639cAEF577BEDEAD4B94D3215A6c2aC0A8'
			# Web Relay 
			self.relay_address = '0x18bD40F878927E74a807969Af2e3045170669c71'
			self.relay_workspace_contract = '0xD6679Be1FeDD66e9313b9358D89E521325e37683'
			self.relay_private_key = '0xc5381961fcd24555420d511c758804ef8b71e63b72d3dc98f8a8e285881796f9'
			self.relay_publickeyhex = self.w3.soliditySha3(['address'], [self.relay_address])			
			# Talao company
			self.owner_talao='0xE7d045966ABf7cAdd026509fc485D1502b1843F1' # la company
			self.owner_talao_private_key='0x26A0B235537FEF1672597067858379BEC0FFBCF557A25A719B8DC24E8FA573BE'
			self.workspace_contract_talao='0xfafDe7ae75c25d32ec064B804F9D83F24aB14341'
			self.ISSUER ='certificates.talao.io:5011'
			#self.DAPP_LINK="\r\nDapp Link : http://vault.talao.io:4011/visit/"
			#self.WORKSPACE_LINK = 'http://vault.talao.io:4011/visit/'
			self.GASPRICE='2'		
		
		if self.BLOCKCHAIN == 'talaonet' :
			self.start_block = 10000
			self.ether2transfer = 1	
			self.talao_to_transfer = 101
			self.talao_bonus = 10
			self.fromBlock= 1000
			self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
			self.Talao_token_contract = '0x6F4148395c94a455dc224A56A6623dEC2395b99B' # Talao token
			self.CHAIN_ID = 50000
			# Talaogen  
			self.Talaogen_public_key = '0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b' # talaogen, uniquement pour le tranfer d'ether et de token
			self.Talaogen_private_key = '0xbbfea0f9ed22445e7f5fb1c4ca780e96c73da3c74fbce9a6972c45730a855460' #talaogen a retirer mais voir pb de send ether vs transaction sur chain POA
			# Foundation and factory 
			self.foundation_contract = '0xb4C784Bda6A994f9879b791Ee2A243Aa47fDabb6'
			self.foundation_address ='0xDA1d3332A17A8C4B8fef4BE1F7b9DD578C83B322'
			self.workspacefactory_contract = '0x0969E4E66f47D543a9Debb7b0B1F2928f1F50AAf'
			# Web Relay 
			self.relay_address = '0x5f736A4A69Cc9A6F859be788A9f59483A2219d1C'
			self.relay_workspace_contract = '0xAe3D8c93Caf52AB09c74463A1358c0121C8C61e3'
			self.relay_private_key = '0xef24aa43533337b9b525f5258688227a80ae4029bbf2905a55690031b4970102'
			self.relay_publickeyhex = self.w3.soliditySha3(['address'], [self.relay_address])			
			# Talao company
			self.owner_talao='0xEE09654eEdaA79429F8D216fa51a129db0f72250' # la company
			self.owner_talao_private_key='0xf0f38e326b3415e4ba7e620dee7797ecf44e8ccac513d736ab82f9f11d22557a'
			self.workspace_contract_talao='0x4562DB03D8b84C5B10FfCDBa6a7A509FF0Cdcc68'
			self.ISSUER='certificates.talao.io:5011'
			#self.DAPP_LINK="\r\nDapp Link : http://vault.talao.io:4011/visit/"
			#self.WORKSPACE_LINK='http://vault.talao.io:4011/visit/'
			self.GASPRICE='1'		

		elif self.BLOCKCHAIN == 'ethereum'  :
			self.ether2transfer = 20
			self.talao_to_transfer = 101
			self.talao_bonus = 10
			self.start_block = 0
			self.fromBlock= 5800000
			self.IPCProvider="/mnt/ssd/ethereum/geth.ipc"
			self.w3=Web3(Web3.IPCProvider("/mnt/ssd/ethereum/geth.ipc"))	 				
			self.Talao_token_contract='0x1D4cCC31dAB6EA20f461d329a0562C1c58412515' # Talao token
			self.CHAIN_ID = 1
			# Talaogen 
			self.Talaogen_public_key='0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b' # talaogen, uniquement pour le tranfer d'ether et de token
			self.Talaogen_private_key=''  # pb send transaction
			#  Foundation et factory """
			self.foundation_contract='0xD46883ddfF92CC0474255F2F8134C63f8209171d'
			self.foundation_address = "0xD46883ddfF92CC0474255F2F8134C63f8209171d"
			self.workspacefactory_contract='0x7A237F06f85710b66184aFcDC55E2845F1B8f0eb'
			#  Web Relay 
			self.relay_address = ""
			self.relay_workspace_contract = ""
			self.relay_private_key = ''
			self.relay_publickeyhex = self.w3.soliditySha3(['address'], [self.relay_address])			
			# Talao company 
			self.owner_talao = '' # la company
			self.workspace_contract_talao = ''
			self.ISSUER = 'backend.talao.io'
			self.DAPP_LINK = '\r\nDapp Link : https://my.freedapp.io/visit/'
			self.WORKSPACE_LINK = 'https://my.freedapp.io/visit/'
			self.GASPRICE = '2'			
	
		if self.w3.isConnected()== False :
			print('Not Connected, network problem')
			sys.exit()	
		else :
			print('Connected to Blockchain')
		
		self.w3.geth.personal.unlockAccount(self.Talaogen_public_key,self.password,0)
		self.w3.geth.personal.unlockAccount(self.foundation_address,self.password,0)
		#self.w3.geth.personal.unlockAccount(self.owner_talao,self.password,0)
		self.w3.geth.personal.unlockAccount(self.relay_address,self.password,0) 
		# faire >>>personal.importRawKey(relay, "suc2cane") avec address sans '0x'
	
	
