"""

$python encrypt.py <jwk file>

store encypted_issuer_key.txt on server
store fernet_key in a password file

https://cryptography.io/en/latest/#welcome-to-pyca-cryptography

"""

from cryptography.fernet import Fernet
import sys

# generate a Fernet key and save it in text file
fernet_key = Fernet.generate_key()
with open('fernet_key.txt', 'w') as outfile :
    outfile.write(fernet_key.decode())

# upload issuer key in clear text format and compact
filename = sys.argv[1]
with open(filename, 'r') as outfile :
    signer_jwk_key = outfile.read().replace(" ","")

# encrypt the issuer key with the Fernet key 
f = Fernet(fernet_key)
encrypted_issuer_key = f.encrypt(signer_jwk_key.encode())
with open('encrypted_issuer_key.txt', 'w') as outfile :
    outfile.write(encrypted_issuer_key.decode())


###########################
"""
to decrypt an encrypted issuer key stored in a text file  "encrypted_issuer_key.txt" 
with a Fernet key read from the paswword file
This as to be added to our code
"""
from cryptography.fernet import Fernet

def decrypt(fernet_key: str)-> str :
    f = Fernet(fernet_key)
    with open('encrypted_issuer_key.txt', 'r') as outfile :
        encrypted_issuer_key = outfile.read()
    return f.decrypt(encrypted_issuer_key.encode()).decode()

# for testing purpose
print("issuer key = ", decrypt(fernet_key))
