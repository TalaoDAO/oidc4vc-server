
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
mychain = 'talaonet'

logging.info('start to init environment')
mode = environment.currentMode(mychain,myenv)
logging.info('end of init environment')

# Redis init red = redis.StrictRedis()
red= redis.Redis(host='localhost', port=6379, db=0)

# Centralized  routes : modules in ./routes
#from routes import web_revocationlist
#from r!outes import web_wallet_return_code
from routes import web_wallet_api
from routes import  web_wallet_test, web_app 
from routes import web_display_VP


#BUNNEY Calum <calum.bunney@nexusgroup.com>
# Server Release
VERSION = '1.67'
logging.info('Talao version : %s', VERSION)

# Framework Flask and Session setup
app = Flask(__name__)
app.jinja_env.globals['Version'] = VERSION
app.jinja_env.globals['Created'] = time.ctime(os.path.getctime('main.py'))
app.jinja_env.globals['Chain'] = mychain.capitalize()
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
CORS(app)

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
web_wallet_api.init_app(app, red, mode)


web_display_VP.init_app(app, red, mode)
#web_revocationlist.init_app(app, red, mode) see latyer use

web_app.init_app(app, red, mode)
#web_wallet_return_code.init_app(app, red, mode)


logging.info('end init routes')



# MAIN entry point for test
if __name__ == '__main__':
    # info release
    logging.info('flask test serveur run with debug mode')
    app.run(host = mode.flaskserver, port= mode.port, debug = mode.test, threaded=True)