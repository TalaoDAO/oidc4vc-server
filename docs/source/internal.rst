
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

