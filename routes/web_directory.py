from flask import request, render_template, session
import json
import logging
import os
logging.basicConfig(level=logging.INFO)

# dependances
LANGUAGES = ['en', 'fr']

def init_app(app, mode) :
	app.add_url_rule('/directory', view_func=ssi_directory, methods = ['GET', 'POST'])
	global PATH
	PATH = mode.sys_path + '/Talao/issuers_directory/'
	return


def ssi_directory() :
	card = str()
	if not session.get('language') :
		session['language'] = request.accept_languages.best_match(LANGUAGES)
	for filename in os.listdir(PATH) :
		provider = json.load(open(PATH + filename, 'r'))
		description_text = str()
		for description in provider.get('description') :
			if description['@language'] ==  session['language'] :
				description_text = description.get('@value', "")
				break
		requirement_text = str()
		for requirement in provider.get('requirements') :
			if requirement['@language'] ==  session['language'] :
				requirement_text = requirement.get('@value', "")
				break
		link = str()
		for service in provider.get('services') :
			link_text = str()
			for description in service.get('description') :
				if description['@language'] ==  session['language'] :
					link_text = description.get('@value', "")
					break
			link += """<li class="list-group-item"><a href = '"""+ service.get('link', "") + """' class="card-link">""" + link_text + """</a></li>"""
		card +=""" 
		 	<div class="card m-2" >
            	<div class="card-body">
              		<h5 class="card-header">
						<a href='""" + provider.get('website',"") + """' ><img src='""" + provider.get('image', "") + """' class="img-thumbnail" alt="No image"></a>
					</h5>
              		<div class="card-title"><strong>""" + provider.get('name', "") + """</strong></div>
              		<p class="card-text">""" + description_text + """<br>
              		<br>""" + requirement_text + """</p>
            	</div>
            	<ul class="list-group list-group-flush">""" + link + """</ul>
        	</div>"""
	return render_template('directory/directory.html', card=card)