Overview
========

To be completed


Talent Connect
==============

The Talent Connect APIs are a set of APIs to manage sata exchange and onboardind process with Talents who have a Distributed Professional Identiy.
It is an easy way for companies to get reliable data about their professional activities without downloading data to a centralized Database. 

Furthermore each parcel of data can be temperproofed through imutable transactions. 
  

ERC735 Interface
----------------

Those APIs are based on the EIP735 standard. They are build with topicnames according to an ascci to integer `translation <https://github.com/ethereum/EIPs/issues/735#issuecomment-450647097>`_.
Read more about the technical aspect on `EIP735 <https://github.com/ethereum/EIPs/issues/735>`_
Username and Topicname must be provided.

Exemple :

.. code:: 
   
   $ curl -GET http://192.168.0.34:3000/api/claim/  -d username=bnp -d topicname=name

Return of call (JSON)

.. code-block:: JSON

  {
  "topic_value": 110097109101,
  "topic_name": "name",
  "created": "2020-05-27 10:32:46",
  "transaction_hash": "0xb948f9d02c53c37b4da93d68bed1cbf9219f64e8094a642e32ac53c3b4cccc5f",
  "issuer": {
    "address": "0x18bD40F878927E74a807969Af2e3045170669c71",
    "workspace_contract": "0xD6679Be1FeDD66e9313b9358D89E521325e37683",
    "category": 2001,
    "type": "Company",
    "username": "web.relay.talao",
    "name": "Relay",
    "contact_name": null,
    "contact_email": null,
    "contact_phone": null,
    "website": null,
    "email": "thierry.thevenet@talao.io"
  },
  "transaction_fee": 503392000000000,
  "claim_id": "dbbbd3f44051315cf3c7e5821570063265ef86fd370ae491a094dd42748ec1b5",
  "ipfs_hash": "",
  "data_location": "https://ipfs.infura.io/ipfs/",
  "privacy": "public",
  "identity": {
    "address": "0x8AF132eEb947459Bc56FCc64Ae8c41f42F6AbA05",
    "workspace_contract": "0x4A2B67f773D30210Bb7C224e00eAD52CFCDf0Bb4"
  },
  "claim_value": "BNP"
  }

Topicname standard list :

	* for a person : firstname, lastname, url, email 
	* for a company : name, contact_name, contact_phone, contact_email, website, email
				

To get a full resume :

.. code:: 

   $ curl http://127.0.0.1:3000/api/resume/  -GET -H "Content-Type: application/json" -d username=jean.pascalet




RESTfull API
============

JSON
----

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
	"firstname" : "Jean",
	"lastname" : "Pascalet"
	"company" : {"contact_email" : "Pierre@bnp.com",
				"name" : "Thales",
				"contact_name" : "Jean Dujardin",
				"contact_phone" : "0607254589"},
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
