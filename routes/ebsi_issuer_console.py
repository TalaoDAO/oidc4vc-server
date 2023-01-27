from flask import  request, render_template, redirect, session, jsonify
import json
import logging
import didkit
import copy
import db_api 
from urllib.parse import urlencode
import uuid
from op_constante_ebsi import pre_authorized_code_list, ebsi_credential_requested_list
from op_constante_ebsi import ebsi_vc_type_list, method_list, landing_page_style_list, ebsi_credential_to_issue_list
import ebsi
import issuer_activity_db_api
import pyotp
import datetime

logging.basicConfig(level=logging.INFO)

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/ebsi/issuer/console/logout',  view_func=ebsi_nav_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/ebsi/issuer/console',  view_func=ebsi_issuer_console, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/ebsi/issuer/console/select',  view_func=ebsi_issuer_select, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/ebsi/issuer/console/advanced',  view_func=ebsi_issuer_advanced, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/ebsi/issuer/console/preview',  view_func=ebsi_issuer_preview, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/issuer/preview_presentation/<stream_id>',  view_func=ebsi_issuer_preview_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    app.add_url_rule('/sandbox/ebsi/issuer/console/activity',  view_func=ebsi_issuer_activity, methods = ['GET', 'POST'])
    # nav bar option
    app.add_url_rule('/sandbox/ebsi/issuer/nav/logout',  view_func=ebsi_nav_logout, methods = ['GET'])
    app.add_url_rule('/sandbox/ebsi/issuer/nav/create',  view_func=ebsi_nav_create, methods = ['GET'], defaults= {'mode' : mode})
    return
    

def ebsi_nav_logout() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    session.clear()
    return redirect ('/sandbox/saas4ssi')

# display activities of the issuer
def ebsi_issuer_activity() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')

    if request.method == 'GET' :  
        activities = issuer_activity_db_api.list(session['client_data']['client_id'])
        activities.reverse() 
        activity_list = str()
        for data in activities :
            data_dict = json.loads(data)
            vp = data_dict.get('vp', [])
            if isinstance(vp, dict) : # only one verifiable presentation sent by wallet
                vp_list = list()
                vp_list.append(json.dumps(vp))
                vp = vp_list
            DID = data_dict.get('wallet_did', "Unknown            ")
            data_received = list()
            for credential in vp :
                if not json.loads(credential).get('verifiableCredential') :
                    data_received = ""
                elif json.loads(credential)['verifiableCredential']['credentialSubject']['type'] == 'EmailPass' :
                    data_received.append("email=" +json.loads(credential)['verifiableCredential']['credentialSubject']['email'])
                elif  json.loads(credential)['verifiableCredential']['credentialSubject']['type'] == 'Over18' :
                    data_received.append('Over18=True')
                elif  json.loads(credential)['verifiableCredential']['credentialSubject']['type'] == 'Over13' :
                    data_received.append('Over13=True')
                elif  json.loads(credential)['verifiableCredential']['credentialSubject']['type'] == 'Nationality' :
                    data_received.append('nationality=' + json.loads(credential)['verifiableCredential']['credentialSubject']['nationality'])  
                elif  json.loads(credential)['verifiableCredential']['credentialSubject']['type'] == 'AgeRange' :
                    data_received.append('ageRange=' + json.loads(credential)['verifiableCredential']['credentialSubject']['ageRange'])  
                elif  json.loads(credential)['verifiableCredential']['credentialSubject']['type'] == 'Gender' :
                    data_received.append('gender=' + json.loads(credential)['verifiableCredential']['credentialSubject']['gender'])    
                elif  json.loads(credential)['verifiableCredential']['credentialSubject']['type'] == 'TezosAssociatedAddress' :
                    data_received.append('tezosAddress=' + json.loads(credential)['verifiableCredential']['credentialSubject']['associatedAddress'])               
                elif  json.loads(credential)['verifiableCredential']['credentialSubject']['type'] == 'PhoneProof' :
                    data_received.append('phon=' + json.loads(credential)['verifiableCredential']['credentialSubject']['phone']) 
                elif  json.loads(credential)['verifiableCredential']['credentialSubject']['type'] == 'PassportNumber' :
                    data_received.append('passport_footprint=' + json.loads(credential)['verifiableCredential']['credentialSubject']['passportNumber']) 
            activity = """<tr>
                    <td>""" + data_dict['presented'] + """</td>
                     <td>""" +  DID + """</td>
                    <td>""" + " & ".join(data_received) + """</td>
                    </tr>"""
            activity_list += activity
        return render_template('ebsi/ebsi_issuer_activity.html', activity=activity_list) 
    else :
        return redirect('/sandbox/ebsi/issuer/console?client_id=' + session['client_data']['client_id'])

def ebsi_issuer_select() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :  
        my_list = db_api.list_ebsi_issuer()
        issuer_list=str()
        for data in my_list :
            data_dict = json.loads(data)         
            client_id = data_dict['client_id']
            act = len(issuer_activity_db_api.list(client_id))              
            if data_dict['method'] == "ebsi" :
                DID = data_dict['did_ebsi']
            elif data_dict['method'] == "relay" :
                DID = method_list['relay']
            if data_dict['user'] == "all" or session['login_name'] in [data_dict['user'], "admin"] :
                issuer = """<tr>
                        <td>""" + data_dict.get('application_name', "unknown") + """</td>
                         <td>""" + str(act) + """</td>
                        <td>""" + data_dict.get('user', "unknown") + """</td>
                        <td><a href=/sandbox/ebsi/issuer/console?client_id=""" + data_dict['client_id'] + """>""" + data_dict['client_id'] + """</a></td>
                        <td>""" + DID[:10] +'....' + DID[-10:] + """</td> 
                        <td>""" + ebsi_credential_to_issue_list.get(data_dict['credential_to_issue'], 'unknown') + """</td>
                        <td>""" + ebsi_credential_requested_list.get(data_dict['credential_requested'], 'Unknown') + """</td>
                        <td>""" + ebsi_credential_requested_list.get(data_dict.get('credential_requested_2'), "None") + """</td>
                        <td>""" + ebsi_credential_requested_list.get(data_dict.get('credential_requested_3'), "None") + """</td>
                        <td>""" + ebsi_credential_requested_list.get(data_dict.get('credential_requested_4'), "None") + """</td>
                        </tr>"""
                issuer_list += issuer
        return render_template('ebsi/ebsi_issuer_select.html', issuer_list=issuer_list, login_name=session['login_name']) 
   
       
def ebsi_nav_create(mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return redirect('/sandbox/ebsi/issuer/console?client_id=' + db_api.create_ebsi_issuer(mode,  user=session['login_name']))


def ebsi_issuer_preview (mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    stream_id = str(uuid.uuid1())
    client_id = session['client_data']['client_id']
    issuer_data = json.loads(db_api.read_ebsi_issuer(client_id))
    qrcode_message = issuer_data.get('qrcode_message', "No message")
    mobile_message = issuer_data.get('mobile_message', "No message")
    if not issuer_data.get('landing_page_style') :
        qrcode_page = "op_issuer_qrcode_2.html"
    else : 
        qrcode_page = issuer_data.get('landing_page_style')

    if session['client_data']['method'] == "ebsi" :
        issuer_did = session['client_data']['did_ebsi']
    elif session['client_data']['method'] == "relay" :
        issuer_did = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
    else : 
        issuer_did = didkit.key_to_did(session['client_data']['method'], session['client_data']['jwk'])
        
    url = mode.server + 'sandbox/issuer/preview_presentation/' + stream_id + '?' + urlencode({'issuer' : issuer_did})
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url})
    return render_template(qrcode_page,
							url=url,
                            deeplink=deeplink,
							stream_id=stream_id,
                            qrcode_message=qrcode_message,
                            mobile_message=mobile_message,
                            landing_page_url= issuer_data['landing_page_url'],
                            title=issuer_data['title'],
                            page_title=issuer_data['page_title'],
                            page_subtitle=issuer_data['page_subtitle'],
                            page_description=issuer_data['page_description'],
                            terms_url= issuer_data.get('terms_url'),
                            privacy_url=issuer_data.get('privacy_url'),
                            back_button = True,
                            page_background_color = issuer_data['page_background_color'],
                            page_text_color = issuer_data['page_text_color'],
                            qrcode_background_color = issuer_data['qrcode_background_color'],
                            )
    
def ebsi_issuer_preview_presentation_endpoint(stream_id, red):
    if request.method == 'GET':
        try :
            my_pattern = json.loads(red.get(stream_id).decode())['pattern']
        except :
            logging.error('red decode failed')
            red.set(stream_id + '_access',  'server_error')
            red.publish('login', json.dumps({"stream_id" : stream_id}))
            return jsonify("server error"), 500
        return jsonify(my_pattern)


def ebsi_issuer_console(mode) :
    global  reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            return redirect('/sandbox/ebsi/issuer/console/select')
        else  :
            session['client_id'] = request.args.get('client_id')
        session['client_data'] = json.loads(db_api.read_ebsi_issuer(session['client_id']))

        """
        # credential requested 1
        credential_requested_select = str()
        for key, value in ebsi_credential_requested_list.items() :
                if key ==   session['client_data']['credential_requested'] :
                    credential_requested_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_requested_select +=  "<option value=" + key + ">" + value + "</option>"
        """

        landing_page_style_select = str()
        for key, value in landing_page_style_list.items() :
                if key == session['client_data'].get('landing_page_style') :
                    landing_page_style_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    landing_page_style_select +=  "<option value=" + key + ">" + value + "</option>"
        """
        # credential requested 2
        credential_requested_2_select = str()
        for key, value in ebsi_credential_requested_list.items() :
                if key ==   session['client_data'].get('credential_requested_2', "DID") :
                    credential_requested_2_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_requested_2_select +=  "<option value=" + key + ">" + value + "</option>"
        
        # credential requested 3
        credential_requested_3_select = str()
        for key, value in ebsi_credential_requested_list.items() :
                if key ==   session['client_data'].get('credential_requested_3', "DID") :
                    credential_requested_3_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_requested_3_select +=  "<option value=" + key + ">" + value + "</option>"
        
        # credential requested 4
        credential_requested_4_select = str()
        for key, value in ebsi_credential_requested_list.items() :
                if key ==   session['client_data'].get('credential_requested_4', "DID") :
                    credential_requested_4_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_requested_4_select +=  "<option value=" + key + ">" + value + "</option>"
        """
        # cedential to usse for EBSI issuer
        credential_items = ebsi_credential_to_issue_list.items()
        credential_to_issue_select = str()
        for key, value in credential_items :
                if key ==   session['client_data']['credential_to_issue'] :
                    credential_to_issue_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_to_issue_select +=  "<option value=" + key + ">" + value + "</option>"
        return render_template('ebsi/ebsi_issuer_console.html',
                login_name=session['login_name'],
                application_name=session['client_data'].get('application_name', 'Unknown'),
                client_secret=session['client_data']['client_secret'],
                user=session['client_data']['user'], 
                callback=session['client_data']['callback'],
                pre_authorized_code = session['client_data'].get('pre-authorized_code'), 
                issuer_landing_page = session['client_data']['issuer_landing_page'],
                title = session['client_data'].get('title'),
                contact_name = session['client_data'].get('contact_name'),
                contact_email = session['client_data'].get('contact_email'),
                privacy_url = session['client_data'].get('privacy_url'),
                landing_page_url = session['client_data'].get('landing_page_url'),
                terms_url = session['client_data'].get('terms_url'),
                client_id= session['client_data']['client_id'],
                company_name = session['client_data']['company_name'],
                #reason = session['client_data']['reason'],
                #reason_2 = session['client_data'].get('reason_2', ""),
                #reason_3 = session['client_data'].get('reason_3', ""),
                #reason_4 = session['client_data'].get('reason_4', ""),
                page_title = session['client_data']['page_title'],
                note = session['client_data']['note'],
                page_subtitle = session['client_data']['page_subtitle'],
                page_description = session['client_data']['page_description'],
                qrcode_message = session['client_data'].get('qrcode_message', ""),
                mobile_message = session['client_data'].get('mobile_message', ""),
                credential_to_issue_select = credential_to_issue_select,
                #credential_requested_select =  credential_requested_select,
                landing_page_style_select =  landing_page_style_select,
                #credential_requested_2_select =  credential_requested_2_select,
                #credential_requested_3_select =  credential_requested_3_select,
                #credential_requested_4_select =  credential_requested_4_select,
                page_background_color = session['client_data']['page_background_color'],
                page_text_color = session['client_data']['page_text_color'],
                qrcode_background_color = session['client_data']['qrcode_background_color'],
                )
    if request.method == 'POST' :
        if request.form['button'] == "delete" :
            db_api.delete_ebsi_issuer( request.form['client_id'])
            return redirect ('/sandbox/ebsi/issuer/console')
        
        else :
            session['client_data']['contact_name'] = request.form['contact_name']
            session['client_data']['user'] = request.form['user']
            session['client_data']['callback'] = request.form['callback']
            #session['client_data']['secret'] = request.form['secret']
            session['client_data']['landing_page_style'] = request.form['landing_page_style']
            session['client_data']['page_title'] = request.form['page_title']
            session['client_data']['page_subtitle'] = request.form['page_subtitle']
            session['client_data']['page_description'] = request.form['page_description']
            session['client_data']['note'] = request.form['note']          
            session['client_data']['title'] = request.form['title']
            session['client_data']['contact_email'] = request.form['contact_email']
            session['client_data']['privacy_url'] = request.form['privacy_url']
            session['client_data']['landing_page_url'] = request.form['landing_page_url']
            session['client_data']['terms_url'] = request.form['terms_url']
            session['client_data']['client_id'] =  request.form['client_id']
            session['client_data']['company_name'] = request.form['company_name']
            session['client_data']['application_name'] = request.form['application_name']
            session['client_data']['pre-authorized_code'] = request.form['pre_authorized_code']
            #session['client_data']['reason'] = request.form['reason']
            #session['client_data']['reason_2'] = request.form.get('reason_2', "")
            #session['client_data']['reason_3'] = request.form.get('reason_4', "")
            #session['client_data']['reason_4'] = request.form.get('reason_4', "")
            #session['client_data']['credential_requested'] = request.form['credential_requested']
            #session['client_data']['credential_requested_2'] = request.form['credential_requested_2']
            #session['client_data']['credential_requested_3'] = request.form['credential_requested_3']
            #session['client_data']['credential_requested_4'] = request.form['credential_requested_4']
            session['client_data']['credential_to_issue'] = request.form['credential_to_issue']
            #session['client_data']['credential_to_issue_2'] = request.form['credential_to_issue_2']
            session['client_data']['qrcode_message'] = request.form['qrcode_message']
            session['client_data']['mobile_message'] = request.form['mobile_message'] 
            session['client_data']['page_background_color'] = request.form['page_background_color']      
            session['client_data']['page_text_color'] = request.form['page_text_color']  
            session['client_data']['qrcode_background_color'] = request.form['qrcode_background_color']    
              
            if request.form['button'] == "preview" :
                return redirect ('/sandbox/ebsi/issuer/console/preview')

            if request.form['button'] == "activity" :
                return redirect ('/sandbox/ebsi/issuer/console/activity')
            
            if request.form['button'] == "advanced" :
                return redirect ('/sandbox/ebsi/issuer/console/advanced')
            
            if request.form['button'] == "update" :
                db_api.update_ebsi_issuer(request.form['client_id'], json.dumps(session['client_data']))
                return redirect('/sandbox/ebsi/issuer/console?client_id=' + request.form['client_id'])

            if request.form['button'] == "copy" :
                new_client_id=  db_api.create_ebsi_issuer(mode,  user=session['login_name'])
                new_data = copy.deepcopy(session['client_data'])
                new_data['application_name'] = new_data['application_name'] + ' (copie)'
                new_data['client_id'] = new_client_id
                new_data['user'] = session['login_name']
                db_api.update_ebsi_issuer(new_client_id, json.dumps(new_data))
                return redirect('/sandbox/ebsi/issuer/console?client_id=' + new_client_id)


async def ebsi_issuer_advanced() :
    global  reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        session['client_data'] = json.loads(db_api.read_ebsi_issuer(session['client_id']))
        """
        pre_authorized_code_select = str()       
        for key, value in pre_authorized_code_list.items() :
                if key ==  session['client_data'].get('pre_authorized_code', "") :
                    pre_authorized_code_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    pre_authorized_code_select +=  "<option value=" + key + ">" + value + "</option>"
        """
        ebsi_vc_type_select = str()       
        for key, value in ebsi_vc_type_list.items() :
                if key ==   session['client_data'].get('ebsi_issuer_vc_type', "jwt_vc") :
                    ebsi_vc_type_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    ebsi_vc_type_select +=  "<option value=" + key + ">" + value + "</option>"

        did_ebsi = session['client_data']['did_ebsi']
        print('did ebsi = ', did_ebsi)
        print('jwk = ', session['client_data']['jwk'])

        did_document = ebsi.did_resolve(did_ebsi, session['client_data']['jwk'])
        jwk = json.dumps(json.loads(session['client_data']['jwk']), indent=4)
        did_ebsi = session['client_data']['did_ebsi']
        return render_template('ebsi/ebsi_issuer_advanced.html',
                client_id = session['client_data']['client_id'],
                jwk = jwk,
                #pre_authorized_code_select=pre_authorized_code_select,
                ebsi_vc_type_select=ebsi_vc_type_select,
                did_ebsi = did_ebsi,
                did_document=json.dumps(json.loads(did_document), indent=4)
                )
    if request.method == 'POST' :        
        if request.form['button'] == "back" :
            return redirect('/sandbox/ebsi/issuer/console?client_id=' + request.form['client_id'])

        if request.form['button'] == "update" :
            #session['client_data']['pre_authorized_code'] = request.form['pre_authorized_code']
            session['client_data']['ebsi_issuer_vc_type'] = request.form['ebsi_issuer_vc_type']
            jwk_dict = json.loads(session['client_data']['jwk'])
            jwk_dict['alg'] = "ES256K"
            session['client_data']['jwk'] = json.dumps(jwk_dict)
            if request.form['method'] == "ebsi" and  request.form['did_ebsi'] != "Not applicable" :
                session['client_data']['did_ebsi'] = request.form['did_ebsi']
            db_api.update_ebsi_issuer( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/ebsi/issuer/console/advanced')
          