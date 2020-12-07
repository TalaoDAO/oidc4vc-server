
Talao Connect API
==================

The Talao API server is an OpenID Provider for decentralized self-sovereign Identity.

Talao Connect APIs can be used for authentication, identification, claims issuance and more generally for Identity management.
For instance in the Human Resource sector it is an easy way to get reliable data about Talents and a powerfull and secure tool for onbarding user while keeping their data safe.

Those API do not provide basic account setup (details, signature, logo ...) which are available through the web platform https://talao.co .

Standard use cases for APIs are :

* Issue claims (certificates, diplomas, agreements, ...) to persons, companies and all sorts of organizations.
* Authenticate users who have their own Decentralized Identity.
* Create decentralized Identities for others.
* Strenghen an employer brand with latest technology features like Blockchain Resume, Decentralized Identity,...

We use OpenID Connect Autorization Code flow for authentification and OAuth 2.0 Authorization code flow and Client Credentials flow to manage user access to their identity.

Contact us relay-support@talao.io to open your Company Identity and receive your application granted permissions to use those APIs.

From the OIDC and OAuth 2.0 perspective :

* "Company" is the Client application
* "User" is the Resource Owner, it maybe a Talent or another Company
* "Talao API server" is the Authorization Server/Resource Server

Resolver
********

The Resolver allows to get public data about and Identity. It provides for a username or a DID (Decentralized IDientifier) the asssociated DID or username, 
the Identity owner address and the RSA Public Key to authenticate the Identity.

.. code::

  curl  -H "Content-Type: application/json" -X POST https://talao.co/resolver/  -d '{"input" : "thierrythevenet"}'

Return is a JSON structure :

.. code-block:: 

  {
     "blockchain": "talaonet",
     "username": "thierrythevenet",
     "did": "did:talao:talaonet:81d8800eDC8f309ccb21472d429e039E0d9C79bB",
     "address": "0xE474E9a6DFD6D8A3D60A36C2aBC428Bf54d2B1E8",
     "workspace contract": "0x81d8800eDC8f309ccb21472d429e039E0d9C79bB",
     "RSA public key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAA....NOb9W\nEwIDAQAB\n-----END PUBLIC KEY-----"
  }

Resolver has a standard UI access at http://talao.co/resolver