

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
* user:manage:referent : this scope if accepted by user allows your company to add or remove referents on behalf of a user
* user:manage:data : this scope if accepted by user allows your company to add or remove data (account settings) on behalf of a user

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



Endpoint : POST https://talao.co/api/v1/user_uploads_signature
***************************************************************

To add a signature file to an Identity. Image format are jpeg, png, jpg. Image will be displayed with size in pixels : height="150" width="200".

Scope required : user:manage:data

the Content-Type of the Header of the POST request will be multipart/form-data.

.. code::

  $ curl -X POST https://talao.co/api/v1/user_accepts_company_referent  \
  -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9"  \
  -H "Content-Type : multipart/form-data" \
  -F "data=@signature.png"

JSON return :

.. code-block:: JSON

  {
   "hash": "QmNr71LjJPGUYKASinx2R5u63Zpmj8ZUqniFxHhqqHBujh"
  }


Endpoint : POST https://talao.co/api/v1/user_uploads_logo
************************************************************

Same as prevous one with logo. Image will be displayed with size in pixels : height="200" width="200".



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
