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
    



# Talent-Connect API
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

"""
def analysis(workspace_contract,resume, mode) :
	
	
	#TALAO = '0xfafDe7ae75c25d32ec064B804F9D83F24aB14341'.lower()
	#whitelist = [TALAO]
	
	# global
	nb_doc = 0
	nb_claim = 0
	is_kbis = "N/A"
	is_kyc = "N/A"
	nb_description = 0
	nb_experience = 0
	
	# Issuers
	nb_issuer_none = 0 
	nb_issuer_self = 0
	nb_issuer_person = 0
	nb_issuer_company = 0
	
	#nb_issuer_is_relay = 0
	#nb_issuer_external = 0
	#nb_issuer_in_whitelist = 0
	
	
	# Certificate indicators
	nb_certificate = 0
	nb_certificate_experience = 0
	nb_certificate_education = 0
	nb_certificate_skills = 0
	nb_certificate_recommendation = 0
	nb_certificate_language = 0
	
	# Corpus
	description = ""	 
	position = "" 
	skills = [] 
	
	# Calculation
	average_experience = 0 
	
	
	
	doc_name = ['file', 'experience', 'education', 'kbis', 'kyc', 'certificate']
	company_claim_name = ['name', 'contact_email', 'contact_phone', 'contact_name',  'website', 'about']
	person_claim_name = ['firstname', 'lastname', 'birthdate', 'postal_address', 'about','education', 'profil_title', 'contact_email', 'contact_phone']

	if resume['type'] == 'person' :
		claim_name = person_claim_name
	else :
		claim_name = company_claim_name

	# source of data (all)
	for doctype in doc_name :
		if resume.get(doctype) is not None :
			for i in range(0, len(resume[doctype])) :
				nb_doc +=1			
				issuer_workspace_contract = resume[doctype][i]['issuer']['workspace_contract']			
				if issuer_workspace_contract == None :
					nb_issuer_none +=1
				elif issuer_workspace_contract.lower() ==  workspace_contract.lower() or issuer_workspace_contract.lower() ==  mode.relay_workspace_contract.lower() :
					nb_issuer_self +=1				
				elif  resume[doctype][i]['issuer']['category'] == 2001 :
					nb_issuer_company +=1
				else :
					nb_issuer_person +=1	
	
	for doctype in claim_name :		# 0,2 pt/ topicname	
		if resume['personal'][doctype]['issuer'] is not None :
			issuer_workspace_contract = resume['personal'][doctype]['issuer']['workspace_contract']	
			if issuer_workspace_contract is None :
				pass
			elif issuer_workspace_contract.lower() == workspace_contract.lower() or issuer_workspace_contract.lower() ==  mode.relay_workspace_contract.lower() :
				nb_claim += 1
				nb_doc += 0.2
				nb_issuer_self += 0.2
			else  :
				nb_doc += 0.2
				nb_claim +=1
		
	self_completion_value = math.floor(100*nb_issuer_self/nb_doc)
	self_completion = str(self_completion_value) + '%'
 
	person_completion_value = math.floor(100*nb_issuer_person/nb_doc)
	person_completion = str(person_completion_value) + '%'

	company_completion_value = math.floor(100*nb_issuer_company/nb_doc)
	company_completion = str(company_completion_value) + '%'

	
	# Kyc et Kbis
	if resume['type'] == 'person' :	
		is_kyc = 'Yes' if len(resume['kyc']) != 0 else 'No'
	else :
		is_kbis = 'Yes' if len(resume['kbis']) != 0 else 'No'

	# Experience, Education, Language, Skills, etc
	nb_experience = len(resume['experience'])
	nb_certificate = len (resume['certificate'])
	
	if resume.get('experience') is not None :
		for exp in resume['experience'] :
			nb_description +=1	
			description += exp['description']
			position += exp['title'] + ' '
			skills += exp['skills']			 
	
	if resume.get('education') is not None :
		for edu in resume['education'] :
			nb_description +=1	
			description += edu['description']
			skills += edu['skills']		
	
	
	# calcul du nombre de certificat par type
	issuers = dict()
	if resume.get('certificate') is not None :
		for cert in resume['certificate'] :
			if cert['issuer']['category'] == 2001 :
				name = cert['issuer']['name'].capitalize()
			else :
				name = cert['issuer']['firstname'].capitalize() + ' ' + cert['issuer']['lastname'].capitalize()				
			issuers[name] = issuers.get(name, 0) + 1
			
			if cert['type'].lower() == 'experience' :
				nb_description +=1
				nb_certificate_experience +=1
				position += cert['title'] + ' '
				description += cert['description']
				skills += cert['skills']			 
			
			if cert['type'].lower() == 'education' :
				nb_description +=1
				nb_certificate_education +=1
				description += cert['description']

			if cert['type'].lower() == 'language' :
				nb_description +=1
				nb_certificate_language +=1
				description += cert['description']
			
			if cert['type'].lower() == 'recommendation' :
				nb_description +=1
				nb_certificate_recommendation +=1
				description += cert['description']
			
			if cert['type'].lower() == 'skills' :
				nb_description +=1
				nb_certificate_skills +=1
				skills += cert['skills']
				description += cert['description']
	
	if nb_certificate != 0 :
		cert_experience_value = math.floor(100*nb_certificate_experience/nb_certificate)
		cert_experience = str(cert_experience_value) + '%'
	
		cert_education_value = math.floor(100*nb_certificate_education/nb_certificate)
		cert_education = str(cert_education_value) + '%'
	
		cert_skills_value = math.floor(100*nb_certificate_skills/nb_certificate)
		cert_skills = str(cert_skills_value) + '%'
	
		cert_recommendation_value = math.floor(100*nb_certificate_recommendation/nb_certificate)
		cert_recommendation = str(cert_recommendation_value) + '%'

		cert_language_value = math.floor(100*nb_certificate_language/nb_certificate)
		cert_language = str(cert_language_value) + '%'
	else :
		cert_experience = '0%'
		cert_education = '0%'
		cert_skills = '0%'
		cert_language = '0%'
		cert_recommendation = '0%'
	
	# top issuers
	key_issuers = dict()
	sorted_issuers = sorted(issuers.items(), key=lambda x: x[1], reverse = True)
	for count,item in enumerate(sorted_issuers, start=0) :
		key_issuers.update({'issuer_word'+ str(count) : item[0].capitalize(), 'issuer_freq'+str(count) : item[1]/nb_certificate})
	print(key_issuers)
	
	
	# finalisation du texte "description"			
	if resume['personal']['about']['claim_value'] is not None :
		nb_description +=1
		description += resume['personal']['about']['claim_value'] 	
	if nb_description != 0 :
		average_description = len(description.split())/nb_description		
	else : average_description = 0
	
	
	# resume completion
	completion_value = math.floor(100*nb_claim/10)
	completion = str(completion_value) + '%'
	
	
	
	# NLP
	english_no_words = list(set(nltk.corpus.stopwords.words("english")))
	french_no_words = list(set(nltk.corpus.stopwords.words("french")))
	a = ['.', '(', ')', ',', ':'] + english_no_words + french_no_words
	
	token_description = word_tokenize(description.lower())
	token_skills = word_tokenize(" ".join(skills).lower())
	token_position = word_tokenize(position.lower())
	
	skills_counter = len(token_skills)
	description_counters = len(token_description)
	position_counter = len(token_position)
	
	clean_token_description = [x for x in token_description if x not in a]
	fdist_description = FreqDist(clean_token_description)
	fdist_description = fdist_description.most_common(20)

	clean_token_skills = [x for x in token_skills if x not in a]
	fdist_skills = FreqDist(clean_token_skills)
	fdist_skills = fdist_skills.most_common(20)
	
	clean_token_position = [x for x in token_position if x not in a]
	fdist_position = FreqDist(clean_token_position)
	fdist_position = fdist_position.most_common(20)
	
	skills_counter = 0
	for (a,b) in fdist_skills :
		skills_counter += b
	skills_word_list =  [ (a,b/skills_counter)  for (a,b) in fdist_skills]
	skills_key_words = {}
	for count,item in enumerate(skills_word_list, start=0) :
		skills_key_words.update({'ski_word'+ str(count) : item[0].capitalize(), 'ski_freq'+str(count) : item[1]})

	description_counter = 0
	for (a,b) in fdist_description :
		description_counter += b
	description_word_list =  [ (a,b/description_counter)  for (a,b) in fdist_description]	
	description_key_words = {}
	for count,item in enumerate(description_word_list, start=0) :
		description_key_words.update({'des_word'+ str(count) : item[0].capitalize(), 'des_freq'+str(count) : item[1]})

	position_counter = 0
	for (a,b) in fdist_position :
		position_counter += b
	position_word_list =  [ (a,b/position_counter)  for (a,b) in fdist_position]	
	position_key_words = {}
	for count,item in enumerate(position_word_list, start=0) :
		position_key_words.update({'pos_word'+ str(count) : item[0].capitalize(), 'pos_freq'+str(count) : item[1]})
		
	my_analysis = {'topic' : 'analysis', 
					'id' : 'did:talao:'+ mode.BLOCKCHAIN + ':' + workspace_contract[2:],
					'workspace_contract' : workspace_contract,
					'self_completion' : self_completion,
					'person_completion' : person_completion,
					'company_completion' : company_completion,
					'issuers' : len(resume['issuer_keys']),
					'nb_data' : math.floor(nb_doc)+1,
					'completion' : completion,
					'kyc' : is_kyc,
					'nb_description' : nb_description,
					'nb_words_per_description' : average_description,
					'nb_certificate' : nb_certificate,
					'cert_recommendation' : cert_recommendation,
					'cert_experience' : cert_experience,
					'cert_skills' : cert_skills,
					'cert_education' : cert_education,
					'cert_language' : cert_language,
					**skills_key_words,
					**description_key_words,
					**key_issuers,
					**position_key_words,
					}
	#print('my analysis = ', my_analysis)				
	return my_analysis
			
	"""
