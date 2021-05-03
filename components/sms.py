""" for token see passwords.json 
https://ssl.smsapi.com/#/payments/transfer/success
"""

import os
from smsapi.client import SmsApiComClient
from smsapi.exception import SmsApiException

def send_code(phone, code, mode) :
	""" code = str, phone number with country code 33607182594 """
	token = mode.sms_token
	try :
		client = SmsApiComClient(access_token=token)
		send_results = client.sms.send(to=phone, message="# Your verification code is : " + code)
		for result in send_results :
			print('result = ', result.id,result.points,result.error)
			return True
	except SmsApiException as e:
		print(e.message)
		return False

def check_phone(phone, mode) :
	token = mode.sms_token
	try:
		client = SmsApiComClient(access_token=token)
		client.sms.send(to=phone, message="Your phone number has been verified.")
		return True
	except SmsApiException as e:
		print('sms api message = ', e.message)
		return False

