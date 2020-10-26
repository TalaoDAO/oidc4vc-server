Overview
========

What is Talao ?
---------------

Talao is a Blockchain protocol to manage professional data. 

Traditionnal architectures to validate, certify, and manage professional data are based on centralized, top-down approaches that rely on third-party private operators. 
Unfortunatky these solutions often lead to inappropriate use of personal data and hacks.

Talao approaches this issue starting from a user perspective through a Blockchain decentralized Identity focused on professional data :

  - You own your data for your lifetime.
  - No private operators or government agencies can decide to update or delete your data.
  - No one can access your encrypted data without your permission.
  - No storage costs.
  - Certificates are tamper proof and tracable.
  - Certificates issuers are identified.

Talao allows Professional Identities for Talents, Companies and certificates issuers such as Schools or Training Centers.
It is for everyone the opportunity to use a new technology to get tamper proof professional data while keping the ownership of those data.

Identities with their certificates can be displayed anywhere on digital plateforms : social medias, websites, Jobboards, etc. They provide to third parties reliable data about professional experiences, skills and education.


How does Talao work ?
---------------------

Talao is based on smart contracts Identities, it means that individuals and companies first setup their own private smart contract on the Blockchain to store and manage
their data. Each individual or company is given its own private key to access and update its Identity.

Thanks to cryptographic algorithms those private keys are only used to sign messages sent by the Identity owner to the Blockchain. Those keys are never stored in a database.
If someone wants to update his data, he will sign a message (data update) with his private key and send it to thousands of Blockchain servers.
Each server will check the signature, update its data then compare it to other servers. As Blockchain data are duplicated on thousands of servers, no one can alone hack the Identity.  

This Talao web application https://talao.co is a portal to access Identities with a simple User Interface and automated processus.

.. warning:: As this web application is a third party wallet, we strongly advise not to use your Identity address to store crypto currencies.


TalaoNet
--------

TalaoNet is a Private Ethereum Network with a Proof Of Authority consensus (Clique) managed by Talao and partners.
The Talao protocol has been deployed on TalaoNet.

RPC URL https://18.190.21.227:8502

Main contract addresses

- Talao token : 0x6F4148395c94a455dc224A56A6623dEC2395b99B
- Foundation : 0xb4C784Bda6A994f9879b791Ee2A243Aa47fDabb6
- Workspace Factory : 0x0969E4E66f47D543a9Debb7b0B1F2928f1F50AAf

Protocol code available at https://github.com/TalaoDAO/talao-contracts

Credits
-------

Thanks to the awesome Ethereum community which provide us with great tools, Solidity code and inspiration.
Special thanks to `OriginProtocol <https://www.originprotocol.com>`_ for their implementation of `ERC 725 and ERC 735 <https://erc725alliance.org/>`_, which we use with slight modifications.

Thanks to the NLTK team and community for their Natural Language Programming work we used in the Dashboard panel is based on the python librairy `NLTK <https://www.nltk.org/>`_.
For more information Bird, Steven, Edward Loper and Ewan Klein (2009), Natural Language Processing with Python. O’Reilly Media Inc.
