from flask import  request, render_template, redirect, session, jsonify
import json
import logging
import didkit
import db_api 
from urllib.parse import urlencode
import uuid
from op_constante import credential_requested_list, credential_to_issue_list, protocol_list, method_list
import ebsi

logging.basicConfig(level=logging.INFO)

public_key =  {"e":"AQAB","kid" : "123", "kty":"RSA","n":"uEUuur6rqoEMaV3qEgzf4a8jSWzLuftWzW1t9SApbKKKI9_M2ZCValgbUJqpto190zKgBge20d7Hwb24Y_SrxC2e8W7sQMNCEHdCrAvzjtk36o3tKHbsSfYFRfDexZJKQ75tsA_TOSMRKH_xGSO-15ZL86NXrwMrg3CLPXw6T0PjG38IsJ2UHAZL-3ezw7ibDto8LD06UhLrvCMpBlS6IMmDYFRJ-d2KvnWyKt6TyNC-0hNcDS7X0jaODATmDh-rOE5rv5miyljjarC_3p8D2MJXmYWk0XjxzozXx0l_iQyh-J9vQ_70gBqCV1Ifqlu8VkasOfIaSbku_PJHSXesFQ"}


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/issuer/console/logout',  view_func=issuer_console_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/issuer/console',  view_func=issuer_console, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer/console/select',  view_func=issuer_select, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/issuer/console/advanced',  view_func=issuer_advanced, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/issuer/console/preview',  view_func=issuer_preview, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/issuer/preview_presentation/<stream_id>',  view_func=issuer_preview_presentation_endpoint, methods = ['GET', 'POST'],  defaults={'red' : red})
    return
      
# authentication
def issuer_console_logout():
    if session.get('is_connected') :
        session.clear()
    return redirect('/sandbox/op/issuer/console')


def issuer_select(mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')

    if request.method == 'GET' :  
        my_list = db_api.list_issuer()
        issuer_list=str()
        for data in my_list :
            data_dict = json.loads(data)
            if session['login_name'] == data_dict['user'] or data_dict['user'] == "all" or session['login_name'] == "admin1234" :
                issuer = """<tr>
                    <td>""" + data_dict['company_name'] + """</td>
                     <td>""" + data_dict['user'] + """</td>
                    <td><a href=/sandbox/op/issuer/console?client_id=""" + data_dict['client_id'] + """>""" + data_dict['client_id'] + """</a></td>
                    <td>""" + data_dict['credential_to_issue'] + """</td>
                    <td>""" + data_dict['credential_requested'] + """</td>
                    <td>""" + data_dict['callback'] + """</td>
                    <td>""" + data_dict['webhook'] + """</td>
                    </tr>"""
                issuer_list += issuer
            else :
                pass     
        return render_template('issuer_select.html', issuer_list=issuer_list, login_name=session['login_name']) 
    else :
        if request.form['button'] == "new" :
            return redirect('/sandbox/op/issuer/console?client_id=' + db_api.create_issuer(mode))
        elif request.form['button'] == "logout" :
            session.clear()
            return redirect ('/sandbox/saas4ssi')
       

def issuer_preview (mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    stream_id = str(uuid.uuid1())
    client_id = session['client_data']['client_id']
    issuer_data = json.loads(db_api.read_issuer(client_id))
    qrcode_message = issuer_data.get('qrcode_message', "No message")
    mobile_message = issuer_data.get('mobile_message', "No message")
    if session['client_data']['method'] == "ebsi" :
        issuer_did = did_ebsi(session['client_data']['jwk'])
    else : 
        issuer_did = didkit.key_to_did(session['client_data']['method'], session['client_data']['jwk'])
    url = mode.server + 'sandbox/issuer/preview_presentation/' + stream_id + '?' + urlencode({'issuer' : issuer_did})
    deeplink = mode.deeplink + 'app/download?' + urlencode({'uri' : url})
    return render_template('op_issuer_qrcode.html',
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
                            company_name=issuer_data['company_name'],
                            back_button = True,
                            page_background_color = issuer_data['page_background_color'],
                            page_text_color = issuer_data['page_text_color'],
                            qrcode_background_color = issuer_data['qrcode_background_color'],
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
        return jsonify(my_pattern)


def issuer_console(mode) :
    global  reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            return redirect('/sandbox/op/issuer/console/select')
        else  :
            session['client_id'] = request.args.get('client_id')
        session['client_data'] = json.loads(db_api.read_issuer(session['client_id']))
        credential_requested_select = str()
        for key, value in credential_requested_list.items() :
                if key ==   session['client_data']['credential_requested'] :
                    credential_requested_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_requested_select +=  "<option value=" + key + ">" + value + "</option>"
        credential_to_issue_select = str()
        for key, value in credential_to_issue_list.items() :
                if key ==   session['client_data']['credential_to_issue'] :
                    credential_to_issue_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_to_issue_select +=  "<option value=" + key + ">" + value + "</option>"
        return render_template('issuer_console.html',
                public_key=public_key,
                login_name=session['login_name'],
                user=session['client_data']['user'], 
                callback=session['client_data']['callback'],
                webhook=session['client_data']['webhook'],
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
                page_title = session['client_data']['page_title'],
                note = session['client_data']['note'],
                page_subtitle = session['client_data']['page_subtitle'],
                page_description = session['client_data']['page_description'],
                qrcode_message = session['client_data'].get('qrcode_message', ""),
                mobile_message = session['client_data'].get('mobile_message', ""),
                credential_to_issue_select = credential_to_issue_select,
                credential_requested_select =  credential_requested_select,
                page_background_color = session['client_data']['page_background_color'],
                page_text_color = session['client_data']['page_text_color'],
                qrcode_background_color = session['client_data']['qrcode_background_color']
                )
    if request.method == 'POST' :
        if request.form['button'] == "new" :
            return redirect('/sandbox/op/issuer/console?client_id=' + db_api.create_issuer(mode,  user=session['login_name']))
        elif request.form['button'] == "demo" :
            return redirect('/sandbox/op/issuer/console?client_id=' + db_api.create_issuer(mode,  user=session['login_name'], demo=True))
        
        elif request.form['button'] == "select" :
            return redirect ('/sandbox/op/issuer/console/select')
        
        elif request.form['button'] == "delete" :
            db_api.delete_issuer( request.form['client_id'])
            return redirect ('/sandbox/op/issuer/console')

        elif request.form['button'] == "logout" :
            session.clear()
            return redirect ('/sandbox/saas4ssi')

        elif request.form['button'] == "advanced" :
            return redirect ('/sandbox/op/issuer/console/advanced')
        
        elif request.form['button'] in [ "update", "preview"] :
            session['client_data']['contact_name'] = request.form['contact_name']
            session['client_data']['user'] = request.form['user']
            session['client_data']['callback'] = request.form['callback']
            session['client_data']['webhook'] = request.form['webhook']
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
            session['client_data']['reason'] = request.form.get('reason', "")
            session['client_data']['credential_requested'] = request.form['credential_requested']
            session['client_data']['credential_to_issue'] = request.form['credential_to_issue']
            session['client_data']['qrcode_message'] = request.form['qrcode_message']
            session['client_data']['mobile_message'] = request.form['mobile_message'] 
            session['client_data']['page_background_color'] = request.form['page_background_color']      
            session['client_data']['page_text_color'] = request.form['page_text_color']         
            session['client_data']['qrcode_background_color'] = request.form['qrcode_background_color']      
            db_api.update_issuer(request.form['client_id'], json.dumps(session['client_data']))
            if request.form['button'] == "preview" :
                return redirect ('/sandbox/op/issuer/console/preview')
            return redirect('/sandbox/op/issuer/console?client_id=' + request.form['client_id'])
        else :
            return redirect('/sandbox/op/issuer/console')


async def issuer_advanced() :
    global  reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        session['client_data'] = json.loads(db_api.read_issuer(session['client_id']))
        protocol_select = str()       
        for key, value in protocol_list.items() :
                if key ==   session['client_data'].get('protocol', "") :
                    protocol_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    protocol_select +=  "<option value=" + key + ">" + value + "</option>"
        method_select = str()       
        for key, value in method_list.items() :
                if key ==   session['client_data'].get('method', "") :
                    method_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    method_select +=  "<option value=" + key + ">" + value + "</option>"
        if session['client_data'].get('emails') :
            emails_filtering = """<input class="form-check-input" checked type="checkbox" name="emails" value="ON" id="flexCheckDefault">"""
        else :
            emails_filtering = """<input class="form-check-input" type="checkbox" name="emails" value="ON" id="flexCheckDefault">"""

        if session['client_data']['method'] == "ebsi" :
            DID = session['client_data']['did_ebsi']
            did_document = ebsi.did_resolve(DID, session['client_data']['jwk'])
        else : 
            DID = didkit.key_to_did(session['client_data']['method'], session['client_data']['jwk'])
            did_document = await didkit.resolve_did(DID, '{}')
        return render_template('issuer_advanced.html',
                client_id = session['client_data']['client_id'],
                protocol = session['client_data']['protocol'],
                jwk = json.dumps(json.loads(session['client_data']['jwk']), indent=4),
                method = session['client_data']['method'],
                emails_filtering=emails_filtering,
                protocol_select=protocol_select,
                method_select=method_select,
                did_ebsi = session['client_data']['did_ebsi'],
                DID = DID,
                did_document=json.dumps(json.loads(did_document), indent=4)
                )
    if request.method == 'POST' :
        if request.form['button'] == "back" :
            return redirect ('/sandbox/op/issuer/console?client_id=' + request.form['client_id'] )
        
        elif request.form['button'] == "update" :
            session['client_data']['protocol'] = request.form['protocol']
            if request.form['method'] != "ebsi" :
                try :
                    didkit.key_to_did(request.form['method'], request.form['jwk'])
                except :
                    logging.error('wrong key/method')
                    return redirect('/sandbox/op/issuer/console/advanced')
            session['client_data']['method'] = request.form['method']
            jwk_dict = json.loads(request.form['jwk'])
            if request.form['method'] in ['key', "ebsi"] :
                jwk_dict['alg'] = "ES256K"
            else : 
                jwk_dict['alg'] = "ES256K-R"
            session['client_data']['jwk'] = json.dumps(jwk_dict)
            session['client_data']['did_ebsi'] = request.form['did_ebsi']
            db_api.update_issuer( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/op/issuer/console/advanced')
          