import base64
import subprocess
import sys
import os
import json

did = "did:web:demo.talao.co"
email =  "googandads@gmail.com"
data = json.dumps({"did" : did, "email" : email})
my_metadata = bytearray(data, 'utf-8')


def build_metadata(metadata) :
    with open("passbase-test-private-key.pem", "rb") as f:
        p = subprocess.Popen(
            "/usr/bin/openssl rsautl -sign -inkey " + f.name,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        signature, stderr = p.communicate(input=metadata)
        print('erreur = ', stderr)
        encrypted_metadata = base64.b64encode(signature)
    return encrypted_metadata.decode()

print(build_metadata(my_metadata))