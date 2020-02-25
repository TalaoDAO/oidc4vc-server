#
#
#                Generateur Talao
#
#
# Debian version  10.2
# python 3.7
# web3.py au 31-12-2019
# pycryptodome 3.9.4
# 	
#
# 6 400 000 gas pour la creation d un workspace complet

# import des fonctions generiques
import sys
import csv
#import random
from web3.auto import w3
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import http.client
import json
from datetime import datetime
from Crypto.Protocol.KDF import PBKDF2

# import des fonctions custom
import Talao_token_transaction
import Talao_backend_transaction
import Talao_message
import Talao_ipfs

# import des constantes de l environnement
import constante

# wallet de Talaogen
talao_public_Key='0x84235B2c2475EC26063e87FeCFF3D69fb56BDE9b'
talao_private_Key='0xbbfea0f9ed22445e7f5fb1c4ca780e96c73da3c74fbce9a6972c45730a855460'

#owner du Talao issuer pour la certification rinkeby
# Talao_issuer='0xE7d045966ABf7cAdd026509fc485D1502b1843F1'

# Ouverture du fichier d'archive Talao_Identity.csv
fname= constante.BLOCKCHAIN +"_Talao_Identity.csv"
file = open(fname, "a")
writer = csv.writer(file)



###################################################################
#		EXIT
###################################################################
def option4(): 
	print("Sortie sur option 4 du menu")	
	return

###################################################################
# information sur une identité
# 		0 identityInformation.creator = msg.sender;
#       1 identityInformation.category = _category;
#       2 identityInformation.asymetricEncryptionAlgorithm = _asymetricEncryptionAlgorithm;
#       3 identityInformation.symetricEncryptionAlgorithm = _symetricEncryptionAlgorithm;
#       4 identityInformation.asymetricEncryptionPublicKey = _asymetricEncryptionPublicKey;
#       5 identityInformation.symetricEncryptionEncryptedKey = _symetricEncryptionEncryptedKey;
#       6 identityInformation.encryptedSecret = _encryptedSecret;
###################################################################
def option3() : 
	address=input("Ethereum address =")
	t=float(Talao_token_transaction.token_balance(address))
	print(t, " tokens Talao")	
	a=w3.eth.getBalance(address)
	b=a/1000000000000000000
	print(b, 'ethers')	

	# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract=Talao_token_transaction.ownersToContracts(address)
	print('Adresse du Workspace', workspace_contract)
	
	# recuperation de la cle RSA publique
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	rsa_public_key=data[4]

	# read la cle privee RSA sur le fichier
	filename = "./RSA_key/"+constante.BLOCKCHAIN+'/'+str(address)+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	with open(filename,"r") as fp :
		rsa_private_key=fp.read()	
		fp.close()   	
		
	#recuperer la cle AES cryptée
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	my_aes_encrypted=data[5]
		
	# decoder la cle AES cryptée avec la cle RSA privée
	key = RSA.importKey(rsa_private_key)
	cipher = PKCS1_OAEP.new(key)	
	aes=cipher.decrypt(my_aes_encrypted)			
	print('Clé AES décryptée = ', aes)
	
	#recuperer lE secret crypté
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	data = contract.functions.identityInformation().call()
	secret_encrypted=data[6]
	
	# decoder lE secret cryptée avec la cle RSA privée
	key = RSA.importKey(rsa_private_key)
	cipher = PKCS1_OAEP.new(key)	
	SECRET=cipher.decrypt(secret_encrypted)			
	password = SECRET.hex()
	print('password = ', password)
	
# documents
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	nb_document = contract.functions.getDocuments().call()
	for i in nb_document :
		document = contract.functions.getDocument(i).call()
		hash=document[6]
		res=Talao_ipfs.IPFS_get(hash.decode('utf-8'))
		print('')
		print ('doc ipfs retrouvé avec document sur blockchain', res)
		print('')
		print(document)
	return


###################################################################
# creer un workspace a partir d'un wallet
###################################################################
def option7() : 	
	return





###################################################################
# Creation de wallets investis en tokens et ethers
###################################################################
def option5(): 

	nb=int(input('Nombre de wallets creer ='))
	for i in range(0,nb) :
 
# creation du wallet	
		account = w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
		eth_a=account.address
		eth_p=account.privateKey.hex()
		print('adresse Ethereum =',eth_a)	

# Transaction pour le transfert de 0.03 ethers depuis le portfeuille TalaoGen
		hash1=Talao_token_transaction.ether_transfer(eth_a, 30)
		
# Transaction pour le transfert de 100 tokens Talao depuis le portfeuille TalaoGen
		hash2=Talao_token_transaction.token_transfer(eth_a,100)
		
# copie dans le fichier archive Talao_Identity.csv
		status='wallet investie'
		name='N/A'
		firstname='N/A'
		email='N/A'
		rsa_a='N/A'
		writer.writerow( (name, firstname, email,status,eth_a, eth_p, rsa_a) )

	return

###################################################################
#	envoi d'ethers
###################################################################
def option6() : 
	your_address=input('Adresse =')
	value_to_address=int(input("Ethers a envoyer (en milli)="))
	hash=Talao_token_transaction.ether_transfer(your_address, value_to_address)
	print('Hash de la transaction=', hash)	
	return	

	
###################################################################
# Creation d'un workspace from scratch
###################################################################
# generateur de RSA
def my_rand(n):
	my_rand.counter += 1
	return PBKDF2(eth_p[:16], "my_rand:%d" % my_rand.counter, dkLen=n, count=1)

def option1(firstname, name, email): 

# calcul du temps
	time_debut=datetime.now()

# creation de la wallet	
	account = w3.eth.account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
	eth_a=account.address
	global eth_p
	eth_p=account.privateKey.hex()
	print('')	
	print('adresse = ',eth_a)
	print('')
	print('private key = ', eth_p)
	print('')

# création de la cle RSA (bytes) aléatoire
#	RSA_key = RSA.generate(2048)	
# cle RSA determistic 
	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
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
	print('')
	
# encryption de la cle AES avec la cle RSA
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	AES_encrypted=cipher_rsa.encrypt(AES_key)
	
# encryption du SECRET avec la cle RSA 
	cipher_rsa = PKCS1_OAEP.new(RSA_key)
	SECRET_encrypted=cipher_rsa.encrypt(SECRET_key)
	
# Transaction pour le transfert de 0.025 ethers depuis le portfeuille TalaoGen
	hash1=Talao_token_transaction.ether_transfer(eth_a, 25)
	print('hash de transfert de 0.025 eth = ',hash1)
	print('')
	
# Transaction pour le transfert de 100 tokens Talao depuis le portfeuille TalaoGen
	hash2=Talao_token_transaction.token_transfer(eth_a,100)
	print('hash de transfert de 100 TALAO = ', hash2)
	print('')
	
# Transaction pour l'acces dans le token Talao par createVaultAccess
	hash3=Talao_token_transaction.createVaultAccess(eth_a,eth_p)
	print('hash du createVaultaccess = ', hash3)
	print('')
	
# Transaction pour la creation du workspace :
	login='auto.'+ email	
	bemail=bytes(login , 'utf-8')	
	hash4=Talao_token_transaction.createWorkspace(eth_a,eth_p,RSA_public,AES_encrypted,SECRET_encrypted,bemail)
	print('hash de createWorkspace =', hash4)
	print("")

# lecture de l'adresse du workspace contract dans la fondation
	workspace_contract_address=Talao_token_transaction.ownersToContracts(eth_a)
	print( 'workspace contract = ', workspace_contract_address)
	print('')
	
# Transaction pour la creation du compte sur le backend HTTP POST
	backend_Id = Talao_backend_transaction.backend_register(eth_a,workspace_contract_address,firstname, name, login, SECRET)
	
# mise a jour du fichier archive Talao_Identity.csv
	status='Workspace avec Backend '
	writer.writerow( (name, firstname, email,status,eth_a, eth_p, workspace_contract_address, backend_Id, login, SECRET, AES_key) )

# calcul du temps
	time_fin=datetime.now()
	time_delta=time_fin-time_debut
	print('Durée des transactions = ', time_delta)
	print('')
	
# envoi du message de log
	Talao_message.messageLog(name, firstname, email,status,eth_a, eth_p, workspace_contract_address, backend_Id, login, SECRET, AES_key)
	return eth_a,eth_p


###################################################################
#   creer des workspaces a partir d'un fichier csv
###################################################################
#
#


def option2() : 
	
	count=0
	fichiercsv=input('Entrer le nom du fichier CSV = ')

	with open(fichiercsv,newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			_name = row['LAST_NAME']
			_firstname = row['FIRST_NAME']
			_email = row['MAIL']
			print('Name = ', _name)
			option1(_firstname, _name, _email)
			count+=1		
	print ('Compteur = ', count)	
	csvfile.close()	
	return


###################################################################
# 				Main
###################################################################


a=w3.eth.getBalance(talao_public_Key)
b=a/1000000000000000000
t=Talao_token_transaction.token_balance(talao_public_Key)
	
print("")
print("###############################################################")
print("#                                                             #")
print("#             Générateur d'identités (workspace) Talao        #")
print("#                                                             #")
print("###############################################################")
print("")
print("")
print("")
print('Network = ', constante.BLOCKCHAIN)
print('Balance de la wallet du generateur =',b, 'Ethers et ',t,' TALAO tokens')	
print("")
print("")	
print("")
print("1 : Générer une Identité (wallet + workspace + backend) mais sans partenariat ")
print("2 : Générer des Identités (wallet + workspace + backend) à partir d'un fichier .csv")
print("3 : Information sur une Identité")
print("4 : Exit")
print("5 : Creer des wallets investis en tokens et ethers")
print("6 : Envoyer des Ethers")
print("7 : NON...Creer un workspace a partir d'un wallet")
print("8 : NON ....Demande de partnership")
print("9 : NON ....Créer un compte sur le Backend")
print("")


print("")

option=input("Choix : ")

if option=="4" :
	option4()
	
if option=="3" :
	option3()
	
if option=="7" :
	option7()
	
if option=="2" :
	option2()
	
if option=="5" :
	option5()
	
if option=="6" :
	option6()

if option=="1" : # generer une identité complete 
	_name = input ("saissisez le nom de l'Identité a créer :")
	_firstname = input ("saissisez le prénom de l'Identité à créer :") 
	_email = input ("saissisez l'email de l'Identité à créer :")
	option1(_firstname, _name, _email)

if option=="8" : # creation d'une demande de partnership
	my_address= input("Mon adresse Ethereum: ")
	my_private_key=input('Ma private Key')
	his_address=input("Son address Ethereum : ")
	Talao_token_transaction.partnershiprequest(my_address, my_private_key,his_address)

if option=="9" : # creer un compte sur le backend
	name = input ("saissisez le nom de l'Identité a créer sur le Backend :")
	firstname = input ("saissisez le prénom de l'Identité à créer :") 
	email = input ("saissisez l'email de l'Identité à créer (login) :")
	ethereum= input("Mon adresse Ethereum (dont un compte workspace existe) : ")
	password= input("Password sur le backend (login) : ")
	workspace=Talao_token_transaction.ownersToContracts(ethereum)
	backend_register(ethereum,workspace,firstname,name, email, password)

file.close()
sys.exit(0)




