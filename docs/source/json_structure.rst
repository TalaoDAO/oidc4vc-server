JSON data structure
===================

Kbis
____


.. code-block:: JSON

	{
	"siren" : "662 042 449",
	"date" : "1966-09-23",
	"name" : "BNP",
	"legal_form" : "SA",
	"naf" : "6419Z",
	"capital" : "2 499 597 122 EUROS",
	"address" : "16 BOULEVARD DES ITALIENS, 75009 PARIS", 
	"activity" : "Servics financiers",
	"ceo" : null,
	"managing_director" : null
	}




Kyc
___


.. code-block:: JSON

	{
	"country" : "FRA3",
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
	"card_id" : "xxxxxxxx"
	}



Certificates
____________


.. code-block:: JSON

	{
	"type" : "experience",
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
	"reviewer" : "Paul Jacques"
	}



.. code-block:: JSON

	{
	"type" : "reference",
	"version" : 1,
	"title" : "",
	"description" : "",
	"budget" : "",
	"staff" : "",
	"location" : "",
	"start_date" : "2018-02-22",
	"end_date" : "2019-01-25",
	"competencies" : ["", ""],
	"score_recommendation" : 2,
	"score_delivery" : 3,
	"score_schedule" : 4,
	"score_communication" : 4,
	"score_budget" : 4,
	"issued_by" : {
		"name" : "",
		"postal_address" : "",
		"siren" : "",
		"logo" : "xxx",
		"signature" : "xxx",
		"manager" : ""
		}
	"issued_to" : {
		"name" : "",
		"postal_address" : "",
		"siren" : "",
		"logo" : "",
		"signature" : "",
		}
	}


Score is an integer value [0,1,2,3,4,5] for 5 evaluations :


   - How satisfied are you with the overall delivery ?
   - How would you rate his/her ability to deliver to schedule ?
   - How would you rate its communication ?
   - How would you rate its ability to stay within the set budget?
   - How likely are you to recommand this company ?



.. code-block:: JSON

	{
	"type" : "agreement",
	"version" : 1,
	"registration_number" : "xxx",
	"title" : "xxx",
	"description" : "xxx",
	"standard" : "",
	"date_of_issue" : "xxx",
	"valid_until" : "xxx",
	"location" : "xxx",
	"service_product_group" : "xxx",
	"issued_by" : {
		"name" : "",
		"postal_address" : "",
		"siren" : "",
		"logo" : "xxx",
		"signature" : "xxx",
		"manager" : "",
		}
	"issued_to" : {
		"name" : "",
		"postal_address" : "",
		"siren" : "",
		"logo" : "",
		"signature" : "",
		}
	}


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

	{
	"company" : {
		"contact_email" : "Pierre@bnp.com",
		"name" : "Thales",
		"contact_name" : "Jean Dujardin",
		"contact_phone" : "0607254589"
				},
	"title" : "Chef de projet Blockchain",
	"description" : "Conception et ralisation d un prototype Ethereum d un suivi de production",
	"start_date" : "2018/02/22",
	"end_date" : "2019/01/25",
	"skills" : ["Ethereum", "Solidity"],
	"certificate_link" : ""
	}



Education
_________


.. code-block:: JSON

	{
	"organization" : {"contact_email" : "Pierre@bnp.com",
		"name" : "Ensam",
		"contact_name" : "Jean Meleze",
		"contact_phone" : "0607255656"},
	"title" : "Master Engineer",
	"description" : "General Study",
	"start_date" : "1985/02/22",
	"end_date" : "1988/01/25",
	"skills" : [],
	"certificate_link" : ""
	}
