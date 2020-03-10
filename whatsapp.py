
from web3.auto import w3
import constante
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import Talao_token_transaction
import csv
import http.client, urllib.parse
import json
import datetime
import Talao_backend_transaction
import Talao_ipfs
import GETresume
"""
ACCOUNT SID
AC48aad8d4ad812bc595d5a13607a64f0c
AUTH TOKEN
7fb8da939d4328c92fc0039cc34f5cc1

33621040050
"""

from twilio.rest import Client


def sendwhatsapp(msg) :
	# client credentials are read from TWILIO_ACCOUNT_SID and AUTH_TOKEN
	client = Client()

	# this is the Twilio sandbox testing number
	from_whatsapp_number='whatsapp:+14155238886'
	# replace this number with your own WhatsApp Messaging number
	to_whatsapp_number='whatsapp:+33607182594'


	client.messages.create(body='test',
                       from_=from_whatsapp_number,
                       to=to_whatsapp_number)
	return
sendwhatsapp("Hello from Talao Connect")
