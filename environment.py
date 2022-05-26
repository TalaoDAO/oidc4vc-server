"""
initialisation des variables d'environnement
upload du fichier des private key de Talao, Relay et Talaogen
initialisation du provider
construction du registre nameservice
unlock des addresses du node
check de geth
"""

from web3.middleware import geth_poa_middleware
from web3 import Web3
import json
import sys
import logging
import socket

logging.basicConfig(level=logging.INFO)


class currentMode() :

	def __init__(self, mychain, myenv):
		# mychain, myenv --> environment variables set in gunicornconf.py or manually if main.py is launched without Gunicorn
		self.admin = 'thierry.thevenet@talao.io'
		self.test = True
		self.myenv = myenv
		self.BLOCKCHAIN = 'talaonet' #mychain
		self.flaskserver = "127.0.0.1" # default value to avoid pb with aws
		self.port = 4000 #default value to avoid pb with aws
		self.talao_to_transfer = 101  # Vault deposit see Token Talao
		self.ether2transfer = 40	# Init user wallet -> 40/1000 eth
		self.ipfs_gateway = 'https://talao.mypinata.cloud/ipfs/'

		# upload of main private keys. This file (keys.json) is not in the  github repo. Ask admin to get it !!!!!
		try :
			keys = json.load(open('./keys.json'))
		except :
			logging.error('open keys.json file problem')
			sys.exit()
		self.aes_public_key = keys['aes_public_key']
		self.relay_private_key = keys['relay_private_key']
		self.Talaogen_private_key = keys['talaogen_private_key']
		self.owner_talao_private_key = keys['talao_private_key']
		self.foundation_private_key = keys['foundation_private_key']
		self.talao_P256_private_key = keys['talao_P256_private_key']
		self.talao_Ed25519_private_key = keys['talao_Ed25519_private_key']

		# upload of main private passwords. This file (passwords.json) is not in the  github repo.
		try :
			passwords = json.load(open('./passwords.json'))
		except :
			logging.error('open passwords.json file problem')
			sys.exit()
		self.password = passwords['password']
		self.passbase = passwords['passbase']
		self.smtp_password = passwords['smtp_password'] # used in smtp.py
		self.pinata_api_key = passwords['pinata_api_key'] # used in Talao_ipfs.py
		self.pinata_secret_api_key = passwords['pinata_secret_api_key'] # used in Talao_ipfs.py
		self.sms_token = passwords['sms_token'] # used in sms.py
		self.github = passwords['github'] # used for test credeible
		self.deeplink = 'https://app.talao.co/'	
		self.altme_deeplink = 'https://app.altme.io/'		
		if self.myenv == 'aws':
			self.sys_path = '/home/admin'
		else :
			self.sys_path = '/home/thierry'

		self.keystore_path = self.sys_path + '/Talao/keystore/'
		self.Ed25519_path = self.sys_path + '/Talao/keystore_Ed25519/'
		self.P256_path = self.sys_path + '/Talao/keystore_P256/'
		self.db_path = self.sys_path + '/db/talaonet/'
		self.help_path = self.sys_path + '/Talao/templates/'
		self.uploads_path = self.sys_path + '/Talao/uploads/'
		self.verifiable_credentials = self.sys_path + '/Talao/verifiable_credentials/'

		# En Prod chez AWS avec Talaonet
		if self.myenv == 'aws':
			self.server = 'https://talao.co/'
			self.IPCProvider = '/home/admin/Talaonet/node1/geth.ipc'
			self.w3 = Web3(Web3.IPCProvider("/home/admin/Talaonet/node1/geth.ipc", timeout=20))
			self.IP = '18.190.21.227' # talao.co
	
		elif self.myenv == 'local' :
			self.w3 = Web3(Web3.HTTPProvider("https://talao.co/rpc"))
			self.flaskserver = extract_ip()
			self.IP = extract_ip()
			self.server = 'http://' + self.flaskserver + ':3000/'
			self.port = 3000

		else :
			logging.error('environment variable problem')

		self.start_block = 10000
		self.GASPRICE='5'
		self.fromBlock= 1000
		self.CHAIN_ID = 50000
		# POA middleware
		self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
		# Token
		self.Talao_token_contract = '0x6F4148395c94a455dc224A56A6623dEC2395b99B'
		# Talaogen
		self.Talaogen_public_key = '0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b'
		# Foundation and factory
		self.foundation_contract = '0xb4C784Bda6A994f9879b791Ee2A243Aa47fDabb6'
		self.foundation_address ='0xDA1d3332A17A8C4B8fef4BE1F7b9DD578C83B322'
		self.workspacefactory_contract = '0x0969E4E66f47D543a9Debb7b0B1F2928f1F50AAf'
		# Web Relay
		self.relay_address = '0x5f736A4A69Cc9A6F859be788A9f59483A2219d1C'
		self.relay_workspace_contract = '0xAe3D8c93Caf52AB09c74463A1358c0121C8C61e3'
		#self.relay_publickeyhex = self.w3.soliditySha3(['address'], [self.relay_address])
		# Talao company
		self.owner_talao = '0xEE09654eEdaA79429F8D216fa51a129db0f72250'
		self.workspace_contract_talao = '0x4562DB03D8b84C5B10FfCDBa6a7A509FF0Cdcc68'

		if not self.w3.isConnected() :
			logging.error('not Connected, network problem')
			sys.exit()
		else :
			logging.info('connected to %s', self.BLOCKCHAIN)

		""" unlock main account for IPC node only
		Faire >>>personal.importRawKey(relay, "password") avec address sans '0x' et correct password
		 """
		if self.myenv == 'aws':
			self.w3.geth.personal.unlockAccount(self.Talaogen_public_key,self.password,0)
			self.w3.geth.personal.unlockAccount(self.relay_address,self.password,0)

def extract_ip():
    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:       
        st.connect(('10.255.255.255', 1))
        IP = st.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        st.close()
    return IP