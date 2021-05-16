# Talao Credential Repository

The Talao solution allows companies to issue professional verifiable credentials to Talents as employees or freelancers and to companies as customers.  For Talents, it is the possibility to deliver certified data to future employers about their professional skills and experiences.

Precisely Talao professional credentials are about :
Professional experiences : Description of a project or mission with data about hard/soft skills and a management evaluation. For freelancers, it’s about the same content as the ones delivered by online Talent platform (Upworks, etc). 
Professional skills : A statement of knowledge, skill, ability, task or any other assertion expressing a competency that is desired or required to fulfill this role or to work in this occupation.
Legal identities for persons and organizations.
Customer references.
Business certificates and licences.

Here is an example of a customer reference issued by a company for one of its professional services providers (this credential has been stored in a repository to be publicly available). 

The approach we use is based on the Self Sovereign Identities standards (SSI) to manage Decentralized Identifiers (DID) and Verifiable Credentials (VC). Those standards have been published by the W3 Consortium  :

* https://www.w3.org/TR/did-core/
* https://www.w3.org/TR/vc-data-model/

## The solution is made up of 3 components :
* a repository built on an Private Ethereum network "Talaonet" and the Talao protocol (Talao smart contract + ERC725/ERC735).
        This repository is a minimum EDM (Encrypted Data Vault)
* a DID manager for create and read operations. The cryptographiv keys are stores on user wallet (Localstorage browser) and on a encrypted desktop file for users
        and tehye are stored server side for companies.
* an issuer for companies. This issuer is designed for specific worksflows.

WE currently use the Spruce didkit server side to manage did:tz, did:key and did:ethr. 
we use ion tools to manage did:ion
EC secp256k1 (and possibly p-256 and Ed25519 in the near future)

Main script to start web server through Gunicorn
Arguments of main.py are in gunicornconf.py (global variables) :
$ gunicorn -c gunicornconf.py  --reload wsgi:app
if script is launched without Gunicorn, setup environment variables first :
$ export MYCHAIN=talaonet
$ export MYENV=livebox
$ python main.py
