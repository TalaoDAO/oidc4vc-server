from flask import jsonify, request, render_template, redirect, session
from device_detector import SoftwareDetector


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/saas4ssi',  view_func=saas_home, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/verifier',  view_func=saas_verifier, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/device_detector',  view_func=saas_device_detector, methods = ['GET'])
    app.add_url_rule('/sandbox/saas4ssi/qrcode',  view_func=saas_qrcode, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/saas4ssi/issuer',  view_func=saas_issuer, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/menu',  view_func=saas_menu, methods = ['GET', 'POST'])

    app.add_url_rule('/sandbox/saas4ssi/pricing',  view_func=pricing, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing/gaming',  view_func=pricing_gaming, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing/defi',  view_func=pricing_defi, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing/marketplace',  view_func=pricing_marketplace, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing/issuer',  view_func=pricing_issuer, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/pricing/web2',  view_func=pricing_web2, methods = ['GET', 'POST'])

    app.add_url_rule('/sandbox/saas4ssi/offers',  view_func=saas_home, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/credentials',  view_func=credentials, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/login',  view_func=saas_login, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/logout',  view_func=saas_logout, methods = ['GET', 'POST'])


    return


def saas_qrcode (mode) :
    return render_template('saas_qrcode.html', url = mode.server + '/sandbox/saas4ssi/device_detector' )


def saas_device_detector ():
    ua = request.headers.get('User-Agent')
    device = SoftwareDetector(ua).parse()
    if device.os_name() == "Android" :
        return redirect("https://play.google.com/store/apps/details?id=co.altme.alt.me.altme")
    elif device.os_name() == "iOS" : 
        return redirect("https://apps.apple.com/fr/app/altme/id1633216869")
    else :
        return jsonify('unknown device')    

def saas_home():
    session.clear()
    return render_template("home.html")


def credentials():
    return render_template("credentials.html")

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
    return render_template("menu.html", login_name=session["login_name"])


def saas_logout():
    session.clear()
    return redirect ("/sandbox/saas4ssi")

def saas_login():
    if request.method == "GET" :
        return render_template("saas_login.html")
    else :
        if request.form["login_name"].lower() not in ['ebsilux', "admin1234", "guest", "arago1234"] :
            return redirect('/sandbox/saas4ssi')
        print(request.form["login_name"].lower())
        session["login_name"] = request.form["login_name"].lower()
        session['is_connected'] = True
        return render_template("menu.html", login_name=session["login_name"])


def saas_verifier():
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    else :
        return redirect ('/sandbox/op/console/select')



def saas_issuer() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return redirect ('/sandbox/op/issuer/console/select')
