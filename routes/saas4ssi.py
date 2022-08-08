from flask import jsonify, request, render_template, redirect, session
from device_detector import SoftwareDetector


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/saas4ssi',  view_func=saas_login, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/verifier',  view_func=saas_verifier, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas4ssi/device_detector',  view_func=saas_device_detector, methods = ['GET'])
    app.add_url_rule('/sandbox/saas4ssi/qrcode',  view_func=saas_qrcode, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/saas4ssi/issuer',  view_func=saas_issuer, methods = ['GET', 'POST'])
    return


def saas_qrcode (mode) :
    return render_template('saas_qrcode.html', url = mode.server + '/sandbox/saas4ssi/device_detector' )


def saas_device_detector ():
    ua = request.headers.get('User-Agent')
    device = SoftwareDetector(ua).parse()
    print(device.os_name())
    if device.os_name() == "Android" :
        return redirect("https://play.google.com/store/apps/details?id=co.altme.alt.me.altme")
    elif device.os_name() == "iOS" : 
        return redirect("https://apps.apple.com/fr/app/talao-wallet/id1582183266?platform=iphone")
    else :
        return jsonify('unknown device')    


def saas_login():
    if request.method == "GET" :
        return render_template("saas4ssi.html")
    else :
        if request.form["login_name"].lower() not in ['ebsilux', "admin1234", "guest"] :
            return redirect('/sandbox/saas4ssi')
        session["login_name"] = request.form["login_name"].lower()
        session['is_connected'] = True
        return render_template("menu.html", login_name=session["login_name"])


def saas_verifier():
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == "GET" :
        return render_template("saas_verifier.html")
    else :
        return redirect("/sandbox/op/console")


def saas_issuer() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == "GET" :
        return render_template("saas_issuer.html")
    else :
        return redirect("/sandbox/op/issuer/console")
