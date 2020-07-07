
Organisation des tests 
=======================

Contexte
--------

Le protocole Talao est une application de la blockchain Ethereum permettant la gestion d'Identités Décentalisées spécialisées sur les données professionnelles.
Cf ce `lien <https://cryptoast.fr/identites-numeriques-decentralisees/>`_ pour plus d'information sur les Identitées Décentralisées. 
Les principaux apports du protocole sont :

   - la protection maximum des données pour les utilisateurs par la desintermédiation,
   - la fiabilité et la traçabilité des données RH pour l'entreprise,
   - la possibilité d'emettre des certificats infalsifiables et inaltérables en quelques minutes avec des frais minimum. 

Une première version du protocole Talao a été déployée en Fevrier 2018. Il a été installé avec un accès sous la forme d'une `Dapp <https://freedapp.io/>`_.
Suite à ce déploiement l'équipe Talao s'est concentrée sur la commercialisation de l'offre auprès des grands comptes sur le secteur des freelances représentant un use case relativement simple.
Plusieurs projets ont été initiés en particulier pour l'émission de certificats pour des entreprises du secteur des ESN qui trouvaient dans un contexte de pénuri de 
ressources et de fort turn over de leurs personnel un outils suplémentaire de renforcement de leur marque employeur.

Dans ce contexte nous avons en revanche constaté que la mise en euvre de la Dapp et en particulier son adoption pour des utilisateurs non experts était difficile compte tenu de la complexité des manipulations.
Il faut aujourd'hui pour utiliser le protocole non seulement disposer d'un wallet Ethereum et de cryptos  mais aussi d'être en mesure de signer des transactions Ethereum avec un outil tel que Metamask.

Dans ce contexte et compte tenu de la période actuelle peut propice à de nouveaux projets en entreprise, l'équipe Talao s'est donc investie sur la réalisation d'une nouvelle solution technique pour l'accès
des utilisateurs au protocole. Cette solution est construite autour d'une **application web centralisée** traditionnelle permettant une simplification maximum de la gestion de son Identité 
en échange d'une réduction plus ou moins importante des principes de la protection des données.
Cette application a été définie autour du concept de la **gestion pour compte de tiers de l'Identité**.

C'est cette nouvelle application qui est l'objet de ces test.


Objectif des tests
------------------

Il s'agit de :

   - vérifier la valeur ajoutée des fonctionnalites proposées aux utilisateurs,
   - de s'assurer de la facilité de leur mise en oeuvre,
   - d'identifier des points d'amélioration (contenu et design),
   - de relever les bugs existants.
   
Le scope du test est :

   - l'application web http://talao.co:5000/starter/
   - Cette documentation dans sa partie user (hors Talent Connect et Internal) 
   
   
Equipe de testeurs et projet de test
------------------------------------

L'équipe de test est constitué de 3 à 5 personnes, la durée des tests est prévue sur environ 2 mois (Juillet- Aout 2020).

.. note::  Les testeur s'engagent sur l'honneur à conserver la confidentialité de ces tests et en particulier de s'abstenir de diffuser des informations concernant ces tests sur les réseaux sociaux sans l'accord de Talao.
           Talao poura interrompre ces tests à tout moment de sa propre initiative si nécessaire.

Environnement technique
-----------------------

L'application est actuellement installée sur un serveur AWS et fonctionne sur la Blockchain Rinkeby de test. Les tokens TALAO et ETH utilisés sur Rinkeby n'ont pas de valeur marchande.

Les problèmes rencontrés sont à notifier sous la forme d'**issues** sur le repository https://github.com/thierrythevenet1963/Talao

La mise à jour de l'application en production est faite habituellement sur une base quotidienne (20h00).


Démarche pour les testeurs
--------------------------

Il n'est pas prévu de plan de test particulier pour les testeurs qui sont libres de manipuler l'application en fonction de leur disponibilité et de leur curiosité.

Nous leur conseillons en revanche :

   - de commencer par la lecture de cette doc et en particulier des chapitres How-To et Quick Start,
   - de commencer par explorer la base de test avant de procéder à la création d'identités et à la demande de certificats,
   - de créer leur propre identité,
   - de limiter la demande de certificats (par email) à 1 ou 2 personnes connues, sachant que systématiquement une identité sera créée pour chacune de ces personnes si celles-ci acceptent d'émettre le certificat. 
   
Le design des vues a été fait pour un usage sur smartphone mais l'application est bien entendue accessible sur PC.

.. note::  Toutes les informations, images, etc de la base de test actuelle correspondent à des utilisateurs et des sociétés fictives meme si les noms sont parfois connus. 


Base de test
------------

user :

    - username : "pascalet", code "123456" : pascalet (Jean Pascalet) a comme référent jean
    - username : "jean", code "123456" : jean (Jean Pierre Roulle) a comme referent BNP, pascalet, jeanpierrevalga. Jean est manager chez BNP
    - username : "thierry" code "123456" : thierry (Thierry Thevenet) est manager chez Talao 
    - username : 'jeanpierrevalga" code "123456" : jeanpierrevalga (Jean Pierre Valga)
    
entreprise :

    - username : "bnp", code "123456" : bnp (BNP) a comme manager jean et comme partner thales et talao
    - username : "talao" code "123456" : talao (Talao) a comme manager thierry. Talao dispose de fonctionnalités étendues pour emettre des "proof of identity" (kbis et kyc) et creer des identités.
    - username : "thales" code "123456"
    - username : "orange" code "123456"


.. note:: Un manager qui veut acceder a l identité de la société ou il est manager doit se connecter avec un username double "person.company". Example jean peut se logger 
          a l identité de bnp avec son username "jean.bnp".  
