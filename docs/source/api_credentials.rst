
OAuth 2.0 Client Credentials Flow
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
