
Talent Connect API
==================

Talent Connect is a set of APIs to exchange public and private data between Professional Identities (Talent or Company).
For companies it is an easy way to get reliable data about Talents and it is a powerfull and secure tool for automatic onbarding.

Those API do not provide account management (update logo, signature, set company details, add managers, change password, ...)

Standard use cases for APIs are :

* Talent registers to a Company recrutment website with his Talao Identity to give an access to his public JSON resume (https://jsonresume.org/).
* Talent registers to a Company to exchange data (resume, passport, diplomas,...) receive claims (experience certificates, skill certificates, ...) and store documents (payslip,...). 

We use OAuth2 Autorization Code flow and OAuth2 Client Credentials flow to manage those cases.

Contact us to have your application granted permission to use those flows.

OAuth 2.0 Authorization Code flow
----------------------------------

Used to get an access to Talent personal data with his agreement (Profile, JSON Resume). Basically same as openid.


OAuth 2.0 Authorization Code Extended flow
------------------------------------------

Same as previous but Talent add the company as a referent.

Talao Digital Onboarding flow
-----------------------------

Used to build an automatic onboarding.
Company acts as a verifier to check Talent claims.
Both parties can issue and receive claims to each other.
Human onboarding process is reduced to minimum.

This flow is built above the Talao Partnership protocol.

1 Talent connects to the company website and is redirected to the Talao login view to follow a two factor authentification process
2 If partnership does not exist, Talent requests a partnership to company
3 Company checks Identity claims to accept or reject the requested partnership

Step 3 is the most important step as it is an automatic process allowed by verifiable claims (ERC725 claims and Talao documents) issued by legitimate issuers.
For instance company can look for a proof of identity issued by a white listed issuer or look for a specif educational degree issued by a specific issuer.

If company accepts partnership, Talent is onboarded and next sign_in will be straight forward through a standard Authorization code flow. 


OAuth 2.0 Client Credentials Flow
---------------------------------

For basic actions we offer OAuth 2.0 application access via the Client Credentials Flow.
Commonly referred to as "OAuth two-legged", this flow allows your application to authorize with Talao's API directly.
Some actions do not involve user interaction but a prior agreement.

Scope is a mechanism in OAuth 2.0 to limit an application's access to a user's account.
An application can request one or more scopes, this information is then presented to the user in the consent screen, and the access token issued to the application will be limited to the scopes granted.

   - profile : to access basic user data
   - resume ; to access user resume
   - issuer : to issue certificates or send files
   - creator : to create identity for others
   - referent : to add referent
   - partner : to request partnership
   - recruter : to invit Talent

Generating an Access Token
---------------------------

Once you have copy your client_id and client_secret values from the https://talao.co website, you are ready to proceed.

Authorization Code
******************


Client Credentials
******************

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
 
