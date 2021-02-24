Overview
========

What is Talao ?
---------------

Talao is a Blockchain protocol to manage a professional Self Sovereign Digital Identity.

Traditional architectures to validate, certify, and manage professional data are based on centralized, top-down approaches that rely on third-party private operators.
Unfortunately these solutions often lead to inappropriate use of personal data and hacks. Whatever the GDPR could impose to private operators, the fact is that our data
are stored on their servers and they will ultimately do what they want with our data.

Talao approaches this issue starting from a user perspective through a Blockchain Decentralized IDentity (DID) focused on professional data :

  - You own your data for your lifetime.
  - No one can access your encrypted data without your permission.
  - No storage costs.
  - Claims are verifiables, tamper proof and trackable.
  - Claims issuers are identified.

Talao allows Professional Identities for Talents, Companies and claims issuers such as Schools or Training Centers.
It is for everyone the opportunity to use a new technology to get tamper proof professional data while keeping the ownership of those data.

Identities with their verifiable claims can be displayed anywhere on digital platforms : social medias, websites, Job boards, etc. They provide to third parties reliable data about professional experiences, skills and education.

Terminology : in this document we will consider "Self Sovereign Identity" as an equivalent to 'Decentralized IDentity'.


How does Talao work ?
---------------------

Talao is based on Ethereum smart contracts Identities.

Smart contract Identities are like digital vault where you can store your data as Digital ID, diplomas, professional certificates, business contracts, pay slips,...
Each individual or company is given its own private key to access and update its Identity.

Thanks to cryptographic algorithms those private keys are only used to sign messages sent by the Identity owner to the Blockchain servers.
If someone wants to update its data, he/she will sign a message with a private key and send it to all Blockchain servers.
Each server will check the signature, update data then compare them to other server copies. As those data are duplicated on thousands of servers, no one can alone hack the Identity.

This Talao web application https://talao.co is a trust service to access Self Sovereign Identities with a simple User Interface and automated processus.
From a blockchain perspective, the Identity owner is the Ethereum account attached to the the smarthone crypto wallet.


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

  * https://identity.foundation/
  * https://ec.europa.eu/futurium/en/system/files/ged/eidas_supported_ssi_may_2019_0.pdf
  * https://joinup.ec.europa.eu/collection/ssi-eidas-bridge/about


What blockchain support does Talao use ?
----------------------------------------

Talao is available on the public Ethereum Mainet and Rinkeby. See https://github.com/TalaoDAO/talao-contracts for details.

Talao is also available on a private Ethereum network named TalaoNet.
TalaoNet runs a Proof Of Authority consensus (Clique) managed by the Talao team and partners.

To connect to this blockchain use RPC URL https://talao.co/rpc

Main contract addresses are :

- Talao token : 0x6F4148395c94a455dc224A56A6623dEC2395b99B
- Foundation : 0xb4C784Bda6A994f9879b791Ee2A243Aa47fDabb6
- Workspace Factory : 0x0969E4E66f47D543a9Debb7b0B1F2928f1F50AAf


Credits
-------

Thanks to the Ethereum community which provide us with great tools, Solidity code and inspiration.

Special thanks to `the WalletConnect team <https://walletconnect.org/>`_ for their implementation of an awesome protocol to connect crypto wallets with Dapps.

Special thanks to `OriginProtocol <https://originprotocol.com/>`_ for their implementation of `ERC 725 and ERC 735 <https://erc725alliance.org/>`_, which we use with slight modifications.

Thanks to the NLTK team and community for their Natural Language Programming work we used in the Dashboard panel is based on the python librairy `NLTK <https://www.nltk.org/>`_.
For more information Bird, Steven, Edward Loper and Ewan Klein (2009), Natural Language Processing with Python. O’Reilly Media Inc.
