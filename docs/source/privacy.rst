
Privacy
=======

Overview about encryption and privacy
-------------------------------------

An Identity is a smart contract on the Ethereum Blockchain, it is defined by its own Ethereum address. 
This smart contract is created at setup by his owner (person or company) through the owner Ethereum address and his associated private key.

In order to get strong privacy, the Talao protocol uses 2 specific AES encryptions keys (one for private data, one for secret data) to encrypt user data.
Those 2 keys are stored within the Identity encrypted with a RSA key. 

Consequently for Individuals there are several ways of using the Relay platform depending of who can access to the owner Ethereum private key and his RSA key :

   - If the Identity has been setup by the Relay itself, the Relay has a copy of the Ethereum Private key and RSA key. They are stored on a Centralized server. 
     We say that the Identity is **managed on behalf of the owner**. All services are available through the Relay which is a classic webserver application. 

   - If the Identity has been setup by the user externally (see `freepdapp <https://freedapp.io/>`_), the Relay is  **Fully or partially activated** (with ERC725 Keys) to be able to sign transactions on behalf of the owner.
     In this case the Relay does not have a copy of the Ethereum private and RSA keys but the user has limited access to the Relay services.
     For instance certificate issuance and Partnership services are not available. 
    
   - An other solution is to do a **Change of ownership** : The Identity is setup by the Relay and later on the Identity is transfered to an Ethereum address setup secretly by the owner. 
     In this case the Relay does not have a copy of the Ethereum private key. This solution has the advantage to not requiring the setup of an Identity externally.
     Certificate issuance services are not available.

For information company Identities are always managed on behalf of the company as they usally do not want to be involved in thoses tasks.


.. note::  For users who mainly want to request certificates, the easiest solution is to get an Identity **managed on behalf of the owner** by Talao.


List of Relay Services : 

   - Request certificates,
   - Edit personal settings,
   - Edit resume (Experience, Education, ...)
   - Issue certificates,
   - Manage Partnership,
   - Manage Alias,
   - Manage Referent,
   - Manage White List,
   - Store files. 


+--------------------------------+-----------------+----------------+-------------------------------------------------------+
|             Mode               |     Priv.key    |     RSA Key    |   Services and Relay rights                           |
+================================+=================+================+=======================================================+
| Managed on behalf of the owner |    - Relay has  |  - Relay has   |   - User can access all services through Relay        |        
|                                |      copy       |    copy        |   - Relays has acces to all data                      |
+--------------------------------+-----------------+----------------+-------------------------------------------------------+
| Fully activated (Key=1)        |     - Secret    |   - Secret     |   - User cannot issue certificates                    |    
|                                |                 |                |   - Relay can edit personal settings and resume       |
|                                |                 |                |   - Relay can add Referent and Alias                  |
|                                |                 |                |   - Relay can issue public data                       |
+--------------------------------+-----------------+----------------+-------------------------------------------------------+
| Partially activated (key=20002)|     - Secret    |    - Secret    |   - User cannot issue certificates                    |    
|                                |                 |                |   - User cannot edit Resume and  personal settings    |
|                                |                 |                |   - User cannot add Alias and Referent                |
|                                |                 |                |   - User cannot manage partnership                    |
|                                |                 |                |   - Relay  can edit Resume                            |
+--------------------------------+-----------------+----------------+-------------------------------------------------------+
| Change of ownership            |      - Secret   |   - Relays has |   - User cannot issue certificates                    |    
|                                |                 |     copy       |   - Relays has access to all data                     |
+--------------------------------+-----------------+----------------+-------------------------------------------------------+



Two-factors authentification
----------------------------
For security this web application uses a two-factors authentification protocol.

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

Private and Secret data are protected by AES encrypted keys which are themselves stored encrypted on Ethereum with an RSA key.

.. warning:: Those keys are determined at Identity creation and cannot be changed later on. 

At creation users can decide what level of privacy for :

- Personal data (except for firstname and lastname which are always required and public)
- File (Data store).

Experiences, Certificates and Education are always Public data.


Public Data is available for anybody :

   - For Talents, by default Firstname and Lastname are Public.
   - For Companies, by default all profil data are Public.

Private Data are only available for your Partners. Read more on :doc:`/resume` .

   - By default for Talents, Contact Email and Contact Name are private.

Secret Data are only available for users.

   - Users can store encypted data on decentralized support as IPFS through this option.
   - Authentification Email is always secret (Relay keeps a copy of ths email for authentification)



