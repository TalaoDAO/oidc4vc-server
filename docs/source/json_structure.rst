JSON data structure
===================

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
	"authority" : "Prefecture de Police de Paris",
	"country" : "France",
	"card_id" : "xxxxxxxx"}



Certificates
____________


.. code-block:: JSON

	{"type" : "experience",	
	"version" : 1,
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


.. code-block:: JSON

	{"type" : "agreement",
	"version" : 1,
	"registration_number" : "xxx",
	"title" : "xxx",
	"description" : "xxx",
	"date_of_issue" : "xxx",
	"valid_until" : "xxx",
	"location" : "xxx",
	"service_product_group" : "xxx",
	"logo" : "xxx",
	"signature" : "xxx"}


.. code-block:: JSON

    {
    "type" : "recommendation",
    "version" : 1,
	"description" : "",
    "relationship" : ""
	}


.. code-block:: JSON

	{
    "type" : "skill",
	"version" : 1,
    "title" : "",
    "description" : "",
    "date_of_issue" : "",
    "logo" : "",
    "signature" : "",
    "manager" : "",
	"reviewer" : ""
	}

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



Skills
_______


to be defined


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
