
Talao Connect API
==================

Talao Connect APIs can be used for authentication, identification, claims issuance and more generally for Identity management.
For instance in the Human Resource sector it is an easy way to get reliable data about Talents and a powerfull and secure tool for onbarding user while keeping their data safe.

Those API do not provide basic account setup (details, signature, logo ...) which are available through the web platform https://talao.co .

Standard use cases for APIs are :

* Issue certificates to users (Talents, Companies,...).
* Onboard users who have their own Decentralized Identity.
* Outsource user data to their Digital Identity.
* Strenghen an employer brand with latest technology features like Blockchain Resume, Decentralized Identity,...

The Talao API server is an OpenId Connect server. We use OpenID Connect Autorization Code flow for authentification and OAuth 2.0 Authorization code flow and Client Credentials flow to manage user access to their identity.

Contact us relay-support@talao.io to open your Company Identity and receive your application granted permissions to use those APIs.

From the OIDC and OAuth 2.0 perspective :

* "Company" is the Client application
* "User" is the Resource Owner, it maybe a Talent or another Company
* "Talao API server" is the Authorization Server/Resource Server


OpenID Connect
--------------

For your users, the OpenID Connect authentication experience includes a consent screen that describes through 'scopes' the information that the user is releasing.
For example, when the user logs in, they might be asked to give your appication access to their name, email address and basic account information.
You request access to this information using the scope parameter, which your app includes in its authentication request.

Scopes available
****************

Scopes for data access are standard OpenID Connect and specific Talao scopes :

* openid (required)
* profile (sub + given_name + family_name + gender)
* birthdate
* email
* phone
* address
* about : short user description
* resume : for person identity only
* proof_of_identity

.. note:: "sub" is the  Decentralized IDentier of the user (did). It always starts with "did:talao:talaonet:".

Those data are available through an ID Token (JWT) and at the user_info endpoint through an Access Token.

Process
*******

As defined by OIDC, 3 steps are required :

Step 1 : to get a grant code from user, redirect your user to https://talao.co/api/v1/authorize with a subset of your scope list .
User will be asked to sign in with his Identity username/password and to consent for your list of scopes.

Example :

.. code::

   https://talao.co/api/v1/authorize?response_type=code&client_id=your_client_id&scope=your_scopes


Step 2, with the grant code, connect to the token endpoint https://talao.co/api/v1/auth/token to get an Access Token and an ID Token. You will need your client_secret.

.. code::

   curl -u your_client_id:your_secret_value -XPOST https://talao.co/api/v1/oauth/token -F grant_type=authorization_code 

If you nly need user authentication, see further how to decode the JWT to get user data and serveur signature.


Step 3 : with the Access Token you can get user data through the user_info endpoint https://talao.co/api/v1/user_info.

.. code::

   curl -H "Authorization: Bearer your_access_token" https://talao.co/api/v1/user_info

Return is JSON (example) :

.. code-block:: JSON

  {
    "sub": "did:talao:talaonet:81d8800eDC8f309ccb21472d429e039E0d9C79bB",
    "given_name": "Thierry",
    "family_name": "Thevenet",
    "gender": null,
    "email": "thierry.thevenet@talao.io",
    "phone": null,
    "resume": {}
  }

Decode JWT
**********

JWT can be decoded with Talao RSA public key . Audience is your client_id, algorithm is RS256

.. code-block:: TEXT

  -----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3fMFBmz2y31GlatcZ/ud\nOL9CmCmvtde2Pu5ZggILlBD6yll+O10eH/8J8wX9OZG+e5vAgT5gkzo247ow4auj\niOA87V9bdexI7nUiD5qjdKTcIofJiDkmCIgF/UqwQ7dfyl1jWDVB1CnfAqkL0U2j\nbU+Nb/y1M1/oTFoid+trRFbhM+0awr06grh4viGJ0i5oVCcuybcDuP7bwNiZD1FP\n85L/hlfXvJs+oz6K+583leu1hj7wFnWSv0jgeYHkdgoG3rSKlbTxt+98dTu3Hy8s\nePl9O/2WKi6SSH0wpR+FqaBULAAyWd0cj5mjBLYoUiGP7qyIU5/9Z+pVf+L7SO7t\nlQIDAQAB\n-----END PUBLIC KEY-----

JWT  payload example :

.. code-block:: JSON

  {
  "iss": "https://talao.co",
  "aud": [
    "iPSoIWDI4shQ0dEG86ZpSFdj"
  ],
  "iat": 1603895896,
  "exp": 1603899496,
  "auth_time": 1603895896,
  "nonce": "64867",
  "at_hash": "uAaDX0YA4NnMkO6fW8-7nw",
  "sub": "did:talao:talaonet:81d8800eDC8f309ccb21472d429e039E0d9C79bB",
  "given_name": "Thierry",
  "family_name": "Thevenet",
  "gender": null,
  "email": "thierry.thevenet@talao.io"
  }


OAuth 2.0 Authorization code flow
----------------------------------

For your users, this flow includes a consent screen that describes through 'scopes' the actions that the user allows to your application.
For example, when the user logs in, they might be asked to accept or reject a partnership.

You request an access to these functionalities using the scope parameter, which your app includes in its request.

Below list of scopes  :

* partner : company requests partnership : If accepted partnership allows to exchange private data without any new authorization. Your company will be added to the user's partner list. Further data access will be available through Client Credentials flow.
* referent : company requests to be appointed as a referent. If accepted your company will be allowed to issue certificatess without any new authorization.
* delete_certificate : user deletes certificate
* remove_partner : user removes partner from partner's list
* remove_referent : user removes referent from referent's list

Step 1, ask for a grant code with your scope list.

.. code::

   https://talao.co/api/v1/authorize?response_type=code&client_id=your_client_id&scope=your_scopes


Step 2, with the grant code, connect to the token endpoint https://talao.co/api/v1/auth/token to get an Access Token. You will need your client_secret.

.. code::

   curl -u your_client_id:your_secret_value -XPOST https://talao.co/api/v1/oauth/token -F grant_type=authorization_code


Step 3, with the Access Token you can acces an endpoint

.. code::

   curl -H "Authorization: Bearer your_access_token" https://talao.co/api/v1/endpoint  your_json_data


Endpoint : https://talao.co/api/v1/company_request
**************************************************

To request a partnership or to be added as referent (scope 'referent or 'partner' is required). No data to provide.

.. code::

   curl -H "Authorization: Bearer your_access_token" https://talao.co/api/v1/company_request

JSON return :

.. code-block:: JSON

  {
   "partnernship_in_identity": "Pending",
   "partnership_in_partner_identity": "Authorized",
   "referent": false
  }

partnership_in_identity :

* Authorized : your company has requested a partnership or accepted the partnership.
* Pending : user is waiting for your decision to accept or reject his request for partnership.
* Removed : your company removed the partnership.
* Unknown : no partnership.
* Rejected : your company refused the user request for partnership.


partnership_in_partner_identity :

* Authorized : user has requested a partnership or accepted your request.
* Pending : user has received your request for partnership but still pending.
* Rejected : user refused your request.
* Removed : user removed the partnership.
* Unknown : no partnership.


referent :

* False/True : is your company in the user's referent list.

.. note:: A partnership is effective when both partnership_in_partner_identity and partnership_in_identity are "Authorized".


Endpoint : https://talao.co/api/v1/user_identity_management
***********************************************************


OAtth 2.0 Client Credentials Flow
----------------------------------

This flow allows your company to access functionalities previously authorized by users (as referent and/or partner) and to manage your own company identity.

to manage other person Identity :

*   https://talao.co/api/v1/issue_experience : to issue experience certificates to a person after your company has been appointed as a referent
*   https://talao.co/api/v1/issue_skill : to issue skill certificates to a person after your company has been appointed as a referent
*   https://talao.co/api/v1/issue_recommendation : to issue recommendation certificates to a person after your company has been appointed as a referent
*   https://talao.co/api/v1/create_person_identity : to create an identity for a person

to manage other company Identity :

*   https://talao.co/api/v1/create_company_identity : to create an identity for a company
*   https://talao.co/api/v1/issue_agreement : to issue agreement certificates to a company after your company has been appointed as a referent
*   https://talao.co/api/v1/issue_reference : to issue reference certificates to a person after your company has been appointed as a referent

to manage your own Identity :

*   https://talao.co/api/v1/client_identity_management : to add/remove a referent to your company's referent list or to request/reject a partnership
*   https://talao.co/api/v1/get_status : to get referent and partner status with a user


Using the Client Credentials Flow is straightforward - simply issue an HTTP GET against the token endpoint with both your client_id and client_secret set appropriately to get the Access Token :
Scope is required.

.. code::

  $ curl -u your_client_id:your_secret_value -XPOST https://talao.co/api/v1/oauth/token -F grant_type=client_credentials -F scope=your_scope

To call an endpoint :

.. code::

  $ curl -H "Authorization: Bearer your_access_token" -H "Content-Type: application/json" https://talao.co/api/v1/endpoint   your_json_data

Your Access Token will be live for 3000 seconds.

Endpoint : https://talao.co/api/v1/create_person_identity
**********************************************************

Create an Identity for a user.
Your company is appointed as a referent to issue certificates to this user.
Your company is apointed as a partner to access all data without any new user authorization.
User Identity username/password are sent by email to user.
Return JSON with did (sub) and username


.. warning:: As your company has an access to all user data, you should give users access to their identity in order them to manage authorizations by themselves.


Create a new identity :

.. code::

  $ curl -X POST https://talao.co/api/v1/create_person_identity \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"firstname":"jean", "lastname":"pascalet", "email":"jean.pascalet@talao.io"}'

JSON Response

.. code-block:: JSON

  {
    "did": "did:talao:talaonet:b8a0a9eE2E780281637bd93C13076cc5E342c9aE",
    "username" : "jeanpascalet",
    "firstname": "jean",
    "lastname": "pascalet",
    "email": "jean.pascalet@talao.io"
  }

Endpoint : https://talao.co/api/v1/issue_experience
***************************************************

Issue an experience certificate to a user.
Company must be allowed to issue experience certificate (scope = reference).
Company must be a in the user's referent list.

Issue an experience certificate :

.. code::

  $ curl -X POST https://talao.co/api/v1/issue_experience  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"did" : "did:talao:talonet:2165165", "certificate": JSON_certificate}'

Example of a JSON_certificate :

.. code-block:: JSON

  {
    "title" : "Chef de projet Blockchain",
    "description" : "Conception et realisation d un prototype Ethereum d un suivi de production",
    "start_date" : "2018/02/22",
    "end_date" : "2019/01/25",
    "skills" : ["Ethereum", "Solidity"],
    "score_recommendation" : 2,
    "score_delivery" : 3,
    "score_schedule" : 4,
    "score_communication" : 4,
  }

JSON return :

.. code-block:: JSON

  {
    "link": "https://talao.co/certificate/?certificate_id=did:talao:talaonet:81d8800eDC8f309ccb21472d429e039E0d9C79bB:document:12",
    "type" : "experience",
    "title" : "Chef de projet Blockchain",
    "description" : "Conception et ralisation d un prototype Ethereum d un suivi de production",
    "start_date" : "2018-02-22",
    "end_date" : "2019-01-25",
    "skills" : ["Ethereum", "Solidity"],
    "score_recommendation" : 2,
    "score_delivery" : 3,
    "score_schedule" : 4,
    "score_communication" : 4,
    "manager" : "Director",
    "reviewer" : "",
    "logo" : "QmRgLUZbLfRR7hW4CB7tqTFrjrfXxVUaP3XnNjC5D5QzT",
    "signature" : "QmHT7UZbLfRR7hW4CB7tqTFrjrfXxVUaP3XnNjC5D5Qzza",
    "ipfs_hash" : "QmH456ab656446564f",
    "transaction_hash" : "46516871335453AB354654CF551651"
  }


Endpoint : https://talao.co/api/v1/get_status
*********************************************

Get the referent and partnership status of a user.

.. code::

  $ curl -X POST https://talao.co/api/v1/get_status  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"did" : "did:talao:talaonet:fA38BeA7A9b1946B645C16A99FB0eD07D168662b"}'


JSON return : same as endpoint https://talao.co/api/v1/company_request


Endpoint : https://talao.co/api/v1/issue_reference
***************************************************

Issue an experience certificate to a company.
Company must be allowed to issue reference certificate (scope = reference).
Company must be a in the company's referent list.

Issue a reference certificate :

.. code::

  $ curl -X POST https://talao.co/api/v1/issue_reference  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"did" : "did:talao:talonet:2165165", "certificate": JSON_certificate}'

Example of a JSON_certificate :

.. code-block:: JSON

  {
    "project_title" : "Ligne de production moteur NFG-1000",
    "project_description" : "Conception, réalisation et installation d'une nouvelle ligne de production",
    "project_budget" : "2000000",
    "project_staff" : "12",
    "project_location" : "Bordeaux",
    "start_date" : "2019-02-22",
    "end_date" : "2020-01-25",
    "competencies" : ["CATIA V6",],
    "score_recommendation" : 4,
    "score_delivery" : 3,
    "score_schedule" : 4,
    "score_communication" : 4,
    "score_budget" : 4,
   }
