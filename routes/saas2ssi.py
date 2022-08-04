from flask import jsonify, request, render_template, redirect, session
import json
from datetime import timedelta
from device_detector import SoftwareDetector




def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/saas2ssi',  view_func=saas_login, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas2ssi/menu',  view_func=saas_menu, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas2ssi/verifier',  view_func=saas_verifier, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/saas2ssi/device_detector',  view_func=saas_device_detector, methods = ['GET'])
    app.add_url_rule('/sandbox/saas2ssi/qrcode',  view_func=saas_qrcode, methods = ['GET'], defaults={'mode' : mode})

    app.add_url_rule('/sandbox/saas2ssi/issuer',  view_func=saas_issuer, methods = ['GET', 'POST'])


    return

def saas_qrcode (mode) :
    return render_template('saas_qrcode.html', url = mode.server + '/sandbox/saas2ssi/device_detector' )


def saas_device_detector ():
    ua = request.headers.get('User-Agent')
    device = SoftwareDetector(ua).parse()
    print(device.os_name())
    if device.os_name() == "Android" :
        return redirect("https://play.google.com/store/apps/details?id=co.talao.wallet&hl=fr_FR")
    elif device.os_name() == "iOS" : 
        return redirect("https://apps.apple.com/fr/app/talao-wallet/id1582183266?platform=iphone")
    else :
        return jsonify('unknown device')    

def saas_login():
    if request.method == "GET" :
        return render_template("saas2ssi.html")
    else :
        session["login_name"] = request.form["login_name"]
        if session["login_name"].lower() not in ['ebsilux', "admin1234", "guest"] :
            return redirect('/sandbox/saas2ssi')
        return redirect("/sandbox/saas2ssi/menu")

def saas_menu():
    return render_template("menu.html", login_name=session["login_name"])

def saas_verifier():
    if request.method == "GET" :
        return render_template("saas_verifier.html",
                 login_name=session["login_name"],
                 client_id = "fhwrsmszjn",
                 issuer = "https://talao.co/sandblox/op",
                 client_secret = "9bd6eeb0-0617-11ed-8fe6-8d54d1ffa6d3")
    else :
        session["is_connected"] = True
        return redirect("/sandbox/op/console")

def saas_issuer():
    if request.method == "GET" :
        return render_template("saas_issuer.html",
            link="link"
            )
    else :
        session["is_connected"] = True
        return redirect("/sandbox/op/issuer/console")
