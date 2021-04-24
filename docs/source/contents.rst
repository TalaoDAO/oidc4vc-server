Overview
========

What is Talao ?
---------------

Talao is a solution to manage a professional Self Sovereign Digital Identity.

Traditional architectures to validate, certify, and manage professional data are based on centralized, top-down approaches that rely on third-party private operators.
Unfortunately these solutions often lead to inappropriate use of personal data and hacks. Whatever the GDPR could impose to private operators, the fact is that our data
are stored on their servers and they will ultimately do what they want with our data.

Talao approaches this issue starting from a user perspective through a Blockchain Decentralized IDentity (DID) focused on professional data :

  - You own your data for your lifetime.
  - No one can access your data without your permission.
  - No storage costs.
  - Claims are verifiables credentials, they are tamper proof, trackable and signed by the issuer.
  - Credentials issuers are identified.

Talao allows Professional Identities for Talents, Companies and claims issuers such as Schools or Training Centers.
It is for everyone the opportunity to use a new technology to get tamper proof professional data while keeping the ownership of those data.

Identities with their verifiable credentials can be displayed anywhere on digital platforms : social medias, websites, Job boards, etc. They provide to third parties reliable data about professional experiences, skills and education.

Terminology : in this document we will consider "Self Sovereign Identity" as an equivalent to 'Decentralized IDentity'.


How does Talao work ?
---------------------

That is quite simple, first you download the crypto wallet app of your choice on your smarphone, then you scan the QR Code displayed on your desktop and you are in !

Under the hood, Talao is based on Ethereum smart contracts Identities. Smart contract Identities are like digital vault where you can store your data as Digital ID, diplomas, professional certificates, business contracts, pay slips,...
Each individual or company has its own private key to access and update its Identity.

Thanks to cryptographic algorithms those private keys are used to sign messages sent by the Identity owner to the Blockchain nodes (Internet servers).
If someone wants to update its data, he/she will sign a message with a private key and send it to all Blockchain nodes.
Each server will check the signature, update data then compare them to other server copies. As those data are duplicated on multiple servers, no one can alone hack the Identity.

This Talao web application https://talao.co is a relay to access Self Sovereign Identities with a simple User Interface and automated processus.
From a blockchain perspective, the Identity owner is the Ethereum account attached to the the smartphone crypto wallet.

What are Verifiable Credentials ?
-----------------------------------

As defined in the current Credentials specification of W3C1 :

"In the physical world, a credential might consist of:

  * Information related to identifying the subject of the credential (for example, a photo, name, or identification number)
  * Information related to the issuing authority (for example, a city government, national agency, or certification body)
  * Information related to the type of credential this is (for example, a Dutch passport, an American driving license, or a health insurance card)
  * Information related to specific attributes or properties being asserted by the issuing authority about the subject (for example, nationality, the classes of vehicle entitled to drive, or date of birth)
  * Evidence related to how the credential was derived
  * Information related to constraints on the credential (for example, expiration date, or terms of use).

A verifiable credential can represent all of the same information that a physical credential represents. The addition of technologies, such as digital signatures, makes verifiable credentials more tamper-evident and more trustworthy than their physical counterparts. "


More information available :


  * https://www.w3.org/TR/vc-data-model/


What are Decentralized IDentities (DID) ?
------------------------------------------

The Decentralized Digital Identity concept is based on the use of Decentralised Identifiers. As defined in the current DID
specification of W3C1 :

“Decentralized Identifiers (DIDs) are a new type of identifier for verifiable, "self-sovereign" digital
identity. DIDs are fully under the control of the DID subject, independent from any centralized
registry, identity provider, or certificate authority. DIDs are URLs that relate a DID subject to means
for trustable interactions with that subject. DIDs resolve to DID Documents — simple documents
that describe how to use that specific DID. Each DID Document may contain at least three things:
proof purposes, verification methods, and service endpoints. Proof purposes are combined with
verification methods to provide mechanisms for proving things. For example, a DID Document can
specify that a particular verification method, such as a cryptographic public key or pseudonymous
biometric protocol, can be used to verify a proof that was created for the purpose of authentication.
Service endpoints enable trusted interactions with the DID controller.”

Furthermore eIDAS regulations now in place in Europe are taking the opportunity to include Self Sovereign Identiy technologies to expand security
and data protection (see the SSI-eIDAS Bridge project launched by EU)..


More information available :


  * https://www.w3.org/TR/did-core/
  * https://identity.foundation/
  * https://ec.europa.eu/futurium/en/system/files/ged/eidas_supported_ssi_may_2019_0.pdf
  * https://joinup.ec.europa.eu/collection/ssi-eidas-bridge/about


What blockchains support does Talao use ?
-----------------------------------------

The Talao solution is available with different public Blockchain vs did method :

  * Ethereum with the did:ethr method, see https://github.com/uport-project/ethr-did-registry for details.
  * Tezos with the did:tz with curve Ed25519 method, see https://did-tezos.spruceid.com/

We also use :

  * did:key with curve secp256k1 for specif use cases, see https://w3c-ccg.github.io/did-method-key/
  * did:web (did:wab:talao.io:...) with curve secp256k1 and a RSA256 key see https://w3c-ccg.github.io/did-method-web/


Credits
-------

Thanks to the Ethereum community which provide us with great tools, Solidity code and inspiration.

Special thanks to `Spruce <https://www.spruceid.com/>`_ for their implementation of SSI and its wide JSON_LD signing suite.

Special thanks to `OriginProtocol <https://originprotocol.com/>`_ for their implementation of `ERC 725 and ERC 735 <https://erc725alliance.org/>`_, which we use with slight modifications.
