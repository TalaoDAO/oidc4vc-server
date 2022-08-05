


credential_list = {
                    'EmailPass' : 'Proof of email',
                    'IdCard' : 'Identity card',
                    'Over18' : 'Over 18',
                    'Tez_Voucher_1' : "Voucher 15% Tezotopia",
                    'LearningAchievement' : 'Diploma',
                    'StudentCard' : 'Student card',
                    'CertificateOfEmployment' : 'Certificate of employment',
                    'DID' : "Decentralized Identifier",
                    'ANY' : 'Any'
                }

credential_to_issue_list = {
                    'LearningAchievement' : 'Diploma',
                    'StudentCard' : 'Student card',
                    'CertificateOfEmployment' : 'Certificate of employment',
                    "VaccinationEvent" : "Vaccination certificate"
                }

credential_requested_list = {
                    'EmailPass' : 'Proof of email',
                    'IdCard' : 'Identity card',
                    'Over18' : 'Over 18',
                    'DID' : "Decentralized Identifier",
                    "TezosAssociatedWallet" : "Proof of crypto account",
                    'ANY' : 'Any'
                }

protocol_list = {'w3cpr' : "W3C Presentation Request ",
                 #'openid4vc' : 'OpenID 4 VC'
                 }

model_one = {
            "type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": [{
                    "example" : {
                        "type" : "",
                    },
                    "reason": [
                        {
                            "@language": "en",
                            "@value": ""
                        }
                    ]
                }]
                }
            ],
            "challenge": "",
            "domain" : ""
            }


model_DIDAuth = {
           "type": "VerifiablePresentationRequest",
           "query": [{
               "type": "DIDAuth"
               }],
           "challenge": "a random uri",
           "domain" : "talao.co"
    }

model_any = {
            "type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": list()
                }
            ],
            "challenge": "",
            "domain" : ""
            }


verifier_client_data_pattern = {
                "user" : "all",
                "client_id" :  "",
                "client_secret" : "",
                "jwk" : "",
                "company_name" : "New verifier",
                "reason" : "",
                "authorized_emails" : "",
                "vc" : "",
                "note" : "This verifier is ......",
                "page_title" : "Page title",
                "page_subtitle" : "Page subtitle",
                "page_description" : "Page description",
                "protocol" : "w3cpr",
                "qrcode_message" : "Sign In with your wallet",
                "mobile_message" : "",
                "emails" : None,
                "contact_email" : "",
                "contact_name" : "",
                "landing_page_url" : "https://www.my_company.com",
                "privacy_url" : "https://www.my_company.comprivacy",
                "terms_url" : "https://www.my_company.com/terms_and_conditions", 
                "title" : "Sign-In"
                }


issuer_client_data_pattern = {
                "user" : "all",
                "client_id" :  "",
                "callback" : "",
                "webhook" : "",
                 "jwk" : "",
                "issuer_landing_page" : "",     
                "note" : "This issuer is ......",
                "company_name" : "New issuer",
                "reason" : "Text in wallet message",
                "credential_requested" : "",
                "credential_to_issue" : "",
                "protocol" : "w3cpr",
                "page_title" : "Page title",
                "page_subtitle" : "Page subtitle",
                "page_description" : "Page description",
                "qrcode_message" : "Scan with your wallet",
                "mobile_message" : "",
                "contact_email" : "",
                "contact_name" : "",
                "landing_page_url" : "https://www.my_company.com",
                "privacy_url" : "https://www.my_company.com/privacy",
                "terms_url" : "https://www.my_company.com/terms_and_conditions", 
                "title" : "Scan to issue"
                }


LearningAchievement = {
        "type" : "LearningAchievement",
        "id": "",
        "familyName": "Lea",
        "givenName": "Skywalker",
        "birthDate": "1977-08-15",
        "email" : "lea@starwar.io",
        "hasCredential": {
            "title":  "Pilot",
            "description" : "hhhhh"
        },
        "issuedBy" : {
            "name": "Star war commander",
            "address" : "",
            "logo" : ""
        }
    }

VaccinationEvent = {
        "type": "VaccinationEvent",
        "id" : "",
        "batchNumber": "1183738569",
        "administeringCentre": "MoH",
        "healthProfessional": "MoH",
        "countryOfVaccination": "NZ",
        "recipient": {
            "type": "VaccineRecipient",
            "givenName": "JOHN",
            "familyName": "SMITH",
            "gender": "Male",
            "birthDate": "1958-07-17"
        },
        "vaccine": {
            "type": "Vaccine",
            "disease": "COVID-19",
            "atcCode": "J07BX03",
            "medicinalProductName": "COVID-19 Vaccine Moderna",
            "marketingAuthorizationHolder": "Moderna Biotech"
        }
}

StudentCard = {
        "id": "",
        "type": "StudentCard",
        "recipient": {
            "birthDate": "1991-12-10T12:02:55.268Z",
            "familyName": "Doe",
            "givenName": "John",
            "image": "https://gateway.pinata.cloud/ipfs/QmSSJooT2JFraZFNHavVLQzzxwSpg3ithJL4ztGYY9MpBY",
            "signatureLines": {
                "image": "https://gateway.pinata.cloud/ipfs/QmeMfck3z6K5p8xmCqQpjH3R7s3YddR5DsMNLewWvzQrFS"
            }
        },
        "issuedBy": {
            "address": "16 rue de Wattignies, 75012 Paris, France",
            "directorName": "Nicolas Muller",
            "logo": "https://talao.mypinata.cloud/ipfs/QmNwbEEupT7jR2zmrA87FsN4hUS8eXnCxM8DsL9RXc25cu",
            "name": "Talao CFA"
        }
    }

CertificateOfEmployment = {
        "id": "",
        "familyName": "Derangeot",
        "jobTitle": "Lead developer",
        "employmentType": "Contrat à durée illimitée",
        "startDate": "2019-09-04",
        "type": "CertificateOfEmployment",
        "givenName": "Paul",
        "workFor": {
            "address": "16 rue de Wattignies, 75012 Paris, France",
            "logo": "https://talao.mypinata.cloud/ipfs/QmNwbEEupT7jR2zmrA87FsN4hUS8eXnCxM8DsL9RXc25cu",
            "name": "Talao"
        },
        "issuedBy": {
            "address": "16 rue de Wattignies, 75012 Paris, France",
            "logo": "https://talao.mypinata.cloud/ipfs/QmNwbEEupT7jR2zmrA87FsN4hUS8eXnCxM8DsL9RXc25cu",
            "name": "Talao"
        },
        "baseSalary": "65000 euros"
    }