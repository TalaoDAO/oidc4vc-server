import os
import time
import markdown
from flask import Flask, redirect, request, render_template_string, request
from flask_session import Session
from flask_mobility import Mobility

from datetime import timedelta
from flask_qrcode import QRcode
import redis
import sys
import logging
import environment
#from components import message

logging.basicConfig(level=logging.INFO)
logging.info("python version : %s", sys.version)

# Environment variables set in gunicornconf.py  and transfered to environment.py
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')
if not myenv :
   myenv='local'
logging.info('start to init environment')
mode = environment.currentMode(mychain,myenv)
logging.info('end of init environment')

# Redis init red = redis.StrictRedis()
red= redis.Redis(host='localhost', port=6379, db=0)

# Centralized  routes : modules in ./routes
from routes import verifier_console, issuer_console, api_verifier, api_issuer
from routes import  web_wallet_test
from routes import web_display_VP
from routes import saas4ssi
from routes import beacon_issuer_console, api_issuer_beacon
from routes import api_verifier_beacon, beacon_verifier_console
from routes import api_verifier_ebsi, ebsi_verifier_console
from routes import api_issuer_ebsi, ebsi_issuer_console

# Framework Flask and Session setup
app = Flask(__name__)
app.jinja_env.globals['Version'] = "0.2.2"
app.jinja_env.globals['Created'] = time.ctime(os.path.getctime('main.py'))
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_COOKIE_NAME'] = 'talao'
app.config['SESSION_TYPE'] = 'redis' # Redis server side session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30) # cookie lifetime
app.config['SESSION_FILE_THRESHOLD'] = 100
app.config['SECRET_KEY'] = "OCML3BRawWEUeaxcuKHLpw" + mode.password
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["jpeg", "jpg", "png", "gif"]

sess = Session()
sess.init_app(app)
qrcode = QRcode(app)
Mobility(app)

@app.errorhandler(403)
def page_abort(e):
    logging.warning('abort 403')
    return redirect(mode.server + 'login/')

"""
@app.errorhandler(500)
def error_500(e):
    message.message("Error 500 on sandbox", 'thierry.thevenet@talao.io', str(e) , mode)
    return redirect(mode.server + '/sandbox')
"""


# BASIC wallet protocol
api_verifier.init_app(app, red, mode)
api_issuer.init_app(app, red, mode)
verifier_console.init_app(app, red, mode)
issuer_console.init_app(app, red, mode)

# EBSI wallet
ebsi_verifier_console.init_app(app, red, mode)
api_verifier_ebsi.init_app(app, red, mode)
ebsi_issuer_console.init_app(app, red, mode)
api_issuer_ebsi.init_app(app, red, mode)

# BEACON integration
api_issuer_beacon.init_app(app, red, mode)
api_verifier_beacon.init_app(app, red, mode)
beacon_verifier_console.init_app(app, red, mode)
beacon_issuer_console.init_app(app, red, mode)

# MAIN
saas4ssi.init_app(app, red, mode)
web_display_VP.init_app(app, red, mode)
web_wallet_test.init_app(app, red, mode)


@app.route('/sandbox/md_file', methods = ['GET'])
def md_file() :
	#https://dev.to/mrprofessor/rendering-markdown-from-flask-1l41
    if request.args['file'] == 'privacy' :
        content = open('privacy_en.md', 'r').read()
    elif request.args['file'] == 'terms_and_conditions' :
        content = open('mobile_cgu_en.md', 'r').read()
    return render_template_string( markdown.markdown(content, extensions=["fenced_code"]))


# MAIN entry point for test
if __name__ == '__main__':
    # info release
    logging.info('flask test serveur run with debug mode')
    app.run(host = mode.flaskserver,
             port= mode.port,
               debug = mode.test,
                 threaded=True)