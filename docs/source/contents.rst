Overview
========

Talao markets its professional data certification solution on the Ethereum Blockchain to Talents, Companies and other organizations such as schools or training centers.

The Talo protocol is based on a Decentralized IDentity focused on professional data. Talents and Companies are the only owner of their data. No centralized operator can decide the use or update of your data.


Objectives
----------

For Companies and Talents, the issuance of certificates on the blockchain with Talao protocol has several interests:

- Attracting the new talents by allowing them to value the experience they will have with the company (including during the recruitment process), and thus their future employability
- Spreading the image of an innovative and modern company through the use of blockchain technology, which is adopted above all by the younger generations
- Mastering what the talents say about their mission and their activity in the company, and in particular avoiding the dissemination of confidential, sensitive or erroneous information
- Valuing their own talents externally, for example with their clients, by presenting them with CVs with certificates signed by former clients. This is particularly relevant for service companies.


Talao Professional Identity Relay
---------------------------------

The Talao Professional Identity Relay (http://talao.co:5000) is an intermediary between users and their Identity. 
The objective of this centralized platform is to simplify the onboarding process which is so far still quite difficult for non technical experts.

.. note:: Depending on user choice the Talao Professional Identity Relay will have parts of information about cryptographic keys. Read more on :doc:`/privacy`.  


Distributed Identity vs Centralized
-----------------------------------
Current architectures to validate, certify, and manage identity are based on centralized, top-down approaches that rely on trusted authorities and third-party operators. 
We approach the problem of digital identity starting from a human rights perspective, with a primary focus on identity systems in the developed world. 

We assert that individual persons must be allowed to manage their personal information in a multitude of different ways in different contexts and that to do so, 
each individual must be able to create multiple unrelated identities.

Therefore, we first define a set of fundamental constraints that digital identity systems must satisfy to preserve and promote privacy as required for individual autonomy.

With these constraints in mind, we then propose a decentralized, standards-based approach, using a combination of distributed ledger technology and thoughtful regulation,
to facilitate many-to-many relationships among providers of key services. 
 
Our proposal for digital identity differs from others in its approach to trust in that we do not seek to bind credentials to each other or to a mutually trusted authority to achieve strong non-transferability. Because the system does not implicitly encourage its users to maintain a single aggregated identity that can potentially be constrained or reconstructed against their interests, individuals and organizations are free to embrace the system and share in its benefits.

Decentralized IDentifiers (DID)
-------------------------------

[`w3.org <https://www.w3.org/TR/did-core/>`_] "Decentralized identifiers (DIDs) are a new type of identifier that enables verifiable, decentralized digital identity. A DID identifies any subject (e.g., a person, organization, thing, data model, abstract entity, etc.) that the controller of the DID decides that it identifies.
These new identifiers are designed to enable the controller of a DID to prove control over it and to be implemented independently of any centralized registry, identity provider, or certificate authority.
DIDs are URLs that associate a DID subject with a DID document allowing trustable interactions associated with that subject.
Each DID document can express cryptographic material, verification methods, or service endpoints, which provide a set of mechanisms enabling a DID controller to prove control of the DID. Service endpoints enable trusted interactions associated with the DID subject.
A DID document might contain semantics about the subject that it identifies. A DID document might contain the DID subject itself (e.g. a data model)."
