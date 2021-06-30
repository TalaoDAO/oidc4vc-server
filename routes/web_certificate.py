
from os import path
from flask import session, flash, jsonify
from flask import request, redirect, render_template,Response
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA512
from flask_babel import _


import requests
import shutil
import json

import logging
logging.basicConfig(level=logging.INFO)

# dependances
from protocol import Document, Identity, Claim, ownersToContracts
from components import ns
from signaturesuite import helpers

SALT = 'repository_salt'


def init_app(app, mode) :
	app.add_url_rule('/certificate/',  view_func=show_certificate, defaults={'mode': mode})
	app.add_url_rule('/guest/certificate/',  view_func=show_certificate, defaults={'mode': mode})  # idem previous
	app.add_url_rule('/certificate/verify/',  view_func=certificate_verify, methods = ['GET'], defaults={'mode': mode})
	app.add_url_rule('/certificate/issuer_explore/',  view_func=certificate_issuer_explore, methods = ['GET'], defaults={'mode': mode})
	app.add_url_rule('/guest/',  view_func=certificate_issuer_explore, methods = ['GET'], defaults={'mode': mode}) # idem previous
	return


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

	try  :
		certificate_id = request.args['certificate_id']
		method = certificate_id.split(':')[1]
		# translator for repository claim
		if method in ['web', 'tz', 'ethr'] :
			did = 'did:' + method + ':' + certificate_id.split(':')[2]
			private_key = '0x' + PBKDF2(did.encode(), SALT, 32, count=1000000, hmac_hash_module=SHA512).hex()
			address = helpers.ethereum_pvk_to_address(private_key)
			workspace_contract = ownersToContracts(address, mode)
			claim_id = certificate_id.split(':')[4]
			credential = Claim()
			credential.get_by_id( mode.relay_workspace_contract, None, workspace_contract, claim_id, mode)
			return jsonify(credential.claim_value)

		# standard
		elif method == 'talao' :
			try :
				doc_id = int(certificate_id.split(':')[5])
				identity_workspace_contract = '0x'+ certificate_id.split(':')[3]
			except :
				content = json.dumps({'message' : 'request malformed'})
				return Response(content, status=406, mimetype='application/json')
		else :
			content = json.dumps({'message' : 'method not supported'})
			return Response(content, status=406, mimetype='application/json')

	except :
		content = json.dumps({'message' : 'request malformed'})
		return Response(content, status=406, mimetype='application/json')


	if session.get('certificate_id') != request.args['certificate_id'] :
		certificate = Document('certificate')
		if not certificate.relay_get(identity_workspace_contract, doc_id, mode) :
			content = json.dumps({'message' : 'This credential does not exist or it has been deleted'})
			return Response(content, status=406, mimetype='application/json')
		if certificate.privacy != 'public' :
			content = json.dumps({'message' : 'This credential is private'})
			return Response(content, status=406, mimetype='application/json')
		session['displayed_certificate'] = certificate.__dict__

	# ProfessionalExperienceAssessment Display
	if "ProfessionalExperienceAssessment" in session['displayed_certificate']['type'] :
		yellow_star = "color: rgb(251,211,5); font-size: 12px;" # yellow
		black_star = "color: rgb(0,0,0);font-size: 12px;" # black

		# Icon "fa-star" treatment
		score = []
		context = dict()
		reviewRecommendation, reviewDelivery, reviewSchedule, reviewCommunication = 0,1,2,3
		score.append(int(session['displayed_certificate']['credentialSubject']['review'][reviewRecommendation]['reviewRating']['ratingValue']))
		score.append(int(session['displayed_certificate']['credentialSubject']['review'][reviewDelivery]['reviewRating']['ratingValue']))
		score.append(int(session['displayed_certificate']['credentialSubject']['review'][reviewSchedule]['reviewRating']['ratingValue']))
		score.append(int(session['displayed_certificate']['credentialSubject']['review'][reviewCommunication]['reviewRating']['ratingValue']))
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
			my_badge = ""

		# if there is no signature one uses Picasso signature
		signature = session['displayed_certificate']['credentialSubject']['signatureLines']['image']
		if not signature :
			signature = 'QmS9TTtjw1Fr5oHkbW8gcU7TnnmDvnFVUxYP9BF36kgV7u'

		# if there is no logo one uses default logo
		logo = session['displayed_certificate']['credentialSubject']['author']['logo']
		if not logo  :
			logo = 'QmXKeAgNZhLibNjYJFHCiXFvGhqsqNV2sJCggzGxnxyhJ5'

		# upload signature and logo on server
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
		try :
			name = session['displayed_certificate']['credentialSubject']['recipient']['givenName'] + ' ' + \
				session['displayed_certificate']['credentialSubject']['recipient']['familyName']
		except :
			name = session['displayed_certificate']['credentialSubject']['recipient']['name']
			
		return render_template('./certificate/experience_certificate.html',
							**menu,
							managerName=session['displayed_certificate']['credentialSubject']['signatureLines']['name'],
							companyName=session['displayed_certificate']['credentialSubject']['author']['name'],
							badge=my_badge,
							title = session['displayed_certificate']['credentialSubject']['title'],
							subject_name = name,
							description=session['displayed_certificate']['credentialSubject']['description'],
							start_date=session['displayed_certificate']['credentialSubject']['startDate'],
							end_date=session['displayed_certificate']['credentialSubject']['endDate'],
							signature=signature,
							logo=logo,
							certificate_id=certificate_id,
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
							#identity_firstname=identity_profil['firstname'],
							#identity_lastname=identity_profil['lastname'],
							description=description,
							issuer_picture=issuer_picture,
							issuer_title=issuer_title,
							issuer_firstname=session['displayed_certificate']['issuer']['firstname'] if session['displayed_certificate']['issuer']['category']== 1001 else "",
							issuer_lastname=session['displayed_certificate']['issuer']['lastname']if session['displayed_certificate']['issuer']['category']== 1001 else "",
							relationship=session['displayed_certificate']['relationship'],
							certificate_id=certificate_id,
							#identity_username=identity_username,
							#issuer_username=issuer_username,
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
							#identity_firstname=identity_profil['firstname'],
							#identity_lastname=identity_profil['lastname'],
							#identity_name =identity_profil['firstname'] + ' ' + identity_profil['lastname'],
							description=description,
							issuer_picture=issuer_picture,
							signature=signature,
							logo=logo,
							certificate_id=certificate_id,
							title=session['displayed_certificate']['title'],
							#issuer_name=session['displayed_certificate']['issuer']['name'],
							viewer=viewer
							)
	# agreement certificate display
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

	# if reference credential display
	if session['displayed_certificate']['credentialSubject']['credentialCategory'] == 'reference' :
		yellow_star = "color: rgb(251,211,5); font-size: 12px;" # yellow
		black_star = "color: rgb(0,0,0);font-size: 12px;" # black

		description = session['displayed_certificate'].get('description','Unknown').replace('\r\n','<br>')

		signature = session['displayed_certificate']['credentialSubject']['managerSignature']
		logo = session['displayed_certificate']['credentialSubject']['companyLogo']

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
		skills_str = ""
		try :
			for skill in session['displayed_certificate']['credentialSubject']['offers']['skills'] :
				skills_str += skill['description'] + ','
		except :
			logging.warning('skills not found')
		return render_template('./certificate/reference_certificate.html',
							**menu,
							issued_to_name = session['displayed_certificate']['credentialSubject']['name'],
							issuanceDate = session['displayed_certificate']['issuanceDate'][:10],
							startDate = session['displayed_certificate']['credentialSubject']['offers']['startDate'],
							endDate = session['displayed_certificate']['credentialSubject']['offers']['endDate'],
							price = session['displayed_certificate']['credentialSubject']['offers']['price'],
							currency = session['displayed_certificate']['credentialSubject']['offers']['priceCurrency'],
							description=session['displayed_certificate']['credentialSubject']['offers']['description'],
							review= session['displayed_certificate']['credentialSubject']['review']['reviewBody'],
							location=session['displayed_certificate']['credentialSubject']['offers']['location'],
							logo=logo,
							issuer_name = session['displayed_certificate']['credentialSubject']['companyName'],
							title = session['displayed_certificate']['credentialSubject']['offers']['title'],
							signature=signature,
							manager = session['displayed_certificate']['credentialSubject']['companyName'],
							certificate_id=certificate_id,
							viewer=viewer,
							skills=skills_str
							)

	else :
		# clean up to get a standard credential
		del session['displayed_certificate']['topic']
		del session['displayed_certificate']['doc_id']
		del session['displayed_certificate']['data_location']
		del session['displayed_certificate']['privacy']
		return jsonify(session['displayed_certificate'])

def certificate_verify(mode) :
	"""		 verify credential data and did
	"""
	menu = session.get('menu', dict())
	viewer = 'guest' if not session.get('username') else 'user'

	try :
		certificate_id = request.args['certificate_id']
		identity_workspace_contract = '0x'+ certificate_id.split(':')[3]
		credential = Document('certificate')
		doc_id = int(certificate_id.split(':')[5])
		credential.relay_get_credential(identity_workspace_contract, doc_id, mode)
		credential_text = json.dumps(credential.__dict__, sort_keys=True, indent=4, ensure_ascii=False)
	except :
		logging.error('data not found')
		return jsonify ({'result' : 'certificate not found'})

	# Issuer , Referent
	issuer = """<b>""" + _('Issuer DID') + """</b> : """ + credential.issuer

	# User, holder
	user = """<b>""" + _('User DID') + """</b> : """ + credential.credentialSubject['id']

	my_verif = "".join([issuer, "<br>", user, '<br>'])

	return render_template('./certificate/verify_certificate.html',
							**menu,
							certificate_id=certificate_id,
							topic = "",
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
				#topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:] + ':claim:' + issuer_explore.personal[topic_name]['claim_id']
				issuer_personal = issuer_personal + """
				<span><b>"""+ Topic[topic_name] +"""</b> : """+ issuer_explore.personal[topic_name]['claim_value']+"""
				</span><br>"""

		# Proofs of Identity
		my_kyc = ""

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
				elif  certificate['issuer']['category'] == 1001 :
					certificate_issuer_name = certificate['issuer']['firstname'] + ' ' + certificate['issuer']['lastname']
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
							issuer_picturefile=issuer_explore.picture,
							certificate_id= certificate_id,
							viewer=viewer,)


	if issuer_explore.type == 'company' :

		# kbis
		if not issuer_explore.personal['website']['claim_value'] and not issuer_explore.kbis :
			my_kbis = """<p class="text-warning">No data available</p><br>"""

		if issuer_explore.personal['website']['claim_value'] :
			my_kbis = """<b>Contact</b> : """ + issuer_explore.personal['contact_email']['claim_value'] #+ """ <br>

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
