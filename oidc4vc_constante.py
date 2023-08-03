


user = {
        "login_name" : "",
        "did" : "",
        "client_id" : []
}

"""
ebsi_vc_type_list = {
    "jwt_vc" : "JWT-JSON",
    "ldp_vc" : "JSON-LD"
}
"""


oidc4vc_profile_list = {
    'EBSI-V2' : 'EBSI V2',
    'DEFAULT' : 'Default profile',
    'GAIA-X' : 'GAIA-X projects',
    'EBSI-V3' : 'EBSI V3',
    'JWT-VC' : 'JWT-VC presentation profile',
    'HEDERA' : 'Hedera projects'
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


type_2_schema = {
    'VerifiableId' : 'https://api-conformance.ebsi.eu/trusted-schemas-registry/v2/schemas/z22ZAMdQtNLwi51T2vdZXGGZaYyjrsuP1yzWyXZirCAHv',
    'VerifiableDiploma'  : 'https://api.preprod.ebsi.eu/trusted-schemas-registry/v1/schemas/0xbf78fc08a7a9f28f5479f58dea269d3657f54f13ca37d380cd4e92237fb691dd' 
} 




# OIDC4VC issuer
ebsi_credential_requested_list = {
                    'https://api-conformance.ebsi.eu/trusted-schemas-registry/v2/schemas/z22ZAMdQtNLwi51T2vdZXGGZaYyjrsuP1yzWyXZirCAHv' : 'VerifiableId',
                    'https://api.preprod.ebsi.eu/trusted-schemas-registry/v1/schemas/0xbf78fc08a7a9f28f5479f58dea269d3657f54f13ca37d380cd4e92237fb691dd' : 'VerifiableDiploma',
                    'DID' : "None"
                }


# issuer
landing_page_style_list = {
                    "./ebsi/ebsi_issuer_qrcode.html" : "Style",
                    "./ebsi/ebsi_issuer_qrcode_test.html" : "Test"
                }


# verifier
ebsi_verifier_landing_page_style_list = {
                    "./ebsi/ebsi_verifier_qrcode_2.html" : "Style 2",
                    "./ebsi/ebsi_verifier_qrcode_test.html" : "Test",
                    "./ebsi/diploma_verifier.html" : "Diplome Tezos Ebsi"

}


pre_authorized_code_list = {'none' : "None",
                 'pac' : 'Pre authorized code',
                  'pac_pin' : 'Pre authorized code + PIN code'
                 }



client_data_pattern_ebsi = {
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
                "page_background_color" : "#ffffff",
                "page_text_color" : "#000000",
                "credential_duration" : "365",
                "qrcode_background_color" :"#ffffff",
                "qrcode_message" : "Scan with your wallet",
                "mobile_message" : "Open your wallet",
                "contact_email" : "support@altme.io",
                "contact_name" : "",
                "landing_page_url" : "https://talao.io",
                "privacy_url" : "https://altme.io/privacy",
                "terms_url" : "https://altme.io/cgu", 
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


