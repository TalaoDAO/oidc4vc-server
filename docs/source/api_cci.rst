
Talao API
=========

An API to get company credentials link or data.

Credential link list
********************

.. code::

  curl  -H "Content-Type: application/json" -X GET https://talao.co/api/v1/credential?siret=<siret_number>

example :

.. code::

  curl  -H "Content-Type: application/json" -X GET https://talao.co/api/v1/credential?siret=1234567890000


Return is a JSON structure with all credential links in an JSON array :

.. code-block:: 

    {
    "category": "success", 
    "data": [
        "https://talao.co/certificate/?certificate_id=did:talao:talaonet:2e06194D1F093509E10490Da5426A373A79eE44A:document:5", 
        "https://talao.co/certificate/?certificate_id=did:talao:talaonet:2e06194D1F093509E10490Da5426A373A79eE44A:document:6", 
        "https://talao.co/certificate/?certificate_id=did:talao:talaonet:2e06194D1F093509E10490Da5426A373A79eE44A:document:7"
    ], 
    "message": "Credential link list", 
    "status": 200
    }



Resolver
********

The Resolver allows to get the comapany DID (Decentralized Ientifier) from the SIRET.

.. code::

  curl  -H "Content-Type: application/json" -X GET https://talao.co/api/v1/resolver?siret=123456789

Return is a JSON structure :

.. code-block:: 

    {
    "category": "success", 
    "data": "did:web:talao.co", 
    "message": "DID", 
    "status": 200
    }

The DID Document can be obtain from the Universal Resolver https://resolver.identity.foundation/