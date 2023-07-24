profile = {

    "EBSIV2" :
        {
            "issuer_vc_type" : "jwt_vc",
            "verifier_vp_type" : "jwt_vp",
            "offer_prefix" : "openid://initiate_issuance",
            "presentation_prefix" : 'openid://',
            'cryptographic_binding_methods_supported' : ['DID'],
            'cryptographic_suites_supported' : ['ES256K','ES256','ES384','ES512','RS256'],
            'subject_syntax_types_supported' : ['did:ebsi'],
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            'credential_supported' : ['VerifiableDiploma', 'VerifiableId'],
            'schema_for_type' : True,
            'oidc4vci_draft' : 'https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#abstract',
            'siopv2_draft' : '',
            'service_documentation' : 'It is the profile of the EBSI V2 compliant test. DID for natural person is did:ebsi. \
                The schema url is used as the VC type in the credential offer QR code. \
                The prefix openid_initiate_issuance://'
        }, 
    "EBSIV3" :
        {
            "issuer_vc_type" : "jwt_vc",
            "verifier_vp_type" : "jwt_vp",
            "offer_prefix" : "openid://initiate_issuance",
            "presentation_prefix" : 'openid-vc://',
            'cryptographic_binding_methods_supported' : ['DID'],
            'credential_supported' : ['VerifiableDiploma', 'VerifiableId'],
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            'cryptographic_suites_supported' : ['ES256K','ES256','ES384','ES512','RS256'],
            'subject_syntax_types_supported' : ['did:key'],
            'schema_for_type' : False,
            'oidc4vci_draft' : 'https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html',
            'service_documentation' : 'New environment for V3 compliance test'

        },
     "GAIAX-COMMUNITY" :
        {
            "issuer_vc_type" : "ldp_vc",
            "verifier_vp_type" : "ldp_vp",
            "offer_prefix" : "openid-initiate-issuance://" ,
            "presentation_prefix" : "openid-vc://",
            "cryptographic_binding_methods_supported" : ('DID'),
            'credential_supported' : ['EmployeeCredential'],
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            "cryptographic_suites_supported" : ['ES256K','ES256','ES384','ES512','RS256'],
            "subject_syntax_types_supported" : ['did:key'],
            "schema_for_type" : False,
            "oidc4vci_draft" : "https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html",
            'service_documentation' : 'Issuer pour projet Docaposte Gaia-X'

        },
    "DEFAULT" :
        {
            "issuer_vc_type" : "ldp_vc",
            "verifier_vp_type" : "ldp_vp",
            "offer_prefix" : "openid-credential-offer://" ,
            "presentation_prefix" : "openid-vc://",
            "cryptographic_binding_methods_supported" : ('DID'),
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            "cryptographic_suites_supported" : ['ES256K','ES256','ES384','ES512','RS256'],
            "subject_syntax_types_supported" : ['did:ebsi', 'did:key', 'did:ethr', 'did:tz'],
            "schema_for_type" : False,
            "oidc4vci_draft" : "https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html",
            'service_documentation' : 'Last release of the OIDC4VC documentation'

        },
    "ARF" :
        {
            "issuer_vc_type" : "jwt_vc",
            "verifier_vp_type" : "jwt_vp",
            "offer_prefix" : "openid-credential-offer://" ,
            "presentation_prefix" : 'openid-vc://',
            'cryptographic_binding_methods_supported' : ('DID'),
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            'cryptographic_suites_supported' : ['ES256K','ES256','ES384','ES512','RS256'],
            'subject_syntax_types_supported' : ['did:ebsi', 'did:key', 'did:ethr', 'did:tz'],
            'schema_for_type' : False,
            'service_documentation' : 'EUDI wallet profile -> JWT format with x509 certificates for keys'
        },
    "JWTVC" :
        {
            "issuer_vc_type" : "jwt_vc",
            "verifier_vp_type" : "jwt_vp",
            "presentation_prefix" : 'openid-vc://',
            'cryptographic_binding_methods_supported' : ('DID'),
            'cryptographic_suites_supported' : ['ES256K','ES256','ES384','ES512','RS256'],
            'subject_syntax_types_supported' : ['did:ion'],
            'schema_for_type' : False,
            'service_documentation' : 'https://identity.foundation/jwt-vc-presentation-profile/'

        },

}
