import math
import numpy as np
import nltk
import os
import nltk.corpus
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
import random
from datetime import datetime


def dashboard(workspace_contract,resume, mode) :
	""" external call available """
		
	# global
	nb_doc = 0
	nb_claim = 0
	is_kbis = "N/A"
	is_kyc = "N/A"
	nb_description = 0
	nb_experience = 0
	update = []
	
	# Issuers
	nb_issuer_none = 0
	nb_issuer_self = 0
	nb_issuer_person = 0
	nb_issuer_company = 0
	issuer_list = []
	
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
				print("")
				created = datetime.fromisoformat(resume[doctype][i]['created'])
				update.append(created)
				nb_doc +=1			
				issuer_workspace_contract = resume[doctype][i]['issuer']['workspace_contract']	
				if issuer_workspace_contract == None :
					nb_issuer_none +=1
				elif issuer_workspace_contract.lower() ==  workspace_contract.lower() or issuer_workspace_contract.lower() ==  mode.relay_workspace_contract.lower() :
					nb_issuer_self +=1				
				elif  resume[doctype][i]['issuer']['category'] == 2001 :
					issuer_list.append(issuer_workspace_contract)
					nb_issuer_company +=1
				else :
					nb_issuer_person +=1
					issuer_list.append(issuer_workspace_contract)	
	
	for doctype in claim_name :		# 0,2 pt/ topicname	
		if resume['personal'][doctype]['issuer'] is not None and resume['personal'][doctype]['privacy'] == 'public' :
			issuer_workspace_contract = resume['personal'][doctype]['issuer']['workspace_contract']
			print('doctype = ', doctype, resume['personal'][doctype])
			created = datetime.fromisoformat(resume['personal'][doctype]['created'])
			update.append(created)
			if issuer_workspace_contract is None :
				pass
			elif issuer_workspace_contract.lower() == workspace_contract.lower() or issuer_workspace_contract.lower() ==  mode.relay_workspace_contract.lower() :
				nb_claim += 1
				nb_doc += 0.2
				#nb_issuer_self += 0.2
			else  :
				nb_doc += 0.2
				nb_claim +=1
	
	issuer_list = list(dict.fromkeys(issuer_list))
	nb_issuer = len(issuer_list)
	if nb_doc != 0 :	
		person_completion_value = math.floor(100*nb_issuer_person/nb_doc)
		person_completion = str(person_completion_value) + '%'

		company_completion_value = math.floor(100*nb_issuer_company/nb_doc)
		company_completion = str(company_completion_value) + '%'
		
		nb_issuer_self = nb_doc - nb_issuer_person - nb_issuer_company
		self_completion_value = math.floor(100*nb_issuer_self/nb_doc)
		self_completion = str(self_completion_value) + '%'
		
	else : 
		self_completion_value = 0
		self_completion = '0%'
		person_completion_value = 0
		person_completion = '0%'
		company_completion_value = 0
		company_completion = '0%'
		
	# update
	sorted_update = sorted(update, reverse=True)
	last_update = sorted_update[0]
	update_number = len(sorted_update)
	update_duration = datetime.now() - last_update
	update_duration_value = int(divmod(update_duration.total_seconds(), 86400)[0])
	update_duration_string = str(update_duration_value) + ' days' 
	
	# Kyc et Kbis
	if resume['type'] == 'person' :	
		is_kyc = 'Yes' if len(resume['kyc']) != 0 else 'No'
	else :
		is_kbis = 'Yes' if len(resume['kbis']) != 0 else 'No'

	nb_experience = len(resume['experience'])
	nb_certificate = len (resume['certificate'])	
	
	# Experience (duration, etc)
	experiences= dict()
	key_experiences = dict()
	if resume.get('experience') is not None :
		for exp in resume['experience'] :
			nb_description +=1	
			description += exp['description']
			position += exp['title'] + ' '
			skills += exp['skills']			 
			duration = datetime.fromisoformat(exp['end_date']) - datetime.fromisoformat(exp['start_date'])
			duration_in_days = divmod(duration.total_seconds(), 86400)   
			experiences[exp['title']+ ', ' +exp['company']['name']] = duration_in_days
	sorted_experiences = sorted(experiences.items(), key=lambda x: x[1], reverse = True)
	for count,item in enumerate(sorted_experiences, start=0) :
		key_experiences.update({'exp_name'+ str(count) : item[0], 'exp_dur'+str(count) : str(item[1][0]).split('.')[0] + ' days'})	
	
	#Education	
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
	
	# top certificate issuers
	key_issuers = dict()
	sorted_issuers = sorted(issuers.items(), key=lambda x: x[1], reverse = True)
	for count,item in enumerate(sorted_issuers, start=0) :
		key_issuers.update({'issuer_word'+ str(count) : item[0], 'issuer_freq'+str(count) : item[1]/nb_certificate})
	
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
	#print(nltk.pos_tag(token_description))
	
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
		skills_key_words.update({'ski_word'+ str(count) : item[0].capitalize(),
								'ski_freq'+str(count) : float("{:.4f}".format(item[1])) })

	description_counter = 0
	for (a,b) in fdist_description :
		description_counter += b
	description_word_list =  [ (a,b/description_counter)  for (a,b) in fdist_description]	
	description_key_words = {}
	for count,item in enumerate(description_word_list, start=0) :
		description_key_words.update({'des_word'+ str(count) : item[0].capitalize(), 'des_freq'+str(count) : float("{:.4f}".format(item[1]))})

	position_counter = 0
	for (a,b) in fdist_position :
		position_counter += b
	position_word_list =  [ (a,b/position_counter)  for (a,b) in fdist_position]	
	position_key_words = {}
	for count,item in enumerate(position_word_list, start=0) :
		position_key_words.update({'pos_word'+ str(count) : item[0].capitalize(), 'pos_freq'+str(count) : float("{:.4f}".format(item[1]))})
	
	# index/rating max 70 today
	if update_duration_value < 20 :
		quality_update = 10
	else :
		quality_update = 0
		
	if nb_certificate < 20 :
		quality_certificate  = nb_certificate 
	else :
		quality_certificate = 20
	if is_kyc == 'Yes' :
		quality_kyc = 20
	else :
		quality_kyc = 0
	quality_completion = 10 * completion_value/100
	if nb_issuer < 20 :
		quality_issuer = nb_issuer
	else :
		quality_issuer = 20				
	quality = quality_issuer + quality_completion + quality_certificate + quality_kyc + quality_update
	index = float("{:.2f}".format(quality))
	
	#ups and downs 	
	up_down = ups_and_downs(update_duration_value,
				self_completion_value,
				person_completion_value,
				company_completion_value,
				nb_certificate,
				is_kyc,
				completion_value,
				nb_experience,
				average_description,
				update_duration_string,
				nb_doc,
				sorted_issuers) 
	
	my_analysis = {'topic' : 'analysis', 
					'id' : 'did:talao:'+ mode.BLOCKCHAIN + ':' + workspace_contract[2:],
					'self_completion' : self_completion,
					'person_completion' : person_completion,
					'company_completion' : company_completion,
					'index' : index,
					'issuers' : nb_issuer,
					'nb_data' : math.floor(nb_doc)+1,
					'completion' : completion,
					'last_update' : last_update.strftime("%Y/%m/%d") + " (" + update_duration_string + ")",
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
					**up_down,
					**key_experiences
					}
	return my_analysis

			
def ups_and_downs(update_duration_value,
				self_completion_value,
				person_completion_value,
				company_completion_value,
				nb_certificate,
				is_kyc,
				completion_value,
				nb_experience,
				average_description,
				update_duration_string,
				nb_doc,
				sorted_issuers) :
	
	# Identity update limit, days 
	UPDATE_LIMIT = 15
	
	# Source of data, base 100
	PERSON_COMPLETION_THRESHOLD = 40
	SELF_COMPLETION_THRESHOLD = 40
	COMPANY_COMPLETION_THRESHOLD = 40

	# Document, absolut
	DOCUMENT_THRESHOLD = 10
	
	# Certificate, absolut
	CERTIFICATE_THRESHOLD = 10
	
	# Exprience, absolut
	EXPERIENCE_THRESHOLD = 10
	
	# Profil completion, base 100
	COMPLETION_THRESHOLD = 60
	
	# Average description, words
	DESCRIPTION_THRESHOLD = 30
	
	# Setup
	up = ['This resume is based on the Talao protocol and data are tamper proof.' ]
	down = []
	
	# Rules 
	
	if update_duration_value < UPDATE_LIMIT :
		up.append("This resume has been updated less than " + update_duration_string + " ago. This strengthens the resume as it brings more trust to data." )
	else :
		down.append("The resume has benn update more than 15 days agos. This may be an issue.")
				 
	if self_completion_value < SELF_COMPLETION_THRESHOLD  and nb_doc > DOCUMENT_THRESHOLD :
		up.append("A large part of the information of this resume are provided by third parties. This strengthens the resume and brings more reliability to data." )
	else :
		down.append("Most of the information are self declared. This weakens the resume.")
	
	if person_completion_value > PERSON_COMPLETION_THRESHOLD  :
		down.append("Most of the certificates are provided by Individuals. This weakens the resume.")
	
	if company_completion_value > COMPANY_COMPLETION_THRESHOLD  :
		up.append("Most of the certificates are provided by Companies. This provides very reliable data for third parties.")
		
	if nb_certificate != 0 and sorted_issuers[0][1]/nb_certificate < 0.15  :
		up.append("Certicates are issued by several different referents. This brings more reliability to data.")
	else :
		down.append("Most Certificates are issued by the same referents. This weakens the resume.")
	
	if is_kyc == 'Yes' :
		up.append("Proof of Identity is available. Third party can now rely on this Identity.")
	else :
		down.append("No proof of Identity. Third party cannot rely on this Identity. Contact Talao to get your Proof of Identity and improve your rating.")
	
	if completion_value > COMPLETION_THRESHOLD :
		up.append("Personal data are numerous.")
	else :
		down.append("Weak Personal information.This resume is not sufficiently detailed to be efficient.")
	
	if nb_certificate > CERTIFICATE_THRESHOLD :
		up.append("The profil is has numerous cerificates. This brings more reliability to data.")
	else :
		down.append("Weak number of certificates, few reliable Data.")
	
	if nb_experience > EXPERIENCE_THRESHOLD :
		up.append("The profil has numerous experiences. This brings more information to the resume.")
	else :
		down.append("Weak number of experience. This does not provide enough information to third parties.")
	
	if average_description > DESCRIPTION_THRESHOLD  :
		up.append("Descriptions are precise. This strengthen the resume")
	else :
		down.append("Descriptions are weak because not very precise.")
	
	# Fill up if weak
	if nb_doc < 3 :
		down = up = []
		for i in range(3) :
			up.append("Sorry, there are not enough data")
			down.append("Sorry, there are not enough data")
	elif len(up) == 1 :
		up.append("Sorry, only 1 good news there !")
		up.append("Sorry, only 1 good news there !")
	elif len(up) == 2 :
		up.append("Sorry, only 2 good news there !")
	else :
		up = random.sample(up, 3)
		down = random.sample(down, 3)
	
	# packing
	up_down = {'word0' : up[0],
				'word1' : up[1],
				'word2' : up[2],
				'word3' : down[0],
				'word4' : down[1],
				'word5' : down[2]
				} 
	
	return up_down
