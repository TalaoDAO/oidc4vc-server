
from flask import Flask, session, send_from_directory, flash, send_file, abort
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
from flask_fontawesome import FontAwesome
import unidecode

# dependances
import constante
from protocol import Document
import environment



# environment setup
mode = environment.currentMode()
w3 = mode.w3

def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if session.get('username') is None :
		abort(403)
	else :
		return session['username']



# route user/update_skills/
def update_skills() :
	check_login()
	if request.method == 'GET' :		
		if session['skills'] is not None :
			skills = session['skills']['description']
			#description = [{'skill_code' : 'consulting' ,'skill_name' : 'consulting', 'skill_level' : 'intermediate', 'skill_domain' : 'industry'},] 	
			skills_row = ""
			for counter, skill in enumerate(skills, 0) :
				#skill_level = 'Intermed.' if skill['skill_level'] == 'Intermediate' else skill['skill_level'] 
				skill_level = skill['skill_level']
				form_row = """
					<div class="form-row">
						  <div class="col-4 col-sm-4 col-lg-4 col-xl-4">
                       
                            <div class="form-group">
								<p> """ + skill['skill_name'] + """</p>
							</div>
                         </div>
                         
                        <!--   <div class="col-3 col-sm-3 col-lg-3 col-xl-3">
                             <div class="form-group">
								<p>""" + skill['skill_domain'] + """</p>
							</div>
                         </div>
                        --> 
                         
                           <div class="col-4 col-sm-4 col-lg-4 col-xl-4">
                         
                            <div class="form-group">
								<p> """ + skill_level + """</p>
							</div>	
                         </div>
                           <div class="col-4 col-sm-4 col-lg-4 col-xl-4">
                        
                             <div class="form-group">
								<div class="text-center">
									<button title="Delete first if you want to update." class="btn btn-secondary btn-sm" name="choice" value=""" + str(counter) + """ type="submit">Delete</button></div>
								</div>
							</div>
                     </div>"""
				skills_row = form_row + skills_row									
		else :
			skills_row = ""
			
		return render_template('update_skills.html', **session['menu'], skills_row=skills_row)
	
	if request.method == 'POST' :
		# add a skill
		if request.form['choice'] == 'add' :
			skill_code = unidecode.unidecode(request.form['skill_name'].lower())
			skill_code = skill_code.replace(" ", "")
			skill_code = skill_code.replace("-", "")
			skill = {'skill_code' : skill_code,
									'skill_name' : request.form['skill_name'].capitalize(),
									'skill_level' : request.form['skill_level'],
									'skill_domain' : ""}
			if session['skills'] is None  :
				session['skills'] = dict()
				session['skills']['description'] = []
				session['skills']['version'] = 1
			for one_skill in session['skills']['description'] :
				if one_skill['skill_code'] == skill_code :
					flash('Skill alreday added', 'warning')
					return redirect(mode.server + 'user/update_skills/')
			if skill_code == "" :
				return redirect(mode.server + 'user/update_skills/')			
			else :
				session['skills']['description'].append(skill)												
				return redirect(mode.server + 'user/update_skills/')
		# update the skill document
		elif request.form['choice'] == 'update' :
			# case update before add first time
			if session['skills'] is None :
				return redirect( mode.server + 'user/')
			# update first time
			elif session['skills'].get('doc_id') is None :
				my_skills = Document('skills')
				skill_data = {'version' : session['skills']['version'],  'description' : session['skills']['description']}
				data = my_skills.relay_add(session['workspace_contract'], skill_data, mode)
				if data is None :
					flash('Transaction failed', 'danger')
					return redirect( mode.server + 'user/')
				doc_id = data[0]
				session['skills']['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] +':document:' + str(doc_id)  
				
			# standard update
			else :
				my_skills = Document('skills')
				skill_data = {'version' : session['skills']['version'], 'description' : session['skills']['description']}
				data = my_skills.relay_update(session['workspace_contract'], session['skills']['doc_id'], skill_data, mode)
				if data is None :
					flash('Transaction failed', 'danger')
					return redirect( mode.server + 'user/')
				doc_id = data[0]
				session['skills']['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] +':document:' + str(doc_id)  
			flash('Your skills have been updated', 'success')	
			return redirect( mode.server + 'user/')
		
		# delete the skill 	
		else :
			counter = request.form['choice']
			del session['skills']['description'][int(counter)]
			return redirect (mode.server + 'user/update_skills/')

