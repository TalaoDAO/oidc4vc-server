"""
pour l authentication cf https://realpython.com/token-based-authentication-with-flask/
pour la validation du bearer token https://auth0.com/docs/quickstart/backend/python/01-authorization
interace wsgi https://www.bortzmeyer.org/wsgi.html
request : http://blog.luisrei.com/articles/flaskrest.html

"""
import os
from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
from flask_fontawesome import FontAwesome
from datetime import timedelta, datetime
import time
import json
import random
from Crypto.PublicKey import RSA
from authlib.jose import JsonWebEncryption
from urllib.parse import urlencode
from eth_account.messages import defunct_hash_message
import logging
logging.basicConfig(level=logging.INFO)

# dependances
from components import Talao_message, Talao_ipfs, hcode, ns, sms, directory, privatekey
import constante
from protocol import ownersToContracts, contractsToOwners, destroy_workspace, save_image, partnershiprequest, remove_partnership, token_balance
from protocol import Claim, File, Identity, Document, read_profil, get_data_from_token


def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if not session.get('workspace_contract') and not session.get('username') :
		abort(403)
	else :
		return True

# mentions legales
#@app.route('/company')
def company() :
	return render_template('company.html')

# protection des données personelles
#@app.route('/privacy')
def privacy() :
	return render_template('privacy.html')


def data(mode) :
	"""
	 on ne gere aucune information des data en session 
	#@app.route('/data/', methods=['GET'])
	"""
	check_login()
	try :
		dataId = request.args['dataId']
		workspace_contract = '0x' + dataId.split(':')[3]
		support = dataId.split(':')[4]
	except :
		logging.error('data request malformed')
		return redirect(mode.server + 'user/')

	if support == 'document' :
		doc_id = int(dataId.split(':')[5])
		my_topic = dataId.split(':')[6]
		my_data = Document(my_topic)
		if not my_data.relay_get(workspace_contract, doc_id, mode) :
			logging.error('document does not exist')
			return redirect(mode.server + 'user/')
		expires = my_data.expires
		my_topic = my_data.topic.capitalize()

	if support == 'claim' :
		claim_id = dataId.split(':')[5]
		my_data = Claim()
		if not my_data.get_by_id(session.get('workspace_contract'), session.get('private_key_value'), workspace_contract, claim_id, mode) :
			logging.error('claim does ot exist')
			return redirect(mode.server + 'user/')
		expires = 'Unlimited'
		my_topic = 'Personal'

	myvisibility = my_data.privacy

	# issuer
	issuer_username = ns.get_username_from_resolver(my_data.issuer['workspace_contract'], mode)
	issuer_username = 'Unknown' if not issuer_username  else issuer_username

	# advanced """
	(location, link) = (my_data.data_location, my_data.data_location)
	if mode.BLOCKCHAIN == 'rinkeby' :
		transaction_hash = """<a class = "card-link" href = https://rinkeby.etherscan.io/tx/ """ + my_data.transaction_hash + """>"""+ my_data.transaction_hash + """</a>"""
	elif mode.BLOCKCHAIN == 'ethereum' :
		transaction_hash = """<a class = "card-link" href = https://etherscan.io/tx/ """ + my_data.transaction_hash + """>"""+ my_data.transaction_hash + """</a>"""
	else :
		transaction_hash = my_data.transaction_hash

	if support == 'document' :
		myadvanced = """
				<b>Advanced</b>
				<li><b>Document Id</b> : """ + dataId + """<br></li>
				<li><b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a></li>"""

		# Verifiable Credential
		credential = Document('certificate')
		credential.relay_get_credential(session['workspace_contract'], doc_id, mode, loading = 'full')
		credential_text = json.dumps(credential.__dict__, sort_keys=True, indent=4, ensure_ascii=False)

	# if support is an ERC725 Claim
	else :
		(location, link) = (mode.BLOCKCHAIN, "") if myvisibility == 'public' else (my_data.data_location, my_data.data_location)
		myadvanced = """
				<b>Advanced</b>
				<li><b>Claim Id</b> : """ + str(claim_id) + """<br></li>
				<li><b>Topic</b> : """ + str(my_data.topicname) + """<br></li>
				<li><b>Privacy</b> : """ + myvisibility + """<br></li>
				<li><b>Created</b> : """ + my_data.created + """<br></li>
				<li><b>Expires</b> : """ + expires + """<br></li>
				<li><b>Transaction Hash</b> : """ +transaction_hash + """<br></li>
				<li><b>Data storage</b> : <a class="card-link" href=""" + link + """>""" + location + """</a></li>"""

	return render_template('data_check.html', **session['menu'], verif=myadvanced, credential=credential_text)


def user(mode) :
	"""
	#@app.route('/user/', methods = ['GET'])
	Main view for Identity
	We setup Ientity with workspace or username depending of the login method
	"""
	check_login()
	if not session.get('uploaded', False) :
		logging.info('start first instanciation')

		if not session.get('workspace_contract') :
			logging.info('Identity set up from username')
			data_from_username = ns.get_data_from_username(session['username'], mode)
			session['workspace_contract'] = data_from_username['workspace_contract']
		else :
			logging.info('Identity set up from workspace contract')

		if mode.test :
			user = Identity(session['workspace_contract'], mode, authenticated=True)
		else :
			try :
				user = Identity(session['workspace_contract'], mode, authenticated=True)
			except :
				logging.error('cannot init Identity')
				flash('session aborted', 'warning')
				return render_template('login.html')

		logging.warning('end of first intanciation')

		# clean up for resume
		user_dict = user.__dict__.copy()
		del user_dict['aes']
		del user_dict['rsa_key_value']
		del user_dict['private_key_value']
		del user_dict['secret']
		del user_dict['partners']

		# init session
		session['resume'] = user_dict
		session['uploaded'] = True
		session['type'] = user.type
		session['address'] = user.address
		session['workspace_contract'] = user.workspace_contract
		session['issuer'] = user.issuer_keys
		session['whitelist'] = user.white_keys
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
		session['has_vault_access'] = user.has_vault_access

		phone =  ns.get_data_from_username(session.get('username'), mode).get('phone')
		session['phone'] = phone if phone else ""

		if user.type == 'person' :
			session['experience'] = user.experience
			session['education'] = user.education
			session['kyc'] = user.kyc
			session['profil_title'] = user.profil_title
			session['menu'] = {'picturefile' : user.picture,
								'username' : session.get('username', ""),
								'name' : session['name'],
								'private_key_value' : user.private_key_value,
								'rsa_filename': session['rsa_filename'],
								'profil_title' : session['profil_title'],
								'clipboard' : mode.server  + "resume/?did=" + session['did']}
			# no credential workflow
			session['host'] = session['employee'] = None
			session['role'] = session['referent'] = None

		if user.type == 'company' :
			session['kbis'] = user.kbis
			session['profil_title'] = ""
			session['menu'] = {'picturefile' : user.picture,
								'username' : session['username'],
								'name' : user.name,
								'private_key_value' : user.private_key_value,
								'rsa_filename': session['rsa_filename'],
								'profil_title' : session['profil_title'],
								'clipboard' : mode.server  + "board/?did=" + session['did']}

			# data for credential workflow
			# for admin, issuer or reviewer
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

		"""
		# Warning message for first connexion
		message1 = message2 = message3 = ""
		if not session['private_key'] :
			message1 = "Private key not found on server. "
		if not session['rsa_key'] :
			message2 = "Rsa key not found. "
		if not session['has_vault_access'] :
			message3 = "Your wallet is not activated. "
		if message1 and message2 and not message3 :
			message = "You control your Identity with your smartphone wallet."
		elif message1 and message2 and message3 :
			message = "You must activate your wallet to control your Identity."
		elif message1 or message2 :
			message = message1 + message2
		else :
			message = "Your have allowed this third party wallet to manage your Identity."
		flash(message, 'warning')
		"""

		# Dashboard start for employees
		if session['role'] in ['issuer', 'reviewer'] :
			return redirect (mode.server + 'company/dashboard/')

		# Homepage start for Talent
		if user.type == 'person' :
			return render_template('homepage.html', **session['menu'])

	# account
	#my_account = """ <b>ETH</b> : """ + str(session['eth'])+"""<br>
	#				<b>token TALAO</b> : """ + str(session['token'])
	my_account = ""
	if session['username'] == 'talao' :
		relay_eth = mode.w3.eth.getBalance(mode.relay_address)/1000000000000000000
		relay_token = float(token_balance(mode.relay_address,mode))
		talaogen_eth = mode.w3.eth.getBalance(mode.Talaogen_public_key)/1000000000000000000
		talaogen_token = float(token_balance(mode.Talaogen_public_key, mode))
		total_deposit, vault_deposit = get_data_from_token(mode)
		my_account = my_account + """<br><br>
					<b>Relay ETH</b> : """ + str(relay_eth) + """<br>
					<b>Relay token Talao</b> : """ + str(relay_token) + """<br><br>
					<b>Talao Gen ETH</b> : """ + str(talaogen_eth) + """<br>
					<b>Talao Gen token Talao</b> : """ + str(talaogen_token) + """<br><br>
					<b>Vault Deposit</b> : """ + str(vault_deposit/10**18) + """ TALAO <br>
					<b>Total Deposit</b> : """ + str(total_deposit/10**18) + """ TALAO<br>
					<b>Nb Identities</b> : """ + str(int(total_deposit/vault_deposit))

	# advanced
	relay = 'Activated' if session['relay_activated'] else 'Not Activated'
	relay_rsa_key = 'Yes' if session['rsa_key']  else 'No'
	relay_private_key = 'Yes' if session['private_key'] else 'No'
	#path = """https://rinkeby.etherscan.io/address/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/address/"""
	my_advanced = """
					<b>Blockchain</b> : """ + mode.BLOCKCHAIN.capitalize() + """<br>
					<b>DID</b> : did:talao:talaonet:""" + session['workspace_contract'][2:] + """</a><br>
					<b>Owner Wallet Address</b> : """ + session['address'] + """<br>"""
	if session['username'] != 'talao' :
		my_advanced = my_advanced + """ <hr><b>Relay Status : </b>""" + relay + """<br>"""
		my_advanced = my_advanced + """<b>RSA Key on server</b> : """ + relay_rsa_key + """<br>"""
		my_advanced = my_advanced + """<b>Private Key on server </b> : """ + relay_private_key +"""<br>"""
	my_advanced = my_advanced + "<hr>" + my_account +  "<hr>"

	# Partners
	if not session['partner'] :
		my_partner = """<a class="text-info">No Partners available</a>"""
	else :
		my_partner = ""
		for partner in session['partner'] :
			#partner_username = ns.get_username_from_resolver(partner['workspace_contract'])
			#partner_username = 'Unknown' if partner_username is None else partner_username
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
		my_issuer = """  <a class="text-info">No Referents available</a>"""
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


	# whitelist
	if not session['whitelist'] :
		my_white_issuer = """  <a class="text-info">No Whitelist available</a>"""
	else :
		my_white_issuer = ""
		for issuer in session['whitelist'] :
			issuer_username = ns.get_username_from_resolver(issuer['workspace_contract'], mode)
			issuer_username = 'Unknown' if issuer_username is None else issuer_username
			issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_white_issuer/?issuer_username="""+issuer_username +"""&amp;issuer_address="""+issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span>"""
			my_white_issuer = my_white_issuer + issuer_html + """<br>"""


	# files
	if not session['identity_file'] :
		my_file = """<a class="text-info">No Files available</a>"""
	else :
		my_file = ""
		for one_file in session['identity_file'] :
			file_html = """
				<b>File Name</b> : """+one_file['filename']+ """ ( """+ one_file['privacy'] + """ ) <br>
				<b>Created</b> : """+ one_file['created'] + """<br>
				<p>
					<a class="text-secondary" href="/user/remove_file/?file_id=""" + one_file['id'] + """&filename="""+one_file['filename'] +"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>

					<a class="text-secondary" href=/user/download/?filename=""" + one_file['filename'] + """>
						<i data-toggle="tooltip" class="fa fa-download" title="Download"></i>
					</a>
				</p>"""
			my_file = my_file + file_html

	# skills
	if not session['skills'] or not session['skills'].get('id') :
		my_skills =  """<a class="text-info">No data available</a>"""
	else :
		my_skills = ""
		for skill in session['skills']['description'] :
			skill_html = skill['skill_name'] + """ (""" + skill['skill_level'] + """)""" + """<br>"""
			my_skills = my_skills + skill_html
		my_skills = my_skills + """
				<p>
					<a class="text-secondary" href=/data/?dataId="""+ session['skills']['id'] + """:skills>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""



	# specific to person
	if session['type'] == 'person' :
		# experience
		my_experience = ""
		if len (session['experience']) == 0:
			my_experience = my_experience + """<a class="text-info">No Experience available</a>"""
		else :
			for experience in sorted(session['experience'], key= lambda d: time.strptime(d['start_date'], "%Y-%m-%d"), reverse=True) :
				exp_html = """
				<b>Company</b> : """+experience['company']['name']+"""<br>
				<b>Title</b> : """+experience['title']+"""<br>
				<b>Start Date</b> : """+experience['start_date']+"""<br>
					<b>End Date</b> : """+experience['end_date']+"""<br>
				<b>Description</b> : """+experience['description'][:100]+"""...<br>
				<p>
					<a class="text-secondary" href="/user/remove_experience/?experience_id=""" + experience['id'] + """&experience_title="""+ experience['title'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>

					<a class="text-secondary" href=/data/?dataId="""+ experience['id'] + """:experience>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""
				my_experience = my_experience + exp_html + "<hr>"

		# education
		my_education = ""
		if not session['education'] :
			my_education = my_education + """<a class="text-info">No Education available</a>"""
		else :
			for education in session['education'] :
				edu_html = """
				<b>Organization</b> : """+education['organization']['name']+"""<br>
				<b>Title</b> : """+education['title'] + """<br>
				<b>Start Date</b> : """+education['start_date']+"""<br>
				<b>End Date</b> : """+education['end_date']+"""<br>
				<p>
					<a class="text-secondary" href="/user/remove_education/?education_id=""" + education['id'] + """&education_title="""+ education['title'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href=/data/?dataId="""+ education['id'] + """:education>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""
				my_education = my_education + edu_html	+ "<hr>"

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
		my_personal = ""
		for topicname in session['personal'].keys() :
			if session['personal'][topicname]['claim_value'] :
				topicname_value = session['personal'][topicname]['claim_value']
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':claim:' + session['personal'][topicname]['claim_id']
				topicname_privacy = ' (' + session['personal'][topicname]['privacy'] + ')'
				my_personal = my_personal + """
				<span><b>""" + Topic[topicname] + """</b> : """+ topicname_value + topicname_privacy +"""
					<a class="text-secondary" href=/data/?dataId=""" + topicname_id + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span><br>"""

		# kyc Digital Identity this is ann ERC725 claim
		my_kyc = ""
		if not session['kyc'] or not session['kyc'][0]['claim_id']:
			my_kyc = my_kyc + """<p>Your Professionnal Digital Identity has not been activated yet.
			  You can now start the Identity verification process.</p>
			 				<br>
							 <a href="/user/request_proof_of_identity/">
                            	<div class="form-group"><button class="btn btn-primary btn-sm pull-right" type="button">Identity verification</button></div>
                             </a>
							"""
		else :
			kyc = session['kyc'][0]
			kyc_html = """ Your Professionnal Digital Identity has been activated by """ +  kyc['issuer'].get('name', 'Unknown') + """<br>
				<b>Date of issue</b> : """ + kyc['created'] + """<br>

				<div id="id_kyc"></div>
				<p>
					<a class="text-secondary" href="/user/remove_kyc/?kyc_id=""" + kyc.get('id',"") + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/data/?dataId=""" + kyc.get('id',"") + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>
                    <div id="button" class="form-group"> <button id="in_progress_button" onclick="getKyc()" class="btn btn-primary btn-sm " type="button">Check your Digital Identity</button></div>
				"""
			my_kyc = my_kyc + kyc_html

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

		# credentials
		my_certificates = ""
		if not session['certificate'] :
			my_certificates = my_certificates + """<a class="text-info">No Credential available</a>"""
		else :
			for counter, certificate in enumerate(session['certificate'],1) :
				issuer_username = ns.get_username_from_resolver(certificate['issuer']['workspace_contract'], mode)
				issuer_username = 'Unknown' if not issuer_username else issuer_username
				if certificate['issuer']['category'] == 2001 : # company
					issuer_name = certificate['issuer']['name']
					#issuer_type = 'Company'
				elif  certificate['issuer']['category'] == 1001 :
					issuer_name = certificate['issuer']['firstname'] + ' ' + certificate['issuer']['lastname']
					#issuer_type = 'Person'
				else :
					pass
				try :
					cert_html = """<hr>
							<b>Referent Name</b> : """ + issuer_name +"""<br>
							<b>Credential Type</b> : """ + certificate['credentialSubject']['credentialCategory'].capitalize()+"""<br>
							<b>Title</b> : """ + certificate['credentialSubject']['title'] + """<br>
							<b>Description</b> : """ + certificate['credentialSubject']['description'][:100]+"""...<br>"""
				except :
					cert_html = "credential : #" + str(counter) + """<br>"""

				cert_html += """<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """>Display Credential</a><br>
							<p>
							<a class="text-secondary" href="/user/remove_certificate/?certificate_id=""" + certificate['id'] + """&certificate_title="""+ certificate.get('title', "None") + """">
							<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
							</a>
							<a class="text-secondary" href=/data/?dataId=""" + certificate['id'] + """:certificate>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check">&nbsp&nbsp&nbsp</i>
							</a>
							<a class="text-secondary" onclick="copyToClipboard('#p"""+ str(counter) + """')">
							<i data-toggle="tooltip" class="fa fa-clipboard" title="Copy Credential Link"></i>
							</a>
							</p>
							<p hidden id="p""" + str(counter) + """" >""" + mode.server  + """guest/certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """</p>"""
				my_certificates += cert_html

		return render_template('person_identity.html',
							**session['menu'],
							display_alias = display_alias,
							personal=my_personal,
							kyc=my_kyc,
							experience=my_experience,
							education=my_education,
							skills=my_skills,
							certificates=my_certificates,
							access=my_access,
							partner=my_partner,
							issuer=my_issuer,
							whitelist=my_white_issuer,
							advanced=my_advanced,
							digitalvault= my_file,
							nb_certificates=len(session['certificate'])
							)
	# specific to company
	if session['type'] == 'company' :

		# Admin list  and add admin
		my_admin_start = """<a href="/company/add_employee/?role_to_add=admin">Add an Admin</a><hr> """
		my_admins = ""
		admin_list = ns.get_employee_list(session['host'],'admin', 'all', mode)
		for admin in admin_list :
			admin_html = """
				<span>""" + admin['username'] + """ => """ +  admin['identity_name'] +"""
				<a class="text-secondary" href="/user/remove_access/?employee_to_remove="""+ admin['username']+"""">
					<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">	</i>
				</a>
				</span>"""
			my_admins +=  admin_html + """<br>"""
		my_admins = my_admin_start + my_admins

		# Issuer list and add issuer within a company
		my_managers_start = """<a href="/company/add_employee/?role_to_add=issuer">Add an Issuer</a><hr> """
		my_managers = ""
		manager_list = ns.get_employee_list(session['host'],'issuer', 'all', mode)
		for manager in manager_list :
			manager_html = """
				<span>""" + manager['username'] + """ => """ +  manager['identity_name'] +"""
				<a class="text-secondary" href="/user/remove_access/?employee_to_remove="""+ manager['username']+"""">
					<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">	</i>
				</a>
				</span>"""
			my_managers += manager_html + """<br>"""
		my_managers = my_managers_start + my_managers

		# Reviewer list and add reviewers
		my_reviewers_start = """<a href="/company/add_employee/?role_to_add=reviewer">Add a Reviewer</a><hr> """
		my_reviewers = ""
		reviewer_list = ns.get_employee_list(session['host'], 'reviewer', 'all', mode)
		for reviewer in reviewer_list :
			reviewer_html = """
				<span>""" + reviewer['username'] + """ => """ +  reviewer['identity_name'] +"""
				<a class="text-secondary" href="/user/remove_access/?employee_to_remove="""+ reviewer['username']+"""">
					<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">	</i>
				</a>
				</span>"""
			my_reviewers += reviewer_html + """<br>"""
		my_reviewers = my_reviewers_start + my_reviewers

		# kbis
		if not session['kbis'] :
			my_kbis = """<a href="/user/request_proof_of_identity/">Request a Proof of Identity</a><hr>
					<a class="text-danger">No Proof of Identity available</a>"""
		else :
			my_kbis = ""
			for kbis in session['kbis'] :
				kbis_html = """
				<b>Name</b> : """+ kbis['name'] +"""<br>
				<b>SIREN</b> : """+ kbis.get('siren', '') +"""<br>
				<b>Creation</b> : """+ kbis['date'] + """<br>
				<b>Capital</b> : """+ kbis['capital']+"""<br>
				<b>Address</b> : """+ kbis['address']+"""<br>

					<a class="text-secondary" href="/user/remove_kbis/?kbis_id=""" + kbis['id'] + """">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href=/data/?dataId="""+ kbis['id'] + """:kbis>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				"""
				my_kbis = my_kbis + kbis_html

		# company settings
		if session['role'] in ['creator', 'admin'] :
			my_personal = """<a href="/user/picture/">Change Logo</a><br>
						<a href="/user/signature/">Change Signature</a><br>"""
		else :
			my_personal = ""

		for topicname in session['personal'].keys() :
			if session['personal'][topicname]['claim_value'] :
				topicname_value = session['personal'][topicname]['claim_value']
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':claim:' + session['personal'][topicname]['claim_id']
				topicname_privacy = ' (' + session['personal'][topicname]['privacy'] + ')'
				my_personal = my_personal + """
				<span><b>""" + topicname + """</b> : """+ topicname_value + topicname_privacy +"""
					<a class="text-secondary" href=/data/?dataId=""" + topicname_id + """>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span><br>"""
		if session['role'] in ['creator', 'admin'] :
			my_personal = my_personal + """<a href="/user/update_company_settings/">Update Company Data</a>"""

		# certificates
		if  not session['certificate'] :
			my_certificates =  """<a class="text-info">No Credentials available</a>"""
		else :
			my_certificates = """<div  style="height:300px;overflow:auto;overflow-x: hidden;">"""
			for counter, certificate in enumerate(session['certificate'],1) :
				issuer_username = ns.get_username_from_resolver(certificate['issuer']['workspace_contract'], mode)
				issuer_username = 'Unknown' if not issuer_username else issuer_username
				if certificate['issuer']['category'] == 2001 :
					issuer_name = certificate['issuer']['name']
				else :
					issuer_name = certificate['issuer']['firstname'] + ' ' + certificate['issuer']['lastname']
				if certificate['type'] == 'agreement' :
					if not issuer_name :
						issuer_name = 'unknown'
					cert_html = """<hr>
								<b>Referent Name</b> : """ + issuer_name +"""<br>
								<b>Certificate Type</b> : """ + certificate.get('type','').capitalize()+"""<br>
								<b>Title</b> : """ + certificate.get('title',"").capitalize()+"""<br>
								<b>Registration number</b> : """ + certificate.get('registration_number',"").capitalize()+"""<br>
								<b>Description</b> : " """ + certificate['description'][:100]+"""..."<br>

								<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """>Display Certificate</a><br>
								<p>
								<a class="text-secondary" href="/user/remove_certificate/?certificate_id=""" + certificate['id'] + """&certificate_title=""" + certificate['type'].capitalize()+ """">
								<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
								</a>

								<a class="text-secondary" href=/data/?dataId=""" + certificate['id'] + """:certificate>
								<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check">&nbsp&nbsp&nbsp</i>
								</a>
								<a class="text-secondary" onclick="copyToClipboard('#p"""+ str(counter) + """')">
								<i data-toggle="tooltip" class="fa fa-clipboard" title="Copy Certificate Link"></i>
								</a>
								</p>
								<p hidden id="p""" + str(counter) +"""" >""" + mode.server  + """guest/certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """</p>"""

				elif certificate['type'] ==  "reference" :
					cert_html = """<hr>
								<b>Referent Name</b> : """ + issuer_name +"""<br>
								<b>Certificate Type</b> : """ + certificate.get('type', 'Unknown').capitalize()+"""<br>
								<b>Title</b> : """ + certificate.get('title', 'Unknown').capitalize()+"""<br>
								<b>Description</b> : " """ + certificate.get('description', 'Unknown')[:100]+"""..."<br>
								<b>Budget</b> : """ + certificate.get('budget', 'Unknown') + """<br>
								<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """>Display Certificate</a><br>
								<p>
								<a class="text-secondary" href="/user/remove_certificate/?certificate_id=""" + certificate['id'] + """&certificate_title=""" + certificate.get('type', 'Unknown').capitalize()+ """">
								<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
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
					cert_html =""
					logging.error('incorrect certificate type : ' + certificate.get('type', 'Unknown'))
				my_certificates = my_certificates + cert_html
			my_certificates = my_certificates + """</div>"""

		return render_template('company_identity.html',
							**session['menu'],
							admin=my_admins,
							manager=my_managers,
							reviewer=my_reviewers,
							personal=my_personal,
							skills=my_skills,
							kbis=my_kbis,
							issuer=my_issuer,
							certificates=my_certificates,
							whitelist=my_white_issuer,
							advanced=my_advanced,
							digitalvault=my_file)


def user_advanced(mode) :
	check_login()

	# account
	my_account = ""
	if session['username'] == 'talao' :
		relay_eth = mode.w3.eth.getBalance(mode.relay_address)/1000000000000000000
		relay_token = float(token_balance(mode.relay_address,mode))
		talaogen_eth = mode.w3.eth.getBalance(mode.Talaogen_public_key)/1000000000000000000
		talaogen_token = float(token_balance(mode.Talaogen_public_key, mode))
		my_account = my_account + """<br><br>
					<b>Relay ETH</b> : """ + str(relay_eth) + """<br>
					<b>Relay token Talao</b> : """ + str(relay_token) + """<br><br>
					<b>Talao Gen ETH</b> : """ + str(talaogen_eth) + """<br>
					<b>Talao Gen token Talao</b> : """ + str(talaogen_token)

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
		#display_alias = False
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

	# Blockchain data
	vault = 'Yes' if session['has_vault_access'] else 'No'
	relay_rsa_key = 'Yes' if session['rsa_key']  else 'No'
	relay_private_key = 'Yes' if session['private_key'] else 'No'
	did = "did:talao:" + mode.BLOCKCHAIN + ":" + session['workspace_contract'][2:]
	if ns.get_wallet_from_workspace_contract(session['workspace_contract'], mode) :
		wallet = 'Alias (Centralized mode)'
	else :
		wallet = 'Owner (Decentralized mode)'
	role = session['role'] if session.get("role") else 'None'
	referent = session['referent'] if session.get('referent') else 'None'
	my_advanced = """
					<b>Blockchain</b> : """ + mode.BLOCKCHAIN.capitalize() + """<br>
					<b>DID</b> : <a class = "card-link" href = "https://talao.co/resolver?did=""" + did + """"">""" + did + """</a><br>
					<b>Owner Address</b> : """+ session['address'] + """</a><br>
					<b>Wallet</b> : """ + wallet  + """<br>
					<b>Role</b> : """ + role + """<br>
					<b>Referent</b> : """ + referent + """<br>"""
	if session['username'] != 'talao' :
		my_advanced = my_advanced + """ <hr><b>Wallet has locked token : </b>""" + vault + """<br>"""
		my_advanced = my_advanced + """<b>RSA Key on server </b> : """ + relay_rsa_key + """<br>"""
		my_advanced = my_advanced + """<b>Private Key on server </b> : """ + relay_private_key +"""<br>"""
	my_advanced = my_advanced + "<hr>" + my_account

	# Partners
	if session['partner'] == [] :
		my_partner = """<a class="text-info">No Partners available</a>"""
	else :
		my_partner = ""
		for partner in session['partner'] :
			#partner_username = ns.get_username_from_resolver(partner['workspace_contract'])
			#partner_username = 'Unknown' if partner_username is None else partner_username
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
		my_issuer = """  <a class="text-info">No Referents available</a>"""
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


	# whitelist
	if session['whitelist'] == [] :
		my_white_issuer = """  <a class="text-info">No Whitelist available</a>"""
	else :
		my_white_issuer = ""
		for issuer in session['whitelist'] :
			issuer_username = ns.get_username_from_resolver(issuer['workspace_contract'], mode)
			issuer_username = 'Unknown' if not issuer_username else issuer_username
			issuer_html = """
				<span>""" + issuer_username + """
					<a class="text-secondary" href="/user/remove_white_issuer/?issuer_username="""+issuer_username +"""&amp;issuer_address="""+issuer['address']+"""">
						<i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
					</a>
					<a class="text-secondary" href="/user/issuer_explore/?issuer_username=""" + issuer_username + """">
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</span>"""
			my_white_issuer = my_white_issuer + issuer_html + """<br>"""

	return render_template('advanced.html',
							**session['menu'],
							access=my_access,
							partner=my_partner,
							issuer=my_issuer,
							api=my_api,
							whitelist=my_white_issuer,
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
			flash('Picture has been updated', 'success')
		else :
			flash('Logo has been updated', 'success')
	return render_template('account.html',
							**session['menu'],
							checkBox = checkBox)
