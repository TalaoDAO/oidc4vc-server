
import copy
import os.path
from os import path
from flask import Flask, session, send_from_directory, flash
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
import requests
import shutil
from flask_fontawesome import FontAwesome
import json
from sys import getsizeof
import random

import logging
logging.basicConfig(level=logging.INFO)

# dependances
from protocol import Document, read_profil, Identity, Claim
import constante
from components import ns, analysis

def convert(obj):
	if type(obj) == list:
		for x in obj:
			convert(x)
	elif type(obj) == dict:
		for k, v in obj.items():
			if v is None:
				obj[k] = 'Unknown'
			else:
				convert(v)


def show_certificate(mode):
	"""
	# display experience certificate for anybody. Stand alone routine
	# #route /guest/certificate
	# @route /certificate/
	"""
	menu = session.get('menu', dict())
	viewer = 'guest' if not session.get('username') else 'user'
	certificate_id = request.args['certificate_id']
	doc_id = int(certificate_id.split(':')[5])
	identity_workspace_contract = '0x'+ certificate_id.split(':')[3]
	self_claim = None

	try:
		self_claim = certificate_id.split(':')[6]
	except:
		pass

	if session.get('certificate_id') != certificate_id :
		certificate = Document('certificate')
		exist = certificate.relay_get(identity_workspace_contract, doc_id, mode, loading = 'full')
		if not exist :
			content = json.dumps({'topic' : 'error', 'msg' : 'Credential Not Found'})
			response = Response(content, status=406, mimetype='application/json')
			return response
		session['certificate_id'] = certificate_id
		session['displayed_certificate'] = certificate.__dict__

	identity_profil= read_profil(identity_workspace_contract, mode, 'light')[0]
	issuer_username = None if 'issuer_username' not in session else session['issuer_username']
	identity_username = None if 'username' not in session else session['username']

	if self_claim == "experience" :
		description = session['displayed_certificate']['description'].replace('\r\n','<br>')

		my_badge = ''
		for skill in session['displayed_certificate']['skills'] :
			skill_to_display = skill.replace(" ", "").capitalize().strip(',')
			my_badge +=  """<span class="badge badge-pill badge-secondary" style="margin: 4px; padding: 8px;"> """+ skill_to_display + """</span>"""
		return render_template('./certificate/self_claim.html',
							**menu,
							type = 'Experience',
							certificate_id= certificate_id,
							company = session['displayed_certificate']['company']['name'],
							email = session['displayed_certificate']['company']['contact_email'],
							tel = session['displayed_certificate']['company']['contact_phone'],
							contact_name = session['displayed_certificate']['company']['contact_name'],
							start_date = session['displayed_certificate']['start_date'],
							end_date = session['displayed_certificate']['end_date'],
							description = description,
							badge = my_badge,
							viewer=viewer,
							title = session['displayed_certificate']['title'],
							)

	if self_claim == "skills" :
		description = session['displayed_certificate']['description']

		my_badge = ''
		#for skill in session['displayed_certificate']['skills'] :
		#	skill_to_display = skill.replace(" ", "").capitalize().strip(',')
		#	my_badge = my_badge + """<span class="badge badge-pill badge-secondary" style="margin: 4px; padding: 8px;"> """+ skill_to_display + """</span>"""
		return render_template('./certificate/self_claim.html',
							**menu,
							type = 'Experience',
							certificate_id= certificate_id,
							description = description,
							viewer=viewer,
							)

	if self_claim == "education" :
		description = session['displayed_certificate']['description'].replace('\r\n','<br>')

		my_badge = ''
		for skill in session['displayed_certificate']['skills'] :
			skill_to_display = skill.replace(" ", "").strip(',')
			if skill_to_display :
				my_badge = my_badge + """<span class="badge badge-pill badge-secondary" style="margin: 4px; padding: 8px;"> """+ skill_to_display.capitalize() + """</span>"""
		return render_template('./certificate/self_claim.html',
							**menu,
							type = 'Education',
							certificate_id= certificate_id,
							company = session['displayed_certificate']['organization']['name'],
							email = session['displayed_certificate']['organization']['contact_email'],
							tel = session['displayed_certificate']['organization']['contact_phone'],
							contact_name = session['displayed_certificate']['organization']['contact_name'],
							start_date = session['displayed_certificate']['start_date'],
							end_date = session['displayed_certificate']['end_date'],
							description = description,
							badge = my_badge,
							viewer=viewer,
							title = session['displayed_certificate']['title'],
							link = session['displayed_certificate']['certificate_link']
							)

	# Experience Certificate Display
	if session['displayed_certificate']['credentialSubject']['credentialCategory'] == 'experience' :
		yellow_star = "color: rgb(251,211,5); font-size: 12px;" # yellow
		black_star = "color: rgb(0,0,0);font-size: 12px;" # black

		# Icon "fa-star" treatment
		score = []
		context = dict()
		score.append(int(session['displayed_certificate']['credentialSubject']['reviewRecommendation']['reviewRating']['ratingValue']))
		score.append(int(session['displayed_certificate']['credentialSubject']['reviewDelivery']['reviewRating']['ratingValue']))
		score.append(int(session['displayed_certificate']['credentialSubject']['reviewSchedule']['reviewRating']['ratingValue']))
		score.append(int(session['displayed_certificate']['credentialSubject']['reviewCommunication']['reviewRating']['ratingValue']))
		for q in range(0,4) :
			for i in range(0,score[q]) :
				context["star"+str(q)+str(i)] = yellow_star
			for i in range(score[q],5) :
				context ["star"+str(q)+str(i)] = black_star

		if session['displayed_certificate']['credentialSubject']['skills'] :
			skills = session['displayed_certificate']['credentialSubject']['skills']
			my_badge = ""
			for skill in skills :
				if skill['description'] :
					my_badge += """<span class="badge badge-pill badge-secondary" style="margin: 4px; padding: 8px;"> """+ skill['description'].strip(' ').capitalize() + """</span>"""
		else :
			my_badge = None

		if session['displayed_certificate']['issuer']['category'] == 2001 : # company
			signature = session['displayed_certificate']['credentialSubject']['managerSignature']
			logo = session['displayed_certificate']['credentialSubject']['companyLogo']

			# if there is no signature one uses Picasso signature
			if not signature :
				signature = 'QmS9TTtjw1Fr5oHkbW8gcU7TnnmDvnFVUxYP9BF36kgV7u'
			# if there is no logo one uses default logo
			if not logo  :
				logo = 'QmXKeAgNZhLibNjYJFHCiXFvGhqsqNV2sJCggzGxnxyhJ5'

			if not path.exists(mode.uploads_path + signature) :
				url = 'https://gateway.pinata.cloud/ipfs/'+ signature
				response = requests.get(url, stream=True)
				with open(mode.uploads_path + signature, 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response

			if not path.exists(mode.uploads_path + logo) :
				url = 'https://gateway.pinata.cloud/ipfs/'+ logo
				response = requests.get(url, stream=True)
				with open(mode.uploads_path + logo, 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response

			return render_template('./certificate/experience_certificate.html',
							**menu,
							manager= session['displayed_certificate']['credentialSubject']['managerName'],
							badge=my_badge,
							title = session['displayed_certificate']['credentialSubject']['title'],
							identity_firstname=identity_profil['firstname'],
							identity_lastname=identity_profil['lastname'],
							description=session['displayed_certificate']['credentialSubject']['description'],
							start_date=session['displayed_certificate']['credentialSubject']['startDate'],
							end_date=session['displayed_certificate']['credentialSubject']['endDate'],
							signature=signature,
							logo=logo,
							certificate_id=certificate_id,
							identity_username=identity_username,
							issuer_username=issuer_username,
							viewer=viewer,
							#verify_link = session['displayed_certificate']['issuer']['website']+ "/verify?certificate_id=" + session['certificate_id'],
							**context)


		else : # issuer is a person
			return render_template('./certificate/certificate_light.html',
							**menu,
							manager= session['displayed_certificate']['manager'],
							badge=my_badge,
							title = session['displayed_certificate']['title'],
							identity_firstname=identity_profil['firstname'],
							identity_lastname=identity_profil['lastname'],
							description=session['displayed_certificate']['description'],
							start_date=session['displayed_certificate']['start_date'],
							end_date=session['displayed_certificate']['end_date'],
							certificate_id=certificate_id,
							identity_username=identity_username,
							issuer_username=issuer_username,
							viewer=viewer,
							**context)

	# Recommendation Certificate Display
	if session['displayed_certificate']['type'] == 'recommendation' :
		issuer_picture = session['displayed_certificate'].get('logo')
		if session['displayed_certificate']['issuer']['category'] == 1001 :
			issuer_picture = session['displayed_certificate'].get('picture')
		else :
			issuer_picture = session['displayed_certificate'].get('logo')

		issuer_title = "" if not session['displayed_certificate'].get('title')  else session['displayed_certificate']['title']
		if issuer_picture  :
			if not path.exists(mode.uploads_path + issuer_picture) :
				logging.info('picture already on disk')
				url='https://gateway.pinata.cloud/ipfs/'+ issuer_picture
				response = requests.get(url, stream=True)
				with open(mode.uploads_path + issuer_picture, 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response

		description = """ " """ + session['displayed_certificate']['description'] + """ " """
		return render_template('./certificate/recommendation_certificate.html',
							**menu,
							identity_firstname=identity_profil['firstname'],
							identity_lastname=identity_profil['lastname'],
							description=description,
							issuer_picture=issuer_picture,
							issuer_title=issuer_title,
							issuer_firstname=session['displayed_certificate']['issuer']['firstname'] if session['displayed_certificate']['issuer']['category']== 1001 else "",
							issuer_lastname=session['displayed_certificate']['issuer']['lastname']if session['displayed_certificate']['issuer']['category']== 1001 else "",
							relationship=session['displayed_certificate']['relationship'],
							certificate_id=certificate_id,
							identity_username=identity_username,
							issuer_username=issuer_username,
							viewer=viewer
							)

	# Skill Certificate Display
	if session['displayed_certificate']['type'] == 'skill' :
		issuer_picture = session['displayed_certificate'].get('picture')
		issuer_title = "" if not session['displayed_certificate'].get('title') else session['displayed_certificate']['title']

		description = session['displayed_certificate']['description'].replace('\r\n','<br>')

		signature = session['displayed_certificate']['signature']
		logo = session['displayed_certificate']['logo']
		# if there is no signature one uses Picasso signature
		if not signature  :
			signature = 'QmS9TTtjw1Fr5oHkbW8gcU7TnnmDvnFVUxYP9BF36kgV7u'
		# if there is no logo one uses default logo
		if not logo  :
			logo = 'QmXKeAgNZhLibNjYJFHCiXFvGhqsqNV2sJCggzGxnxyhJ5'

		if not path.exists(mode.uploads_path + signature) :
				url = 'https://gateway.pinata.cloud/ipfs/'+ signature
				response = requests.get(url, stream=True)
				with open(mode.uploads_path + signature, 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response

		if not path.exists(mode.uploads_path + logo) :
			url = 'https://gateway.pinata.cloud/ipfs/'+ logo
			response = requests.get(url, stream=True)
			with open(mode.uploads_path + logo, 'wb') as out_file:
				shutil.copyfileobj(response.raw, out_file)
			del response

		return render_template('./certificate/skill_certificate.html',
							**menu,
							manager= session['displayed_certificate']['manager'],
							identity_firstname=identity_profil['firstname'],
							identity_lastname=identity_profil['lastname'],
							identity_name =identity_profil['firstname'] + ' ' + identity_profil['lastname'],
							description=description,
							issuer_picture=issuer_picture,
							signature=signature,
							logo=logo,
							certificate_id=certificate_id,
							title=session['displayed_certificate']['title'],
							issuer_name=session['displayed_certificate']['issuer']['name'],
							viewer=viewer
							)
	# if agreement certificate display
	if session['displayed_certificate']['type'] == 'agreement':
		description = session['displayed_certificate']['description'].replace('\r\n','<br>')

		signature = session['displayed_certificate']['issued_by'].get('signature')
		logo = session['displayed_certificate']['issued_by'].get('logo')

		# if there is no signature or no logo , view is reduced see html else we download file rom ipfs if needed
		if signature and logo :
			if not path.exists(mode.uploads_path + signature) :
				url = 'https://gateway.pinata.cloud/ipfs/'+ signature
				response = requests.get(url, stream=True)
				with open(mode.uploads_path + signature, 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response

			if not path.exists(mode.uploads_path + logo) :
				url = 'https://gateway.pinata.cloud/ipfs/'+ logo
				response = requests.get(url, stream=True)
				with open(mode.uploads_path + logo, 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response

		if session['displayed_certificate']['service_product_group'] :
			products = session['displayed_certificate']['service_product_group'].replace(' ', '').split(",")
			service_product_group = ""
			for product in products:
				service_product_group = service_product_group + """<li class="text-dark my-2 mx-5">""" + product.capitalize() + "</li>"
		else :
			service_product_group = None

		return render_template('./certificate/agreement_certificate.html',
							**menu,
							date_of_issue = session['displayed_certificate']['date_of_issue'],
							date_of_validity = session['displayed_certificate']['valid_until'],
							location = session['displayed_certificate']['location'],
							description=description,
							logo=logo,
							issued_to_name = session['displayed_certificate']['issued_to'].get('name', ''),
							issuer_name = session['displayed_certificate']['issued_by'].get('name',''),
							issuer_siret = session['displayed_certificate']['issued_by'].get('siret', ''),
							title = session['displayed_certificate']['title'],
							signature=signature,
							viewer=viewer,
							standard=session['displayed_certificate']['standard'],
							registration_number = session['displayed_certificate']['registration_number'],
							service_product_group = service_product_group,
							certificate_id=certificate_id,
							)
	# if reference certificate display
	if session['displayed_certificate']['type'] == 'reference' :
		yellow_star = "color: rgb(251,211,5); font-size: 12px;" # yellow
		black_star = "color: rgb(0,0,0);font-size: 12px;" # black

		# Icon "fa-star" treatment
		score = []
		context = dict()
		score.append(int(session['displayed_certificate'].get('score_delivery',1)))
		score.append(int(session['displayed_certificate'].get('score_schedule', 1)))
		score.append(int(session['displayed_certificate'].get('score_communication',1)))
		score.append(int(session['displayed_certificate'].get('score_budget', 1)))
		score.append(int(session['displayed_certificate'].get('score_recommendation',1)))

		for q in range(0,5) :
			for i in range(0,score[q]) :
				context["star"+str(q)+str(i)] = yellow_star
			for i in range(score[q],5) :
				context ["star"+str(q)+str(i)] = black_star

		description = session['displayed_certificate'].get('description','Unknown').replace('\r\n','<br>')

		signature = session['displayed_certificate']['issued_by']['signature']
		logo = session['displayed_certificate']['issued_by']['logo']

		if signature and logo :
			if not path.exists(mode.uploads_path + signature) :
				url = 'https://gateway.pinata.cloud/ipfs/'+ signature
				response = requests.get(url, stream=True)
				with open(mode.uploads_path + signature, 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response

			if not path.exists(mode.uploads_path + logo) :
				url = 'https://gateway.pinata.cloud/ipfs/'+ logo
				response = requests.get(url, stream=True)
				with open(mode.uploads_path + logo, 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response

		if session['displayed_certificate']['competencies'] :
			# cf probleme avec autre modifs / CCI
			#competencies = session['displayed_certificate']['competencies'].replace(' ', '').split(",")
			competencies = session['displayed_certificate']['competencies']
			my_badge = ""
			for competencie in competencies :
				my_badge = my_badge + """<span class="badge badge-pill badge-secondary" style="margin: 4px; padding: 8px;"> """+ competencie.capitalize() + """</span>"""
		else :
			my_badge = None

		return render_template('./certificate/reference_certificate.html',
							**menu,
							issued_to_name = session['displayed_certificate']['issued_to']['name'],
							start_date = session['displayed_certificate']['start_date'],
							end_date = session['displayed_certificate']['end_date'],
							location = session['displayed_certificate'].get('location', 'Unknown'),
							staff = session['displayed_certificate'].get('staff', 'Unknown'),
							budget = session['displayed_certificate'].get('budget', 'Unknown'),
							description=description,
							logo=logo,
							issuer_name = session['displayed_certificate']['issued_by']['name'],
							title = session['displayed_certificate'].get('title', 'Unknown'),
							signature=signature,
							badge = my_badge,
							manager = session['displayed_certificate']['issued_by']['manager'],
							certificate_id=certificate_id,
							viewer=viewer,
							**context)



#		 verify certificate
#@app.route('/certificate/verify/, methods=['GET'])
def certificate_verify(mode) :

	menu = session.get('menu', dict())
	viewer = 'guest' if not session.get('username') else 'user'

	certificate_id = request.args['certificate_id']
	identity_workspace_contract = '0x'+ certificate_id.split(':')[3]
	issuer_workspace_contract = session['displayed_certificate']['issuer']['workspace_contract']
	certificate = copy.deepcopy(session['displayed_certificate'])
	convert(certificate)

	if certificate_id != certificate['id'] :
		content = json.dumps({'topic' : 'error', 'msg' : 'Certificate Not Found'})
		response = Response(content, status=406, mimetype='application/json')
		return response

	issuer_type = 'Person' if certificate['issuer']['category'] == 1001 else 'Company'

	user_profil, user_category = read_profil(identity_workspace_contract, mode, 'full')
	user_type = 'Person' if user_category == 1001 else 'Company'
	convert(user_profil)

	# Issuer , Referent
	if issuer_type == 'Company' :
		issuer = """
				<span>
				<b>Referent Identity (Issuer)</b><a class="text-secondary" href=/certificate/issuer_explore/?workspace_contract=""" + issuer_workspace_contract +"""&certificate_id=""" + certificate_id + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Check Issuer Identity"></i></a>
				<br><b>DID</b> : """ + certificate['issuer']['id']
	if issuer_type == 'Person' :
		issuer = """
				<span>
				<hr>
				<b>Referent Identity (Issuer)</b><a class="text-secondary" href=/certificate/issuer_explore/?workspace_contract=""" + issuer_workspace_contract + """&certificate_id=""" + certificate_id +""">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Check Issuer Identity"></i></a>
				<br><b>DID</b> : """ + certificate['issuer']['id']


	# User, Receiver
	user =""
	if user_type == 'Company' :
		user = """
				<span>
				<hr>
				<b>User Identity</b><a class="text-secondary" href=/certificate/issuer_explore/?workspace_contract=""" + identity_workspace_contract + """&certificate_id=""" + certificate_id +""">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Check User Identity"></i></a>
				<br><b>DID</b> : """ + 'did:talao:'+ mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:]
	#if user_type == 'Person' :
	#	user = """
	#			<span>
	#			<hr>
	#			<b>User Identity (Receiver)</b><a class="text-secondary" href=/certificate/issuer_explore/?workspace_contract=""" + identity_workspace_contract + """&certificate_id=""" + certificate_id +""">
	#					<i data-toggle="tooltip" class="fa fa-search-plus" title="Check User Identity"></i></a>
	#			<br><b>DID</b> : """ + 'did:talao:'+ mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:]

	# Verifiable Credential
	credential = Document('certificate')
	doc_id = int(session['certificate_id'].split(':')[5])
	credential.relay_get_credential(identity_workspace_contract, doc_id, mode, loading = 'full')
	credential_text = json.dumps(credential.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

	my_verif = "".join([issuer, user, '<br>'])

	return render_template('./certificate/verify_certificate.html',
							**menu,
							certificate_id=certificate_id,
							topic = certificate['topic'].capitalize(),
							credential = credential_text,
							verif=my_verif,
							viewer=viewer,
							)



# issuer explore
#@app.route('/guest/', methods=['GET'])
#@app.route('/certificate/issuer_explore/', methods=['GET'])
def certificate_issuer_explore(mode) :
	""" This can be an entry point too"""
	menu = session.get('menu', dict())
	viewer = 'guest' if not session.get('username')  else 'user'

	issuer_workspace_contract = request.args['workspace_contract']
	certificate_id = request.args.get('certificate_id')
	#session['certificate_id'] = certificate_id
	try :
		issuer_explore = Identity(issuer_workspace_contract, mode, authenticated=False)
	except :
		logging.warning('issuer does not exist')
		flash('Identity not found ', 'danger')
		return redirect(mode.server + 'certificate/verify/?certificate_id=' + certificate_id)

	if issuer_explore.type == 'person' :
		session['resume']= issuer_explore.__dict__
		""" clean up """
		del session['resume']['file_list']
		del session['resume']['experience_list']
		del session['resume']['education_list']
		del session['resume']['other_list']
		del session['resume']['kbis_list']
		del session['resume']['certificate_list']
		del session['resume']['partners']
		del session['resume']['synchronous']
		del session['resume']['authenticated']
		del session['resume']['rsa_key']
		del session['resume']['relay_activated']
		del session['resume']['private_key']
		del session['resume']['category']
		del session['resume']['identity_file']
		session['resume']['topic'] = 'resume'

	if issuer_explore.type == 'person' :
		# personal
		Topic = {'firstname' : 'Firstname',
				'lastname' : 'Lastname',
				'about' : 'About',
				'profil_title' : 'Title',
				'birthdate' : 'Birth Date',
				'contact_email' : 'Contact Email',
				'contact_phone' : 'Contact Phone',
				'postal_address' : 'Postal Address',
				'education' : 'Education'}
		issuer_username =	 ns.get_username_from_resolver(issuer_workspace_contract, mode)
		issuer_username = 'Unknown' if not issuer_username else issuer_username
		issuer_personal = """<span><b>Username</b> : """ + issuer_username +"""<br>"""
		for topic_name in issuer_explore.personal.keys() :
			if issuer_explore.personal[topic_name]['claim_value']  :
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:] + ':claim:' + issuer_explore.personal[topic_name]['claim_id']
				issuer_personal = issuer_personal + """
				<span><b>"""+ Topic[topic_name] +"""</b> : """+ issuer_explore.personal[topic_name]['claim_value']+"""
					
				</span><br>"""

		# Proofs of Identity
		my_kyc = ""

		#if not len (issuer_explore.kyc):
		#	my_kyc = """<a class="text-danger">No Certificate of Identity available</a>"""
		#else :
		#	my_kyc = "<b>Certificate issued by Talao</b><br><br>"
		#	for kyc in issuer_explore.kyc :
		#		kyc_html = """
		#		<b>Firstname</b> : """+ kyc['firstname'] +"""<br>
		#		<b>Lastname</b> : """+ kyc['lastname'] +"""<br>
		#		<b>Birth Date</b> : """+ kyc['birthdate'] +"""<br>
		#		<b>Gender</b> : """+ kyc['sex'] +"""<br>
		#		<b>Nationality</b> : """+ kyc['nationality'] + """<br>
		#		<b>Date of Issue</b> : """+ kyc['date_of_issue']+"""<br>
		#		<b>Date of Expiration</b> : """+ kyc['date_of_expiration']+"""<br>
		#		<b>Authority</b> : """+ kyc['authority']+"""<br>
		#		<b>Country</b> : """+ kyc['country']+"""<br>
		#		<b>Card Id</b> : """+ kyc['card_id']+"""<br>
		#		<p>
		#			<a class="text-secondary" href=/certificate/data/?dataId="""+ kyc['id'] + """:kyc>
		#				<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
		#			</a>
		#		</p>"""
		#		my_kyc = my_kyc + kyc_html


		# experience
		issuer_experience = ''
		if issuer_explore.experience == [] :
			issuer_experience = """  <a class="text-info">No data available</a>"""
		else :
			for experience in issuer_explore.experience :
				exp_html = """
					<b>Company</b> : """+experience['company']['name']+"""<br>
					<b>Title</b> : """+experience['title']+"""<br>
					<b>Description</b> : """+experience['description'][:100]+"""...<br>
					<p>
						
					</p>"""
				issuer_experience = issuer_experience + exp_html + """<hr>"""

		# education
		issuer_education = ''
		if issuer_explore.education == [] :
			issuer_education = """  <a class="text-info">No data available</a>"""
		else :
			for education in issuer_explore.education :
				edu_html = """
					<b>Organization</b> : """+education['organization']['name']+"""<br>
					<b>Title</b> : """+education['title']+"""<br>
					<b>Description</b> : """+education['description'][:100]+"""...<br>
					<p>
						
					</p>"""
				issuer_education = issuer_education + edu_html + """<hr>"""

		# skills
		if not issuer_explore.skills or not issuer_explore.skills.get('id') :
			issuer_skills =  """<a class="text-info">No Skills Available</a>"""
		else :
			issuer_skills = ""
			for skill in issuer_explore.skills['description'] :
				skill_html = """
				"""+ skill['skill_name'] + """ (""" + skill['skill_level'] + """)""" + """<br>
	<!--			<b>Domain</b> : """+skill['skill_domain'] + """<br>
				<b>Level</b> : """+ skill['skill_level'] + """...<br>
				<p>
					<a class="text-secondary" href="/user/remove_experience/?experience_id="""  + """>
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>

					
				</p>  -->"""
				issuer_skills = issuer_skills + skill_html
			issuer_skills = issuer_skills + """
				<p>
				
				</p>"""

		# certificates
		issuer_certificates = ""
		if issuer_explore.certificate == [] :
			issuer_certificates = """<a class="text-info">No data available</a>"""
		else :
			for certificate in issuer_explore.certificate :
				certificate_issuer_username = ns.get_username_from_resolver(certificate['issuer']['workspace_contract'], mode)
				certificate_issuer_username = 'Unknown' if not certificate_issuer_username else certificate_issuer_username
				if certificate['issuer']['category'] == 2001 :
					certificate_issuer_name = certificate['issuer']['name']
					#certificate_issuer_type = 'Company'
				elif  certificate['issuer']['category'] == 1001 :
					certificate_issuer_name = certificate['issuer']['firstname'] + ' ' + certificate['issuer']['lastname']
					#certificate_issuer_type = 'Person'
				else :
					pass
				cert_html = """
						<b>Issuer Name</b> : """ + certificate_issuer_name +"""<br>
						<b>Title</b> : """ + certificate['title']+"""<br>
						<b>Description</b> : """ + certificate['description'][:100]+"""...<br>
						<b></b><a href= """ + mode.server +  """guest/certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer_workspace_contract[2:] + """:document:""" + str(certificate['doc_id']) + """>Display Certificate</a><br>
						<p>
							
						</p>"""
				issuer_certificates = issuer_certificates + cert_html + """<hr>"""
		# services
		#services ="""
		#		<a class="text-success" href="/certificate/certificate_data_analysis/" >Talent Dashboard</a></br>
		#		<a class="text-success" href="" >Send a memo to this Talent</a></br>
		#		<a href="/register/" class="text-warning"> Register to get access to other services.</a><br><br>"""

		return render_template('./certificate/certificate_person_issuer_identity.html',
							**menu,
							issuer_name=issuer_explore.name,
							issuer_profil_title = issuer_explore.profil_title,
							kyc=my_kyc,
							personal=issuer_personal,
							experience=issuer_experience,
							skills=issuer_skills,
							certificates=issuer_certificates,
							education=issuer_education,
							#services=services,
							issuer_picturefile=issuer_explore.picture,
							certificate_id= certificate_id,
							viewer=viewer,)


	if issuer_explore.type == 'company' :

		# kbis
		if not issuer_explore.personal['website']['claim_value'] and not issuer_explore.kbis :
			my_kbis = """<p class="text-warning">No data available</p><br>"""

		if issuer_explore.personal['website']['claim_value'] :
			#on_line_check = on_line_checking(issuer_explore.personal['website']['claim_value'])
			my_kbis = """<b>Contact</b> : """ + issuer_explore.personal['contact_email']['claim_value'] #+ """ <br>
			#	<b>Visual check</b> : <a href=" """ + issuer_explore.personal['website']['claim_value'] + """/did/">""" + issuer_explore.personal['website']['claim_value'] + """</a><br>
			#	<b>On-Line check</b> : """ + on_line_check

		for kbis in issuer_explore.kbis :
			my_kbis = my_kbis + "<hr><b>Certificate issued by Talao</b><br><br>"
			kbis_html = """
				<b>Name</b> : """+ kbis['name'] +"""<br>
				<b>Siret</b> : """+ kbis['siret'] +"""<br>
				<b>Creation</b> : """+ kbis['date'] + """<br>
				<b>Capital</b> : """+ kbis['capital']+"""<br>
				<b>Address</b> : """+ kbis['address']+"""<br>
				<p>
					
				</p>"""
			my_kbis = my_kbis + kbis_html

		# personal
		issuer_username =	 ns.get_username_from_resolver(issuer_workspace_contract, mode)
		issuer_username = 'Unknown' if not issuer_username  else issuer_username
		issuer_personal = """ <span><b>Username</b> : """ + issuer_username	+ """<br>"""
		for topic_name in issuer_explore.personal.keys() :
			if issuer_explore.personal[topic_name]['claim_value'] :
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:] + ':claim:' + issuer_explore.personal[topic_name]['claim_id']
				issuer_personal = issuer_personal + """
				<span><b>"""+ topic_name +"""</b> : """+ issuer_explore.personal[topic_name]['claim_value']+"""
					
				</span><br>"""

		services ="""<a class="text-warning">Register to get access to services.</a><br><br>"""

		return render_template('./certificate/certificate_company_issuer_identity.html',
							**menu,
							issuer_name=issuer_explore.name,
							kbis=my_kbis,
							services=services,
							personal=issuer_personal,
							issuer_picturefile=issuer_explore.picture,
							certificate_id=certificate_id,
							viewer=viewer,)




# Analysis
#@app.route('/certificate/data_analysis/', methods=['GET'])
def certificate_data_analysis(mode) :

	viewer = 'guest' if not session.get('username') else 'user'

	certificate_id = session['certificate_id']
	identity_workspace_contract = '0x' + certificate_id.split(':')[3]
	if request.method == 'GET' :
		my_analysis = analysis.dashboard(identity_workspace_contract, session['resume'], mode)

		return render_template('dashboard.html',
								viewer= viewer,
								**my_analysis)
