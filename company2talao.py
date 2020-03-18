import sys
import csv
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Protocol.KDF import PBKDF2
import http.client
import json
from datetime import datetime
import ipfshttpclient


# dependances
import Talao_token_transaction
import Talao_ipfs
import addclaim
import constante
import environment


# initialisation de l'environnement
mode=environment.currentMode('test', 'rinkeby')
mode.print_mode()
w3=mode.initProvider()

# variable pour calcul RSA
password = "suc2cane"
master_key = ""
salt = ""


# wallet de Talaogen
#talao_public_Key='0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b'
#talao_private_Key='0xbbfea0f9ed22445e7f5fb1c4ca780e96c73da3c74fbce9a6972c45730a855460'



def createWorkspace(address,private_key,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail,mode) :

	contract=w3.eth.contract(mode.workspacefactory_contract,abi=constante.Workspace_Factory_ABI)

	# calcul du nonce de l envoyeur de token . Ici le caller
	nonce = w3.eth.getTransactionCount(address)  

	# Build transaction
	txn=contract.functions.createWorkspace(2001,1,1,bRSAPublicKey,bAESEncryptedKey,bsecret,bemail).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 6500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)	
	return hash

##############################################
# deterministic RSA rand function variable
##############################################
# deterministic RSA rand function
def my_rand(n):
    # kluge: use PBKDF2 with count=1 and incrementing salt as deterministic PRNG
    my_rand.counter += 1
    return PBKDF2(master_key, "my_rand:%d" % my_rand.counter, dkLen=n, count=1)




############################################
# Creation d'un workspace from scratch
############################################

def creationworkspacefromscratch(email,mode): 

	# creation de la wallet	
	account = w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
	eth_a=account.address
	eth_p=account.privateKey.hex()
	print('adresse = ',eth_a)
	print('private key = ', eth_p)
	
	# création de la cle RSA (bytes) deterministic
	# https://stackoverflow.com/questions/20483504/making-rsa-keys-from-a-password-in-python
	global salt
	global master_key
	salt = eth_p
	master_key = PBKDF2(password, salt, count=10000)  # bigger count = better
	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
	RSA_private = RSA_key.exportKey('PEM')
	RSA_public = RSA_key.publickey().exportKey('PEM')

	# création de la cle RSA (bytes), des cle public et privées
	#RSA_key = RSA.generate(2048)
	#RSA_private = RSA_key.exportKey('PEM')
	#RSA_public = RSA_key.publickey().exportKey('PEM')

	# stockage de la cle privée RSA dans un fichier du repertoire ./RSA_key/rinkeby ou ethereum
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+str(eth_a)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
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
	
	# Transaction pour le transfert de 0.06 ethers depuis le portfeuille TalaoGen
	hash1=Talao_token_transaction.ether_transfer(eth_a, 60,mode)
	print('hash de transfert de 0.06 eth = ',hash1)
	
	# Transaction pour le transfert de 100 tokens Talao depuis le portfeuille TalaoGen
	hash2=Talao_token_transaction.token_transfer(eth_a,100,mode)
	print('hash de transfert de 100 TALAO = ', hash2)
	
	# Transaction pour l'acces dans le token Talao par createVaultAccess
	hash3=Talao_token_transaction.createVaultAccess(eth_a,eth_p,mode)
	print('hash du createVaultaccess = ', hash3)
	
	# Transaction pour la creation du workspace :
	bemail=bytes(email , 'utf-8')	
	hash4=createWorkspace(eth_a,eth_p,RSA_public,AES_encrypted,SECRET_encrypted,bemail,mode)
	print('hash de createWorkspace =', hash4)

	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract_address=Talao_token_transaction.ownersToContracts(eth_a,mode)
	print( 'workspace contract = ', workspace_contract_address)
		
	return eth_a, eth_p, SECRET, workspace_contract_address, email, SECRET, AES_key



##############################################################
#             MAIN
##############################################################
# tous les claims sont signe par Talao qui cré les companies

# Ouverture du fichier d'archive Talao_Identity.csv
fname= mode.BLOCKCHAIN +"_Talao_Identity.csv"
identityfile = open(fname, "a")
writer = csv.writer(identityfile)


# ouverture du fichier company au format json
filename=input("Saisissez le nom du fichier de company.json ?  ")
companyfile=open(filename, "r")
company=json.loads(companyfile.read())
	
# calcul du temps de process
time_debut=datetime.now()

# CREATION DU WORKSPACE MINIMUM
email = company['profil']["contact"]['email'] # base pour la construction du registre de nameservice
(address, private_key,password, workspace_contract, email, SECRET, AES_key)=creationworkspacefromscratch(email,mode)

# CREATION DES CLAIM DU PROFIL cf readprofile de getresume
name = company['profil']["name"]
addclaim.addClaim(workspace_contract, address,private_key, "firstname", address, name, "",mode) 
website = company["profil"]["website"]
addclaim.addClaim(workspace_contract, address,private_key, "url", address, website, "",mode) 
contact = company["profil"]["contact"]["name"]
addclaim.addClaim(workspace_contract, address,private_key, "contact", address, contact, "",mode) 
address_company = company["profil"]["address"]
addclaim.addClaim(workspace_contract, address,private_key, "address", address, address_company, "",mode) 


# initialisation du claim "auth_website" par le owner lui meme
addclaim.addClaim(workspace_contract, address,private_key, "auth_website", address, company["profil"]["website"], "",mode) 
# ajouter au registre..............ICI peut etre ?????

# AJOUT CLE 3 a Talao SAS par le owner lui meme	       
#envoyer la transaction sur le contrat
contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
# calcul du nonce de l envoyeur de token . Ici le owner
nonce = w3.eth.getTransactionCount(address)  
# calcul du keccak
_key=w3.soliditySha3(['address'], [mode.owner_talao])
# Build transaction
txn = contract.functions.addKey(_key, 3, 1).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
#sign transaction
signed_txn=w3.eth.account.signTransaction(txn,private_key)
# send transaction	
w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
w3.eth.waitForTransactionReceipt(hash1)		
print("creation de cle 3 pour Talao = ", hash1)


# MISE A JOUR DU KBIS PAR TALAO SAS
kbis={
                "name": company["kbis"]["name"],
                "activity": company["kbis"]["activity"],
                "siret": company["kbis"]["siret"],
                "address": company["kbis"]["address"],
                "capital": company["kbis"]["capital"],
                "date": company["kbis"]["date"],
                "legal_form": company["kbis"]["legal_form"],
                "managing director": company["kbis"]["managing_director"],
                "naf": company["kbis"]["naf"],
                "president": company["kbis"]["ceo"]
            }
client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
ipfshash=client.add_json(kbis)
client.pin.add(ipfshash)
address_talao=mode.owner_talao # Talao SAS
topicvalue = 107098105115 # kbis
topicname="kbis"
issuer = node.owner_talao
data =""

# calcul de la signature
msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
message = encode_defunct(text=msg.hex())
signed_message = w3.eth.account.sign_message(message, private_key=mode.foundation_private_key)
signature=signed_message['signature']	

#private_key_talao='0x26A0B235537FEF1672597067858379BEC0FFBCF557A25A719B8DC24E8FA573BE' # Talao SAS
#h=addclaim.addClaim(workspace_contract, address_talao,private_key_talao, "kbis", address_talao, "", ipfshash)

# build, sign and send avec une addresse dans le node "defaultAccount
w3.eth.defaultAccount=mode.owner_talao
hash1=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).transact({'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce})	
w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	

print("ajout du kbis par Talao SAS",h) 


# AJOUT CLE 3 A LA FONDATION (pour nameservice) par le owner
#owner_foundation = mode.owner_foundation       
#envoyer la transaction sur le contrat
contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
# calcul du nonce de l envoyeur de token . Ici le owner
nonce = w3.eth.getTransactionCount(address)  
# calcul du keccak
_key=w3.soliditySha3(['address'], [mode.owner_foundation])
# Build transaction
txn = contract.functions.addKey(_key, 3, 1).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
#sign transaction
signed_txn=w3.eth.account.signTransaction(txn,private_key)
# send transaction	
w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
hash1=w3.toHex(w3.keccak(signed_txn.rawTransaction))
w3.eth.waitForTransactionReceipt(hash1)		
print("creation de cle 3 pour la fondation = ", hash1)
        

# calcul de la duree de transaction et du cout
time_fin=datetime.now()
time_delta=time_fin-time_debut
print('Durée des transactions = ', time_delta)
a=w3.eth.getBalance(address)
cost=0.06-a/1000000000000000000	
print('Cout des transactions =', cost)	


# mise a jour du fichier archive Talao_Identity.csv
status="Compnay Identity company2talao.py"
writer.writerow(( datetime.today(),name, "", email,status,address, private_key, workspace_contract, "", email, SECRET, AES_key,cost) )

# fermeture des fichiers
identityfile.close()
sys.exit(0)
