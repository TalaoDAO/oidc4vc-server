import os
import time
from flask import Flask, redirect
from flask_session import Session
from datetime import timedelta
from flask_qrcode import QRcode
import redis
import sys
import logging
import environment

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

# Server Release
VERSION = "2.8"
logging.info('Talao version : %s', VERSION)

# Framework Flask and Session setup
app = Flask(__name__)
app.jinja_env.globals['Version'] = VERSION
app.jinja_env.globals['Created'] = time.ctime(os.path.getctime('main.py'))
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_COOKIE_NAME'] = 'talao'
app.config['SESSION_TYPE'] = 'redis' # Redis server side session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=360) # cookie lifetime
app.config['SESSION_FILE_THRESHOLD'] = 100
app.config['SECRET_KEY'] = "OCML3BRawWEUeaxcuKHLpw" + mode.password
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["jpeg", "jpg", "png", "gif"]

sess = Session()
sess.init_app(app)
qrcode = QRcode(app)

@app.errorhandler(403)
def page_abort(e):
    """
    we set the 403 status explicitly
    """
    logging.warning('abort 403')
    return redirect(mode.server + 'login/')

logging.info('start init routes')
# Centralized @route
web_wallet_test.init_app(app, red, mode)
api_verifier.init_app(app, red, mode)
api_issuer.init_app(app, red, mode)
verifier_console.init_app(app, red, mode)
issuer_console.init_app(app, red, mode)
saas4ssi.init_app(app, red, mode)

web_display_VP.init_app(app, red, mode)
logging.info('end init routes')

# MAIN entry point for test
if __name__ == '__main__':
    # info release
    logging.info('flask test serveur run with debug mode')
    app.run(host = mode.flaskserver, port= mode.port, debug = mode.test, threaded=True)