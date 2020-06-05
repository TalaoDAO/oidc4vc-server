

		
#############################################################
#    affichage d'un certificat de type claim
#############################################################
#data='did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:b34c2a6837a9e89da5ef886d18763fb13a12615814d50a5b73ae403cb547d788'
#data="did:talao:rinkeby:ab6d2bAE5ca59E4f5f729b7275786979B17d224b:claim:abf370997a7b240f56c62b8b33cc8976f9808d3889f3eed865c79e4622d90af4"


from flask import request, redirect, render_template
from flask_api import FlaskAPI
import random
import ipfshttpclient
from flask_fontawesome import FontAwesome

# dependances
import Talao_message
import createidentity
from protocol import canRegister_email
from protocol import Certificate
import environment
import constante

# environment setup
mode=environment.currentMode()
w3=mode.w3

# get ipfs data
def getclaimipfs (claim_id, workspace_contract) :
	
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	contract=w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	claimdata=contract.functions.getClaim(claim_id).call()
	if claimdata[5]!="" :
		data=client.get_json(claimdata[5])
		return data
	else :
		return False

# fonction appelée par la route app.add_url_rule('/certificate/<data>',  view_func=web_show_certificate.show_certificate)
# display experience certificate for anybody. Stand alone routine
def show_certificate(data):

	doc_id = data.split(':')[5]
	identity_workspace_contract = '0x'+data.split(':')[3]
	certificate = Certificate()
	download = certificate.relay_get_certificate(self, identity_workspace_contract, doc_id, mode)
	
	if not download :
		return {"ERROR" : "No Certificate"}
	
	ok="color: rgb(251,211,5); font-size: 10px;"
	ko="color: rgb(0,0,0);font-size: 10px;"
	
	# gestion des "fa-star" 
	score=[]
	score.append(certificate["score_recommendation"])
	score.append(certificate["score_delivery"])
	score.append(certificate["score_schedule"])
	score.append(certificate["score_communication"])
	for q in range(0,4) :
		for i in range(0,score[q]) :
			context["star"+str(q)+str(i)]=ok
		for i in range(score[q],5) :
			context ["star"+str(q)+str(i)]=ko

	return render_template('certificate.html',
							manager= certificate.manager,
							title = certificate.title,
							description=certificate.description,
							firstname=certificate.firstname,
							lastname=certificate.lastname,
							signature=certificate.signature,
							logo=certificate.logo,
							**context)


#         verify certificate
#@app.route('/certificate/verify/<dataId>', methods=['GET'])
def certificate_verify(dataId) :
	workspace_contract = '0x'+dataId.split(':')[3]
	
	doc_id = data.split(':')[5]
	identity_workspace_contract = '0x'+data.split(':')[3]
	certificate = Certificate()
	download = certificate.relay_get_certificate(self, identity_workspace_contract, doc_id, mode)
	
	his_topic = his_data.topic.capitalize()	
	his_visibility = his_data.encrypted.capitalize()
	
	# issuer
	his_issuer = """
				<span>
				<b>Name</b> : """ + his_data.issuer_name + """<br>
				<b>Username</b> : """ + his_data.issuer_username +"""<br>
				<b>Type</b> : """ + his_data.issuer_type + """<br>
				<b>Contact</b> : """ + his_data.issuer_contact + """<br>
				<b>Email</b> : """ + his_data.issuer_email + """<br>
				<b>Adress</b> : """ + his_data.issuer_address + """<br>
				<b>Website</b> : <a href=""" + his_data.issuer_website +""">"""+ his_data.issuer_website  + """</a><br>			
					<a class="text-secondary" href=/guest/issuer_explore/?issuer_username="""+his_data.issuer_username+""" >
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span>"""
	
	
	# advanced
	path = """https://rinkeby.etherscan.io/tx/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/tx/"""
	his_advanced = """
		<!--		<b>Data Id</b> : """ + his_data.id + """<br>  -->
				<b>Created</b> : """ + his_data.created + """<br>	
				<b>Expires</b> : """ + his_data.expires + """<br>
			<!--	<b>Signature Check</b> : """ + his_data.signature_check + """<br> -->
				<b>Transaction Hash</b> : <a class = "card-link" href = """ + path + his_data.transaction_hash + """>"""+ his_data.transaction_hash + """</a><br>					
				<b>Data storage</b> : <a class="card-link" href=""" + his_data.data_location + """>""" + his_data.data_location + """</a>"""
	
	# experience/education/employability/certificate
	if his_data.topic.capitalize() == "Experience"  :
		his_title = his_data.value['position']
		his_summary = his_data.value['summary']		
		his_value = """ 
				<b>Title</b> : """+his_data.value['position'] + """<br>
				<b>Company</b> : """+his_data.value['company']['name'] + """<br>
				<b>Manager</b> : """+his_data.value['company'].get('manager', 'Unknown') + """<br>
				<b>Manager Email</b> : """+his_data.value['company'].get('manager_email', 'Unknown') + """<br>
				<b>Start Date</b> : """+his_data.value['startDate'] + """<br>		
				<b>End Date</b> : """+his_data.value['endDate'] + """<br>
				<b>Skills</b> : """+his_data.value['skills'] + """<br>
				<b>Certificate</b> : """ + his_data.value['certificate_link']
	
	elif his_data.topic.capitalize() == "Education" :
		return 'work in progress'
	
	elif his_data.topic.capitalize() == "Employability" :
		return 'work in progress'		
	
	elif his_data.topic.capitalize() == "Certificate" :
		his_title = his_data.value['position']
		his_summary = his_data.value['summary']		
		his_value = """ 
				<b>Title</b> : """+his_data.value['position'] + """<br>
				<b>Company</b> : """+his_data.value['company']['name'] + """<br>
				<b>Manager</b> : """+his_data.value['company'].get('manager', 'Unknown') + """<br>
				<b>Manager Email</b> : """+his_data.value['company'].get('manager_email', 'Unknown') + """<br>
				<b>Start Date</b> : """+his_data.value['startDate'] + """<br>		
				<b>End Date</b> : """+his_data.value['endDate'] + """<br>
				<b>Skills</b> : """+his_data.value['skills'] 
				

	else :
		his_title = 'Profil'
		his_summary = ''		
		his_value = """<b>"""+his_data.topic.capitalize()+"""</b> : """+his_data.value
		
	
	return render_template('verify_certificate.html',
							dataid = dataId,
							topic = his_topic,
							visibility = his_visibility,
							title = his_title,
							summary = his_summary,
							issuer=his_issuer,
							value = his_value,
							advanced = his_advanced)
