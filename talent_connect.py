"""
gestion des api 
"""

from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort, Response
from flask_session import Session


from flask import request, Response
import json

# dependances
from protocol import contractsToOwners, read_workspace_info
from protocol import Identity, Claim, Document
import environment
import constante

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
		my_analysis = analysis(workspace_contract, resume, mode)
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


def analysis(workspace_contract,resume, mode) :
	""" external call available """
	
	print('session dans anlysis = ', session['username'])
	
	nb_issuer_none = 0 
	nb_issuer_self_declared = 0
	nb_issuer_is_relay = 0
	nb_issuer_external = 0
	nb_issuer_in_whitelist = 0
	nb_claim = 0
	is_kbis = "N/A"
	is_kyc = "N/A"
	nb_doc_description = 0
	nb_experience = 0
	nb_certificate = 0
	description = ""	
	average_experience = 0
	talao = '0xfafDe7ae75c25d32ec064B804F9D83F24aB14341'.lower()
	whitelist = [talao]
	nb_doc = 0
	
	doc_name = ['file', 'experience', 'education', 'kbis', 'kyc', 'certificate']
	company_claim_name = ['name', 'contact_email', 'contact_phone', 'contact_name', 'postal_address', 'website']
	person_claim_name = ['firstname', 'lastname', 'birthdate', 'postal_address', 'about','education', 'profil_title', 'contact_email', 'contact_phone']

	if resume['type'] == 'person' :
		claim_name = person_claim_name
	else :
		claim_name = company_claim_name

	for doctype in doc_name :
		if resume.get(doctype) is not None :
			for i in range(0, len(resume[doctype])) :
				nb_doc +=1			
				issuer_workspace_contract = resume[doctype][i]['issuer']['workspace_contract']			
				if issuer_workspace_contract == None :
					nb_issuer_none +=1
				elif issuer_workspace_contract.lower() ==  workspace_contract.lower() or issuer_workspace_contract.lower() ==  mode.relay_workspace_contract.lower() :
					nb_issuer_self_declared +=1				
				else  :
					nb_issuer_external +=1	


	for doctype in claim_name :	
		if resume['personal'][doctype]['issuer'] is None :
			pass	
		elif resume['personal'][doctype]['issuer']['workspace_contract'].lower == workspace_contract.lower() :
			nb_claim += 1
			nb_doc +=1
			nb_issuer_self_declared +=1
		elif  resume['personal'][doctype]['issuer']['workspace_contract'].lower ==  mode.relay_workspace_contract.lower():
			nb_doc += 1
			nb_claim +=1
			nb_issuer_self_declared +=1
		else  :
			nb_doc +=1
			nb_claim +=1
			nb_issuer_external +=1	

	

	if resume['type'] == 'person' :	
		is_kyc = True if len(resume['kyc']) != 0 else False
	else :
		is_kbis = True if len(resume['kbis']) != 0 else False

	nb_experience = len(resume['experience'])
	nb_certificate = len (resume['certificate'])
	
	if resume.get('experience') is not None :
		for exp in resume['experience'] :
			nb_doc_description +=1	
			description += exp['description']			 
	if resume.get('certificate') is not None :
		for cert in resume['certificate'] :
			nb_doc_description +=1	
			description += cert['description']			 
	if resume['personal']['about']['claim_value'] is not None :
		nb_doc_description +=1
		description += resume['personal']['about']['claim_value'] 
	
	if nb_doc_description != 0 :
		average_description = len(description.split())/nb_doc_description		
	else : average_description = 0
	
	claim_rate = nb_claim/10
		
	my_analysis = {'topic' : 'analysis', 
					'id' : 'did:talao:'+ mode.BLOCKCHAIN + ':' + workspace_contract[2:],
					'workspace_contract' : workspace_contract,
					'type' : resume['type'], 
					'name' : resume['name'],
					'nb_data' : nb_doc,
					'nb_data_self_declared' : nb_issuer_self_declared,
					'nb_data_with_issuer' : nb_issuer_external,
					'kyc' : is_kyc,
					'personal_data' : claim_rate,
					'nb_description' : nb_doc_description,
					'nb_words_per_description' : average_description,
					'nb_certificate' : nb_certificate,
					'nb_experience' : nb_experience }
	return my_analysis				
				
