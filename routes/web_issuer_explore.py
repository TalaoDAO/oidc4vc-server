""" Issuer explore is used to display Ientity when search """

import os
from os import path
import time
from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
from flask_fontawesome import FontAwesome
from datetime import timedelta, datetime
import json
import random
from Crypto.PublicKey import RSA
import requests
import shutil
import logging
logging.basicConfig(level=logging.INFO)

# dependances
from core import Talao_message, Talao_message, hcode, ns, sms
import constante
from protocol import ownersToContracts, contractsToOwners, destroy_workspace, save_image, partnershiprequest, remove_partnership, token_balance
from protocol import Claim, File, Identity, Document, read_profil


def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if not session.get('username') and not session.get('workspace_contract') :
		logging.error('abort')
		abort(403)
	else :
		return True


# helper
def is_username_in_list(my_list, username) :
	if not username :
		return False
	for user in my_list :
		if user['username'] == username :
			return True
	return False

# helper
def is_username_in_list_for_partnership(partner_list, username) :
	if not username :
		return False
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
		logging.info(' , issuer = %s', issuer_workspace_contract)
		session['issuer_explore'] = Identity(issuer_workspace_contract, mode, workspace_contract_from = session['workspace_contract'], private_key_from=session['private_key_value']).__dict__.copy()
		session['issuer_username'] = issuer_username

	#issuer_picture = session['issuer_explore']['picture']
	if session['issuer_explore']['type'] == 'person' :
		# file
		if session['issuer_explore']['identity_file'] == []:
			my_file = """<p class="text-center text-muted m-0 " style="font-size: 20px;">No data available</p>"""
		else:
			my_file = ""
			is_encrypted = False
			for one_file in session['issuer_explore']['identity_file']:
				if one_file.get('content') == 'Encrypted':
					is_encrypted = True
					file_html = """
					<b>File Name</b> : """ + one_file['filename'] + """ ( """ + 'Not available - Encrypted ' + """ ) <br>
					<b>Created</b> : """ + one_file['created'] + """<br>"""
				else:
					file_html = """
					<b>File Name</b> : """ + one_file['filename'] + """ ( """ + one_file['privacy'] + """ ) <br>
					<b>Created</b> : """ + one_file['created'] + """<br>
					<a class="text-secondary" href=/user/download/?filename=""" + one_file['filename'] + """>
						<i data-toggle="tooltip" class="fa fa-download" title="Download"></i>
					</a>"""
				my_file = my_file + file_html + """<br>"""

		# experience
		experiences = []
		for experience in session['issuer_explore']['certificate']:
			if experience['credentialSubject']['credentialCategory'] =='experience':
				experiences.append(experience)
		for experience in session['issuer_explore']['experience']:
			experiences.append(experience)

		# tri par date
		for i, experience in enumerate(experiences):
			min = i
			try :
				DTmin = time.strptime(experience['end_date'], "%Y-%m-%d")
			except :
				DTmin = time.strptime(experience['credentialSubject']['endDate'], "%Y-%m-%d")
			for j, certi in enumerate(experiences[i::]):
				try :
					DTcerti = time.strptime(certi['end_date'], "%Y-%m-%d")
				except :
					DTcerti = time.strptime(certi['credentialSubject']['endDate'], "%Y-%m-%d")
				if DTcerti < DTmin:
					min = j + i
					DTmin = DTcerti
			experiences[i] , experiences[min] = experiences[min], experiences[i]
		experiences = experiences[::-1]

		carousel_indicators_experience = """<li data-target="#experience-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_experience = ""
		if experiences == []:
			pass
		else :
			nbr_rows = (len(experiences)-1)//3
			for i in range(nbr_rows):
				carousel_indicators_experience += '<li data-target="#experience-carousel" data-slide-to="{}"></li>'.format(i+1)
			for i, experience in enumerate(experiences):
				# for verifiable credentials
				try:
					logo = experience['credentialSubject']['companyLogo']
					startDate = experience['credentialSubject']['startDate']
					endDate = experience['credentialSubject']['endDate']
					description = experience['credentialSubject']['description']
					title = experience['credentialSubject']['title']

				# for self claims
				except:
					logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'
					startDate = experience['start_date']
					endDate = experience['end_date']
					description = experience['description']
					title = experience['title']

				if logo != None:
					if not path.exists(mode.uploads_path + logo) :
						url = 'https://gateway.pinata.cloud/ipfs/'+ logo
						response = requests.get(url, stream=True)
						with open(mode.uploads_path + logo, 'wb') as out_file:
							shutil.copyfileobj(response.raw, out_file)
							del response

				if i%3==0:
					carousel_rows_experience += '<div class="carousel-item px-2 {a}"><div class="row" style="flex-direction: row;">'.format(a = "active" if (i == 0) else '')
				carousel_rows_experience += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image text-center h-100" style="background-color: white;" ><img src="""
				#image
				try:
					carousel_rows_experience +=""""{}" style="height: 200px;" alt="Loading error"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
				except:
					carousel_rows_experience +=""""https://s3-us-west-2.amazonaws.com/s.cdpn.io/331810/sample59.jpg" alt="Loading error"/></div><figcaption >"""
				#verified
				if experience['topic']=='experience':
					carousel_rows_experience += """<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="fa fa-pencil-square-o" style="color: #747474;font-size: 50px;"></i></div>"""
				else:
					carousel_rows_experience += """<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="material-icons my-auto" style="color: rgb(60,158,255);font-size: 50px;">verified_user</i></div>"""
				#header
				carousel_rows_experience += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + title + "</h4></div></div><hr class='my-1'>"
				#body
				if experience['topic']!='experience':
					carousel_rows_experience += """<p  style="font-size: 1em"><b>Referent name: </b>"""

					if experience['issuer']['category']==2001:
						carousel_rows_experience += experience['issuer']['name'] + """<br>"""
					else:
						carousel_rows_experience += experience['issuer']['firstname'] + ' ' + experience['issuer']['lastname'] + """<br>"""

				carousel_rows_experience += """<b>Start Date</b> : """ + startDate + """<br> """
				carousel_rows_experience += """<b>End Date</b> : """ + endDate + """<br>"""
				if experience['topic']!='experience':
					carousel_rows_experience += """<b>Description</b> : """ + description[:100:]
					if len(description)>100:
						carousel_rows_experience += "...<br>"
					else:
						carousel_rows_experience += "<br>"
				else:
					carousel_rows_experience += """<b>Description</b> : """ + description[:150:]
					if len(description)>150:
						carousel_rows_experience += "...<br>"
					else:
						carousel_rows_experience += "<br>"
				carousel_rows_experience += "</p>"
				#Footer
				if experience['topic']=='experience':
					carousel_rows_experience += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
					carousel_rows_experience += """<a href= /certificate/?certificate_id=""" + experience['id'] + """:experience> </a>"""
				else:
					if experience['issuer']['category']==2001:
						carousel_rows_experience += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em;" >Certified by """ +  experience['issuer']['name'] + """</footer>"""
					else:
						carousel_rows_experience += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em;" >Certified by """ + experience['issuer']['firstname'] + " " +  experience['issuer']['lastname'] + """</footer>"""
					carousel_rows_experience += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['issuer_explore']['workspace_contract'][2:] + """:document:""" + str(experience['doc_id']) + """></a>"""

				carousel_rows_experience += """</figure></div>"""
				if (i+1)%3==0 and (len(experiences)%3!=0 or len(experiences)!=i+1):
					carousel_rows_experience += '</div></div>'
				if i == len(experiences)-1:
					carousel_rows_experience += '</div></div>'

		# recommendation
		recommendations = []
		for certificate in session['issuer_explore']['certificate']:
			if certificate['type'] == "recommendation":
				recommendations.append(certificate)

		carousel_indicators_recommendation = """<li data-target="#recommendation-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_recommendation = ""
		if recommendations == []:
			pass
		else:
			nbr_rows = (len(recommendations)-1)//3
			for i in range(nbr_rows):
				carousel_indicators_recommendation += '<li data-target="#recommendation-carousel" data-slide-to="{}"></li>'.format(i+1)
			for i, recommendation in enumerate(recommendations):

				if recommendation['issuer']['category'] == 1001 :
					issuer_name = recommendation['issuer']['firstname'] + ' ' +recommendation['issuer']['lastname']
				else :
					issuer_name = recommendation['issuer']['name']

				try:
					logo = recommendation['logo']
				except:
					try :
						logo = recommendation['picture']
					except:
						logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'

				if logo :
					if not path.exists(mode.uploads_path + logo) :
						url = 'https://gateway.pinata.cloud/ipfs/'+ logo
						response = requests.get(url, stream=True)
						with open(mode.uploads_path + logo, 'wb') as out_file:
							shutil.copyfileobj(response.raw, out_file)
							del response

				if i%3==0:
					carousel_rows_recommendation += '<div class="carousel-item {a}"><div class="row">'.format(a = "active" if (i == 0) else '')
				carousel_rows_recommendation += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image text-center h-100" style="background-color: white;" ><img src="""
				#image
				try:
					carousel_rows_recommendation +=""""{}" style="height: 200px;" alt="Loading error"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
				except:
					carousel_rows_recommendation +=""""https://s3-us-west-2.amazonaws.com/s.cdpn.io/331810/sample59.jpg" alt="Loading error"/></div><figcaption >"""
				#verified
				carousel_rows_recommendation +="""<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="material-icons my-auto" style="color: rgb(60,158,255);font-size: 50px;">verified_user</i></div>"""
				#header
				carousel_rows_recommendation += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + recommendation.get('title', "") + "</h4></div></div>"
				#body
				carousel_rows_recommendation += """<hr class="my-1"><p style="font-size: 1em"><b>Referent name: </b>""" + issuer_name + "<br>"
				carousel_rows_recommendation += """<b> Relationship: </b>""" + recommendation['relationship'] + "<br>"
				carousel_rows_recommendation += """<b> Description: </b>""" + recommendation['description'][:100]
				if len(recommendation['description'])>100:
					carousel_rows_recommendation += "...<br>"
				else:
					carousel_rows_recommendation += "<br>"

				carousel_rows_recommendation += "</p>"
				#Footer
				carousel_rows_recommendation += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em; color:white;">Certified by """ + issuer_name + """</footer>"""
				#Lien certificates
				carousel_rows_recommendation += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['issuer_explore']['workspace_contract'][2:] + """:document:""" + str(recommendation['doc_id']) + """></a>"""

				carousel_rows_recommendation += """</figure></div>"""
				if (i+1)%3==0 and (len(recommendations)%3!=0 or len(recommendations)!=i+1):
					carousel_rows_recommendation += '</div></div>'
				if i == len(recommendations)-1:
					carousel_rows_recommendation += '</div></div>'

		# Education
		carousel_indicators_education = """<li data-target="#education-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_education = ""
		if session['issuer_explore']['education'] == []:
			pass
		else:
			educations = session['issuer_explore']['education']
			nbr_rows = (len(educations)-1)//3
			for i in range(nbr_rows):
				carousel_indicators_education += '<li data-target="#education-carousel" data-slide-to="{}"></li>'.format(i+1)
			for i, education in enumerate(session['issuer_explore']['education']):
				try:
					logo = education['logo']
				except:
					try :
						logo = education['picture']
					except:
						logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'

				if logo != None:
					if not path.exists(mode.uploads_path + logo) :
						url = 'https://gateway.pinata.cloud/ipfs/'+ logo
						response = requests.get(url, stream=True)
						with open(mode.uploads_path + logo, 'wb') as out_file:
							shutil.copyfileobj(response.raw, out_file)
							del response

				if i%3==0:
					carousel_rows_education += '<div class="carousel-item {a}"><div class="row">'.format(a = "active" if (i == 0) else '')
				carousel_rows_education += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image text-center h-100" style="background-color: white;" ><img src="""
				#image
				try:
					carousel_rows_education +=""""{}" style="height: 200px;" alt="Loading error"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
				except:
					carousel_rows_education +=""""https://s3-us-west-2.amazonaws.com/s.cdpn.io/331810/sample59.jpg" alt="Loading error"/></div><figcaption >"""
				#verified
				carousel_rows_education +="""<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="fa fa-pencil-square-o" style="color: #747474;font-size: 50px;"></i></div>"""
				#header
				carousel_rows_education += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + education['title'] + "</h4></div></div>"
				#body
				carousel_rows_education += """<hr class="my-1"><p style="font-size: 1em"><b>Name: </b>""" + education['organization']['name'] + '<br>'

				carousel_rows_education += """<b>Start Date</b> : """ + education['start_date'] + """<br> """
				carousel_rows_education += """<b>End Date</b> : """ + education['end_date'] + """<br>"""

				carousel_rows_education += "</p>"
				#Footer
				carousel_rows_education += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
				#Lien certificates
				carousel_rows_education += """<a href=  /certificate/?certificate_id="""+education['id'] + """:education></a>"""

				carousel_rows_education += """</figure></div>"""
				if (i+1)%3==0 and (len(educations)%3!=0 or len(educations)!=i+1):
					carousel_rows_education += '</div></div>'
				if i == len(educations)-1:
					carousel_rows_education += '</div></div>'

		# Skills
		skills = []
		for certificate in session['issuer_explore']['certificate']:
			if certificate['type'] == "skill":
				skills.append(certificate)

		carousel_indicators_skill = """<li data-target="#skill-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_skill = ""
		if skills == []:
			if session['issuer_explore']['skills'] == None:
				pass
			else:
				if session['issuer_explore']['skills']['description'] != None:
					carousel_rows_skill += '<div class="carousel-item active"><div class="row">'
					carousel_rows_skill += """<div class="col-md-4 mb-2">
							<figure class="snip1253 mw-100" style="height: 410px; ">
							  <div class="image text-center h-100" style="background-color: white;"><img src="/uploads/QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT" style="height: 200px;" alt="Loading error" /></div>
							  <figcaption class="p-0">
								<div class="row overflow-hidden" style="flex-direction: row;height: 50px">
								  <div class="col bg-transparent px-2" style="max-width:60px;"><i class="fa fa-pencil-square-o" style="color: #747474;font-size: 50px;"></i></div>
								  <div class='col px-0 my-auto'>
									<h4 class='align-center' style='color: black;font-size: 1.4em'>Self claimed skills</h4>
								  </div>
								</div>
								<hr class="my-1">
								<p class="text-center" style="font-size: 1em;">"""
					for i, skill in enumerate(session['issuer_explore']['skills']['description']) :
						if i<4:
							carousel_rows_skill += skill['skill_name'] + "<br>"
						elif i==4:
							carousel_rows_skill += ""
					carousel_rows_skill += """</p></figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
					carousel_rows_skill += """<a href=  /data/?dataId="""+ session['issuer_explore']['skills']['id'] + """:skills></a>"""
					carousel_rows_skill += """</figure></div>"""
					carousel_rows_skill += '</div></div>'
		else:
			nbr_rows = (len(skills)-1)//3
			for i in range(nbr_rows):
				carousel_indicators_skill += '<li data-target="#skill-carousel" data-slide-to="{}"></li>'.format(i+1)
			for i, skill in enumerate(skills):
				try:
					logo = skill['logo']
				except:
					logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'

				if logo != None:
					if not path.exists(mode.uploads_path + logo) :
						url = 'https://gateway.pinata.cloud/ipfs/'+ logo
						response = requests.get(url, stream=True)
						with open(mode.uploads_path + logo, 'wb') as out_file:
							shutil.copyfileobj(response.raw, out_file)
							del response

				if i%3==0:
					carousel_rows_skill += '<div class="carousel-item {a}"><div class="row">'.format(a = "active" if (i == 0) else '')
				carousel_rows_skill += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image text-center h-100" style="background-color: white;" ><img src="""
				#image
				try:
					carousel_rows_skill +=""""{}" style="height: 200px;" alt="Loading error"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
				except:
					carousel_rows_skill +=""""https://s3-us-west-2.amazonaws.com/s.cdpn.io/331810/sample59.jpg" alt="Loading error"/></div><figcaption >"""
				#verified
				carousel_rows_skill +="""<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="material-icons my-auto" style="color: rgb(60,158,255);font-size: 50px;">verified_user</i></div>"""
				#header
				carousel_rows_skill += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + skill['title'] + "</h4></div></div>"
				#body
				carousel_rows_skill += """<hr class="my-1"><p class="text-center" style="font-size: 1em;">"""

				lines = skill['description'].split("\n")
				for l in lines:
					carousel_rows_skill +=  l.strip("\r") + "<br>"

				carousel_rows_skill += "</p>"
				#Footer
				if skill['issuer']['category']==2001:
					carousel_rows_skill += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em;" >Certified by """ +  skill['issuer']['name'] + """</footer>"""
				else:
					carousel_rows_skill += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em;" >Certified by """ + skill['issuer']['firstname'] + " " +  skill['issuer']['lastname'] + """</footer>"""
				#Lien certificates
				carousel_rows_skill += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['issuer_explore']['workspace_contract'][2:] + """:document:""" + str(skill['doc_id']) + """></a>"""

				carousel_rows_skill += """</figure></div>"""
				if (i+1)%3==0 and (len(skills)%3!=0 or len(skills)!=i+1):
					carousel_rows_skill += '</div></div>'
				if i == len(skills)-1:
					created_row = False
					if (i+1)%3==0:
						carousel_rows_skill += '<div class="carousel-item"><div class="row">'
						created_row = True
					carousel_rows_skill += """<div class="col-md-4 mb-2">
							<figure class="snip1253 mw-100" style="height: 410px; ">
							  <div class="image text-center h-100" style="background-color: white;"><img src="/uploads/QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT" style="height: 200px;" alt="Loading error" /></div>
							  <figcaption class="p-0">
								<div class="row overflow-hidden" style="flex-direction: row;height: 50px">
								  <div class="col bg-transparent px-2" style="max-width:60px;"><i class="fa fa-pencil-square-o" style="color: #747474;font-size: 50px;"></i></div>
								  <div class='col px-0 my-auto'>
									<h4 class='align-center' style='color: black;font-size: 1.4em'>Self claimed skills</h4>
								  </div>
								</div>
								<hr class="my-1">
								<p class="text-center" style="font-size: 1em;">"""
					for i, skill in enumerate(session['issuer_explore']['skills']['description']) :
						if i<4:
							carousel_rows_skill += skill['skill_name'] + "<br>"
						elif i==4:
							carousel_rows_skill += "..."
					carousel_rows_skill += """</p></figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
					carousel_rows_skill += """<a href=  /data/?dataId="""+ session['issuer_explore']['skills']['id'] + """:skills></a>"""
					carousel_rows_skill += """</figure></div>"""

					if created_row:
						carousel_rows_skill += '</div></div>'
					carousel_rows_skill += '</div></div>'
		#Services
		if session['type'] == 'person' :
			referent_list =  is_username_in_list(session['issuer'], issuer_username)
			white_list =  is_username_in_list(session['whitelist'], issuer_username)
			# est ce qu il est dans ma partnership list
			partner_list =  is_username_in_list_for_partnership(session['partner'], issuer_username)
			# est ce que je suis dans l'issuer list de ce Talent ?
			in_referent_list = is_username_in_list(session['issuer_explore']['issuer_keys'], session['username'])

		is_manager = False
		if session['type'] == 'company' :
			host_name = session['username'] if len(session['username'].split('.')) == 1 else session['username'].split('.')[1]
			referent_list =  is_username_in_list(session['issuer'], issuer_username)
			white_list =  is_username_in_list(session['whitelist'], issuer_username)
			is_manager = ns.does_manager_exist(issuer_username, host_name, mode)
			in_referent_list = is_username_in_list(session['issuer_explore']['issuer_keys'], host_name)
			partner_list = not is_username_in_list_for_partnership(session['partner'], issuer_username)

		#kyc Digital Identity
		kyc = session['issuer_explore']['kyc'] and session['issuer_explore']['kyc'][0]['claim_id']

		# personal details
		adress = session['issuer_explore']['personal']['postal_address']['claim_value']
		phone = session['issuer_explore']['personal']['contact_phone']['claim_value']
		email = session['issuer_explore']['personal']['contact_email']['claim_value']
		birth_date = session['issuer_explore']['personal']['birthdate']['claim_value']
		education = session['issuer_explore']['personal']['education']['claim_value']
		about = session['issuer_explore']['personal']['about']['claim_value']
		return render_template('./person_issuer_identity.html',
							**session['menu'],
							issuer_name=session['issuer_explore']['name'],
							issuer_address=session['issuer_explore']['address'],
							issuer_username = issuer_username,
							issuer_profil_title = session['issuer_explore']['profil_title'],
							issuer_picturefile=session['issuer_explore']['picture'],
							digitalvault=my_file, adress = adress, phone = phone,
							email = email, birth_date = birth_date, education = education,
							about = about, kyc = kyc, user_type = session['type'],
							referent_list = referent_list,white_list = white_list, partner_list = partner_list,
							in_referent_list = in_referent_list, is_manager = is_manager,
							carousel_indicators_experience=carousel_indicators_experience,
							carousel_indicators_recommendation=carousel_indicators_recommendation,
							carousel_indicators_education=carousel_indicators_education,
							carousel_indicators_skill=carousel_indicators_skill,
							carousel_rows_experience=carousel_rows_experience,
							carousel_rows_recommendation=carousel_rows_recommendation,
							carousel_rows_education=carousel_rows_education,
							carousel_rows_skill=carousel_rows_skill)


	if session['issuer_explore']['type'] == 'company' :

		# file
		if session['issuer_explore']['identity_file'] == []:
			my_file = """<a class="text-info">No Files available</a>"""
		else:
			my_file = ""
			is_encrypted = False
			for one_file in session['issuer_explore']['identity_file']:
				if one_file.get('content') == 'Encrypted':
					is_encrypted = True
					file_html = """
					<b>File Name</b> : """ + one_file['filename'] + """ ( """ + 'Not available - Encrypted ' + """ ) <br>
					<b>Created</b> : """ + one_file['created'] + """<br>"""
				else:
					file_html = """
					<b>File Name</b> : """ + one_file['filename'] + """ ( """ + one_file['privacy'] + """ ) <br>
					<b>Created</b> : """ + one_file['created'] + """<br>
					<a class="text-secondary" href=/user/download/?filename=""" + one_file['filename'] + """>
						<i data-toggle="tooltip" class="fa fa-download" title="Download"></i>
					</a>"""
				my_file = my_file + file_html + """<br>"""

		agreements = []
		for certificate in session['issuer_explore']['certificate']:
			if certificate['type'] == "agreement" or certificate['type'] == "agrement":
				agreements.append(certificate)
		carousel_indicators_agreement = """<li data-target="#agreement-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_agreement = ""
		if agreements == []:
			pass
		else:
			nbr_rows = (len(agreements)-1)//3
			for i in range(nbr_rows):
				carousel_indicators_agreement += '<li data-target="#agreement-carousel" data-slide-to="{}"></li>'.format(i+1)
			for i, agreement in enumerate(agreements):
				try:
					logo = agreement['issued_by']['logo']
				except:
					logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'

				if logo != None:
					if not path.exists(mode.uploads_path + logo) :
						url = 'https://gateway.pinata.cloud/ipfs/'+ logo
						response = requests.get(url, stream=True)
						with open(mode.uploads_path + logo, 'wb') as out_file:
							shutil.copyfileobj(response.raw, out_file)
							del response

				if i%3==0:
					carousel_rows_agreement += '<div class="carousel-item {a}"><div class="row">'.format(a = "active" if (i == 0) else '')
				carousel_rows_agreement += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image p-2 text-center h-100" style="background-color: white;" ><img src="""
				#image
				try:
					carousel_rows_agreement +=""""{}" style="height: 180px;" alt="Loading error"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
				except:
					carousel_rows_agreement +=""""https://s3-us-west-2.amazonaws.com/s.cdpn.io/331810/sample59.jpg" alt="Loading error"/></div><figcaption >"""
				#verified
				carousel_rows_agreement += """<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="material-icons my-auto" style="color: rgb(60,158,255);font-size: 50px;">verified_user</i></div>"""
				#header
				carousel_rows_agreement += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + agreement['title'] + "</h4></div></div>"
				#body
				carousel_rows_agreement += """<hr class="my-1"><p class="my-0" style="font-size: 1em"><b>Issuer Name: </b>""" + agreement['issuer']['name'] + '<br>'

				carousel_rows_agreement += """<b>Issue date</b> : """ + agreement['date_of_issue'] + """<br> """
				carousel_rows_agreement += """<b>End of validity date</b> : """ + agreement['valid_until'] + """<br>"""

				carousel_rows_agreement += """<b> Description: </b>""" + agreement['description'][:150]
				if len(agreement['description'])>150:
					carousel_rows_agreement += "...<br>"
				else:
					carousel_rows_agreement += "<br>"
				carousel_rows_agreement += "</p>"
				#Footer
				carousel_rows_agreement += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em;" >Certified by """ +  agreement['issuer']['name'] + """</footer>"""
				#Lien certificates
				carousel_rows_agreement += """<a href=  /certificate/?certificate_id="""+agreement['id'] + """></a>"""

				carousel_rows_agreement += """</figure></div>"""
				if (i+1)%3==0 and len(agreements)%3!=0:
					carousel_rows_agreement += '</div></div>'
				if i == len(agreements)-1:
					carousel_rows_agreement += '</div></div>'

		references = []
		for certificate in session['issuer_explore']['certificate']:
			if certificate['type'] == "reference":
				references.append(certificate)
		carousel_indicators_reference = """<li data-target="#reference-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_reference = ""
		if references == []:
			pass
		else:
			nbr_rows = (len(references)-1)//3
			for i in range(nbr_rows):
				carousel_indicators_reference += '<li data-target="#reference-carousel" data-slide-to="{}"></li>'.format(i+1)
			for i, reference in enumerate(references):
				try:
					logo = reference['issued_by']['logo']
				except:
					logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'

				if logo != None:
					if not path.exists(mode.uploads_path + logo) :
						url = 'https://gateway.pinata.cloud/ipfs/'+ logo
						response = requests.get(url, stream=True)
						with open(mode.uploads_path + logo, 'wb') as out_file:
							shutil.copyfileobj(response.raw, out_file)
							del response

				if i%3==0:
					carousel_rows_reference += '<div class="carousel-item {a}"><div class="row">'.format(a = "active" if (i == 0) else '')
				carousel_rows_reference += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image text-center h-100" style="background-color: white;" ><img src="""
				#image
				try:
					carousel_rows_reference +=""""{}" style="height: 200px;" alt="Loading error"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
				except:
					carousel_rows_reference +=""""https://s3-us-west-2.amazonaws.com/s.cdpn.io/331810/sample59.jpg" alt="Loading error"/></div><figcaption >"""
				#verified
				carousel_rows_reference += """<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="material-icons my-auto" style="color: rgb(60,158,255);font-size: 50px;">verified_user</i></div>"""
				#header
				carousel_rows_reference += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + reference.get('project_title', "") + "</h4></div></div>"
				#body
				carousel_rows_reference += """<hr class="my-1"><p class="my-0" style="font-size: 1em"><b>Issuer Name: </b>""" + reference['issuer']['name'] + '<br>'

				carousel_rows_reference += """<b>Start date</b> : """ + reference['start_date'] + """<b>	End date</b> : """ + reference['end_date'] + """<br> """
				carousel_rows_reference += """<b>Project Budget</b> : """ + reference.get('project_budget', "") + """<br> """

				carousel_rows_reference += """<b> Description: </b>""" + reference.get('project_description', "")[:150]
				if len(reference.get('project_description', ""))>150:
					carousel_rows_reference += "...<br>"
				else:
					carousel_rows_reference += "<br>"
				carousel_rows_reference += "</p>"
				#Footer
				carousel_rows_reference += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em;" >Certified by """ + reference['issuer']['name'] + """</footer>"""
				#Lien certificates
				carousel_rows_reference += """<a href=  /certificate/?certificate_id="""+reference['id'] + """></a>"""

				carousel_rows_reference += """</figure></div>"""
				if (i+1)%3==0 and len(references)%3!=0:
					carousel_rows_reference += '</div></div>'
				if i == len(references)-1:
					carousel_rows_reference += '</div></div>'
		#Services
		referent_list = False
		white_list = False
		partner_list = False
		in_referent_list = False
		if session['type'] == 'person' :
			referent_list =  is_username_in_list(session['issuer'], issuer_username)
			white_list =  is_username_in_list(session['whitelist'], issuer_username)
			# est ce qu il est dans ma partnership list
			partner_list =  is_username_in_list_for_partnership(session['partner'], issuer_username)
			# est ce que je suis dans l'issuer list de ce Talent ?
			in_referent_list = is_username_in_list(session['issuer_explore']['issuer_keys'], session['username'])

		if session['type'] == 'company' :
			host_name = session['username'] if len(session['username'].split('.')) == 1 else session['username'].split('.')[1]
			referent_list =  is_username_in_list(session['issuer'], issuer_username)
			white_list =  is_username_in_list(session['whitelist'], issuer_username)
			in_referent_list = is_username_in_list(session['issuer_explore']['issuer_keys'], host_name)
			partner_list = is_username_in_list_for_partnership(session['partner'], issuer_username)




		#kyc
		kyc = False
		user_type = session['type']
		contact_name = session['issuer_explore']['personal']['contact_name']['claim_value']
		contact_email = session['issuer_explore']['personal']['contact_email']['claim_value']
		contact_phone = session['issuer_explore']['personal']['contact_phone']['claim_value']
		website = session['issuer_explore']['personal']['website']['claim_value']
		about = session['issuer_explore']['personal']['about']['claim_value']
		staff = session['issuer_explore']['personal']['staff']['claim_value']
		siren = session['issuer_explore']['personal']['siren']['claim_value']
		try:
			sales = "{:,}".format(int(session['issuer_explore']['personal']['sales']['claim_value'])).replace(',', ' ')
		except:
			sales = session['issuer_explore']['personal']['sales']['claim_value']

		if session['issuer_explore']['skills'] is None or session['issuer_explore']['skills'].get('id') is None :
			my_competencies =  """<p class="text-center text-muted m-0 " style="font-size: 20px;">No data available</p>"""
		else:
			my_competencies = ""
			for competencie in session['issuer_explore']['skills']['description'] :
				competencie_html = competencie['skill_name'] + """<br>"""
				my_competencies = my_competencies + competencie_html
			my_competencies = my_competencies + """
				<p>
					<a class="text-secondary" href=/data/?dataId="""+ session['issuer_explore']['skills']['id'] + """:skills>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""
		return render_template('./company_issuer_identity.html',
							**session['menu'],
							issuer_name=session['issuer_explore']['name'],
							issuer_address=session['issuer_explore']['address'],
							issuer_username = issuer_username, user_type = user_type,
							issuer_picturefile=session['issuer_explore']['picture'],
							contact_name = contact_name, contact_email = contact_email, contact_phone = contact_phone,
							website = website,about = about, staff = staff, sales = sales, siren = siren,
							digitalvault=my_file, kyc = kyc,
							referent_list = referent_list,white_list = white_list, partner_list = partner_list,
							in_referent_list = in_referent_list,
							carousel_indicators_agreement=carousel_indicators_agreement,
							carousel_rows_agreement=carousel_rows_agreement,
							carousel_indicators_reference=carousel_indicators_reference,
							carousel_rows_reference=carousel_rows_reference,
							competencies = my_competencies)
