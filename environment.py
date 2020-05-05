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

class currentMode() :
	
	myenv='test'
	mychain='rinkeby'
	password='suc2cane'
	port = '4000'
	apiport = '3000'
	flaskserver = '127.0.0.1'
		
	def __init__(self):
			
		print('debut init')			
		if self.mychain == 'rinkeby' :
			
			
			self.ether2transfer=40	
			
			""" provider """
			self.IPCProvider="/mnt/ssd/rinkeby/geth.ipc"
			self.w3=Web3(Web3.IPCProvider("/mnt/ssd/rinkeby/geth.ipc"))				
			# gestion des extra bytes POA
			self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
		
			self.datadir="/mnt/ssd/rinkeby" 						
			self.BLOCKCHAIN = "rinkeby"		
			self.Talao_token_contract='0xb8a0a9eE2E780281637bd93C13076cc5E342c9aE' # Talao token
			self.CHAIN_ID=4
			# Talaogen  
			self.Talaogen_public_key='0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b' # talaogen, uniquement pour le tranfer d'ether et de token
			self.Talaogen_private_key='0xbbfea0f9ed22445e7f5fb1c4ca780e96c73da3c74fbce9a6972c45730a855460' #talaogen a retirer mais voir pb de send ether vs transaction sur chain POA
			# Foundation and factory """
			self.foundation_contract='0xde4cF27d1CEfc4a6fA000a5399c59c59dA1BF253'
			self.foundation_address ='0x2aaF9517227A4De39d7cd1bb2930F13BdB89A113'
			self.workspacefactory_contract='0x22d0E5639cAEF577BEDEAD4B94D3215A6c2aC0A8'
			# Web Relay 
			self.relay_address = '0x18bD40F878927E74a807969Af2e3045170669c71'
			self.relay_workspace_contract = '0xD6679Be1FeDD66e9313b9358D89E521325e37683'
			self.relay_private_key = '0xc5381961fcd24555420d511c758804ef8b71e63b72d3dc98f8a8e285881796f9'
			# Talao company
			self.owner_talao='0xE7d045966ABf7cAdd026509fc485D1502b1843F1' # la company
			self.owner_talao_private_key='0x26A0B235537FEF1672597067858379BEC0FFBCF557A25A719B8DC24E8FA573BE'
			self.workspace_contract_talao='0xfafDe7ae75c25d32ec064B804F9D83F24aB14341'
			self.ISSUER='certificates.talao.io:5011'
			self.DAPP_LINK="\r\nDapp Link : http://vault.talao.io:4011/visit/"
			self.WORKSPACE_LINK='http://vault.talao.io:4011/visit/'
			self.GASPRICE='2'		
		
		elif self.mychain == 'ethereum' or self.mychain == 'mainet' :
			self.ether2transfer=20
			self.IPCProvider="/mnt/ssd/ethereum/geth.ipc"
			self.w3=Web3(Web3.IPCProvider("/mnt/ssd/ethereum/geth.ipc"))	 	
			self.datadir="/mnt/ssd/ethereum"
			self.BLOCKCHAIN = "ethereum"
			self.Talao_token_contract='0x1D4cCC31dAB6EA20f461d329a0562C1c58412515' # Talao token
			self.CHAIN_ID=1
			""" Talaogen """
			self.Talaogen_public_key='0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b' # talaogen, uniquement pour le tranfer d'ether et de token
			self.Talaogen_private_key=''  # pb send transaction
			"""  fondation et factory """
			self.foundation_contract='0xD46883ddfF92CC0474255F2F8134C63f8209171d'
			self.foundation_address = "0xD46883ddfF92CC0474255F2F8134C63f8209171d"
			self.workspacefactory_contract='0x7A237F06f85710b66184aFcDC55E2845F1B8f0eb'
			"""  Web Relay """
			self.relay_address = ""
			self.relay_workspace_contract = ""
			self.relay_private_key = ''
			""" company Talao """
			self.owner_talao='' # la company
			self.workspace_contract_talao=''
			self.ISSUER='backend.talao.io'
			self.DAPP_LINK='\r\nDapp Link : https://my.freedapp.io/visit/'
			self.WORKSPACE_LINK='https://my.freedapp.io/visit/'
			self.GASPRICE='2'			
		else :
			print('error chain ->', self.mychain)
		
		if self.w3.isConnected()== False :
			print("Not Connected, network problem")
			sys.exit()	
		
		if self.myenv == 'production' or self.myenv == 'prod' :  # sur rasbperry
			self.IP='217.128.135.206' # external
			self.server='http://217.128.135.206:5000/' # external
					
		elif self.myenv == 'test' : # sur portable/internal
			#self.IP='127.0.0.1'
			self.server = 'http://127.0.0.1:4000/' #internal
			
		else : 
			print('error env ->', self.myenv)
		
		print('debut unlock')
		self.w3.geth.personal.unlockAccount(self.Talaogen_public_key,self.password,0)
		self.w3.geth.personal.unlockAccount(self.foundation_address,self.password,0)
		#self.w3.geth.personal.unlockAccount(self.owner_talao,self.password,0)
		self.w3.geth.personal.unlockAccount(self.relay_address,self.password,0) # faire >>>personal.importRawKey(relay, "suc2cane") avec address sans '0x'
	
		lecture = True		
		try :
			myfile = open(self.BLOCKCHAIN+'_register.json', 'r') 
		except :
			print('erreur de lecture du fichier register')
			lecture = False
		try :
			self.register = json.load(myfile)
		except :	
			print('contenu du fichier register erroné')
			lecture = False
		if lecture != False :
			print('upload de register.json')
			myfile.close()	

			
	def initProvider(self) :
		return self.w3
