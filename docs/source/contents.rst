Overview
========

Talao markets its professional data certification solution on the Ethereum Blockchain to Talents, Companies and other organizations such as Schools or Training Centers.

The Talo protocol is based on a Decentralized IDentity focused on professional data. Talents and Companies are the owners of their data.
No centralized operator can decide to update or delete data. No one can access to encrypted Data.

Main differences with other certificates solutions are :    

	- Certificate Data are tamper proof and tracable.
	- Issuers are identified.
	- Recipents are identified.
     

Objectives
----------

For Talent, it is the opportunity to use a new technology to get tamper proof professional certificates while keping the ownership of their data.
Those certificate can be displayed anywhere on digital plateforms, social media, websites,etc. They provide to third parties reliable data about professional experiences, skills, education.

For Companies, the issuance of certificates on the blockchain has several interests:

  - Attracting new Talents by allowing them to value the experience they will have with the company (including during the recruitment process), and thus their future employability
  - Spreading the image of an innovative and modern company through the use of blockchain technology, which is adopted above all by the younger generations
  - Mastering what the Talents say about their missions and their activities in the company, and in particular avoiding the dissemination of confidential, sensitive or erroneous information
  - Valuing their own Talents externally, for example with their clients, by presenting them with CVs with certificates signed by former clients. This is particularly relevant for service companies.


Talao Professional Identity Relay
---------------------------------

The Talao Professional Identity Relay (http://talao.co:5000) is a website available for users (Individuals or Companies) to manage their Identity. 
The objective of this centralized platform is to simplify the onboarding process which is so far quite difficult for non technical experts.

.. note:: Depending on user choice the Talao Professional Identity Relay will have parts of information about cryptographic keys. Read more on :doc:`/privacy`.  


Dynamic Password
----------------

The Talao Relay uses dynamic passwords – machine generated, random numbers that are used once to authenticate. Every time an end user wants to login, 
instead of entering their usual static password every time, they would simply input a unique, machine generated password.
This dynamic password is received on the user's Email provided for registration (Authentificaton Email).

Dynamic passwords are convenient because they don’t have to be remembered, and because the password is never the same, they serve as a major roadblock for hackers
who may be looking to break into user accounts.


Distributed Identity vs Centralized
-----------------------------------
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
