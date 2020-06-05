"""
POur ajouter un kbis a une société par Talao

"""

import constante
import environment
from protocol import Kbis


# environment setup
mode=environment.currentMode()
w3=mode.w3



kbis = { "siret" : "662 042 449 00014",
	   "date" : "1966-09-23",
	    "name" : "BNP",
	    "legal_form" : "SA",
	    "naf" : "6419Z",
	    "capital" : "2 499 597 122 EUROS",
	    "address" : "16 BOULEVARD DES ITALIENS, 75009 PARIS", 
	    "activity" : "Servics financiers",
	    "ceo" : None,
	    "managing_director" : None
	    } 

bnp = '0x4A2B67f773D30210Bb7C224e00eAD52CFCDf0Bb4'

bnp_kbis = Kbis()

print(bnp_kbis.talao_add(bnp, kbis, mode, mydays=0, privacy='public', synchronous=True))

