from flask import render_template

import logging
from flask_babel import Babel, _

logging.basicConfig(level=logging.INFO)

def init_app(app,red, mode) :
    app.add_url_rule('/wallet/playground',  view_func=playground, methods = ['GET', 'POST'])
    return

def playground() :
    return render_template("./wallet/test/playground.html")

 