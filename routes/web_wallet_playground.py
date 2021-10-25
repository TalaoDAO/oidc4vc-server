from flask import jsonify, request, render_template, Response, render_template_string, redirect, url_for

import logging
from flask_babel import Babel, _

logging.basicConfig(level=logging.INFO)

def init_app(app,red, mode) :
    app.add_url_rule('/wallet/playground',  view_func=playground, methods = ['GET', 'POST'], defaults={'red' :red, 'mode' : mode})
    return

def playground(red, mode) :
    return render_template("./wallet/test/playground.html")

 