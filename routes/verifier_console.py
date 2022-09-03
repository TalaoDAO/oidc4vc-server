from flask import  request, render_template, redirect, session, jsonify
import json
import logging
import db_api 
from urllib.parse import urlencode
import uuid
from op_constante import credential_list, protocol_list, model_one, model_any, model_DIDAuth, verifier_landing_page_style_list

logging.basicConfig(level=logging.INFO)

did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/console/logout',  view_func=console_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/console',  view_func=console, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/console/select',  view_func=select, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/console/advanced',  view_func=advanced, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/console/preview',  view_func=preview, methods = ['GET', 'POST'], defaults={'mode' : mode, "red" : red})
    app.add_url_rule('/sandbox/preview_presentation/<stream_id>',  view_func=preview_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    return
      

def console_logout():
    if session.get('is_connected') :
        session.clear()
    return redirect('/sandbox/saas4ssi')


def select(mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')

    if request.method == 'GET' :  
        my_list = db_api.list_verifier()
        verifier_list=str()
        for data in my_list :
            data_dict = json.loads(data)
            if session['login_name'] == data_dict['user'] or data_dict['user'] == "all" or session['login_name'] == "admin1234" :
                verifier = """<tr>
                    <td>""" + data_dict.get('application_name', "") + """</td>
                    <td>""" + data_dict['user'] + """</td>
                    <td>""" + data_dict['vc'] + """</td>
                    <td>""" + mode.server + "sandbox/op" + """</td>
                    <td><a href=/sandbox/op/console?client_id=""" + data_dict['client_id'] + """>""" + data_dict['client_id'] + """</a></td>
                    <td>""" + data_dict['client_secret'] + """</td>
                   
                    </tr>"""
                verifier_list += verifier
            else :
                pass     
        return render_template('verifier_select.html', verifier_list=verifier_list, login_name=session['login_name']) 
    else :
        if request.form['button'] == "new" :
            return redirect('/sandbox/op/console?client_id=' + db_api.create_verifier(mode, user=session['login_name']))
        elif request.form['button'] == "logout" :
            session.clear()
            return redirect ('/sandbox/saas4ssi')
       

def preview (red, mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
        
    stream_id = str(uuid.uuid1())
    client_id = session['client_data']['client_id']
    verifier_data = json.loads(db_api.read_verifier(client_id))
    qrcode_message = verifier_data.get('qrcode_message', "No message")
    mobile_message = verifier_data.get('mobile_message', "No message")
    if verifier_data['vc'] == "ANY" :
        pattern = model_any
    elif verifier_data['vc'] == "DID" :
        pattern = model_DIDAuth
    else :
        pattern = model_one
        pattern["query"][0]["credentialQuery"][0]["reason"][0]["@value"] = verifier_data['reason']
        pattern["query"][0]["credentialQuery"][0]["example"]["type"] = verifier_data['vc']
    data = { "pattern": pattern }
    red.set(stream_id,  json.dumps(data))

    if not verifier_data.get('landing_page_style') :
        qrcode_page = "op_verifier_qrcode.html"
    else : 
        qrcode_page = verifier_data.get('landing_page_style')
    
    url = mode.server + 'sandbox/preview_presentation/' + stream_id + '?' + urlencode({'issuer' : did_selected})
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url})
    return render_template(qrcode_page,
							url=url,
                            deeplink=deeplink,
							stream_id=stream_id,
                            page_title=verifier_data['page_title'],
                            page_subtitle=verifier_data['page_subtitle'],
                            page_description=verifier_data['page_description'],
                            qrcode_message=qrcode_message,
                            mobile_message=mobile_message,
                            landing_page_url= verifier_data['landing_page_url'],
                            title=verifier_data['title'],
                            terms_url= verifier_data.get('terms_url'),
                            privacy_url=verifier_data.get('privacy_url'),
                            company_name=verifier_data.get('company_name'),
                            page_background_color = verifier_data['page_background_color'],
                            page_text_color = verifier_data['page_text_color'],
                            qrcode_background_color = verifier_data['qrcode_background_color'],
                            back_button = True
                            )
    
def preview_presentation_endpoint(stream_id, red):
    if request.method == 'GET':
        try :
            my_pattern = json.loads(red.get(stream_id).decode())['pattern']
        except :
            logging.error('red decode failed')
            red.set(stream_id + '_access',  'server_error')
            red.publish('login', json.dumps({"stream_id" : stream_id}))
            return jsonify("server error"), 500
        return jsonify(my_pattern)


def console(mode) :
    global vc, reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            return redirect('/sandbox/op/console/select?user='+ session.get('login_name'))
        else  :
            session['client_id'] = request.args.get('client_id')
        session['client_data'] = json.loads(db_api.read_verifier(session['client_id']))
        
        landing_page_style_select = str()
        for key, value in verifier_landing_page_style_list.items() :
                if key == session['client_data'].get('landing_page_style') :
                    landing_page_style_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    landing_page_style_select +=  "<option value=" + key + ">" + value + "</option>"

        vc_select = str()
        for key, value in credential_list.items() :
                if key ==   session['client_data']['vc'] :
                    vc_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    vc_select +=  "<option value=" + key + ">" + value + "</option>"

        authorization_request = mode.server + 'sandbox/op/authorize?client_id=' + session['client_data']['client_id'] + "&response_type=code&redirect_uri=" +  session['client_data']['callback'] 
        implicit_request = mode.server + 'sandbox/op/authorize?client_id=' + session['client_data']['client_id'] + "&response_type=implicit&redirect_uri=" +  session['client_data']['callback']
        return render_template('verifier_console.html',
                authorization_request = authorization_request,
                implicit_request = implicit_request,
                title = session['client_data'].get('title'),
                application_name = session['client_data'].get('application_name', ""),
                contact_name = session['client_data'].get('contact_name'),
                contact_email = session['client_data'].get('contact_email'),
                privacy_url = session['client_data'].get('privacy_url'),
                landing_page_url = session['client_data'].get('landing_page_url'),
                terms_url = session['client_data'].get('terms_url'),
                issuer = mode.server + "sandbox/op",
                client_id= session['client_data']['client_id'],
                client_secret= session['client_data']['client_secret'],
                callback= session['client_data']['callback'],
                token=mode.server + 'sandbox/op/token',
                page_title = session['client_data']['page_title'],
                note = session['client_data']['note'],
                page_subtitle = session['client_data']['page_subtitle'],
                page_description = session['client_data']['page_description'],
                page_background_color = session['client_data']['page_background_color'],
                page_text_color = session['client_data']['page_text_color'],
                qrcode_background_color = session['client_data']['qrcode_background_color'],
                authorization=mode.server + 'sandbox/op/authorize',
                logout=mode.server + 'sandbox/op/logout',
                userinfo=mode.server + 'sandbox/op/userinfo',
                company_name = session['client_data']['company_name'],
                reason = session['client_data']['reason'],
                qrcode_message = session['client_data'].get('qrcode_message', ""),
                mobile_message = session['client_data'].get('mobile_message', ""),
                user_name=session['client_data'].get('user'),
                landing_page_style_select =  landing_page_style_select,
                vc_select=vc_select,
                login_name=session['login_name']
                )
    if request.method == 'POST' :
        if request.form['button'] == "new" :
            return redirect('/sandbox/op/console?client_id=' + db_api.create_verifier(mode, user=session['login_name']))
        
        elif request.form['button'] == "select" :
            return redirect ('/sandbox/op/console/select?user=' + session['login_name'])
        
        elif request.form['button'] == "delete" :
            db_api.delete_verifier( request.form['client_id'])
            return redirect ('/sandbox/op/console')

        elif request.form['button'] == "logout" :
            session.clear()
            return redirect ('/sandbox/saas4ssi')

        elif request.form['button'] == "advanced" :
            return redirect ('/sandbox/op/console/advanced')
      
        elif request.form['button'] in [ "update", "preview"] :
            session['client_data']['note'] = request.form['note']
            session['client_data']['application_name'] = request.form['application_name']
            session['client_data']['page_title'] = request.form['page_title']
            session['client_data']['page_subtitle'] = request.form['page_subtitle']
            session['client_data']['page_description'] = request.form['page_description']
            session['client_data']['page_background_color'] = request.form['page_background_color']      
            session['client_data']['page_text_color'] = request.form['page_text_color']  
            session['client_data']['qrcode_background_color'] = request.form['qrcode_background_color'] 
            session['client_data']['contact_name'] = request.form['contact_name']
            session['client_data']['title'] = request.form['title'] 
            session['client_data']['landing_page_style'] = request.form['landing_page_style']
            session['client_data']['callback'] = request.form['callback']
            session['client_data']['contact_email'] = request.form['contact_email']
            session['client_data']['privacy_url'] = request.form['privacy_url']
            session['client_data']['landing_page_url'] = request.form['landing_page_url']
            session['client_data']['terms_url'] = request.form['terms_url']
            session['client_data']['client_id'] =  request.form['client_id']
            session['client_data']['client_secret'] = request.form['client_secret']
            session['client_data']['company_name'] = request.form['company_name']
            session['client_data']['reason'] = request.form.get('reason', "")
            session['client_data']['vc'] = request.form['vc']
            session['client_data']['qrcode_message'] = request.form['qrcode_message']
            session['client_data']['mobile_message'] = request.form['mobile_message']          
            db_api.update_verifier(request.form['client_id'], json.dumps(session['client_data']))
            if request.form['button'] == "preview" :
                return redirect ('/sandbox/op/console/preview')
            return redirect('/sandbox/op/console?client_id=' + request.form['client_id'])
        else :
            return redirect('/sandbox/op/console')


def advanced() :
    global vc, reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        session['client_data'] = json.loads(db_api.read_verifier(session['client_id']))
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
            db_api.update_verifier( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/op/console?client_id=' + request.form['client_id'])
          

