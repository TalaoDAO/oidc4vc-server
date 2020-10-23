
Talent Connect API
==================

Talent Connect APIs can be used for authentication, authorization and claims issuance.
For companies it is an easy way to get reliable data about Talents and a powerfull and secure tool for onbarding while keeping user's data safe.

Those API do not provide account setup (company details, signature, logo ...) which are available through the web platform https://talao.co .

Standard use cases for APIs are :

* Issue certificates to Talents.
* Setup a Talent onboarding process with a reliable source of data.
* Outsource Talent data.
* Strenghen an employer brand with latest technology features (Blockchain Resume,...).

We use OAuth2 Autorization Code flow and OAuth2 Client Credentials flow to manage those cases.
Contact us relay-support@talao.io to open your Company Identity and receive your application granted permissions to use those APIs

OAuth 2.0 Authorization Code flow
----------------------------------

For your users, the OAuth 2.0 authentication experience includes a consent screen that describes through 'scopes' the information that the user is releasing.
For example, when the user logs in, they might be asked to give your appication access to their email address, resume and basic account information.
You request access to this information using the scope parameter, which your app includes in its authentication request.

If no scope is provided, the flow is only used for authentification.

Scopes for data access are :

* profile (sub, given_name, family_name, gender,...)
* birthdate
* email
* phone
* resume : JSON resume see https://jsonresume.org/
* proof_of_identity

Those two other scopes allow special features through other client credentials flow and specific endpoints :

* private : Request authorization to access private data (partnership).
* certification : Request authorization to issue certificates.

To get a grant code for this flow, redirect your user to https://talao.co/api/v1/authorize with a subset of your scope list .
User will be asked to sign in with their Decentralized Identifier and to consent for your list of scopes.

Example :

.. code::

   https://talao.co/api/v1/authorize?response_type=code&client_id=your_client_id&scope=your_scopes

With the grant code, connect to the token endpoint https://talao.co/api/v1/auth/token to get an access token. You will need your client_secret.

.. code::

   curl -u your_client_id:your_secret_value -XPOST https://talao.co/api/v1/oauth/token -F grant_type=client_credentials -F scope=your_scopes

With the access token you can get Talent data through the user_info endpoint https://talao.co/api/v1/user_info.

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


OAuth 2.0 Client Credentials Flow
---------------------------------

For basic actions we offer OAuth 2.0 application access via the Client Credentials Flow.
Commonly referred to as "OAuth two-legged", this flow allows your application to call Talao's APIs  :

*   https://talao.co/api/v1/issue : to issue certificates depending on scopes (experience, skill, proof_of_identity, recommendation)
*   https://talao.co/api/v1/create : to create identity.
*   https://talao.co/api/v1/refer : to add a referent.
*   https://talao.co/api/v1/request_partner : to request a partnership.
*   https://talao.co/api/v1/reject_partner : to reject a partnership.


Using the Client Credentials Flow is straightforward - simply issue an HTTP GET against the token endpoint with both your client_id and client_secret set appropriately to get the access token :

.. code::

  $ curl -u your_client_id:your_secret_value -XPOST https://talao.co/api/v1/oauth/token -F grant_type=client_credentials -F scope=experience+skill

To call an endpoint :

.. code::

  $ curl -H "Authorization: Bearer your_access_token" https://talao.co/api/v1/endpoint   your_data

For test, get an access token with those credentials :

* client_id: vJENicdQO38y1pcVRQREeuoy
* client_secret: oMwwlIQRjz751loQHesGWIFmH6iVt7XmO0s1W3Vax1pdMUG5

.. code-block:: JSON

  $ curl -u vJENicdQO38y1pcVRQREeuoy:oMwwlIQRjz751loQHesGWIFmH6iVt7XmO0s1W3Vax1pdMUG5 -XPOST https://talao.co/api/v1/oauth/token -F grant_type=client_credentials -F scope=experience

Your access token is live for 3000 seconds.

https://talao.co/api/v1/create
*******************************

Create an Identity for others. You company is appointed as a referent to issue certificates.
Identity credentials are sent by email to Talent.

Example :

.. code::

  $ curl -X POST https://talao.co/api/v1/create  \
   -H "Authorization: Bearer rp9maPLRQEJ3bviGwTMPXvQdcx8YlqONuVDFZSAqupDdgXb9" \
   -H "Content-Type: application/json" \
   -d '{"firstname":"jean", "lastname":"pascalet", "email":"jean.pascalet@talao.io"}'

Response

.. code-block:: JSON

  {
    "status" : "900",
    "did": "did:talao:talaonet:__TEST__",
    "username" : "jeanpascalet",
    "firstname": "jean",
    "lastname": "pascalet",
    "email": "jean.pascalet@talao.io"}
  }

with status :

* 900 : Ok
* 910 : Failed, client has no identity
* 920 : Failed, creation identity (Ethereum transaction failed)
* 930 : Failed, incorrect request (data missing)

Try for test with your access token :

.. code-block:: JSON

  $ curl -X POST https://talao.co/api/v1/create  -H "Authorization: Bearer your_acces_token" -H "Content-Type: application/json" -d '{"firstname":"jean", "lastname":"pascalet", "email":"jean.pascalet@talao.io"}'


https://talao.co/api/v1/issue
******************************

to be done

https://talao.co/api/v1/request_partner
***************************************

to be done


https://talao.co/api/v1/reject_partner
***************************************

to be done