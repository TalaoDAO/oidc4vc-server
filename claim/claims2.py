myclaim = {
    "vp_token": {
        "presentation_definition": {
            "id": "vp token example",
            "input_descriptors": [
                {
                    "id": "vid credential",
                    "format": {
                        "jwt_vc": {
                            "proof_type": ["JsonWebSignature2020"]
                        }
                    },
                    "constraints": {
                        "fields": [
                            {
                                "path": [
                                    "$.credentialSchema.id"
                                ],
                                "filter": {
                                    "type": "string",
                                    "pattern": "https://api.preprod.ebsi.eu/trusted-schemas-registry/v1/schemas/0xad457662a535791e888994e97d7b5e0cdd09fbae2c8900039d2ee2d9a64969b1"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }
}