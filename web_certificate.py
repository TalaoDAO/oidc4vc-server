


from flask import request, redirect, render_template, Response, session
from flask_api import FlaskAPI
from flask_fontawesome import FontAwesome
import json

# dependances
from protocol import Document, read_profil
import environment
import constante

# environment setup
mode = environment.currentMode()
w3 = mode.w3


# display experience certificate for anybody. Stand alone routine
def show_certificate(data):

	doc_id = int(data.split(':')[5])
	identity_workspace_contract = '0x'+data.split(':')[3]

	if not 'displayed_certificate' in session  :
		certificate = Document('certificate')
		exist = certificate.relay_get(identity_workspace_contract, doc_id, mode)	
		if not exist :
			content = json.dumps({'topic' : 'error', 'msg' : 'Certificate Not Found'})
			response = Response(content, status=406, mimetype='application/json')
			return response
		
		session['displayed_certificate'] = certificate.__dict__
		session['profil'], session['category'] = read_profil(identity_workspace_contract, mode, 'light')
		print('displayed certificate  = ', session['displayed_certificate'])
	
	ok="color: rgb(251,211,5); font-size: 10px;" # yellow
	ko="color: rgb(0,0,0);font-size: 10px;" # black
	
	# Icon "fa-star" treatment 
	score = []
	context = dict()
	score.append(int(session['displayed_certificate']['score_recommendation']))
	score.append(int(session['displayed_certificate']['score_delivery']))
	score.append(int(session['displayed_certificate']['score_schedule']))
	score.append(int(session['displayed_certificate']['score_communication']))
	for q in range(0,4) :
		for i in range(0,score[q]) :
			context["star"+str(q)+str(i)]=ok
		for i in range(score[q],5) :
			context ["star"+str(q)+str(i)]=ko
			
	my_badge = ""
	for skill in session['displayed_certificate']['skills'] :		
		my_badge = my_badge + """<span class="badge badge-pill badge-secondary" style="margin: 4px;"> """+ skill + """</span>"""
																	

	return render_template('newcertificate.html',
							manager= session['displayed_certificate']['manager'],
							badge=my_badge,
							title = session['displayed_certificate']['title'],
							firstname=session['profil']['firstname'],
							lastname=session['profil']['lastname'],
							description=session['displayed_certificate']['description'],
							start_date=session['displayed_certificate']['start_date'],
							end_date=session['displayed_certificate']['end_date'],
							signature=session['displayed_certificate']['signature'],
							logo=session['displayed_certificate']['logo'],
							data=data,
							**context)

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



#         verify certificate
#@app.route('/certificate/verify/<dataId>', methods=['GET'])
def certificate_verify(dataId) :
	
	certificate = session['displayed_certificate']
	convert(certificate)
	
	
	if dataId != certificate['id'] :
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
				<b>Type</b> : """ + issuer_type + """<br>
				<b>Contact Name</b> : """ + certificate['issuer']['contact_name'] + """<br>
				<b>Contact Email</b> : """ + certificate['issuer']['contact_email'] + """<br>
				<b>Contact Phone</b> : """ + certificate['issuer']['contact_phone'] + """<br>"""
	
	if certificate['issuer']['website'] != 'Unknown' :
		website = """
				<b>Website</b> : <a href=""" + certificate['issuer']['website'] +""">"""+ certificate['issuer']['website']  + """</a><br>			
				</span>"""
	else :
		website = ""
	
	# advanced
	path = """https://rinkeby.etherscan.io/tx/""" if mode.BLOCKCHAIN == 'rinkeby' else  """https://etherscan.io/tx/"""
	advanced = """
		<!--	<b>Data Id</b> : """ + certificate['id'] + """<br>  -->
				<b>Certificate Created</b> : """ + certificate['created'] + """<br>	
				<b>Expires</b> : """ + certificate['expires'] + """<br>
				<b>Transaction Hash</b> : <a class = "card-link" href = """ + path + certificate['transaction_hash'] + """>"""+ certificate['transaction_hash'] + """</a><br>					
				<b>Data storage</b> : <a class="card-link" href=""" + certificate['data_location'] + """>""" + certificate['data_location'] + """</a>"""
	
	
	my_verif = issuer + website + '<hr>' + advanced
	
		
	
	return render_template('new_verify_certificate.html',
							data= dataId,
							topic = certificate['topic'].capitalize(),
							verif=my_verif,
							)
