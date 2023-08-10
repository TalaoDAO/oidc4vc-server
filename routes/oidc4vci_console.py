from flask import  request, render_template, redirect, session, jsonify, flash
import json
import logging
import copy
import db_api 
from constante import  landing_page_style_list, oidc4vc_profile_list
from profile import profile
import oidc4vc

logging.basicConfig(level=logging.INFO)

def init_app(app,red, mode) :
    app.add_url_rule('/issuer/console/logout',  view_func=nav_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/issuer/console',  view_func=issuer_console, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/issuer/console/select',  view_func=issuer_select, methods = ['GET', 'POST'])
    app.add_url_rule('/issuer/console/advanced',  view_func=issuer_advanced, methods = ['GET', 'POST'])
    # nav bar option
    app.add_url_rule('/issuer/nav/logout',  view_func=nav_logout, methods = ['GET'])
    app.add_url_rule('/issuer/nav/create',  view_func=nav_create, methods = ['GET'], defaults= {'mode' : mode})
    return
    

def nav_logout() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    session.clear()
    return redirect ('/sandbox/saas4ssi')

def issuer_select() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    my_list = db_api.list_issuer()
    issuer_list=str()
    for issuer_data in my_list :
        data_dict = json.loads(issuer_data)         
        client_id = data_dict['client_id']
        if data_dict['user'] == "all" or session['login_name'] in [data_dict['user'], "admin"] :
            curve = json.loads(data_dict['jwk'])['crv']
            vm =  data_dict['verification_method']
            issuer = """<tr>
                    <td>""" + data_dict.get('application_name', "unknown") + """</td>
                    <td>""" + data_dict.get('user', "unknown") + """</td>
                    <td>""" +  data_dict['profile'] + """</td>
                    <td><a href=/issuer/console?client_id=""" + client_id + """>""" + client_id + """</a></td>
                    <td>""" + data_dict['did'] + """</td> 
                    <td>""" + vm + """</td> 
                    <td>""" + curve + """</td>
                    </tr>"""
            issuer_list += issuer
    return render_template('issuer_oidc/issuer_select.html', issuer_list=issuer_list, login_name=session['login_name']) 
   
       
def nav_create(mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return redirect('/issuer/console?client_id=' + db_api.create_issuer(mode,  user=session['login_name']))


def issuer_console(mode) :
    global  reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            return redirect('/issuer/console/select')
        else  :
            session['client_id'] = request.args.get('client_id')
        session['client_data'] = json.loads(db_api.read_issuer(session['client_id']))

        issuer_landing_page_select = str()
        for key, value in landing_page_style_list.items() :
                if key == session['client_data'].get('issuer_landing_page') :
                    issuer_landing_page_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    issuer_landing_page_select +=  "<option value=" + key + ">" + value + "</option>"
        issuer_api_endpoint = mode.server + 'issuer/api/' + session['client_id']
        return render_template('issuer_oidc/issuer_console.html',
                login_name=session['login_name'],
                application_name=session['client_data'].get('application_name', 'Unknown'),
                client_secret=session['client_data']['client_secret'],
                user=session['client_data']['user'], 
                callback=session['client_data']['callback'],
                issuer_api_endpoint = issuer_api_endpoint,
                title = session['client_data'].get('title'),
                contact_name = session['client_data'].get('contact_name'),
                contact_email = session['client_data'].get('contact_email'),
                client_id= session['client_data']['client_id'],
                company_name = session['client_data']['company_name'],
                page_title = session['client_data']['page_title'],
                note = session['client_data']['note'],
                page_subtitle = session['client_data']['page_subtitle'],
                page_description = session['client_data']['page_description'],
                qrcode_message = session['client_data'].get('qrcode_message', ""),
                mobile_message = session['client_data'].get('mobile_message', ""),
                issuer_landing_page_select =  issuer_landing_page_select,
                )
    if request.method == 'POST' :
        if request.form['button'] == "delete" :
            db_api.delete_issuer( request.form['client_id'])
            return redirect ('/issuer/console')
        
        else :
            session['client_data']['contact_name'] = request.form['contact_name']
            session['client_data']['user'] = request.form['user']
            session['client_data']['callback'] = request.form['callback']
            session['client_data']['page_title'] = request.form['page_title']
            session['client_data']['page_subtitle'] = request.form['page_subtitle']
            session['client_data']['page_description'] = request.form['page_description']
            session['client_data']['note'] = request.form['note']          
            session['client_data']['title'] = request.form['title']
            session['client_data']['contact_email'] = request.form['contact_email']
            session['client_data']['issuer_landing_page'] = request.form['issuer_landing_page']
            session['client_data']['client_id'] =  request.form['client_id']
            session['client_data']['company_name'] = request.form['company_name']
            session['client_data']['application_name'] = request.form['application_name']
            session['client_data']['qrcode_message'] = request.form['qrcode_message']
            session['client_data']['mobile_message'] = request.form['mobile_message'] 
              
            if request.form['button'] == "preview" :
                return redirect ('/issuer/console/preview')

            if request.form['button'] == "activity" :
                return redirect ('/issuer/console/activity')
            
            if request.form['button'] == "advanced" :
                return redirect ('/issuer/console/advanced')
            
            if request.form['button'] == "update" :
                db_api.update_issuer(request.form['client_id'], json.dumps(session['client_data']))
                return redirect('/issuer/console?client_id=' + request.form['client_id'])

            if request.form['button'] == "copy" :
                new_client_id=  db_api.create_issuer(mode,  user=session['login_name'])
                new_data = copy.deepcopy(session['client_data'])
                new_data['application_name'] = new_data['application_name'] + ' (copie)'
                new_data['client_id'] = new_client_id
                new_data['user'] = session['login_name']
                db_api.update_issuer(new_client_id, json.dumps(new_data))
                return redirect('/issuer/console?client_id=' + new_client_id)


async def issuer_advanced() :
    global  reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        session['client_data'] = json.loads(db_api.read_issuer(session['client_id']))
        oidc4vc_profile_select = str()
        for key, value in oidc4vc_profile_list.items() :
                if key ==  session['client_data']['profile'] :
                    oidc4vc_profile_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    oidc4vc_profile_select +=  "<option value=" + key + ">" + value + "</option>"      

        did = session['client_data'].get('did', "")
        
        did_document = oidc4vc.did_resolve_lp(did)
        issuer_profile = profile[session['client_data']['profile']]
        jwk = json.dumps(json.loads(session['client_data']['jwk']), indent=4)
      
        return render_template('issuer_oidc/issuer_advanced.html',
                client_id = session['client_data']['client_id'],
                jwk = jwk,
                verification_method = session['client_data'].get('verification_method', ""),
                oidc4vc_profile_select=oidc4vc_profile_select,
                did = session['client_data'].get('did', ""),
                profile=json.dumps(issuer_profile, indent=4),
                did_document=json.dumps(did_document, indent=4)
                )
    if request.method == 'POST' :     
        session['client_data'] = json.loads(db_api.read_issuer(session['client_id']))
        if request.form['button'] == "back" :
            return redirect('/issuer/console?client_id=' + request.form['client_id'])

        if request.form['button'] == "update" :
            session['client_data']['profile'] = request.form['profile']
            session['client_data']['did'] = request.form['did']
            session['client_data']['verification_method'] = request.form['verification_method']
            try :
                did_method = request.form['did'].split(':')[1]
            except :
                did_method = None
            issuer_profile = session['client_data'].get('profile', 'DEFAULT')
            if issuer_profile in ["EBSI-V2", "EBSI-V3"] and did_method != 'ebsi' :
                flash("This profile requires did:ebsi", "warning")
                return redirect('/issuer/console/advanced')
            elif issuer_profile == "JWTVC" and did_method not in ['web', 'ion'] :
                flash("This profile requires did:web or did:ion", "warning")
                return redirect('/issuer/console/advanced')
            else:
                pass
            session['client_data']['jwk'] = request.form['jwk']
            db_api.update_issuer( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/issuer/console/advanced')
          