
Professional Identity
=====================

A professional Decentralized Identity is made up of data relating to individuals career, skills and experience.

Personal settings
-----------------

They are traditional information one can get in a resume :

- Firstname, lastname, contact email, contact phone, bithdate, about, postal address
 
.. warning:: By default those personal data are given by user through the Relay which is an automatic 'Issuer'. 

They are eventually not reliable for third parties as data are either self declared or issued on user behalf.


Proof of Identity
-----------------

This is one of the most important feature of the Identity.

In order to get reliable data, one has to prove the user belonging of the Identiy and the liability of personal data.

This process is today manage only by Talao through a KYC process for Talents and Companies.
Read more on :doc:`/proof_of_identity`

.. note:: We strongly suggest to ask Talao for a Proof of Identity as soon as possible. They are currently free of charge 



Experience
----------

Experience data are always Public. Those Experiences are issued by yourself. They are an essential part of a standard resume.
Those data are self declared.

Education
----------

Education data are always Public. Those Educations are issued by yourself only. They are an essential part of a strandard resume.
Those data are self declared.


Certificates
------------

Certificates are always public. 

They have a strong added value as they are issued (signed) by third parties and so data can be checked for reliability and proof of issuance.

There are several types of certificates :

   * Experience Certificates issued by companies
   * Skills and Trainng Certificates issues by companies (Not implemented yet in July 2020)
   * Recommendation issued by Companies or Persons


One can check the issuer of each of those certificates. For each issuer one can check its proof of identity and its own certificates.
This process can be done as long as one find strong proofs of evidence.

One can make a copy of the certificate link to insert them anywhere in digital presentation. Certificate links can be deleted by user from his/her Identity.
However if the link is deleted the certificate is always "live" on its decentralized support as data are tamper proof.


Alias
-----

An Alias is a new couple of Username+Email for authentification through the `Relay <http://talao.co:50000/login/>`_

At setup, one smart contract is created for each identity and one authentification email is encrypted and stored within this smart contract on the Ethereum Blockchain. 
The address of the smart contract is the Decentralized IDentifier (DID) of the Identity. Unfortunaltly theis address is quite difficult to memorize (ex : 0xfC6acd13F07bcCFB7563908f717377806e0Ed92E). 
So when user signs in the first time, he registers a "username" to have a readable identifier associated to his smart contract address.

An Alias is another Username you can use with another email to access yous Identity through the Relay.

You can add as many Alias you want, for instance you can use an Alias for each of your device.


Referent
--------

A Referent is a Company or a Person the user has authorized to issue certificates.
The user is the only one able to appoint Referents. User does not need the Referent authoriation to appoint him/her.
In the other hand the Referent is not obliged to issue any certificate to the user.

Partner
-------

A Partner is a Company or a Person with whom you share Private data.

A partnership is the relationship you share with your Partner. You can request a partnership but it has to be accepted by other party to be effective.

Any party can cancel a partnership at anytime.

.. warning:: When a partnership is established you share your private data. 
   After cancellation the other party can eventualky keep on using your private key to access your private data. 


White List
----------

The White List is made up of reliable issuers from your standpoint.
You can add a new issuer in your White List through the White List menu. 
It is likely your own Referent and Partners are reliable but you have to add them anyway, you can also add other Issuers even if they are not in your Referent List.

This White List allowed you to have better view of others certificates.

.. note:: By default Relay is not a White List issuer, but Talao is. At start Talao is the only company to issue Proof of Identity. 



Data Store
-------------

The Data Store is decentralized support to store data you either want to share with others (public privacy) or only with Partners (private privacy) or you want to keep secret for everybody.

If you want to change the nature of the privacy you firtst need to remove the file and create a new one. The document will be encrypted at creation and stored on a decentralized support (IPFS today).



Advanced
--------

This information is usefull to check and track your data through other means as `Ethereum Explorer <https://etherscan.io>`_

Relay Status : Activated if user has given to the Relay the right to sign on behalf the Identity. If Relaus does not have this right, no data can be updated through the Relay application.

Private Key : Yes  or No. If True the Relay has a copy of the Ethereum private key og the Identity. This is the case when the Identity is created through the Relay (Quick Start).

RSA Key : Yes or No. If No Relay cannot crate Private or Secret data.

