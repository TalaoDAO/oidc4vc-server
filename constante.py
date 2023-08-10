
user = {
        "login_name" : "",
        "did" : "",
        "client_id" : []
}



oidc4vc_profile_list = {
    'DEFAULT' : 'DEFAULT (ldp_vc, ldp_vp)',
    'GAIA-X' : 'GAIA-X',
    'EBSI-V3' : 'EBSI V3',
    'JWT-VC' : 'JWT-VC presentation profile',
    'HEDERA' : 'HEDERA (jwt_vc, jwt_vp)'
}



#OIDC4VC Verifier
ebsi_verifier_credential_list = {
    "DID" : "Authentication (id_token)",
    "None" : "None",
    'VerifiableId' :  'Verifiable ID (vp_token)',
    'VerifiableDiploma' : 'EBSI Diploma (vp_token)',
    'EmployeeCredential' : 'Employee Credential (vp_token)',
    'ProofOfAsset' : 'Carbon credit projects',
    'EmailPass' : 'Email proof (vp_token)',
    'PhoneProof' : 'Phone proof (vp_token)',
    'DeviceInfo' : 'Device information (vp_token)'
}




# issuer
landing_page_style_list = {
                    "./issuer_oidc/issuer_qrcode.html" : "Style",
                    "./issuer_oidc/issuer_qrcode_test.html" : "Test"
                }


# verifier
ebsi_verifier_landing_page_style_list = {
                    "./ebsi/ebsi_verifier_qrcode_2.html" : "Style 2",
                    "./ebsi/ebsi_verifier_qrcode_test.html" : "Test",

}


pre_authorized_code_list = {'none' : "None",
                 'pac' : 'Pre authorized code',
                  'pac_pin' : 'Pre authorized code + PIN code'
                 }



client_data_pattern = {
                "profile" : "DEFAULT",
                "pkce" : None,
                "request_uri" : None,
                "vc" : "DID",
                "vc_2" : "DID",
                "user" : "guest",
                "client_id" :  "",
                "client_secret" : "",
                "callback" : "https://altme.io",
                "jwk" : "",
                "did": "did:web:app.altme.io:issuer",
                "verification_method" : "did:web:app.altme.io:issuer#key-1",
                "issuer_landing_page" : "./ebsi/ebsi_issuer_qrcode_test.html",     
                "note" : "",
                "company_name" : "New company",
                "application_name" : "Application name",
                "reason" : "This purpose 1",
                "reason_2" : "This is purpose 2 ",
                "reason_3" : "This is purpose 3 ",
                "reason_4" : "This purpose 4",
                "credential_requested" : "DID",
                "credential_requested_2" : "DID",
                "credential_requested_3" : "DID",
                "credential_requested_4" : "DID",
                "landing_page_style" : "./ebsi/ebsi_issuer_qrcode_test.html",
                "verifier_landing_page_style" : "./ebsi/ebsi_verifier_qrcode_2.html",
                "page_title" : "Page title",
                "page_subtitle" : "Page subtitle",
                "page_description" : "Add here a credential description as you would like to see it displayed on the landing page of your app.",
                "credential_duration" : "365",
                "qrcode_message" : "Scan with your wallet",
                "mobile_message" : "Open your wallet",
                "contact_email" : "support@altme.io",
                "contact_name" : "",
                "landing_page_url" : "https://talao.io",
                "title" : "Get it !" # QR code title
                }

ebsi_verifier_claims = {
    "vp_token":{
        "presentation_definition": {
            "id":"",
            "input_descriptors":[],
            "format":""
        }
    }
}


