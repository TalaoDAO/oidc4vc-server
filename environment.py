"""

initialisation des variables d'environnement 
initialisation du provider
construction du registre nameservice
unlock des addresses du node
check de geth

"""

from web3 import Web3
import nameservice
import json
import sys

class currentMode() :

	def __init__(self, myenv, mychain):
		
		print('debut init')
		
	
		self.env=myenv
		self.chain=mychain
		self.port = '4000'
		self.apiport = '3000'
		self.flaskserver = '127.0.0.1'
			
		if mychain == 'rinkeby' :
			self.ether2transfer=20	
			self.IPCProvider="/mnt/ssd/rinkeby/geth.ipc"
			self.w3=Web3(Web3.IPCProvider("/mnt/ssd/rinkeby/geth.ipc"))			
			self.datadir="/mnt/ssd/rinkeby" 						
			self.BLOCKCHAIN = "rinkeby"		
			self.Talao_contract_address='0xb8a0a9eE2E780281637bd93C13076cc5E342c9aE' # Talao token
			self.CHAIN_ID=4
			self.Talaogen_public_key='0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b' # talaogen, uniquement pour le tranfer d'ether et de token
			self.Talaogen_private_key='0xbbfea0f9ed22445e7f5fb1c4ca780e96c73da3c74fbce9a6972c45730a855460' #talaogen a retirer mais voir pb de send ether vs transaction sur chain POA
			self.foundation_contract='0xde4cF27d1CEfc4a6fA000a5399c59c59dA1BF253'
			self.foundation_address ='0x2aaF9517227A4De39d7cd1bb2930F13BdB89A113'
			self.workspacefactory_contract='0x22d0E5639cAEF577BEDEAD4B94D3215A6c2aC0A8'
			self.owner_talao='0xE7d045966ABf7cAdd026509fc485D1502b1843F1' # la company
			self.ISSUER='certificates.talao.io:5011'
			self.DAPP_LINK="\r\nDapp Link : http://vault.talao.io:4011/visit/"
			self.WORKSPACE_LINK='http://vault.talao.io:4011/visit/'
			self.GASPRICE='2'		
		
		elif mychain == 'ethereum' or mychain == 'mainet' :
			self.ether2transfer=20
			self.IPCProvider="/mnt/ssd/ethereum/geth.ipc"
			self.w3=Web3(Web3.IPCProvider("/mnt/ssd/ethereum/geth.ipc"))	 	
			self.datadir="/mnt/ssd/ethereum"
			self.BLOCKCHAIN = "ethereum"
			self.Talao_contract_address='0x1D4cCC31dAB6EA20f461d329a0562C1c58412515' # Talao token
			self.CHAIN_ID=1
			self.Talaogen_public_key='0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b' # talaogen, uniquement pour le tranfer d'ether et de token
			self.Talaogen_private_key=''  # pb send transaction
			self.foundation_contract='0xD46883ddfF92CC0474255F2F8134C63f8209171d'
			self.foundation_address = "0xD46883ddfF92CC0474255F2F8134C63f8209171d"
			self.workspacefactory_contract='0x7A237F06f85710b66184aFcDC55E2845F1B8f0eb'
			self.owner_talao='' # la company
			self.ISSUER='backend.talao.io'
			self.DAPP_LINK='\r\nDapp Link : https://my.freedapp.io/visit/'
			self.WORKSPACE_LINK='https://my.freedapp.io/visit/'
			self.GASPRICE='2'			
		else :
			print('error chain ->', mychain)
		
		if self.w3.isConnected()== False :
			print("Not Connected, network problem")
			sys.exit()	
		
		if myenv == 'production' or myenv == 'prod' :  # sur rasbperry
			self.IP='217.128.135.206' # external
			self.server='http://217.128.135.206:5000/' # external
					
		elif myenv == 'test' : # sur portable/internal
			#self.IP='127.0.0.1'
			self.server = 'http://127.0.0.1:4000/' #internal
			
		else : 
			print('error env ->', myenv)
		
		print('debut unlock')
		self.w3.geth.personal.unlockAccount(self.Talaogen_public_key,"suc2cane",0)
		self.w3.geth.personal.unlockAccount(self.foundation_address,"suc2cane",0)
		self.w3.geth.personal.unlockAccount(self.owner_talao,"suc2cane",0)
	
		print('upload de register.json')
		with open(self.BLOCKCHAIN+'_register.json', 'r') as myfile: 
			self.register = json.load(myfile)
			myfile.close()
		
	
		
	def print_mode(self) :		
		mymode = vars(self)
		for i in mymode.keys() :
			print(i,'-->', mymode[i])
			
	def initProvider(self) :
		return self.w3
