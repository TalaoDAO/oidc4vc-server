from flask import jsonify, request, render_template, redirect, session, flash
import base64
import json
import db_user_api
import op_constante
import logging
import message

logging.basicConfig(level=logging.INFO)


admin_list = ["thierry.thevenet@talao.io", "nicolas.muller@talao.io", "hugo@altme.io", "googandads@gmail.com"]

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/saas4ssi',  view_func=saas_home, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/dids',  view_func=dids, methods = ['GET'])

    app.add_url_rule('/sandbox/saas4ssi/verifier',  view_func=saas_verifier, methods = ['GET', 'POST'])
    #app.add_url_rule('/sandbox/saas4ssi/device_detector',  view_func=saas_device_detector, methods = ['GET'])
    app.add_url_rule('/sandbox/saas4ssi/issuer',  view_func=saas_issuer, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/beacon',  view_func=saas_beacon, methods = ['GET', 'POST'])

    app.add_url_rule('/sandbox/saas4ssi/beacon/verifier',  view_func=saas_beacon_verifier, methods = ['GET', 'POST'])


    app.add_url_rule('/sandbox/saas4ssi/menu',  view_func=saas_menu, methods = ['GET', 'POST'])

    app.add_url_rule('/sandbox/saas4ssi/credential_supported',  view_func=credential_supported, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing',  view_func=pricing, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing/gaming',  view_func=pricing_gaming, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing/defi',  view_func=pricing_defi, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing/marketplace',  view_func=pricing_marketplace, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing/issuer',  view_func=pricing_issuer, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing/web2',  view_func=pricing_web2, methods = ['GET', 'POST'])

    app.add_url_rule('/sandbox/saas4ssi/offers',  view_func=saas_home, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/credentials',  view_func=credentials, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/verifier_home',  view_func=verifier, methods = ['GET', 'POST'])

    app.add_url_rule('/sandbox/saas4ssi/login',  view_func=saas_login, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/saas4ssi/signup',  view_func=saas_signup, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/saas4ssi/admin',  view_func=admin, methods = ['GET', 'POST'], defaults={'mode' : mode})

    app.add_url_rule('/sandbox/saas4ssi/callback',  view_func=saas_callback, methods = ['GET', 'POST'], defaults={'mode' : mode}) # signup
    app.add_url_rule('/sandbox/saas4ssi/callback_2',  view_func=saas_callback_2, methods = ['GET', 'POST']) # login

    app.add_url_rule('/sandbox/saas4ssi/logout',  view_func=saas_logout, methods = ['GET', 'POST'])

    app.add_url_rule('/sandbox/saas4ssi/webhook',  view_func=default_webhook, methods = ['POST'])


    return

"""
def saas_device_detector ():
    ua = request.headers.get('User-Agent')
    device = SoftwareDetector(ua).parse()
    if device.os_name() == "Android" :
        return redirect("https://play.google.com/store/apps/details?id=co.altme.alt.me.altme")
    elif device.os_name() == "iOS" : 
        return redirect("https://apps.apple.com/fr/app/altme/id1633216869")
    else :
        return jsonify('unknown device')    
"""

def default_webhook() :
     data = request.get_json()   
     return jsonify ('ok')

def saas_home():
    if request.args.get('pricing') == 'on' :
        session['pricing'] = True
    return render_template("home.html")


def credentials():
    return render_template("credentials.html")


def credential_supported():
    return render_template("credential_supported.html")

def verifier():
    print('verifier')
    return render_template("verifier.html")

def dids():
    return render_template("dids.html")

def pricing():
    return render_template("pricing.html")
def pricing_gaming():
    return render_template("pricing_gaming.html")
def pricing_defi():
    return render_template("pricing_defi.html")
def pricing_marketplace():
    return render_template("pricing_marketplace.html")
def pricing_issuer():
    return render_template("pricing_issuer.html")
def pricing_web2():
    return render_template("pricing_web2.html")

def saas_menu ():
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return render_template("menu.html", login_name=session["login_name"])


def saas_logout():
    session.clear()
    return redirect ("/sandbox/saas4ssi")


def saas_login(mode):
    if mode.myenv == 'aws':
        client_id = "cbtzxuotun"
    elif mode.server == "http://192.168.0.65:3000/" :
        client_id = "zpfzzwfstl"
    else :
        client_id = "grtqvinups"
    url = mode.server + "sandbox/op/authorize?client_id=" + client_id +"&response_type=id_token&response_mode=query&redirect_uri=" + mode.server + "sandbox/saas4ssi/callback_2"
    return redirect (url)
       

def saas_signup(mode):
    if mode.myenv == 'aws':
        client_id = "ovuifzktle"
    elif mode.server == "http://192.168.0.65:3000/" :
        client_id = "evqozlvnsm"
    else :
        client_id = "tjxhcdbxei"
    url = mode.server + "sandbox/op/authorize?client_id=" + client_id +"&response_type=id_token&response_mode=query&redirect_uri=" + mode.server + "sandbox/saas4ssi/callback"
    return redirect (url)


def admin(mode) :
    if request.method == "GET" :
        return render_template("admin.html")
    if request.form['secret'] == mode.admin :
        session['is_connected'] = True
        session['login_name'] = 'admin'
        return render_template("menu.html", login_name=session["login_name"])
    else :
        return redirect ("/sandbox/saas4ssi")


# sign up
def saas_callback(mode):
    if request.args.get("error") :
        logging.warning("access denied")
        session.clear()
        return redirect ("/sandbox/saas4ssi")
    id_token = request.args['id_token']
    s = id_token.split('.')[1]
    payload = base64.urlsafe_b64decode(s + '=' * (4 - len(s) % 4)) 
    login_name = json.loads(payload.decode())['email']
    if not db_user_api.read(login_name) :
        data = op_constante.user
        data["did"] = json.loads(payload.decode())['sub']
        data['login_name'] = session['login_name'] = login_name
        session['is_connected'] = True
        db_user_api.create(login_name, data)
        try :
            message.message("New sign up on Altme", "thierry@altme.io", "New user = " + login_name, mode)
        except :
            pass
        return redirect ('/sandbox/saas4ssi/menu')
    else :
        logging.warning('erreur, user exists')
        #message.message("User tried to sign up 2 times", "thierry@altme.io", "user = " + login_name, mode)
        #session.clear()
        flash("You are already registered as a user !", "error")
        return redirect ("/sandbox/saas4ssi")

# login
def saas_callback_2():
    if request.args.get("error") :
        logging.warning("access denied")
        session.clear()
        return redirect ("/sandbox/saas4ssi")
    id_token = request.args['id_token']
    s = id_token.split('.')[1]
    payload = base64.urlsafe_b64decode(s + '=' * (4 - len(s) % 4))
    login_name = json.loads(payload.decode())['email']
    if login_name in admin_list :
        session['login_name'] = "admin"
        session['is_connected'] = True
        return redirect ('/sandbox/saas4ssi/menu')
    elif db_user_api.read(login_name) :
        session['login_name'] = login_name
        session['is_connected'] = True
        return redirect ('/sandbox/saas4ssi/menu')
    else :
        logging.warning('erreur, user does not exist')
        session.clear()
        return render_template ("access_denied.html")


def saas_verifier():
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    else :
        return redirect ('/sandbox/op/console/select')



def saas_issuer() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return redirect ('/sandbox/op/issuer/console/select')




def saas_beacon() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return redirect ('/sandbox/op/beacon/console/select')



def saas_beacon_verifier() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return redirect ('/sandbox/op/beacon/verifier/console/select')
