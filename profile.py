profile = {

    "EBSIV2" :
        {
            "issuer_vc_type" : "jwt_vc", ## jwt_vc_json, jwt_vc_json-ld, ldp_vc
            "verifier_vp_type" : "jwt_vp",
            "oidc4vci_prefix" : "openid://initiate_issuance",
            "siopv2_prefix" : 'openid://',
            "oidc4vp_prefix" : 'openid://',
            "cryptographic_binding_methods_supported" : ['DID'],
            'cryptographic_suites_supported' : ['ES256K','ES256','ES384','ES512','RS256'],
            'subject_syntax_types_supported' : ['did:ebsi'],
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            'credential_supported' : ['VerifiableDiploma', 'VerifiableId'],
            'schema_for_type' : True,
            'service_documentation' : 'EBSI V2 COMPLIANCE. It is the profile of the EBSI V2 compliant test. DID for natural person is did:ebsi. \
                The schema url is used as the VC type in the credential offer QR code. \
                The prefix openid_initiate_issuance:// \
                oidc4vci_draft : https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#abstract',
        }, 
     "CUSTOM" :
        {
            "issuer_vc_type" : "jwt_vc",
            "verifier_vp_type" : "jwt_vp",
            "oidc4vci_prefix" : "openid-initiate-issuance://" ,
            "siopv2_prefix" : 'openid://',
            "oidc4vp_prefix" : 'openid://',
            "cryptographic_binding_methods_supported" : ['DID'],
            'cryptographic_suites_supported' : ['ES256K','ES256','ES384','ES512','RS256'],
            'subject_syntax_types_supported' : ['did:key'],
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            'credential_supported' : ['VerifiableDiploma', 'VerifiableId', 'EmployeeCredential'],
            'schema_for_type' : True,
            'service_documentation' : '??? out of date issuer',
        }, 
    "EBSIV3" :
        {
            "issuer_vc_type" : "jwt_vc",
            "verifier_vp_type" : "jwt_vp",
            "oidc4vci_prefix" : "openid://initiate_issuance",
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
            'service_documentation' : 'New environment for V3 compliance test'

        },
     "GAIAX" :
        {
            "issuer_vc_type" : "ldp_vc",
            "verifier_vp_type" : "ldp_vp",
            "oidc4vci_prefix" : "openid-initiate-issuance://" ,
            "presentation_prefix" : "openid-vc://",
            "cryptographic_binding_methods_supported" : ('DID'),
            'credential_supported' : ['EmployeeCredential', 'VerifiableId'],
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            "cryptographic_suites_supported" : ['ES256K','ES256','ES384','ES512','RS256'],
            "subject_syntax_types_supported" : ['did:key'],
            "schema_for_type" : False,
            'service_documentation' : 'WORK IN PROGRESS. WE use JSON-LD VC and VP and last release of the specs. \
                oidc4vci_draft : https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html \
                siopv2_draft : https://openid.net/specs/openid-connect-self-issued-v2-1_0.html \
                oidc4vp_draft : https://openid.net/specs/openid-4-verifiable-presentations-1_0.html  \
                 Issuer pour projet Docaposte Gaia-X'

        },
    "DEFAULT" :
        {
            "issuer_vc_type" : "jwt_vc",
            "verifier_vp_type" : "jwt_vp",
            "oidc4vci_prefix" : "openid-credential-offer://" ,
            "siopv2_prefix" : 'siopv2://',
            "oidc4vp_prefix" : 'oidc4vp://',
            'credential_supported' : ['EmployeeCredential', 'VerifiableId'],
            "cryptographic_binding_methods_supported" : ('DID'),
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            "cryptographic_suites_supported" : ['ES256K','ES256','ES384','ES512','RS256'],
            "subject_syntax_types_supported" : ['did:key'],
            "schema_for_type" : False,
            'service_documentation' : 'Last release of the OIDC4VC documentation \
             oidc4vci_draft : https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html \
                siopv2_draft : https://openid.net/specs/openid-connect-self-issued-v2-1_0.html \
                oidc4vp_draft : https://openid.net/specs/openid-4-verifiable-presentations-1_0.html  \
                 '

        },
    "ARF" :
        {
            "issuer_vc_type" : "jwt_vc",
            "verifier_vp_type" : "jwt_vp",
            "oidc4vci_prefix" : "openid-credential-offer://" ,
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
            "siopv2_prefix" : 'openid-vc://',
            'cryptographic_binding_methods_supported' : ('DID'),
            'cryptographic_suites_supported' : ['ES256K','ES256','ES384','ES512','RS256'],
            'subject_syntax_types_supported' : ['did:ion'],
            'schema_for_type' : False,
            'service_documentation' : 'https://identity.foundation/jwt-vc-presentation-profile/'

        },

}
