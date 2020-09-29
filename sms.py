""" for token see passwords.json """

import os
from smsapi.client import SmsApiComClient
from smsapi.exception import SmsApiException


def send_code(phone, code, mode) :
	""" code = str, phone number with country code 33607182594 """
	token = mode.sms_token
	client = SmsApiComClient(access_token=token)
	send_results = client.sms.send(to=phone, message="# Your verification code is : " + code)
	for result in send_results:
		print(result.id, result.points, result.error)
	return True
   

def check_phone(phone, mode) :
	token = mode.sms_token
	client = SmsApiComClient(access_token=token)
	try:
		client.sms.send(to=phone, message="Your phone number has been checked.")
		return True
	except SmsApiException as e:
		print(e.message, e.code)
		return False

