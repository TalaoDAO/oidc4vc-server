# Talao Credential Portfolio

The Talao solution allows Talents the possibility to deliver certified data to future employers about their professional skills and experiences. All those credentials make up an Employment portfolio. For companies it is web solution, easy to sue, to issue professional verifiable credentials to Talents as employees or freelancers.

Precisely Talao professional credentials are about :
Professional experiences : Description of a project or mission with data about hard/soft skills and a management evaluation. For freelancers, it’s about the same content as the ones delivered by online Talent platform (Upworks, etc). 
Professional skills : A statement of knowledge, skill, ability, task or any other assertion expressing a competency that is desired or required to fulfill this role or to work in this occupation.
Legal identities for persons and organizations.
Customer references.
Business certificates and licences.

The approach we use is based on the Self Sovereign Identities standards (SSI) to manage Decentralized Identifiers (DID) and Verifiable Credentials (VC). Those standards have been published by the W3 Consortium  :

* https://www.w3.org/TR/did-core/
* https://www.w3.org/TR/vc-data-model/

##  Components :
* a repository built on an Private Ethereum network "Talaonet" and the Talao protocol (Talao smart contract + ERC725/ERC735).
        This repository is a slim EDV (Encrypted Data Vault)

* a DID manager for create and read operations. The cryptographiv keys are stores on user wallet (Localstorage browser) and on a encrypted desktop file for users.
        Keys are stored server side for companies. We currently support did:web, did:tz, did:ethr and did:ion.

* a credential issuer for companies. This issuer is designed for support a review + validation workflow. A credential draft is first sent by Talent to the reviewer then to the issuer.

WE currently use the Spruce didkit server side to manage did:tz, did:key and did:ethr. 
we use ion tools to manage did:ion
EC secp256k1 (and possibly p-256 and Ed25519 in the near future)

## License
Copyright 2021 Talao.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this software except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 or the LICENSE file in this repository.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.