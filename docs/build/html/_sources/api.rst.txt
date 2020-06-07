
Talent Connect APIs
===================

The Talent Connect APIs are a set of APIs to get public data of a Professional Identity (Talent or Company) to eventually start an onboardind process.

For companies it is an easy way to get reliable data about Talents. 

For Talents it is an efficient way to expose their true skills and personal credentials while controlling their data.

Each parcel of data can be explored to get

  * issuer information, signature, name,
  * date of creation and expiration,
  * data location,
  * proofs of validity. 
  

General use :

.. code:: 
   
   $ curl -GET http://talao.co:5000/api/v1/talent-connect/ -H "Content-Type: application/json" \
   -d user=......
   -d topicname=....
   -d option=....
   
user 
-----
   
   * a username (jean.pascalet,....)
   * or a Decentalized IDentifiant (did:talao:rinkeby:did:talao:rinkebyD6679Be1FeDD66e9313b9358D89E521325e37683,...) 

topicname
---------

   * for a person : firstname, lastname, contact_email, contact_phone, birthdate, postal_address (self declared)
   * for a company : name, contact_name, contact_phone, contact_email, website (self declared)
   * resume : full resume of a user
   * analysis : resume data analysis
   * kyc or kbis (issued by third parties)
   * experience : list of all experiences (self declaration)
   * certificate : list of all certificates issued by third paries
   * education : list of diplomas (self declaration)
    
option
------

   * to be completed
 
   
Exemples
---------
   
To get access to the "firstname" parcel of information of a Talent :

.. code:: 
   
   $ curl -GET http://talao.co:5000/api/v1/talent-connect/ -H "Content-Type: application/json" -d user=jean.pascalet -d topicname=firstname

Return of call (JSON)

.. code-block:: JSON

  {
  "topicvalue": 102105114115116110097109101,
  "topicname": "firstname",
  "created": "2020-05-26 16:02:00",
  "transaction_hash": "0xf669fae0cbbf20e20e7d05ef0b089e20b77fc23ca9f1f0a1b8e4976efee6bdc3",
  "issuer": {
    "address": "0x18bD40F878927E74a807969Af2e3045170669c71",
    "workspace_contract": "0xD6679Be1FeDD66e9313b9358D89E521325e37683",
    "category": 2001,
    "id": "did:talao:rinkebyD6679Be1FeDD66e9313b9358D89E521325e37683",
    "type": "company",
    "username": "web.relay.talao",
    "name": "Relay",
    "contact_name": null,
    "contact_email": null,
    "contact_phone": null,
    "website": null
  },
  "transaction_fee": 2000000000000,
  "claim_id": "1be33b54289ed1cb918ea9327e1c79be80e55cfda6e830e3ffbb3c21f53b0c9d",
  "ipfs_hash": "",
  "data_location": "https://ipfs.infura.io/ipfs/",
  "privacy": "public",
  "identity": {
    "address": "0x048D19e72030a9D7a949517D5a9E3844b4533fc2",
    "workspace_contract": "0xEc0Cf3FA4158D8dd098051cfb14af7b4812d51aF",
    "category": null,
    "id": "did:talao:rinkebyEc0Cf3FA4158D8dd098051cfb14af7b4812d51aF"
  },
  "claim_value": "Jean"
  }
 

To get access to the kbis of a Company :

.. code:: 
   
   $ curl -GET http://talao.co:5000/api/v1/talent-connect/ -H "Content-Type: application/json" -d user=bnp -d topicname=kbis


.. code-block:: JSON

   {
  "topic": "kbis",
  "created": "2020-06-02 23:10:05",
  "issuer": {
    "address": "0xE7d045966ABf7cAdd026509fc485D1502b1843F1",
    "workspace_contract": "0xfafDe7ae75c25d32ec064B804F9D83F24aB14341",
    "category": 2001,
    "id": "did:talao:rinkeby:fafDe7ae75c25d32ec064B804F9D83F24aB14341",
    "name": "Talao",
    "contact_name": "Thierry Thevenet",
    "contact_email": "thierry.thevenet@talao.io",
    "contact_phone": "0607182594",
    "website": "www.talao.io"
  },
  "transaction_hash": "0x05398cf146309d98df452f1859fe27001e4fb8ebf8bbd618fdb89bc4d0025450",
  "transaction_fee": 2000000000000,
  "doctypeversion": 2,
  "ipfshash": "QmQUjGw9U2ifze5PLb4Dpx5cdwRSXVGEGXTYE8mH7wP9SQ",
  "data_location": "https://gateway.ipfs.io/ipfs/QmQUjGw9U2ifze5PLb4Dpx5cdwRSXVGEGXTYE8mH7wP9SQ",
  "expires": "Unlimited",
  "privacy": "public",
  "doc_id": 1,
  "id": "did:talao:rinkeby:4A2B67f773D30210Bb7C224e00eAD52CFCDf0Bb4:document:1",
  "identity": {
    "address": "0x8AF132eEb947459Bc56FCc64Ae8c41f42F6AbA05",
    "workspace_contract": "0x4A2B67f773D30210Bb7C224e00eAD52CFCDf0Bb4",
    "category": 2001,
    "id": "did:talao:rinkeby:4A2B67f773D30210Bb7C224e00eAD52CFCDf0Bb4"
  },
  "name": "BNP",
  "siret": "662 042 449 00014",
  "date": "1966-09-23",
  "capital": "2 499 597 122 EUROS",
  "address": "16 BOULEVARD DES ITALIENS, 75009 PARIS",
  "legal_form": "SA",
  "activity": "Servics financiers",
  "naf": "6419Z",
  "ceo": null,
  "managing_director": null
  }

To get a full resume of a talent through his username :

.. code:: 

   $ curl http://talao.co:5000/api/v1/talent-connect/  -GET -H "Content-Type: application/json" -d user=jean.pascalet -d topicname=resume


To get a full resume through Talent DID :

.. code:: 

   $ curl http://talao.co:5000/api/v1/talent-connect/  -GET -H "Content-Type: application/json" -d user=did:talao:rinkeby:Ec0Cf3FA4158D8dd098051cfb14af7b4812d51aF -d topicname=resume


To get an Analysis :

.. code:: 

   $ curl http://talao.co:5000/api/v1/talent-connect/  -GET -H "Content-Type: application/json" -d user=jean.pascalet -d topicname=analysis


.. code-block:: JSON

   {
  "id": "did:talao:rinkeby:Ec0Cf3FA4158D8dd098051cfb14af7b4812d51aF",
  "workspace_contract": "0xEc0Cf3FA4158D8dd098051cfb14af7b4812d51aF",
  "type": "person",
  "name": "Jean Pascalet",
  "nb_data": 10,
  "nb_data_self_declared": 9,
  "nb_data_whitelist_issuer": 1,
  "nb_data_unknown_issuer": 0,
  "kyc": true,
  "kbis": "N/A",
  "nb_experience": 2,
  "nb_words_per_experience": 33.5,
  "nb_certificate": 0
  }



Internal 
=========

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
