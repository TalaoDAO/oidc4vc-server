from flask import  request, render_template, redirect, session, jsonify, Response
import json
import logging
import didkit
import copy
import db_api 
import message
import uuid
from op_constante import protocol_list, method_list, beacon_verifier_credential_list
from op_constante import sbt_network_list, tezid_network_list
import ebsi
import beacon_activity_db_api
import db_user_api
import op_constante
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

    # API Gamer Pass
    app.add_url_rule('/sandbox/op/beacon/verifier/api/create/<verifiable_credential>',  view_func=create_verifier_gamer_pass, methods = ['POST'], defaults= {'mode' : mode})

    return
 

#from ratelimiter import RateLimiter
# API pour Verifier https://pypi.org/project/ratelimiter/
#@RateLimiter(max_calls=1, period=10)
def create_verifier_gamer_pass(verifiable_credential, mode):
    data_received = request.json
    try :
        contact_email = data_received['contact_email']
        webhook = data_received['webhook']
    except :
        headers = {'WWW-Authenticate' : 'Bearer realm="userinfo", error="invalid_request", error_description = "Data is missing in request"'}
        return Response(status=401,headers=headers) 
    
    # only one verifier by email
    if not db_user_api.read(contact_email) :
        data = op_constante.user
        data["did"] = "unknown"
        data['login_name'] = contact_email
        db_user_api.create(contact_email, data)
        try :
            message.message("New sign up on Altme through API", "thierry@altme.io", "New user = " + contact_email, mode)
        except :
            pass
    else :
        logging.warning('user alreday registered')
        headers = {'WWW-Authenticate' : 'Bearer realm="userinfo", error="user_already_registered", error_description = "Use the Talao.co web platform to create new verifiers"'}
        return Response(status=401,headers=headers)
    
    if verifiable_credential == "gamerpass" :
        beacon_payload_message =  "Sign with your Gamer Pass" if not data_received.get('message') else data_received['message']
        reason = "Select your Gamer Pass"
        vc = "GamerPass"
    elif verifiable_credential == "over13" :
        beacon_payload_message =  "Sign with your proof of age : Over13" if not data_received.get('message') else data_received['message']
        reason = "Select your Over13 proof"
        vc = "Over13"
    elif verifiable_credential == "over18" :
        beacon_payload_message =  "Sign with your proof of age : Over18" if not data_received.get('message') else data_received['message']
        reason = "Select your Over18 proof"
        vc = "Over18"
    else :
        logging.warning('credentila not suupported')
        headers = {'WWW-Authenticate' : 'Bearer realm="userinfo", error="credential_not_supported", error_description = "This credential is not supported"'}
        return Response(status=401,headers=headers)
    
    verifier_id = db_api.create_beacon_verifier(mode,  user=contact_email)

    #website = "altme.io" if not data_received.get('website') else data_received['website']
    application_name = "Application of " + contact_email if not data_received.get('application_name') else data_received['application_name']
    company_name = "Company of " + contact_email if not data_received.get('company_name') else data_received['company_name']
    contact_name = "" if not data_received.get('contact_name') else data_received['contact_name']

    # update verifier
    verifier_data =  json.loads(db_api.read_beacon_verifier(verifier_id))
    verifier_data["vc"] = vc
    verifier_data["reason"] = reason
    verifier_data["beacon_payload_message"] = beacon_payload_message
    verifier_data["webhook"] = webhook
    verifier_data["contact_email"] = contact_email
    verifier_data['user'] = contact_email
    verifier_data["application_name"] = application_name
    verifier_data["company_name"] = company_name
    verifier_data["contact_name"] = contact_name
    db_api.update_beacon_verifier(verifier_id,  json.dumps(verifier_data))
    
    # send back verifier data
    RAW_payload =  beacon_payload_message + ' ' + verifier_data['issuer_landing_page'] +'?id=<your_user_id>'
    data_sent = {
        "contact_email" : contact_email,
        "vc" : vc,
        "user" : contact_email,
        "application_name" : application_name,
        "company_name" : company_name,
        "contact_name" : contact_name,
        "webhook" : webhook,
        "verifier_id" : verifier_id,
        "verifier_secret" : verifier_data['client_secret'],
        "beacon_payload_message" : beacon_payload_message,
        "RAW_payload" : RAW_payload,
        #"MICHELINE_payload" : payload_tezos(RAW_payload, 'MICHELINE', website=website),
        #"OPERATION_payload"  : payload_tezos(RAW_payload, 'OPERATION', website=website)
    }
    return jsonify(data_sent)

# curl -d '{"webhook" : "https://altme.io/webhook", "contact_email" :"thierry@altme.io"}'  -H "Content-Type: application/json" -X POST http://192.168.0.66:3000/sandbox/op/beacon/verifier/api/create/over13
# curl -d '{"webhook" : "https://altme.io/webhook", "contact_email" :"thierry@gmail.io"}'  -H "Content-Type: application/json" -X POST https://talao.co/sandbox/op/beacon/verifier/api/create/over13

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
                    <td>""" +  data_dict.get('blockchainAddress', "Unknow") + """</td>
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
                        <td>""" + data_dict['webhook'] + """</td>
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
        raw_payload = session['client_data'].get('beacon_payload_message', 'Any string') + session['client_data']['issuer_landing_page'] + "?id="
        micheline_payload = payload_tezos( raw_payload, 'MICHELINE')
        operation_payload = payload_tezos( raw_payload, 'OPERATION')
        #DID, did_ebsi, jwk, did_document = await did(session)
        
        # SBT network
        sbt_network_select = str()
        for key, value in sbt_network_list.items() :
                if key ==   session['client_data'].get('sbt_network', 'none') :
                    sbt_network_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    sbt_network_select +=  "<option value=" + key + ">" + value + "</option>"
        
        # TezID network
        tezid_network_select = str()
        for key, value in tezid_network_list.items() :
                if key ==   session['client_data'].get('tezid_network', 'none') :
                    tezid_network_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    tezid_network_select +=  "<option value=" + key + ">" + value + "</option>"
        
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
                sbt_name = session['client_data'].get('sbt_name', ''),
                sbt_description = session['client_data'].get('sbt_description', ''),
                sbt_network = session['client_data'].get('sbt_network', 'none'),
                sbt_thumbnail_uri = session['client_data'].get('sbt_thumbnail_uri', ''),
                sbt_display_uri = session['client_data'].get('sbt_display_uri', ''),
                sbt_artifact_uri = session['client_data'].get('sbt_display_uri', ''),
                sbt_network_select=sbt_network_select,
                
                raw_payload = raw_payload,
                micheline_payload = micheline_payload,
                operation_payload = operation_payload,
                beacon_payload_message = session['client_data'].get('beacon_payload_message', 'Any string'),
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
                vc_select_2=vc_select_2,
                tezid_proof_type = session['client_data'].get('tezid_proof_type', session['client_data']['client_id']),
                tezid_network_select=tezid_network_select
                )
    if request.method == 'POST' :
        if request.form['button'] == "delete" :
            db_api.delete_beacon_verifier( request.form['client_id'])
            return redirect ('/sandbox/op/beacon/verifier/console')
        else :
            session['client_data']['sbt_name'] = request.form['sbt_name']
            session['client_data']['sbt_description'] = request.form['sbt_description']
            session['client_data']['sbt_display_uri'] = request.form['sbt_display_uri']
            session['client_data']['sbt_artifact_uri'] = request.form['sbt_display_uri']
            session['client_data']['sbt_thumbnail_uri'] = request.form['sbt_thumbnail_uri']
            session['client_data']['sbt_network'] = request.form['sbt_network']

            session['client_data']['beacon_payload_message'] = request.form['beacon_payload_message']
            session['client_data']['contact_name'] = request.form['contact_name']
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
            session['client_data']['vc_2'] = request.form['vc_2']   
            session['client_data']['tezid_network'] = request.form['tezid_network']   
            session['client_data']['tezid_proof_type'] = request.form['tezid_proof_type']           
              
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




def beacon_verifier_advanced() :
    global vc, reason
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
        
        return render_template('beacon/beacon_verifier_advanced.html',
                client_id = session['client_data']['client_id'],
                protocol = session['client_data']['protocol'],
                protocol_select=protocol_select
                )
    if request.method == 'POST' :

        if request.form['button'] == "back" :
            return redirect ('/sandbox/op/beacon/verifier/console?client_id=' + request.form['client_id'] )
        
        elif request.form['button'] == "update" :
            session['client_data']['protocol'] = request.form['protocol']
            db_api.update_verifier( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/op/beacon/verifier/console?client_id=' + request.form['client_id'])
          



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
def payload_tezos(input, signature_type, website='altme.io') :
    if signature_type not in ['MICHELINE', 'OPERATION'] :
        return
    char2Bytes = lambda text : text.encode('utf-8').hex()
    formattedInput = ' '.join([
        'Tezos Signed Message:',
        website,
        datetime.now().replace(microsecond=0).isoformat() + "Z",
        input
        ])
    code = '05' if signature_type == "MICHELINE" else '03'
    bytes = char2Bytes(formattedInput)
    payloadBytes = code + '0100' + char2Bytes(str(len(bytes)))  + bytes
    return payloadBytes

