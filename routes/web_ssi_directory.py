from os import path
from flask import request, render_template,abort
import time
import logging
logging.basicConfig(level=logging.INFO)

# dependances


def init_app(app, mode) :
	app.add_url_rule('/dummy_ssi_directory', view_func=ssi_directory, methods = ['GET', 'POST'], defaults={'mode': mode})
	return

def ssi_directory(mode) :
	if mode.myenv == "aws" :
		abort(403)
	return render_template('services/services_xl.html', server=mode.server)