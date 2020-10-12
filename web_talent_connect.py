"""
gestion des api 
"""

from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort, Response
from flask_session import Session

"""
import math
import numpy as np
import nltk
import nltk.corpus
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
#from nltk.corpus import stopwords
"""

import os

from flask import request, Response
import json

# dependances
from protocol import contractsToOwners, read_workspace_info
from protocol import Identity, Claim, Document
import environment
import constante
import analysis

# environment setup
mode = environment.currentMode()
w3 = mode.w3


#@app.route('/api/talent-connect/auth/', methods = ['POST'])
def auth() :
	if request.authorization is None :
		content = json.dumps({'username' : None, 'password' : None})
		response = Response(content, status=401, mimetype='application/json')
		return response

	workspace_contract = request.authorization.get("username")
	secret_received = request.authorization.get("password")
	address = contractsToOwners(workspace_contract, mode)
	filename = "./RSA_key/" + mode.BLOCKCHAIN + '/' + str(address) + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
	try :
		fp = open(filename,"r")
		rsa_key = fp.read()
		fp.close()
	except IOError :
		content = json.dumps({'topic' : 'error', 'msg' : 'Cannot verify login/secret'})
		response = Response(content, status=406, mimetype='application/json')
		return response

	(workspace_contract, category, email , secret, aes)  = read_workspace_info (address, rsa_key, mode) 
	if secret_received != secret :
		content = json.dumps({'topic' : 'error', 'msg' : 'Wrong secret'})
		response = Response(content, status=401, mimetype='application/json')
		return response

	data = request.get_json(silent=True)
	if data['action'] == 'call_back' :
		pass
		# send a message
	elif data['action'] == 'do something' :
		pass
		# do something
	else :
		content = json.dumps({'topic' : 'error', 'msg' : 'action '+ data['action'] +' is not implemented'})
		response = Response(content, status=406, mimetype='application/json')
		return response

	username = get_username_from_resolver(workspace_contract)
	content = json.dumps({'User' : username, 'msg' : "ok"})
	response = Response(content, status=200, mimetype='application/json')
	return response
    



# Talent-Connect Public API
#@app.route('/api/talent-connect/', methods = ['GET'])
def get() :
	print('ok talent connect')
	user = request.args.get('user')
	topicname = request.args.get('topicname')
	""" liste des options possibles"""
	whitelist = request.args.get('whitelist')
	check = request.args.get('check')
	
	""" user = username or user = did
	only workspace_contract is needed anyway """
	if user[:10] != 'did:talao:' :
		username = user
		data = ns.get_data_from_username(username, mode)
		if data is None :
			content = json.dumps({'topic' : 'error', 'msg' : 'Username not found'})
			response = Response(content, status=401, mimetype='application/json')
			return response
			 
		workspace_contract = data['workspace_contract']
	
	else :
		workspace_contract = '0x' + user.split(':')[3]
	
	if topicname == 'resume' :
		resume = get_resume(workspace_contract)
		content = json.dumps(resume)
		response = Response(content, status=200, mimetype='application/json')
		return response
	
	elif topicname == 'analysis' :
		user = Identity(workspace_contract, mode)
		resume = user.__dict__
		my_analysis = analysis.dashboard(workspace_contract, resume, mode)
		content = json.dumps(my_analysis)
		response = Response(content, status=200, mimetype='application/json')
		return response
	
	
	elif topicname in ['experience', 'kyc', 'kbis', 'certificate', 'education'] :
		user = Identity(workspace_contract, mode)
		resume = user.__dict__
		
		if len(resume.get(topicname, [])) != 0  :		
			content = json.dumps(resume[topicname])
			response = Response(content, status=200, mimetype='application/json')
			return response
			
		else :
			content = json.dumps({'topic' : 'error', 'msg' : topicname +' not found'})
			response = Response(content, status=401, mimetype='application/json')
			return response	

	else :
		claim = Claim()
		claim.get_by_topic_name(data['workspace_contract'], topicname, mode)
		print(claim.transaction_hash)
		if claim.transaction_hash is None :
			content = json.dumps({'topic' : 'error', 'msg' : topicname + ' not found'})
			response = Response(content, status=401, mimetype='application/json')
			return response 
		else :
			content = json.dumps(claim.__dict__)
			response = Response(content, status=200, mimetype='application/json')
			return response	


def get_resume(workspace_contract) :
	user = Identity(workspace_contract, mode)
	json_data = user.__dict__
	""" clean up """
	del json_data['mode']
	del json_data['file_list']
	del json_data['experience_list']
	del json_data['education_list']
	del json_data['other_list']
	del json_data['kbis_list']
	del json_data['kyc_list']
	del json_data['certificate_list']
	del json_data['eventslist']
	del json_data['partners']
	del json_data['synchronous']
	del json_data['authenticated']
	del json_data['rsa_key']
	del json_data['relay_activated']
	del json_data['private_key']
	del json_data['category']
	del json_data['identity_file']
	json_data['topic'] = 'resume'
	return json_data
