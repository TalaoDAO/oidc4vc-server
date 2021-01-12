
import os
import time
from flask import request, session, url_for, Response, abort, flash
from flask import render_template, redirect, jsonify
from werkzeug.security import gen_salt
from authlib.integrations.flask_oauth2 import current_token, client_authenticated
from authlib.oauth2 import OAuth2Error, OAuth2Request
from models import db, User, OAuth2Client
from oauth2 import authorization, require_oauth
import json
from urllib.parse import urlencode, parse_qs, urlparse
import random
import sms
from datetime import datetime, timedelta

import ns
import constante
from protocol import read_profil, contractsToOwners, add_key, partnershiprequest, authorize_partnership, get_category, ownersToContracts
from protocol import save_image, has_key_purpose, Document, get_image, is_partner, get_partner_status, Claim, Identity
import createidentity
import createcompany
import privatekey
import Talao_message

# Resolver pour l acces a un did. Cela retourne un debut de DID Document....
#@route('/resolver')
def resolver(mode):
    if 'method' not in session :
        session['method'] = request.method
    if request.method == 'GET' and not request.args.get('username') :
        return render_template('resolver.html', output="")
    elif request.method == 'GET' :
        input = request.args.get('username')
    else :
        input = json.loads(request.data.decode("utf-8"))['input']
    try :
        if input[:3] == 'did' :
            did = input
            workspace_contract = '0x' + input.split(':')[3]
            username = ns.get_username_from_resolver(workspace_contract, mode)
        else :
            username = input.lower()
            workspace_contract = ns.get_data_from_username(username, mode).get('workspace_contract')
            did = 'did:talao:'+ mode.BLOCKCHAIN + ':' + workspace_contract[2:]
    except :
        print('Error : wrong input')
        output =  "Username, workspace_contract or did not found"
        return render_template('resolver.html', output=output)

    address = contractsToOwners(workspace_contract, mode)
    contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
    rsa_public_key = contract.functions.identityInformation().call()[4]
    payload = {'blockchain' : mode.BLOCKCHAIN,
                     'username' : username,
                     'did' : did,
                     'address' : address,
                     'workspace contract' : workspace_contract,
                     'RSA public key' : rsa_public_key.decode('utf-8')}
    if session['method'] == 'GET' :
        del session['method']
        return render_template('resolver.html', output=json.dumps(payload, indent=4))
    else :
        del session['method']
        response = Response(json.dumps(payload), status=200, mimetype='application/json')
        return response

def send_secret_code (username, code, mode) :
    data = ns.get_data_from_username(username, mode)
    if data == dict() :
        return None
    if not data['phone'] :
        subject = 'Talao : Email authentification  '
        Talao_message.messageHTML(subject, data['email'], 'code_auth', {'code' : code}, mode)
        print('Warning : code sent by email')
        return 'email'
    else :
        print('Warning : code sent by sms')
        sms.send_code(data['phone'], code, mode)
    return 'sms'

def check_login() :
    #check if the user is correctly logged. This function is called everytime a user function is called
    if not session.get('username') :
        print('Warning : call abort 403')
        abort(403)
    else :
        return session['username']

def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None

def split_by_crlf(s):
    return [v for v in s.splitlines() if v]

def get_client_workspace(client_id, mode) :
    client = OAuth2Client.query.filter_by(client_id=client_id).first()
    client_username = json.loads(client._client_metadata)['client_name']
    return ns.get_data_from_username(client_username, mode).get('workspace_contract')

def get_user_workspace(user_id, mode):
    user = User.query.get(user_id)
    user_username = user.username
    return  ns.get_data_from_username(user_username, mode).get('workspace_contract')

#@route('/api/v1', methods=('GET', 'POST'))
"""
This function is called from the Talao identity to create the API credentials of a client
"""
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session['id'] = user.id
        # if user is not just to log in, but need to head back to the auth page, then go for it
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect('/api/v1')
    user = current_user()
    if user:
        clients = OAuth2Client.query.filter_by(user_id=user.id).all()
    else:
        clients = []
    return render_template('/oauth/home.html', user=user, clients=clients)

#@route('/api/v1/oauth_logout')
def oauth_logout():
    post_logout = request.args.get('post_logout_redirect_uri')
    session.clear()
    print('Warning : logout ID provider')
    return redirect(post_logout)

#@route('/api/v1/oauth_login')
def oauth_login(mode):
    """ login of the Identity provider """
    # Inital call from /authorization
    if request.method == 'GET' :
        if request.args.get('mobile') == 'on' :
             return render_template('/oauth/oauth_login_mobile.html')
        #session['remember_me'] = 'on'
        session['url'] = request.args.get('next')
        return render_template('/oauth/oauth_login_qrcode.html')


# walletconnect login
#@app.route('/oauth_wc_login/', methods = ['GET', 'POST'])
def oauth_wc_login(mode) :
    if request.method == 'GET' :
        # call from JS, QRmodal rejected by user
        if request.args.get('value') == 'undefined' :
            return redirect (mode.server + 'api/v1/oauth_login')
        # init first call
        session['wc_address'] = True
        return render_template('/oauth/oauth_wc_confirm.html')
    if request.method == 'POST' :
        print('request = ', request.__dict__)
        print('address = ', request.form['address'])
        if not session['wc_address'] :
            return render_template('/oauth/oauth_login_qrcode.html')
        myaddress = request.form['address']
        if not myaddress :
          	return render_template('/oauth/oauth_login_qrcode.html')
        # web3.py needs checksum addresses
        myaddress = mode.w3.toChecksumAddress(request.form['address'])

        # reverse for demo with crypto wallet
        if myaddress == "0x9B05084b8D19404f1689e69F40114990b562fa87" :
            session['username'] = 'thierrythevenet'
        if myaddress == "0x87E127664Bbdb45483517814051229a4484a66B1" :
            session['username'] = 'nicolasmuller'
        else :
            workspace_contract = ownersToContracts(myaddress, mode)
            if not workspace_contract :
                session['wc_address'] = False
                return render_template('/oauth/oauth_wc_reject.html')
            session['username'] = ns.get_username_from_resolver(workspace_contract, mode)
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            user = User(username=session['username'])
            db.session.add(user)
            db.session.commit()
        session['id'] = user.id
        del session['username']
        print('Warning : user is logged in Talao')
        print(' session de url = ', session['url'])
        return redirect(session['url'])


#@route('/api/v1/create_client', methods=('GET', 'POST'))
""" gestion minimaliste des grants client qui sont dans la base db.sqlite
cette fonction est appellée par Talao identity 
"""
def create_client():
    check_login()
    user = current_user()
    if not user:
        return redirect('/api/v1')
    if request.method == 'GET':
        return render_template('/oauth/create_client.html')
    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=user.id,
    )
    form = request.form
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"]
    }
    client.set_client_metadata(client_metadata)
    if form['token_endpoint_auth_method'] == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)
    db.session.add(client)
    db.session.commit()
    return redirect('/api/v1')

#@route('/oauth/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response('revocation')

#@route('/api/v1/oauth/token', methods=['POST'])
def issue_token():
    response = authorization.create_token_response()
    return response

# AUTHORIZATION CODE
#@route('/api/v1/authorize', methods=['GET', 'POST'])
def authorize(mode):
    user = current_user()
    client_id = request.args['client_id']
    client = OAuth2Client.query.filter_by(client_id=client_id).first()
    client_username = json.loads(client._client_metadata)['client_name']
    client_workspace_contract = ns.get_data_from_username(client_username, mode).get('workspace_contract')
    profil,category = read_profil(client_workspace_contract, mode, 'light)')
    client_name = profil['name']
    # if user log status is not true (Auth server), then to log it in
    if not user :
        return redirect(url_for('oauth_login', next=request.url, client_name=client_name))
    # if user is already logged we prepare the consent screen
    if request.method == 'GET':
        try:
            grant = authorization.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            return error.error
        # configure consent screen : oauth_authorize.html
        consent_screen_scopes = ['openid', 'user:manage:referent', 'user:manage:partner', 'user:manage:certificate', 'user:manage:data']
        user_workspace_contract = ns.get_data_from_username(user.username, mode)['workspace_contract']
        category = get_category(user_workspace_contract, mode)
        if category == 1001 : # person
            consent_screen_scopes.extend(['address', 'profile', 'about', 'birthdate', 'resume', 'proof_of_identity', 'email', 'phone'])
        checkbox = {key.replace(':', '_') : 'checked' if key in grant.request.scope and key in client.scope.split() else ""  for key in consent_screen_scopes}
        # Display view to ask for user consent if scope is more than just openid
        return render_template('/oauth/oauth_authorize.html', user=user, grant=grant,client_name=client_name, **checkbox)
    # POST, call from consent screen
    print('request form = ', request.form)
    if not user and 'username' in request.form:
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
    if 'reject' in request.form :
        return authorization.create_authorization_response(grant_user=None)
    # update scopes after user consent
    query_dict = parse_qs(request.query_string.decode("utf-8"))
    my_scope = ""
    for scope in query_dict['scope'][0].split() :
        if request.form.get(scope) :
            my_scope = my_scope + scope + " "
    query_dict["scope"] = [my_scope[:-1]]
    # we setup a custom Oauth2Request as we have changed the scope in the query_dict
    req = OAuth2Request("POST", request.base_url + "?" + urlencode(query_dict, doseq=True))
    #if not session['remember_me'] :
    #    pass
    #    #session.clear()
    return authorization.create_authorization_response(grant_user=user, request=req)


#########################################  AUTHORIZATION CODE ENDPOINT   ################################

# endpoint standard OIDC
#route('/api/v1/user_info')
@require_oauth('address openid profile resume email birthdate proof_of_identity about resume gender name contact_phone website', 'OR')
def user_info(mode):
    user_id = current_token.user_id
    user_workspace_contract = get_user_workspace(user_id,mode)
    user_info = dict()
    profile, category = read_profil(user_workspace_contract, mode, 'full')
    user_info['sub'] = 'did:talao:' + mode.BLOCKCHAIN +':' + user_workspace_contract[2:]
    print('Warning : token scope received = ', current_token.scope)
    if 'proof_of_identity' in current_token.scope :
        user_info['proof_of_identity'] = 'Not implemented yet'

    if category == 1001 : # person
        if 'profile' in current_token.scope :
            user_info['given_name'] = profile.get('firstname')
            user_info['family_name'] = profile.get('lastname')
            user_info['gender'] = profile.get('gender')
        for scope in ['email', 'phone', 'birthdate', 'about'] :
            if scope in current_token.scope :
                user_info[scope] = profile.get(scope) if profile.get(scope) != 'private' else None
        if 'resume' in current_token.scope :
            user = Identity(user_workspace_contract, mode, authenticated=False)
            # clean up for resume
            user_dict = user.__dict__.copy()
            #del user_dict['aes']
            #del user_dict['rsa_key_value']
            #del user_dict['private_key_value']
            #del user_dict['secret']
            #del user_dict['partners']
            user_info['resume'] = user_dict
        if 'address' in current_token.scope :
            user_info['address'] = profile.get('postal_address') if profile.get('postal_address') != 'private' else None
    if category == 2001 : # company
        print('Error : OIDC request for company')
    # setup response
    response = Response(json.dumps(user_info), status=200, mimetype='application/json')
    return response


#route('/api/v1/user_accepts_company_referent')
@require_oauth('user:manage:referent')
def user_accepts_company_referent(mode):
    user_id = current_token.user_id
    user_workspace_contract = get_user_workspace(user_id,mode)
    user_address = contractsToOwners(user_workspace_contract, mode)
    client_id = current_token.client_id
    client_workspace_contract = get_client_workspace(client_id, mode)
    client_address = contractsToOwners(client_workspace_contract, mode)
    # add key 20002
    if not has_key_purpose(user_workspace_contract, client_address, 20002, mode) :
        relay_private_key = privatekey.get_key(mode.relay_address,'private_key', mode)
        if not add_key(mode.relay_address, mode.relay_workspace_contract, user_address, user_workspace_contract, relay_private_key, client_address, 20002 , mode, synchronous=False) :
            referent = False
        else :
            referent = True
    else :
        referent = True
    response = Response(json.dumps({'referent' : referent}), status=200, mimetype='application/json')
    return response


#route('/api/v1/user_adds_referent')
@require_oauth('user:manage:referent')
def user_adds_referent(mode):
    user_id = current_token.user_id
    user_workspace_contract = get_user_workspace(user_id,mode)
    user_address = contractsToOwners(user_workspace_contract, mode)
    data = json.loads(request.data.decode("utf-8"))
    try :
        referent_workspace_contract = '0x' + data['did_referent'].split(':')[3]
        referent_address = contractsToOwners(referent_workspace_contract, mode)
    except :
        response_dict = {'detail' : 'did_referent or request malformed '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    # add key 20002
    if not has_key_purpose(user_workspace_contract, referent_address, 20002, mode) :
        relay_private_key = privatekey.get_key(mode.relay_address,'private_key', mode)
        if not add_key(mode.relay_address, mode.relay_workspace_contract, user_address, user_workspace_contract, relay_private_key, referent_address, 20002 , mode, synchronous=False) :
            referent = False
        else :
            referent = True
    else :
        referent = True
    response = Response(json.dumps({'referent' : referent}), status=200, mimetype='application/json')
    return response


#route('/api/v1/user_accepts_company_partnership')
@require_oauth('user:manage:partner')
def user_accepts_company_partnership(mode):
    user_id = current_token.user_id
    user_workspace_contract = get_user_workspace(user_id,mode)
    user_address = contractsToOwners(user_workspace_contract, mode)
    client_id = current_token.client_id
    client_workspace_contract = get_client_workspace(client_id, mode)
    client_address = contractsToOwners(client_workspace_contract, mode)

    # client requests partnership to user
    if not is_partner(user_address, client_workspace_contract, mode) :
        client_address = contractsToOwners(client_workspace_contract, mode)
        relay_private_key = privatekey.get_key(mode.relay_address,'private_key', mode)
        client_rsa_key = privatekey.get_key(client_address,'rsa_key', mode)
        partnershiprequest(mode.relay_address, mode.relay_workspace_contract, client_address, client_workspace_contract, relay_private_key, user_workspace_contract, client_rsa_key, mode, synchronous=False)

    # user accepts client request for partnership if not already partner
    if not is_partner(client_address, user_workspace_contract,mode) :
        relay_private_key = privatekey.get_key(mode.relay_address,'private_key', mode)
        user_rsa_key = privatekey.get_key(user_address, 'rsa_key', mode)
        authorize_partnership(mode.relay_address, mode.relay_workspace_contract, user_address, user_workspace_contract, relay_private_key, client_workspace_contract, user_rsa_key, mode, synchronous=True)

    partnership_in_identity,partnership_in_partner  = get_partner_status(user_address, client_workspace_contract,mode)
    # setup response
    response = Response(json.dumps({'partnership_in_identity' : partnership_in_identity, 'partnership_in_partner' : partnership_in_partner}), status=200, mimetype='application/json')
    return response

#route('/api/v1/user_uploads_signature')
@require_oauth('user:manage:data')
def user_uploads_signature(mode):
    user_id = current_token.user_id
    user_workspace_contract = get_user_workspace(user_id,mode)
    user_address = contractsToOwners(user_workspace_contract, mode)
    try :
        signature_file = request.files['image']
    except :
        response_dict = {'detail' : 'Image file not found or incorrect.'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    # Read the image via file.stream
    filename = "api_signature"
    signature_file.save(os.path.join(mode.uploads_path, filename))
    picturefile = mode.uploads_path  + filename
    image_hash = save_image(mode.relay_address,
                            mode.relay_workspace_contract,
                            user_address,
                            user_workspace_contract,
                            mode.relay_private_key,
                            picturefile,
                            'signature',
                            mode,
                            synchronous = False)
    if not image_hash :
        response_dict = {'detail' : 'Transaction failed'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    response = Response(json.dumps({'hash' : image_hash}), status=200, mimetype='application/json')
    return response

#route('/api/v1/user_uploads_logo')
@require_oauth('user:manage:data')
def user_uploads_picture(mode):
    user_id = current_token.user_id
    user_workspace_contract = get_user_workspace(user_id,mode)
    user_address = contractsToOwners(user_workspace_contract, mode)
    try :
        signature_file = request.files['image']
    except :
        response_dict = {'detail' : 'Image file not found or incorrect.'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    # Read the image via file.stream
    filename = "api_picture"
    signature_file.save(os.path.join(mode.uploads_path, filename))
    picturefile = mode.uploads_path  + filename
    image_hash = save_image(mode.relay_address,
                            mode.relay_workspace_contract,
                            user_address,
                            user_workspace_contract,
                            mode.relay_private_key,
                            picturefile,
                            'picture',
                            mode,
                            synchronous = False)
    if not image_hash :
        response_dict = {'detail' : 'Transaction failed.'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    response = Response(json.dumps({'hash' : image_hash}), status=200, mimetype='application/json')
    return response

#route('/api/v1/user_updates_company_settings')
@require_oauth('user:manage:data')
def user_updates_company_settings(mode):
    user_id = current_token.user_id
    user_workspace_contract = get_user_workspace(user_id,mode)
    data = json.loads(request.data.decode("utf-8"))
    profil, category = read_profil(user_workspace_contract, mode, 'full')
    if category == 1001 :
        response_dict = {'detail' : 'Only company Identity allowed.'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    company_settings = ['name','contact_name','contact_email','contact_phone','website', 'about', 'staff', 'mother_company', 'sales', 'siren', 'postal_address']
    for setting in company_settings :
        if data.get(setting) and data.get(setting) != profil[setting] :
            if Claim().relay_add(user_workspace_contract,setting, data.get(setting), 'public', mode)[0] :
                profil[setting] = data.get(setting)
            else :
                print('Error : user_updates_company_settings transaction failed")')
    # setup response
    response = Response(json.dumps(profil), status=200, mimetype='application/json')
    return response


# issue a certificates on behalf of user(user=issued_by)
#@route('/api/v1/user_issues_certificate')
@require_oauth('user:manage:certificate')
def user_issues_certificate(mode):
    user_id = current_token.user_id
    issued_by_workspace_contract = get_user_workspace(user_id,mode)
    issued_by_address = contractsToOwners(issued_by_workspace_contract, mode)
    data = json.loads(request.data.decode("utf-8"))
    certificate = data['certificate']
    try :
        issued_to_workspace_contract = '0x' + data['did_issued_to'].split(':')[3]
        issued_to_address = contractsToOwners(issued_to_workspace_contract, mode)
        issued_by_private_key = privatekey.get_key(issued_by_address,'private_key', mode)
    except :
        response_dict = {'detail' : 'did or request malformed '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    if not issued_to_address or not issued_by_address :
        response_dict = {'detail' : 'did does not exist'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    if data['certificate_type'] not in ['reference', 'agreement', 'experience', 'skill', 'recommendation' ] :
        response_dict = {'detail' : 'This type of certificate cannot be issued'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    issued_to_profil, issued_to_category = read_profil(issued_to_workspace_contract, mode, 'full')
    issued_by_profil, issued_by_category = read_profil(issued_by_workspace_contract, mode, 'full')
    certificate['type'] = data['certificate_type']
    certificate['version'] = 1

    if issued_by_category == 1001 : # person
        certificate["issued_by"]  = {
		    "firstname" : issued_by_profil['firstname'],
            "lastname" : issued_by_profil['lastname'],
		    "postal_address" : issued_by_profil['postal_address'],
		    "picture" : get_image(issued_by_workspace_contract, 'picture', mode),
		    "signature" : get_image(issued_by_workspace_contract, 'signature', mode),
		    }
    else : # company
        certificate["issued_by"]  = {
		    "name" : issued_by_profil['name'],
		    "postal_address" : issued_by_profil['postal_address'],
		    "siren" : issued_by_profil['siren'],
		    "logo" :get_image(issued_by_workspace_contract, 'logo', mode),
		    "signature" : get_image(issued_by_workspace_contract, 'signature', mode),
            "manager" : "Director",
		    }
    if issued_to_category == 2001 : # company
        certificate["issued_to"]  = {
		    "name" : issued_to_profil['name'],
		    "postal_address" : issued_to_profil['postal_address'],
		    "siren" : issued_to_profil['siren'],
		    "logo" : get_image(issued_to_workspace_contract, 'logo', mode),
		    "signature" : get_image(issued_to_workspace_contract, 'signature', mode),
		    }
    else :# person
         certificate["issued_to"]  = {
		    "firstname" : issued_to_profil['firstname'],
            "lastname" : issued_to_profil['lastname'],
		    "postal_address" : issued_to_profil['postal_address'],
		    "picture" : get_image(issued_to_workspace_contract, 'picture', mode),
		    "signature" : get_image(issued_to_workspace_contract, 'signature', mode),
		    }
    my_certificate = Document('certificate')
    document_id, ipfs_hash, transaction_hash = my_certificate.add(issued_by_address,
                        issued_by_workspace_contract,
                        issued_to_address,
                        issued_to_workspace_contract,
                        issued_by_private_key,
                        certificate,
                        mode,
                        mydays=0,
                        privacy='public')
    if not document_id :
        response_dict = {'detail' : 'transaction failed, check if companies have correct referent status'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    response_dict = {'link' : mode.server + 'certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + issued_by_workspace_contract[2:] + ':document:' + str(document_id),
                      **certificate, 'ipfs hash' : ipfs_hash, 'transaction hash' : transaction_hash}
    response = Response(json.dumps(response_dict), status=200, mimetype='application/json')
    return response

############################################ CLIENT CREDENTIAL ENDPOINT ######################################################################

# create a person identity with a key2002 key and partnership
#@route('/api/v1/create_person_identity')
@require_oauth('client:create:identity') #scope
def oauth_create_person_identity(mode):
    # creation d'une identité"
    client_id = current_token.client_id
    client_workspace_contract = get_client_workspace(client_id, mode)
    data = json.loads(request.data.decode("utf-8"))
    if not data.get('email') or not data.get('firstname') or not data.get('lastname') :
        response_dict = {'detail' : 'request malformed'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    creator = None if not client_workspace_contract else contractsToOwners(client_workspace_contract, mode)
    identity_username = ns.build_username(data.get('firstname'), data.get('lastname'), mode)
    send_email = data.get('send_email', True)
    try :
        identity_workspace_contract = createidentity.create_user(identity_username, data.get('email'), mode, creator=creator, partner=True, send_email=send_email)[2]
    except :
        response_dict = {'detail' : 'Blockchain failure, contact Talao support '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    # createidentity other problems
    if not identity_workspace_contract :
        response_dict = {'detail' : 'Create Identity failure, contact Talao support '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    response_dict = {'did' : 'did:talao:' + mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:], 'username' : identity_username,}
    response = Response(json.dumps(response_dict), status=200, mimetype='application/json')
    return response

# create a company identity with key20002 and partnership
#@route('/api/v1/create_company_identity')
@require_oauth('client:create:identity')
def oauth_create_company_identity(mode):
    # creation d'une identité"
    client_id = current_token.client_id
    client_workspace_contract = get_client_workspace(client_id, mode)
    data = json.loads(request.data.decode("utf-8"))
    if not data.get('email') or not data.get('name') :
        response_dict = {'detail' : 'request malformed'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    creator = None if not client_workspace_contract else contractsToOwners(client_workspace_contract, mode)
    identity_username = data.get('name').lower()
    send_email = data.get('send_email', True)
    if ns.username_exist(identity_username, mode)   :
        identity_username = identity_username + str(random.randint(1, 100))
    try :
        identity_workspace_contract = createcompany.create_company(data['email'], identity_username, mode, creator=creator, partner=True, send_email=send_email)[2]
    except :
        response_dict = {'detail' : 'Blockchain failure, contact Talao support '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    # createidentity other problems
    if not identity_workspace_contract :
        response_dict = {'detail' : 'Create Identity failure, contact Talao support '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    response_dict = {'did' : 'did:talao:' + mode.BLOCKCHAIN + ':' + identity_workspace_contract[2:], 'username' : identity_username,}
    response = Response(json.dumps(response_dict), status=200, mimetype='application/json')
    return response


# get status
#@route('/api/v1/get_status')
@require_oauth(None)
def oauth_get_status(mode):
    client_id=current_token.client_id
    client_workspace_contract = get_client_workspace(client_id, mode)
    client_address = contractsToOwners(client_workspace_contract, mode)
    data = json.loads(request.data.decode("utf-8"))
    try :
        user_workspace_contract = '0x' + data['did'].split(':')[3]
        user_address = contractsToOwners(user_workspace_contract, mode)
        referent = has_key_purpose(user_workspace_contract, client_address, 20002, mode)
        partnership_in_identity,partnership_in_partner  = get_partner_status(user_address, client_workspace_contract,mode)
    except :
        response_dict = {'detail' : 'did or request malformed '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    response_dict = {'partnernship_in_identity' : partnership_in_identity , 'partnership_in_partner_identity' : partnership_in_partner, 'referent' : referent}
    response = Response(json.dumps(response_dict), status=200, mimetype='application/json')
    return response


# company issues experience certificates to user
#@route('/api/v1/issue_experience')
@require_oauth('client:issue:experience')
def oauth_issue_experience(mode):
    client_id=current_token.client_id
    client_workspace_contract = get_client_workspace(client_id, mode)
    client_address = contractsToOwners(client_workspace_contract, mode)
    client_private_key = privatekey.get_key(client_address,'private_key', mode)
    data = json.loads(request.data.decode("utf-8"))
    try :
        user_workspace_contract = '0x' + data['did'].split(':')[3]
        user_address = contractsToOwners(user_workspace_contract, mode)
        certificate = data['certificate']
    except :
        response_dict = {'detail' : 'did or request malformed '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    if user_address is None :
        response_dict = {'detail' : 'did does not exist'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    if not has_key_purpose(user_workspace_contract, client_address, 20002, mode) :
        response_dict = {'detail' : 'Your company is not in the user referent list'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    certificate['type'] = 'experience'
    certificate['version'] = 1
    certificate['logo'] = get_image(client_workspace_contract, 'logo', mode)
    certificate['signature'] = get_image(client_workspace_contract, 'signature', mode)
    certificate['manager'] = 'Director'
    certificate['reviewer'] = ''
    my_certificate = Document('certificate')
    document_id, ipfs_hash, transaction_hash = my_certificate.add(client_address,
                        client_workspace_contract,
                        user_address,
                        user_workspace_contract,
                        client_private_key,
                        certificate,
                        mode,
                        mydays=0,
                        privacy='public')
    if not document_id :
        response_dict = {'detail' : 'transaction failed'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    response_dict = {'link' : mode.server + 'certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + user_workspace_contract[2:] + ':document:' + str(document_id),
                      **certificate, 'ipfs hash' : ipfs_hash, 'transaction hash' : transaction_hash}
    response = Response(json.dumps(response_dict), status=200, mimetype='application/json')
    return response


# issue an agrement certificates
#@route('/api/v1/issue_agreement')
@require_oauth('client:issue:agreement')
def oauth_issue_agreement(mode):
    client_id=current_token.client_id
    client_workspace_contract = get_client_workspace(client_id, mode)
    client_address = contractsToOwners(client_workspace_contract, mode)
    client_private_key = privatekey.get_key(client_address,'private_key', mode)
    data = json.loads(request.data.decode("utf-8"))
    try :
        user_workspace_contract = '0x' + data['did'].split(':')[3]
        user_address = contractsToOwners(user_workspace_contract, mode)
        certificate = data['certificate']
    except :
        response_dict = {'detail' : 'did or request malformed '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    if user_address is None :
        response_dict = {'detail' : 'did does not exist'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    if not has_key_purpose(user_workspace_contract, client_address, 20002, mode) :
        response_dict = {'detail' : 'Your company is not in the user referent list'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    user_profil = read_profil(user_workspace_contract, mode, 'full')[0]
    client_profil = read_profil(client_workspace_contract, mode, 'full')[0]
    certificate['type'] = 'agreement'
    certificate['version'] = 1
    certificate["issued_by"]  = {
		"name" : client_profil['name'],
		"postal_address" : client_profil['postal_address'],
		"siren" : client_profil['siren'],
		"logo" :get_image(client_workspace_contract, 'logo', mode),
		"signature" : get_image(client_workspace_contract, 'signature', mode),
        "manager" : "Director",
		}
    certificate["issued_to"]  = {
		"name" : user_profil['name'],
		"postal_address" : user_profil['postal_address'],
		"siren" : user_profil['siren'],
		"logo" : get_image(user_workspace_contract, 'logo', mode),
		"signature" : get_image(user_workspace_contract, 'signature', mode),
		}
    my_certificate = Document('certificate')
    document_id, ipfs_hash, transaction_hash = my_certificate.add(client_address,
                        client_workspace_contract,
                        user_address,
                        user_workspace_contract,
                        client_private_key,
                        certificate,
                        mode,
                        mydays=0,
                        privacy='public')
    if not document_id :
        response_dict = {'detail' : 'transaction failed'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    response_dict = {'link' : mode.server + 'certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + user_workspace_contract[2:] + ':document:' + str(document_id),
                      **certificate, 'ipfs hash' : ipfs_hash, 'transaction hash' : transaction_hash}
    response = Response(json.dumps(response_dict), status=200, mimetype='application/json')
    return response

# issue a reference certificates
#@route('/api/v1/issue_reference')
@require_oauth('client:issue:reference')
def oauth_issue_reference(mode):
    client_id=current_token.client_id
    client_workspace_contract = get_client_workspace(client_id, mode)
    client_address = contractsToOwners(client_workspace_contract, mode)
    client_private_key = privatekey.get_key(client_address,'private_key', mode)
    data = json.loads(request.data.decode("utf-8"))
    try :
        user_workspace_contract = '0x' + data['did'].split(':')[3]
        user_address = contractsToOwners(user_workspace_contract, mode)
        certificate = data['certificate']
    except :
        response_dict = {'detail' : 'did or request malformed '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    if user_address is None :
        response_dict = {'detail' : 'did does not exist'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    if not has_key_purpose(user_workspace_contract, client_address, 20002, mode) :
        response_dict = {'detail' : 'Your company is not in the user referent list'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    user_profil = read_profil(user_workspace_contract, mode, 'full')[0]
    client_profil = read_profil(client_workspace_contract, mode, 'full')[0]
    certificate['type'] = 'reference'
    certificate['version'] = 1
    certificate["issued_by"]  = {
		"name" : client_profil['name'],
		"postal_address" : client_profil['postal_address'],
		"siren" : client_profil['siren'],
		"logo" :get_image(client_workspace_contract, 'logo', mode),
		"signature" : get_image(client_workspace_contract, 'signature', mode),
        "manager" : "Director",
		}
    certificate["issued_to"]  = {
		"name" : user_profil['name'],
		"postal_address" : user_profil['postal_address'],
		"siren" : user_profil['siren'],
		"logo" : get_image(user_workspace_contract, 'logo', mode),
		"signature" : get_image(user_workspace_contract, 'signature', mode),
		}
    my_certificate = Document('certificate')
    document_id, ipfs_hash, transaction_hash = my_certificate.add(client_address,
                        client_workspace_contract,
                        user_address,
                        user_workspace_contract,
                        client_private_key,
                        certificate,
                        mode,
                        mydays=0,
                        privacy='public')
    if not document_id :
        response_dict = {'detail' : 'transaction failed'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    response_dict = {'link' : mode.server + 'certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + user_workspace_contract[2:] + ':document:' + str(document_id),
                      **certificate, 'ipfs hash' : ipfs_hash, 'transaction hash' : transaction_hash}
    response = Response(json.dumps(response_dict), status=200, mimetype='application/json')
    return response


# get a list of certificate
#@route('/api/v1/get_certificate_list')
@require_oauth(None)
def oauth_get_certificate_list(mode):
    client_id=current_token.client_id
    client_workspace_contract = get_client_workspace(client_id, mode)
    client_address = contractsToOwners(client_workspace_contract, mode)
    data = json.loads(request.data.decode("utf-8"))
    try :
        user_workspace_contract = '0x' + data['did'].split(':')[3]
        user_address = contractsToOwners(user_workspace_contract, mode)
        certificate_type = data['certificate_type']
    except :
        response_dict = {'detail' : 'did or request malformed '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    if user_address is None :
        response_dict = {'detail' : 'did does not exist'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    # check if client is in the partner list of identity
    if not is_partner(client_address, user_workspace_contract, mode):
        response_dict = {'detail' : 'Your company is not in the partner list of this Identity'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    contract = mode.w3.eth.contract(user_workspace_contract,abi = constante.workspace_ABI)
    certificate_list = list()
    for doc_id in contract.functions.getDocuments().call() :
        if contract.functions.getDocument(doc_id).call()[0] == 20000 :
            certificate = Document('certificate')
            if certificate.relay_get(user_workspace_contract, doc_id, mode, loading='light') :
                if certificate.type == certificate_type or certificate_type.lower() == 'all' :
                    certificate_list.append(data['did'] + ':document:' + str(doc_id))
    response_dict = {'certificate_list' : certificate_list}
    response = Response(json.dumps(response_dict), status=200, mimetype='application/json')
    return response


# get certificate data
#@route('/api/v1/get_certificate')
@require_oauth(None)
def oauth_get_certificate(mode):
    client_id=current_token.client_id
    client_workspace_contract = get_client_workspace(client_id, mode)
    client_address = contractsToOwners(client_workspace_contract, mode)
    data = json.loads(request.data.decode("utf-8"))
    try :
        user_workspace_contract = '0x' + data['certificate_id'].split(':')[3]
        user_address = contractsToOwners(user_workspace_contract, mode)
        doc_id =  int(data['certificate_id'].split(':')[5])
    except :
        response_dict = {'detail' : 'did or request malformed '}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    if user_address is None :
        response_dict = {'detail' : 'did does not exist'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    # check if client is in the partner list of identity
    if not is_partner(client_address, user_workspace_contract, mode):
        response_dict = {'detail' : 'Your company is not in the partner list of this Identity'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
        return response
    certificate = Document('certificate')
    if not certificate.relay_get(user_workspace_contract, doc_id, mode, loading='light') :
        response_dict = {'detail' : 'Certificate not found'}
        response = Response(json.dumps(response_dict), status=400, mimetype='application/json')
    else :
        response_dict = certificate.__dict__
    response = Response(json.dumps(response_dict), status=200, mimetype='application/json')
    return response
