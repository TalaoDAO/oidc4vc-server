from flask import request, render_template, session
import json
import logging
import os
logging.basicConfig(level=logging.INFO)

# dependances
LANGUAGES = ['en', 'fr']
IMAGE_PATH = 'static/directory/'

def init_app(app, mode) :
	app.add_url_rule('/directory', view_func=ssi_directory, methods = ['GET', 'POST'],  defaults={'mode': mode})
	global PATH
	PATH = mode.sys_path + '/Talao/issuers_directory/'
	return


def ssi_directory(mode) :
	card = str()
	if not session.get('language') :
		session['language'] = request.accept_languages.best_match(LANGUAGES)
	provider_list = [filename.lower() for filename in os.listdir(PATH)]
	featured_provider = request.args.get('search', "").lower() + (".json")
	if featured_provider in provider_list :
		provider_list.remove(featured_provider)
		provider_list.insert(0, featured_provider)
	for filename in provider_list :
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
		 	<div class="card m-2 border shadow" >
            	<div class="card-body">
              		<div>
						<a href='""" + provider.get('website',"") + """' >
						<div class="text-center">
							<img src='""" + IMAGE_PATH + provider.get('image', "") + """' class="img-thumbnail " alt="No image">
						</div>
						</a>
					</div>
              		<div class="card-title"><strong>""" + provider.get('name', "") + """</strong></div>
              		<p class="card-text">""" + description_text + """<br>
              		<br>""" + requirement_text + """</p>
            	</div>
            	<ul class="list-group list-group-flush">""" + link + """</ul>
        	</div>"""
	return render_template('directory/directory.html', card=card, server=mode.server)