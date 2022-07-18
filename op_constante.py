


credential_list = {
                    'EmailPass' : 'Proof of email',
                    'Kyc' : 'Identity card',
                    'Over18' : 'Over 18',
                    'Tez_Voucher_1' : "Voucher 15% Tezotopia",
                    'LearningAchievement' : 'Diploma',
                    'StudentCard' : 'Student card',
                    'CertificateOfEmployment' : 'Certificate of employment',
                    'DID' : "Decentralized Identifier",
                    'ANY' : 'Any'
                }

protocol_list = {'w3cpr' : "W3C Presentation Request ",
                 'openid4vc' : 'OpenID 4 VC'
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


client_data_pattern = {
                "client_id" :  "",
                "client_secret" : "",
                "jwk" : "",
                "company_name" : "New verifier",
                "reason" : "Text in wallet message",
                "authorized_emails" : "",
                "vc" : "",
                "protocol" : "w3cpr",
                "qrcode_message" : "Sign In with your wallet",
                "mobile_message" : "Mobile message",
                "emails" : None,
                "contact_email" : "",
                "contact_name" : "",
                "landing_page_url" : "",
                "privacy_url" : "https://talao.co/md_file?file=privacy",
                "terms_url" : "https://talao.co/md_file?file=terms_and_conditions", 
                "title" : "Sign-In"
                }