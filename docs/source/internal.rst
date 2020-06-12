
Internal 
=========

Name Service
------------

Name Service (NS) is an independant routine to provide a readable identifier to DID.
NS is supported by a Company Identity (nameservice) and claims issued within the Identity. Each user has a claim issued with a claim id calculated with his "namehash".
Namehash are deducted from username according to the `Ethereum Name Service algorithm <https://docs.ens.domains/dapp-developer-guide/resolving-names>`_ .

Claim Id are defined with address = namehash and topic = 117115101114110097109101 (username) with SHA3.


.. code-block:: python

   claim_id = w3.solidityKeccak(['address', 'uint256'], [namehash, 117115101114110097109101 ]).hex()


claims data are stored on IPFS as a JSON :

.. code-block:: JSON


  { "namehash' : namehash,
	"wokspace_contract" : address,
	"hosts" :  [address],
	"publickey" : sha3_address,
	} 


Talao ERC725 Keys
-----------------


+--------------------+-----------------------------------+
|       Keys         |               Type                |
+====================+===================================+
| 1                  |   Management Key, do everything   |
+--------------------+-----------------------------------+
| 2                  |   Not used  (see ERC725)          |    
+--------------------+-----------------------------------+
| 3                  |   Not used                        |
+--------------------+-----------------------------------+
| 4                  |   Not Used                        |
+--------------------+-----------------------------------+
| 5                  |   Issuer White List               |
+--------------------+-----------------------------------+
| 20002              |   Issuer Documents                |
+--------------------+-----------------------------------+
| 20003              |   Member                          |
+--------------------+-----------------------------------+




Talao Documents
---------------

JSON format is used to organized data within Talao Documents. 

Read more technical information on `Talao Documents <https://github.com/TalaoDAO/talao-contracts/blob/master/contracts/content/Documents.sol>`_.

Doctype
_______

One document is defined through is 'doctype' (int). A document can be **Public**, **Private** or **Secret**. By default most documents are Public.


+--------------------+-----------+-----------+-----------+
|       doctype      |  Public   |  Private  |   Secret  |
+====================+===========+===========+===========+
| kbis               |   10000   |    N/A    |    N/A    |
+--------------------+-----------+-----------+-----------+
| kyc                |   15000   |    N/A    |    N/A    |    
+--------------------+-----------+-----------+-----------+
| certificate        |   20000   |    N/A    |    N/A    |
+--------------------+-----------+-----------+-----------+
| education          |   40000   |   40001   |   40002   |
+--------------------+-----------+-----------+-----------+
| experience         |   50000   |   50001   |   50002   |
+--------------------+-----------+-----------+-----------+


Kbis
____


.. code-block:: JSON

   { "siret" : "662 042 449 00014",
   "date" : "1966-09-23",
   "name" : "BNP",
   "legal_form" : "SA",
   "naf" : "6419Z",
   "capital" : "2 499 597 122 EUROS",
   "address" : "16 BOULEVARD DES ITALIENS, 75009 PARIS", 
   "activity" : "Servics financiers",
   "ceo" : null,
   "managing_director" : null} 
	



Kyc
___

	
.. code-block:: JSON

	{"country" : "FRA3",
	"id" : "15CA98225",
	"lastname" : "Houlle",
	"firstname" : "Pierre david",
	"sex" : "M",
	"nationality" : "Francaise",
	"date_of_birth" : "1980-1212",
	"date_of_issue" : "2012-02-13",
	"date_of-expiration" : "2022-02-12",
	"authority" : "Prefecture de Police de Paris"}



Certificate
___________


.. code-block:: JSON

	{"type" : "experience",	
	"title" : "Chef de projet Blockchain",
	"description" : "Conception et ralisation d un prototype Ethereum d un suivi de production",
	"start_date" : "2018/02/22",
	"end_date" : "2019/01/25",
	"skills" : ["Ethereum", "Solidity"],  		
	"score_recommendation" : 2,
	"score_delivery" : 3,
	"score_schedule" : 4,
	"score_communication" : 4,
	"logo" : "thales.png",
	"signature" : "permet.png",
	"manager" : "Jean Permet",
	"reviewer" : "Paul Jacques"}



	    
Experience
__________



.. code-block:: JSON

	{"company" : {"contact_email" : "Pierre@bnp.com",
				"name" : "Thales",
				"contact_name" : "Jean Dujardin",
				"contact_phone" : "0607254589"},
	"title" : "Chef de projet Blockchain",
	"description" : "Conception et ralisation d un prototype Ethereum d un suivi de production",
	"start_date" : "2018/02/22",
	"end_date" : "2019/01/25",
	"skills" : ["Ethereum", "Solidity"],
	"certificate_link" : ""}



	    
Education
_________




.. code-block:: JSON

	{"organization" : {"contact_email" : "Pierre@bnp.com",
				"name" : "Ensam",
				"contact_name" : "Jean Meleze",
				"contact_phone" : "0607255656"},
	"title" : "Master Engineer",
	"description" : "General Study",
	"start_date" : "1985/02/22",
	"end_date" : "1988/01/25",
	"skills" : [],
	"certificate_link" : ""}
