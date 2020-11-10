
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

# dependances
from protocol import Document, read_profil, Identity, Claim
import constante
import ns
import analysis

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

# display experience certificate for anybody. Stand alone routine
# #route /guest/certificate
# @route /certificate/
def show_certificate(mode):

	menu = session.get('menu', dict())
	viewer = 'guest' if session.get('username') is None else 'user'
	certificate_id = request.args['certificate_id']
	print('certificate_id = ', certificate_id)
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
			content = json.dumps({'topic' : 'error', 'msg' : 'Certificate Not Found'})
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
			my_badge = my_badge + """<span class="badge badge-pill badge-secondary" style="margin: 4px; padding: 8px;"> """+ skill_to_display + """</span>"""
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
							title = session['displayed_certificate']['title'],
							)

	if self_claim == "education" :
		description = session['displayed_certificate']['description'].replace('\r\n','<br>')

		my_badge = ''
		for skill in session['displayed_certificate']['skills'] :
			skill_to_display = skill.replace(" ", "").capitalize().strip(',')
			if skill_to_display != '':
				my_badge = my_badge + """<span class="badge badge-pill badge-secondary" style="margin: 4px; padding: 8px;"> """+ skill_to_display + """</span>"""
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
							title = session['displayed_certificate']['title'],
							link = session['displayed_certificate']['certificate_link']
							)

	# Experience Certificate Display
	if session['displayed_certificate']['type'] == 'experience' :
		yellow_star = "color: rgb(251,211,5); font-size: 12px;" # yellow
		black_star = "color: rgb(0,0,0);font-size: 12px;" # black

		# Icon "fa-star" treatment
		score = []
		context = dict()
		score.append(int(session['displayed_certificate']['score_recommendation']))
		score.append(int(session['displayed_certificate']['score_delivery']))
		score.append(int(session['displayed_certificate']['score_schedule']))
		score.append(int(session['displayed_certificate']['score_communication']))
		for q in range(0,4) :
			for i in range(0,score[q]) :
				context["star"+str(q)+str(i)] = yellow_star
			for i in range(score[q],5) :
				context ["star"+str(q)+str(i)] = black_star

		my_badge = ""
		for skill in session['displayed_certificate']['skills'] :
			skill_to_display = skill.replace(" ", "").capitalize()
			my_badge = my_badge + """<span class="badge badge-pill badge-secondary" style="margin: 4px;"> """+ skill_to_display + """</span>"""

		if session['displayed_certificate']['issuer']['category'] == 2001 : # company
			signature = session['displayed_certificate']['signature']
			logo = session['displayed_certificate']['logo']

			# if there is no signature one uses Picasso signature
			if signature is None :
				signature = 'QmS9TTtjw1Fr5oHkbW8gcU7TnnmDvnFVUxYP9BF36kgV7u'
			# if there is no logo one uses default logo
			if logo is None :
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

			return render_template('./certificate/certificate.html',
							**menu,
							manager= session['displayed_certificate']['manager'],
							badge=my_badge,
							title = session['displayed_certificate']['title'],
							identity_firstname=identity_profil['firstname'],
							identity_lastname=identity_profil['lastname'],
							description=session['displayed_certificate']['description'],
							start_date=session['displayed_certificate']['start_date'],
							end_date=session['displayed_certificate']['end_date'],
							signature=signature,
							logo=logo,
							certificate_id=certificate_id,
							identity_username=identity_username,
							issuer_username=issuer_username,
							viewer=viewer,
							verify_link = session['displayed_certificate']['issuer']['website']+ "/verify?certificate_id=" + session['certificate_id'],
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
		issuer_picture = session['displayed_certificate'].get('picture')
		issuer_title = "" if session['displayed_certificate'].get('title') is None else session['displayed_certificate']['title']

		if issuer_picture != None :
			if not path.exists(mode.uploads_path + issuer_picture) :
				print('picture already on disk')
				url='https://gateway.pinata.cloud/ipfs/'+ issuer_picture
				response = requests.get(url, stream=True)
				with open(mode.uploads_path + issuer_picture, 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response
			else :
				print('no picture on disk')
		description = """ " """ + session['displayed_certificate']['description'] + """ " """
		return render_template('./certificate/recommendation.html',
							**menu,
							identity_firstname=identity_profil['firstname'],
							identity_lastname=identity_profil['lastname'],
							description=description,
							issuer_picture=issuer_picture,
							issuer_title=issuer_title,
							issuer_firstname=session['displayed_certificate']['issuer']['firstname'],
							issuer_lastname=session['displayed_certificate']['issuer']['lastname'],
							relationship=session['displayed_certificate']['relationship'],
							certificate_id=certificate_id,
							identity_username=identity_username,
							issuer_username=issuer_username,
							viewer=viewer
							)

	# Skill Certificate Display
	if session['displayed_certificate']['type'] == 'skill' :
		issuer_picture = session['displayed_certificate'].get('picture')
		issuer_title = "" if session['displayed_certificate'].get('title') is None else session['displayed_certificate']['title']

		description = session['displayed_certificate']['description'].replace('\r\n','<br>')

		signature = session['displayed_certificate']['signature']
		logo = session['displayed_certificate']['logo']
		# if there is no signature one uses Picasso signature
		if signature is None :
			signature = 'QmS9TTtjw1Fr5oHkbW8gcU7TnnmDvnFVUxYP9BF36kgV7u'
		# if there is no logo one uses default logo
		if logo is None :
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

	if session['displayed_certificate']['type'] in ['agreement', 'agrement'] :
		description = session['displayed_certificate']['description'].replace('\r\n','<br>')

		signature = session['displayed_certificate']['issued_by']['signature']
		logo = session['displayed_certificate']['issued_by']['logo']
		# if there is no signature one uses Picasso signature
		if signature is None :
			signature = 'QmS9TTtjw1Fr5oHkbW8gcU7TnnmDvnFVUxYP9BF36kgV7u'
		# if there is no logo one uses default logo
		if logo is None :
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

		products = session['displayed_certificate']['service_product_group'].split(",")
		for product in products:
			service_product_group = """<li class="text-dark my-2 mx-5">""" + product + "</li>"

		print(session['displayed_certificate'])
		return render_template('./certificate/agreement_certificate.html',
							**menu,
							date_of_issue = session['displayed_certificate']['date_of_issue'],
							date_of_validity = session['displayed_certificate']['valid_until'],
							location = session['displayed_certificate']['location'],
							description=description,
							logo=logo,
							issued_to_name = session['displayed_certificate']['issued_to']['name'],
							issuer_name = session['displayed_certificate']['issued_by']['name'],
							issuer_siret = session['displayed_certificate']['issued_by']['siret'],
							title = session['displayed_certificate']['title'],
							signature=signature,
							registration_number = session['displayed_certificate']['registration_number'],
							service_product_group = service_product_group,
							certificate_id=certificate_id,
							)

	if session['displayed_certificate']['type'] == 'reference' :
		yellow_star = "color: rgb(251,211,5); font-size: 12px;" # yellow
		black_star = "color: rgb(0,0,0);font-size: 12px;" # black

		# Icon "fa-star" treatment
		score = []
		context = dict()
		score.append(int(session['displayed_certificate']['score_delivery']))
		score.append(int(session['displayed_certificate']['score_schedule']))
		score.append(int(session['displayed_certificate']['score_communication']))
		score.append(int(session['displayed_certificate']['score_budget']))
		score.append(int(session['displayed_certificate']['score_recommendation']))

		for q in range(0,5) :
			for i in range(0,score[q]) :
				context["star"+str(q)+str(i)] = yellow_star
			for i in range(score[q],5) :
				context ["star"+str(q)+str(i)] = black_star

		description = session['displayed_certificate']['project_description'].replace('\r\n','<br>')

		signature = session['displayed_certificate']['issued_by']['signature']
		logo = session['displayed_certificate']['issued_by']['logo']
		# if there is no signature one uses Picasso signature
		if signature is None :
			signature = 'QmS9TTtjw1Fr5oHkbW8gcU7TnnmDvnFVUxYP9BF36kgV7u'
		# if there is no logo one uses default logo
		if logo is None :
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

		my_badge = ''
		for competencies in session['displayed_certificate']['competencies'] :
			competencies_to_display = competencies.capitalize().strip(',')
			my_badge = my_badge + """<span class="badge badge-pill badge-secondary" style="margin: 4px; padding: 8px;"> """+ competencies_to_display + """</span>"""

		return render_template('./certificate/reference_certificate.html',
							**menu,
							start_date = session['displayed_certificate']['start_date'],
							end_date = session['displayed_certificate']['end_date'],
							location = session['displayed_certificate']['project_location'],
							staff = session['displayed_certificate']['project_staff'],
							budget = session['displayed_certificate']['project_budget'],
							description=description,
							logo=logo,
							issuer_name = session['displayed_certificate']['issued_by']['name'],
							title = session['displayed_certificate']['project_title'],
							signature=signature,
							badge = my_badge,
							manager = session['displayed_certificate']['issued_by']['manager'],
							certificate_id=certificate_id,
							**context)



#		 verify certificate
#@app.route('/certificate/verify/<dataId>', methods=['GET'])
def certificate_verify(mode) :

	menu = session.get('menu', dict())
	viewer = 'guest' if session.get('username') is None else 'user'

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
	if user_type == 'Company' :
		user = """
				<span>
				<hr>
				<b>User Identity</b><a class="text-secondary" href=/certificate/issuer_explore/?workspace_contract=""" + identity_workspace_contract + """&certificate_id=""" + certificate_id +""">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Check User Identity"></i></a>
				<br><b>DID</b> : """ + 'did:talao:'+ mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:]
	if user_type == 'Person' :
		user = """
				<span>
				<hr>
				<b>User Identity (Receiver)</b><a class="text-secondary" href=/certificate/issuer_explore/?workspace_contract=""" + identity_workspace_contract + """&certificate_id=""" + certificate_id +""">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Check User Identity"></i></a>
				<br><b>DID</b> : """ + 'did:talao:'+ mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:]

	# advanced
	path = """https://rinkeby.etherscan.io/tx/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/tx/"""
	# en attendant d'avoir une solution de chain explorer pour Talaonet....
	if mode.BLOCKCHAIN == 'talaonet' :
		blockchain = "TalaoNet RPC URL http://18.190.21.227:8502"
		transaction_hash = certificate['transaction_hash']
	else :
		blockchain = mode.BLOCKCHAIN.capitalize()
		transaction_hash = """ <a class = <a class= "card-link" href = """ + path + certificate['transaction_hash'] + """>"""+ certificate['transaction_hash']
	advanced = """<hr>
				<b>Blockchain</b> : """ + blockchain + """<br>
				<b>Document Id</b> : """ + certificate['id'] + """<br>
				<b>Transaction Hash</b> : """ + transaction_hash + """</a><br>
				<b>Certificate issued on </b> : """ + certificate['created'] + """<br>
				<b>Certificate expires on </b> : """ + certificate['expires'] + """<br>
				<b>Data storage</b> : <a class="card-link" href=""" + certificate['data_location'] + """>""" + certificate['data_location'] + """</a> <hr>"""

	my_verif = "".join([ advanced, issuer, user, '<br>'])

	return render_template('./certificate/verify_certificate.html',
							**menu,
							certificate_id=certificate_id,
							topic = certificate['topic'].capitalize(),
							verif=my_verif,
							viewer=viewer,
							)



# issuer explore
#@app.route('/guest/', methods=['GET'])
#@app.route('/certificate/issuer_explore/', methods=['GET'])
def certificate_issuer_explore(mode) :
	""" This can be an entry point too"""
	menu = session.get('menu', dict())
	viewer = 'guest' if session.get('username') is None else 'user'

	issuer_workspace_contract = request.args['workspace_contract']
	certificate_id = request.args.get('certificate_id')
	#session['certificate_id'] = certificate_id
	#print('certificate id ', certificate_id)
	issuer_explore = Identity(issuer_workspace_contract, mode, authenticated=False)

	if issuer_explore.type == 'person' :
		session['resume']= issuer_explore.__dict__
		""" clean up """
		del session['resume']['mode']
		del session['resume']['file_list']
		del session['resume']['experience_list']
		del session['resume']['education_list']
		del session['resume']['other_list']
		del session['resume']['kbis_list']
		del session['resume']['kyc_list']
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
		issuer_username = 'Unknown' if issuer_username is None else issuer_username
		issuer_personal = """<span><b>Username</b> : """ + issuer_username +"""<br>"""
		for topic_name in issuer_explore.personal.keys() :
			if issuer_explore.personal[topic_name]['claim_value'] is not None :
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:] + ':claim:' + issuer_explore.personal[topic_name]['claim_id']
				issuer_personal = issuer_personal + """
				<span><b>"""+ Topic[topic_name] +"""</b> : """+ issuer_explore.personal[topic_name]['claim_value']+"""
					<a class="text-secondary" href=/certificate/data/?dataId=""" + topicname_id + """:personal>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span><br>"""

		# Proofs of Identity
		if len (issuer_explore.kyc) == 0:
			my_kyc = """<a class="text-danger">No Certificate of Identity available</a>"""
		else :
			my_kyc = "<b>Certificate issued by Talao</b><br><br>"
			for kyc in issuer_explore.kyc :
				kyc_html = """
				<b>Firstname</b> : """+ kyc['firstname'] +"""<br>
				<b>Lastname</b> : """+ kyc['lastname'] +"""<br>
				<b>Birth Date</b> : """+ kyc['birthdate'] +"""<br>
				<b>Gender</b> : """+ kyc['sex'] +"""<br>
				<b>Nationality</b> : """+ kyc['nationality'] + """<br>
				<b>Date of Issue</b> : """+ kyc['date_of_issue']+"""<br>
				<b>Date of Expiration</b> : """+ kyc['date_of_expiration']+"""<br>
				<b>Authority</b> : """+ kyc['authority']+"""<br>
				<b>Country</b> : """+ kyc['country']+"""<br>
				<b>Card Id</b> : """+ kyc['card_id']+"""<br>
				<p>
					<a class="text-secondary" href=/certificate/data/?dataId="""+ kyc['id'] + """:kyc>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""
				my_kyc = my_kyc + kyc_html


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
						<a class="text-secondary" href=/certificate/data/?dataId="""+experience['id'] + """:experience>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
						</a>
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
						<a class="text-secondary" href=/certificate/data/?dataId="""+education['id'] + """:education>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
						</a>
					</p>"""
				issuer_education = issuer_education + edu_html + """<hr>"""

		# skills
		if issuer_explore.skills is None or issuer_explore.skills.get('id') is None :
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

					<a class="text-secondary" href=/data/?dataId=""" + """:experience>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>  -->"""
				issuer_skills = issuer_skills + skill_html
			issuer_skills = issuer_skills + """
				<p>
					<a class="text-secondary" href=/data/?dataId="""+ issuer_explore.skills['id'] + """:skills>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""

		# certificates
		issuer_certificates = ""
		if issuer_explore.certificate == [] :
			issuer_certificates = """<a class="text-info">No data available</a>"""
		else :
			for certificate in issuer_explore.certificate :
				certificate_issuer_username = ns.get_username_from_resolver(certificate['issuer']['workspace_contract'], mode)
				certificate_issuer_username = 'Unknown' if certificate_issuer_username is None else certificate_issuer_username
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
							<a class="text-secondary" href=/certificate/data/?dataId=""" + certificate['id'] + """:certificate>
								<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
							</a>
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
		print('issuer explore', issuer_explore.__dict__)
		# do something specific

		# kbis
		response = requests.post( issuer_explore.personal['website']['claim_value'] + '/on_line_did/' )
		print('response = ', response)
		print(issuer_explore.personal['website']['claim_value'] + '/on_line_did/')
		if response.status_code == 200 :
			on_line_check = "True"
		else :
			on_line_check = "False"
		my_kbis = """<b>Contact</b> : """ + issuer_explore.personal['contact_email']['claim_value'] + """ <br>
				<b>Visual check</b> : <a class = "card-link" href=/call_did/?website=""" + issuer_explore.personal['website']['claim_value'] + """>""" + issuer_explore.personal['website']['claim_value'] + """</a><br>
				<b>On-Line check</b> : """ + on_line_check

		for kbis in issuer_explore.kbis :
			my_kbis = my_kbis + "<hr><b>Certificate issued by Talao</b><br><br>"
			kbis_html = """
				<b>Name</b> : """+ kbis['name'] +"""<br>
				<b>Siret</b> : """+ kbis['siret'] +"""<br>
				<b>Creation</b> : """+ kbis['date'] + """<br>
				<b>Capital</b> : """+ kbis['capital']+"""<br>
				<b>Address</b> : """+ kbis['address']+"""<br>
				<p>
					<a class="text-secondary" href=/certificate/data/?dataId="""+ kbis['id'] + """:kbis>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""
			my_kbis = my_kbis + kbis_html

		# personal
		issuer_username =	 ns.get_username_from_resolver(issuer_workspace_contract, mode)
		issuer_username = 'Unknown' if issuer_username is None else issuer_username
		issuer_personal = """ <span><b>Username</b> : """ + issuer_username	+ """<br>"""
		for topic_name in issuer_explore.personal.keys() :
			if issuer_explore.personal[topic_name]['claim_value'] is not None :
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:] + ':claim:' + issuer_explore.personal[topic_name]['claim_id']
				issuer_personal = issuer_personal + """
				<span><b>"""+ topic_name +"""</b> : """+ issuer_explore.personal[topic_name]['claim_value']+"""
					<a class="text-secondary" href=/certificate/data/?dataId=""" + topicname_id + """:personal>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
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



#@app.route('/certificate/data/', methods=['GET'])
def certificate_data(mode) :

	menu = session.get('menu', dict())
	viewer = 'guest' if session.get('username') is None else 'user'
	dataId = request.args['dataId']
	workspace_contract = '0x' + dataId.split(':')[3]
	support = dataId.split(':')[4]
	if support == 'document' :
		doc_id = int(dataId.split(':')[5])
		my_topic = dataId.split(':')[6]
		if my_topic in [ 'experience', 'certificate', 'kbis', 'kyc', 'education', 'skills'] :
			my_data = Document(my_topic)
			my_data.relay_get(workspace_contract, doc_id, mode)
		else :
			print('Error data in webserver.py, Class instance needed')
			content = json.dumps({'topic' : 'error', 'msg' : 'Data Not Found'})
			response = Response(content, status=406, mimetype='application/json')
			return response
		expires = my_data.expires
		my_topic = my_data.topic.capitalize()

	# certificate are seen as guest always (no access to private data)
	if support == 'claim' :
		claim_id = dataId.split(':')[5]
		my_data = Claim()
		my_data.get_by_id(None, None, workspace_contract, claim_id, mode)
		expires = 'Unlimited'
		my_topic = 'Personal'
	myvisibility = my_data.privacy
	#issuer_is_white = False

	# issuer
	issuer_name = my_data.issuer['name'] if my_data.issuer['category'] == 2001 else my_data.issuer['firstname'] + ' ' +my_data.issuer['lastname']
	issuer_username = ns.get_username_from_resolver(my_data.issuer['workspace_contract'], mode)
	issuer_username = 'Unknown' if issuer_username is None else issuer_username
	issuer_type = 'Company' if my_data.issuer['category'] == 2001 else 'Person'

	if my_data.issuer['workspace_contract'] == workspace_contract or my_data.issuer['workspace_contract'] == mode.relay_workspace_contract :
		front =  """
				 <a class="text-warning">Self Declaration</a>
				</span>"""
	else :
		front =  """
					<a class="text-secondary" href=/certificate/issuer_explore/?workspace_contract="""+ my_data.issuer['workspace_contract'] + """ >
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a><br>
				</span>"""

	myissuer = """
				<span>
				<b>Issuer</b>""" + front + """
				<li><b>Name</b> : """ + issuer_name + """<br></li>
				<li><b>Username</b> : """ + issuer_username +"""<br></li>
				<li><b>Type</b> : """ + issuer_type + """<br></li>"""

	# advanced """
	(location, link) = (my_data.data_location, my_data.data_location)
	path = """https://rinkeby.etherscan.io/tx/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/tx/"""
	if support == 'document' :
		myadvanced = """
				<b>Advanced</b>
				<li><b>Document Id</b> : """ + str(doc_id) + """<br></li>
				<li><b>Privacy</b> : """ + myvisibility + """<br></li>
				<li><b>Created</b> : """ + my_data.created + """<br></li>
				<li><b>Expires</b> : """ + expires + """<br></li>
				<li><b>Transaction Hash</b> : <a class = "card-link" href = """ + path + my_data.transaction_hash + """>"""+ my_data.transaction_hash + """</a><br></li>
				<li><b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a></li>"""
	else :
		(location, link) = (mode.BLOCKCHAIN, "") if myvisibility == 'public' else (my_data.data_location, my_data.data_location)
		path = """https://rinkeby.etherscan.io/tx/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/tx/"""
		myadvanced = """
				<b>Advanced</b>
				<li><b>Claim Id</b> : """ + str(claim_id) + """<br></li>
				<li><b>Topic</b> : """ + str(my_data.topicname) + """<br></li>
				<li><b>Privacy</b> : """ + myvisibility + """<br></li>
				<li><b>Created</b> : """ + my_data.created + """<br></li>
				<li><b>Expires</b> : """ + expires + """<br></li>
				<li><b>Transaction Hash</b> : <a class = "card-link" href = """ + path + my_data.transaction_hash + """>"""+ my_data.transaction_hash + """</a><br></li>
				<li><b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a></li>"""

	# value
	if my_topic.lower() == "experience"  :
		myvalue = """
				<b>Data Content</b>
				<li><b>Title</b> : """+my_data.title + """<br></li>
				<li><b>Company Name</b> : """+my_data.company['name']+"""<br></li>
				<li><b>Contact Name</b> : """+my_data.company['contact_name']+"""<br></li>
				<li><b>Contact Email</b> : """+my_data.company['contact_email']+"""<br></li>
				<li><b>Contact Phone</b> : """+my_data.company['contact_phone']+"""<br></li>
				<li><b>Start Date</b> : """+my_data.start_date + """<br></li>
				<li><b>End Date</b> : """+my_data.end_date+"""<br></li>
				<li><b>Skills</b> : """+ " ".join(my_data.skills)+"""</li>"""

	elif my_topic.lower() == "education" :
		myvalue = """
				<b>Data Content</b>
				<li><b>Title</b> : """+my_data.title + """<br>
				<li><b>Organization Name</b> : """+my_data.organization['name']+"""<br></li>
				<li><b>Contact Name</b> : """+my_data.organization['contact_name']+"""<br></li>
				<li><b>Contact Email</b> : """+my_data.organization['contact_email']+"""<br></li>
				<li><b>Contact Phone</b> : """+my_data.organization['contact_phone']+"""<br></li>
				<li><b>Start Date</b> : """+my_data.start_date + """<br></li>
				<li><b>End Date</b> : """+my_data.end_date+"""<br></li>
				<li><b>Skills</b> : """+ " ".join(my_data.skills) +"""<br></li>
				<li><b>Diploma Link</b> : """+  my_data.certificate_link+"""</li>"""

	elif my_topic.lower() == "certificate" :
		if my_data.type == 'experience' :
			myvalue = """
				<b>Data Content</b>
				<li><b>Title</b> : """ + my_data.title + """<br></li>
				<li><b>Start Date</b> : """+ my_data.start_date + """<br></li>
				<li><b>End Date</b> : """+ my_data.end_date + """<br></li>
				<li><b>Skills</b> : """+ "".join(my_data.skills) + """<br></li>
				<li><b>Delivery Quality</b> : """+ my_data.score_delivery + """<br></li>
				<li><b>Schedule Respect</b> : """+ my_data.score_schedule + """<br></li>
				<li><b>Communication Skill</b> : """+ my_data.score_communication + """<br></li>
				<li><b>Recommendation</b> : """+ my_data.score_recommendation + """<br></li>"""
				#<li><b>Manager</b> : """+ my_data.manager+"""</li>"""
		elif my_data.type == 'recommendation' :
			myvalue = """
				<b>Data Content</b>
				<li><b>Descrition</b> : """ + my_data.description + """<br></li>
				<li><b>Relationship</b> : """+ my_data.relationship + """<br></li>"""
		else :
			myvalue = """
				<b>Data Content</b>
				<li><b>Title</b> : """ + my_data.title + """<br></li>
				<li><b>Issued Date</b> : """+ my_data.end_date + """<br></li>
				<li><b>Skills</b> : """ + my_data.description  + """<br></li>"""


	elif my_topic.lower() == "kbis" :
		myvalue = """
				<b>Data Content</b>
				<li><b>Name</b> : """ + my_data.name+ """<br></li>
				<li><b>Siret</b> : """ + my_data.siret + """<br></li>
				<li><b>Created</b> : """+ my_data.date + """<br></li>
				<li><b>Address</b> : """+ my_data.address + """<br></li>
				<li><b>Legal Form</b> : """+ my_data.legal_form + """<br></li>
				<li><b>Capital</b> : """+ my_data.capital + """<br></li>
				<li><b>Naf</b> : """+ my_data.naf + """<br></li>
				<li><b>Activity</b> : """+ my_data.activity+"""</li>"""



	elif my_topic.lower() == "kyc" :
		myvalue = """
				<b>Data Content</b>
				<li><b>Firstname</b> : """+ my_data.firstname + """<br></li>
				<li><b>Lastname</b> : """ + my_data.lastname + """<br></li>
				<li><b>Sex</b> : """+ my_data.sex + """<br></li>
				<li><b>Nationality</b> : """+ my_data.nationality + """<br></li>
				<li><b>Birth Date</b> : """+ my_data.birthdate + """<br></li>
				<li><b>Date of Issue</b> : """+ my_data.date_of_issue + """<br></li>
				<li><b>Date of Expiration</b> : """+ my_data.date_of_expiration + """<br></li>
				<li><b>Authority</b> : """+ my_data.authority + """<br></li>
				<li><b>Country</b> : """+ my_data.country+"""</li>"""

	elif my_topic.lower() == 'personal' :
		myvalue = """<b>Data</b> : """+ my_data.claim_value

	elif my_topic.lower() == 'skills' :
		myvalue = ''
		for skill in my_data.description :
			skill_to_display = skill['skill_name'].capitalize()
			myvalue = myvalue + """<li>  """+ skill_to_display + """</li>"""

	else :
		print(('topic not found'))
		content = json.dumps({'topic' : 'error', 'msg' : 'Data Not Found'})
		response = Response(content, status=406, mimetype='application/json')
		return response

	#mydelete_link = "/talao/api/data/delete/"

	my_verif = "<hr>" + myvalue + "<hr>" + myissuer +"<hr>" + myadvanced

	return render_template('./certificate/certificate_data_check.html',
							**menu,
							verif=my_verif,
							viewer=viewer,
							)

# Analysis
#@app.route('/certificate/data_analysis/', methods=['GET'])
def certificate_data_analysis(mode) :

	viewer = 'guest' if session.get('username') is None else 'user'

	certificate_id = session['certificate_id']
	identity_workspace_contract = '0x' + certificate_id.split(':')[3]
	if request.method == 'GET' :
		my_analysis = analysis.dashboard(identity_workspace_contract, session['resume'], mode)

		return render_template('dashboard.html',
								viewer= viewer,
								**my_analysis)
