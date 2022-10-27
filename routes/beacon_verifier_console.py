from flask import  request, render_template, redirect, session, jsonify
import json
import logging
import didkit
import copy
import db_api 
import uuid
from op_constante import protocol_list, method_list, beacon_verifier_credential_list
import ebsi
import beacon_activity_db_api
from datetime import datetime

logging.basicConfig(level=logging.INFO)

DID_issuer = "did:tz:tz1NyjrTUNxDpPaqNZ84ipGELAcTWYg6s5Du"


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/beacon/verifier/console/logout',  view_func=beacon_verifier_nav_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/beacon/verifier/console',  view_func=beacon_verifier_console, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/beacon/verifier/console/select',  view_func=beacon_verifier_select, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/beacon/verifier/console/advanced',  view_func=beacon_verifier_advanced, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/beacon/verifier/console/activity',  view_func=beacon_verifier_activity, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/beacon/verifier/console/qrcode',  view_func=beacon_verifier_qrcode, methods = ['GET', 'POST'])
    # nav bar option
    app.add_url_rule('/sandbox/op/beacon/verifier/nav/logout',  view_func=beacon_verifier_nav_logout, methods = ['GET'])
    app.add_url_rule('/sandbox/op/beacon/verifier/nav/create',  view_func=beacon_verifier_nav_create, methods = ['GET'], defaults= {'mode' : mode})
    return
 
async def beacon_verifier_qrcode() :
    payload = session['client_data']['issuer_landing_page'] #+ "?issuer=" + DID_issuer
    url = payload.split('#')[1]
    payload = session['client_data'].get('beacon_payload_message', 'Any string') + session['client_data']['issuer_landing_page'] #+ "?issuer=" + DID_issuer
    return render_template('beacon/beacon_verifier_qrcode.html', url=url, payload=payload)


def beacon_verifier_nav_logout() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    session.clear()
    return redirect ('/sandbox/saas4ssi')


# display activities of the beacon
def beacon_verifier_activity() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :  
        activities = beacon_activity_db_api.list(session['client_data']['client_id'])
        activities.reverse() 
        activity_list = str()
        for data in activities :
            data_dict = json.loads(data)
            verification = "Succeed" if data_dict.get('verification', True) else "Failed"
            activity = """<tr>
                    <td>""" + data_dict['presented'] + """</td>
                    <td>""" +  data_dict['blockchainAddress'] + """</td>
                    <td>""" + " ".join(data_dict['vc_type']) + """</td>
                    <td>""" + verification + """</td>
                    </tr>"""
            activity_list += activity
        return render_template('beacon/beacon_verifier_activity.html', activity=activity_list) 
    else :
        return redirect('/sandbox/op/beacon/verifier/console?client_id=' + session['client_data']['client_id'])


def beacon_verifier_select(mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :  
        my_list = db_api.list_beacon_verifier()
        verifier_list=str()
        for data in my_list :
            data_dict = json.loads(data)
            client_id = data_dict['client_id']
            act = len(beacon_activity_db_api.list(client_id))   
            standalone = "off" if data_dict.get('standalone') in [None, False]  else "on" 
            try :
                if data_dict['user'] == "all" or session['login_name'] in [data_dict['user'], "admin"] :
                    verifier = """<tr>
                        <td>""" + data_dict.get('application_name', "") + """</td>
                        <td>""" + str(act) + """</td>
                        <td>""" + data_dict['user'] + """</td>
                        <td>""" + beacon_verifier_credential_list[data_dict['vc']] + """</td>
                         <td>""" + standalone + """</td>                       
                        <td>""" + data_dict['callback'] + """</td>
                        <td><a href=/sandbox/op/beacon/verifier/console?client_id=""" + data_dict['client_id'] + """>""" + data_dict['client_id'] + """</a></td>
                        <td>""" + data_dict['client_secret'] + """</td>
                    </tr>"""
                    verifier_list += verifier
            except :
                pass
        return render_template('beacon/beacon_verifier_select.html', verifier_list=verifier_list, login_name=session['login_name']) 
    else :
        if request.form['button'] == "new" :
            return redirect('/sandbox/op/beacon/veifier/console?client_id=' + db_api.create_verifier(mode, user=session['login_name']))
        elif request.form['button'] == "logout" :
            session.clear()
            return redirect ('/sandbox/saas4ssi')
        elif request.form['button'] == "home" :
            return render_template("menu.html", login_name=session["login_name"])


def beacon_verifier_nav_create(mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return redirect('/sandbox/op/beacon/verifier/console?client_id=' + db_api.create_beacon_verifier(mode,  user=session['login_name']))


async def beacon_verifier_console(mode) :
    global  reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            return redirect('/sandbox/op/beacon/verifier/console/select')
        else  :
            session['client_id'] = request.args.get('client_id')
        session['client_data'] = json.loads(db_api.read_beacon_verifier(session['client_id']))
        raw_payload = session['client_data'].get('beacon_payload_message', 'Any string') + session['client_data']['issuer_landing_page'] #+ "?issuer=" + DID_issuer
        micheline_payload = payload_tezos( raw_payload, 'MICHELINE')
        operation_payload = payload_tezos( raw_payload, 'OPERATION')
        #DID, did_ebsi, jwk, did_document = await did(session)
        vc_select_1 = str()
        for key, value in beacon_verifier_credential_list.items() :
                if key ==   session['client_data']['vc'] :
                    vc_select_1 +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    vc_select_1 +=  "<option value=" + key + ">" + value + "</option>"
        vc_select_2 = str()
        for key, value in beacon_verifier_credential_list.items() :
                if key ==   session['client_data'].get('vc_2', "DID") :
                    vc_select_2 +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    vc_select_2 +=  "<option value=" + key + ">" + value + "</option>"
        return render_template('beacon/beacon_verifier_console.html',
                raw_payload = raw_payload,
                micheline_payload = micheline_payload,
                operation_payload = operation_payload,
                beacon_payload_message = session['client_data'].get('beacon_payload_message', 'Any string'),
                standalone = "" if session['client_data'].get('standalone') in [None, False]  else "checked" ,
                login_name=session['login_name'],
                application_name=session['client_data'].get('application_name', 'Unknown'),
                client_secret=session['client_data']['client_secret'],
                user=session['client_data']['user'], 
                webhook=session['client_data']['webhook'],
                #issuer_landing_page = session['client_data']['issuer_landing_page'] + "?issuer=" + DID_issuer,
                contact_name = session['client_data'].get('contact_name'),
                contact_email = session['client_data'].get('contact_email'),
                privacy_url = session['client_data'].get('privacy_url'),
                landing_page_url = session['client_data'].get('landing_page_url'),
                terms_url = session['client_data'].get('terms_url'),
                client_id= session['client_data']['client_id'],
                company_name = session['client_data']['company_name'],
                note = session['client_data']['note'],
                reason = session['client_data']['reason'],
                reason_2 = session['client_data'].get('reason_2'),
                vc_select_1=vc_select_1,
                vc_issuer_id =  session['client_data'].get('vc_issuer_id', ""),
                vc_select_2=vc_select_2,
                )
    if request.method == 'POST' :
        if request.form['button'] == "delete" :
            db_api.delete_beacon_verifier( request.form['client_id'])
            return redirect ('/sandbox/op/beacon/verifier/console')
        else :
            session['client_data']['beacon_payload_message'] = request.form['beacon_payload_message']
            session['client_data']['contact_name'] = request.form['contact_name']
            session['client_data']['standalone'] = request.form.get('standalone') 
            session['client_data']['user'] = request.form['user']
            session['client_data']['webhook'] = request.form['webhook']
            session['client_data']['note'] = request.form['note']          
            session['client_data']['contact_email'] = request.form['contact_email']
            #session['client_data']['landing_page_url'] = request.form['landing_page_url']
            session['client_data']['client_id'] =  request.form['client_id']
            session['client_data']['company_name'] = request.form['company_name']
            session['client_data']['application_name'] = request.form['application_name']
            session['client_data']['reason'] = request.form.get('reason', "")
            session['client_data']['reason_2'] = request.form.get('reason_2', "")
            session['client_data']['vc'] = request.form['vc_1']
            session['client_data']['vc_issuer_id'] = request.form['vc_issuer_id']
            session['client_data']['vc_2'] = request.form['vc_2']            
              
            if request.form['button'] == "qrcode" :
                return redirect ('/sandbox/op/beacon/verifier/console/qrcode')
            if request.form['button'] == "activity" :
                return redirect ('/sandbox/op/beacon/verifier/console/activity')
            if request.form['button'] == "advanced" :
                return redirect ('/sandbox/op/beacon/verifier/console/advanced')
            if request.form['button'] == "update" :
                db_api.update_beacon_verifier(request.form['client_id'], json.dumps(session['client_data']))
                return redirect('/sandbox/op/beacon/verifier/console?client_id=' + request.form['client_id'])
            if request.form['button'] == "copy" :
                new_client_id=  db_api.create_beacon_verifier(mode,  user=session['login_name'])
                new_data = copy.deepcopy(session['client_data'])
                new_data['application_name'] = new_data['application_name'] + ' (copie)'
                new_data['client_id'] = new_client_id
                new_data['user'] = session['login_name']
                db_api.update_beacon_verifier(new_client_id, json.dumps(new_data))
                return redirect('/sandbox/op/beacon/verifier/console?client_id=' + new_client_id)            
            return(jsonify('ok'))


async def beacon_verifier_advanced() :
    global  reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        session['client_data'] = json.loads(db_api.read_beacon_verifier(session['client_id']))
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
        DID, did_ebsi, jwk, did_document = await did(session)
        return render_template('beacon_verifier_advanced.html',
                client_id = session['client_data']['client_id'],
                protocol = session['client_data']['protocol'],
                jwk = jwk,
                method = session['client_data']['method'],
                protocol_select=protocol_select,
                method_select=method_select,
                did_ebsi = did_ebsi,
                DID = DID,
                did_document=json.dumps(json.loads(did_document), indent=4)
                )
    if request.method == 'POST' :
        if request.form['button'] == "back" :
            return redirect('/sandbox/op/beacon/verifier/console?client_id=' + request.form['client_id'])

        if request.form['button'] == "update" :
            session['client_data']['protocol'] = request.form['protocol']
            session['client_data']['method'] = request.form['method']

            if  session['client_data']['method'] == "relay" :
                db_api.update_beacon_verifier( request.form['client_id'], json.dumps(session['client_data']))
                return redirect('/sandbox/op/beacon/verifier/console/advanced')

            if request.form['method'] != "ebsi" :
                try :
                    didkit.key_to_did(request.form['method'], session['client_data']['jwk'])
                except :
                    logging.error('wrong key/method')
                    return redirect('/sandbox/op/beacon/verifier/console/advanced')

            jwk_dict = json.loads(session['client_data']['jwk'])
            if request.form['method'] in ['key', "ebsi"] :
                jwk_dict['alg'] = "ES256K"
            else : 
                jwk_dict['alg'] = "ES256K-R"
            session['client_data']['jwk'] = json.dumps(jwk_dict)
            if request.form['method'] == "ebsi" and  request.form['did_ebsi'] != "Not applicable" :
                session['client_data']['did_ebsi'] = request.form['did_ebsi']
            db_api.update_beacon_verifier( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/op/beacon/verifier/console/advanced')


async def did(session) :
    if session['client_data']['method'] == "ebsi" :
        DID = "Not applicable"
        did_document = ebsi.did_resolve(DID, session['client_data']['jwk'])
        jwk = json.dumps(json.loads(session['client_data']['jwk']), indent=4)
        did_ebsi = session['client_data']['did_ebsi']

    elif session['client_data']['method'] == "relay" :
        DID = "Unknown"
        did_document = '{ "DID document" : "Unknown" }'
        jwk = '{ "JWK" : "Unknown" }'
        did_ebsi = "Not applicable"
    else : 
        DID = didkit.key_to_did(session['client_data']['method'], session['client_data']['jwk'])
        did_document = await didkit.resolve_did(DID, '{}')
        jwk = json.dumps(json.loads(session['client_data']['jwk']), indent=4)
        did_ebsi = 'Not applicable'
    return DID, did_ebsi, jwk, did_document


"""
https://docs.walletbeacon.io/guides/sign-payload/
https://tezostaquito.io/docs/signing/#generating-a-signature-with-beacon-sdk
"""
def payload_tezos(input, signature_type) :
    if signature_type not in ['MICHELINE', 'OPERATION'] :
        return
    char2Bytes = lambda text : text.encode('utf-8').hex()
    formattedInput = ' '.join([
        'Tezos Signed Message:',
        'altme.io',
        datetime.now().replace(microsecond=0).isoformat() + "Z",
        input
        ])
    code = '05' if signature_type == "MICHELINE" else '03'
    bytes = char2Bytes(formattedInput)
    payloadBytes = code + '0100' + char2Bytes(str(len(bytes)))  + bytes
    return payloadBytes

