from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization
from flask import session
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
import os


from protocol import contractsToOwners
from components import privatekey, ns
from signaturesuite import helpers


def generate_CA(mode) :
    # upload RSA private pem 
    talao_rsa_private_key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
    if type(talao_rsa_private_key) == bytes :
        talao_rsa_key = serialization.load_pem_private_key(talao_rsa_private_key,password=None,)
    else :
        talao_rsa_key = serialization.load_pem_private_key(bytes(talao_rsa_private_key, 'utf-8'),password=None,)


    # Talao as Conformity Authority
    talao_issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Paris"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Talao"),
    x509.NameAttribute(NameOID.DOMAIN_COMPONENT, "talao.io"),
    #x509.NameAttribute(NameOID.POSTAL_ADDRESS, "16 rue de wattignies, 75012 Paris"),
    x509.NameAttribute(NameOID.COMMON_NAME, "talao"),
    x509.NameAttribute(NameOID.USER_ID, 'did:web:talao.io'),])

    # issue CA certificate for Talao
    cert = x509.CertificateBuilder()
    cert = cert.subject_name(talao_issuer)
    cert = cert.issuer_name(talao_issuer)
    cert = cert.public_key( talao_rsa_key.public_key())
    cert=cert.serial_number(x509.random_serial_number())
    cert=cert.not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
    cert=cert.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
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
    cert=cert.sign(talao_rsa_key, hashes.SHA256())

    # Write this CA certificate out to disk.
    with open('talao.pem', "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    return 


############# generate certificate for user

def generate_X509(workspace_contract, password, mode) :

    did = helpers.ethereum_pvk_to_DID(session['private_key_value'], session['method'])

    talao_issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Paris"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Talao"),
    x509.NameAttribute(NameOID.DOMAIN_COMPONENT, "talao.io"),
    #x509.NameAttribute(NameOID.POSTAL_ADDRESS, "16 rue de wattignies, 75012 Paris"),
    x509.NameAttribute(NameOID.COMMON_NAME, "talao"),
    x509.NameAttribute(NameOID.USER_ID, did),])

    # upload the Talao private rsa key
    talao_rsa_private_key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
    if type(talao_rsa_private_key) == bytes :
        talao_rsa_key = serialization.load_pem_private_key(talao_rsa_private_key,password=None,)
    else :
        talao_rsa_key = serialization.load_pem_private_key(bytes(talao_rsa_private_key, 'utf-8'),password=None,)

    # get identity data
    address = contractsToOwners(workspace_contract, mode)

    rsa_privatekey = privatekey.get_key(address, 'rsa_key', mode)
    if type(rsa_privatekey) == bytes :
        subject_key = serialization.load_pem_private_key(rsa_privatekey,password=None,)
    else :
        subject_key = serialization.load_pem_private_key(bytes(rsa_privatekey, 'utf-8'),password=None,)

    #profil = read_profil(workspace_contract, mode, 'full')[0]
    #name = profil['firstname'] + ' ' + profil['lastname']
    username = ns.get_username_from_resolver(workspace_contract,mode)
    email = ns.get_data_from_username(username,mode)['email']
 
    subject = x509.Name([
            #x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
            #x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, ""),
            #x509.NameAttribute(NameOID.LOCALITY_NAME, "Paris"),
            #x509.NameAttribute(NameOID.ORGANIZATION_NAME, ""),
            x509.NameAttribute(NameOID.COMMON_NAME, session['name']),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, email),
            x509.NameAttribute(NameOID.USER_ID, did),])

    cert = x509.CertificateBuilder()
    cert = cert.subject_name(subject)
    # talao as CA
    cert = cert.issuer_name(talao_issuer)
    cert = cert.public_key( subject_key.public_key())
    cert=cert.serial_number(x509.random_serial_number())
    cert=cert.not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
    cert=cert.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
    cert=cert.add_extension(x509.BasicConstraints(ca=False, path_length=None),critical=True)
    cert = cert.add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.EMAIL_PROTECTION,
                                                    x509.oid.ExtendedKeyUsageOID.CODE_SIGNING,
                                                    x509.oid.ExtendedKeyUsageOID.TIME_STAMPING]), critical=True)
    #cert=cert.add_extension(x509.SubjectAlternativeName([x509.RFC822Name(email), x509.OtherName(NameOID.COMMON_NAME, bytes(did, 'utf-8'))]),critical=True,)
    #cert=cert.add_extension(x509.SubjectAlternativeName([x509.OtherName(NameOID.COMMON_NAME, bytes(did, 'utf-8'))]),critical=True,)
    cert = cert.add_extension(x509.KeyUsage(digital_signature=True,
                                            key_encipherment=True,
                                            data_encipherment=True,
                                            key_agreement=True,
                                            content_commitment=False,
                                            key_cert_sign=False,
                                            crl_sign=False,
                                            encipher_only=False,
                                            decipher_only=False ), critical=True)
    cert=cert.sign(talao_rsa_key, hashes.SHA256())

    # Write our certificate out to disk.
    filename = mode.uploads_path + workspace_contract + ".pem"
    with open(filename, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    certificate = pkcs12.serialize_key_and_certificates(bytes(did, 'utf-8'), subject_key, cert, None, serialization.BestAvailableEncryption(bytes(password, 'utf-8')))
    filename = mode.uploads_path + workspace_contract+ ".p12"
    with open(filename, "wb") as f:
        f.write(certificate)
    return True



if __name__ == '__main__':
    generate_CA(mode)