import base64
import subprocess
import sys
import os

my_metadata = bytearray('{"did":"did:web:demo.talao.co", "email" : "googandads@gmail.com"}', 'utf-8')


def build_metadata(metadata) :
    with open("input.txt", "wb") as f:
        f.write(metadata)
        f.close()
    os.system("openssl rsautl -sign -inkey passbase-test-private-key.pem -out output.txt -in input.txt")
    with open("output.txt", "rb") as f:
        signature = f.read()
        f.close()
    encrypted_metadata = base64.b64encode(signature)
    return (encrypted_metadata.decode())



def build_metadata(metadata) :
    with open("passbase-test-private-key.pem", "rb") as f:
        p = subprocess.Popen(
            "openssl rsautl -sign -inkey " + f.name,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        signature, stderr = p.communicate(input=metadata)
        print('erreur = ', stderr)
        encrypted_metadata = base64.b64encode(signature)
    return encrypted_metadata.decode()