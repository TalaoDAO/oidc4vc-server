from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes

import environment
from protocol import contractsToOwners, ownersToContracts, update_self_claims
import constante
import os
import privatekey
import ns
import Talao_message 

"""
# Environment variables set in gunicornconf.py  and transfered to environment.py
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')
# Environment setup
mode = environment.currentMode(mychain,myenv)
"""


filename = 'talao.key'
with open(filename, "rb") as key_file:
    CA_key = serialization.load_pem_private_key(key_file.read(),password=None,)


issuer = x509.Name([
x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
x509.NameAttribute(NameOID.LOCALITY_NAME, "Paris"),
x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Talao"),
x509.NameAttribute(NameOID.DOMAIN_COMPONENT, "talao.io"),
x509.NameAttribute(NameOID.POSTAL_ADDRESS, "16 rue de wattignies, 75012 Paris"),
x509.NameAttribute(NameOID.COMMON_NAME, "talao"),])


"""
# certificate for CA Talao

cert = x509.CertificateBuilder()
cert = cert.subject_name(issuer)
cert = cert.issuer_name(issuer)
cert = cert.public_key( CA_key.public_key())
cert=cert.serial_number(x509.random_serial_number())
cert=cert.not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=10))
cert=cert.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=100))
cert=cert.add_extension(x509.BasicConstraints(ca=True, path_length=None),critical=True)
cert = cert.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                data_encipherment=True,
                key_agreement=True,
                content_commitment=True,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False
            ),
            critical=False
        )
cert=cert.sign(CA_key, hashes.SHA256())

# Write CA certificate out to disk.
with open("talao.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

"""

#############certificate for user

filename = 'thierry.key'
with open(filename, "rb") as key_file:
    subject_key = serialization.load_pem_private_key(key_file.read(),password=None,)

def generate_X5019(name,email, subject_key, issuer) :


    subject = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, ""),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Paris"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, ""),
    x509.NameAttribute(NameOID.COMMON_NAME, name),
    x509.NameAttribute(NameOID.EMAIL_ADDRESS, email),
    x509.NameAttribute(NameOID.USER_ID, "did:talao:talaonet:81d8800eDC8f309ccb21472d429e039E0d9C79bB"),])


    cert = x509.CertificateBuilder()
    cert = cert.subject_name(subject)
    cert = cert.issuer_name(issuer)
    cert = cert.public_key( subject_key.public_key())
    cert=cert.serial_number(x509.random_serial_number())
    cert=cert.not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=10))
    cert=cert.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=100))
    cert=cert.add_extension(x509.BasicConstraints(ca=False, path_length=None),critical=True)
    cert = cert.add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.EMAIL_PROTECTION,
                                                    x509.oid.ExtendedKeyUsageOID.CODE_SIGNING,
                                                    x509.oid.ExtendedKeyUsageOID.TIME_STAMPING]), critical=True)
    cert=cert.add_extension(x509.SubjectAlternativeName([x509.RFC822Name(email)]),critical=True,)
    cert = cert.add_extension(x509.KeyUsage(digital_signature=True,
                                            key_encipherment=True,
                                            data_encipherment=True,
                                            key_agreement=True,
                                            content_commitment=False,
                                            key_cert_sign=False,
                                            crl_sign=False,
                                            encipher_only=False,
                                            decipher_only=False ), critical=True)
    cert=cert.sign(CA_key, hashes.SHA256())
    # Write our certificate out to disk.
    with open(name + ".pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    certificate = pkcs12.serialize_key_and_certificates(bytes(name + " Certificat", 'utf-8'), subject_key, cert, None, serialization.BestAvailableEncryption(b'suc2cane'))
    with open(name +".p12", "wb") as f:
        f.write(certificate)


generate_X5019('Thierry Thevenet Talao','thierry.thevenet@talao.io', subject_key, issuer)
generate_X5019('Thierry Thevenet Yahoo','thevenet_thierry@yahoo.fr', subject_key, issuer)