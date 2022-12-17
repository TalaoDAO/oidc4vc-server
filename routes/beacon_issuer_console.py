from flask import  request, render_template, redirect, session, jsonify
import json
import logging
import didkit
import copy
import db_api 
from urllib.parse import urlencode
import uuid
from op_constante import credential_requested_list, credential_requested_list_2, credential_to_issue_list, protocol_list, method_list, landing_page_style_list, credential_to_issue_list_for_guest
from op_constante import sbt_network_list, tezid_network_list
import ebsi
import beacon_activity_db_api
from datetime import datetime

logging.basicConfig(level=logging.INFO)

DID_issuer = "did:tz:tz1NyjrTUNxDpPaqNZ84ipGELAcTWYg6s5Du"


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/op/beacon/console/logout',  view_func=beacon_nav_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/beacon/console',  view_func=beacon_console, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/sandbox/op/beacon/console/select',  view_func=beacon_select, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/beacon/console/advanced',  view_func=beacon_advanced, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/beacon/console/activity',  view_func=beacon_activity, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/op/beacon/console/qrcode',  view_func=beacon_qrcode, methods = ['GET', 'POST'])

    # nav bar option
    app.add_url_rule('/sandbox/op/beacon/nav/logout',  view_func=beacon_nav_logout, methods = ['GET'])
    app.add_url_rule('/sandbox/op/beacon/nav/create',  view_func=beacon_nav_create, methods = ['GET'], defaults= {'mode' : mode})
    return
    
# authentication
"""
def beacon_console_logout():
    if session.get('is_connected') :
        session.clear()
    else :
        return redirect('/sandbox/saas4ssi')
    return redirect('/sandbox/op/beacon/console')
"""

async def beacon_qrcode() :
    payload = session['client_data']['issuer_landing_page'] #+ "?issuer=" + DID_issuer
    url = payload.split('#')[1]
    payload = session['client_data'].get('beacon_payload_message', 'Any string') + session['client_data']['issuer_landing_page'] #+ "?issuer=" + DID_issuer
    return render_template('beacon/beacon_issuer_qrcode.html', url=url, payload=payload)


def beacon_nav_logout() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    session.clear()
    return redirect ('/sandbox/saas4ssi')

# display activities of the beacon
def beacon_activity() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')

    if request.method == 'GET' :  
        activities = beacon_activity_db_api.list(session['client_data']['client_id'])
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
        return render_template('beacon/beacon_issuer_activity.html', activity=activity_list) 
    else :
        return redirect('/sandbox/op/beacon/console?client_id=' + session['client_data']['client_id'])

def beacon_select() :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :  
        my_list = db_api.list_beacon()
        beacon_list=str()
        for data in my_list :
            data_dict = json.loads(data)         
            client_id = data_dict['client_id']
            act = len(beacon_activity_db_api.list(client_id))              
            if data_dict['method'] == "ebsi" :
                DID = data_dict['did_ebsi']
            elif data_dict['method'] == "relay" :
                DID = method_list['relay']
            elif data_dict['method'] == False :
                DID = "problem"
            else : 
                DID = didkit.key_to_did(data_dict['method'], data_dict['jwk'])
            if data_dict['user'] == "all" or session['login_name'] in [data_dict['user'], "admin"] :
                beacon = """<tr>
                        <td>""" + data_dict.get('application_name', "unknown") + """</td>
                         <td>""" + str(act) + """</td>
                        <td>""" + data_dict.get('user', "unknown") + """</td>
                        <td><a href=/sandbox/op/beacon/console?client_id=""" + data_dict['client_id'] + """>""" + data_dict['client_id'] + """</a></td>
                        <td>""" + DID[:10] +'....' + DID[-10:] + """</td> 
                        <td>""" + credential_to_issue_list.get(data_dict['credential_to_issue'], 'unknown') + """</td>
                        <td>""" + credential_requested_list.get(data_dict['credential_requested'], 'Unknown') + """</td>
                        <td>""" + credential_requested_list.get(data_dict.get('credential_requested_2'), "None") + """</td>
                        <td>""" + credential_requested_list.get(data_dict.get('credential_requested_3'), "None") + """</td>
                        <td>""" + credential_requested_list.get(data_dict.get('credential_requested_4'), "None") + """</td>

                        </tr>"""
                beacon_list += beacon
        return render_template('beacon/beacon_issuer_select.html', beacon_list=beacon_list, login_name=session['login_name']) 
   
       

def beacon_nav_create(mode) :
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    return redirect('/sandbox/op/beacon/console?client_id=' + db_api.create_beacon(mode,  user=session['login_name']))




async def beacon_console(mode) :
    global  reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        if not request.args.get('client_id') :
            return redirect('/sandbox/op/beacon/console/select')
        else  :
            session['client_id'] = request.args.get('client_id')
        session['client_data'] = json.loads(db_api.read_beacon(session['client_id']))
        
        # TezID network
        tezid_network_select = str()
        for key, value in tezid_network_list.items() :
                if key ==   session['client_data'].get('tezid_network', 'none') :
                    tezid_network_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    tezid_network_select +=  "<option value=" + key + ">" + value + "</option>"

        # SBT network
        sbt_network_select = str()
        for key, value in sbt_network_list.items() :
                if key ==   session['client_data'].get('sbt_network', 'none') :
                    sbt_network_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    sbt_network_select +=  "<option value=" + key + ">" + value + "</option>"
        
        # credential requested 1
        credential_requested_select = str()
        for key, value in credential_requested_list.items() :
                if key ==   session['client_data']['credential_requested'] :
                    credential_requested_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_requested_select +=  "<option value=" + key + ">" + value + "</option>"

        landing_page_style_select = str()
        for key, value in landing_page_style_list.items() :
                if key == session['client_data'].get('landing_page_style') :
                    landing_page_style_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    landing_page_style_select +=  "<option value=" + key + ">" + value + "</option>"
        
        # credential requested 2
        credential_requested_2_select = str()
        for key, value in credential_requested_list_2.items() :
                if key ==   session['client_data'].get('credential_requested_2', "DID") :
                    credential_requested_2_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_requested_2_select +=  "<option value=" + key + ">" + value + "</option>"
        
        # credential requested 3
        credential_requested_3_select = str()
        for key, value in credential_requested_list_2.items() :
                if key ==   session['client_data'].get('credential_requested_3', "DID") :
                    credential_requested_3_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_requested_3_select +=  "<option value=" + key + ">" + value + "</option>"
        
        # credential requested 4
        credential_requested_4_select = str()
        for key, value in credential_requested_list_2.items() :
                if key ==   session['client_data'].get('credential_requested_4', "DID") :
                    credential_requested_4_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_requested_4_select +=  "<option value=" + key + ">" + value + "</option>"


        credential_to_issue_select = str()

        if session["login_name"] == 'admin' :
            credential_items = credential_to_issue_list.items()
        else :
            credential_items = credential_to_issue_list_for_guest.items()
        for key, value in credential_items :
                if key ==   session['client_data']['credential_to_issue'] :
                    credential_to_issue_select +=  "<option selected value=" + key + ">" + value + "</option>"
                else :
                    credential_to_issue_select +=  "<option value=" + key + ">" + value + "</option>"
        
        raw_payload = session['client_data'].get('beacon_payload_message', 'Any string') + session['client_data']['issuer_landing_page'] #+ "?issuer=" + DID_issuer
        micheline_payload = payload_tezos( raw_payload, 'MICHELINE')
        #DID, did_ebsi, jwk, did_document = await did(session)
        return render_template('beacon/beacon_issuer_console.html',
                sbt_name = session['client_data'].get('sbt_name', ''),
                sbt_description = session['client_data'].get('sbt_description', ''),
                sbt_network = session['client_data'].get('sbt_network', 'none'),
                sbt_thumbnail_uri = session['client_data'].get('sbt_thumbnail_uri', ''),
                sbt_display_uri = session['client_data'].get('sbt_display_uri', ''),
                sbt_artifact_uri = session['client_data'].get('sbt_display_uri', ''),
                sbt_network_select =  sbt_network_select,
                
                raw_payload = raw_payload,
                micheline_payload = micheline_payload,
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
                reason = session['client_data']['reason'],
                reason_2 = session['client_data'].get('reason_2', ""),
                reason_3 = session['client_data'].get('reason_3', ""),
                reason_4 = session['client_data'].get('reason_4', ""),
                page_title = session['client_data']['page_title'],
                note = session['client_data']['note'],
                card_title = session['client_data']['card_title'],
                card_subtitle = session['client_data']['card_subtitle'],
                card_description = session['client_data']['card_description'],
                credential_to_issue_select = credential_to_issue_select,
                credential_duration= session['client_data'].get('credential_duration', 365),
                credential_requested_select =  credential_requested_select,
                credential_requested_2_select =  credential_requested_2_select,
                credential_requested_3_select =  credential_requested_3_select,
                credential_requested_4_select =  credential_requested_4_select,
                page_background_color = session['client_data']['page_background_color'],
                card_background_color = session['client_data']['card_background_color'],
                card_text_color = session['client_data']['card_text_color'],
                tezid_proof_type = session['client_data'].get('tezid_proof_type', session['client_data']['client_id']),
                tezid_network_select=tezid_network_select 
                )
    if request.method == 'POST' :
        if request.form['button'] == "delete" :
            db_api.delete_beacon( request.form['client_id'])
            return redirect ('/sandbox/op/beacon/console')
        else :
            session['client_data']['sbt_name'] = request.form['sbt_name']
            session['client_data']['sbt_description'] = request.form['sbt_description']
            session['client_data']['sbt_display_uri'] = request.form['sbt_display_uri']
            session['client_data']['sbt_artifact_uri'] = request.form['sbt_display_uri']
            session['client_data']['sbt_thumbnail_uri'] = request.form['sbt_thumbnail_uri']
            session['client_data']['sbt_network'] = request.form['sbt_network']

            session['client_data']['beacon_payload_message'] = request.form['beacon_payload_message']
            session['client_data']['contact_name'] = request.form['contact_name']
            session['client_data']['standalone'] = request.form.get('standalone') 
            session['client_data']['user'] = request.form['user']
            session['client_data']['webhook'] = request.form['webhook']
            session['client_data']['card_title'] = request.form['card_title']
            session['client_data']['card_subtitle'] = request.form['card_subtitle']
            session['client_data']['card_description'] = request.form['card_description']
            session['client_data']['note'] = request.form['note']          
            session['client_data']['contact_email'] = request.form['contact_email']
            #session['client_data']['landing_page_url'] = request.form['landing_page_url']
            session['client_data']['client_id'] =  request.form['client_id']
            session['client_data']['company_name'] = request.form['company_name']
            session['client_data']['application_name'] = request.form['application_name']
            session['client_data']['reason'] = request.form['reason']
            session['client_data']['reason_2'] = request.form.get('reason_2', "")
            session['client_data']['reason_3'] = request.form.get('reason_3', "")
            session['client_data']['reason_4'] = request.form.get('reason_4', "")
            session['client_data']['credential_requested'] = request.form['credential_requested']
            session['client_data']['credential_requested_2'] = request.form['credential_requested_2']
            session['client_data']['credential_requested_3'] = request.form['credential_requested_3']
            session['client_data']['credential_requested_4'] = request.form['credential_requested_4']
            session['client_data']['credential_to_issue'] = request.form['credential_to_issue']
            session['client_data']['credential_duration'] = request.form['credential_duration']
            session['client_data']['card_background_color'] = request.form['card_background_color']      
            session['client_data']['card_text_color'] = request.form['card_text_color']    
            session['client_data']['tezid_network'] = request.form['tezid_network']   
            session['client_data']['tezid_proof_type'] = request.form['tezid_proof_type']             
              
            if request.form['button'] == "qrcode" :
                return redirect ('/sandbox/op/beacon/console/qrcode')

            if request.form['button'] == "activity" :
                return redirect ('/sandbox/op/beacon/console/activity')
            
            if request.form['button'] == "advanced" :
                return redirect ('/sandbox/op/beacon/console/advanced')
            
            if request.form['button'] == "update" :
                db_api.update_beacon(request.form['client_id'], json.dumps(session['client_data']))
                return redirect('/sandbox/op/beacon/console?client_id=' + request.form['client_id'])

            if request.form['button'] == "copy" :
                new_client_id=  db_api.create_beacon(mode,  user=session['login_name'])
                new_data = copy.deepcopy(session['client_data'])
                new_data['application_name'] = new_data['application_name'] + ' (copie)'
                new_data['client_id'] = new_client_id
                new_data['user'] = session['login_name']
                db_api.update_beacon(new_client_id, json.dumps(new_data))
                return redirect('/sandbox/op/beacon/console?client_id=' + new_client_id)
            
            logging.error("error button %s", request.form['button'])
            return(jsonify('ok'))


async def beacon_advanced() :
    global  reason
    if not session.get('is_connected') or not session.get('login_name') :
        return redirect('/sandbox/saas4ssi')
    if request.method == 'GET' :
        session['client_data'] = json.loads(db_api.read_beacon(session['client_id']))
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
        return render_template('beacon/beacon_issuer_advanced.html',
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
            return redirect('/sandbox/op/beacon/console?client_id=' + request.form['client_id'])

        if request.form['button'] == "update" :
            session['client_data']['protocol'] = request.form['protocol']
            session['client_data']['method'] = request.form['method']

            if  session['client_data']['method'] == "relay" :
                db_api.update_beacon( request.form['client_id'], json.dumps(session['client_data']))
                return redirect('/sandbox/op/beacon/console/advanced')

            if request.form['method'] != "ebsi" :
                try :
                    didkit.key_to_did(request.form['method'], session['client_data']['jwk'])
                except :
                    logging.error('wrong key/method')
                    return redirect('/sandbox/op/beacon/console/advanced')

            jwk_dict = json.loads(session['client_data']['jwk'])
            if request.form['method'] in ['key', "ebsi"] :
                jwk_dict['alg'] = "ES256K"
            else : 
                jwk_dict['alg'] = "ES256K-R"
            session['client_data']['jwk'] = json.dumps(jwk_dict)
            if request.form['method'] == "ebsi" and  request.form['did_ebsi'] != "Not applicable" :
                session['client_data']['did_ebsi'] = request.form['did_ebsi']
            db_api.update_beacon( request.form['client_id'], json.dumps(session['client_data']))
            return redirect('/sandbox/op/beacon/console/advanced')


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
    def char2Bytes(text): 
        return text.encode('utf-8').hex()
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

