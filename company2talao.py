import sys
import csv
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import http.client
import json
from datetime import datetime

# import des fonctions custom
import Talao_token_transaction
import Talao_ipfs

from web3 import Web3
my_provider = Web3.IPCProvider('/home/thierry/.ethereum/rinkeby/geth.ipc')
w3 = Web3(my_provider)

import constante

# wallet de Talaogen
talao_public_Key='0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b'
talao_private_Key='0xbbfea0f9ed22445e7f5fb1c4ca780e96c73da3c74fbce9a6972c45730a855460'


owner_foundation = '0x2aaF9517227A4De39d7cd1bb2930F13BdB89A113'
owner_talao = '0xE7d045966ABf7cAdd026509fc485D1502b1843F1'

############################################################

# solidity function createWorkspace (
#        uint16 _category,
#        uint16 _asymetricEncryptionAlgorithm,
#        uint16 _symetricEncryptionAlgorithm,
#        bytes _asymetricEncryptionPublicKey,
#        bytes _symetricEncryptionEncryptedKey,
#        bytes _encryptedSecret,
#        bytes _email

def createWorkspace(address,private_key,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail) :

	contract=w3.eth.contract(constante.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)

	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(address)  

	# Build transaction
	txn=contract.functions.createWorkspace(2001,1,1,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail).buildTransaction({'chainId': constante.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(constante.GASPRICE, 'gwei'),'nonce': nonce,})
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)	
	return hash


############################################
# Creation d'un workspace from scratch
############################################

def creationworkspacefromscratch(email): 

	# creation de la wallet	
	account = w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
	eth_a=account.address
	eth_p=account.privateKey.hex()
	print('adresse = ',eth_a)
	print('private key = ', eth_p)
	
	# création de la cle RSA (bytes), des cle public et privées
	RSA_key = RSA.generate(2048)
	RSA_private = RSA_key.exportKey('PEM')
	RSA_public = RSA_key.publickey().exportKey('PEM')

	# stockage de la cle privée RSA dans un fichier du repertoire ./RSA_key/rinkeby ou ethereum
	filename = "./RSA_key/"+constante.BLOCKCHAIN+'/'+str(eth_a)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	fichier=open(filename,"wb")
	fichier.write(RSA_private)
	fichier.close()   

	# création de la cle AES
	AES_key = get_random_bytes(16)	

	# création du Secret
	SECRET_key = get_random_bytes(16)
	SECRET=SECRET_key.hex()
	print('SECRET = ', SECRET)
	
	# encryption de la cle AES avec la cle RSA
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted=cipher_rsa.encrypt(AES_key)
	
	# encryption du SECRET avec la cle RSA 
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted=cipher_rsa.encrypt(SECRET_key)
	
	# Transaction pour le transfert de 0.04 ethers depuis le portfeuille TalaoGen
	hash1=Talao_token_transaction.ether_transfer(eth_a, 40)
	print('hash de transfert de 0.04 eth = ',hash1)
	
	# Transaction pour le transfert de 100 tokens Talao depuis le portfeuille TalaoGen
	hash2=Talao_token_transaction.token_transfer(eth_a,100)
	print('hash de transfert de 100 TALAO = ', hash2)
	
	# Transaction pour l'acces dans le token Talao par createVaultAccess
	hash3=Talao_token_transaction.createVaultAccess(eth_a,eth_p)
	print('hash du createVaultaccess = ', hash3)
	
	# Transaction pour la creation du workspace :
	bemail=bytes(email , 'utf-8')	
	hash4=createWorkspace(eth_a,eth_p,RSA_public,AES_encrypted,SECRET_encrypted,bemail)
	print('hash de createWorkspace =', hash4)

	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract_address=Talao_token_transaction.ownersToContracts(eth_a)
	print( 'workspace contract = ', workspace_contract_address)
		
	return eth_a, eth_p, SECRET, workspace_contract_address, email, SECRET, AES_key



##############################################################
#             MAIN
##############################################################
# tous les claims sont signe par le controller (owner) -> self claim

# Ouverture du fichier d'archive Talao_Identity.csv
fname= constante.BLOCKCHAIN +"_Talao_Identity.csv"
identityfile = open(fname, "a")
writer = csv.writer(identityfile)

# ouverture du fichier company au format json
filename=input("Saisissez le nom du fichier de company.json ?")
companyfile=open(filename, "r")
company=json.loads(companyfile.read())
	
# calcul du temps de process
time_debut=datetime.now()

# CREATION DU WORKSPACE
name = company['profil']["name"]
firstname = ""
email = company['profil']["contact"]['email']


(address, private_key,password, workspace_contract, email, SECRET, AES_key)=creationworkspacefromscratch(email)


#ajout d'un cle 3 a la fondation
owner_foundation = '0x2aaF9517227A4De39d7cd1bb2930F13BdB89A113'	       
#envoyer la transaction sur le contrat
contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
# calcul du nonce de l envoyeur de token . Ici le owner
nonce = w3.eth.getTransactionCount(address)  
# calcul du keccak
_key=w3.soliditySha3(['address'], [owner_foundation])
# Build transaction
txn = contract.functions.addKey(_key, 3, 1).buildTransaction({'chainId': constante.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(constante.GASPRICE, 'gwei'),'nonce': nonce,})
#sign transaction
signed_txn=w3.eth.account.signTransaction(txn,private_key)
# send transaction	
w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
w3.eth.waitForTransactionReceipt(hash1)		
print("creation de cle 3 pour la fondation = ", hash1)


#ajout d'un cle 3 a la Talao	       
#envoyer la transaction sur le contrat
contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
# calcul du nonce de l envoyeur de token . Ici le owner
nonce = w3.eth.getTransactionCount(address)  
# calcul du keccak
_key=w3.soliditySha3(['address'], [owner_talao])
# Build transaction
txn = contract.functions.addKey(_key, 3, 1).buildTransaction({'chainId': constante.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(constante.GASPRICE, 'gwei'),'nonce': nonce,})
#sign transaction
signed_txn=w3.eth.account.signTransaction(txn,private_key)
# send transaction	
w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
w3.eth.waitForTransactionReceipt(hash1)		
print("creation de cle 3 pour Talao = ", hash1)
        

# calcul de la duree de transaction et du cout
time_fin=datetime.now()
time_delta=time_fin-time_debut
print('Durée des transactions = ', time_delta)
a=w3.eth.getBalance(address)
cost=0.04-a/1000000000000000000	
print('Cout des transactions =', cost)	


# mise a jour du fichier archive Talao_Identity.csv
status="Identité créée par resume2talao"
writer.writerow(( datetime.today(),name, firstname, email,status,address, private_key, workspace_contract, "NON", email, SECRET, AES_key,cost) )


# fermeture des fichiers
resumefile.close()
identityfile.close()
sys.exit(0)
