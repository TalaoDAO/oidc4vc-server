from flask import jsonify, request, render_template, redirect, session, flash
import base64
import json
import db_user_api
import logging
import message

logging.basicConfig(level=logging.INFO)


admin_list = ["thierry.thevenet@talao.io", "nicolas.muller@talao.io", "hugo@altme.io", "googandads@gmail.com"]

def init_app(app,red, mode) :

    app.add_url_rule('/',  view_func=home, methods = ['GET', 'POST'])
    app.add_url_rule('/menu',  view_func=menu, methods = ['GET', 'POST'])
    app.add_url_rule('/admin',  view_func=admin, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/callback',  view_func=callback, methods = ['GET', 'POST'], defaults={'mode' : mode}) # signup
    app.add_url_rule('/callback_2',  view_func=callback_2, methods = ['GET', 'POST']) # login
    app.add_url_rule('/logout',  view_func=logout, methods = ['GET', 'POST'])
    app.add_url_rule('/webhook',  view_func=default_webhook, methods = ['POST'])
    
    # access to issuers and verifiers
    app.add_url_rule('/verifier',  view_func=verifier, methods = ['GET', 'POST'])
    app.add_url_rule('/issuer',  view_func=issuer, methods = ['GET', 'POST'])
    
    # test
    app.add_url_rule('/issuer/test',  view_func=issuer_test, methods = ['GET', 'POST'])
    app.add_url_rule('/verifier/test',  view_func=verifier_test, methods = ['GET', 'POST'])
   
    return




def issuer_test() :
    return render_template('issuer_oidc/wallet_issuer_test.html')


def verifier_test() :
    return render_template('ebsi/wallet_verifier_test.html')


def default_webhook() :
     data = request.get_json()   
     return jsonify ('ok')


def home():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        logging.info('remote IP = %s', request.environ['REMOTE_ADDR'])
    else:
        logging.info('remote IP = %s', request.environ['HTTP_X_FORWARDED_FOR']) # if behind a proxy
    return render_template("home.html")

def menu ():
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/')
    return render_template("menu.html", login_name=session["login_name"])


def logout():
    session.clear()
    return redirect ("/")



def admin(mode) :
    if request.method == "GET" :
        return render_template("admin.html")
    
    if request.form['secret'] == mode.admin :
        session['is_connected'] = True
        session['login_name'] = 'admin'
        return render_template("menu.html", login_name=session["login_name"])
    else :
        return redirect ("/")


# Register
def callback(mode):
    if request.args.get("error") :
        logging.warning("access denied")
        session.clear()
        return redirect ("/")
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
            message.message("Registration on Saas Altme of " + login_name , "thierry@altme.io", "New user = " + login_name, mode)
        except :
            pass
        return redirect ('/menu')
    else :
        logging.warning('user already exists')
        flash("You are already registered, you can login !", "warning")
        return redirect ("/")


# login
def callback_2():
    if request.args.get("error") :
        logging.warning("access denied")
        session.clear()
        return redirect ("/")
    id_token = request.args['id_token']
    s = id_token.split('.')[1]
    payload = base64.urlsafe_b64decode(s + '=' * (4 - len(s) % 4))
    login_name = json.loads(payload.decode())['email']
    if login_name in admin_list :
        session['login_name'] = "admin"
        session['is_connected'] = True
        return redirect ('/menu')
    elif db_user_api.read(login_name) :
        session['login_name'] = login_name
        session['is_connected'] = True
        return redirect ('/menu')
    else :
        logging.warning('erreur, user does not exist')
        session.clear()
        return render_template ("access_denied.html")


def verifier() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/')
    return redirect ('/verifier/console/select')


def issuer() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return redirect ('/issuer/console/select')
