Sign documents and emails with your Identity
============================================

So far digital signature are managed by International standards of cryptography as X509.

[wikipedia] "...In cryptography, X.509 is a standard defining the format of public key certificates.
X.509 certificates are used in many Internet protocols, including TLS/SSL, which is the basis for HTTPS,the secure protocol for browsing the web.
They are also used in offline applications, like electronic signatures. An X.509 certificate contains a public key and an identity (a hostname, or an organization, or an individual),
and is either signed by a certificate authority or self-signed.
When a certificate is signed by a trusted certificate authority, or validated by other means,
someone holding that certificate can rely on the public key it contains to establish secure communications with another party, or
validate documents digitally signed by the corresponding private key."

In order to allow user to sign documents and emails with his/her decentralized Identity, Talao provides X509 certificates attached to Identity. Those certificates are signed by Talao as a Certification Authority.
You will get two certificates as files xxxx.p12 and xxxx.pem. Thoses cestificates will be needed to sign and encrypt data with your email client.

Sign in, chose your Identity page, clic on "Advanced" in the top right menu and then clic on "RSA key and x509 Certificates".

To install those certificates in SMTP clients :

For Thunderbird Mozilla : https://www.ssl.com/how-to/installing-an-s-mime-certificate-and-sending-secure-email-in-mozilla-thunderbird-on-windows-10/

For Outlook : https://www.thesslstore.com/knowledgebase/email-signing-support/install-e-mail-signing-certificates-outlook/

To get the Talao Conformity Authority certificate clic `here <https://talao.io/get_talao_CA/>`_ .
