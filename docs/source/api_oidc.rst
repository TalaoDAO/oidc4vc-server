

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

JWT can be decoded with Talao RSA public key . Audience is 'did:talao:talaonet:EE09654eEdaA79429F8D216fa51a129db0f72250', algorithm is RS256

Talao RSA key :

.. code-block:: TEXT

  -----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3fMFBmz2y31GlatcZ/ud\nOL9CmCmvtde2Pu5ZggILlBD6yll+O10eH/8J8wX9OZG+e5vAgT5gkzo247ow4auj\niOA87V9bdexI7nUiD5qjdKTcIofJiDkmCIgF/UqwQ7dfyl1jWDVB1CnfAqkL0U2j\nbU+Nb/y1M1/oTFoid+trRFbhM+0awr06grh4viGJ0i5oVCcuybcDuP7bwNiZD1FP\n85L/hlfXvJs+oz6K+583leu1hj7wFnWSv0jgeYHkdgoG3rSKlbTxt+98dTu3Hy8s\nePl9O/2WKi6SSH0wpR+FqaBULAAyWd0cj5mjBLYoUiGP7qyIU5/9Z+pVf+L7SO7t\nlQIDAQAB\n-----END PUBLIC KEY-----

JWT  payload example :

.. code-block:: JSON

  {
  "iss": "did:talao:talaonet:EE09654eEdaA79429F8D216fa51a129db0f72250",
  "aud": ["did:talao:talaonet:EE09654eEdaA79429F8D216fa51a129db0f72250"],
  "iat": 1603895896,
  "exp": 1603899496,
  "auth_time": 1603895896,
  "nonce": "64867",
  "at_hash": "uAaDX0YA4NnMkO6fW8-7nw",
  "sub": "did:talao:talaonet:81d8800eDC8f309ccb21472d429e039E0d9C79bB",
  "given_name": "Thierry",
  "family_name": "Thevenet",
  "gender": null,
  "email": "thierry.thevenet@talao.io",
  }

