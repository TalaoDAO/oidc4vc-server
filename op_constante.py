user = {
        "login_name" : "",
        "did" : "",
        "client_id" : []
}



method_list = {
                    "relay" : "Relay (external issuer)",
                    "ethr" : "did:ethr",
                    "key" : "did:key",
                    "tz": "did:tz",
                    "ebsi" : "did:ebsi",
                    "pkh:tz" : "did:pkh:tz",
                }

# for verifier
credential_list = {
                    "StandAlonePass" : "Pass",
                    'EmailPass' : 'Proof of email',
                    'PhoneProof' : 'Proof of phone',
                    'AgeRange' : 'Age range',
                    'Nationality' : 'Nationality',
                    'Gender' : 'Gender',
                    'IdCard' : 'Identity card',
                    'Over18' : 'Over 18',
                  #  'Tez_Voucher_1' : "Voucher 15% Tezotopia",
                    'VerifiableDiploma' : 'Diploma EBSI (Verifiable Diploma)',
                    'LearningAchievement' : 'Diploma',
                    'StudentCard' : 'Student card',
                    'AragoPass' : 'Arago Pass',
                  #  'CertificateOfEmployment' : 'Certificate of employment',
                  #  'VotersCard' : 'Voter card',
                  #  'TalaoCommunity' : 'Talao Community card',
                  #  'DID' : "None",
                    'ANY' : 'Any'
                }

credential_to_issue_list = {
                   'NewIdentityPass' : 'Pass as ID card (reserved)',
                    'StandAlonePass' : 'Pass with no data transfer',
                    'VerifierPass' : 'Pass with credential transfer',
                    'LearningAchievement' : 'Diploma (Learning achievement)',
                    'VerifiableDiploma' : 'Diploma EBSI (Verifiable Diploma)',
                   'StudentCard' : 'Student card (reserved)',
                    'CertificateOfEmployment' : 'Certificate of employment (reserved)',
                    'TalaoCommunity' : 'Talao Community card (reserved)',
                    "VotersCard" : "Voter Card (reserved)",
                    'PhoneProof' : 'Proof of phone number (reserved)'
                }

credential_to_issue_list_for_guest = {
                    'StandAlonePass' : 'Pass',
                    'VerifierPass' : 'Pass with credential transfer',
                    'LearningAchievement' : 'Diploma - Learning achievement',
                    'VerifiableDiploma' : 'Diploma EBSI - Verifiable Diploma',
                }


credential_requested_list = {
                    'EmailPass' : 'Proof of email',
                    'AgeRange' : 'Age range',
                    'Nationality' : 'Nationality',
                    'Gender' : 'Gender card',
                    'PhonePass' : 'Proof of phone number',
                    'IdCard' : 'Identity card',
                    'Over18' : 'Proof of majority',
                    "TezosAssociatedAddress" : "Proof of Tezos blockchain account",
                    "AragoPass" : "Arago Pass",
                    "login" : "Login and password",
                    "secret" : "Secret",
                    'DID' : "None",
                }

landing_page_style_list = {
                    "op_issuer_qrcode.html" : "Style 1",
                    "op_issuer_qrcode_2.html" : "Style 2"
                }

verifier_landing_page_style_list = {
                    "op_verifier_qrcode.html" : "Style 1",
                    "op_verifier_qrcode_2.html" : "Style 2",
                    "op_verifier_qrcode_3.html" : "Style 3",
                    "op_verifier_qrcode_4.html" : "Altme",
                     "arago_verifier_qrcode.html" : "Arago Style"
                }


protocol_list = {'w3cpr' : "W3C Presentation Request ",
                 'siopv2' : 'Siop V2'
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

model_two = {
            "type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": [
                        {
                            "example" : {"type" : ""},
                            "reason": [{"@language": "en","@value": ""}]
                        }
                    ]
                },
                {
                    "type": "QueryByExample",
                    "credentialQuery": [
                        {
                            "example" : {"type" : ""},
                            "reason": [{"@language": "en","@value": ""}]
                        }
                    ]
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
                "authorized_emails" : "",
                "vc" : "DID",
                "vc_2" : "DID",
                "emails" : None,
                "user" : "guest",
                "client_id" :  "",
                "client_secret" : "",
                "callback" : "https://altme.io",
                "webhook" : "https://altme.io",
                "jwk" : "",
                "method" : "",
                "did_ebsi": "",
                "issuer_landing_page" : "",     
                "note" : "",
                "company_name" : "New company",
                "application_name" : "Application name",
                "reason" : "Text in wallet message for credential 1",
                "reason_2" : "Text in wallet message for credential 2",
                "credential_requested" : "DID",
                "credential_requested_2" : "DID",
                "credential_to_issue" : "StandAlonePass",
                "protocol" : "w3cpr",
                "landing_page_style" : "op_issuer_qrcode.html",
                "verifier_landing_page_style" : "op_verifier_qrcode_2.html",
                "page_title" : "Page title",
                "page_subtitle" : "Page subtitle",
                "page_description" : "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
                "page_background_color" : "#ffffff",
                "page_text_color" : "#000000",
                "card_title" : "Page title",
                "card_subtitle" : "Page subtitle",
                "card_description" : "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
                "card_background_color" : "#ec6f6f",
                "card_text_color" : "#ffffff",
                "credential_duration" : "365",
                "qrcode_background_color" :"#ffffff",
                "qrcode_message" : "Scan with your wallet",
                "mobile_message" : "Open your wallet",
                "contact_email" : "contact@company.com",
                "contact_name" : "",
                "secret" : "",
                "landing_page_url" : "https://www.company.com",
                "privacy_url" : "https://www.company.com/privacy",
                "terms_url" : "https://www.company.com/terms_and_conditions", 
                "title" : "Get it !" # QR code title
                }
