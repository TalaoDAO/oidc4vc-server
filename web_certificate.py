

from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
import requests
import shutil
from flask_fontawesome import FontAwesome
import json

# dependances
from protocol import Document, read_profil
import environment
import constante

# environment setup
mode = environment.currentMode()
w3 = mode.w3


# 
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
def show_certificate():
	""" Its sometimes a GUEST screen 
	"""
	certificate_id = request.args['certificate_id']
	call_from = request.args.get('call_from')
	
	doc_id = int(certificate_id.split(':')[5])
	identity_workspace_contract = '0x'+ certificate_id.split(':')[3]
	
	if session.get('certificate_id') != certificate_id :
		certificate = Document('certificate')
		exist = certificate.relay_get(identity_workspace_contract, doc_id, mode, loading = 'full')	
		if not exist :
			content = json.dumps({'topic' : 'error', 'msg' : 'Certificate Not Found'})
			response = Response(content, status=406, mimetype='application/json')
			return response
		session['certificate_id'] = certificate_id
		session['displayed_certificate'] = certificate.__dict__
		session['profil'], session['category'] = read_profil(identity_workspace_contract, mode, 'light')
	
	issuer_username = None if 'issuer_username' not in session else session['issuer_username']
	identity_username = None if 'username' not in session else session['username']
		
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
	
	signature = session['displayed_certificate']['signature']
	logo = session['displayed_certificate']['logo']
	print('signature = ', signature, ' logo = ', logo)
	
	if signature is not None and logo is not None :
		url='https://gateway.pinata.cloud/ipfs/'+ signature
		response = requests.get(url, stream=True)
		with open('./photos/' + signature, 'wb') as out_file:
			shutil.copyfileobj(response.raw, out_file)
		del response
		
		url='https://gateway.pinata.cloud/ipfs/'+ logo
		response = requests.get(url, stream=True)
		with open('./photos/' + logo, 'wb') as out_file:
			shutil.copyfileobj(response.raw, out_file)
		del response
		
		return render_template('newcertificate.html',
							manager= session['displayed_certificate']['manager'],
							badge=my_badge,
							title = session['displayed_certificate']['title'],
							firstname=session['profil']['firstname'],
							lastname=session['profil']['lastname'],
							description=session['displayed_certificate']['description'],
							start_date=session['displayed_certificate']['start_date'],
							end_date=session['displayed_certificate']['end_date'],
							signature=signature,
							logo=logo,
							certificate_id=certificate_id,
							identity_username=identity_username,
							issuer_username=issuer_username,
							call_from=call_from,
							**context)


	else :
		return render_template('newcertificate_light.html',
							manager= session['displayed_certificate']['manager'],
							badge=my_badge,
							title = session['displayed_certificate']['title'],
							firstname=session['profil']['firstname'],
							lastname=session['profil']['lastname'],
							description=session['displayed_certificate']['description'],
							start_date=session['displayed_certificate']['start_date'],
							end_date=session['displayed_certificate']['end_date'],
							certificate_id=certificate_id,
							identity_username=identity_username,
							issuer_username=issuer_username,
							call_from=call_from,
							**context)




#         verify certificate
#@app.route('/certificate/verify/<dataId>', methods=['GET'])
def certificate_verify() :
	
	certificate_id = request.args['certificate_id']
	call_from = request.args.get('call_from')
	certificate = session['displayed_certificate'].copy()
	convert(certificate)
	
	if certificate_id != certificate['id'] :
		content = json.dumps({'topic' : 'error', 'msg' : 'Certificate Not Found'})
		response = Response(content, status=406, mimetype='application/json')
		return response
	
	
	issuer_type = 'Person' if certificate['issuer']['category'] == 1001 else 'Company' 
	
	# issuer
	if issuer_type == 'Company' :
		issuer = """
				<span>
				<b>Issuer Identity</b> : """ + certificate['issuer']['id'] + """<br>
				<b>Name</b> : """ + certificate['issuer']['name'] + """<br>
				<b>Contact Name</b> : """ + certificate['issuer']['contact_name'] + """<br>
				<b>Contact Email</b> : """ + certificate['issuer']['contact_email'] + """<br>
				<b>Contact Phone</b> : """ + certificate['issuer']['contact_phone'] + """<br>"""
	
	
	else :
		issuer = """
				<span>
				<b>Issuer Identity</b> : """ + certificate['issuer']['id'] + """<br>
				<b>Firstname</b> : """ + certificate['issuer']['firstname'] + """<br>
				<b>Lastname</b> : """ + certificate['issuer']['lastname'] + """<br>
				<b>Issuer Email</b> : """ + certificate['issuer']['contact_email'] + """<br>
				<b>Issuer Phone</b> : """ + certificate['issuer']['contact_phone'] + """<br>"""
		
		
	company_website = certificate['issuer'].get('website')
	if  company_website not in [ 'Unknown', None] :
		website = """
				<b>Website</b> : <a href=""" + company_website +""">"""+ company_website  + """</a><br>			
				</span>"""
	else :
		website = ""
	
	# advanced
	path = """https://rinkeby.etherscan.io/tx/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/tx/"""
	advanced = """
		<!--	<b>Data Id</b> : """ + certificate['id'] + """<br>  -->
				<b>Certificate issued on </b> : """ + certificate['created'] + """<br>	
				<b>Certificate expires on </b> : """ + certificate['expires'] + """<br>
				<b>Transaction Hash</b> : <a class = "card-link" href = """ + path + certificate['transaction_hash'] + """>"""+ certificate['transaction_hash'] + """</a><br>					
				<b>Data storage</b> : <a class="card-link" href=""" + certificate['data_location'] + """>""" + certificate['data_location'] + """</a>"""
	
	
	my_verif = issuer + website  + advanced
	
		
	
	return render_template('new_verify_certificate.html',
							certificate_id=certificate_id,
							call_from=call_from,
							topic = certificate['topic'].capitalize(),
							verif=my_verif,
							)


