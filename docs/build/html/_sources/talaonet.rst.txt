Overview
========

Talaonet is a Private Ethereum Network with a Proof Of Authority consensus managed by Talao and partners. 
The Talao protocol has been deployed on Talaonet.


Genesis file 
------------

.. code-block:: JSON

  {
  "config": {
    "chainId": 50000,
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip150Hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "clique": {
      "period": 5,
      "epoch": 30000
    }
  },
  "nonce": "0x0",
  "timestamp": "0x5f64a2c0",
  "extraData": "0x0000000000000000000000000000000000000000000000000000000000000000b2facb12e295fd63448bed4132746912c55d44bb0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "gasLimit": "0x47b760",
  "difficulty": "0x1",
  "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
  "coinbase": "0x0000000000000000000000000000000000000000",
  "alloc": {
    "b2facb12e295fd63448bed4132746912c55d44bb": {
      "balance": "0x200000000000000000000000000000000000000000000000000000000000000"
    },
    "da1d3332a17a8c4b8fef4be1f7b9dd578c83b322": {
      "balance": "0x200000000000000000000000000000000000000000000000000000000000000"
    }
  },
  "number": "0x0",
  "gasUsed": "0x0",
  "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000"
  }

Peers
-----

.. code-block:: JSON

  ["enode://ffe89bf39a71a2bd65af78214eeb85ff47e60a348a9f5fd85f9c4348f7bcb15aaec2be8c6a5e7fb4ff1ae866fdb60a05a55d5805f3c3b5c343ecdbfb611ed188@18.190.21.227:30311",
  "enode://e0aba907468fddc14bb2b775c974e1ef039920feccadbc45ccf1d7e7a72a7f9e65702ed5a12a00c7ff8e9097e50f9131282ef9487734daa061251f6d1f4d3ade@18.190.21.227:30312"]


Main contract addresses
-----------------------

Talao token : 0x6F4148395c94a455dc224A56A6623dEC2395b99B

Foundation : 0xb4C784Bda6A994f9879b791Ee2A243Aa47fDabb6

Workspace Factory : 0x0969E4E66f47D543a9Debb7b0B1F2928f1F50AAf
