profile = {

   
    "EBSI-V3" : # TODO completed
        {
            "issuer_vc_type" : "jwt_vc",
            "verifier_vp_type" : "jwt_vp",
            "oidc4vci_prefix" : "openid-credential-offer://",
            "siopv2_prefix" : 'openid-vc://',
            "oidc4vp_prefix" : 'openid-vc://',
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
     "DEFAULT" :
        {
            "issuer_vc_type" : "ldp_vc",
            "verifier_vp_type" : "ldp_vp",
            "oidc4vci_prefix" : "openid-credential-offer://" ,
            "siopv2_prefix" : "openid-vc://",
            "oidc4vp_prefix" : "openid-vc://",
            "cryptographic_binding_methods_supported" : ('DID'),
            'credential_supported' : ['EmployeeCredential',  'VerifiableId', 'EmailPass'],
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            "cryptographic_suites_supported" : ['ES256K','ES256','ES384','ES512','RS256'],
            "subject_syntax_types_supported" : ['did:key'],
            "schema_for_type" : False,
            'service_documentation' : 'We use JSON-LD VC and VP and last release of the specs. \
                oidc4vci_draft : https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html \
                siopv2_draft : https://openid.net/specs/openid-connect-self-issued-v2-1_0.html \
                oidc4vp_draft : https://openid.net/specs/openid-4-verifiable-presentations-1_0.html  \
                 '
        },
         "GAIA-X" :
        {
            "issuer_vc_type" : "ldp_vc",
            "verifier_vp_type" : "ldp_vp",
            "oidc4vci_prefix" : "openid-initiate-issuance://" ,
            "presentation_prefix" : "openid-vc://",
            "cryptographic_binding_methods_supported" : ('DID'),
            'credential_supported' :  ['EmployeeCredential',  'VerifiableId', 'EmailPass'],
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            "cryptographic_suites_supported" : ['ES256K','ES256','ES384','ES512','RS256'],
            "subject_syntax_types_supported" : ['did:key'],
            "schema_for_type" : False,
            'service_documentation' : 'THIS PROFILE OF OIDC4VCI IS DEPRECATED. \
                oidc4vci_draft : https://openid.net/specs/openid-connect-4-verifiable-credential-issuance-1_0-05.html#name-credential-endpoint \
                siopv2_draft : https://openid.net/specs/openid-connect-self-issued-v2-1_0.html \
                oidc4vp_draft : https://openid.net/specs/openid-4-verifiable-presentations-1_0.html  \
                 '
        },
        "HEDERA" :
        {
            "issuer_vc_type" : "jwt_vc",
            "verifier_vp_type" : "jwt_vp",
            "oidc4vci_prefix" : "openid-credential-offer-hedera://" ,
            "presentation_prefix" : "openid-hedera://",
            "cryptographic_binding_methods_supported" : ('DID'),
            'credential_supported' :  ['EmployeeCredential', 'VerifiableId', 'EmailPass', 'AgeOver18'],
            "grant_types_supported": [
                "authorization_code",
                "urn:ietf:params:oauth:grant-type:pre-authorized_code"
            ],
            "cryptographic_suites_supported" : ['ES256K','ES256','ES384','ES512','RS256'],
            "subject_syntax_types_supported" : ['did:key', 'did:pkh'],
            "schema_for_type" : False,
            'service_documentation' : 'WORK IN PROGRESS EON project. last release of the specs. \
                oidc4vci_draft : https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html \
                siopv2_draft : https://openid.net/specs/openid-connect-self-issued-v2-1_0.html \
                oidc4vp_draft : https://openid.net/specs/openid-4-verifiable-presentations-1_0.html  \
                 Issuer and verifier for marjetplace and WCM'
        },
    
    "JWT-VC" :
        {
            "verifier_vp_type" : "jwt_vp",
            "siopv2_prefix" : 'openid-vc://',
            'cryptographic_binding_methods_supported' : ('DID'),
            'credential_supported' : ['EmployeeCredential', 'VerifiableId', 'EmailPass'],
            'cryptographic_suites_supported' : ['ES256K','ES256','ES384','ES512','RS256'],
            'subject_syntax_types_supported' : ['did:ion', 'did:web'],
            'schema_for_type' : False,
            'service_documentation' : 'https://identity.foundation/jwt-vc-presentation-profile/'

        },

}
