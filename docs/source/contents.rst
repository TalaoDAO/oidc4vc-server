Overview
========

What is it for ?
----------------

This web applicaton (named "Talao Relay") is a professional data certification solution on the Ethereum Blockchain for Talents, Companies and other organizations such as Schools or Training Centers.
It is for everyone the opportunity to use a new technology to get tamper proof professional certificates while keping the ownership of their data.

Those certificates can be displayed anywhere on digital plateforms, social medias, websites, etc. They provide to third parties reliable data about professional experiences, skills, education.
The Talao protocol is based on a Decentralized IDentity focused on professional data.

Differences with other certificates solutions are :    

  - You own your data for your lifetime.
  - No private operators or government agencies can decide to update or delete your data.
  - No one can access your encrypted data without your permission.
  - No storage costs, you only pay Blockchain fees to update your data.
  - Certificates are tamper proof and tracable.
  - Issuers are identified.
     

For Companies, the issuance of certificates on the Blockchain has several interests:

  - Attracting new Talents by allowing them to value the experience they will have with the company (including during the recruitment process), and thus their future employability
  - Spreading the image of an innovative and modern company through the use of blockchain technology, which is adopted above all by the younger generations
  - Mastering what the Talents say about their missions and their activities in the company, and in particular avoiding the dissemination of confidential, sensitive or erroneous information
  - Valuing their own Talents externally, for example with their clients, by presenting them with CVs with certificates signed by former clients. This is particularly relevant for service companies.


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


Decentralized Identity vs Centralized
-------------------------------------
Current architectures to validate, certify, and manage identities are based on centralized, top-down approaches that rely on trusted authorities and third-party operators. 
Talao approaches the problem of digital identity starting from a human rights perspective, with a focus on professional data. 

We assert that individual persons must be allowed to manage their personal information in a multitude of different ways in different contexts and that to do so, 
each individual must be able to create multiple unrelated identities.

Our proposal for digital identity differs from others in its approach to trust in that we do not seek to bind credentials to each other or to a mutually trusted authority to achieve strong non-transferability. Because the system does not implicitly encourage its users to maintain a single aggregated identity that can potentially be constrained or reconstructed against their interests, individuals and organizations are free to embrace the system and share in its benefits.


Decentralized IDentifiers (DID)
-------------------------------

[`w3.org <https://www.w3.org/TR/did-core/>`_] "Decentralized identifiers (DIDs) are a new type of identifier that enables verifiable, decentralized digital identity. A DID identifies any subject (e.g., a person, organization, thing, data model, abstract entity, etc.) that the controller of the DID decides that it identifies.
These new identifiers are designed to enable the controller of a DID to prove control over it and to be implemented independently of any centralized registry, identity provider, or certificate authority.
DIDs are URLs that associate a DID subject with a DID document allowing trustable interactions associated with that subject.
Each DID document can express cryptographic material, verification methods, or service endpoints, which provide a set of mechanisms enabling a DID controller to prove control of the DID. Service endpoints enable trusted interactions associated with the DID subject.
A DID document might contain semantics about the subject that it identifies. A DID document might contain the DID subject itself (e.g. a data model)."

Credits
-------

Thanks to the awesome Ethereum community which provide us with great tools, Solidity code and inspiration.
Special thanks to `OriginProtocol <https://www.originprotocol.com>`_ for their implementation of `ERC 725 and ERC 735 <https://erc725alliance.org/>`_, which we use with slight modifications.

Thanks to the NLTK team and community for their Natural Language Programming work we used in the Dashboard panel is based on the python librairy `NLTK <https://www.nltk.org/>`_.
For more information Bird, Steven, Edward Loper and Ewan Klein (2009), Natural Language Processing with Python. O’Reilly Media Inc.
