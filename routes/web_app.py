
from flask import request, redirect, render_template
from flask_babel import _
import logging

PRESENTATION_DELAY = 600 # seconds

DID_WEB = 'did:web:talao.cp'
DID_ETHR = 'did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250'
DID_TZ = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
DID_KEY =  'did:key:zQ3shWBnQgxUBuQB2WGd8iD22eh7nWC4PTjjTjEgYyoC3tjHk'                      

logging.basicConfig(level=logging.INFO)

def init_app(app, red, mode) :
    app.add_url_rule('/app/download',  view_func=app_download, methods = ['GET', 'POST'])
    return

def app_download() :
    return render_template('./wallet/app_download.html')