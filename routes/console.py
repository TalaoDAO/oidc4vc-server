from flask import  request, render_template, redirect, session
from flask import session,jsonify
import json
import logging
import didkit
import random
import requests
import verifier_db_api 
from urllib.parse import urlencode


logging.basicConfig(level=logging.INFO)



credential_list = {
                    'EmailPass' : 'Proof of email',
                    'Kyc' : 'Identity card',
                    'Over18' : 'Over 18',
                    'Tez_Voucher_1' : "Voucher 15% Tezotopia",
                    'LearningAchievement' : 'Diploma',
                    'StudentCard' : 'Student card',
                    'CertificateOfEmployment' : 'Certificate of employment',
                    'DID' : "Decentralized Identifier",
                    'ANY' : 'Any'
                }

protocol_list = {'w3cpr' : "W3C Presentation Request ",
                 'openid4vc' : 'OpenID 4 VC'
                 }

client_data_pattern = {
                "client_id" :  "",
                "client_secret" : "",
                "jwk" : "",
                "method" : "",
                "company_name" : "",
                "reason" : "",
                "authorized_emails" : "",
                "vc" : "",
                "protocol" : "",
                "qrcode_message" : "",
                "mobile_message" : "",
                "emails" : None
                }

did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/console/login',  view_func=console_login, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/console/callback',  view_func=console_callback, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/console/logout',  view_func=console_logout, methods = ['GET', 'POST'], defaults={'mode' : mode})

    app.add_url_rule('/sandbox/console',  view_func=console, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/console/select',  view_func=select, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/console/advanced',  view_func=advanced, methods = ['GET', 'POST'])

    return



# parameters provided by platform
client_id = 'gajjfwdbhy'
client_secret = 'a86c8a1e-fb80-11ec-ad02-db56768956ef'


# website homepage
def console_login(mode) :
    if not session.get('is_connected') :
        data = {
                'response_type': 'code',
                'client_id': client_id,
                'state': str(random.randint(0, 99999)),
                'nonce' :  str(random.randint(10000, 999999)), 
                'redirect_uri': mode.server + 'sandbox/console/callback',
                'scope': 'openid'    }
        session['data'] = data
        return redirect('/sandbox/authorize?' + urlencode(data))
    
    else  :
        print('user is connected in console')
        return redirect('/sandbox/console')
    


def console_callback(mode):
    if 'error' in request.args :
            session['is_connected'] = False
            print('error = ', request.args['error'])
            return redirect('/')
    
    data = {
        'grant_type': 'authorization_code',
        'redirect_uri': mode.server + 'sandbox/console/callback',
        'code': request.args['code']
    }
    response = requests.post(mode.server + 'sandbox/token', data=data, auth=(client_id, client_secret))

    if response.status_code == 200:
        #token_data = response.json() emails filtering
        session['is_connected'] = True
        print('passé ici')
        return redirect('../console')
    else :
        session['is_connected'] = False
        return redirect('sandbox/console')
      


def console_logout(mode):
    if not session.get('is_connected') :
        return redirect('sandbox/console/login')
    session.clear()
    print("logout envoyé")
    response = requests.post(mode.server + 'sandbox/logout', data="")
    return redirect('sandbox/console')



def select() :
    if not session.get('is_connected') :
        return redirect('/sandbox/console/login')

    if request.method == 'GET' :  
        my_list = verifier_db_api.list_verifier()
        select=str()
        for data in my_list :
            data_dict = json.loads(data)
            data_displayed = "client_id : " + data_dict['client_id'] +  "&nbsp&nbsp&nbsp&nbsp" + "client_secret : " + data_dict['client_secret'] + "&nbsp&nbsp&nbsp&nbsp" +  "company name : " + data_dict['company_name'] 
            select +=  "<option value=" + data_dict['client_id'] + ">" + data_displayed + "</option>"      
        return render_template('select.html', select=select) 
    else :
        client_id = request.form['client_id']
        return redirect ('/sandbox/console?client_id=' + client_id)



def console(mode) :
    global vc, reason
    if not session.get('is_connected') :
        return redirect('/sandbox/console/login')
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            return redirect('/sandbox/console/select')
        else  :
            session['client_id'] = request.args.get('client_id')
        session['client_data'] = json.loads(verifier_db_api.read_verifier(session['client_id']))
        vc_select = str()
        for key, value in credential_list.items() :
                if key ==   session['client_data']['vc'] :
                    vc_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    vc_select +=  "<option value=" + key + ">" + value + "</option>"

        print(session['client_data'])
        return render_template('console.html',
                client_id= session['client_data']['client_id'],
                client_secret= session['client_data']['client_secret'],
                token=mode.server + 'sandbox/authorize',
                authorization=mode.server + 'sandbox/token',
                logout=mode.server + 'sandbox/logout',
                company_name = session['client_data']['company_name'],
                reason = session['client_data']['reason'],
                qrcode_message = session['client_data'].get('qrcode_message', ""),
                mobile_message = session['client_data'].get('mobile_message', ""),
                vc_select=vc_select,
                )
    if request.method == 'POST' :
        if request.form['button'] == "new" :
            return redirect('/sandbox/console?client_id=' + verifier_db_api.create_verifier())
        
        elif request.form['button'] == "select" :
            return redirect ('/sandbox/console/select')
        
        elif request.form['button'] == "delete" :
            verifier_db_api.delete_verifier( request.form['client_id'])
            return redirect ('/sandbox/console')

        elif request.form['button'] == "logout" :
            session.clear()
            return redirect ('/sandbox/console')

        elif request.form['button'] == "advanced" :
            return redirect ('/sandbox/console/advanced')
        
        elif request.form['button'] == "update" :
            session['client_data']['client_id'] =  request.form['client_id']
            session['client_data']['client_secret'] = request.form['client_secret']
            session['client_data']['company_name'] = request.form['company_name']
            session['client_data']['reason'] = request.form.get('reason', "")
            session['client_data']['vc'] = request.form['vc']
            session['client_data']['qrcode_message'] = request.form['qrcode_message']
            session['client_data']['mobile_message'] = request.form['mobile_message']          
            verifier_db_api.update_verifier( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/console?client_id=' + request.form['client_id'])
        else :
            return redirect('/sandbox/console')

def advanced() :
    global vc, reason
    if not session.get('is_connected') :
        return redirect('/sandbox/console/login')
    if request.method == 'GET' :
        session['client_data'] = json.loads(verifier_db_api.read_verifier(session['client_id']))
        print(session['client_data'])
        protocol_select = vc_select = str()
        did = ""
        for method in ['tz', 'key', 'ethr', 'sol', 'pkh:tz', 'ion'] :
            if session['client_data'].get('method') == method :
                try :
                    did += "<option selected value=" + method + ">" + didkit.key_to_did(method,session['client_data']['jwk']) + "</option>"
                except :
                    pass
            else :
                try :
                    did += "<option value=" + method + ">" + didkit.key_to_did(method,session['client_data']['jwk']) + "</option>"
                except :
                    pass

        for key, value in credential_list.items() :
                if key ==   session['client_data']['vc'] :
                    vc_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    vc_select +=  "<option value=" + key + ">" + value + "</option>"

        for key, value in protocol_list.items() :
                if key ==   session['client_data'].get('protocol', "") :
                    protocol_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    protocol_select +=  "<option value=" + key + ">" + value + "</option>"
        if session['client_data'].get('emails') :
            emails_filtering = """<input class="form-check-input" checked type="checkbox" name="emails" value="ON" id="flexCheckDefault">"""
        else :
            emails_filtering = """<input class="form-check-input" type="checkbox" name="emails" value="ON" id="flexCheckDefault">"""
        return render_template('advanced.html',
                client_id = session['client_data']['client_id'],
                jwk = session['client_data']['jwk'],
                did=did,
                authorized_emails = session['client_data']['authorized_emails'],
                protocol = session['client_data']['protocol'],
                emails_filtering=emails_filtering,
                protocol_select=protocol_select
                )
    if request.method == 'POST' :

        if request.form['button'] == "back" :
            return redirect ('/sandbox/console?client_id=' + request.form['client_id'] )
        
        elif request.form['button'] == "update" :
            session['client_data']['jwk'] = request.form['jwk']
            session['client_data']['method'] = request.form['method']
            session['client_data']['authorized_emails'] = request.form.get('authorized_emails', "")
            session['client_data']['protocol'] = request.form['protocol']
            session['client_data']['emails'] = request.form.get('emails')
            verifier_db_api.update_verifier( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/console?client_id=' + request.form['client_id'])
          

