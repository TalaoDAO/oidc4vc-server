
Privacy
=======

Overview about encryption and privacy
-------------------------------------

An Identity is a smart contract on the public Ethereum Blockchain or a private Blockchain (POA). Identity is defined by its own Ethereum address.
This smart contract is created at setup by his owner (person or company) through the owner Ethereum address and his associated private key.

In order to get strong privacy, the Talao protocol uses 3 specific AES encryptions keys (one for public data, one for private data, one for secret data) to encrypt user data.
2 keys (private and secret) are stored within the Identity encrypted with a RSA key, the third one for public data is available within the open code.
User data are mainly stored on a decentralized file system IPFS.

Consequently for Individuals there are several ways of using the web platform depending of who can access to the owner Ethereum private key and his encryption keys :

   - If the Identity has been setup by the website https://talao.co, the website server is a **third party wallet**, it has a copy of the Ethereum Private key and RSA key. They are stored on a Centralized server. We say that the Identity is **managed on behalf of the identity owner**.
     All services are available through the website which is a classic web application.

   - If the Identity has been setup externally by a user (see `freepdapp <https://freedapp.io/>`_), the website is  **fully or partially activated** to act as an agent and sign transactions on behalf of the owner.
     In this case the server does not have a copy of the Ethereum private and RSA keys but the user has limited access to the website services.
     For instance certificate issuance and Partnership services are not available.

   - An other solution is to setup an identity through the website then later do a **Change of ownership** : Identity is setup by the website and later on the Identity is transfered to an Ethereum address setup secretly by the owner. 
     In this case the server does not have a copy of the Ethereum private key. This solution has the advantage to be easy and fast.
     Certificate issuance services will not be available but the identity will able to receive certificates from others.


.. note::  For users who mainly want to request certificates, the easiest solution is to get an Identity **managed on behalf of the owner** by Talao.



List of website services : 

   - Edit personal settings,
   - Edit resume (Experience, Education, ...)
   - Issue certificates,
   - Reqest certificates,
   - Manage Partnership,
   - Manage Alias,
   - Manage Referent,
   - Manage White List,
   - Invit user,
   - Store files. 



Two-factors authentification
----------------------------

If they do not have their smartphone one hand, user can acces their Identity with their username and paswword. In this case they have a limited access to their Identity but they can build 
their resume. For security we uses a two-factors authentification protocol for this type of authentication.

`Wikipedia <https://en.wikipedia.org/wiki/Multi-factor_authentication>`_ : "Multi-factor authentication is an authentication method in which a computer user is granted access only after successfully presenting two or more pieces of evidence (or factors) to an authentication mechanism: knowledge (something the user and only the user knows), possession (something the user and only the user has), and inherence (something the user and only the user is).
Two-factor authentication (also known as 2FA) is a type, or subset, of multi-factor authentication. It is a method of confirming users' claimed identities by using a combination of two different factors: 1) something they know, 2) something they have, or 3) something they are."

Dynamic passwords (named secret code) are random numbers that are used once to authenticate. Every time an end user wants to login, 
he enters his usual static password and a secret code sent in real time by Email or by short messages on the user's Phone.
The secret code lifetime is 3 minutes.

Dynamic passwords are convenient because they don’t have to be remembered, and because the password is never the same, they serve as a major roadblock for hackers
who may be looking to break into user accounts.

.. note:: By default at setup the static password is 'identity' and scret code are sent by email. Once logged, one can change the static password and choose sms to receive your secret code on your phone.





Data and privacy
----------------

Data are either public, private or secret data

Private and Secret data are protected by AES encrypted keys which are themselves stored encrypted on Ethereum with an RSA key. Public data are encrypted with an AES key stored within the code.

.. warning:: The private and secret keys are determined at Identity creation and cannot be changed later on. 

At creation users can decide what level of privacy for :

- Personal data (except for firstname and lastname which are always required and public)
- File (Data store).

Experiences, Certificates and Education are always Public data.

Public Data is available for anybody :

   - For Talents, by default Firstname and Lastname are Public.
   - For Companies, by default all profil data are Public.

Private Data are only available for your Partners. Read more on :doc:`/resume` .

Secret Data are only available for users.

   - Users can store encypted data on decentralized support as IPFS through this option.
   - Authentification Email is always secret (Relay keeps a copy of ths email for authentification)
   - By default for Talents, Email and phone are secret, used for authentification only.



