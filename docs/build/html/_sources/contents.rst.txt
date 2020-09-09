Overview
========

What is Talao ?
---------------

Talao is a Blockchain protocol to manage professional data. 

Traditionnal architectures to validate, certify, and manage professional data are based on centralized, top-down approaches that rely on third-party private operators. 
Unfortunatky this organization often leads to inappropriate use of personal data and hacks.

Talao approaches this problem starting from a user perspective through a Blockchain decentralized Identity focused on professional data :

  - You own your data for your lifetime.
  - No private operators or government agencies can decide to update or delete your data.
  - No one can access your encrypted data without your permission.
  - No storage costs, you only pay Blockchain fees to update your data.
  - Certificates are tamper proof and tracable.
  - Certificates issuers are identified.

Talao allows professional data certification for Talents, Companies and other organizations such as Schools or Training Centers.
It is for everyone the opportunity to use a new technology to get tamper proof professional data while keping the ownership of those data.

Identities with their certificates can be displayed anywhere on digital plateforms : social medias, websites, Jobboards, etc. They provide to third parties reliable data about professional experiences, skills and education.


How does Talao work ?
---------------------

Talao is based on smart contracts Identities, it means that individuals and companies must first setup their own private smart contract (program) on the Blockchain to store and manage
their data. Each individual or company is given its own private key to access and update its Identity. 

Thanks to cryptographic algorithms those private keys are only used to sign messages sent by the Identity owner to the Blockchain. Those keys are never stored in a database.
If someone wants to update his data, he will sign a message (data update) with his private key and send it to thousands of Blockchain servers.
Each server will check the signature, update its data then compare it to other servers. As Blockchain data are duplicated on thousands of servers, no one can alone hack the Identity.  

This Talao web application (named Relay) is a portal to access Identities with a simple User Interface and automated processus.

Credits
-------

Thanks to the awesome Ethereum community which provide us with great tools, Solidity code and inspiration.
Special thanks to `OriginProtocol <https://www.originprotocol.com>`_ for their implementation of `ERC 725 and ERC 735 <https://erc725alliance.org/>`_, which we use with slight modifications.

Thanks to the NLTK team and community for their Natural Language Programming work we used in the Dashboard panel is based on the python librairy `NLTK <https://www.nltk.org/>`_.
For more information Bird, Steven, Edward Loper and Ewan Klein (2009), Natural Language Processing with Python. O’Reilly Media Inc.
