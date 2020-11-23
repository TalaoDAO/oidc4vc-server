
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

For your users (as a person), the OpenID Connect authentication experience includes a consent screen that describes through 'scopes' the information that the user is releasing.
For example, when the user logs in, they might be asked to give your appication access to their name, email address and basic account information.
You request access to this information using the scope parameter, which your app includes in its authentication request.

Scopes available
****************

Scopes for data access are standard OpenID Connect and specific Talao scopes :

* openid (required to get a JWT)
* profile (sub + given_name + family_name + gender)
* birthdate
* email
* phone
* address
* about : short user description
* resume (in progress on 11-17-2020) : for person identity only
* proof_of_identity (in progress on 11-17-2020)

.. note:: "sub" is the  Decentralized IDentier of the user (did). It always starts with "did:talao:".

Those data are available through an ID Token (JWT) and at the user_info endpoint with an Access Token.

For companies, there is only the "openid" scope available.

Process
*******

As defined by OIDC, 3 steps are required :

Step 1 : to get a grant code from user, redirect your user to https://talao.co/api/v1/authorize with a subset of your scope list .
User will be asked to sign in with his Identity username/password and to consent for your list of scopes.
scope "openid" is required to get a JWT.

Example :

.. code::

   https://talao.co/api/v1/authorize?response_type=code&client_id=your_client_id&scope=openid+profile&state=state&nonce=nonce



Step 2, with the grant code, connect to the token endpoint https://talao.co/api/v1/auth/token to get an Access Token and an ID Token. You will need your client_secret.

.. code::

   curl -u your_client_id:your_secret_value -XPOST https://talao.co/api/v1/oauth/token -F grant_type=authorization_code

If you only need user authentication, see further how to decode the JWT and get user data with server signature.


Step 3 : with the Access Token you can also get user data through the user_info endpoint https://talao.co/api/v1/user_info.

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

Talao RSA key :

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

There is no off-line access through Refresh Token but Talao partnership allows your company to get user data as long as the partnership is authorized.
However it means that you always need consent of an online user who signed-in Talao to issue or delete a certificate on his/her behalf.

.. note:: If your company needs to sign a certificate as an issuer, see further the Client Credential flow.


You request an access to these functionalities using the scope parameter, which your app includes in its request.

Below list of scopes  :

* user:manage:certificate : This scope if accepted by user allows your company to issue/delete certificates on behalf of a user
* user:manage:partner : This scope if accepted by user allows your company to request, accept or reject partnerships with all Identities on behalf of a user
* user:manage:referent : this is accepted by user scope allows your company to add or remove referents on behalf of a user
* user:manage:data : this is accepted by user scope allows your company to add or remove data (account settings) on behalf of a user

Step 1, ask for a grant code with your scope list, nonce, state.


.. code::

   https://talao.co/api/v1/authorize?response_type=code&client_id=your_client_id&scope=your_scopes&state=state&nonce=nonce


Step 2, with the grant code, connect to the token endpoint https://talao.co/api/v1/auth/token to get an Access Token. You will need your client_secret.

.. code::

   curl -u your_client_id:your_secret_value -XPOST https://talao.co/api/v1/oauth/token -F grant_type=authorization_code

Access Token is live 500 seconds.

Step 3, with the Access Token you can acces an endpoint

.. code::

   curl -H "Authorization: Bearer your_access_token" -H "Content-Type: application/json"  https://talao.co/api/v1/endpoint  -d your_json_data


Endpoint : POST https://talao.co/api/v1/user_issues_certificate
****************************************************************

Issue a certificate to an Identity(person or company) on behalf of a user.
certificate is "reference" or "agreement or "experience" or "skill" or "recommendation".
User must be in the identity's referent list.

Scope required : user:manage:certificate

Issue an agreement certificate :

.. code::

  $ curl -X POST https://talao.co/api/v1/user_issues_certificate  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"did_issued_to" : "did:talao:talonet:2165165", "certificate_type" : "agreement", "certificate": agreement_JSON_certificate}'

Example of a agreement_JSON_certificate :

.. code-block:: JSON

  {
    "registration_number" : "2020-11-31003",
    "title" : "IQ - ISO9001:2020",
    "description" : "Quality Management Process",
    "standard" : "ISO 9001",
    "date_of_issue" : "2020-11-01",
    "valid_until" : "2030-10-31",
    "location" : "Toulouse Bordeaux Paris",
    "service_product_group" : "Drone Serie production line",
  }


Issue a reference certificate :

.. code::

  $ curl -X POST https://talao.co/api/v1/user_issues_certificate  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"did_issued_to" : "did:talao:talonet:2165165", "certificate_type" : "reference", "certificate": reference_JSON_certificate}'

Example of a reference_JSON_certificate :

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


Endpoint : POST https://talao.co/api/v1/user_accepts_company_partnership
*************************************************************************

This is a straightforward process to build a partnership with an Identity. It combines your company request for a partnership and an authorization from Identity.

Scope required : user:manage:partner

.. code::

  $ curl -X POST https://talao.co/api/v1/user_accepts_company_partnership  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \

JSON return :

.. code-block:: JSON

  {
   "partnernship_in_identity": "Authorized",
   "partnership_in_partner_identity": "Authorized",
  }



Endpoint : POST https://talao.co/api/v1/user_updates_company_settings
*************************************************************************

To update identity settings of a company.
You can set 'name','contact_name','contact_email','contact_phone','website', 'about', 'staff', 'mother_company', 'sales', 'siren', 'postal_address'.
If no data is provided you get all current Identity settings.

Scope required : user:manage:data

.. code::

  $ curl -X POST https://talao.co/api/v1/user_updates_company_settings  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -d {"staff" : "6"}

JSON return :

.. code-block:: JSON

  {
    "name" : "Talao",
    "contact_name" : "Nicolas Muller",
    "contact_email" : "nicolas.muller@talao.io",
    "contact_phone" : "0607182594",
    "website" : "https://talao.co",
    "about" : "Talao focuses on professional identity management based on an extension of the ERC725 protocol, through a BtoB go-to-market strategy and a network of partners to develop compatibility with corporate IT systems.",
    "staff" : "6",
    "sales" : "3200000",
    "mother_company" : null,
    "siren" : "837674480",
    "postal_address" : null
  }


Endpoint : POST https://talao.co/api/v1/user_accepts_company_referent
**********************************************************************

To add your company in the Identity referent list

Scope required : user:manage:referent


.. code::

  $ curl -X POST https://talao.co/api/v1/user_accepts_company_referent  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" 

JSON return :

.. code-block:: JSON

  {
   "referent": true
  }



Endpoint : POST https://talao.co/api/v1/user_adds_referent
***********************************************************

To add an Identity to the user referent list

Scope required : user:manage:referent


.. code::

  $ curl -X POST https://talao.co/api/v1/user_adds_referent  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"did_referent" : "did:talao:talaonet:fA38BeA7A9b1946B645C16A99FB0eD07D168662b"}'


JSON return :

.. code-block:: JSON

  {
   "referent": true
  }


OAtth 2.0 Client Credentials Flow
----------------------------------

This flow allows your company to access functionalities previously authorized by users (as referent and/or partner) and to manage your own company identity.

To create Identities :

*   https://talao.co/api/v1/create_person_identity : to create an identity for a person (with partnership setup)
*   https://talao.co/api/v1/create_company_identity : to create an identity for a company (with parnership setup)

As a partner of an Identity

*   https://talao.co/api/v1/get_certificate_list : to get the list of all certificates of an Identity
*   https://talao.co/api/v1/get_certificate : to get certificate data

To manage your own Identity

*   https://talao.co/api/v1/issue_experience : to issue experience certificates to a person after your company has been appointed as a referent
*   https://talao.co/api/v1/issue_skill : to issue skill certificates to a person after your company has been appointed as a referent
*   https://talao.co/api/v1/issue_recommendation : to issue recommendation certificates to a person after your company has been appointed as a referent

*   https://talao.co/api/v1/issue_agreement : to issue agreement certificates to a company after your own company has been appointed as a referent
*   https://talao.co/api/v1/issue_reference : to issue reference certificates to a person after your company has been appointed as a referent

*   https://talao.co/api/v1/get_status : to get your own referent/partner status with an identity



Using the Client Credentials Flow is straightforward - simply issue an HTTP GET against the token endpoint with both your client_id and client_secret set appropriately to get the Access Token :

Scope are required for most endpoints.

.. code::

  $ curl -u your_client_id:your_secret_value -XPOST https://talao.co/api/v1/oauth/token -F grant_type=client_credentials -F scope=your_scope

To call an endpoint :

.. code::

  $ curl -H "Authorization: Bearer your_access_token" -H "Content-Type: application/json" https://talao.co/api/v1/endpoint   your_json_data

Your Access Token will be live for 3000 seconds.

Endpoint : POST https://talao.co/api/v1/issue_experience
*********************************************************

Issue an experience certificate to a user.
Company must be a in the user's referent list.

Scope required client:issue:experience.

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


Endpoint : POST https://talao.co/api/v1/create_person_identity
***************************************************************

Create an Identity for a user.
Your company is appointed as a referent to issue certificates to this user.
Your company is apointed as a partner to access all data without any new user authorization.
User Identity username/password are sent by email to user by defaul. Setup "send_email" to False to disable.
Return JSON with did (sub) and username.

Scope required : client:create:identity


.. warning:: As your company has an access to all user data, you should give users access to their identity in order them to manage authorizations by themselves.


Create a new person identity :

.. code::

  $ curl -X POST https://talao.co/api/v1/create_person_identity \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"firstname":"jean", "lastname":"pascalet", "email":"jean.pascalet@talao.io", "send_email" : false}'

JSON Response

.. code-block:: JSON

  {
    "did": "did:talao:talaonet:b8a0a9eE2E780281637bd93C13076cc5E342c9aE",
    "username" : "jeanpascalet",
  }


Endpoint : POST https://talao.co/api/v1/get_status
***************************************************

Get the referent and partnership status of a user with your company.

No scope required.

.. code::

  $ curl -X POST https://talao.co/api/v1/get_status  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"did" : "did:talao:talaonet:fA38BeA7A9b1946B645C16A99FB0eD07D168662b"}'


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


Endpoint : POST https://talao.co/api/v1/create_company_identity
****************************************************************

Create an Identity for a company.

Your company is appointed as a referent to issue certificates to this company.
Your company is apointed as a partner to access all data without any new user authorization.
User Identity username/password are sent by email to user by default,  Setup "send_email" to False to disable.
Return JSON with did (sub) and username.

Scope required : client:create:identity

.. warning:: As your company has an access to all user data, you should give users access to their identity in order them to manage authorizations by themselves.


Create a new identity :

.. code::

  $ curl -X POST https://talao.co/api/v1/create_company_identity \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"name":"NewIndus", "email":"jean.petit@newindus.io", "send_email" : false}'

JSON Response

.. code-block:: JSON

  {
    "did": "did:talao:talaonet:1a50a9eE2E780281637bd93C13076cc5E342c9aE",
    "username" : "newindus",
  }


Endpoint : POST https://talao.co/api/v1/issue_reference
********************************************************

Issue a reference certificate to a company.
Your company must be a in the company's referent list.

Scope required client:issue:reference

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



Endpoint : POST https://talao.co/api/v1/issue_agreement
********************************************************

Issue an agreement certificate to a company.
Your company must be in the company's referent list.

Scope required client:issue:agreement.

Issue an agreement :

.. code::

  $ curl -X POST https://talao.co/api/v1/issue_agreement_on_behalf  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"did" : "did:talao:talonet:2165165", "certificate": JSON_certificate}'

Example of a JSON_certificate:

.. code-block:: JSON

  {
    "registration_number" : "2020-11-31003",
    "title" : "IQ - ISO9001:2020",
    "description" : "Quality Management Process",
    "standard" : "ISO 9001",
    "date_of_issue" : "2020-11-01",
    "valid_until" : "2030-10-31",
    "location" : "Toulouse Bordeaux Paris",
    "service_product_group" : "Drone Serie production line",
  }


Endpoint : POST https://talao.co/api/v1/update_identity_settings
*****************************************************************


to be done



Endpoint : POST https://talao.co/api/v1/get_certificate_list
*************************************************************

Get the certificate list of an Identity.
Your company must be in the partner list.

certificate_type is : "experience", "skill", "agreement", "reference", "recommendation" or "all".

No scope required.

.. code::

  $ curl -X POST https://talao.co/api/v1/get_certificate_list  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"did" : "did:talao:talonet:2165165", "certificate_type": "reference"}'

Example of a JSON return :

.. code-block:: JSON

  {
    "certificate_list" : ["did:talao:talaonet:b8a0a9eE2E780281637bd93C13076cc5E342c9aE:document:6",
     "did:talao:talaonet:b8a0a9eE2E780281637bd93C13076cc5E342c9aE:document:12"]
  }

Endpoint : POST https://talao.co/api/v1/get_certificate
********************************************************

Get certificate data.
Your company must be in the partner list of the Identity.

No scope required.

.. code::

  $ curl -X POST https://talao.co/api/v1/get_certificate  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"certificate_id" : "did:talao:talaonet:81d8800eDC8f309ccb21472d429e039E0d9C79bB:document:12"}'

Example of a JSON return :

.. code-block:: JSON

  {
    "created": "2020-09-28 14:37:59",
    "data_location": "https://gateway.pinata.cloud/ipfs/QmWrsG2RSVmJFpLsfwHJttv4DC7RhdN5oxnsJ3k5EVh7cP",
    "description": "D\u00e9veloppement d'un application web d\u2019acc\u00e8s au protocole Talao permettant de mettre en oeuvre toutes les fonctionnalit\u00e9s du protocole et en particulier la gestion des cl\u00e9s priv\u00e9es, les partenariats et le cryptage des donn\u00e9es.",
    "doc_id": 12,
    "doctype": 20000,
    "doctypeversion": 2,
    "end_date": "2020-07-30",
    "expires": "Unlimited",
    "id": "did:talao:talaonet:81d8800eDC8f309ccb21472d429e039E0d9C79bB:document:12",
    "identity": {
      "address": "0xE474E9a6DFD6D8A3D60A36C2aBC428Bf54d2B1E8",
      "category": 1001,
      "id": "did:talao:talaonet:81d8800eDC8f309ccb21472d429e039E0d9C79bB",
      "workspace_contract": "0x81d8800eDC8f309ccb21472d429e039E0d9C79bB"
    },
    "ipfshash": "QmWrsG2RSVmJFpLsfwHJttv4DC7RhdN5oxnsJ3k5EVh7cP",
    "issuer": {
      "address": "0xEE09654eEdaA79429F8D216fa51a129db0f72250",
      "category": 2001,
      "id": "did:talao:talaonet:4562DB03D8b84C5B10FfCDBa6a7A509FF0Cdcc68",
      "name": "Talao",
      "workspace_contract": "0x4562DB03D8b84C5B10FfCDBa6a7A509FF0Cdcc68"
    },
    "logo": "Qme3vLZP6n8xNQj6qmL8piGyWVUhm4oYhmYXMqvczzN3Z1",
    "manager": "Director",
    "privacy": "public",
    "reviewer": "",
    "score_communication": "4",
    "score_delivery": "4",
    "score_recommendation": "4",
    "score_schedule": "4",
    "signature": "QmdMBfNut5GosNKrN73GhncbvkWqGLLNZJR5omEpAi9bkD",
    "skills": [
      "Blockchain",
      " Solidity",
      " Talao",
      " ERC725",
      " Python"
    ],
    "start_date": "2020-03-01",
    "title": "Project Leader",
    "topic": "certificate",
    "transaction_fee": 1000000000000,
    "transaction_hash": "0x0e4600aab98d171078509f51bb12b1d16def8574f57251c1fc94a9b5e7cf66ca",
    "type": "experience",
    "version": 1
  }

Use Case a tester
*****************

Use Case #1 : Une entreprise de formation professionnelle souhaite emettre des attestations de compétences sur la Blockchain pour ses clients (personnes physiques).

Use Case #2 : Un groupement qui dispose d'une base d'adherents (entreprises), souhaite proposer à ses membres de se faire "certifier" sur la Blockchain par des sociétés tiers pour lesquelles elles ont prestées.
les certificats sont ajoutés au profil des adhérents sur le portail du groupement. On peut sur ce portail rechercher les entreprises selon des criteres de compétence certifiés.
