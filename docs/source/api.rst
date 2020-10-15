
Talent Connect Overview
=======================

Talent Connect is a set of APIs to exchange public and private data between Professional Identities (Talent or Company) and eventually start an onboarding process.

For companies it is an easy way to get reliable data about Talents.
For Talents it is an efficient way to expose their true skills and personal credentials while controlling their data.

A standard use case is :

  * Talent fills a Company recrutment website with his Talao username.
  * Company downloads Talent public resume (public Talao API).
  * Company requests Talent to access his private professional data (secure Talao API).
  * Talent receives the request with Company's credentials (email or phone sms).
  * Talent accepts or rejects the request (Talao website).
  * If accepted, Company downloads Talent private professional data (secure API).

OAuth 2.0 Client Credentials Flow (2-Legged)
--------------------------------------------
For certain endpoints we offer OAuth 2.0 application access via the Client Credentials Flow.
Commonly referred to as "OAuth two-legged", this flow allows your application to authorize with Talao's API directly - outside the context of any specific user.
By default, your application will not have the ability to use client credentials flow.  Contact us to have your application granted permission to use this flow.

Once you have your Client ID and Client Secret values, as in the example above, you are ready to proceed.

Scopes available :

   - skill : to issue skill certificate
   - experience : to issue experince certificate
   - kbis : to issue proof of identity for companies
   - kyc : to issue proof of identity for person
   - identity : to create identity


Generating an Access Token
**************************

Using the Client Credentials Flow is straightforward - simply issue an HTTP GET against the endpoint with both your client_id and client_secret set appropriately.

To get the token :

.. code:: 

   curl -u your_client_ID:your_secret_value -XPOST https://talao.co/api/v1/oauth/token -F grant_type=client_credentials -F scope=identity

To get an access to an endpoint

.. code:: 

   curl -H "Authorization: Bearer your_token" https://talao.co/api/v1/endpoint -d  firstname=Pierre -d lastname=Dupont


Endpoint
********

/create_identity

Public Request
***************

.. code:: 

  GET https://talao.co/api/v1/talent-connect/

Header
******

.. code:: 
  
  "Content-Type: application/json" 

Payload
*******

  
   * user 
   
      * a username or a Decentalized IDentifiant

   * topicname

      * for a person : firstname, lastname, contact_email, contact_phone, birthdate, postal_address (self declared)
      * for a company : name, contact_name, contact_phone, contact_email, website (self declared)
      * resume : full resume of a user
      * analysis : resume data analysis
      * kyc or kbis (issued by third parties)
      * experience : list of all experiences (self declaration)
      * certificate : list of all certificates issued by third paries
      * education : list of diplomas (self declaration)
      * search : (to be completed)
    
   * option (optional)

      * to be completed

Example
********

.. code:: 
   
   $ curl -GET https://talao.co/api/v1/talent-connect/ \
   -H "Content-Type: application/json" \
   -d user=jean.pascalet \
   -d topicname=experience 
   
   
Response
********

.. code-block:: JSON

  [
  {
    "topic": "experience",
    "created": "2020-05-25 10:07:22",
    "issuer": {
      "address": "0x18bD40F878927E74a807969Af2e3045170669c71",
      "workspace_contract": "0xD6679Be1FeDD66e9313b9358D89E521325e37683",
      "category": 2001,
      "id": "did:talao:rinkeby:D6679Be1FeDD66e9313b9358D89E521325e37683",
      "name": "Relay",
      "contact_name": null,
      "contact_email": null,
      "contact_phone": null,
      "website": null
    },
    "transaction_hash": "0x49dc98ad487a33a4e066e8e05758870e7972466c5e74c261ea5b4ebe091003de",
    "transaction_fee": 2000000000000,
    "doctypeversion": 2,
    "ipfshash": "QmThxo5shaJSDCYZprXzwknqgCoPja5rUW3528qNFHCKft",
    "data_location": "https://gateway.ipfs.io/ipfs/QmThxo5shaJSDCYZprXzwknqgCoPja5rUW3528qNFHCKft",
    "expires": "Unlimited",
    "privacy": "public",
    "doc_id": 23,
    "id": "did:talao:rinkeby:Ec0Cf3FA4158D8dd098051cfb14af7b4812d51aF:document:23",
    "identity": {
      "address": "0x048D19e72030a9D7a949517D5a9E3844b4533fc2",
      "workspace_contract": "0xEc0Cf3FA4158D8dd098051cfb14af7b4812d51aF",
      "category": 1001,
      "id": "did:talao:rinkeby:Ec0Cf3FA4158D8dd098051cfb14af7b4812d51aF"
    },
    "title": "CTO",
    "description": "En charge du projet Blockchain",
    "end_date": "2020-05-01",
    "start_date": "2020-01-01",
    "company": {
      "address": null,
      "contact_email": "basil@bnp.com",
      "contact_name": "",
      "contact_phone": "0607182594",
      "name": "BNP",
      "website": null,
      "workspace_contract": null
    },
    "certificate_link": null,
    "skills": [
      "Java"
    ]
  },
  {
    "topic": "experience",
    "created": "2020-06-06 18:54:35",
    "issuer": {
      "address": "0x18bD40F878927E74a807969Af2e3045170669c71",
      "workspace_contract": "0xD6679Be1FeDD66e9313b9358D89E521325e37683",
      "category": 2001,
      "id": "did:talao:rinkeby:D6679Be1FeDD66e9313b9358D89E521325e37683",
      "name": "Relay",
      "contact_name": null,
      "contact_email": null,
      "contact_phone": null,
      "website": null
    },
    "transaction_hash": "0xb3c181a2490ebf9a18e875cbb47e14041c5f7a34854cd8e9ca9f2016d092696c",
    "transaction_fee": 2000000000000,
    "doctypeversion": 2,
    "ipfshash": "QmdWCKBVybPRQvWmY7hAbkRHFRXvvPPqKAi8ieZBm2WtEd",
    "data_location": "https://gateway.ipfs.io/ipfs/QmdWCKBVybPRQvWmY7hAbkRHFRXvvPPqKAi8ieZBm2WtEd",
    "expires": "Unlimited",
    "privacy": "public",
    "doc_id": 36,
    "id": "did:talao:rinkeby:Ec0Cf3FA4158D8dd098051cfb14af7b4812d51aF:document:36",
    "identity": {
      "address": "0x048D19e72030a9D7a949517D5a9E3844b4533fc2",
      "workspace_contract": "0xEc0Cf3FA4158D8dd098051cfb14af7b4812d51aF",
      "category": 1001,
      "id": "did:talao:rinkeby:Ec0Cf3FA4158D8dd098051cfb14af7b4812d51aF"
    },
    "title": "CTO",
    "description": "We are working to deliver software solutions and consulting services to businesses worldwide, and help our clients to create innovative and technological products in various areas.\r\n\r\nInnowise Group team is divided into several departments and structural units responsible for certain areas of company\u2019s activities.\r\nSeamless collaboration between all of them on a daily basis helps us achieve short term objectives and strategic goals.",
    "end_date": "2019-11-01",
    "start_date": "2019-07-01",
    "company": {
      "contact_email": "pierre@bnp.com",
      "contact_name": "Pierre",
      "contact_phone": "01 607182594",
      "name": "Covea"
    },
    "certificate_link": "",
    "skills": [
      "Business",
      "Management,",
      "consulting"
    ]
  }
  ]
   
 

Exchange data with User
------------------------

General Request
***************

Authenticating using a login and secret through HTTP Basic Authentication.
Check your your API credentials.

Access can be also secured through a specific White List to limit the client domains.  


.. code:: 

  POST https://talao.co/api/v1/talent-connect/auth/

Header
******

.. code:: 
  
  "Content-Type: application/json" 
  
Authentification
*****************  

.. code:: 
  
  login:secret

Payload
*******

.. code:: 
  
   {"action" : xxxx, "user" : xxxxx} 
	
action :

  * call_back : send an email
  * to be completed

Example
*******

.. code:: 

   curl -X POST https://talao.co/talent-connect/auth/  \
   -u 0x4A2B67f773D30210Bb7C224e00eAD52CFCDf0Bb4:3042d4704a513b3ffb4a2adb78e73446   \ 
   -d '{"action" : "call_back"}' \
   -H "Content-Type: application/json" 
 
