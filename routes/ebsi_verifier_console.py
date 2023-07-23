from flask import  request, render_template, redirect, session, jsonify
import json
import copy
import logging
import db_api 
import activity_db_api


from urllib.parse import urlencode
import uuid
from oidc4vc_constante import ebsi_verifier_credential_list, ebsi_path_list
from oidc4vc_constante import ebsi_vp_type_list, ebsi_verifier_landing_page_style_list

logging.basicConfig(level=logging.INFO)

did_selected = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/ebsi/verifier/console/logout',  view_func=ebsi_verifier_console_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/ebsi/verifier/console',  view_func=ebsi_verifier_console, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/verifier/console/select',  view_func=ebsi_verifier_console_select, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/verifier/console/preview',  view_func=ebsi_verifier_console_preview, methods = ['GET', 'POST'], defaults={'mode' : mode, "red" : red})
    app.add_url_rule('/sandbox/ebsi/verifier/console/activity',  view_func=ebsi_verifier_console_activity, methods = ['GET', 'POST'])

    #app.add_url_rule('/sandbox/ebsi/verifier/preview_presentation/<stream_id>',  view_func=ebsi_verifier_preview_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})

      # nav bar option
    app.add_url_rule('/sandbox/ebsi/verifier/nav/logout',  view_func=ebsi_verifier_nav_logout, methods = ['GET'])
    app.add_url_rule('/sandbox/ebsi/verifier/nav/create',  view_func=ebsi_verifier_nav_create, methods = ['GET'], defaults= {'mode' : mode})
    return

      
def ebsi_verifier_nav_logout() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    session.clear()
    return redirect ('/sandbox/saas4ssi')


def ebsi_verifier_nav_create(mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return redirect('/sandbox/ebsi/verifier/console?client_id=' + db_api.create_ebsi_verifier(mode, user=session['login_name']))

 
def ebsi_verifier_console_logout():
    if session.get('is_connected') :
        session.clear()
    return redirect('/sandbox/saas4ssi')


def ebsi_verifier_console_select(mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :  
        my_list = db_api.list_ebsi_verifier()
        verifier_list=str()
        for data in my_list :
            data_dict = json.loads(data)
            client_id = data_dict['client_id']
            act = len(activity_db_api.list(client_id))   
            try :
                if data_dict['user'] == "all" or session['login_name'] in [data_dict['user'], "admin"] :
                    verifier = """<tr>
                        <td>""" + data_dict.get('application_name', "") + """</td>
                        <td>""" + str(act) + """</td>
                        <td>""" + data_dict['user'] + """</td>
                        <td>""" + ebsi_verifier_credential_list.get(data_dict['vc'], "unknown") + """</td>
                        <td>""" + ebsi_verifier_credential_list.get(data_dict['vc_2'], "unknown") + """</td>
                        <td>""" + data_dict['callback'] + """</td>
                        <td><a href=/sandbox/ebsi/verifier/console?client_id=""" + data_dict['client_id'] + """>""" + data_dict['client_id'] + """</a></td>
                        <td>""" + data_dict['client_secret'] + """</td>
                    </tr>"""
                    verifier_list += verifier
            except :
                pass
        return render_template('ebsi/ebsi_verifier_select.html', verifier_list=verifier_list, login_name=session['login_name']) 
    else :
        if request.form['button'] == "new" :
            return redirect('/sandbox/ebsi/verifier/console?client_id=' + db_api.create_ebsi_verifier(mode, user=session['login_name']))
        elif request.form['button'] == "logout" :
            session.clear()
            return redirect ('/sandbox/saas4ssi')
        elif request.form['button'] == "home" :
            return render_template("menu.html", login_name=session["login_name"])


def ebsi_verifier_console_activity() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')

    if request.method == 'GET' :  
        activities = activity_db_api.list(session['client_data']['client_id'])
        activities.reverse() 
        activity_list = str()
        for data in activities :
            data_dict = json.loads(data)
            status = "Approved" if data_dict.get('status') else "Denied"
            user = data_dict.get('user', "Unknown") if data_dict.get('user') else "Unknown"
            activity = """<tr>
                    <td>""" + data_dict.get('presented', "unknown") + """</td>
                    <td>""" + user + """</td>
                    <td>""" + ebsi_verifier_credential_list.get(data_dict['credential_1'], "None") + """</td>
                    <td>""" + ebsi_verifier_credential_list.get(data_dict['credential_2'], "None") + """</td>
                    <td>""" + status + """</td>
                    </tr>"""
            activity_list += activity
        return render_template('ebsi/ebsi_verifier_activity.html', activity=activity_list) 
    else :
        return redirect('/sandbox/ebsi/verifier/console?client_id=' + session['client_data']['client_id'])
     

def ebsi_verifier_console_preview (red, mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    stream_id = str(uuid.uuid1())
    client_id = session['client_data']['client_id']
    verifier_data = json.loads(db_api.read_ebsi_verifier(client_id))
    qrcode_message = verifier_data.get('qrcode_message', "No message")
    mobile_message = verifier_data.get('mobile_message', "No message")
    qrcode_page = verifier_data.get('verifier_landing_page_style')
    url = mode.server + 'sandbox/preview_presentation/' + stream_id + '?' + urlencode({'issuer' : did_selected})
    deeplink_altme = mode.deeplink_altme + 'app/download?' + urlencode({'uri' : url})
    deeplink_talao = mode.deeplink_talao + 'app/download?' + urlencode({'uri' : url})
    return render_template(qrcode_page,
							url=url,
                            deeplink=deeplink_altme,
                            deeplink_talao=deeplink_talao,
							stream_id=stream_id,
                            page_title=verifier_data['page_title'],
                            page_subtitle=verifier_data['page_subtitle'],
                            page_description=verifier_data['page_description'],
                            application_name=verifier_data['application_name'],
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
    

def ebsi_verifier_preview_presentation_endpoint(stream_id, red):
    if request.method == 'GET':
        try :
            my_pattern = json.loads(red.get(stream_id).decode())['pattern']
        except :
            logging.error('red decode failed')
            red.set(stream_id + '_access',  'server_error')
            red.publish('login', json.dumps({"stream_id" : stream_id}))
            return jsonify("server error"), 500
        return jsonify(my_pattern)
    

def ebsi_verifier_console(mode) :
    global vc, reason
  
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            return redirect('/sandbox/ebsi/verifier/console/select?user='+ session.get('login_name'))
        else  :
            session['client_id'] = request.args.get('client_id')
        session['client_data'] = json.loads(db_api.read_ebsi_verifier(session['client_id']))
        
        verifier_landing_page_style_select = str()
        for key, value in ebsi_verifier_landing_page_style_list.items() :
                if key == session['client_data'].get('verifier_landing_page_style') :
                    verifier_landing_page_style_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    verifier_landing_page_style_select +=  "<option value=" + key + ">" + value + "</option>"

        ebsi_vp_type_select = str()
        for key, value in ebsi_vp_type_list.items() :
                if key ==   session['client_data'].get('ebsi_vp_type', "jwt_vp") :
                    ebsi_vp_type_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    ebsi_vp_type_select +=  "<option value=" + key + ">" + value + "</option>"

        vc_select_1 = str()
        for key, value in ebsi_verifier_credential_list.items() :
                if key ==   session['client_data']['vc'] :
                    vc_select_1 +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    vc_select_1 +=  "<option value=" + key + ">" + value + "</option>"
        
        vc_select_2 = str()
        for key, value in ebsi_verifier_credential_list.items() :
                if key ==   session['client_data'].get('vc_2', "DID") :
                    vc_select_2 +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    vc_select_2 +=  "<option value=" + key + ">" + value + "</option>"

        path_select_1 = str()
        for key, value in ebsi_path_list.items() :
                if key ==   session['client_data'].get('path_1', "$.credentialSchema.id") :
                    path_select_1 +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    path_select_1 +=  "<option value=" + key + ">" + value + "</option>"
        
        path_select_2 = str()
        for key, value in ebsi_path_list.items() :
                if key ==   session['client_data'].get('path_2', "$.credentialSchema.id") :
                    path_select_2 +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    path_select_2 +=  "<option value=" + key + ">" + value + "</option>"
        
        authorization_request = mode.server + 'sandbox/ebsi/authorize?client_id=' + session['client_data']['client_id'] + "&scope=openid&response_type=code&redirect_uri=" +  session['client_data']['callback'] 
        implicit_request = mode.server + 'sandbox/ebsi/authorize?client_id=' + session['client_data']['client_id'] + "&scope=openid&response_type=id_token&redirect_uri=" +  session['client_data']['callback']
        return render_template('ebsi/ebsi_verifier_console.html',
                authorization_request = authorization_request,
                implicit_request = implicit_request,
                title = session['client_data'].get('title'),
                pkce = "" if session['client_data'].get('pkce') in [None, False]  else "checked" ,
                request_uri = "" if session['client_data'].get('request_uri') in [None, False]  else "checked" ,
                standalone = "" if session['client_data'].get('standalone') in [None, False]  else "checked" ,
                application_name = session['client_data'].get('application_name', ""),
                contact_name = session['client_data'].get('contact_name'),
                contact_email = session['client_data'].get('contact_email'),
                privacy_url = session['client_data'].get('privacy_url'),
                landing_page_url = session['client_data'].get('landing_page_url'),
                terms_url = session['client_data'].get('terms_url'),
                issuer = mode.server + "sandbox/ebsi",
                client_id= session['client_data']['client_id'],
                client_secret= session['client_data']['client_secret'],
                callback= session['client_data']['callback'],
                token=mode.server + 'sandbox/ebsi/token',
                page_title = session['client_data']['page_title'],
                note = session['client_data']['note'],
                page_subtitle = session['client_data']['page_subtitle'],
                page_description = session['client_data']['page_description'],
                page_background_color = session['client_data']['page_background_color'],
                page_text_color = session['client_data']['page_text_color'],
                qrcode_background_color = session['client_data']['qrcode_background_color'],
                authorization=mode.server + 'sandbox/ebsi/authorize',
                logout=mode.server + 'sandbox/ebsi/logout',
                userinfo=mode.server + 'sandbox/ebsi/userinfo',
                company_name = session['client_data']['company_name'],
                reason = session['client_data']['reason'],
                reason_2 = session['client_data'].get('reason_2'),
                qrcode_message = session['client_data'].get('qrcode_message', ""),
                mobile_message = session['client_data'].get('mobile_message', ""),
                user_name=session['client_data'].get('user'),
                verifier_landing_page_style_select =  verifier_landing_page_style_select,
                vc_select_1=vc_select_1,
                vc_issuer_id =  session['client_data'].get('vc_issuer_id', ""),
                vc_select_2=vc_select_2,
                ebsi_vp_type_select=ebsi_vp_type_select,
                path_select_1=path_select_1,
                path_select_2=path_select_2,
                login_name=session['login_name']
                )
    if request.method == 'POST' :
       
        if request.form['button'] == "delete" :
            db_api.delete_ebsi_verifier( request.form['client_id'])
            return redirect ('/sandbox/ebsi/verifier/console')

        elif request.form['button'] == "activity" :
            return redirect ('/sandbox/ebsi/verifier/console/activity')
      
        elif request.form['button'] == "update" :
            session['client_data']['note'] = request.form['note']
            session['client_data']['standalone'] = request.form.get('standalone') 
            session['client_data']['pkce'] = request.form.get('pkce') 
            session['client_data']['request_uri'] = request.form.get('request_uri') 
            session['client_data']['application_name'] = request.form['application_name']
            session['client_data']['page_title'] = request.form['page_title']
            session['client_data']['page_subtitle'] = request.form['page_subtitle']
            session['client_data']['page_description'] = request.form['page_description']
            session['client_data']['page_background_color'] = request.form['page_background_color']      
            session['client_data']['page_text_color'] = request.form['page_text_color']  
            session['client_data']['qrcode_background_color'] = request.form['qrcode_background_color'] 
            session['client_data']['contact_name'] = request.form['contact_name']
            session['client_data']['title'] = request.form['title'] 
            session['client_data']['verifier_landing_page_style'] = request.form['verifier_landing_page_style']
            session['client_data']['callback'] = request.form['callback']
            session['client_data']['contact_email'] = request.form['contact_email']
            session['client_data']['privacy_url'] = request.form['privacy_url']
            session['client_data']['landing_page_url'] = request.form['landing_page_url']
            session['client_data']['terms_url'] = request.form['terms_url']
            session['client_data']['client_id'] =  request.form['client_id']
            session['client_data']['client_secret'] = request.form['client_secret']
            session['client_data']['company_name'] = request.form['company_name']
            session['client_data']['reason'] = request.form.get('reason', "")
            session['client_data']['reason_2'] = request.form.get('reason_2', "")
            session['client_data']['vc'] = request.form['vc_1']
            #session['client_data']['vc_issuer_id'] = request.form['vc_issuer_id']
            session['client_data']['vc_2'] = request.form['vc_2']
            session['client_data']['path_1'] = request.form['path_1']
            session['client_data']['path_2'] = request.form['path_2']
            session['client_data']['user'] = request.form['user_name']
            session['client_data']['ebsi_vp_type'] = request.form['ebsi_vp_type']
            session['client_data']['qrcode_message'] = request.form['qrcode_message']
            session['client_data']['mobile_message'] = request.form['mobile_message']          
            db_api.update_ebsi_verifier(request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/ebsi/verifier/console?client_id=' + request.form['client_id'])

        elif request.form['button'] == "copy" :
            new_client_id=  db_api.create_ebsi_verifier(mode,  user=session['login_name'])
            new_data = copy.deepcopy(session['client_data'])
            new_data['application_name'] = new_data['application_name'] + ' (copie)'
            new_data['client_id'] = new_client_id
            new_data['user'] = session['login_name']
            db_api.update_ebsi_verifier(new_client_id, json.dumps(new_data))
            return redirect('/sandbox/ebsi/verifier/console?client_id=' + new_client_id)

        elif request.form['button'] == "preview" :
            return redirect ('/sandbox/ebsi/verifier/console/preview')
 