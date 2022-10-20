from flask import render_template


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/saas4ssi/dapp',  view_func=dapp_wallet, methods = ['GET', 'POST'])
    return

def dapp_wallet():
   return render_template('dapp.html')
