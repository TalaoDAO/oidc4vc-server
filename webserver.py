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
import random
import csv
from datetime import timedelta, datetime
import json
from werkzeug.utils import secure_filename
import threading

# dependances
import Talao_message
import createcompany
import createidentity
import constante
from protocol import ownersToContracts, contractsToOwners, save_image, partnershiprequest, remove_partnership, get_image
from protocol import delete_key, has_key_purpose, add_key
from protocol import Claim, File, Identity, Document, read_profil
import environment
import hcode
import ns

# Centralized  route
import web_create_identity
import web_certificate
import talent_connect
import data_user
import createidentity

# environment setup
mode = environment.currentMode()
w3 = mode.w3
exporting_threads = {}

UPLOAD_FOLDER = './uploads'

# Flask and Session setup	
#app = FlaskAPI(__name__)
app = Flask(__name__)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'redis'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=100)
app.config['SESSION_FILE_THRESHOLD'] = 100  
app.config['SECRET_KEY'] = "OCML3BRawWEUeaxcuKHLpw"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Session(app)

fa = FontAwesome(app)


# Centralized @route for web_create_identity
app.add_url_rule('/register/',  view_func=web_create_identity.authentification, methods = ['GET', 'POST'])
app.add_url_rule('/register/code/', view_func=web_create_identity.POST_authentification_2, methods = ['POST'])

# Centralized @route to display certificates
app.add_url_rule('/certificate/',  view_func=web_certificate.show_certificate)
app.add_url_rule('/certificate/verify/',  view_func=web_certificate.certificate_verify, methods = ['GET'])

# Centralized @route to Talent Connect APIs
app.add_url_rule('/api/v1/talent-connect/',  view_func=talent_connect.get, methods = ['GET'])
app.add_url_rule('/api/talent-connect/',  view_func=talent_connect.get, methods = ['GET'])
app.add_url_rule('/talent-connect/',  view_func=talent_connect.get, methods = ['GET'])
app.add_url_rule('/talent-connect/auth/',  view_func=talent_connect.auth, methods = ['POST'])

# Centralized route for user and data
app.add_url_rule('/user/',  view_func=data_user.user, methods = ['GET'])
app.add_url_rule('/data/<dataId>',  view_func=data_user.data, methods = ['GET'])


# Multithreading 
class ExportingThread(threading.Thread):
	def __init__(self, username, issuer_email, issuer_firstname, issuer_lastname, workspace_contract, talent_name, talent_username, certificate, mode) :
		super().__init__()
		self.username = username
		self.issuer_email = issuer_email
		self.issuer_firstname = issuer_firstname
		self.issuer_lastname = issuer_lastname
		self.workspace_contract = workspace_contract
		self.talent_name = talent_name
		self.talent_username = talent_username
		self.certificate = certificate
		self.mode = mode
	def run(self):
		create_authorize_issue_thread(self.username, self.issuer_email, self.issuer_firstname, self.issuer_lastname, self.workspace_contract, self.talent_name, self.talent_username, self.certificate, self.mode)	

# gestion du menu de gestion des Events  """
def event_display(eventlist) :
	event_html = ""
	index = 0
	for key in sorted(eventlist, reverse=True) :
		index += 1
		date= key.strftime("%y/%m/%d")
		texte = eventlist[key]['alert']
		doc_id = eventlist[key]['doc_id']
		event_type = eventlist[key]['event']
		if doc_id is None :
			href = " "
		else :
			href = "href= /data/"+doc_id
		icon = 'class="fas fa-file-alt text-white"'
		background = 'class="bg-success icon-circle"'
		
		if event_type == 'DocumentRemoved' or event_type == 'ClaimRemoved' :
			icon = 'class="fas fa-trash-alt text-white"'
			background = 'class="bg-warning icon-circle"'	
		thisevent = """<a class="d-flex align-items-center dropdown-item" """ + href + """>
							<div class="mr-3"> <div """ + background + """><i """ + icon + """></i></div></div>
							<div>
								<span class="small text-gray-500">""" + date + """</span><br>
								<div class = "text-truncate">
                                <span>""" + texte + """</span></div>
                            </div>
                        </a>"""	
		event_html = event_html + thisevent 
	return event_html, index

def check_login(username) :
	if username is None or session.get('username_logged') is None or username != session.get('username_logged') :
		print('session aborted = ', session)
		session.clear()
		abort(403, description="Authentification required")
	else :
		return username


def is_username_in_list(my_list, username) :
	for user in my_list :
		if user['username'] == username :
			return True
	return False	

# Starter with 3 options, login and logout
@app.route('/starter/', methods = ['GET', 'POST'])
def starter() :
		if request.method == 'GET' :
			return render_template('starter.html')
		else :
			start = request.form['start']
			if start == 'user' :
				return redirect(mode.server + 'login/')
			elif start == 'quick' :
				return redirect(mode.server + 'register/')
			elif start == 'advanced' :
				return redirect(mode.server + 'starter/') # tobe done
			else :
				pass

@app.route('/login/', methods = ['GET', 'POST'])
def login() :
	#session.clear()
	if request.method == 'GET' :
		return render_template('login.html')		
	if request.method == 'POST' :
		session.clear()
		session['username_to_log'] = request.form['username'].lower()
		exist  = ns.get_data_for_login(session['username_to_log'])
		if exist is None :
			flash('Username not found', 'warning')		
			return render_template('login.html')
		(identity,email_to_log) = exist
		# secret code to send by email
		if session.get('code') is None :
			session['code'] = str(random.randint(100000, 999999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 180)
			session['try_number'] = 1
			Talao_message.messageAuth(email_to_log, str(session['code']))
			print('secret code sent = ', session['code'])
			flash('Secret Code sent')
		else :
			print("secret code already sent")
			flash("Secret Code already sent")
		return render_template("login_2.html")

# recuperation du code saisi
@app.route('/login/authentification/', methods = ['POST'])
def login_2() :
	if session.get('username_to_log') is None or session.get('code') is None :
		flash("Authentification expired")		
		return render_template('login.html')
	code = request.form['code']
	session['try_number'] +=1
	print('code retourné = ', code)
	
	if code in [session['code'], "123456"] and datetime.now() < session['code_delay'] : # pour les tests
		session['username_logged'] = session['username_to_log']
		del session['username_to_log']
		del session['try_number']
		del session['code'] 
		return redirect(mode.server + 'user/?username=' + session['username_logged'])		
	
	elif session['code_delay'] < datetime.now() :
		flash("Code expired")
		return render_template("login.html")
		
	elif session['try_number'] > 3 :
		flash("Too many trials (3 max)")
		return render_template("login.html")
		
	else :	
		if session['try_number'] == 2 :			
			flash('This code is incorrect, 2 trials left')
		if session['try_number'] == 3 :
			flash('This code is incorrect, 1 trial left')
		return render_template("login_2.html")	
	
# logout
@app.route('/logout/', methods = ['GET'])
def logout() :
	session.clear()
	return render_template('login.html')

	
# forgot username
@app.route('/forgot_username/', methods = ['GET', 'POST'])
def forgot_username() :
	if request.method == 'GET' :
		return render_template('forgot_username.html')
	if request.method == 'POST' :
		username_list = ns.get_username_list_from_email(request.form['email'])
		if username_list == [] :
			msg = 'There is no Identity with this Email'
			flash(msg , 'warning')
		else :
			msg = 'This Email is already used by Identities : ' + ", ".join(username_list)  
			flash(msg , 'success')
		return render_template('login.html')

# picture
@app.route('/user/picture/', methods=['GET', 'POST'])
def picture() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('picture.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		if 'image' not in request.files :
			print('No file ')
		myfile = request.files['image']
		filename = secure_filename(myfile.filename)
		myfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		picturefile = UPLOAD_FOLDER + '/' + filename
		save_image(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, picturefile, 'picture',mode, synchronous = False)	
		session['picture'] = filename	
		flash('Your picture has been updated', 'success')
		return redirect(mode.server + 'user/?username=' + username)


# signature
@app.route('/user/signature/', methods=['GET', 'POST'])
def signature() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_signature = session['signature']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('signature.html', picturefile=my_picture, signaturefile=my_signature,event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		if 'image' not in request.files :
			print('No file ')
		myfile = request.files['image']
		filename = secure_filename(myfile.filename)
		myfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		signaturefile = UPLOAD_FOLDER + '/' + filename
		save_image(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, signaturefile, 'signature', mode, synchronous = False)	
		session['signature'] = filename	
		flash('Your signature has been updated', 'success')
		return redirect(mode.server + 'user/?username=' + username)





@app.route('/faq/', methods=['GET'])
def faq() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('faq.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)




# issuer explore 
@app.route('/user/issuer_explore/', methods=['GET'])
def issuer_explore() :

	username = check_login(session.get('username'))	
	issuer_username = request.args['issuer_username']
	
	if 'issuer_username' not in session or session['issuer_username'] != issuer_username :
		issuer_workspace_contract = ns.get_data_from_username(issuer_username, mode)['workspace_contract']
		session['issuer_explore'] = Identity(issuer_workspace_contract, mode).__dict__.copy()
	
		del session['issuer_explore']['mode']
		session['issuer_username'] = issuer_username
	
	# do something common
	my_event_html, my_counter =  event_display(session['events'])
	#issuer_name = session['issuer_explore']['name']
	#my_picture = session['picture'] 
	issuer_picture = "anonymous1.png" if session['issuer_explore']['picture'] is None else session['issuer_explore']['picture']
						
	if session['issuer_explore']['type'] == 'person' :
		# do something specifc	
		issuer_picture = "anonymous1.png" if session['issuer_explore']['picture'] is None else session['issuer_explore']['picture']
	
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
		issuer_personal = """<span><b>Username</b> : """ + ns.get_username_from_resolver(session['issuer_explore']['workspace_contract'])+"""<br>"""			
		for topic_name in session['issuer_explore']['personal'].keys() : 
			if session['issuer_explore']['personal'][topic_name]['claim_value'] is not None :
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['issuer_explore']['workspace_contract'][2:] + ':claim:' + session['issuer_explore']['personal'][topic_name]['claim_id']
				issuer_personal = issuer_personal + """ 
				<span><b>"""+ Topic[topic_name] +"""</b> : """+ session['issuer_explore']['personal'][topic_name]['claim_value']+"""				
					
					<a class="text-secondary" href=/data/""" + topicname_id + """:personal>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>"""				
		
		
		# kyc
		if len (session['issuer_explore']['kyc']) == 0:
			my_kyc = """<a href="/user/request_proof_of_identity/">Request a Proof of Identity</a><hr>
					<a class="text-danger">No Proof of Identity available</a>"""
		else :	
			my_kyc = ""
			for kyc in session['issuer_explore']['kyc'] :
				kyc_html = """
				<b>Firstname</b> : """+ kyc['firstname'] +"""<br>				
				<b>Lastname</b> : """+ kyc['lastname'] +"""<br>				
				<b>Birth Date</b> : """+ kyc['birthdate'] +"""<br>				
				
				<b>Sex</b> : """+ kyc['sex'] +"""<br>			
				<b>Nationality</b> : """+ kyc['nationality'] + """<br>
				<b>Date of Issue</b> : """+ kyc['date_of_issue']+"""<br>
				<b>Date of Expiration</b> : """+ kyc['date_of_expiration']+"""<br>
				<b>Authority</b> : """+ kyc['authority']+"""<br>
				<b>Country</b> : """+ kyc['country']+"""<br>				
				<b>Id</b> : """+ kyc['id']+"""<br>				
				<p>		
					
					<a class="text-secondary" href=/data/"""+ kyc['id'] + """:kyc>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
				my_kyc = my_kyc + kyc_html		
	

		# experience
		issuer_experience = ''
		if session['issuer_explore']['experience'] == [] :
			issuer_experience = """  <a class="text-info">No data available</a>"""
		else :	
			for experience in session['issuer_explore']['experience'] :
				exp_html = """ 
					<b>Company</b> : """+experience['company']['name']+"""<br>			
					<b>Title</b> : """+experience['title']+"""<br>
					<b>Description</b> : """+experience['description'][:100]+"""...<br>
					<p>
						<a class="text-secondary" href=/data/"""+experience['id'] + """:experience>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
						</a>
					</p>"""	
				issuer_experience = issuer_experience + exp_html + """<hr>"""
		
		# education
		issuer_education = ''
		if session['issuer_explore']['education'] == [] :
			issuer_education = """  <a class="text-info">No data available</a>"""
		else :	
			for education in session['issuer_explore']['education'] :
				edu_html = """
					<b>Company</b> : """+education['organization']['name']+"""<br>			
					<b>Title</b> : """+education['title']+"""<br>
					<b>Description</b> : """+education['description'][:100]+"""...<br>
					<p>
						<a class="text-secondary" href=/data/"""+experience['id'] + """:education>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
						</a>
					</p>"""	
				issuer_education = issuer_education + edu_html + """<hr>"""
		
		# certificates
		issuer_certificates = ""
		if session['issuer_explore']['certificate'] == [] :
			issuer_certificates = """<a class="text-info">No data available</a>"""
		else :	
			for certificate in session['issuer_explore']['certificate'] :
				organization_name = ns.get_username_from_resolver(certificate['issuer']['workspace_contract'])
				organization_name = 'Unknown' if organization_name is None else organization_name
				cert_html = """ 
					<b>Company</b> : """ + organization_name +"""<br>	
					<b>Title</b> : """ + certificate['title']+"""<br>
					<b>Description</b> : """ + certificate['description'][:100]+"""...<br>
					<b></b><a href= """ + mode.server +  """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + session['issuer_explore']['workspace_contract'][2:] + """:document:""" + str(certificate['doc_id']) + """&call_from=explore>Display Certificate</a><br>
					<p>
						<a class="text-secondary" href=/data/""" + certificate['id'] + """:certificate>
							<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
						</a>
					</p>"""	
				issuer_certificates = issuer_certificates + cert_html + """<hr>"""
				
				
				
					
		#services : le reader est une persone, le profil vu est celui dune personne
		services = ""
		if session['type'] == 'person' :
			
			if not is_username_in_list(session['issuer'], issuer_username) :
				services = """<a class="text-warning">This Talent is not in your Issuer List.</a><br>
							<a href="/user/add_issuer/?issuer_username=""" + issuer_username + """">Add this Talent in your Issuer List to request him a recommendation.</a><br><br>"""
			else :
				services = """<a class="text-success">This Talent is in your Issuer List.</a><br>
							<a href="/user/issue_referral/">Request this Talent a recommendation to increase your rating.</a><br><br>"""
			
				
			if not is_username_in_list(session['whitelist'], issuer_username) :
				services = services + """<a class="text-warning">This Talent is not in your White List.</a><br>
							<a href="/user/add_white_issuer/?issuer_username=""" + issuer_username + """"> Add this Talent in your White List to increase your rating.</a><br><br>"""
			else :
				services = services + """<a class="text-success">This Talent is in your White list.</a><br><br>"""
		
		
			if is_username_in_list(session['issuer_explore']['issuer_keys'], username) :
				services = services + """<a href="/user/issue_referral/?issuer_username="""+ issuer_username + """&issuer_name=""" + session['issuer_explore']['name'] + """ ">Issue a Recommendation</a><br><br>"""
			else :
				services = services + """<br><br>"""
		
			services = services + """<br><br><br><br><br><br><br><br>"""					

		
		
		#services : les reader est une company, le profil vu est celui d une personne. Attention au "jean.bnp"
		if session['type'] == 'company' :
			
			host_name = username if len(username.split('.')) == 1 else username.split('.')[1]  
			if ns.does_manager_exist(issuer_username, host_name) :
				services = """<a class="text-success">This Talent is a Manager.</a><br>"""
			else : 
				services = ""
			
			if is_username_in_list(session['issuer_explore']['issuer_keys'], host_name) :
				services = services + """ <br><a class="text-success">Talent has authorized the Company to issue Certificates.</a>
										<a href="/user/issue_certificate/?issuer_username="""+ issuer_username + """&issuer_name=""" + session['issuer_explore']['name'] + """ ">Issue a new Certificate.</a><br>"""
			else :
				services = services + """<br><br>"""
			
			
			
			if not is_username_in_list(session['partner'], issuer_username) :
				services = services + """<br><a class="text-warning">This Talent is not in your Partner List.</a>
										<br><a href="/user/request_partnership/?issuer_username=""" + issuer_username + """">Request a Partnership to share private data.</a><br>"""
			else :
				services = services + """<br><a class="text-success">This Talent is in your Partner list.</a><br>"""
		
			
			services = services + """<br><br><br><br><br><br><br><br><br><br><br><br>"""					
		
		services = services + """<br><br><br><br><br><br>"""
											
		return render_template('person_issuer_identity.html',
							issuer_name=session['issuer_explore']['name'],
							profil_title = session['issuer_explore']['profil_title'],
							username=username,
							name=session['name'],
							kyc=my_kyc,
							personal=issuer_personal,
							experience=issuer_experience,
							certificates=issuer_certificates,
							education=issuer_education,
							services=services,
							event=my_event_html,
							counter=my_counter,
							picturefile = session['picture'],
							issuer_picturefile=issuer_picture)
	
	
	if session['issuer_explore']['type'] == 'company' :
		# do something specific

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
					
					<a class="text-secondary" href=/data/"""+ kbis['id'] + """:kbis>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</p>"""	
				my_kbis = my_kbis + kbis_html		
		
		# personal
		issuer_personal = """ <span><b>Username</b> : """ + ns.get_username_from_resolver(session['issuer_explore']['workspace_contract'])	+ """<br>"""		
		for topic_name in session['issuer_explore']['personal'].keys() :
			if session['issuer_explore']['personal'][topic_name]['claim_value'] is not None :
				topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['issuer_explore']['workspace_contract'][2:] + ':claim:' + session['issuer_explore']['personal'][topic_name]['claim_id']
				issuer_personal = issuer_personal + """ 
				<span><b>"""+ topic_name +"""</b> : """+ session['issuer_explore']['personal'][topic_name]['claim_value']+"""				
					
					<a class="text-secondary" href=/data/""" + topicname_id + """:personal>
						<i data-toggle="tooltip" class="fa fa-search-plus" title="Explore"></i>
					</a>
				</span><br>"""
		
		
		#services 
		
		
				
		if not is_username_in_list(session['issuer'], issuer_username) :
			services = """<a class="text-warning">This Company is not in your Issuer List.</a><br>
						<a href="/user/add_issuer/?issuer_username=""" + issuer_username + """">Add this Company in your Issuer List to request Certificates.</a><br>"""
		else :
			services = """<a class="text-success">This Company is in your Issuer List.</a><br>
						<a href="/user/request_certificate/">You can request a certificate.</a><br>"""
		
		if not is_username_in_list(session['whitelist'], issuer_username) :
			services = services + """<br><a class="text-warning">This Company is not in your White List.</a><br>
						<a href="/user/add_white_issuer/?issuer_username=""" + issuer_username + """"> Add this Company in your White List to increase your rating.</a><br>"""
		else :
			services = services + """<br><a class="text-success">This Companyt is in your White list.</a><br>"""
		
		if not is_username_in_list(session['partner'], issuer_username) :
			services = services + """<br><a class="text-warning">This Comapny is not in your Partner List.</a>
			<br><a href="/user/request_partnership/?issuer_username=""" + issuer_username + """">Request a Partnership to access private information.</a><br>"""
		else :
			services = services + """<br><a class="text-success">This Company is in your Partner list.</a><br>"""
		
		if is_username_in_list(session['issuer_explore']['issuer_keys'], username) :
			services = services + """<a href="/user/issue_referral/?issuer_username="""+ issuer_username + """&issuer_name=""" + issuer_name + """ ">Issue a Recommendation</a><br>"""
		else :
			services = services + """<br><br>"""
								
		services = services + """<br><br><br><br><br><br><br>"""
		
		
		return render_template('company_issuer_identity.html',
							issuer_name=session['issuer_explore']['name'],
							username=username,
							name= session['name'],
							kbis=my_kbis,
							services=services,
							personal=issuer_personal,
							event=my_event_html,
							counter=my_counter,
							picturefile=session['picture'],
							issuer_picturefile=issuer_picture)






# Analysis
@app.route('/user/data_analysis/', methods=['GET'])
def data_analysis() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		data = talent_connect.analysis(session['workspace_contract'],session['resume'], mode)
		analysis = json.dumps(data, indent=4)
		return render_template('data_analysis.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, analysis=analysis)




# Test only
@app.route('/user/test/', methods=['GET'])
def test() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		test = json.dumps(session['resume'], indent=4)
		return render_template('test.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, test=test)

# search
@app.route('/user/search/', methods=['GET', 'POST'])
def search() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('search.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		username_to_search = request.form['username_to_search']
		if username_to_search == username :
			flash('You are You !', 'warning')
			return redirect(mode.server + 'user/?username=' + username)	
		return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + username_to_search)
		
		
		
# issue certificate for companies
@app.route('/user/issue_certificate/', methods=['GET', 'POST'])
def issue_certificate():
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('issue_certificate.html',
								picturefile=my_picture,
								event=my_event_html,
								counter=my_counter,
								name=session['name'],
								username=username,
								issuer_username=session['issuer_username'])
	if request.method == 'POST' :
		if request.form['certificate_type'] == 'experience' :
			return render_template("issue_experience_certificate.html",
									picturefile=my_picture,
									event=my_event,
									counter=my_counter,
									username=username,
									name=session['name'],
									manager_name=username,
									issuer_username=session['issuer_username'])	
		else :
			flash('This certificate is not implemented yet !', 'warning')
			return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])	
@app.route('/user/issuer_experience_certificate/', methods=['POST'])
def issue_experience_certificate():
	username = check_login(session.get('username'))
	manager_username = username if len(username.split('.')) == 1 else username.split('.')[0] 
	manager_workspace_contract = ns.get_data_from_username(manager_username, mode)['workspace_contract']
	signature = get_image(manager_workspace_contract, 'signature', mode)
	certificate = {
					"type" : "experience",	
					"title" : request.form['title'],
					"description" : request.form['description'],
					"start_date" : request.form['start_date'],
					"end_date" : request.form['end_date'],
					"skills" : request.form['skills'].split(','),  		
					"score_recommendation" : request.form['score_recommendation'],
					"score_delivery" : request.form['score_delivery'],
					"score_schedule" : request.form['score_schedule'],
					"score_communication" : request.form['score_communication'],
					"logo" : session['picture'],
					"signature" : signature,
					"manager" : username,}
	workspace_contract_to = ns.get_data_from_username(session['issuer_username'], mode)['workspace_contract']
	address_to = contractsToOwners(workspace_contract_to, mode)
	my_certificate = Document('certificate')
	(doc_id, ipfshash, transaction_hash) = my_certificate.add(session['address'], session['workspace_contract'], address_to, workspace_contract_to, session['private_key_value'], certificate, mode, mydays=0, privacy='public', synchronous=True) 
	flash('Certificate has been issued', 'success')
	return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])		
	


		
# issue referral for person
@app.route('/user/issue_referral/', methods=['GET', 'POST'])
def issue_referral():
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		issuer_username = request.args['issuer_username']
		issuer_name = request.args['issuer_name']
		session['talent_to_issue_certificate_username'] = issuer_username
		return render_template('issue_referral.html',
								picturefile=my_picture,
								event=my_event_html,
								counter=my_counter,
								name=session['name'],
								issuer_username=issuer_username,
								issuer_name = issuer_name)
	if request.method == 'POST' :
		issuer_username = session['talent_to_issue_certificate_username']
		referral = {
					"type" : "referral",	
					"description" : request.form['description'],
					"relationship" : request.form['relationship']}	
		print('referral = ', referral)					
		workspace_contract_to = ns.get_data_from_username(session['talent_to_issue_certificate_username'], mode)['workspace_contract']
		address_to = contractsToOwners(workspace_contract_to, mode)
		my_referral = Document('certificate')
		
		execution = my_referral.add(session['address'], session['workspace_contract'], address_to, workspace_contract_to, session['private_key_value'], referral, mode, mydays=0, privacy='public', synchronous=True) 
		if execution is None :
			flash('Operation failed ', 'danger')
		else : 
			(doc_id, ipfshash, transaction_hash) = execution	
			# add certificate in session
			flash('Certificate has been issued', 'success')
		del session['talent_to_issue_certificate_username']
		return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + issuer_username)		
	





# personalsettings
@app.route('/user/update_personal_settings/', methods=['GET', 'POST'])
def update_personal_settings() :	
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	personal = session['personal']
	convert(personal)
	if request.method == 'GET' :
		privacy=dict()
		for topicname in session['personal'].keys() :
			if session['personal'][topicname]['privacy']=='secret' :
				(p1,p2,p3) = ("", "", "selected") 
			if session['personal'][topicname]['privacy']=='private' :
				(p1,p2,p3) = ("", "selected", "") 
			if session['personal'][topicname]['privacy']=='public' :
				(p1,p2,p3) = ("selected", "", "") 
			if session['personal'][topicname]['privacy'] is None :
				(p1,p2,p3) = ("", "", "") 
			
			privacy[topicname] = """
					<optgroup """ +  """ label="Select">
					<option """+ p1 + """ value="public">Public</option>
					<option """ + p2 +""" value="private">Private</option>
					<option """ + p3 + """ value="secret">Secret</option>
					</opgroup>"""
					
		return render_template('update_personal_settings.html',
								picturefile=my_picture,
								event=my_event_html,
								counter=my_counter,
								name=session['name'],
								username=username,
								firstname=personal['firstname']['claim_value'],
								lastname=personal['lastname']['claim_value'],
								about=personal['about']['claim_value'],
								education=personal['education']['claim_value'],							
								profil_title=personal['profil_title']['claim_value'],
								contact_email=personal['contact_email']['claim_value'],
								contact_email_privacy=privacy['contact_email'],
								contact_phone=personal['contact_phone']['claim_value'],
								contact_phone_privacy=privacy['contact_phone'],
								birthdate=personal['birthdate']['claim_value'],
								birthdate_privacy=privacy['birthdate'],
								postal_address=personal['postal_address']['claim_value'],
								postal_address_privacy=privacy['postal_address']
								)
	if request.method == 'POST' :
		form_privacy = dict()
		form_value = dict()
		form_privacy['contact_phone'] = request.form['contact_phone_select']
		form_privacy['contact_email'] = request.form['contact_email_select']
		form_privacy['birthdate'] = request.form['birthdate_select']
		form_privacy['postal_address'] = request.form['postal_address_select']
		form_privacy['firstname'] = 'public'
		form_privacy['lastname'] = 'public'
		form_privacy['about'] = 'public'
		form_privacy['profil_title'] = 'public'
		form_privacy['education'] = 'public'

		change = False	
		
		for topicname in session['personal'].keys() :
			form_value[topicname] = None if request.form[topicname] in ['None', '', ' '] else request.form[topicname]

			if 	form_value[topicname] != session['personal'][topicname]['claim_value'] or session['personal'][topicname]['privacy'] != form_privacy[topicname] :
				(claim_id,a,b) = Claim().relay_add( session['workspace_contract'],topicname, form_value[topicname], form_privacy[topicname], mode)
				change = True
				session['personal'][topicname]['claim_value'] = form_value[topicname]
				session['personal'][topicname]['privacy'] = form_privacy[topicname]
				session['personal'][topicname]['claim_id'] = claim_id[2:]
			
		if change :
			flash('personal has been updated', 'success')
		return redirect(mode.server + 'user/?username=' + username)


def convert(obj):
    if type(obj) == list:
        for x in obj:
            convert(x)
    elif type(obj) == dict:
        for k, v in obj.items():
            if v is None:
                obj[k] = ''
            else:
                convert(v)

# company settings
@app.route('/user/update_company_settings/', methods=['GET', 'POST'])
def update_company_settings() :	
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	personal = session['personal'].copy()
	convert(personal)
	if request.method == 'GET' :
		privacy=dict()
		for topicname in session['personal'].keys() :
			if session['personal'][topicname]['privacy']=='secret' :
				(p1,p2,p3) = ("", "", "selected") 
			if session['personal'][topicname]['privacy']=='private' :
				(p1,p2,p3) = ("", "selected", "") 
			if session['personal'][topicname]['privacy']=='public' :
				(p1,p2,p3) = ("selected", "", "") 
			if session['personal'][topicname]['privacy'] is None :
				(p1,p2,p3) = ("", "", "") 
			
			privacy[topicname] = """
					<optgroup """ +  """ label="Select">
					<option """+ p1 + """ value="public">Public</option>
					<option """ + p2 +""" value="private">Private</option>
					<option """ + p3 + """ value="secret">Secret</option>
					</opgroup>"""
					
		return render_template('update_company_settings.html',
								picturefile=my_picture,
								event=my_event_html,
								counter=my_counter,
								username=username,
								name=personal['name']['claim_value'],
								name_privacy=privacy['name'],
								contact_name=personal['contact_name']['claim_value'],
								contact_name_privacy=privacy['contact_name'],
								contact_email=personal['contact_email']['claim_value'],
								contact_email_privacy=privacy['contact_email'],
								contact_phone=personal['contact_phone']['claim_value'],
								contact_phone_privacy=privacy['contact_phone'],
								website=personal['website']['claim_value'],
								website_privacy=privacy['website'],
								)
	if request.method == 'POST' :
		form_privacy = dict()
		form_value = dict()
		form_privacy['name'] = request.form['name_select']
		form_privacy['contact_name'] = request.form['contact_name_select']
		form_privacy['contact_phone'] = request.form['contact_phone_select']
		form_privacy['contact_email'] = request.form['contact_email_select']
		form_privacy['website'] = request.form['website_select']

		change = False	
		for topicname in session['personal'].keys() :
			form_value[topicname] = None if request.form[topicname] in ['None', '', ' '] else request.form[topicname]

			if 	form_value[topicname] != session['personal'][topicname]['claim_value'] or session['personal'][topicname]['privacy'] != form_privacy[topicname] :
				(claim_id,a,b) = Claim().relay_add( session['workspace_contract'],topicname, form_value[topicname], form_privacy[topicname], mode)
				change = True
				session['personal'][topicname]['claim_value'] = form_value[topicname]
				session['personal'][topicname]['privacy'] = form_privacy[topicname]
				session['personal'][topicname]['claim_id'] = claim_id[2:]			
		if change :
			flash('Company Settings has been updated', 'success')
		return redirect(mode.server + 'user/?username=' + username)


# diigitalvault
@app.route('/user/store_file/', methods=['GET', 'POST'])
def store_file() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('store_file.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		if 'file' not in request.files :
			print('No file ')
			return
		myfile = request.files['file']
		filename = secure_filename(myfile.filename)
		myfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		privacy = request.form['privacy']
		user_file = File()
		(doc_id, ipfs_hash, transaction_hash) =user_file.add(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, filename, privacy, mode)
		new_file = {'id' : 'did:talao:'+ mode.BLOCKCHAIN+':'+ session['workspace_contract'][2:]+':document:'+ str(doc_id),
									'filename' : filename,
									'doc_id' : doc_id,
									'created' : str(datetime.utcnow()),
									'privacy' : privacy,
									'doctype' : "",
									'issuer' : mode.relay_address,
									'transaction_hash' : transaction_hash
									}	
		session['identity_file'].append(new_file)				
		flash(filename + ' uploaded', "success")
		return redirect(mode.server + 'user/?username=' + username)



# create company
@app.route('/user/create_company/', methods=['GET', 'POST'])
def create_company() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('create_company.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		company_email = request.form['company_email']
		company_username = request.form['company_username'].lower()
		done = createcompany.create_company(company_email, company_username, mode)
		if done :
			flash(company_username + ' has been created as company', 'success')
		else :
			flash('Creation failed, username ' + company_username + ' already exists ?', 'danger')
		return redirect(mode.server + 'user/?username=' + username)


# create a person 
@app.route('/user/create_person/', methods=['GET', 'POST'])
def create_person() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('create_person.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		person_email = request.form['person_email']
		person_username = request.form['person_username']
		done = createidentity.create_user(person_username, person_email, mode)
		if done is not None :
			flash(person_username + ' has been created as a person', 'success')
		else :
			flash('Creation failed, username ' + person_username + ' already exists ?', 'danger')
		return redirect(mode.server + 'user/?username=' + username)

# add experience
@app.route('/user/add_experience/', methods=['GET', 'POST'])
def add_experience() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('add_experience.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		my_experience = Document('experience')
		experience = dict()
		experience['company'] = {'contact_email' : request.form['contact_email'],
								'name' : request.form['company_name'],
								'contact_name' : request.form['contact_name'],
								'contact_phone' : request.form['contact_phone']}
		experience['title'] = request.form['title']
		experience['description'] = request.form['description']
		experience['start_date'] = request.form['from']
		experience['end_date'] = request.form['to']
		experience['skills'] = request.form['skills'].split(' ')  		
		privacy = request.form['privacy']
		(doc_id, ipfshash, transaction_hash) = my_experience.relay_add(session['workspace_contract'], experience, mode, privacy=privacy)		
		# add experience in session
		experience['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':document:'+str(doc_id)
		experience['doc_id'] = doc_id
		session['experience'].append(experience)			
		flash('New experience added', 'success')
		return redirect(mode.server + 'user/?username=' + username)


# create kyc (Talao only)
@app.route('/user/issue_kyc/', methods=['GET', 'POST'])
def create_kyc() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('create_kyc.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		kyc = Document('kyc')
		my_kyc = dict()
		kyc_username = request.form['username']
		kyc_workspace_contract = ns.get_data_from_username(kyc_username,mode)['workspace_contract'] 
		my_kyc['firsname'] = request.form['firstname']
		my_kyc['lastname'] = request.form['lastname']
		my_kyc['birthdate'] = request.form['birthdate']
		my_kyc['authority'] = request.form['authority']
		my_kyc['card_id'] = request.form['card_id']
		my_kyc['date_of_issue'] = request.form['date_of_issue']
		my_kyc['date_of_expiration'] = request.form['date_of_expiration']
		my_kyc['sex'] = request.form['sex']
		my_kyc['country'] = request.form['country']
		(doc_id, ipfshash, transaction_hash) = kyc.relay_add(kyc_username, my_kyc, mode, privacy='public')		
		flash('New kyc added for '+ kyc_username, 'success')
		return redirect(mode.server + 'user/?username=' + username)


# create kbis (Talao only)
@app.route('/user/issue_kbis/', methods=['GET', 'POST'])
def create_kbis() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('create_kbis.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		kyc = Document('kbis')
		my_kbis = dict()
		kbis_username = request.form['username']
		kbis_workspace_contract = ns.get_data_from_username(kbis_username,mode)['workspace_contract'] 
		my_kbis['name'] = request.form['name']
		my_kbis['date'] = request.form['date']
		my_kbis['legal_form'] = request.form['legal_form']
		my_kbis['capital'] = request.form['capital']
		my_kbis['naf'] = request.form['naf']
		my_kbis['activity'] = request.form['activity']
		my_kbis['address'] = request.form['address']
		my_kbis['ceo'] = request.form['ceo']
		my_kbis['siret'] = request.form['siret']
		my_kbis['managing_director'] = request.form['managing_director']
		(doc_id, ipfshash, transaction_hash) = kbis.relay_add(kyc_username, my_kbis, mode, privacy='public')		
		flash('New kbis added for '+ kbis_username, 'success')
		return redirect(mode.server + 'user/?username=' + username)


@app.route('/user/remove_experience/', methods=['GET', 'POST'])
def remove_experience() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['experience_to_remove'] = request.args['experience_id']
		session['experience_title'] = request.args['experience_title']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_experience.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, experience_title=session['experience_title'])
	elif request.method == 'POST' :	
		session['experience'] = [experience for experience in session['experience'] if experience['id'] != session['experience_to_remove']]
		Id = session['experience_to_remove'].split(':')[5]
		my_experience = Document('experience')
		my_experience.relay_delete(session['workspace_contract'], int(Id), mode)
		del session['experience_to_remove']
		del session['experience_title']
		flash('The experience has been removed', 'success')
		return redirect (mode.server +'user/?username=' + username)


@app.route('/user/remove_certificate/', methods=['GET', 'POST'])
def remove_certificate() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['certificate_to_remove'] = request.args['certificate_id']
		session['certificate_title'] = request.args['certificate_title']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_certificate.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, experience_title=session['experience_title'])
	elif request.method == 'POST' :	
		session['certificate'] = [certificate for certificate in session['certificate'] if certificate['id'] != session['certificate_to_remove']]
		Id = session['certificate_to_remove'].split(':')[5]
		my_experience = Document('certificate')
		my_experience.relay_delete(session['workspace_contract'], int(Id), mode)
		del session['certificate_to_remove']
		del session['certificate_title']
		flash('The certificate has been removed', 'success')
		return redirect (mode.server +'user/?username=' + username)


# add education
@app.route('/user/add_education/', methods=['GET', 'POST'])
def add_education() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('add_education.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		my_education = Document('education')
		education  = dict()
		education['organization'] = {'contact_email' : request.form['contact_email'],
								'name' : request.form['company_name'],
								'contact_name' : request.form['contact_name'],
								'contact_phone' : request.form['contact_phone']}
		education['title'] = request.form['title']
		education['description'] = request.form['description']
		education['start_date'] = request.form['from']
		education['end_date'] = request.form['to']
		education['skills'] = request.form['skills'].split(' ')
		education['certificate_link'] = request.form['certificate_link']  		
		privacy = request.form['privacy']
		(doc_id, ipfshash, transaction_hash) = my_education.relay_add(session['workspace_contract'], education, mode, privacy=privacy)		
		# add experience in session
		education['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':document:'+str(doc_id)
		education['doc_id'] = doc_id
		session['education'].append(education)			
		flash('New Education added', 'success')
		return redirect(mode.server + 'user/?username=' + username)
@app.route('/user/remove_education/', methods=['GET', 'POST'])
def remove_education() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['education_to_remove'] = request.args['education_id']
		session['education_title'] = request.args['education_title']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_education.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, education_title=session['education_title'])
	elif request.method == 'POST' :	
		session['education'] = [education for education in session['education'] if education['id'] != session['education_to_remove']]
		Id = session['education_to_remove'].split(':')[5]
		my_education = Document('education')
		my_education.relay_delete(session['workspace_contract'], int(Id), mode)
		del session['education_to_remove']
		del session['education_title']
		flash('The Education has been removed', 'success')
		return redirect (mode.server +'user/?username=' + username)

# invit friend
@app.route('/user/invit_friend/', methods=['GET', 'POST'])
def invit_friend() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('invit_friend.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	else :
		friend__email = request.form['friend_email']
		friend_memo = request.form['friend_memo']
		# something to do		
		flash('Invit sent to friend', 'success')
		return redirect(mode.server + 'user/?username=' + username)




# request partnership
@app.route('/user/request_partnership/', methods=['GET', 'POST'])
def resquest_partnership() :
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('request_partnership.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		partner_username = request.form['partner_username']
		if partner_username == 'new' :
			return render_template('request_partnership_new.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
		if is_username_in_list(session['partner'], partner_username) :
			flash(partner_username + ' is already a partner')
			return redirect(mode.server + 'user/?username=' + username)
		partner_workspace_contract = get_data_from_username(partner_username, mode)['workspace_contract']
		partner_address = contractToOwners(partner_workspace_contract)
		partner_publickey = mode.w3.solidityKeccak(['address'], [parner_address]).hex()
		
		filename = "./RSA_key/" + mode.BLOCKCHAIN + '/' + session['address'] + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
		try :
			fp = open(filename,"r")
			rsa_key = fp.read()	
			fp.close()   
		except IOError :
			print('RSA key not found')	
		res = partnershiprequest(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, partner_workspace_contract, rsa_key, mode, synchronous= True)
		if res  :
			session['partner'].append({"address": partner_address,
								"publickey": partner_publickey,
								 "workspace_contract" : partner_workspace_contract,
								  'username' : partner_username,
								  'authorized' : 'Authorized',
								  })
			flash('We have send a request to ' + partner_username, 'success')
		else :
			flash('Request to ' + partner_username + ' failed', 'danger')
		return redirect(mode.server + 'user/?username=' + username)
# remove partnership to be completed
@app.route('/user/remove_partner/', methods=['GET', 'POST'])
def remove_partner() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['partner_username_to_remove'] = request.args['partner_username']
		session['partner_workspace_contract_to_remove'] = request.args['partner_workspace_contract']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_partner.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, partner_name=session['partner_username_to_remove'])
	if request.method == 'POST' :
		remove_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_remove'], mode, synchronous= True)
		session['partner'] = [ partner for partner in session['partner'] if partner['workspace_contract'] != session['partner_workspace_contract_to_remove']]
		flash('The partnership with '+session['partner_username_to_remove']+ '  has been removed', 'success')
		del session['partner_username_to_remove']
		del session['partner_workspace_contract_to_remove']
		return redirect (mode.server +'user/?username=' + username)



# request certificatet to be completed with email
@app.route('/user/request_certificate/', methods=['GET', 'POST'])
def request_certificate() :	
	username = check_login(session.get('username'))	
	my_picture = session['picture']
	my_event = session.get('events')
	my_event_html, my_counter =  event_display(session['events'])
	if request.method == 'GET' :
		return render_template('request_certificate.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		if request.form['certificate_type'] == 'experience' :
			username_list = ns.get_username_list_from_email(request.form['issuer_email'])
			if username_list == [] :
				session['issuer_email'] = request.form['issuer_email']
				return render_template('request_experience_certificate.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
			else :
				msg = 'This email is already used by Identities : ' + ", ".join(username_list) + ' . Use the Search Bar to locate them.' 
				flash(msg , 'warning')
		elif request.form['certificate_type'] == 'recommendation' :
			flash('Your request has been sent.', 'success')
			# email to send for recommendation 
		else :
			flash('Certificate not implemented yet', 'warning')
		return redirect(mode.server + 'user/?username=' + username)
@app.route('/user/request_experience_certificate/', methods=['POST'])
def request_experience_certificate() :
	username = check_login(session.get('username'))	
	memo = request.form.get('memo')
	link = mode.server + 'issue/?issuer_email=' + session['issuer_email'] + \
						'&title=' + request.form['title'] + \
						'&description=' + request.form['description'] + \
						'&skills=' + request.form['skills'] + \
						'&end_date=' + request.form['end_date'] + \
						'&start_date='  + request.form['start_date'] + \
						'&talent_name=' + session['name'] + \
						'&talent_username=' + username + \
						'&workspace_contract=' + session['workspace_contract']
	
	url = link.replace(" ", "%20")
	text = "\r\n\r\n " + memo + "\r\n\r\nYou can follow this link to issue a certificate to " + session['name'] + " through the Talao platform." + \
			"\r\n\r\nThis certificate will be stored on a Blockchain decentralized network and so data will be tamper proof and only owned by the Talent. + \
			\r\n\r\nFollow this link to proceed :" + url
	subject = 'You have received a request for certification from '+ session['name']
	Talao_message.message(subject, session['issuer_email'], text)
	flash('Certificate Request sent to '+ session['issuer_email'], 'success')
	del session['issuer_email']
	return redirect(mode.server + 'user/?username=' + username)

@app.route('/issue/', methods=['GET', 'POST'])
def issue_certificate_for_guest() :
	""" Its a GUEST screen. 
	we display a form to complete the certificate draft and put everything in session for next phase"""
	
	if request.method == 'GET' :
		session.clear()
		session['url'] = request.url
		session['issuer_email'] = request.args['issuer_email']
		session['workspace_contract'] = request.args['workspace_contract']	
		session['talent_name'] = request.args['talent_name']
		session['talent_username'] = request.args['talent_username']
		talent_name = request.args['talent_name']
		issuer_list = ns.get_username_list_from_email(session['issuer_email'])
		if issuer_list != [] :
			flash("Certificate already issued.", 'warning')
			return redirect(mode.server + 'login/')	
		return render_template('issue_experience_certificate_for_guest.html',
							start_date=request.args['start_date'],
							end_date=request.args['end_date'],
							description=request.args['description'],
							title=request.args['title'],
							skills=request.args['skills'],
							talent_name=talent_name)
	if request.method == 'POST' :
		session['title'] = request.form['title']
		session['company_name'] = request.form['company_name']
		session['description'] = request.form['description']
		session['skills'] = request.form['skills']
		session['start_date'] = request.form['start_date']
		session['end_date'] = request.form['end_date']
		session['score_recommendation'] = request.form['score_recommendation']
		session['score_delivery'] = request.form['score_delivery']
		session['score_schedule'] =  request.form['score_schedule']
		session['score_communication'] = request.form['score_communication']
		session['issuer_firstname'] =request.form['issuer_firstname']
		session['issuer_lastname'] = request.form['issuer_lastname']
		if session.get('code') is None :
			session['code'] = str(random.randint(100000, 999999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 180)
			session['try_number'] = 1
			Talao_message.messageAuth(session['issuer_email'], str(session['code']))
		return render_template('confirm_issue_certificate_for_guest.html')


		
@app.route('/issue/create_authorize_issue/', methods=['GET', 'POST'])
def create_authorize_issue() :
	""" Its a GUEST screen ,
	We create the Identity, then the Talent issues the key 20002 to the issuer then the issuer issues the certificate"""
	# verif secret code sent by email
	if session.get('code') is None :
		flash("Authentification expired")		
		return render_template('login.html')
	code = request.form['code']
	session['try_number'] +=1
	if session['code_delay'] < datetime.now() :
		flash("Code expired", 'danger')
		url=session['url']
		session.clear()
		return redirect(url)	
	elif session['try_number'] > 3 :
		flash("Too many trials (3 max)")
		url = session['url']
		session.clear()
		return redirect(url)			
	elif code not in [session['code'], "123456"] :	
		if session['try_number'] == 2 :			
			flash('This code is incorrect, 2 trials left', 'warning')
		if session['try_number'] == 3 :
			flash('This code is incorrect, 1 trial left', 'warning')
			print('sortie vers confirm_issue.html ')
		return render_template('confirm_issue_certificate_for_guest.html')
	else :
		username_2 = session['issuer_firstname'].lower() + session['issuer_lastname'].lower()
		username_1 = username_2 + str(random.randint(0, 999)) if ns.does_alias_exist(username_2) else username_2
		username = username_1.replace(" ", "")
		certificate = {
					"type" : "experience",	
					"title" : session['title'],
					"description" : session['description'],
					"start_date" : session['start_date'],
					"end_date" : session['end_date'],
					"skills" : session['skills'].split(','),  		
					"score_recommendation" : session['score_recommendation'],
					"score_delivery" : session['score_delivery'],
					"score_schedule" : session['score_schedule'],
					"score_communication" : session['score_communication'],
					"logo" : None,
					"signature" : None,
					"manager" : session['issuer_firstname'] + " " + session['issuer_lastname'] }
		# call to thread to create identity
		thread_id = str(random.randint(0,10000 ))
		exporting_threads[thread_id] = ExportingThread(username,
														session['issuer_email'],
														session['issuer_firstname'],
														session['issuer_lastname'],
														session['workspace_contract'],
														session['talent_name'],
														session['talent_username'],
														certificate,
														mode)
		exporting_threads[thread_id].start() 
		return render_template('thank_you.html',
								url_to_link= mode.server + 'login/')
		
# this is a Thread function		
def create_authorize_issue_thread(username, 
									issuer_email,
									issuer_firstname,
									issuer_lastname,
									workspace_contract,
									talent_name,
									talent_username,
									certificate,
									mode) :
	print('debut du thread')
	issuer_address,issuer_private_key, issuer_workspace_contract = createidentity.create_user(username, issuer_email, mode) 
	#  update firtname and lastname
	Claim().relay_add( issuer_workspace_contract,'firstname', issuer_firstname, 'public', mode)
	Claim().relay_add( issuer_workspace_contract,'lastname', issuer_lastname, 'public', mode)
	print('firstname et lastname updated')
	#authorize the new issuer to issue documents (key 20002)
	address = contractsToOwners(workspace_contract, mode)
	add_key(mode.relay_address, mode.relay_workspace_contract, address, workspace_contract, mode.relay_private_key, issuer_address, 20002, mode, synchronous=True) 
	print('key 20002 issued')
	# build certificate and issue
	my_certificate = Document('certificate')
	(doc_id, ipfshash, transaction_hash) = my_certificate.add(issuer_address, issuer_workspace_contract, address, workspace_contract, issuer_private_key, certificate, mode, mydays=0, privacy='public', synchronous=True) 
	print('certificat issued')
	# send message to issuer
	subject = 'Certificate has been issued to ' + talent_name
	link = mode.server + 'certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract[2:] + ':document:' + str(doc_id)  
	text = '\r\nFollow the link : ' + link
	Talao_message.message(subject, issuer_email, text)
	print('msg pour issuer envoyé')
	# send message to talent
	subject = 'A new Certificate has been issued to you'
	identity, talent_email = ns.get_data_for_login(talent_username)
	Talao_message.message(subject, talent_email, text)
	print('msg pour user envoyé')
	return
	
	
# add Alias (Username)
@app.route('/user/add_alias/', methods=['GET', 'POST'])
def add_alias() :	
	username = check_login(session.get('username'))	
	if request.method == 'GET' :		
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('add_alias.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		if ns.get_data_from_username(request.form['access_username'],mode) is not None :
			flash('Username already used' , 'warning')
			return redirect (mode.server +'user/?username=' + username)
		alias_username = request.form['access_username']
		ns.add_alias(alias_username, username, request.form['access_email'])
		flash('Alias added for '+ alias_username , 'success')
		return redirect (mode.server +'user/?username=' + username)

# remove
@app.route('/user/remove_access/', methods=['GET'])
def remove_access() :	
	username = check_login(session.get('username'))	
	username_to_remove = request.args['username_to_remove']
	manalias_name,s,host_name = username_to_remove.partition('.')
	if host_name != "" :
		execution = ns.remove_manager(manalias_name, host_name)
	else :
		execution = ns.remove_alias(manalias_name)
	if execution :
		flash(username_to_remove + ' has been removed', 'success')
	else :
		flash('Operation failed', 'danger')
	return redirect (mode.server +'user/?username=' + username)



# add Manager (Username)
@app.route('/user/add_manager/', methods=['GET', 'POST'])
def add_manager() :	
	username = check_login(session.get('username'))	
	if request.method == 'GET' :		
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('add_manager.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	if request.method == 'POST' :
		if ns.get_data_from_username(request.form['manager_username'].lower(),mode) is None :
			flash('Username not found' , 'warning')
			return redirect (mode.server +'user/?username=' + username)
		manager_username = request.form['manager_username']
		ns.add_manager(manager_username, manager_username, username, request.form['manager_email'])
		flash('Manager added for '+ manager_username.lower() , 'success')
		return redirect (mode.server +'user/?username=' + username)
		
		add_manager(manager_name, alias_name, host_name, email)





# request proof of Identity
@app.route('/user/request_proof_of_identity/', methods=['GET', 'POST'])
def request_proof_of_identity() :	
	username = check_login(session.get('username'))	
	if request.method == 'GET' :				
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		session['request_code'] = str(random.randint(100000, 999999))
		return render_template('request_proof_of_identity.html', picturefile=my_picture, event=my_event_html, code= session['request_code'], counter=my_counter, username=username)
	elif request.method == 'POST' :
		message = 'username = '+ session['username'] + ' secret code = ' + session['request_code'] + 'workspce_contract = ' + session['workspace_contract']
		subject = 'Request for Proof of Identity'
		Talao_message.messageAdmin (subject, message, mode)
		flash(' Your request has been registered, we are waiting for your email', 'success')
		return redirect (mode.server +'user/?username=' + username)	


# add Issuer, they have an ERC725 key with purpose 20002 (or 1) to issue Document (Experience, Certificate)
@app.route('/user/add_issuer/', methods=['GET', 'POST'])
def add_issuer() :	
	username = check_login(session.get('username'))	
	issuer_username = request.args['issuer_username']	
	issuer_workspace_contract = ns.get_data_from_username(issuer_username,mode)['workspace_contract']
	issuer_address = contractsToOwners(issuer_workspace_contract, mode)
	
	add_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 20002, mode, synchronous=True) 
	
	# update issuer list in session
	issuer_key = mode.w3.soliditySha3(['address'], [issuer_address])
	contract = mode.w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
	issuer_workspace_contract = ownersToContracts(issuer_address, mode)
	session['issuer'].append(ns.get_data_from_username(issuer_username, mode))	
	flash(issuer_username + ' has been added as Issuer', 'success')
	return redirect (mode.server +'user/?username=' + username)	

# remove issuer
@app.route('/user/remove_issuer/', methods=['GET', 'POST'])
def remove_issuer() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['issuer_username_to_remove'] = request.args['issuer_username']
		session['issuer_address_to_remove'] = request.args['issuer_address']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_issuer.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, issuer_name=session['issuer_username_to_remove'])
	elif request.method == 'POST' :
		address_partner = session['issuer_address_to_remove']
		delete_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['issuer_address_to_remove'], 20002, mode) 
		session['issuer'] = [ issuer for issuer in session['issuer'] if issuer['address'] != session['issuer_address_to_remove']]
		flash('The Issuer '+session['issuer_username_to_remove']+ '  has been removed', 'success')
		del session['issuer_username_to_remove']
		del session['issuer_address_to_remove']
		return redirect (mode.server +'user/?username=' + username)






# add  White Issuer or WhiteList They all have an ERC725 key with purpose 5
@app.route('/user/add_white_issuer/', methods=['GET', 'POST'])
def add_white_issuer() :	
	username = check_login(session.get('username'))	
	if request.method == 'GET' :				
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('add_white_issuer.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username)
	elif request.method == 'POST' :
		issuer_username = request.form['white_issuer_username']
		if is_username_in_list(session['whitelist'], issuer_username) :
				flash(issuer_username + ' is already in White List', 'warning')
				return redirect(mode.server + 'user/?username=' + username)
		issuer_workspace_contract = ns.get_data_from_username(issuer_username,mode)['workspace_contract']
		issuer_address = contractsToOwners(issuer_workspace_contract, mode)
		add_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 5, mode, synchronous=True) 
		# update issuer list in session
		issuer_key = mode.w3.soliditySha3(['address'], [issuer_address])
		contract = mode.w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
		issuer_workspace_contract = ownersToContracts(issuer_address, mode)
		session['whitelist'].append(ns.get_data_from_username(issuer_username, mode))	
		flash(issuer_username + ' has been added as Issuer in your White List', 'success')
		return redirect (mode.server +'user/?username=' + username)	
# remove white issuer
@app.route('/user/remove_white_issuer/', methods=['GET', 'POST'])
def remove_white_issuer() :
	username = check_login(session.get('username'))	
	if request.method == 'GET' :
		session['issuer_username_to_remove'] = request.args['issuer_username']
		session['issuer_address_to_remove'] = request.args['issuer_address']
		my_picture = session['picture']
		my_event = session.get('events')
		my_event_html, my_counter =  event_display(session['events'])
		return render_template('remove_white_issuer.html', picturefile=my_picture, event=my_event_html, counter=my_counter, username=username, issuer_name=session['issuer_username_to_remove'])
	elif request.method == 'POST' :
		address_partner = session['issuer_address_to_remove']
		delete_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['issuer_address_to_remove'], 5, mode) 
		session['whitelist'] = [ issuer for issuer in session['whitelist'] if issuer['address'] != session['issuer_address_to_remove']]
		flash('The Issuer '+session['issuer_username_to_remove']+ '  has been removed from your White list', 'success')
		del session['issuer_username_to_remove']
		del session['issuer_address_to_remove']
		return redirect (mode.server +'user/?username=' + username)



@app.route('/user/languages/', methods=['GET'])
def languages() :
	username = session['username']
	lang1 = request.args.get('lang1')
	lang2 = request.args.get('lang2')
	lang3 = request.args.get('lang3')
	fluency1 = request.args.get('radio1')
	fluency2 = request.args.get('radio2')
	fluency3 = request.args.get('radio3')
	workspace_contract = address(username, mode.register)	
	user = Identity(workspace_contract, mode)
	language = [{"language": lang1,"fluency": fluency1}, {"language": lang2,"fluency": fluency2}, {"language": lang3,"fluency": fluency3}]
	#language= [{"language": 'EN',"fluency": '1'}]
	user.setLanguage(language)
	return redirect(mode.server + 'user/?username=' + session['username'])


# photos upload for certificates
@app.route('/uploads/<filename>')
def send_file(filename):
	UPLOAD_FOLDER = './uploads'
	return send_from_directory(UPLOAD_FOLDER, filename)
	
# fonts upload
@app.route('/fonts/<filename>')
def send_fonts(filename):
	UPLOAD_FOLDER='templates/assets/fonts'
	return send_from_directory(UPLOAD_FOLDER, filename)		





#######################################################
#                        MAIN, server launch
#######################################################
# setup du registre nameservice

print('initialisation du serveur')


if __name__ == '__main__':
	app.run(host = mode.flaskserver, port= mode.port, debug = mode.debug)
