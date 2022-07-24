from flask import  request, render_template, redirect, session, jsonify
import json
import logging
import random
import requests
import db_api 
from urllib.parse import urlencode
import uuid
from op_constante import credential_list, protocol_list

logging.basicConfig(level=logging.INFO)


public_key =  {"e":"AQAB","kid" : "123", "kty":"RSA","n":"uEUuur6rqoEMaV3qEgzf4a8jSWzLuftWzW1t9SApbKKKI9_M2ZCValgbUJqpto190zKgBge20d7Hwb24Y_SrxC2e8W7sQMNCEHdCrAvzjtk36o3tKHbsSfYFRfDexZJKQ75tsA_TOSMRKH_xGSO-15ZL86NXrwMrg3CLPXw6T0PjG38IsJ2UHAZL-3ezw7ibDto8LD06UhLrvCMpBlS6IMmDYFRJ-d2KvnWyKt6TyNC-0hNcDS7X0jaODATmDh-rOE5rv5miyljjarC_3p8D2MJXmYWk0XjxzozXx0l_iQyh-J9vQ_70gBqCV1Ifqlu8VkasOfIaSbku_PJHSXesFQ"}

did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/issuer/console/login',  view_func=issuer_console_login, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer/console/callback',  view_func=issuer_console_callback, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer/console/logout',  view_func=issuer_console_logout, methods = ['GET', 'POST'], defaults={'mode' : mode})
    
    app.add_url_rule('/sandbox/op/issuer/console',  view_func=issuer_console, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer/console/select',  view_func=issuer_select, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer/console/advanced',  view_func=issuer_advanced, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/issuer/console/preview',  view_func=issuer_preview, methods = ['GET', 'POST'], defaults={'mode' : mode, "red" : red})
    app.add_url_rule('/sandbox/issuer/preview_presentation/<stream_id>',  view_func=issuer_preview_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})

    return


# parameters provided by platform
client_id = 'omwfxyojto'
client_secret = 'c74a61c2-0aad-11ed-9d6f-9b0deb2319ac'


# website homepage / authentication
def issuer_console_login(mode) :
    if not session.get('is_connected') :
        data = {
                'response_type': 'code',
                'client_id': client_id,
                'state': str(random.randint(0, 99999)),
                'nonce' :  str(random.randint(10000, 999999)), 
                'redirect_uri': mode.server + 'sandbox/op/issuer/console/callback',
                'scope': 'openid'    }
        session['data'] = data
        return redirect('/sandbox/op/authorize?' + urlencode(data))
    else  :
        return redirect('/sandbox/op/issuer/console')
    

# authentication
def issuer_console_callback(mode):
    if 'error' in request.args :
            session['is_connected'] = False
            return redirect('/')
    
    data = {
        'grant_type': 'authorization_code',
        'redirect_uri': mode.server + 'sandbox/op/issuer/console/callback',
        'code': request.args['code']
    }
    response = requests.post(mode.server + 'sandbox/op/token', data=data, auth=(client_id, client_secret))

    if response.status_code == 200:
        session['is_connected'] = True
    else :
        session['is_connected'] = False
    return redirect('/sandbox/op/issuer/console')
      
# authentication
def issuer_console_logout(mode):
    if not session.get('is_connected') :
        return redirect('sandbox/op/issuer/console/login')
    session.clear()
    response = requests.post(mode.server + 'sandbox/logout', data="")
    return redirect('/sandbox/op/issuer/console')


def issuer_select(mode) :
    if not session.get('is_connected') :
        return redirect('/sandbox/op/issuer/console/login')

    if request.method == 'GET' :  
        my_list = db_api.list_issuer()
        issuer_list=str()
        for data in my_list :
            data_dict = json.loads(data)
            issuer = """<tr>
                <td>""" + data_dict['company_name'] + """</td>
                <td><a href=/sandbox/op/issuer/console?client_id=""" + data_dict['client_id'] + """>""" + data_dict['client_id'] + """</a></td>
                <td>""" + data_dict['vc'] + """</td>
                </tr>"""
            issuer_list += issuer     
        return render_template('issuer_select.html', issuer_list=issuer_list) 
    else :
        if request.form['button'] == "new" :
            return redirect('/sandbox/op/issuer/console?client_id=' + db_api.create_issuer(mode))
        elif request.form['button'] == "logout" :
            session.clear()
            return redirect ('/sandbox/op/issuer/console')
       


def issuer_preview (red, mode) :
    stream_id = str(uuid.uuid1())
    client_id = session['client_data']['client_id']
    issuer_data = json.loads(db_api.read_issuer(client_id))
    qrcode_message = issuer_data.get('qrcode_message', "No message")
    mobile_message = issuer_data.get('mobile_message', "No message")
    
    url = mode.server + 'sandbox/issuer/preview_presentation/' + stream_id + '?' + urlencode({'issuer' : did_selected})
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url})
    return render_template('op_issuer_qrcode.html',
							url=url,
                            deeplink=deeplink,
							stream_id=stream_id,
                            qrcode_message=qrcode_message,
                            mobile_message=mobile_message,
                            landing_page_url= issuer_data['landing_page_url'],
                            title=issuer_data['title'],
                            terms_url= issuer_data.get('terms_url'),
                            privacy_url=issuer_data.get('privacy_url'),
                            company_name=issuer_data.get('company_name')
                            )
    
def issuer_preview_presentation_endpoint(stream_id, red):
    if request.method == 'GET':
        try :
            my_pattern = json.loads(red.get(stream_id).decode())['pattern']
        except :
            logging.error('red decode failed')
            red.set(stream_id + '_access',  'server_error')
            red.publish('login', json.dumps({"stream_id" : stream_id}))
            return jsonify("server error"), 500
        print(my_pattern)
        return jsonify(my_pattern)


def issuer_console(mode) :
    global vc, reason
    if not session.get('is_connected') :
        return redirect('/sandbox/op/issuer/console/login')
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            return redirect('/sandbox/op/issuer/console/select')
        else  :
            session['client_id'] = request.args.get('client_id')
        session['client_data'] = json.loads(db_api.read_issuer(session['client_id']))
        vc_select = str()
        for key, value in credential_list.items() :
                if key ==   session['client_data']['vc'] :
                    vc_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    vc_select +=  "<option value=" + key + ">" + value + "</option>"

        return render_template('issuer_console.html',
                public_key=public_key,
                issuer_landing_page = session['client_data']['issuer_landing_page'],
                title = session['client_data'].get('title'),
                contact_name = session['client_data'].get('contact_name'),
                contact_email = session['client_data'].get('contact_email'),
                privacy_url = session['client_data'].get('privacy_url'),
                landing_page_url = session['client_data'].get('landing_page_url'),
                terms_url = session['client_data'].get('terms_url'),
                client_id= session['client_data']['client_id'],
                company_name = session['client_data']['company_name'],
                reason = session['client_data']['reason'],
                qrcode_message = session['client_data'].get('qrcode_message', ""),
                mobile_message = session['client_data'].get('mobile_message', ""),
                vc_select=vc_select,
                )
    if request.method == 'POST' :
        if request.form['button'] == "new" :
            return redirect('/sandbox/op/issuer/console?client_id=' + db_api.create_issuer(mode))
        
        elif request.form['button'] == "select" :
            return redirect ('/sandbox/op/issuer/console/select')
        
        elif request.form['button'] == "delete" :
            db_api.delete_issuer( request.form['client_id'])
            return redirect ('/sandbox/op/issuer/console')

        elif request.form['button'] == "logout" :
            session.clear()
            return redirect ('/sandbox/op/issuer/console')

        elif request.form['button'] == "advanced" :
            return redirect ('/sandbox/op/issuer/console/advanced')
        
        elif request.form['button'] in [ "update", "preview"] :
            session['client_data']['contact_name'] = request.form['contact_name']
            session['client_data']['title'] = request.form['title']
            session['client_data']['contact_email'] = request.form['contact_email']
            session['client_data']['privacy_url'] = request.form['privacy_url']
            session['client_data']['landing_page_url'] = request.form['landing_page_url']
            session['client_data']['terms_url'] = request.form['terms_url']
            session['client_data']['client_id'] =  request.form['client_id']
            session['client_data']['company_name'] = request.form['company_name']
            session['client_data']['reason'] = request.form.get('reason', "")
            session['client_data']['vc'] = request.form['vc']
            session['client_data']['qrcode_message'] = request.form['qrcode_message']
            session['client_data']['mobile_message'] = request.form['mobile_message']          
            db_api.update_issuer(request.form['client_id'], json.dumps(session['client_data']))
            if request.form['button'] == "preview" :
                return redirect ('/sandbox/op/issuer/console/preview')
            return redirect('/sandbox/op/issuer/console?client_id=' + request.form['client_id'])
        else :
            return redirect('/sandbox/op/issuer/console')


def issuer_advanced() :
    global vc, reason
    if not session.get('is_connected') :
        return redirect('/sandbox/op/issuer/console/login')
    if request.method == 'GET' :
        session['client_data'] = json.loads(db_api.read_issuer(session['client_id']))
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
        return render_template('issuer_advanced.html',
                client_id = session['client_data']['client_id'],
                protocol = session['client_data']['protocol'],
                emails_filtering=emails_filtering,
                protocol_select=protocol_select
                )
    if request.method == 'POST' :

        if request.form['button'] == "back" :
            return redirect ('/sandbox/op/issuer/console?client_id=' + request.form['client_id'] )
        
        elif request.form['button'] == "update" :
            session['client_data']['protocol'] = request.form['protocol']
            db_api.update_issuer( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/op/issuer/console?client_id=' + request.form['client_id'])
          

