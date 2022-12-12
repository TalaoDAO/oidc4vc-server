
user = {
        "login_name" : "",
        "did" : "",
        "client_id" : []
}


sbt_network_list = {
    'none' : 'None',
    #'tezos' : 'Tezos Mainnet',
    'ghostnet' : 'Tezos Ghostnet',
    #'ethereum' : 'Ethereum Mainet',
    #'rinkeby' : 'Ethereum Rinkeby'
}


tezid_network_list = {
    'none' : 'None',
    #'tezos' : 'Tezos Mainnet',
    'ghostnet' : 'Tezos Ghostnet',
}

method_list = {
                    "relay" : "Relay (external issuer)",
                    "ethr" : "did:ethr",
                    "key" : "did:key",
                    "tz": "did:tz",
                    "ebsi" : "did:ebsi",
                    "pkh:tz" : "did:pkh:tz",
                }

# for verifier admin
credential_list = {
                    'Pass' : 'Pass',
                    'GamerPass' : 'Gamer Pass',
                    'EmailPass' : 'Proof of email',
                    'PhoneProof' : 'Proof of phone',
                    'AgeRange' : 'Age range',
                    'Nationality' : 'Nationality',
                    'Gender' : 'Gender',
                    'IdCard' : 'Identity card',
                    'Over18' : 'Over 18',
                    'Over13' : 'Over 13',
                    'PassportNumber' : 'Passport footprint',
                    "TezosAssociatedAddress" : "Proof of Tezos blockchain account",
                    'Tez_Voucher_1' : "Voucher Tezotopia",
                    'VerifiableDiploma' : 'Diploma EBSI (Verifiable Diploma)',
                    'LearningAchievement' : 'Diploma',
                    'StudentCard' : 'Student card',
                    'AragoPass' : 'Arago Pass',
                    'InfrachainPass' : 'Infrachain Pass',
                    'CertificateOfEmployment' : 'Certificate of employment',
                    'VotersCard' : 'Voter card',
                    'TalaoCommunity' : 'Talao Community card',
                    'DID' : "None",
                    'ANY' : 'Any'
                }

# for verifier  guest
credential_list_for_guest = {
                    'Pass' : 'Pass',
                    'GamerPass' : 'Gamer Pass',
                    "TezosAssociatedAddress" : "Proof of Tezos blockchain account",
                    "EthereumAssociatedAddress" : "Proof of Ethereum blockchain account",
                    'EmailPass' : 'Proof of email',
                    'PassportNumber' : 'Passport footprint',
                    'PhoneProof' : 'Proof of phone',
                    'AgeRange' : 'Age range',
                    'Nationality' : 'Nationality',
                    'Gender' : 'Gender',
                    'IdCard' : 'Identity card',
                    'Over18' : 'Over 18',
                    'Over13' : 'Over 13',
                    'AragoPass' : 'Arago Pass',
                    'InfrachainPass' : 'Infrachain Pass',
                    'DID' : "None",
                    'ANY' : 'Any'
                }

# for beacon verifier for guest
beacon_verifier_credential_list = {
                    'Pass' : 'Pass',
                    'GamerPass' : 'Gamer Pass',
                    'TezosAssociatedAddress' : 'Proof of Tezos blockchain account',
                    'EthereumAssociatedAddress' : 'Proof of Ethereum blockchain account',
                    'EmailPass' : 'Proof of email',
                    #'PassportNumber' : 'Passport footprint',
                    #'PhoneProof' : 'Proof of phone',
                    #'AgeRange' : 'Age range',
                    #'Nationality' : 'Nationality',
                    #'Gender' : 'Gender',
                    'TalaoCommunity' : 'Talao loyalty card',
                    'LearningAchievement' : 'Diploma',
                    'BloometaPass' : 'Bloometa gaming card',
                    'IdCard' : 'Identity card',
                    'Over18' : 'Over 18',
                    'Over13' : 'Over 13',
                    'AragoPass' : 'Arago Pass',
                    'DID' : 'None',
                    'ANY' : 'Any'
                }

# for tezid verifier for guest
tezid_verifier_credential_list = {
                    'Pass' : 'Pass',
                    'GamerPass' : 'Gamer Pass',
                    #'TezosAssociatedAddress' : 'Proof of Tezos blockchain account',
                    #'EthereumAssociatedAddress' : 'Proof of Ethereum blockchain account',
                    #'EmailPass' : 'Proof of email',
                    #'PassportNumber' : 'Passport footprint',
                    #'PhoneProof' : 'Proof of phone',
                    #'AgeRange' : 'Age range',
                    #'Nationality' : 'Nationality',
                    #'Gender' : 'Gender',
                    #'TalaoCommunity' : 'Talao loyalty card',
                    #'LearningAchievement' : 'Diploma',
                    #'BloometaPass' : 'Bloometa gaming card',
                    #'IdCard' : 'Identity card',
                    'Over18' : 'Over 18',
                    'Over13' : 'Over 13',
                    #'AragoPass' : 'Arago Pass',
                    'DID' : 'None'
                    #'ANY' : 'Any'
                }


# issuer
credential_to_issue_list = {
                    'Pass' : 'Pass',
                   'AragoPass' : 'Pass Arago',
                   'InfrachainPass' : 'Pass Infrachain',
                    'BloometaPass' : 'Bloometa card',
                    'TezVoucher_1' : 'Tezotopia 10% voucher (fake)',
                    'LearningAchievement' : 'Diploma (Learning achievement)',
                    'VerifiableDiploma' : 'Diploma EBSI (Verifiable Diploma)',
                    'StudentCard' : 'Student card',
                    'CertificateOfEmployment' : 'Certificate of employment',
                    'TalaoCommunity' : 'Talao Community card',
                    "VotersCard" : "Voter Card",
                    'PhoneProof' : 'PhoneProof',
                }

# issuer for guest
credential_to_issue_list_for_guest = {
                    'Pass' : 'Pass',
                }

# for issuer
credential_requested_list = {
                    'EmailPass' : 'Proof of email',
                    'AgeRange' : 'Age range',
                    'Nationality' : 'Nationality',
                    'Gender' : 'Gender card',
                    'PhoneProof' : 'Proof of phone number',
                    'IdCard' : 'Identity card',
                    'Over18' : 'Proof of majority (Over 18)',
                    'Over13' : 'Over 13',
                    'PassportNumber' : 'Passport footprint',                  
                    "TezosAssociatedAddress" : "Proof of Tezos blockchain account",
                    "EthereumAssociatedAddress" : "Proof of Ethereum blockchain account",
                    "AllAddress" : "Proof of blockchain crypto account",
                    "AragoPass" : "Arago Pass",
                    "login" : "Login and password",
                    "secret" : "Secret",
                    "totp" : "Time-based OTP",
                    'DID' : "None",
                }

# for issuer for 2, 3 and 4th credential
credential_requested_list_2 = {
                    'EmailPass' : 'Proof of email',
                    'AgeRange' : 'Age range',
                    'Nationality' : 'Nationality',
                    'Gender' : 'Gender card',
                    'PhoneProof' : 'Proof of phone number',
                    'IdCard' : 'Identity card',
                    'Over18' : 'Proof of majority (Over 18)',
                    'Over13' : 'Over 13',
                    'PassportNumber' : 'Passport footprint',                  
                    "TezosAssociatedAddress" : "Proof of Tezos blockchain account",
                    "EthereumAssociatedAddress" : "Proof of Ethereum blockchain account",
                    "AllAddress" : "Proof of blockchain account",
                    "AragoPass" : "Arago Pass",
                    'DID' : "None",
                }

# issuer
landing_page_style_list = {
                    "op_issuer_qrcode.html" : "Style 1",
                    "op_issuer_qrcode_2.html" : "Style 2",
                    "op_issuer_qrcode_emailpass.html" : "EmailPass card",
                    "op_issuer_qrcode_phoneproof.html" : "PhoneProof card",
                    "op_issuer_qrcode_bloometa.html" : "Bloometa pass"
                }

# verifier
verifier_landing_page_style_list = {
                    "op_verifier_qrcode.html" : "Style 1",
                    "op_verifier_qrcode_2.html" : "Style 2",
                    "op_verifier_qrcode_3.html" : "Style 3",
                    "op_verifier_qrcode_4.html" : "Altme",
                    "op_verifier_qrcode_5.html" : "Style 2 with counter",
                     "arago_verifier_qrcode.html" : "Arago Style"
                }


protocol_list = {'w3cpr' : "W3C Presentation Request ",
                 'siopv2' : 'Siop V2 EBSI implementation',
                  'siopv2_openid' : 'Siop V2 OpenID implementation'
                 }

pre_authorized_code_list = {'none' : "None",
                 'pac' : 'Pre authorized code',
                  'pac_pin' : 'Pre authorized code + PIN code'
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
                        },
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

model_three = {
            "type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": [
                        {
                            "example" : {"type" : ""},
                            "reason": [{"@language": "en","@value": ""}]
                        },
                        {
                            "example" : {"type" : ""},
                            "reason": [{"@language": "en","@value": ""}]
                        },
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
           "challenge": "",
           "domain" : ""
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
                "sbt_name" : "",
                "sbt_description" : "",
                "sbt_display_uri" : "",
                "sbt_thumbnail_uri" : "",
                "sbt_artifact_uri" : "",
                "sbt_network" : "none",
                "beacon_mode" : "issuer",
                "pre_authorized_code" : "no",
                "beacon_payload_message" : "Any string for a message to display",
                "pkce" : None,
                "tezid_proof_type" : "",
                "tezid_network" : "none",
                "vc" : "DID",
                "vc_issuer_id" : "",
                "vc_2" : "DID",
                "totp_interval" : "30", 
                "standalone" : None, # data are NOT transfered to application by default
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
                "reason" : " ",
                "reason_2" : " ",
                "reason_3" : " ",
                "reason_4" : " ",
                "credential_requested" : "DID",
                "credential_requested_2" : "DID",
                "credential_requested_3" : "DID",
                "credential_requested_4" : "DID",
                "credential_to_issue" : "Pass",
                "protocol" : "w3cpr",
                "landing_page_style" : "op_issuer_qrcode.html",
                "verifier_landing_page_style" : "op_verifier_qrcode_2.html",
                "page_title" : "Page title",
                "page_subtitle" : "Page subtitle",
                "page_description" : "Add here a credential description as you would like to see it displayed on the landing page of your app.",
                "page_background_color" : "#ffffff",
                "page_text_color" : "#000000",
                "card_title" : "Card title",
                "card_subtitle" : "Card subtitle",
                "card_description" : "Add here a credential description as you would like to see it displayed in the wallet.",
                "card_background_color" : "#ec6f6f",
                "card_text_color" : "#ffffff",
                "credential_duration" : "365",
                "qrcode_background_color" :"#ffffff",
                "qrcode_message" : "Scan with your wallet",
                "mobile_message" : "Open your wallet",
                "contact_email" : "support@altme.io",
                "contact_name" : "",
                "secret" : "", # static or OTP
                "landing_page_url" : "https://talao.io",
                "privacy_url" : "https://talao.co/md_file?file=privacy",
                "terms_url" : "https://talao.co/md_file?file=terms_and_conditions", 
                "title" : "Get it !" # QR code title
                }
