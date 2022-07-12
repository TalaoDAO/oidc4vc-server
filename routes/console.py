from flask import  request, render_template, redirect, session
import json
import logging
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
    app.add_url_rule('/sandbox/op/console/login',  view_func=console_login, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/console/callback',  view_func=console_callback, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/console/logout',  view_func=console_logout, methods = ['GET', 'POST'], defaults={'mode' : mode})

    app.add_url_rule('/sandbox/op/console',  view_func=console, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/console/select',  view_func=select, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/console/advanced',  view_func=advanced, methods = ['GET', 'POST'])
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
                'redirect_uri': mode.server + 'sandbox/op/console/callback',
                'scope': 'openid'    }
        session['data'] = data
        return redirect('/sandbox/op/authorize?' + urlencode(data))
    else  :
        return redirect('/sandbox/op/console')
    


def console_callback(mode):
    if 'error' in request.args :
            session['is_connected'] = False
            return redirect('/')
    
    data = {
        'grant_type': 'authorization_code',
        'redirect_uri': mode.server + 'sandbox/op/console/callback',
        'code': request.args['code']
    }
    response = requests.post(mode.server + 'sandbox/op/token', data=data, auth=(client_id, client_secret))

    if response.status_code == 200:
        session['is_connected'] = True
    else :
        session['is_connected'] = False
    return redirect('/sandbox/op/console')
      


def console_logout(mode):
    if not session.get('is_connected') :
        return redirect('sandbox/op/console/login')
    session.clear()
    response = requests.post(mode.server + 'sandbox/logout', data="")
    return redirect('/sandbox/op/console')



def select() :
    if not session.get('is_connected') :
        return redirect('/sandbox/op/console/login')

    if request.method == 'GET' :  
        my_list = verifier_db_api.list_verifier()
        verifier_list=str()
        for data in my_list :
            data_dict = json.loads(data)
            verifier = """<tr>
                <td>""" + data_dict['company_name'] + """</td>
                <td><a href=/sandbox/op/console?client_id=""" + data_dict['client_id'] + """>""" + data_dict['client_id'] + """</a></td>
                <td>""" + data_dict['client_secret'] + """</td>
                <td>""" + data_dict['vc'] + """</td>
                </tr>"""
            verifier_list += verifier
            #data_dict = json.loads(data)
            #data_displayed = "client_id : " + data_dict['client_id'] +  "&nbsp&nbsp&nbsp&nbsp" + "client_secret : " + data_dict['client_secret'] + "&nbsp&nbsp&nbsp&nbsp" +  "company name : " + data_dict['company_name'] 
            #select +=  "<option value=" + data_dict['client_id'] + ">" + data_displayed + "</option>"      
        return render_template('select.html', verifier_list=verifier_list) 
    else :
        client_id = request.form['client_id']
        return redirect ('/sandbox/op/console?client_id=' + client_id)



def console(mode) :
    global vc, reason
    if not session.get('is_connected') :
        return redirect('/sandbox/op/console/login')
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            return redirect('/sandbox/op/console/select')
        else  :
            session['client_id'] = request.args.get('client_id')
        session['client_data'] = json.loads(verifier_db_api.read_verifier(session['client_id']))
        vc_select = str()
        for key, value in credential_list.items() :
                if key ==   session['client_data']['vc'] :
                    vc_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    vc_select +=  "<option value=" + key + ">" + value + "</option>"

        return render_template('console.html',
                issuer = mode.server + "sandblox/op",
                client_id= session['client_data']['client_id'],
                client_secret= session['client_data']['client_secret'],
                token=mode.server + 'sandbox/op/authorize',
                authorization=mode.server + 'sandbox/op/token',
                logout=mode.server + 'sandbox/op/logout',
                userinfo=mode.server + 'sandbox/op/userinfo',
                company_name = session['client_data']['company_name'],
                reason = session['client_data']['reason'],
                qrcode_message = session['client_data'].get('qrcode_message', ""),
                mobile_message = session['client_data'].get('mobile_message', ""),
                vc_select=vc_select,
                )
    if request.method == 'POST' :
        if request.form['button'] == "new" :
            return redirect('/sandbox/op/console?client_id=' + verifier_db_api.create_verifier())
        
        elif request.form['button'] == "select" :
            return redirect ('/sandbox/op/console/select')
        
        elif request.form['button'] == "delete" :
            verifier_db_api.delete_verifier( request.form['client_id'])
            return redirect ('/sandbox/op/console')

        elif request.form['button'] == "logout" :
            session.clear()
            return redirect ('/sandbox/op/console')

        elif request.form['button'] == "advanced" :
            return redirect ('/sandbox/op/console/advanced')
        
        elif request.form['button'] == "update" :
            session['client_data']['client_id'] =  request.form['client_id']
            session['client_data']['client_secret'] = request.form['client_secret']
            session['client_data']['company_name'] = request.form['company_name']
            session['client_data']['reason'] = request.form.get('reason', "")
            session['client_data']['vc'] = request.form['vc']
            session['client_data']['qrcode_message'] = request.form['qrcode_message']
            session['client_data']['mobile_message'] = request.form['mobile_message']          
            verifier_db_api.update_verifier( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/op/console?client_id=' + request.form['client_id'])
        else :
            return redirect('/sandbox/op/console')

def advanced() :
    global vc, reason
    if not session.get('is_connected') :
        return redirect('/sandbox/op/console/login')
    if request.method == 'GET' :
        session['client_data'] = json.loads(verifier_db_api.read_verifier(session['client_id']))
        protocol_select = vc_select = str()       
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
                authorized_emails = session['client_data']['authorized_emails'],
                protocol = session['client_data']['protocol'],
                emails_filtering=emails_filtering,
                protocol_select=protocol_select
                )
    if request.method == 'POST' :

        if request.form['button'] == "back" :
            return redirect ('/sandbox/op/console?client_id=' + request.form['client_id'] )
        
        elif request.form['button'] == "update" :
            session['client_data']['authorized_emails'] = request.form.get('authorized_emails', "")
            session['client_data']['protocol'] = request.form['protocol']
            session['client_data']['emails'] = request.form.get('emails')
            verifier_db_api.update_verifier( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/op/console?client_id=' + request.form['client_id'])
          

