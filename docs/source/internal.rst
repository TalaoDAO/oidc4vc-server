
Internal 
=========

Name Service (NS)
-----------------

Name Service (NS) is an independant routine to provide a readable identifier for DID and an easy way to log to company and person Identity through Relay.
One can use NS to setup Manager for companies. THe Managers have the right to use the Relay to sign transaction on behalf of the Identity.

It supports :

   * Identity_name : a readable name for a DID (an identity workspace contract).
   * Alias Name : for a person it is a readable name to log its own identity an an email to authentify.
   * Manager Name : a readable name/email to log to a company identity. 

Manager have a username made up of 2 parts example 'johndoe.generalmotors". A manager MUST have is own identity.
Identity and Alias are one part names : "johndoe"

At Identity creation, 2 statements are written :

   * in the Resolver Table (identity_name/identity_workspace_contract/date)
   * in the Alias Table (alias_name/identity_name/email/date).

At Manager creation, one stament is written :

   * in the Manager Table of the company (manager_name/alias_name/email/date). 

To log to the company Identity through Relay the manager will use a 2 parts username as  "manager_name.company_identity_name".


NS is today supported by SQLite3 with one DB per company for Managers and one DB for DID, Publickey and Alias (Migration to a decentralied support in progress).
	
.. code-block:: python

   def init():
	  conn = sqlite3.connect('nameservice.db')
	  cur = conn.cursor()
	  cur.execute('create table alias(alias_name text, identity_name text, email text, date real)')
	  cur.execute('create table resolver(identity_name text, identity_workspace_contract text, date real)')
	  cur.execute('create table publickey(address text, key text)')
	  conn.commit()
	  cur.close()
	  return
	
   def init_host(host_name) :
	  conn = sqlite3.connect(host_name + '.db')
	  cur = conn.cursor()
	  cur.execute('create table manager(manager_name text, alias_name text, email text, date real)')
	  conn.commit()
	  cur.close()

IPFS
----

We use IPFS and `Pinata <https://pinata.cloud>`_ pin services for data persistence.

To add data to IPFS we first add to PInata Node and pin to local node.
To get data , we first get from local and after timeout of 5s we get from pinata.
Our Pin Policy at Pinata is to have 2 replications in Europe. 



Identity vs keys
----------------

Company Identities are always created by Talao which has a copy of the private key and RSA key

For User Identity, it depends on the way it has been created. Talao might have nothing or only a Management key to sign transactions or a Management Key + RSA key or the private key.
If user Identity has been created by Relay, Talao has a copy of the private key, RSA key and secret key. 


Talao ERC725 Keys 
-----------------


+--------------------+-----------------------------------+
|       Keys         |               Usage               |
+====================+===================================+
| 1                  |   Relay if activated              |
+--------------------+-----------------------------------+
| 2                  |   Not Used                        |    
+--------------------+-----------------------------------+
| 3                  |   Personal/Company settings       |
+--------------------+-----------------------------------+
| 4                  |   Not used                        |
+--------------------+-----------------------------------+
| 5                  |   Issuer White List               |
+--------------------+-----------------------------------+
| 20002              |   Issuer Documents                |
+--------------------+-----------------------------------+
| 20003              |   Not used                        |
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
	"authority" : "Prefecture de Police de Paris",
	"card_id" : "xxxxxxxx"}



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
