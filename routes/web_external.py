from os import path
from flask import request, render_template,abort
import requests
import shutil
import json
import time
import logging
logging.basicConfig(level=logging.INFO)

# dependances
from protocol import Identity

#@app.route('/resume/', methods=['GET'])
def resume(mode) :
	"""
	Public resume available for all
	This is always an external an external entry point
	Flask session is clear
	we load the Identity from blockchain
	"""
	try :
		workspace_contract = '0x' + request.args.get('did').split(':')[3]
		issuer_explore = Identity(workspace_contract, mode)
	except :
		logging.error('wrong did as person')
		abort(403)

	if issuer_explore.type == 'person' :
		"""
		session['resume']= issuer_explore.__dict__
		del session['resume']['file_list']
		del session['resume']['experience_list']
		del session['resume']['education_list']
		del session['resume']['other_list']
		del session['resume']['certificate_list']
		del session['resume']['partners']
		del session['resume']['authenticated']
		del session['resume']['rsa_key']
		del session['resume']['relay_activated']
		del session['resume']['private_key']
		session['resume']['topic'] = 'resume'
		"""
		# file
		if not issuer_explore.identity_file :
			my_file = """<p class="text-center text-muted m-0 " style="font-size: 20px;">No data available</p>"""
		else:
			my_file = ""
			for one_file in issuer_explore.identity_file:
				if one_file.get('content') != 'Encrypted':
					file_html = """
					<b>File Name</b> : """ + one_file['filename'] + """ ( """ + one_file['privacy'] + """ ) <br>
					<b>Created</b> : """ + one_file['created'] + """<br>
					<a class="text-secondary" href=/user/download/?filename=""" + one_file['filename'] + """>
						<i data-toggle="tooltip" class="fa fa-download" title="Download"></i>
					</a>"""
					my_file += file_html + """<br>"""

		# experience
		experiences = []
		for experience in issuer_explore.certificate:
			if experience['credentialSubject']['credentialCategory'] =='experience':
				experiences.append(experience)
		for experience in issuer_explore.experience:
			experiences.append(experience)

		# tri par date
		for i, experience in enumerate(experiences):
			min = i
			try :
				DTmin = time.strptime(experience['start_date'], "%Y-%m-%d")
			except :
				DTmin = time.strptime(experience['credentialSubject']['startDate'], "%Y-%m-%d")
			for j, certi in enumerate(experiences[i::]):
				try :
					DTcerti = time.strptime(certi['start_date'], "%Y-%m-%d")
				except :
					DTcerti = time.strptime(certi['credentialSubject']['startDate'], "%Y-%m-%d")
				if DTcerti < DTmin:
					min = j + i
					DTmin = DTcerti
			experiences[i] , experiences[min] = experiences[min], experiences[i]
		experiences = experiences[::-1]

		carousel_indicators_experience = """<li data-target="#experience-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_experience = ""
		if not experiences :
			pass
		else :
			nbr_rows = (len(experiences)-1)//3
			for i in range(nbr_rows):
				carousel_indicators_experience += '<li data-target="#experience-carousel" data-slide-to="{}"></li>'.format(i+1)
			for i, experience in enumerate(experiences):
				try:
					logo = experience['credentialSubject']['companyLogo']
					startDate = experience['credentialSubject']['startDate']
					endDate = experience['credentialSubject']['endDate']
					description = experience['credentialSubject']['description']
					title = experience['credentialSubject']['title']
					issuer_name = experience['credentialSubject']['companyName']

				# for self claims
				except:
					logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'
					startDate = experience['start_date']
					endDate = experience['end_date'] if experience['end_date'] else "Current"
					description = experience['description']
					title = experience['title']
					issuer_name = ""

				if logo :
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
				if experience.get('topic') != 'certificate':
					carousel_rows_experience += """<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="fa fa-pencil-square-o" style="color: #747474;font-size: 50px;"></i></div>"""
				else:
					carousel_rows_experience += """<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="material-icons my-auto" style="color: rgb(60,158,255);font-size: 50px;">verified_user</i></div>"""
				#header
				carousel_rows_experience += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + title + "</h4></div></div><hr class='my-1'>"
				#body
				if experience.get('topic') == 'certificate':
					carousel_rows_experience += """<p style="font-size: 1em"><b>Issuer name : </b>""" + issuer_name + """<br>"""
				else :
					carousel_rows_experience += """<p style="font-size: 1em"><b>Company name : </b>""" + experience['company']['name'] + """<br>"""

				carousel_rows_experience += """<b>Start Date</b> : """ + startDate + """<br> """
				carousel_rows_experience += """<b>End Date</b> : """ + endDate + """<br>"""
				if experience.get('topic') != 'experience':
					carousel_rows_experience += """<b>Description</b> : """ + description[:100:]
					if len(description) > 100:
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
				if experience.get('topic') != 'certificate':
					carousel_rows_experience += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
					#carousel_rows_experience += """<a href= /certificate/?certificate_id=""" + experience['id'] + """:experience> </a>"""
				else:
					carousel_rows_experience += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em;" >Certified by """ +  issuer_name + """</footer>"""
					carousel_rows_experience += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer_explore.workspace_contract[2:] + """:document:""" + str(experience['doc_id']) + """></a>"""

				#Lien experiences
				#carousel_rows_experience += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer_explore.workspace_contract[2:] + """:document:""" + str(experience['doc_id']) + """></a>"""

				carousel_rows_experience += """</figure></div>"""
				if (i+1)%3 == 0 and (len(experiences)%3!=0 or len(experiences)!=i+1):
					carousel_rows_experience += '</div></div>'
				if i == len(experiences)-1:
					carousel_rows_experience += '</div></div>'

		# recommendation
		recommendations = []
		for certificate in issuer_explore.certificate:
			if certificate['type'] == "recommendation":
				recommendations.append(certificate)

		carousel_indicators_recommendation = """<li data-target="#recommendation-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_recommendation = ""
		if not recommendations :
			pass
		else:
			nbr_rows = (len(recommendations)-1)//3
			for i in range(nbr_rows):
				carousel_indicators_recommendation += '<li data-target="#recommendation-carousel" data-slide-to="{}"></li>'.format(i+1)
			for i, recommendation in enumerate(recommendations):

				if recommendation['issuer']['type'] == 2001:
					name = recommendation['issuer']['name']
				else :
					name = recommendation['issuer']['firstname'] + " " + recommendation['issuer']['lastname']

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

				carousel_rows_recommendation += """<hr class="my-1"><p style="font-size: 1em"><b>Referent name: </b>""" + name + "<br>"
				carousel_rows_recommendation += """<b> Relationship: </b>""" + recommendation.get('relationship', '') + "<br>"
				carousel_rows_recommendation += """<b> Description: </b>""" + recommendation['description'][:150]
				if len(recommendation['description'])>150:
					carousel_rows_recommendation += "...<br>"
				else:
					carousel_rows_recommendation += "<br>"

				carousel_rows_recommendation += "</p>"
				#Footer
				carousel_rows_recommendation += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em; color:white;">Certified by """ + name + """</footer>"""
				#Lien certificates
				carousel_rows_recommendation += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer_explore.workspace_contract[2:] + """:document:""" + str(recommendation['doc_id']) + """></a>"""

				carousel_rows_recommendation += """</figure></div>"""
				if (i+1)%3==0 and (len(recommendations)%3!=0 or len(recommendations)!=i+1):
					carousel_rows_recommendation += '</div></div>'
				if i == len(recommendations)-1:
					carousel_rows_recommendation += '</div></div>'

		# education
		carousel_indicators_education = """<li data-target="#education-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_education = ""
		if not issuer_explore.education :
			pass
		else:
			educations = issuer_explore.education
			nbr_rows = (len(educations)-1)//3
			for i in range(nbr_rows):
				carousel_indicators_education += '<li data-target="#education-carousel" data-slide-to="{}"></li>'.format(i+1)
			for i, education in enumerate(issuer_explore.education):
				try:
					logo = education['logo']
				except:
					try :
						logo = education['picture']
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
				carousel_rows_education += """<hr class="my-1"><p style="font-size: 1em"><b>Name : </b>""" + education['organization']['name'] + '<br>'
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

		# skills
		skills = []
		for certificate in issuer_explore.certificate:
			if certificate['type'] == "skill":
				skills.append(certificate)

		carousel_indicators_skill = """<li data-target="#skill-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_skill = ""
		if not skills :
			if issuer_explore.skills  and issuer_explore.skills['description'] :
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
				for i, skill in enumerate(issuer_explore.skills['description']) :
					if i<4:
						carousel_rows_skill += skill['skill_name'] + "<br>"
					elif i==4:
						carousel_rows_skill += ""
				carousel_rows_skill += """</p></figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
				#carousel_rows_skill += """<a href=/certificate/?certificate_id="""+ issuer_explore.skills['id'] + """:skills></a>"""
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

				if logo :
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
				if skill['issuer']['type']== 'company':
					carousel_rows_skill += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em;" >Certified by """ +  skill['issuer']['name'] + """</footer>"""
				else:
					carousel_rows_skill += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em;" >Certified by """ + skill['issuer']['firstname'] + " " +  skill['issuer']['lastname'] + """</footer>"""
				#carousel_rows_skill += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer_explore.workspace_contract[2:] + """:document:""" + str(skill['doc_id']) + """></a>"""

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
					for i, skill in enumerate(issuer_explore.skills['description']) :
						if i<4:
							carousel_rows_skill += skill['skill_name'] + "<br>"
						elif i==4:
							carousel_rows_skill += "..."
					carousel_rows_skill += """</p></figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
					carousel_rows_skill += """<a href= /certificate/?certificate_id="""+ issuer_explore.skills['id'] + """:skills></a>"""
					carousel_rows_skill += """</figure></div>"""

					if created_row:
						carousel_rows_skill += '</div></div>'
					carousel_rows_skill += '</div></div>'
		adress = issuer_explore.personal['postal_address']['claim_value']
		phone = issuer_explore.personal['contact_phone']['claim_value']
		email = issuer_explore.personal['contact_email']['claim_value']
		birth_date = issuer_explore.personal['birthdate']['claim_value']
		education = issuer_explore.personal['education']['claim_value']
		about = issuer_explore.personal['about']['claim_value']
		return render_template('./CV_blockchain.html',
							issuer_name=issuer_explore.name,
							issuer_profil_title = issuer_explore.profil_title,
							issuer_picturefile=issuer_explore.picture,
							digitalvault=my_file,
							adress = adress,
							phone = phone,
							email = email,
							birth_date = birth_date,
							education = education,
							about = about,
							carousel_indicators_experience=carousel_indicators_experience,
							carousel_indicators_recommendation=carousel_indicators_recommendation,
							carousel_indicators_education=carousel_indicators_education,
							carousel_indicators_skill=carousel_indicators_skill,
							carousel_rows_experience=carousel_rows_experience,
							carousel_rows_recommendation=carousel_rows_recommendation,
							carousel_rows_education=carousel_rows_education,
							carousel_rows_skill=carousel_rows_skill)
	else:
		logging.error('resume entry with category company')
		abort(403)


def board(mode):
	""" company registry
	route # /board and /company/registry/

	"""
	try :
		workspace_contract = '0x' + request.args.get('did').split(':')[3]
		issuer_explore = Identity(workspace_contract, mode)
	except :
		logging.error('wrong did as company ')
		abort(403)

	if issuer_explore.type == 'company' :
		"""
		session['resume']= issuer_explore.__dict__
		del session['resume']['file_list']
		del session['resume']['experience_list']
		del session['resume']['education_list']
		del session['resume']['other_list']
		del session['resume']['certificate_list']
		del session['resume']['partners']
		del session['resume']['authenticated']
		del session['resume']['rsa_key']
		del session['resume']['relay_activated']
		del session['resume']['private_key']
		session['resume']['topic'] = 'resume'
		"""
		contact_name = issuer_explore.personal['contact_name']['claim_value']
		contact_email = issuer_explore.personal['contact_email']['claim_value']
		contact_phone = issuer_explore.personal['contact_phone']['claim_value']
		website = issuer_explore.personal['website']['claim_value']
		about = issuer_explore.personal['about']['claim_value']
		staff = issuer_explore.personal['staff']['claim_value']
		siren = issuer_explore.personal['siren']['claim_value']
		try:
			sales = "{:,}".format(int(issuer_explore.personal['sales']['claim_value'])).replace(',', ' ')
		except:
			sales = issuer_explore.personal['sales']['claim_value']

		agreements = []
		for certificate in issuer_explore.certificate:
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

				if logo :
					if not path.exists(mode.uploads_path + logo) :
						url = 'https://gateway.pinata.cloud/ipfs/'+ logo
						response = requests.get(url, stream=True)
						with open(mode.uploads_path + logo, 'wb') as out_file:
							shutil.copyfileobj(response.raw, out_file)
							del response

				if i%3==0:
					carousel_rows_agreement += '<div class="carousel-item {a}"><div class="row">'.format(a = "active" if (i == 0) else '')
				carousel_rows_agreement += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image text-center h-100" style="background-color: white;" ><img src="""
				#image
				try:
					carousel_rows_agreement +=""""{}" style="height: 200px;" alt="Loading error"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
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
		for certificate in issuer_explore.certificate :
			if certificate['credentialSubject']['credentialCategory'] =='reference':
				references.append(certificate)
		carousel_indicators_reference = """<li data-target="#reference-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
		carousel_rows_reference = ""
		if not references :
			pass
		else:
			nbr_rows = (len(references)-1)//3
			for i in range(nbr_rows):
				carousel_indicators_reference += '<li data-target="#reference-carousel" data-slide-to="{}"></li>'.format(i+1)
			for i, reference in enumerate(references):
				logo = reference['credentialSubject']['companyLogo']
				startDate = reference['credentialSubject']['offers']['startDate']
				endDate = reference['credentialSubject']['offers']['endDate']
				description = reference['credentialSubject']['offers']['description']
				title = reference['credentialSubject']['offers']['title']
				issuer_name = reference['credentialSubject']['companyName']
				budget = reference['credentialSubject']['offers']['price']

				if not logo :
					logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'

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
				carousel_rows_reference += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + title + "</h4></div></div>"
				#body
				carousel_rows_reference += """<hr class="my-1"><p class="my-0" style="font-size: 1em"><b>Issuer Name: </b>""" + issuer_name + '<br>'

				carousel_rows_reference += """<b>Start date</b> : """ + startDate + """<b>	End date</b> : """ + endDate + """<br> """
				carousel_rows_reference += """<b>Project Budget</b> : """ + budget + """<br> """

				carousel_rows_reference += """<b> Description: </b>""" + description[:150]
				if len(description)>150:
					carousel_rows_reference += "...<br>"
				else:
					carousel_rows_reference += "<br>"
				carousel_rows_reference += "</p>"
				#Footer
				carousel_rows_reference += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #3c9eff; text-align:center;font-size: 1em;" >Certified by """ + issuer_name + """</footer>"""
				#Lien certificates
				carousel_rows_reference += """<a href=  /certificate/?certificate_id="""+reference['id'] + """></a>"""

				carousel_rows_reference += """</figure></div>"""
				if (i+1)%3==0 and len(references)%3!=0:
					carousel_rows_reference += '</div></div>'
				if i == len(references)-1:
					carousel_rows_reference += '</div></div>'

		if issuer_explore.skills is None or issuer_explore.skills.get('id') is None :
			my_competencies =  """<p class="text-center text-muted m-0 " style="font-size: 20px;">No data available</p>"""
		else:
			my_competencies = ""
			for competencie in issuer_explore.skills['description'] :
				competencie_html = competencie['skill_name'] + """<br>"""
				my_competencies = my_competencies + competencie_html
			my_competencies = my_competencies + """
				<p>
					<a class="text-secondary" href=/data/?dataId="""+ issuer_explore.skills['id'] + """:skills>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
					</a>
				</p>"""


		return render_template('./company_ext.html',
							issuer_name = issuer_explore.name,
							contact_name = contact_name,
							contact_email = contact_email,
							contact_phone = contact_phone,
							website = website,
							about = about,
							staff = staff,
							sales = sales,
							siren = siren,
							issuer_logo = issuer_explore.picture,
							carousel_indicators_agreement=carousel_indicators_agreement,
							carousel_rows_agreement=carousel_rows_agreement,
							carousel_indicators_reference=carousel_indicators_reference,
							carousel_rows_reference=carousel_rows_reference,
                            competencies = my_competencies,
							)
	else:
		logging.error('board entry with category person')
		abort(403)
