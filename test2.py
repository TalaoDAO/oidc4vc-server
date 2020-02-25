
from web3.auto import w3
import constante
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import Talao_token_transaction
import csv
import http.client, urllib.parse
import json
import datetime
import Talao_backend_transaction
import Talao_ipfs

# trad lang
def Language(lang) :
	code=lang.lower()
	if code == 'french' :
		return "fr"
	elif code == "english" :
		return "en"
	elif code == "german" :
		return "ge"
	elif code == "danish" :
		return "da"
	elif code=="spanish" :
		return "sp"
	elif code=="chineese" :
		return "ch"		
	elif code == "italian" :
		return "it"	
	elif code== "russian" :
		return "ru"
	elif code == "japaneese" :
		return "ja"
	elif code == "arabic" :
		return "ar"
	elif code == "polish" :
		return "po"
	elif code == "dutch" :
		return "du"
	elif code == "swedish" :
		return "sw"				
	else :
		return ""	


def Proficiency(texte) :
	text=texte.lower()
	if text == 'native or bilingual' :
		return 5
	if text == 'full professional' :
		return 4
	if text == 'elementary' or text =='null' :
		return 1
	if text == 'professional working' :
		return 3
	if text == 'limited working' :
		return 2
		
	

# ouverture du fichier .csv
fichiercsv=input('Entrer le nom du fichier CSV = ')
with open(fichiercsv,newline='') as csvfile:
	reader = csv.DictReader(csvfile)
	
	# pour chaque ligne du fichier = chaque identité/workspace
	for row in reader:
		# UPLOAD DES LANGUAGES et employabilité
		lang=[]
		for i in ['Language 1', 'Language 2', 'Language 3','Language 4', 'Language 5', 'Language 6', 'Language 7', 'Language 8', 'Language 9', 'Language 10'] :
			chaine= row [i]
			if len(chaine) != 0 and chaine != 'NULL' and chaine != " " :
				langtab=chaine.split(',')
				langitem={"code": Language(langtab[0]),"profiency": Proficiency(langtab[1])}	
				lang.append(langitem)		
		employabilite={
  "documentType": 10000,
  "version": 1,
  "recipient": {
    "name": 'name',
    "title": 'jobTitle',
    "email": 'email',
    "ethereum_account": 'address',
    "ethereum_contract": 'workspace_contract'
  },
  "availability": {
    "dateCreated": "2020-02-21T15:35:02.374Z",
    "availabilityWhen": 'null',
    "availabilityFulltime": 'null',
    "mobilityRemote": 'false',
    "mobilityAreas": 'false',
    "mobilityInternational": 'false',
    "mobilityAreasList": [
      
    ],
    "rateCurrency": 'null',
    "ratePrice": "",
    "languages": lang
  }
}	
		print (employabilite)
		#Talao_token_transaction.createDocument(address, private_key, 10000, employabilite, False)


		print('')
		saisie=input('next row ??? yes/no = ')
		if saisie == "no" :
			csvfile.close()
			sys.exit(0)

	csvfile.close()
	sys.exit(0)






