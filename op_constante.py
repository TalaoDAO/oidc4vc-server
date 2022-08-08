
method_list = {
                    "ethr" : "did:ethr",
                    "key" : "did:key",
                    "tz": "did:tz",
                    "ebsi" : "did:ebsi",
                    "pkh:tz" : "did:pkh:tz",
                }

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
                    'NewIdentityPass' : "Pass",
                    'LearningAchievement' : 'Diploma (Learning achievement)',
                    'VerifiableDiploma' : 'Diploma EBSI (Verifiable Diploma)',
                    'StudentCard' : 'Student card',
                    'CertificateOfEmployment' : 'Certificate of employment',
                    "AragoPass" : "Arago Pass"
                }

credential_requested_list = {
                    'EmailPass' : 'Proof of email',
                    'PhonePass' : 'Proof of phone number',
                    'IdCard' : 'Identity card',
                    'Over18' : 'Proof of majority (Over 18)',
                    "TezosAssociatedWallet" : "Proof of crypto account",
                    'DID' : "None",
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
                "client_secret" : "",
                "callback" : "",
                "webhook" : "",
                "jwk" : "",
                "method" : "",
                "did_ebsi": "",
                "issuer_landing_page" : "",     
                "note" : "This issuer is ......",
                "company_name" : "New issuer",
                "reason" : "Text in wallet message",
                "credential_requested" : "IdCard",
                "credential_to_issue" : "NewIdentityPass",
                "protocol" : "w3cpr",
                "page_title" : "Page title",
                "page_subtitle" : "Page subtitle",
                "page_description" : "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
                "page_background_color" : "#ffffff",
                "page_text_color" : "#000000",
                "qrcode_background_color" :"#ffffff",
                "qrcode_message" : "Scan with your wallet",
                "mobile_message" : "",
                "contact_email" : "",
                "contact_name" : "",
                "landing_page_url" : "https://www.my_company.com",
                "privacy_url" : "https://www.my_company.com/privacy",
                "terms_url" : "https://www.my_company.com/terms_and_conditions", 
                "title" : "Scan to issue"
                }