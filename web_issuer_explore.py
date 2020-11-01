""" Issuer explore is used to display Ientity when search """

import os
from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
from flask_fontawesome import FontAwesome
from datetime import timedelta, datetime
import json
import random
from Crypto.PublicKey import RSA

# dependances
import Talao_message
import Talao_ipfs
import constante
from protocol import ownersToContracts, contractsToOwners, destroy_workspace, save_image, partnershiprequest, remove_partnership, token_balance
from protocol import Claim, File, Identity, Document, read_profil
import hcode
import ns
import sms


def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if session.get('username') is None :
		abort(403)
	else :
		return session['username']


# helper
def is_username_in_list(my_list, username) :
	for user in my_list :
		if user['username'] == username :
			return True
	return False
# helper
def is_username_in_list_for_partnership(partner_list, username) :
	for partner in partner_list :
		if partner['username'] == username and partner['authorized'] not in ['Removed',"Unknown", "Rejected"]:
			return True
	return False

# issuer explore
# This view allow user to explore other identities
#@app.route('/user/issuer_explore/', methods=['GET'])
def issuer_explore(mode) :
	check_login()
	issuer_username = request.args['issuer_username']
	if 'issuer_username' not in session or session['issuer_username'] != issuer_username :
		if not ns.username_exist(issuer_username, mode) :
			flash('Issuer data not available', 'danger')
			return redirect(mode.server + 'user/')
		issuer_workspace_contract = ns.get_data_from_username(issuer_username, mode)['workspace_contract']
		session['issuer_explore'] = Identity(issuer_workspace_contract, mode, workspace_contract_from = session['workspace_contract'], private_key_from=session['private_key_value']).__dict__.copy()
		#del session['issuer_explore']['mode']
		session['issuer_username'] = issuer_username

	issuer_picture = session['issuer_explore']['picture']
	if session['issuer_explore']['type'] == 'person' :

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
		issuer_personal = """<span><b>Username</b> : """ + ns.get_username_from_resolver(session['issuer_explore']['workspace_contract'], mode)+"""<br>"""
		is_encrypted = False
		for topic_name in session['issuer_explore']['personal'].keys() :
			if session['issuer_explore']['personal'][topic_name]['claim_value'] is not None :

				if session['issuer_explore']['personal'][topic_name]['claim_value'] != 'private' and session['issuer_explore']['personal'][topic_name]['claim_value'] != 'secret'  :
					topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['issuer_explore']['workspace_contract'][2:] + ':claim:' + session['issuer_explore']['personal'][topic_name]['claim_id']
					issuer_personal = issuer_personal + """
						<span><b>"""+ Topic[topic_name] +"""</b> : """+ session['issuer_explore']['personal'][topic_name]['claim_value']+"""

						<a class="text-secondary" href=/data/?dataId=""" + topicname_id + """:personal>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
						</a>
					</span><br>"""
				elif session['issuer_explore']['personal'][topic_name]['claim_value'] == 'private' :
					is_encrypted = True
					topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['issuer_explore']['workspace_contract'][2:] + ':claim:' + session['issuer_explore']['personal'][topic_name]['claim_id']
					issuer_personal = issuer_personal + """
						<span><b>"""+ Topic[topic_name] +"""</b> : Not available - Encrypted
					</span><br>"""

				else  :
					pass
					print('test')
		if is_encrypted :
			issuer_personal = issuer_personal + """<br><a href="/user/request_partnership/?issuer_username=""" + issuer_username + """">Request a Partnership to this Talent to acces his private data.</a><br>"""

		# kyc
		my_kyc = """ <b>ECDSA Key</b> : """+ session['issuer_explore']['address'] +"""<br><hr>"""
		if len(session['issuer_explore']['kyc']) == 0 :
			my_kyc = my_kyc + """ <a class="text-danger">No other proof of identity available.</a>"""
		else :
			for kyc in session['issuer_explore']['kyc'] :
				kyc_html = """
				<b>Firstname</b> : """+ kyc['firstname'] +"""<br>
				<b>Lastname</b> : """+ kyc['lastname'] +"""<br>
				<b>Birth Date</b> : """+ kyc['birthdate'] +"""<br>
				<b>Gender</b> : """+ kyc['sex'].capitalize() +"""<br>
				<b>Nationality</b> : """+ kyc['nationality'] + """<br>
				<b>Card Id</b> : """+ kyc.get('card_id', 'Unknown')+"""<br>
				<p>
					<a class="text-secondary" href=/data/?dataId="""+ kyc['id'] + """:kyc>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""
				my_kyc = my_kyc + kyc_html

		# experience
		issuer_experience = ''
		if session['issuer_explore']['experience'] == [] :
			issuer_experience = """  <a class="text-info">No Experience available</a>"""
		else :
			for experience in session['issuer_explore']['experience'] :
				exp_html = """
					<b>Company</b> : """+experience['company']['name']+"""<br>
					<b>Title</b> : """+experience['title']+"""<br>
					<b>Description</b> : """+experience['description'][:100]+"""...<br>
					<p>
						<a class="text-secondary" href=/data/?dataId="""+experience['id'] + """:experience>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
						</a>
					</p>"""
				issuer_experience = issuer_experience + exp_html + """<hr>"""

		# education
		issuer_education = ''
		if session['issuer_explore']['education'] == [] :
			issuer_education = """  <a class="text-info">No Education available</a>"""
		else :
			for education in session['issuer_explore']['education'] :
				edu_html = """
					<b>Company</b> : """+education['organization']['name']+"""<br>
					<b>Title</b> : """+education['title']+"""<br>
					<b>Description</b> : """+education['description'][:100]+"""...<br>
					<p>
						<a class="text-secondary" href=/data/?dataId="""+ education['id'] + """:education>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
						</a>
					</p>"""
				issuer_education = issuer_education + edu_html + """<hr>"""

		# skills
		if session['issuer_explore']['skills'] is None or session['issuer_explore']['skills'].get('id') is None :
			issuer_skills =  """<a class="text-info">No Skills Available</a>"""
		else :
			issuer_skills = ""
			for skill in session['issuer_explore']['skills']['description'] :
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
					<a class="text-secondary" href=/data/?dataId="""+ session['issuer_explore']['skills']['id'] + """:skills>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""

		# certificates
		issuer_certificates = ""
		if session['issuer_explore']['certificate'] == [] :
			issuer_certificates = """<a class="text-info">No Certificates available</a>"""
		else :
			for certificate in session['issuer_explore']['certificate'] :
				certificate_issuer_username = ns.get_username_from_resolver(certificate['issuer']['workspace_contract'], mode)
				certificate_issuer_username = 'Unknown' if certificate_issuer_username is None else certificate_issuer_username
				if certificate['issuer']['category'] == 2001 :
					certificate_issuer_name = certificate['issuer']['name']
					certificate_issuer_type = 'Company'
				elif  certificate['issuer']['category'] == 1001 :
					certificate_issuer_name = certificate['issuer']['firstname'] + ' ' + certificate['issuer']['lastname']
					certificate_issuer_type = 'Person'
				else :
					print ('issuer category error, data_user.py')
				if certificate['type'] == 'experience' :
					cert_html = """
						<b>Referent Name</b> : """ + certificate_issuer_name +"""<br>
						<b>Referent Username</b> : """ + certificate_issuer_username +"""<br>
						<b>Referent Type</b> : """ + certificate_issuer_type +"""<br>
						<b>Title</b> : """ + certificate['title']+"""<br>
						<b>Description</b> : """ + certificate['description'][:100]+"""...<br>
						<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['issuer_explore']['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """>Display Certificate</a><br>
						<p>
							<a class="text-secondary" href=/data/?dataId=""" + certificate['id'] + """:certificate>
								<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
							</a>
						</p>"""
				elif certificate['type'] == 'recommendation' :
					cert_html = """
						<b>Referent Name</b> : """ + certificate_issuer_name +"""<br>
						<b>Referent Username</b> : """ + certificate_issuer_username +"""<br>
						<b>Referent Type</b> : """ + certificate_issuer_type +"""<br>
						<b>Description</b> : """ + certificate['description'][:100]+"""...<br>
						<b>Relationship</b> : """ + certificate['relationship']+"""...<br>
						<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['issuer_explore']['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """>Display Certificate</a><br>
						<p>
							<a class="text-secondary" href=/data/?dataId=""" + certificate['id'] + """:certificate>
								<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
							</a>
						</p>"""
				issuer_certificates = issuer_certificates + cert_html + """<hr>"""

		# file
		if session['issuer_explore']['identity_file'] == [] :
			my_file = """<a class="text-info">No Files available</a>"""
		else :
			my_file = ""
			is_encrypted = False
			for one_file in session['issuer_explore']['identity_file'] :
				if one_file.get('content') == 'Encrypted' :
					is_encrypted = True
					file_html = """
					<b>File Name</b> : """+one_file['filename']+ """ ( """+ 'Not available - Encrypted ' + """ ) <br>
					<b>Created</b> : """+ one_file['created'] + """<br>"""
				else :
					file_html = """
					<b>File Name</b> : """+one_file['filename']+ """ ( """+ one_file['privacy'] + """ ) <br>
					<b>Created</b> : """+ one_file['created'] + """<br>
					<a class="text-secondary" href=/user/download/?filename=""" + one_file['filename'] + """>
						<i data-toggle="tooltip" class="fa fa-download" title="Download"></i>
					</a>"""
				my_file = my_file + file_html + """<br>"""
			if is_encrypted :
				my_file = my_file + """<a href="/user/request_partnership/?issuer_username=""" + issuer_username + """">Request a Partnership to this Talent to access his encrypted Data.</a><br>"""

		#services : le reader est une persone, le profil vu est celui dune personne
		services = ""
		if session['type'] == 'person' :
			if not is_username_in_list(session['issuer'], issuer_username) : # est ce que ce talent est dans mon issuer list ?
				services = services + """<br><a class="text-warning">This Talent is not in your Referent List.</a><br>
							<a href="/user/add_issuer/?issuer_username=""" + issuer_username + """">Add this Talent in your Referent List to request him certificates.</a><br>"""
			else :
				services = services + """<br><a class="text-success">This Talent is in your Referent List.</a><br>
							<a href="/user/request_certificate/?issuer_username="""+ issuer_username + """">Request to this Talent a Certificate to strengthen your Resume.</a><br>"""

			if not is_username_in_list(session['whitelist'], issuer_username) : # est ce que ce Talent est dans ma white list ?
				services = services + """<br><a class="text-warning">This Talent is not in your White List.</a><br>
							<a href="/user/add_white_issuer/?issuer_username=""" + issuer_username + """"> Add this Talent to your White List to build your Identity efficiently.</a><br>"""
			else :
				services = services + """<br><a class="text-success">This Talent is in your White list.</a><br>"""

			if not is_username_in_list_for_partnership(session['partner'], issuer_username)  : # est ce qu il est dans ma partnership list
				services = services + """<br><a class="text-warning">This Talent is not in your Partner List.</a><br>
										<a href="/user/request_partnership/?issuer_username=""" + issuer_username + """">Request a Partnership to this Talent to access his private Data.</a><br>"""
			else :
				services = services + """<br><a class="text-success">This Talent is in your Partner list.</a><br>"""

			if is_username_in_list(session['issuer_explore']['issuer_keys'], session['username']) : # est ce que je suis dans l'issuer list de ce Talent ?
				services = services + """<br><a class="text-success">You are in this Talent Referent list.</a><br>
							<a href="/user/issue_certificate/?goback=/user/issuer_explore/?issuer_username="""+ issuer_username +"""" >Issue a Certificate to this Talent.</a><br>"""
			else :
				services = services + """<br><a class="text-warning">You are not in this Talent Referent list.</a><br>"""

			services = services + """<br><a href="/user/send_memo/?issuer_username="""+ issuer_username +""" ">Send a memo to this Talent.</a><br>"""
			services = services + """<br><a href="/user/data_analysis/?user=issuer_explore">Check Dashboard</a><br>"""
			services = services + """<br><br><br><br>"""

		#services : les reader est une company, le profil vu est celui d une personne. Attention au "jean.bnp"
		if session['type'] == 'company' :
			host_name = session['username'] if len(session['username'].split('.')) == 1 else session['username'].split('.')[1]
			if ns.does_manager_exist(issuer_username, host_name, mode) :
				services = services + """<br><a class="text-success">This Talent is a Manager.</a><br>"""

			if is_username_in_list(session['issuer_explore']['issuer_keys'], host_name) :
				services = services + """ <br><a class="text-success">Talent has authorized the Company to issue Certificates.</a><br>
										<a href="/user/issue_certificate/?goback=/user/issuer_explore/?issuer_username="""+ issuer_username +""" ">Issue a new Certificate.</a><br>"""
			else :
				services = services + """<br><br>"""

			if not is_username_in_list_for_partnership(session['partner'], issuer_username) : # est ce qu il est dans ma partnership list
				services = services + """<br><a class="text-warning">This Talent is not in your Partner List.</a>
										<br><a href="/user/request_partnership/?issuer_username=""" + issuer_username + """">Request a Partnership to share private Data.</a><br>"""
			else :
				services = services + """<br><a class="text-success">This Talent is in your Partner list.</a><br>"""

			services = services + """<br><a href="/user/send_memo/?issuer_username="""+ issuer_username +""" ">Send a memo to this Talent.</a><br>"""
			services = services + """<br><a href="/user/data_analysis/?user=issuer_explore">Check Dashboard</a><br><br>"""
			services = services + """<br><br><br><br><br><br><br><br><br><br>"""

		services = services + """<br><br><br><br><br>"""

		return render_template('person_issuer_identity.html',
							**session['menu'],
							issuer_name=session['issuer_explore']['name'],
							issuer_profil_title = session['issuer_explore']['profil_title'],
							kyc=my_kyc,
							personal=issuer_personal,
							experience=issuer_experience,
							certificates=issuer_certificates,
							education=issuer_education,
							services=services,
							digitalvault=my_file,
							skills=issuer_skills,
							issuer_picturefile=issuer_picture)


	if session['issuer_explore']['type'] == 'company' :

		# kbis
		kbis_list = session['issuer_explore']['kbis']
		if len (kbis_list) == 0:
			my_kbis = """<a class="text-danger">No Proof of Identity available</a>"""
		else :
			my_kbis = ""
			for kbis in kbis_list :
				kbis_html = """
				<b>Name</b> : """+ kbis['name'] +"""<br>
				<b>Siret</b> : """+ kbis['siret'] +"""<br>
				<b>Creation</b> : """+ kbis['date'] + """<br>
				<b>Capital</b> : """+ kbis['capital']+"""<br>
				<b>Address</b> : """+ kbis['address']+"""<br>
				<p>
					<a class="text-secondary" href=/data/?dataId="""+ kbis['id'] + """:kbis>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""
				my_kbis = my_kbis + kbis_html

		# personal
		issuer_personal = """ <span><b>Username</b> : """ + ns.get_username_from_resolver(session['issuer_explore']['workspace_contract'], mode)	+ """<br>"""
		for topic_name in session['issuer_explore']['personal'].keys() :
			if session['issuer_explore']['personal'][topic_name]['claim_value'] is not None :
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['issuer_explore']['workspace_contract'][2:] + ':claim:' + session['issuer_explore']['personal'][topic_name]['claim_id']
				issuer_personal = issuer_personal + """
				<span><b>"""+ topic_name +"""</b> : """+ session['issuer_explore']['personal'][topic_name]['claim_value']+"""

					<a class="text-secondary" href=/data/?dataId=""" + topicname_id + """:personal>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>"""




		#services : le reader est une persone, le profil vu est celui d'une company
		if session['type'] == 'person' :

			if not is_username_in_list(session['issuer'], issuer_username) :
				services = """<br><a class="text-warning">This Company is not in your Referent List.</a><br>
						<a href="/user/add_issuer/?issuer_username=""" + issuer_username + """">Add this Company in your Referent List to request Certificates.</a><br>"""
			else :
				services = """<br><a class="text-success">This Company is in your Referent List.</a><br>
						<a href="/user/request_certificate/?issuer_username="""+ issuer_username +"""">Request a certificate to this Company.</a><br>"""

			if not is_username_in_list(session['whitelist'], issuer_username) :
				services = services + """<br><a class="text-warning">This Company is not in your White List.</a><br>
						<a href="/user/add_white_issuer/?issuer_username=""" + issuer_username + """"> Add this Company in your White List to increase your rating.</a><br>"""
			else :
				services = services + """<br><a class="text-success">This Company is in your White list.</a><br>"""

			if not is_username_in_list_for_partnership(session['partner'], issuer_username) :
				services = services + """<br><a class="text-warning">This Company is not in your Partner List.</a>
						<br><a href="/user/request_partnership/?issuer_username=""" + issuer_username + """">Request a Partnership to access private information.</a><br>"""
			else :
				services = services + """<br><a class="text-success">This Company is in your Partner list.</a><br>"""

			if is_username_in_list(session['issuer_explore']['issuer_keys'], session['username']) :
				services = services + """<br><a href="/user/issue_referral/?issuer_username="""+ issuer_username + """&issuer_name=""" + session['issuer_explore']['name'] + """ ">Issue a Review.</a><br>"""
			else :
				services = services + """<br><a class="text-warning">You are not in this Company Referent List.</a><br>"""

			services = services + """<br><a href="/user/send_memo/?issuer_username="""+ issuer_username +""" ">Send a memo to this Company.</a><br>"""

			services = services + """<br><br><br><br><br><br>"""



		#services : le reader est une company , le profil vu est celui d'une company
		else : # session['type'] == 'company' :
			services = ""



		return render_template('company_issuer_identity.html',
							**session['menu'],
							issuer_name=session['issuer_explore']['name'],
							kbis=my_kbis,
							services=services,
							personal=issuer_personal,
							issuer_picturefile=issuer_picture)