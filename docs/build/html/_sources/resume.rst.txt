
Professional Identity
=====================


Personal
--------

- Firstname
- Lastname
- Contact Email
- Contact Phone
- Birthdate
- Address
 
.. warning:: By default those personal data are given by user through the Relay which is an automatic 'Issuer'. 

They are eventually not reliable for third parties as data are issued on your behalf. 

They are however an essential part of a standard resume.


Proof of Identity
-----------------

This is one of the most important feature of the Identity.

In order to get reliable data, one has to prove the belonging of the Identiy and the veracity of personal data.
This process is today manage only by Talao through a KYC process for Talents and Companies.
Read more on :doc:`/proof_of_identity`

Experience
----------

Experience data are always Public. Those Experience are issued by yourself. They are an essential part of a standard resume.

Education
---------

Education data are always Public. Those Education are issued by yourself only. They are an essential part of a standard resume.


Certificates
------------

Certficates are always Public. 

They have a strong added value as they are signed by third parties and data can be checked for reliability and proof of issuance.

There are several types of certificates :

   * Experience Certificates issued by companies
   * Trainng Certifocate issues by companies
   * Recommendation issued by Companies or Persons

One can make a copy of the link to insert them anywhere in digital presentation.


Alias
-----

An Alias is a new couple of Username+Email for authentification through the `Relay <http://talao.co:50000/login/>`_

At Identity creation, one smart contract is crated and one authentification email is encrypted and stored within this smart contract on the Ethereum Blockchain. 
The address of the smart contract is the Decentralized IDentifier (DID) of your Identity. 
When you sign-in if the first time, you register a 3sernane to have a readable identifier associated to the smart contract address.

An Alias alias is another Username you can use with another email to access the Relay.

You can add as many Alias you want, for instance you can use an Alias for each of your device.

.. warning:: The email assciated with your Username is public.


Issuer
------

An Issuer is a Company or a Person you have authorized to issue claims as Certificate, Recommendation, etc.
You are the obly one to appoint Issuers.

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
It is likely your own Issuer and Parners are reliable but you have to add them anyway, you can also add other Issuers even if they are not in your Issuer List.

This White List allowed you to have better view of others certificates.

.. note:: By default Relay is not a White List issuer, but Talao is as Talao is at start teh only company to issue Proof of Identity. 



Data Store
-------------

The Data Store is decentralized support to store data you either want to share with others (public privacy) or only witht Praners (private privacy) or you want to keep secret for everybody.

If you want to change the nature of the privacy you firtst need to remove the file and create a new one. The document will be encrypted at creation.



Advanced
--------

This information is usefull to check and track your data through other means as `Ethereum Explorer <https://etherscan.io>`_

Relay Status : Activated if user has given to the Relay the right to sign on behalf the Identity. If Relaus does not have this right, no data can be updated through the Relay application.

Private Key : Yes  or No. If True the Relay has a copy of the Ethereum private key og the Identity. This is the case when the Identity is created through the Relay (Quick Start).

RSA Key : Yes or No. If No Relay cannot crate Private or Secret data.
