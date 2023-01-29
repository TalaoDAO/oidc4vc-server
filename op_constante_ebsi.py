
user = {
        "login_name" : "",
        "did" : "",
        "client_id" : []
}

ebsi_vc_type_list = {
    "jwt_vc" : "JWT-JSON",
    "ldp_vc" : "JSON-LD"
}

ebsi_vp_type_list = {
    "jwt_vp" : "jwt_vp",
    #"ldp_vp" : "ldp_vp",
}


#EBSI Verifier
ebsi_verifier_credential_list = {
    "DID" : "None",
    'https://api-conformance.ebsi.eu/trusted-schemas-registry/v2/schemas/z22ZAMdQtNLwi51T2vdZXGGZaYyjrsuP1yzWyXZirCAHv' : 'VerifiableId',
    'https://api.preprod.ebsi.eu/trusted-schemas-registry/v1/schemas/0xbf78fc08a7a9f28f5479f58dea269d3657f54f13ca37d380cd4e92237fb691dd' : 'VerifiableDiploma',
}


# EBSI issuer
ebsi_credential_to_issue_list = {
                   'https://api-conformance.ebsi.eu/trusted-schemas-registry/v2/schemas/z22ZAMdQtNLwi51T2vdZXGGZaYyjrsuP1yzWyXZirCAHv' : 'VerifiableId',
                    'https://api.preprod.ebsi.eu/trusted-schemas-registry/v1/schemas/0xbf78fc08a7a9f28f5479f58dea269d3657f54f13ca37d380cd4e92237fb691dd' : 'VerifiableDiploma',
                    'DID' : 'None'
                } 

# EBSI issuer
ebsi_credential_requested_list = {
                    'https://api-conformance.ebsi.eu/trusted-schemas-registry/v2/schemas/z22ZAMdQtNLwi51T2vdZXGGZaYyjrsuP1yzWyXZirCAHv' : 'VerifiableId',
                    'https://api.preprod.ebsi.eu/trusted-schemas-registry/v1/schemas/0xbf78fc08a7a9f28f5479f58dea269d3657f54f13ca37d380cd4e92237fb691dd' : 'VerifiableDiploma',
                    'DID' : "None"
                }


# issuer
landing_page_style_list = {
                    "./ebsi/ebsi_issuer_qrcode_1.html" : "Style 1",
                    "./ebsi/ebsi_issuer_qrcode_2.html" : "Style 2",
                    "./ebsi/ebsi_issuer_qrcode_test.html" : "EBSI issuer test"
                }


# verifier
ebsi_verifier_landing_page_style_list = {
                    "./ebsi/ebsi_verifier_qrcode_1.html" : "Style 1 ",
                    "./ebsi/ebsi_verifier_qrcode_2.html" : "Style 2",
                    "./ebsi/ebsi_verifier_qrcode_3.html" : "Style 3",
                    "./ebsi/ebsi_verifier_qrcode_6.html" : "Style 2 with html",
                    "./ebsi/ebsi_verifier_qrcode_test.html" : "EBSI test"
}


pre_authorized_code_list = {'none' : "None",
                 'pac' : 'Pre authorized code',
                  'pac_pin' : 'Pre authorized code + PIN code'
                 }


client_data_pattern_ebsi = {
                "ebsi_vp_type" : "jwt_vp",
                "ebsi_issuer_vc_type" : "jwt_vc",
                "pkce" : None,
                "vc" : "DID",
                "vc_issuer_id" : "",
                "vc_2" : "DID",
                "pre-authorized_code" : "", 
                "user" : "guest",
                "client_id" :  "",
                "client_secret" : "",
                "callback" : "https://altme.io",
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
                "credential_to_issue" : "https://api.preprod.ebsi.eu/trusted-schemas-registry/v1/schemas/0xbf78fc08a7a9f28f5479f58dea269d3657f54f13ca37d380cd4e92237fb691dd",
                "credential_to_issue_2" : "None",
                "protocol" : "w3cpr",
                "landing_page_style" : "./ebsi/ebsi_issuer_qrcode_test.html",
                "verifier_landing_page_style" : "op_verifier_qrcode_2.html",
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
    "id_token":{
        "email": None
    },
    "vp_token":{
        "presentation_definition": {
            "id":"",
            "input_descriptors":[],
            "format":""
        }
    }
}

input_descriptor = {
                    "id":"",
                    "name":"",
                    "purpose":"",
                    "constraints":{
                        "fields":[
                            {
                                "path":["$.vc.credentialSchema"],
                                "filter": ""
                            }
                        ]
                    }
                }

filter = {
            "allOf":[
                {
                    "type":"array",
                    "contains":{
                        "type":"object",
                        "properties":{
                            "id":{
                                "type":"string",
                                "pattern":""
                            }
                        },
                        "required":["id"]
                    }
                }
            ]
        }


