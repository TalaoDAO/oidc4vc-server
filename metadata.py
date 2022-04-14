import base64
import subprocess


my_metadata = bytearray('{"did":"did:web:demo.talao.co", "email" : "googandads@gmail.com"}', 'utf-8')

def metadata(metadata) :
    with open("passbase-test-private-key.pem", "rb") as f:
        p = subprocess.Popen(
            "openssl rsautl -sign -inkey " + f.name,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        signature, stderr = p.communicate(input=metadata)
        encrypted_metadata = base64.b64encode(signature)
    return encrypted_metadata.decode()

print(metadata(my_metadata))

