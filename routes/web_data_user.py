"""
Identity init for users and companies
"""
from flask import session, flash
from flask import request, redirect, render_template, abort, flash, Response
import time
import json
from flask_babel import _
import requests
import didkit
import logging
from flask_babel import _
logging.basicConfig(level=logging.INFO)
from os import path
from authlib.jose import JsonWebEncryption
from datetime import timedelta, datetime


# dependances
from components import ns,directory, company, privatekey
from protocol import Identity, Document
from signaturesuite import helpers

COMPANY_TOPIC = ['name','contact_name','contact_email', 'contact_phone', 'website', 'about', 'staff', 'sales', 'mother_company', 'siren', 'postal_address']


def init_app(app, mode) :
	app.add_url_rule('/user/',  view_func=user, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/data/',  view_func=data, methods = ['GET'], defaults={'mode': mode})
	app.add_url_rule('/user/advanced/',  view_func=user_advanced, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/user/account/',  view_func=user_account, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/company/',  view_func=the_company, methods = ['GET', 'POST'])
	app.add_url_rule('/text_file',  view_func=text_file, methods = ['GET'])
	app.add_url_rule('/user/import_identity_key/',  view_func=import_identity_key, methods = ['GET', 'POST'], defaults={'mode': mode})
	app.add_url_rule('/user/import_identity_key2/',  view_func=import_identity_key, methods = ['GET', 'POST'], defaults={'mode': mode})
	return


def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if not session.get('workspace_contract') and not session.get('username') :
		abort(403)
	else :
		return True


def the_company() :
	""" mentions legales
	@app.route('/company')
	"""
	return render_template('company.html')


def text_file() :
	if request.args['file'] == 'privacy' :
		content = open('privacy_en.txt', 'r').read() if session['language'] == 'en' else open('privacy_fr.txt', 'r').read()
	elif request.args['file'] == 'terms_and_conditions' :
		content = open('cgu_en.txt', 'r').read() if session['language'] == 'en' else open('cgu_fr.txt', 'r').read()
	return Response(content, mimetype='text/plain')


def import_identity_key(mode) :
	if request.method == 'GET' :
		return render_template ('import_identity_key.html', **session['menu'])
	session['check_identity_key'] = True
	return redirect (mode.server + 'user/')


def data(mode) :
	"""
	#@app.route('/data/', methods=['GET'])
	"""
	check_login()
	try :
		dataId = request.args['dataId']
		workspace_contract = '0x' + dataId.split(':')[3]
	except :
		logging.error('data request malformed')
		return redirect(mode.server + 'user/')

	doc_id = int(dataId.split(':')[5])
	my_data = Document(dataId.split(':')[6])
	if not my_data.relay_get(workspace_contract, doc_id, mode) :
		logging.error('document does not exist')
		return redirect(mode.server + 'user/')

	# advanced information about storage location
	(location, link) = (my_data.data_location, my_data.data_location)
	myadvanced = """<b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a>"""

	# Display raw verifiable credential
	credential = Document('certificate')
	credential.relay_get_credential(session['workspace_contract'], doc_id, mode)
	return render_template('data_check.html',
							**session['menu'],
							verif=myadvanced,
							credential=json.dumps(credential.__dict__, sort_keys=True, indent=4, ensure_ascii=False),
							id=credential.__dict__['id'])


def user(mode) :
	"""
	#@app.route('/user/', methods = ['GET'])
	Main view for Identity Repository
	We setup Ientity with workspace or username depending of the login method
	"""
	#check_login()

	if request.args.get('flash_message') == "credential_offered" :
		flash(_('Your credential has been saved in your wallet'), 'success')
	if request.args.get('flash_message') == "credential_refused" :
		flash(_('Your cannot download this credential'), 'warning')
	
	if not session.get('uploaded') :
		logging.info('start first instanciation')
		# for wallet direct access
		issuer_username = None
		vc= None
		if session.get('username') :
			logging.info('Identity set up from username')
			data_from_username = ns.get_data_from_username(session['username'], mode)
			session['workspace_contract'] = data_from_username['workspace_contract']
		elif session.get('workspace_contract') :
			logging.info('Identity set up from workspace contract')
			session['username'] = ns.get_username_from_resolver(session['workspace_contract'], mode)
		elif request.form.get('token') :
			logging.info('Identity set up from token')
			print("token = ",request.form.get('token'))
			token = request.form.get('token')
			key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
			jwe = JsonWebEncryption()
			try :
				data = jwe.deserialize_compact(token, key)
			except :
				flash (_('Incorrect data.'), 'danger')
				logging.warning('JWE did not decrypt')
				return render_template('./login/login_password.html')
			payload = json.loads(data['payload'].decode('utf-8'))
			print('payload = ', payload)
			if payload['exp'] < datetime.timestamp(datetime.now()) :
				flash (_('Delay expired !'), 'danger')
				return render_template('./login/login_password.html')
			# wallet direct call to issuer explore
			did = payload['did']
			issuer_username = payload['issuer_username']
			vc = payload['vc']
			session['workspace_contract'] = ns.get_workspace_contract_from_did(did, mode)
			session['username'] = ns.get_username_from_resolver(session['workspace_contract'], mode)
		else :
			abort(403)

		if mode.test :
			user = Identity(session['workspace_contract'], mode, authenticated=True)
		else :
			try :
				user = Identity(session['workspace_contract'], mode, authenticated=True)
			except :
				logging.error('cannot init Identity')
				flash(_('session aborted'), 'warning')
				return render_template('login.html')
		logging.info('end of first intanciation')

		# init session side by redis
		session['uploaded'] = True
		session['type'] = user.type
		session['address'] = user.address
		session['workspace_contract'] = user.workspace_contract
		session['issuer'] = user.issuer_keys
		session['partner'] = user.partners
		session['did'] = user.did
		session['eth'] = user.eth
		session['token'] = user.token
		session['rsa_key'] = user.rsa_key
		session['rsa_key_value'] = user.rsa_key_value
		session['rsa_filename'] =  session['did'] + ".pem"
		session['private_key'] = user.private_key
		session['private_key_value'] = user.private_key_value
		session['relay_activated'] = user.relay_activated
		session['personal'] = user.personal
		session['identity_file'] = user.identity_file
		session['name'] = user.name
		session['secret'] = user.secret
		session['picture'] = user.picture
		session['signature'] = user.signature
		session['skills'] = user.skills
		session['certificate'] = user.certificate
		session['private_certificate'] = user.private_certificate
		session['secret_certificate'] = user.secret_certificate
		session['all_certificate'] = user.certificate + user.private_certificate + user.secret_certificate
		session['has_vault_access'] = user.has_vault_access
		session['method'] = ns.get_method(session['workspace_contract'], mode)
		session['mode_server'] = mode.server
		if not session['method'] :
			session['method'] = "ethr"
		phone =  ns.get_data_from_username(session.get('username'), mode).get('phone')
		session['phone'] = phone if phone else ""

		if user.type == 'person' :
			session['profil_title'] = user.profil_title
			session['experience'] = user.experience
			session['education'] = user.education
			# no credential workflow
			session['host'] = session['employee'] = None
			session['role'] = session['referent'] = None
			clipboard = mode.server  + "resume/?did=" + session['did']

			session['check_identity_key'] = False

		if session['type'] == 'company' :
			session['profil_title'] = ""
			# data for credential workflow for admin, issuer or reviewer
			try :
				session['host'] = session['username'].split('.')[1]
				session['employee'] = session['username'].split('.')[0]
				session['role'] =  ns.get_data_from_username(session['username'], mode)['role']
				session['referent'] =  ns.get_data_from_username(session['username'], mode)['referent']
			# for creator
			except :
				session['host'] = session['username']
				session['employee'] = None
				session['role'] = 'creator'
				session['referent'] = None
			clipboard = mode.server  + "board/?did=" + session['did']

		# for nav bar menu display
		session['menu'] = {'picturefile' : mode.ipfs_gateway + session['picture'],
							'username' : session.get('username', ""),
							'name' : session['name'],
							#'private_key_value' : user.private_key_value,
							'rsa_filename': session['rsa_filename'],
							'profil_title' : session['profil_title'],
							'clipboard' : clipboard}
		
		# Dashboard start for employees
		if session['role'] in ['issuer', 'reviewer'] :
			return redirect (mode.server + 'company/dashboard/')

		# wallet direct call redirect 
		if issuer_username :
			issuer_workspace_contract = ns.get_data_from_username(issuer_username, mode)['workspace_contract']
			session['issuer_explore'] = Identity(issuer_workspace_contract, mode, authenticated=True,).__dict__.copy()
			session['issuer_username'] = issuer_username
			session['issuer_explore']['method'] = ns.get_method(session['issuer_explore']['workspace_contract'], mode)
			session['credential_issuer_username'] = issuer_username
			session['reference'] = 'wallet'
			if vc == 'professionalexperienceassessment':	
				# get reviewers available
				select = ""
				reviewer = company.Employee(issuer_username, mode) 
				reviewer_list = reviewer.get_list('reviewer', 'all')
				for reviewer in reviewer_list :
					session['select'] = select + """<option value=""" + reviewer['username'].split('.')[0]  + """>""" + reviewer['username'].split('.')[0] + """</option>"""
				return render_template('./issuer/request_experience_credential.html', **session['menu'], select=session['select'])
			if vc == 'certificateofemployment' :
				return render_template('./issuer/request_work_credential.html', **session['menu'])
			if vc == 'identitypass' :
				return redirect (mode.server + 'user/request_pass_credential')
			if not vc :
				return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + issuer_username)	

		# Homepage start for Talent
		#if user.type == 'person' :
		#	return render_template('homepage.html', **session['menu'])

		# check Identity key Pair for person only client side
		# Keypairs for companies are setpu server side
		if not ns.get_did(session['workspace_contract'], mode) and session['type'] == 'person' :
			return redirect (mode.server + 'user/generate_identity/')

	else :
		session['check_identity_key'] = True

	# Partners
	if not session['partner'] :
		my_partner = """<a class="text-info">No Partners available</a>"""
	else :
		my_partner = ""
		for partner in session['partner'] :
			if partner['authorized'] == 'Pending' :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner['username'] + """">"""+ partner['username'] + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
					<a class="text-secondary" href="/user/reject_partner/?partner_username=""" + partner['username'] +"""&amp;partner_workspace_contract=""" + partner['workspace_contract']+"""">
						<i data-toggle="tooltip" class="fa fa-thumbs-o-down" title="Reject this Partnership.">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/authorize_partner/?partner_username=""" + partner['username'] + """&amp;partner_workspace_contract=""" + partner['workspace_contract']+ """">
						<i data-toggle="tooltip" class="fa fa-thumbs-o-up" title="Authorize this Parnership."></i>
					</a>
				</spn>"""
			elif partner['authorized'] == 'Removed' :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner['username'] + """">"""+ partner['username'] + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
				</spn>"""
			else :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner['username'] + """">"""+ partner['username'] + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
					<a class="text-secondary" href="/user/remove_partner/?partner_username=""" + partner['username'] +"""&amp;partner_workspace_contract=""" + partner['workspace_contract']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove this Partnership.">&nbsp&nbsp&nbsp</i>
				</spn>"""
			my_partner = my_partner + partner_html + """<br>"""

	# Issuer for document, they have an ERC725 key 20002
	if not session['issuer']  :
		my_issuer = """  <a class="text-info">""" + _('No Referents available') + """</a>"""
	else :
		my_issuer = ""
		for one_issuer in session['issuer'] :
			issuer_username = ns.get_username_from_resolver(one_issuer['workspace_contract'], mode)
			issuer_username = 'Unknown' if issuer_username is None else issuer_username
			issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_issuer/?issuer_username="""+ issuer_username +"""&amp;issuer_address=""" + one_issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span>"""
			my_issuer = my_issuer + issuer_html + """<br>"""

	# files
	if not session['identity_file'] :
		my_file = """<a class="text-info">""" + _('No Files available') + """</a>"""
	else :
		my_file = ""
		for one_file in session['identity_file'] :
			file_html = """
				<b>File Name</b> : """+one_file['filename']+ """ ( """+ one_file['privacy'] + """ ) <br>
				<b>Created</b> : """+ one_file['created'] + """<br>
				<p>
					<a class="text-secondary" href="/user/remove_file/?file_id=""" + one_file['id'] + """&filename="""+one_file['filename'] +"""">
						<i data-toggle="tooltip" class="far fa-trash-alt" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>

					<a class="text-secondary" href=/user/download/?filename=""" + one_file['filename'] + """>
						<i data-toggle="tooltip" class="fa fa-download" title="Download"></i>
					</a>
				</p>"""
			my_file = my_file + file_html

	# skills
	if not session['skills'] or not session['skills'].get('id') :
		my_skills =  """<a class="text-info">""" + _('No data available') + """</a>"""
	else :
		my_skills = ""
		for skill in session['skills']['description'] :
			skill_html = skill['skill_name'] + """ (""" + skill['skill_level'] + """)""" + """<br>"""
			my_skills = my_skills + skill_html
		my_skills = my_skills + """
				<p>
				</p>"""


	# specific to person
	if session['type'] == 'person' :
		# experience
		my_experience = ""
		if not session['experience'] :
			my_experience = my_experience + """<a class="text-info">""" + _('No Experience available') + """</a>"""
		else :
			for experience in sorted(session['experience'], key= lambda d: time.strptime(d['start_date'], "%Y-%m-%d"), reverse=True) :
				if not experience['end_date'] :
					end_date = "Current"
				else :
					end_date = experience['end_date']
				exp_html = """
				<b>""" + _('Company') + """</b> : """ + experience['company']['name'] + """<br>
				<b>""" + _('Title') + """</b> : """ + experience['title'] + """<br>
				<b>""" + _('Start Date') + """</b> : """ + experience['start_date'] + """<br>
					<b>""" + _('End Date') + """</b> : """ + end_date + """<br>
				<b>""" + _('Description') + """</b> : """ + experience['description'][:100] + """...<br>
				<p>
					<a class="text-secondary" href="/user/remove_experience?experience_id=""" + experience['id'] + """">
						<i data-toggle="tooltip" class="far fa-trash-alt" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
				</p>"""
				my_experience = my_experience + exp_html + "<hr>"

		# education
		my_education = ""
		if not session['education'] :
			my_education = my_education + """<a class="text-info">""" + _('No Education available') + """</a>"""
		else :
			for education in session['education'] :
				edu_html = """
				<b>""" + _('Organization') + """</b> : """+education['organization']['name']+"""<br>
				<b>""" + _('Title') + """</b> : """+education['title'] + """<br>
				<b>""" + _('Start Date') + """</b> : """+education['start_date']+"""<br>
				<b>""" + _('End Date') + """</b> : """+education['end_date']+"""<br>
				<p>
					<a class="text-secondary" href="/user/remove_education?education_id=""" + education['id'] + """">
						<i data-toggle="tooltip" class="far fa-trash-alt" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
				</p>"""
				my_education = my_education + edu_html	+ "<hr>"

		# personal
		TOPIC = {'firstname' : _('Firstname'),
				'lastname' : _('Lastname'),
				'about' : _('About'),
				'profil_title' : _('Title'),
				'birthdate' : _('Birth Date'),
				'contact_email' : _('Contact Email'),
				'contact_phone' : _('Contact Phone'),
				'postal_address' : _('Postal Address'),
				'education' : _('Education')}
		my_personal = ""
		for topicname in TOPIC.keys() :
			if session['personal'][topicname].get('claim_value') :
				text = session['personal'][topicname]['claim_value'] + ' (' + session['personal'][topicname]['privacy'] + ')'
				my_personal += """<b>""" + TOPIC[topicname] + """</b> : """+ text + """<br>"""

		# Alias
		if session['username'] != ns.get_username_from_resolver(session['workspace_contract'], mode) :
			display_alias = False
			my_access = ""
		else :
			display_alias = True
			my_access = ""
			access_list = ns.get_alias_list(session['workspace_contract'], mode)
			for access in access_list :
				if access['username'] == session['username'] :
					access_html = """
					<span>""" + session['username'] + """ (logged)
					</span>"""
				else :
					access_html = """
					<span>""" + access['username'] + """ : """ +  access['email'] +"""
						<a class="text-secondary" href="/user/remove_access/?alias_to_remove="""+ access['username']+"""">
							<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">	</i>
						</a>
					</span>"""
				my_access +=  access_html + """<br>"""

		# credentials/certificates
		credential_text = {'IdentityPass' : _('Identity pass'),
                'ProfessionalExperienceAssessment' : _('Professional experience assessment'),
                'skill' : _('Skill certificate'),
                'training' : _('Training certificate'),
                'recommendation' : _('Recommendation letter'),
                'CertificateOfEmployment' : _('Certificate of employment'),
                'vacation' : _('Employee vacation time certificate'),
                'internship' : _('Certificate of participation'),
                'relocation' : _('Transfer certificate'),
                'hiring' : _('Promise to hire letter')}
		#privacy_visibility_text = {'public' : _('Public'), 'private' : _('Private'), 'secret' : _('Secret')}
		my_certificates = ""
		if not session['all_certificate'] :
			my_certificates = my_certificates + """<a class="text-info">""" + _('No Credential available') + """</a>"""
		else :
			for counter, certificate in enumerate(session['all_certificate'],1) :
				try : 
					cert_html = """<hr>
						<b>""" + _('Credential Type') + """</b> : """ + credential_text.get(certificate['credentialSubject']['type'], "Not supported") + """<br>
						<b>""" + _('Credential Privacy') + """</b> : """ + certificate['privacy'] + """<br>
						<b>""" + _('Issuer DID') + """</b> : """ + certificate['issuer'] +"""<br>
						<b>""" + _('Issuance Date') + """</b> : """ + certificate['proof']['created'] + """<br>"""
					# FIXME
					credential = Document('certificate')
					credential.relay_get_credential(session['workspace_contract'], int(certificate['doc_id']), mode)
					filepath = './signed_credentials/' + credential.id + ".jsonld"
					if not path.exists(filepath) :
						outfile = open(filepath, 'w')
						json.dump(credential.__dict__, outfile, indent=4, ensure_ascii=False)	
					credential_id = credential.id
				except :
					print('certificat rejeté = ', certificate)
					cert_html = """<hr>
					<b>#</b> : """ + str(counter) + "<br>"
					id = ""
					credential_id = ""
				
				cert_html += """<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """>""" + _('Display Credential') + """</a><br>"""
				
				cert_html += """<b></b><a href= """ + mode.server +  """credible/credentialOffer/""" + credential_id + """>""" + _('Download to your smartphone wallet') + """</a><br>"""				
				cert_html += """<p>
					<a class="text-secondary" href="/user/remove_certificate/?certificate_id=""" + certificate['id'] + """">
					<i data-toggle="tooltip" class="far fa-trash-alt" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>

					<a class="text-secondary" href=/data/?dataId=""" + certificate['id'] + """:certificate>
					<i data-toggle="tooltip" class="fa fa-search-plus" title="Credential data">&nbsp&nbsp&nbsp</i>
					</a>"""

			
				cert_html += """<a class="text-secondary" onclick="copyToClipboard('#p"""+ str(counter) + """')">
					<i data-toggle="tooltip" class="fa fa-clipboard" title="Copy Credential Link">&nbsp&nbsp&nbsp</i>
					</a>"""

				cert_html += """<a class="text-secondary" href=/user/swap_privacy/?certificate_id=""" + certificate['id'] + """&privacy=""" + certificate['privacy'] +  """>
					<i data-toggle="tooltip" title="Change privacy" class="fas fa-redo" >&nbsp&nbsp&nbsp</i>
					</a>

					</p>
					<p hidden id="p""" + str(counter) + """" >""" + mode.server  + """guest/certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """</p>"""
				my_certificates += cert_html

		return render_template('person_identity.html',
							**session['menu'],
							display_alias = display_alias,
							personal=my_personal,
							experience=my_experience,
							education=my_education,
							skills=my_skills,
							certificates=my_certificates,
							access=my_access,
							partner=my_partner,
							issuer=my_issuer,
							digitalvault= my_file,
							nb_certificates=len(session['all_certificate'])
							)
	# specific to company
	if session['type'] == 'company' :

		# init employee table
		employee = company.Employee(session['host'], mode)

		# Admin list  and add admin
		my_admin_start = """<a href="/company/add_employee/?role_to_add=admin">""" + _('Add an Admin') + """</a><hr> """
		my_admins = ""
		admin_list = employee.get_list('admin', 'all')
		for admin in admin_list :
			admin_html = """
				<span>""" + admin['username'] + """ => """ +  admin['identity_name'] +"""
				<a class="text-secondary" href="/company/remove_access?employee_to_remove="""+ admin['username']+"""">
					<i data-toggle="tooltip" class="fas fa-trash-alt" title="Remove">	</i>
				</a>
				</span>"""
			my_admins +=  admin_html + """<br>"""
		my_admins = my_admin_start + my_admins

		# Issuer list and add issuer within a company
		my_managers_start = """<a href="/company/add_employee/?role_to_add=issuer">""" + _('Add an Issuer') + """</a><hr> """
		my_managers = ""
		manager_list = employee.get_list('issuer', 'all')
		for manager in manager_list :
			manager_html = """
				<span>""" + manager['username'] + """ => """ +  manager['identity_name'] +"""
				<a class="text-secondary" href="/company/remove_access?employee_to_remove="""+ manager['username']+"""">
					<i data-toggle="tooltip" class="fas fa-trash-alt" title="Remove">	</i>
				</a>
				</span>"""
			my_managers += manager_html + """<br>"""
		my_managers = my_managers_start + my_managers

		# Reviewer list and add reviewers
		my_reviewers_start = """<a href="/company/add_employee/?role_to_add=reviewer">""" + _('Add a Reviewer') + """</a><hr> """
		my_reviewers = ""
		reviewer_list = employee.get_list('reviewer', 'all')
		for reviewer in reviewer_list :
			reviewer_html = """
				<span>""" + reviewer['username'] + """ => """ +  reviewer['identity_name'] +"""
				<a class="text-secondary" href="/company/remove_access?employee_to_remove="""+ reviewer['username']+"""">
					<i data-toggle="tooltip" class="fas fa-trash-alt" title="Remove">	</i>
				</a>
				</span>"""
			my_reviewers += reviewer_html + """<br>"""
		my_reviewers = my_reviewers_start + my_reviewers

		# Company campaigns
		if session['role'] not in ['issuer', 'reviewer'] :
			my_campaign = """<a href="/company/add_campaign/">""" + _('Add a Campaign') + """</a><hr> """
		else :
			my_campaign = ""
		campaign = company.Campaign(session['host'], mode)
		campaign_list = campaign.get_list()
		if campaign_list :
			for camp in campaign_list :
				try :
					description = json.loads(camp['description'])['description']
				except :
					description = camp.get('description', 'unkown')
				campaign_html = camp.get('campaign_name', 'unknown') + """ : """ +  description[:100]
				remove_option = """...
				<a class="text-secondary" href="/company/remove_campaign/?campaign_name="""+ camp.get('campaign_name', 'unkown') + """">
					<i data-toggle="tooltip" class="fas fa-trash-alt" title="Remove">	</i>
				</a>"""
				if session['role'] not in ['issuer', 'reviewer'] :
					campaign_html += remove_option
				my_campaign += campaign_html + "<hr>"

		# company settings
		if session['role'] in ['creator', 'admin'] :
			my_personal = """<a href="/user/picture/">""" + _('Change Logo') + """</a><br>
						<a href="/user/signature/">""" + _('Change Signature') + """</a><br>"""
		else :
			my_personal = ""

		TOPIC = {'name' : _('Company name'),
				'contact_name' : _('Contact name'),
				'website' : _('website'),
				'siren' : _('SIREN'),
				'about' : _('About'),
				'contact_email' : _('Contact Email'),
				'contact_phone' : _('Contact Phone'),
				'postal_address' : _('Postal Address'),
				'mother_company' : _('Mother company'),
				'staff' : _('Staff'),
				'sales' : _('Sales')}
		for topicname in TOPIC.keys() :
			if session['personal'][topicname].get('claim_value') :
				text = session['personal'][topicname]['claim_value'] + ' (' + session['personal'][topicname]['privacy'] + ')'
				my_personal += """<b>""" + TOPIC[topicname] + """</b> : """+ text + """<br>"""

		if session['role'] in ['creator', 'admin'] :
			my_personal = my_personal + """<a href="/user/update_company_settings/">""" + _('Update Company Data') + """</a>"""

		# credentials
		if  not session['all_certificate'] :
			my_certificates =  """<a class="text-info">""" + _('No Credentials available') + """</a>"""
		else :
			my_certificates = """<div  style="height:300px;overflow:auto;overflow-x: hidden;">"""
			for counter, certificate in enumerate(session['all_certificate'],1) :
				if '@context' in certificate :
					if  certificate['credentialSubject']['credentialCategory'] ==  "reference" :
						cert_html = """<hr>
								<b>""" + _('Issuer Name') + """</b> : """ + certificate['credentialSubject']['companyName'] + """<br>
								<b>""" + _('Credential Type') + """</b> : """ + certificate['credentialSubject']['credentialCategory'].capitalize() + """<br>
								<b>""" + _('Title') + """</b> : """ + certificate['credentialSubject']['offers']['title'] + """<br>
								<b>""" + _('Description') + """</b> : """ + certificate['credentialSubject']['offers']['description']+ """<br>
								<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """>""" + _('Display Certificate') + """</a><br>
								<p>
								<a class="text-secondary" href="/user/remove_certificate/?certificate_id=""" + certificate['id'] + """">
								<i data-toggle="tooltip" class="far fa-trash-alt" title="Remove">&nbsp&nbsp&nbsp</i>
								</a>

								<a class="text-secondary" href=/data/?dataId=""" + certificate['id'] + """:certificate>
								<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check">&nbsp&nbsp&nbsp</i>
								</a>

								<a class="text-secondary" onclick="copyToClipboard('#p"""+ str(counter) + """')">
								<i data-toggle="tooltip" class="fa fa-clipboard" title="Copy Certificate Link"></i>
								</a>
								</p>
								<p hidden id="p""" + str(counter) +"""" >""" + mode.server  + """guest/certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """</p>"""
				else :
					cert_html ="""<a class="text-secondary" href="/user/remove_certificate/?certificate_id=""" + certificate['id'] + """">
								<i data-toggle="tooltip" class="far fa-trash-alt" title="Remove">&nbsp&nbsp&nbsp</i>
								</a>

								<a class="text-secondary" href=/data/?dataId=""" + certificate['id'] + """:certificate>
								<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check">&nbsp&nbsp&nbsp</i>
								</a>"""
					logging.warning('incorrect certificate type')
				my_certificates = my_certificates + cert_html
			my_certificates = my_certificates + """</div>"""

		return render_template('company_identity.html',
							**session['menu'],
							admin=my_admins,
							manager=my_managers,
							reviewer=my_reviewers,
							personal=my_personal,
							issuer=my_issuer,
							certificates=my_certificates,
							company_campaign=my_campaign,
							digitalvault=my_file)


def user_advanced(mode) :
	check_login()

	# account
	my_account = ""
	if session['username'] == 'talao' :
		relay_eth = mode.w3.eth.getBalance(mode.relay_address)/1000000000000000000
		talaogen_eth = mode.w3.eth.getBalance(mode.Talaogen_public_key)/1000000000000000000
		my_account = my_account + """<br><br>
					<b>Relay ETH</b> : """ + str(relay_eth) + """<br>
					<b>Talao Gen ETH</b> : """ + str(talaogen_eth) + """<br>"""

	# API
	credentials = ns.get_credentials(session['username'], mode)
	if not credentials :
		my_api = """<a class="text-info">Contact relay@talao.io to get your API credentials.</a>"""
	else :
		my_api = """ <div style="height:200px;overflow:auto;overflow-x: hidden;">"""
		for cred in credentials :
			my_api = my_api + """
			<b>client_id</b> : """+ cred['client_id'] +"""<br>
			<b>client_secret</b> : """+ cred['client_secret'] + """<br>
			<b>client_uri</b> : """+ cred['client_uri'] + """<br>
			<b>redirect_uri</b> : """+ cred['redirect_uris'][0] + """<br>
			<b>scope</b> : """+ cred['scope'] + """<br>
			<b>grant_types</b> : """+ " ".join(cred['grant_types']) + """<br><hr> """
		my_api = my_api + """</div>"""

	# Alias
	if session['username'] != ns.get_username_from_resolver(session['workspace_contract'], mode) :
		my_access = ""
	else :
		my_access = ""
		access_list = ns.get_alias_list(session['workspace_contract'], mode)
		for access in access_list :
			if access['username'] == session['username'] :
				access_html = """
				<span>""" + session['username'] + """ (logged)
				</span>"""
			else :
				access_html = """
				<span>""" + access['username'] + """ : """ +  access['email'] +"""
						<a class="text-secondary" href="/user/remove_access/?username_to_remove="""+ access['username']+"""">
							<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">	</i>
						</a>
					</span>"""
			my_access = my_access + access_html + """<br>"""

	# DID and DID document
	print('did list = ', ns.get_did_list(session['workspace_contract'],mode))
	did = ns.get_did(session['workspace_contract'], mode)
	print('did = ', did)
	if not did :
		logging.warning('No DID available in local database')
		did = DID_Document = _("No DID available")
	else :
		if did.split(':')[1]  in ['tz', 'ethr', 'key'] :
			# did:tz has no driver for Universal resolver
			DID_Document = json.dumps(json.loads(didkit.resolveDID(did,'{}')), indent=4)
		else  :
			resolver = 'https://resolver.identity.foundation/'
			r = requests.get( resolver + did)
			if r.status_code == 200 :
				DID_Document = json.dumps(r.json(), indent=4)
			else :
				logging.warning('DID Document resolution has been rejected by Universal Resolver.')

	# Repository data
	role = session['role'] if session.get("role") else 'None'
	referent = session['referent'] if session.get('referent') else 'None'
	my_advanced = """
					<b>Portfolio smart contract</b> : """+ session['workspace_contract'] + """<br>
					<b>Portfolio controller</b> : """+ session['address'] + """<br>
					<b>DID</b> : """ + did + """<br>
					<b>All DID attached</b> : """ + "<br>".join(ns.get_did_list(session['workspace_contract'], mode)) + """<br>
					<hr>
					<b>Role</b> : """ + role + """<br>
					<b>Referent</b> : """ + referent + """<br>"""
	my_advanced = my_advanced  + my_account

	# Partners
	if session['partner'] == [] :
		my_partner = """<a class="text-info">""" +  _('No Partners available') + """</a>"""
	else :
		my_partner = ""
		for partner in session['partner'] :
			partner_username = partner['username']
			if partner['authorized'] == 'Pending' :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner_username + """">"""+ partner_username + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
					<a class="text-secondary" href="/user/reject_partner/?partner_username=""" + partner_username+"""&amp;partner_workspace_contract=""" + partner['workspace_contract']+"""">
						<i data-toggle="tooltip" class="fa fa-thumbs-o-down" title="Reject this Partnership.">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/authorize_partner/?partner_username=""" + partner_username + """&amp;partner_workspace_contract=""" + partner['workspace_contract']+ """">
						<i data-toggle="tooltip" class="fa fa-thumbs-o-up" title="Authorize this Parnership."></i>
					</a>
				</spn>"""
			elif partner['authorized'] == 'Removed' :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner_username + """">"""+ partner_username + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
				</spn>"""
			else :
				partner_html = """
				<span><a href="/user/issuer_explore/?issuer_username="""+ partner_username + """">"""+ partner_username + """</a>  (""" + partner['authorized'] + """ - """ +   partner['status'] +   """ )
					<a class="text-secondary" href="/user/remove_partner/?partner_username=""" + partner_username +"""&amp;partner_workspace_contract=""" + partner['workspace_contract']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove this Partnership.">&nbsp&nbsp&nbsp</i>
				</spn>"""
			my_partner = my_partner + partner_html + """<br>"""

	# Issuer for document, they have an ERC725 key 20002
	if session['issuer'] == [] :
		my_issuer = """  <a class="text-info">""" + _('No Referents available') + """</a>"""
	else :
		my_issuer = ""
		for one_issuer in session['issuer'] :
			issuer_username = ns.get_username_from_resolver(one_issuer['workspace_contract'], mode)
			issuer_username = 'Unknown' if not issuer_username else issuer_username
			issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_issuer/?issuer_username="""+issuer_username +"""&amp;issuer_address="""+one_issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span>"""
			my_issuer = my_issuer + issuer_html + """<br>"""

	return render_template('advanced.html',
							**session['menu'],
							access=my_access,
							private_key_value = helpers. ethereum_to_jwk256k(session['private_key_value']),
							partner=my_partner,
							issuer=my_issuer,
							did_doc=DID_Document,
							did=did,
							api=my_api,
							advanced=my_advanced)


# account settings
def user_account(mode) :
	check_login()
	if directory.search_user(mode, session):
		checkBox = "checked"
	else:
		checkBox = ""
	if request.args.get('success') == 'true' :
		if session['type'] == 'person' :
			flash(_('Picture has been updated'), 'success')
		else :
			flash(_('Logo has been updated'), 'success')
	return render_template('account.html',
							**session['menu'],
							checkBox = checkBox)
