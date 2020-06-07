"""
gestion des api 
"""

from flask import request, Response
import json

# dependances
from protocol import  username_to_data, getUsername
from protocol import Identity, Claim, Experience, Kbis, Kyc, Certificate, Education
import environment
import constante

# environment setup
mode=environment.currentMode()
w3=mode.w3

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
		data = username_to_data(username, mode)
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
		my_analysis = analysis(workspace_contract)
		content = json.dumps(my_analysis)
		response = Response(content, status=200, mimetype='application/json')
		return response
	
	
	elif topicname in ['experience', 'kyc', 'kbis', 'certificate', 'education'] :
		user = Identity(workspace_contract, mode)
		resume = user.__dict__
		
		if topicname == 'kyc' and len(resume.get('kyc', [])) != 0  :
			content = json.dumps(resume['kyc'][0])
			response = Response(content, status=200, mimetype='application/json')
			return response
		
		if topicname == 'kbis' and len(resume.get('kbis',[])) != 0 :
			content = json.dumps(resume['kbis'][0])
			response = Response(content, status=200, mimetype='application/json')
			return response

		if topicname == 'experience' and len(resume.get('experience', [])) != 0 :
			content = json.dumps(resume['experience'])
			response = Response(content, status=200, mimetype='application/json')
			return response
	
		if topicname == 'certificate' and len(resume.get('certificate', [])) != 0 :
			content = json.dumps(resume['certificate'])
			response = Response(content, status=200, mimetype='application/json')
			return response
			
		if topicname == 'education' and len(resume.get('education', [])) != 0 :
			content = json.dumps(resume['education'])
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


def analysis(workspace_contract) :
	
	nb_issuer_none = 0 
	nb_issuer_self_declared = 0
	nb_issuer_is_relay = 0
	nb_issuer_external = 0
	nb_issuer_in_whitelist = 0
	is_kbis = "N/A"
	is_kyc = "N/A"
	nb_doc_experience = 0
	description = ""	
	average_experience = 0
	talao = '0xfafDe7ae75c25d32ec064B804F9D83F24aB14341'.lower()
	whitelist = [talao]
	nb_doc = 0
	
	doc_name = ['file', 'experience', 'education', 'kbis', 'kyc', 'certificate']
	claim_name = ['name', 'firstname', 'lastname', 'contact_email', 'contact_phone', 'contact_name', 'birthdate', 'postal_address', 'website']

	user = Identity(workspace_contract, mode)
	resume = user.__dict__

	for doctype in doc_name :
		if resume.get(doctype) is not None :
			for i in range(0, len(resume[doctype])) :
				nb_doc +=1			
				issuer_workspace_contract = resume[doctype][i]['issuer']['workspace_contract']
			
				if issuer_workspace_contract == None :
					nb_issuer_none +=1
				else :	
					issuer_workspace_contract = resume[doctype][i]['issuer']['workspace_contract'].lower()	
					if issuer_workspace_contract ==  workspace_contract.lower() or issuer_workspace_contract ==  mode.relay_workspace_contract.lower() :
						nb_issuer_self_declared +=1				
					elif issuer_workspace_contract in whitelist :
						nb_issuer_in_whitelist += 1			
					else  :
						nb_issuer_external +=1	


	for doctype in claim_name :	
		if resume['personal'].get(doctype) is not None :
				nb_doc +=1
				issuer_workspace_contract = resume['personal'][doctype]['issuer']['workspace_contract']
				if issuer_workspace_contract == None :
					nb_issuer_none +=1
				else : 	
					issuer_workspace_contract = resume['personal'][doctype]['issuer']['workspace_contract'].lower()	
					if issuer_workspace_contract ==  workspace_contract.lower() or issuer_workspace_contract ==  mode.relay_workspace_contract.lower():
						nb_issuer_self_declared +=1
				
					elif issuer_workspace_contract in whitelist :
						nb_issuer_in_whitelist += 1
					else  :
						nb_issuer_external +=1	

	

	if resume['type'] == 'person' :	
		is_kyc = True if len(resume['kyc']) != 0 else False
	else :
		is_kbis = True if len(resume['kbis']) != 0 else False

	
	if resume.get('experience') is not None :
		for i in range(0, len(resume['experience'])) :
			nb_doc_experience +=1	
			description += resume['experience'][i]['description']			 
			average_experience = len(description.split())/nb_doc_experience			
	
	
	nb_certificate = len(resume.get('certificate'))	
	
	
	
	print('')
	print('Resume of ', getUsername(workspace_contract, mode))
	print(' ')
	print('nombre de doc = ', nb_doc)	 
	print('---------------------')
	print('nombre de doc sans issuer = ' , nb_issuer_none)
	print('nombre de doc self = ', nb_issuer_self_declared) 
	print('nombre de doc whitlist = ', nb_issuer_in_whitelist)
	print('nombre issuer unknown = ', nb_issuer_external)
	print('----------------------')
	print('Is there a kbis ', is_kbis)
	print('Is there a kyc ', is_kyc)
	print('----------------------')

	print('There are', nb_doc_experience, 'experiences detailed')
	print('Average nb of words per experience = ', average_experience)
	print('There are ', nb_certificate, ' certificates')

	my_analysis = {'topic' : 'analysis', 
					'id' : 'did:talao:'+ mode.BLOCKCHAIN + ':' + workspace_contract[2:],
					'workspace_contract' : workspace_contract,
					'type' : resume['type'], 
					'name' : resume['name'],
					'nb_data' : nb_doc,
					'nb_data_self_declared' : nb_issuer_self_declared,
					'nb_data_whitelist_issuer' : nb_issuer_in_whitelist,
					'nb_data_unknown_issuer' : nb_issuer_external,
					'kyc' : is_kyc,
					'kbis' : is_kbis,
					'nb_experience' : nb_doc_experience,
					'nb_words_per_experience' : average_experience,
					'nb_certificate' : nb_certificate}
	return my_analysis				
				
