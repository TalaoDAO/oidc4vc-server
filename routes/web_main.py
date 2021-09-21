
import os.path
import os
from flask import session, send_from_directory, flash, jsonify
from flask import request, redirect, render_template,abort
import random
import requests
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import copy
from eth_keys import keys
from eth_utils import decode_hex
from Crypto.PublicKey import RSA
import uuid
import logging
from flask_babel import _

logging.basicConfig(level=logging.INFO)
import didkit

from factory import createcompany, createidentity
from components import Talao_message, Talao_ipfs, ns, privatekey, QRCode, directory, sms, siren, talao_x509, company
from signaturesuite import helpers, vc_signature
import constante
from protocol import ownersToContracts, contractsToOwners,partnershiprequest, remove_partnership
from protocol import  authorize_partnership, reject_partnership, destroy_workspace
from protocol import delete_key, add_key
from protocol import File, Document

# Constants
FONTS_FOLDER='templates/assets/fonts'
RSA_FOLDER = './RSA_key/' 
PERSON_TOPIC = ['firstname','lastname', 'about', 'profil_title', 'birthdate', 'contact_email', 'contact_phone','postal_address', 'education']
COMPANY_TOPIC = ['name','contact_name','contact_email', 'contact_phone', 'website', 'about', 'staff', 'sales', 'mother_company', 'siren', 'postal_address']
CREDENTIAL_TOPIC = ['pass', 'experience', 'skill', 'training', 'recommendation', 'work',  'vacation', 'internship', 'relocation',  'hiring']


# Check if session is active and access is fine. To be used for all routes, excetp external call
def check_login() :
    if not session.get('workspace_contract') and not session.get('username') :
        logging.error('abort call')
        abort(403)
    else :
        return True

def getDID() :
    key = request.args['key']
    method = request.args['method']
    return jsonify (didkit.key_to_did(method, key))


def generate_identity(mode) :
    """ only for users
    """
    if request.method == 'GET' :
        return render_template('generate_identity.html', **session['menu'])
    if request.method == 'POST' :
        did = request.form['did']
        session['method'] = did.split(':')[1]
        ns.add_did(session['workspace_contract'], did, mode)
        ns.update_method(session['workspace_contract'], session['method'], mode)
        return render_template('generate_identity_password.html', **session['menu'], did=did)


def presentation(mode) :
    """ make a presentation 
    @route /user/presenttaion/
    """
    if request.method == 'GET' :
        if not session['all_certificate'] :
            lign = """<a class="text-info">No Credential available</a>"""
        else :
            template =''
            for counter, certificate in enumerate(session['all_certificate'],0) :
                # Display raw verifiable credential
                doc_id = certificate['id'].split(':')[5]
                credential = Document('certificate')
                credential.relay_get_credential(session['workspace_contract'], int(doc_id), mode)
                credential_text = json.dumps(credential.__dict__, indent=4, ensure_ascii=False)
                try :
                    lign = """<div class="form-row">
                        <div class="col">
                            <div class="form-group form-check">
                                <input type="checkbox" class="form-check-input" value='"""+ doc_id +"""' name='""" + str(counter) + """' >
                                <label><b>id</b> : """ + credential.__dict__['id'] + """</label>
                                <b>Credential Type</b> : """ + credential.__dict__['credentialSubject']['credentialCategory'].capitalize()+ """  <b>Privacy</b> : """ +certificate['privacy'].capitalize() + """<br>
                                <div> <textarea  readonly class="form-control" rows="5">""" + credential_text + """</textarea></div>
                                </div>
                            </div>
                        </div>"""
                except :
                    lign = """<hr>
                    <b>#</b> : """ + str(counter) + "<br>"
                template += lign
                session['counter'] = str(counter)

        return render_template('presentation.html', **session['menu'], template=template)

    if request.method == 'POST' :
        vc_list = list()
        for counter in range(0,int(session['counter'])+1) :
            if request.form.get(str(counter)) :
                credential = Document('certificate')
                credential.relay_get_credential(session['workspace_contract'], int(request.form[str(counter)]), mode)
                vc_list.append(credential.__dict__)
        if not vc_list :
            flash(_("No credential selected"), "warning")
            return redirect(mode.server + 'user/presentation/')
        did = ns.get_did(session['workspace_contract'], mode)
        presentation = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "id": "data:" + str(uuid.uuid1()),
            "type": ["VerifiablePresentation"],
            "holder":  did,
            "verifiableCredential": vc_list
            }
        return render_template('sign_presentation.html', **session['menu'],
                                did=did,
                                presentation=json.dumps(presentation),
                                presentation_displayed=json.dumps(presentation, ensure_ascii= False, indent=4))


# helper
def is_username_in_list(my_list, username) :
    if not username :
        return False
    for user in my_list :
        if user['username'] == username :
            return True
    return False


# helper
def is_username_in_list_for_partnership(partner_list, username) :
    if not username :
        return False
    for partner in partner_list :
        if partner['username'] == username and partner['authorized'] not in ['Removed',"Unknown", "Rejected"]:
            return True
    return False


#HomePage
#@app.route('/homepage/', methods=['GET'])
def homepage() :
    check_login()
    if request.method == 'GET' :
        return render_template('homepage.html', **session['menu'])


def translate_credentials() :
	return {'pass_txt' : _('Identiy pass'),
		'experience_txt' : _('Experience credential'),
		'skill_txt' : _('Skill certificate'),
		'training_txt' : _('Training certificate'),
		'recommendation_txt' : _('Recomendation letter'),
		'work_txt' : _('Employer certificate'),
		'vacation_txt' : _('Employee vacation time certificate'),
		'internship_txt' : _('Certificate of participation'),
		'relocation_txt' : _('Transfer certificate'),
		'end_of_work_txt' :_('Labour certificate'),
		'hiring_txt' : _('Promise to hire letter')}


#@app.route('/company/add_credential_supported/', methods=['GET', 'POST'])
def add_credential_supported(mode) :
    check_login()
    if request.method == 'GET' :
        personal = ns.get_personal(session['workspace_contract'], mode)
        credentials_supported = json.loads(personal).get('credentials_supported',[])
        checkbox = dict()
        credentials = translate_credentials()
        for topic in CREDENTIAL_TOPIC :
            checkbox['box_' + topic] = "checked" if topic in credentials_supported else ""
        return render_template('add_credential_supported.html', **session['menu'], **checkbox, **credentials )
    if request.method == 'POST' :
        credentials_supported = list()
        for topic in  CREDENTIAL_TOPIC :
            if request.form.get(str(topic)) :
                credentials_supported.append(request.form.get(str(topic)))
        personal = json.loads(ns.get_personal(session['workspace_contract'], mode))
        personal['credentials_supported'] = credentials_supported
        ns.update_personal(session['workspace_contract'], json.dumps(personal), mode)
        return redirect(mode.server + 'user/')


#@app.route('/verifier/', methods=['GET'])
def verifier() :
    check_login()
    if request.method == 'GET' :
        return render_template('verifier.html', **session['menu'])
    if request.method == 'POST' :
        data = request.get_json()
        try :
            credential = json.loads(data['credential']) # dict
        except :
            return jsonify(_("Credential is not a JSON-LD."))

        # lookup DID Document
        if credential['issuer'].split(':')[1]  == 'tz' :
            # did:tz has no driver for Universal resolver
            DID_Document = json.loads(didkit.resolve_did(credential['issuer'],'{}'))
        else :
            try :
                r = requests.get('https://dev.uniresolver.io/1.0/identifiers/' + credential['issuer'])
            except :
                return jsonify(_("Network connexion problem."))
            if r.status_code == 200 :
                DID_Document = r.json()['didDocument']
            else :
                return jsonify(_("Unknown issuer DID."))

        # lookup Domain list of the service linkedDomains endpoint
        service_list = DID_Document.get('service', [])
        domain_list = list()
        for service in service_list :
            if service['type'] == 'LinkedDomains' :
                domain_list = service['serviceEndpoint']
        if not domain_list :
            return jsonify(vc_signature.verify(data['credential']) + _("No issuer credential has been found (No LinkedDomains service Endpoint)."))
        if isinstance(domain_list, str) :
            domain_list = domain_list.split()

        # lookup issuer dids with  '.well-known/did-configuration.json'
        breakloop = False
        message = _(" No issuer credential has been found.")
        for domain in domain_list :
            r = requests.get(domain + '/.well-known/did-configuration.json')
            if r.status_code == 200 :
                did_configuration = r.json()
                linked_did_list = did_configuration['linked_dids'] 
                for linked_did in linked_did_list :
                    if linked_did['proof']['verificationMethod'] == credential['proof']['verificationMethod'] :
                        result = didkit.verify_credential(json.dumps(linked_did), '{}')
                        if not json.loads(result)['errors'] :
                            message = " This Issuer owns the domain  " + domain + "."
                            breakloop = True
                            break
                if breakloop :
                    break
        return jsonify(vc_signature.verify(data['credential']) + message)


def picture(mode) :
    """ This is to download the user picture or company logo to the uploads folder
    app.route('/user/picture/', methods=['GET', 'POST'])
    """
    check_login()
    if request.method == 'GET' :
        if request.args.get('badtype') == 'true' :
            flash(_('Only "JPEG", "JPG", "PNG" files accepted'), 'warning')
        return render_template('picture.html',**session['menu'])
    if request.method == 'POST' :
        myfile = request.files['croppedImage']
        filename = "profile_pic.jpg"
        path_to_file = mode.uploads_path  + filename
        myfile.save(path_to_file)
        picture_hash = Talao_ipfs.file_add(path_to_file, mode)
        session['personal']['picture'] = session['picture'] = picture_hash
        ns.update_personal(session['workspace_contract'], json.dumps(session['personal']), mode)
        os.rename(path_to_file, mode.uploads_path + picture_hash)
        session['menu']['picturefile'] = mode.ipfs_gateway + session['picture']
        flash(_('Your picture has been updated'), 'success')
        return redirect(mode.server + 'user/')


def signature(mode) :
    """
    #@app.route('/user/signature/', methods=['GET', 'POST'])
    this function is also called for issuer within the company view
    """
    check_login()
    if request.method == 'GET' :
        if request.args.get('badtype') == 'true' :
            flash(_('Only "JPEG", "JPG", "PNG" files accepted'), 'warning')
        if session['role'] != 'issuer' :
            signature = mode.ipfs_gateway + session['signature']
        else :
            session['employee_workspace_contract'] = ns.get_data_from_username(session['username'], mode)['identity_workspace_contract']
            signature = mode.ipfs_gateway + json.loads(ns.get_personal(session['employee_workspace_contract'], mode))['signature']
        return render_template('signature.html', **session['menu'], signaturefile=signature)
    if request.method == 'POST' :
        myfile = request.files['croppedImage']
        path_to_file = mode.uploads_path + "signature.png"
        myfile.save(path_to_file)
        signature_hash = Talao_ipfs.file_add(path_to_file, mode)
        if not signature_hash :
            flash(_('Fail to update signature.'), 'warning')
            return redirect(mode.server + 'user/')
        flash(_('Your signature has been updated.'), 'success')
        if session['role'] != 'issuer' :
            session['personal']['signature'] = signature_hash
            session['signature'] = signature_hash 
            ns.update_personal(session['workspace_contract'], json.dumps(session['personal']), mode)
        else:
            personal = json.loads(ns.get_personal(session['employee_workspace_contract'], mode))
            personal['signature'] = signature_hash
            ns.update_personal(session['employee_workspace_contract'], json.dumps(personal), mode)
            del session['employee_workspace_contract']
        return redirect(mode.server + 'user/')


#@app.route('/user/success/', methods=['GET'])
def success(mode) :
    check_login()
    if request.method == 'GET' :
        if session['type'] == 'person' :
            flash(_('Picture has been updated'), 'success')
        else :
            flash(_('Logo has been updated'), 'success')
        return redirect(mode.server + 'user/')


#@app.route('/user/update_search_setting/', methods=['POST'])
def update_search_setting(mode) :
    check_login()
    try:
        response = directory.update_user(mode, session, request.form["CheckBox"] == "on")
        if response == "User already in database":
            flash(_('Your Name was already in the search bar.'), 'success')
        elif response:
            flash(_('Your Name has been added to the search bar.'), 'success')
        else:
            flash(_('There has been an error, please contact support.'), 'warning')
    except:
        directory.update_user(mode, session, False)
        flash(_('Your Name has been removed from the search bar.'), 'success')
    return redirect(mode.server + 'user/')


#@app.route('/user/update_phone/', methods=['GET', 'POST'])
def update_phone(mode) :
    check_login()
    if request.method == 'GET' :
        return render_template('update_phone.html', **session['menu'], phone=session['phone'])
    if request.method == 'POST' :
        _phone = request.form['phone']
        code = request.form['code']
        phone = code + _phone
        if _phone == "" :
            flash(_('Your phone number has been deleted.'), 'success')
            ns.update_phone(session['username'], None, mode)
            session['phone'] = ""
        elif sms.check_phone(phone, mode) :
            ns.update_phone(session['username'], phone, mode)
            session['phone'] = phone
            flash(_('Your phone number has been updated.'), 'success')
        else :
            flash(_('Incorrect phone number.'), 'warning')
        return redirect(mode.server + 'user/')


#@app.route('/user/update_password/', methods=['GET', 'POST'])
def update_password(mode) :
    check_login()
    if request.method == 'GET' :
        return render_template('update_password.html', **session['menu'])
    if request.method == 'POST' :
        current_password = request.form['current_password']
        new_password = request.form['password']
        if not ns.check_password(session['username'],current_password, mode) :
            flash (_('Wrong password'), 'warning')
            return render_template('update_password.html', **session['menu'])
        ns.update_password(session['username'], new_password, mode)
        flash (_('Password updated'), 'success')
        return redirect(mode.server + 'user/')


#@app.route('/report', methods=['GET', 'POST'])
def report(mode):
    if request.method == 'GET' :
        return render_template('report.html', **session['menu'])
    if request.method == 'POST' :
        email = "thierry.thevenet@talao.io"
        subject = "Bug Report"
        messagetext = """Hello,
        A bug has been reported by this identity: {link}
        His email is : {email}

        Description given by the user:

        {description}
        """.format(link = session['menu']['clipboard'],
                    email = ns.get_data_from_username(session['username'], mode)['email'],
                    description = request.form['description'])
        Talao_message.message(subject, email, messagetext, mode)
        flash(_('The bug has been reported ! Thank you for your help ! '), "success")
        return redirect(mode.server + 'user/')


def select_identity (mode) :
    if request.method == 'GET' :
        """ Select Identity for companies only
        """
        # FIXME
        method = ns.get_method(session['workspace_contract'], mode)
        if method == "ethr" :
            ethr_box = "checked"
            tz_box =  ""
            web_box = ""
        elif method == "tz" :
            ethr_box= ""
            tz_box = "checked"
            web_box = ""
        else :
            ethr_box= ""
            tz_box = ""
            web_box = "checked"
        return render_template('select_identity.html', **session['menu'], ethr_box=ethr_box, tz_box=tz_box, web_box=web_box)

    if request.method == 'POST' :
        ns.update_method(session['workspace_contract'], request.form['method'], mode)
        session['method'] = request.form['method']
        if session['method'] in ['ethr', 'tz'] :
            did = helpers.ethereum_pvk_to_DID(session['private_key_value'], session['method'])
            ns.add_did(session['workspace_contract'], did, mode)
        else :
            did = request.form.get('web_did')
            if not did :
                return redirect(mode.server + 'user/')
        if not did in ns.get_did_list(session['workspace_contract'], mode) :
            ns.add_did(session['workspace_contract'], did, mode)
        return redirect(mode.server + 'user/')

# ["did:web:talao.co", "did:ethr:0xee09654eedaa79429f8d216fa51a129db0f72250"]

# Tutorial
#@app.route('/user/tutorial/', methods=['GET'])
def tutorial() :
    check_login()
    return render_template('tutorial.html', **session['menu'])


#Prefetch for typehead
#@app.route('/prefetch', methods=['GET', 'POST'])
def prefetch(mode) :
    user_list = directory.user_list_search(request.args['q'], mode)
    return json.dumps(user_list)


# search
#@app.route('/user/search/', methods=['GET', 'POST'])
def search(mode) :
    check_login()
    if request.method == 'GET' :
        return render_template('search.html', **session['menu'])
    if request.method == 'POST' :
        username_to_search = request.form['username_to_search'].lower()
        if username_to_search == session['username'] :
            flash(_('Here you are !'), 'success')
            return redirect(mode.server + 'user/')
        if not ns.username_exist(username_to_search, mode) :
            flash(_('Username not found.'), "warning")
            return redirect(mode.server + 'user/')
        else :
            return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + username_to_search)


def issue_certificate(mode):
    """ main function to issue certificate wthout formal request and specific workflow
    FIXME signature management
    @app.route('/user/issue_certificate/', methods=['GET', 'POST'])
    """
    check_login()
    if not session['private_key'] :
        flash(_('We do not have your Private Key to issue a Certificate.'), 'warning')
        return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])

    if session['type'] == 'company' and session['issuer_explore']['type'] == 'person' :
        flash(_('Talent is required to make a formal request.'), 'warning')
        return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])

    if request.method == 'GET' :
        return render_template('issue_certificate.html',
                                **session['menu'],
                                issuer_username=session['issuer_username'])
    if request.method == 'POST' :

        if request.form['certificate_type'] == 'recommendation'  :
            return render_template('issue_recommendation.html',
                                    **session['menu'],
                                    issuer_username=session['issuer_username'],
                                    issuer_name = session['issuer_explore']['name'])

        elif request.form['certificate_type'] == 'reference'  :
            return render_template('issue_reference_credential.html',
                                    **session['menu'],
                                    issuer_username=session['issuer_username'],
                                    issuer_name = session['issuer_explore']['name'])
        
        elif request.form['certificate_type'] == 'ccicertificate'  :
            return render_template('issue_cci_certificate.html',
                                    **session['menu'],
                                    certificate_type="CciCertificate",
                                    issuer_username=session['issuer_username'],
                                    issuer_name = session['issuer_explore']['name'])
        
        elif request.form['certificate_type'] == 'ccicertificate_v2'  :
            return render_template('issue_cci_certificate_v2.html',
                                    certificate_type="CciCertificate_v2",
                                    **session['menu'],
                                    issuer_username=session['issuer_username'],
                                    issuer_name = session['issuer_explore']['name'])

        else :
            flash(_('This certificate is not implemented yet !'), 'warning')
            return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])

def issue_cci_certificate(mode):
    """ issue a reference credential to company without review and no request   
    @app.route('/commpany/issue_cci_certificate/', methods=['GET','POST'])

    foncitonne pour  les 2 versions des certiofiocats UdF avec evaluation ou avec avis
    """
    check_login()

    # call from issue_reference_credential.html
    if request.method == 'POST' :
        workspace_contract_to = ns.get_data_from_username(session['issuer_username'], mode)['workspace_contract']

        # load templates for verifiable credential and init with view form and session
        if request.form['certificate_type'] == "CciCertificate_v2" :
            unsigned_credential = json.load(open('./verifiable_credentials/CciCertificate_v2.jsonld', 'r'))
        elif request.form['certificate_type'] == "CciCertificate" :
            unsigned_credential = json.load(open('./verifiable_credentials/CciCertificate.jsonld', 'r'))
        else :
            print('(errerur certificat type', request.form['certificate_type'])

        unsigned_credential["id"] =  "urn:uuid:" + str(uuid.uuid1())
        unsigned_credential["issuer"] = ns.get_did(session['workspace_contract'], mode)
        unsigned_credential["issuanceDate"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        unsigned_credential[ "credentialSubject"]["id"] = ns.get_did(session['issuer_explore']['workspace_contract'], mode)

        unsigned_credential[ "credentialSubject"]['provider']["legalName"] = session['issuer_explore']['name']
        unsigned_credential[ "credentialSubject"]['provider']["rcs"] = session['issuer_explore']['personal']['rcs'].get('claim_value', "unknown rcs")
        unsigned_credential[ "credentialSubject"]['provider']["siren"] = session['issuer_explore']['personal']['siren'].get('claim_value', "unknown siren")
        unsigned_credential[ "credentialSubject"]['provider']["contactEmail"] = session['issuer_explore']['personal']['contact_email'].get('claim_value', "unknown email")
        unsigned_credential[ "credentialSubject"]['provider']["address"] = session['issuer_explore']['personal']['postal_address'].get('claim_value', "unknown address")

        unsigned_credential['credentialSubject']['title'] = request.form['title']
        unsigned_credential['credentialSubject']['description'] = request.form['description']
        unsigned_credential['credentialSubject']['deliveryTime']['duration'] = request.form['duration']
        unsigned_credential[ "credentialSubject"]["briquesAIF"] = request.form['briquesAIF']
        unsigned_credential[ "credentialSubject"]["domaineIntervention"] = request.form["domaineIntervention"]

        if request.form['certificate_type'] == "CciCertificate" :
            reviewRecommendation, reviewDelivery, reviewSchedule, reviewCommunication = 0,1,2,3
            unsigned_credential['credentialSubject']['review'][reviewRecommendation]['reviewRating']['ratingValue'] = request.form['score_recommendation']
            unsigned_credential['credentialSubject']['review'][reviewSchedule]['reviewRating']['ratingValue'] = request.form['score_schedule']
            unsigned_credential['credentialSubject']['review'][reviewDelivery]['reviewRating']['ratingValue'] = request.form['score_delivery']
            unsigned_credential['credentialSubject']['review'][reviewCommunication]['reviewRating']['ratingValue'] = request.form['score_communication']
        
        elif request.form['certificate_type'] == "CciCertificate_v2" :
            unsigned_credential['credentialSubject']['review']["reviewBody"] = request.form['review']

        unsigned_credential['credentialSubject']['customer']["legalName"] = session['name']
        unsigned_credential['credentialSubject']['customer']["siren"] = session['personal']['siren'].get('claim_value', "unknown siren")
        unsigned_credential['credentialSubject']['customer']["rcs"] = session['personal']['rcs'].get('claim_value', "unknown rcs")
        unsigned_credential['credentialSubject']['customer']["address"] = session['personal']['postal_address'].get('claim_value', "unknown address")
        
        unsigned_credential['credentialSubject']['signatureLines']["jobTitle"] = "Directeur"
        unsigned_credential['credentialSubject']['signatureLines']["responsableMission"] = request.form['responsableMission']

        print('unsigned_credential = ', unsigned_credential)
        
        # sign credential
        signed_credential = vc_signature.sign(unsigned_credential, session['private_key_value'], unsigned_credential['issuer'])
        logging.info('credential signed')

        # store signed credential on server
        filename = unsigned_credential['id'] + '.jsonld'
        path = "./signed_credentials/"
        with open(path + filename, 'w') as outfile :
            json.dump(json.loads(signed_credential), outfile, indent=4, ensure_ascii=False)
            logging.info('credential strored on server')

        # upload to repository
        ref = Document('certificate')
        ref.relay_add(workspace_contract_to, json.loads(signed_credential), mode, synchronous=False)
        logging.info('transaction launched asynchronous')
        flash(_('Credential is beeing issued.'), 'success')

        return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])


def issue_reference_credential(mode):
    """ issue a reference credential to company without review and no request
    FIXME  rework the loading of credential and the credential data model (signatuer lines...)
    call within the "issuer_explore" context
    @app.route('/commpany/issue_reference_credential/', methods=['GET','POST'])
    The signature is the manager's signature except if the issuer is the company 
    """
    check_login()

    # call from issue_reference_credential.html
    if request.method == 'POST' :
        workspace_contract_to = ns.get_data_from_username(session['issuer_username'], mode)['workspace_contract']

        # load templates for verifibale credential and init with view form and session
        unsigned_credential = json.load(open('./verifiable_credentials/reference.jsonld', 'r'))
        id = str(uuid.uuid1())
        unsigned_credential["id"] =  "data:" + id
        unsigned_credential["issuer"] = ns.get_did(session['workspace_contract'], mode)
        unsigned_credential["issuanceDate"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        unsigned_credential[ "credentialSubject"]["id"] = ns.get_did(session['issuer_explore']['workspace_contract'], mode)
        unsigned_credential[ "credentialSubject"]["name"] = session['issuer_explore']["name"]
        unsigned_credential[ "credentialSubject"]["offers"]["title"] = request.form['title']
        unsigned_credential[ "credentialSubject"]["offers"]["description"] = request.form['description']
        unsigned_credential[ "credentialSubject"]["offers"]["startDate"] = request.form['startDate']
        unsigned_credential[ "credentialSubject"]["offers"]["endDate"] = request.form['endDate']
        unsigned_credential[ "credentialSubject"]["offers"]["price"] = request.form['budget']
        unsigned_credential[ "credentialSubject"]["offers"]["location"] = request.form['location']
        unsigned_credential[ "credentialSubject"]["review"]["reviewBody"] = request.form['review']
        for skill in request.form['skills'].split(',') :
            unsigned_credential["credentialSubject"]["offers"]["skills"].append(
            {
            "@type": "DefinedTerm",
            "description": skill
            })
        unsigned_credential[ "credentialSubject"]["companyLogo"] = session['picture']
        unsigned_credential[ "credentialSubject"]["companyName"] = session['name']
        unsigned_credential[ "credentialSubject"]["managerName"] = "Director"
        unsigned_credential[ "credentialSubject"]["managerSignature"] = session['signature']
         
        # sign credential
        signed_credential = vc_signature.sign(unsigned_credential, session['private_key_value'], unsigned_credential['issuer'])
        logging.info('credential signed')

        # store signed credential on server
        filename = unsigned_credential['id'] + '_credential.jsonld'
        path = "./signed_credentials/"
        with open(path + filename, 'w') as outfile :
            json.dump(json.loads(signed_credential), outfile, indent=4, ensure_ascii=False)
            logging.info('credential strored on server')

        # upload to repository
        ref = Document('certificate')
        ref.relay_add(workspace_contract_to, json.loads(signed_credential), mode, synchronous=False)
        logging.info('transaction launched asynchronous')
        flash(_('Credential is beeing issued.'), 'success')

        return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])


def update_personal_settings(mode) :
    """  personal settings

    @app.route('/user/update_personal_settings/', methods=['GET', 'POST'])
    """
    check_login()
    personal = copy.deepcopy(session['personal'])
    convert(personal)
    if request.method == 'GET' :
        privacy=dict()
        for topicname in PERSON_TOPIC :
            if session['personal'][topicname]['privacy']=='secret' :
                (p1,p2,p3) = ("", "", "selected")
            if session['personal'][topicname]['privacy']=='private' :
                (p1,p2,p3) = ("", "selected", "")
            if session['personal'][topicname]['privacy']=='public' :
                (p1,p2,p3) = ("selected", "", "")
            if not session['personal'][topicname]['privacy'] :
                (p1,p2,p3) = ("", "", "")
            privacy[topicname] = """
                    <optgroup>
                    <option """+ p1 + """ value="public">Public</option>
                    <option """ + p2 +""" value="private">Private</option>
                    </opgroup>"""
        return render_template('update_personal_settings.html',
                                **session['menu'],
                                firstname=personal['firstname']['claim_value'],
                                lastname=personal['lastname']['claim_value'],
                                about=personal['about']['claim_value'],
                                education=personal['education']['claim_value'],
                                contact_email=personal['contact_email']['claim_value'],
                                contact_email_privacy=privacy['contact_email'],
                                contact_phone=personal['contact_phone']['claim_value'],
                                contact_phone_privacy=privacy['contact_phone'],
                                birthdate=personal['birthdate']['claim_value'],
                                birthdate_privacy=privacy['birthdate'],
                                postal_address=personal['postal_address']['claim_value'],
                                postal_address_privacy=privacy['postal_address']
                                )
    if request.method == 'POST' :
        form_privacy = dict()
        form_privacy['contact_phone'] = request.form['contact_phone_select']
        form_privacy['contact_email'] = request.form['contact_email_select']
        form_privacy['birthdate'] = request.form['birthdate_select']
        form_privacy['postal_address'] = request.form['postal_address_select']
        form_privacy['firstname'] = 'public'
        form_privacy['lastname'] = 'public'
        form_privacy['about'] = 'public'
        form_privacy['profil_title'] = 'public'
        form_privacy['education'] = 'public'
        for topicname in PERSON_TOPIC :
            personal[topicname]['claim_value'] = request.form[topicname]
            personal[topicname]['privacy'] = form_privacy[topicname]
            session['personal'][topicname] = personal[topicname]
        ns.update_personal(session['workspace_contract'], json.dumps(personal, ensure_ascii=False), mode)
        session['name'] = session['menu']['name'] = personal['firstname']['claim_value'] + ' ' + personal['lastname']['claim_value']
        flash(_('Personal has been updated'), 'success')
        return redirect(mode.server + 'user/')


def convert(obj):
    if type(obj) == list:
        for x in obj:
            convert(x)
    elif type(obj) == dict:
        for k, v in obj.items():
            if v is None:
                obj[k] = ''
            else :
                convert(v)
    return True


# company settings
#@app.route('/user/update_company_settings/', methods=['GET', 'POST'])
def update_company_settings(mode) :
    check_login()
    personal = copy.deepcopy(session['personal'])
    convert(personal)
    if request.method == 'GET' :
        privacy=dict()
        for topicname in COMPANY_TOPIC :
            if session['personal'][topicname]['privacy']=='secret' :
                (p1,p2,p3) = ("", "", "selected")
            if session['personal'][topicname]['privacy']=='private' :
                (p1,p2,p3) = ("", "selected", "")
            if session['personal'][topicname]['privacy']=='public' :
                (p1,p2,p3) = ("selected", "", "")
            if not session['personal'][topicname]['privacy'] :
                (p1,p2,p3) = ("", "", "")
            privacy[topicname] = """
                    <optgroup """ +  """ label="Select">
                    <option """+ p1 + """ value="public">Public</option>
                    <option """ + p2 +""" value="private">Private</option>
                    <option """ + p3 + """ value="secret">Secret</option>
                    </opgroup>"""

        if 'siren' in request.args:
            settings = siren.company(session['personal']['siren']['claim_value'])
            if not settings:
                flash(_('Company not found in SIREN database.'), 'warning')
            else:
                return render_template('update_company_settings.html',
                                        **session['menu'],
                                        contact_name=personal['contact_name']['claim_value'],
                                        contact_name_privacy=privacy['contact_name'],
                                        contact_email=personal['contact_email']['claim_value'],
                                        contact_email_privacy=privacy['contact_email'],
                                        contact_phone=personal['contact_phone']['claim_value'],
                                        contact_phone_privacy=privacy['contact_phone'],
                                        website=personal['website']['claim_value'],
                                        about=settings['activity'] + " " + personal['about']['claim_value'],
                                        staff=settings['staff'],
                                        mother_company=personal['mother_company']['claim_value'],
                                        sales=personal['sales']['claim_value'],
                                        siren=personal['siren']['claim_value'],
                                        postal_address=settings['address'],
                                        )
        return render_template('update_company_settings.html',
                            **session['menu'],
                            contact_name=personal['contact_name']['claim_value'],
                            contact_name_privacy=privacy['contact_name'],
                            contact_email=personal['contact_email']['claim_value'],
                            contact_email_privacy=privacy['contact_email'],
                            contact_phone=personal['contact_phone']['claim_value'],
                            contact_phone_privacy=privacy['contact_phone'],
                            website=personal['website']['claim_value'],
                            about=personal['about']['claim_value'],
                            staff=personal['staff']['claim_value'],
                            mother_company=personal['mother_company']['claim_value'],
                            sales=personal['sales']['claim_value'],
                            siren=personal['siren']['claim_value'],
                            postal_address=personal['postal_address']['claim_value'],
                            )

    if request.method == 'POST' :
        form_privacy = dict()
        form_privacy['contact_name'] = request.form['contact_name_select']
        form_privacy['contact_phone'] = request.form['contact_phone_select']
        form_privacy['contact_email'] = request.form['contact_email_select']
        form_privacy['name'] = 'public'
        form_privacy['website'] = 'public'
        form_privacy['sales'] = 'public'
        form_privacy['about'] = 'public'
        form_privacy['staff'] = 'public'
        form_privacy['mother_company'] = 'public'
        form_privacy['siren'] = 'public'
        form_privacy['postal_address'] = 'public'
        for topicname in COMPANY_TOPIC :
            personal[topicname]['claim_value'] = request.form[topicname]
            personal[topicname]['privacy'] = form_privacy[topicname]
            session['personal'][topicname] = personal[topicname]
        ns.update_personal(session['workspace_contract'], json.dumps(personal, ensure_ascii=False), mode)
        session['name'] = session['menu']['name'] = personal['name']['claim_value']
        directory.update_siren(session['username'], request.form['siren'], mode)
        flash(_('Company settings have been updated'), 'success')
        return redirect(mode.server + 'user/')


# digital vault
#@app.route('/user/store_file/', methods=['GET', 'POST'])
def store_file(mode) :
    check_login()
    if request.method == 'GET' :
        return render_template('store_file.html', **session['menu'])
    if request.method == 'POST' :
        myfile = request.files['file']
        filename = secure_filename(myfile.filename)
        myfile.save(os.path.join(mode.uploads_path, filename))
        privacy = request.form['privacy']
        user_file = File()
        data = user_file.add(mode.relay_address,
                             mode.relay_workspace_contract,
                             session['address'],
                             session['workspace_contract'],
                             mode.relay_private_key,
                             filename,
                             privacy,
                            mode)
        if not data[0] :
            flash(_('Transaction failed'), "danger")
        else :
            new_file = {'id' : 'did:talao:'+ mode.BLOCKCHAIN+':'+ session['workspace_contract'][2:]+':document:'+ str(data[0]),
                                    'filename' : filename,
                                    'doc_id' : data[0],
                                    'created' : str(datetime.utcnow()),
                                    'privacy' : privacy,
                                    'doctype' : "",
                                    'issuer' : mode.relay_address,
                                    'transaction_hash' : data[2]
                                    }
            session['identity_file'].append(new_file)
            flash(_('File ') + filename + _(' has been uploaded.'), "success")
        return redirect(mode.server + 'user/')


# add experience
def add_experience(mode) :
    """ Add ad experience in teh local database
    @app.route('/user/add_experience/', methods=['GET', 'POST'])
    """
    check_login()
    if request.method == 'GET' :
        return render_template('add_experience.html',**session['menu'])
    if request.method == 'POST' :
        experience = dict()
        experience['company'] = {'contact_email' : request.form['contact_email'],
                                'name' : request.form['company_name'],
                                'contact_name' : request.form['contact_name'],
                                'contact_phone' : request.form['contact_phone']}
        experience['title'] = request.form['title']
        experience['description'] = request.form['description']
        experience['start_date'] = request.form['from']
        experience['end_date'] = request.form['to']
        experience['skills'] = request.form['skills'].split(', ')
        experience['id'] =  str(uuid.uuid1())
        personal = json.loads(ns.get_personal(session['workspace_contract'], mode))
        if not personal.get('experience_claims') :
            personal['experience_claims'] = list()
        personal['experience_claims'].append(experience)
        ns.update_personal(session['workspace_contract'], json.dumps(personal), mode)
        session['experience'].append(experience)
        flash(_('New experience added'), 'success')
        return redirect(mode.server + 'user/')

def add_activity(mode) :
    """ Add an experience with current as end_date in the local database
    @app.route('/user/add_experience/', methods=['GET', 'POST'])
    """
    check_login()
    if request.method == 'GET' :
        return render_template('add_activity.html',**session['menu'])
    if request.method == 'POST' :
        experience = dict()
        experience['company'] = {'contact_email' : request.form['contact_email'],
                                'name' : request.form['company_name'],
                                'contact_name' : request.form['contact_name'],
                                'contact_phone' : request.form['contact_phone']}
        experience['title'] = request.form['title']
        experience['description'] = request.form['description']
        experience['start_date'] = request.form['from']
        experience['end_date'] = ""
        experience['skills'] = request.form['skills'].split(', ')
        experience['id'] =  str(uuid.uuid1())
        personal = json.loads(ns.get_personal(session['workspace_contract'], mode))
        if not personal.get('experience_claims') :
            personal['experience_claims'] = list()
        personal['experience_claims'].append(experience)
        ns.update_personal(session['workspace_contract'], json.dumps(personal), mode)
        session['experience'].append(experience)
        flash(_('New experience added'), 'success')
        return redirect(mode.server + 'user/')


#@app.route('/user/remove_experience/', methods=['GET', 'POST'])
def remove_experience(mode) :
    check_login()
    personal = json.loads(ns.get_personal(session['workspace_contract'], mode))
    experience = personal.get('experience_claims', [])
    for counter,exp in enumerate(session['experience'], 0) :
        if exp['id'] == request.args['experience_id'] :
            del session['experience'][counter]
            break
    for counter,exp in enumerate(experience, 0) :
        if exp['id'] == request.args['experience_id'] :
            del experience[counter]
            break
    personal['experience_claims'] = experience
    ns.update_personal(session['workspace_contract'], json.dumps(personal), mode)
    flash(_('The experience has been removed'), 'success')
    return redirect (mode.server +'user/')


def create_company(mode) :
    """ 
    @app.route('/user/create_company/', methods=['GET', 'POST'])
    """
    check_login()
    if request.method == 'GET' :
        return render_template('create_company.html', **session['menu'])
    if request.method == 'POST' :
        email = request.form['email']
        did = request.form.get('did', "")
        username = request.form['name'].lower()
        siren = request.form['siren']
        if ns.username_exist(username, mode)   :
            username = username + str(random.randint(1, 100))
        workspace_contract =  createcompany.create_company(email, username, did, mode, siren=siren)[2]
        if workspace_contract :
            directory.add_user(mode, request.form['name'], username, siren)
            filename = mode.db_path + 'company.json'
            personal = json.load(open(filename, 'r'))
            ns.update_personal(workspace_contract, json.dumps(personal, ensure_ascii=False), mode)
            flash(username + _(' has been created as company.'), 'success')
        else :
            flash(_('Company Creation failed.'), 'danger')
        return redirect(mode.server + 'user/')


def create_user(mode) :
    """ create an employee for a company 
    @app.route('/user/create_user/', methods=['GET', 'POST'])
    """
    check_login()
    if request.method == 'GET' :
        return render_template('create_user.html', **session['menu'])
    if request.method == 'POST' :
        email = request.form['email']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = (firstname + lastname).lower()
        if ns.username_exist(username, mode)   :
            username = username + str(random.randint(1, 100))
        if createidentity.create_user(username, email, mode, firstname=firstname, lastname=lastname, silent=True)[2] :
            name = request.form['firstname'] + ' ' + request.form['lastname']
            directory.add_user(mode, username, name, '')
            flash(username + _(' has been created as a new user of the company.'), 'success')
        else :
            flash(_('Identity creation failed'), 'danger')
        return redirect(mode.server + 'user/')


def remove_certificate(mode) :
    """ delete a certificate 
    @app.route('/user/remove_certificate/', methods=['GET', 'POST'])
    """
    check_login()
    if request.method == 'GET' :
        session['certificate_to_remove'] = request.args['certificate_id']
        return render_template('remove_certificate.html', **session['menu'])
    if request.method == 'POST' :
        session['all_certificate'] = [certificate for certificate in session['all_certificate'] if certificate['id'] != session['certificate_to_remove']]
        doc_id = session['certificate_to_remove'].split(':')[5]
        if not  Document('certificate').relay_delete(session['workspace_contract'], int(doc_id), mode) :
            flash(_('Transaction failed.'), 'danger')
            logging.warning('transaction to delete credential failed')
        else :
            flash(_('The certificate has been removed from your repository.'), 'success')
            del session['certificate_to_remove']
            return redirect (mode.server +'user/')



def swap_privacy(mode) :
    """ swap privacy of a certificate 
    @app.route('/user/swap_privacy/', methods=['GET', 'POST'])
    """
    check_login()
    if request.method == 'GET' :
        session['certificate_to_swap'] = request.args['certificate_id']
        if request.args['privacy'] == 'public' :
            session['new_privacy'] = 'private'
        else :
            session['new_privacy'] = 'public'
        return render_template('swap_privacy.html', **session['menu'], new_privacy=session['new_privacy'])

    if request.method == 'POST' :
        doc_id = int(session['certificate_to_swap'].split(':')[5])
        new_doc_id, new_ipfs_hash, n =  Document('certificate').relay_update_privacy(session['workspace_contract'], doc_id, session['new_privacy'], mode)
        if not new_doc_id :
            flash(_('Transaction failed.'), 'danger')
            logging.warning('transaction to swap credential privacy failed')
        else :
            if session['new_privacy'] == 'private' :
                for counter, certificate in enumerate(session['certificate']) :
                    if int(certificate['id'].split(':')[5]) == doc_id :
                        new_certificate = copy.deepcopy(certificate)
                        new_certificate['id'] = 'did:talao:talaonet' + session['workspace_contract'][2:] + ':document:' + str(new_doc_id)
                        new_certificate['privacy'] = 'private'
                        new_certificate['doc_id'] = new_doc_id
                        new_certificate['data_location'] = 'https://gateway.pinata.cloud/ipfs/'+ new_ipfs_hash
                        del session['certificate'][counter]
                        session['private_certificate'].append(new_certificate)
                        break
            else :
                for counter, certificate in enumerate(session['private_certificate']) :
                    print('certificate(id) = ', certificate['id'], type(certificate['id']))
                    if int(certificate['id'].split(':')[5]) == doc_id :
                        new_certificate = copy.deepcopy(certificate)
                        new_certificate['id'] = 'did:talao:talaonet:' + session['workspace_contract'][2:] + ':document:' + str(new_doc_id)
                        new_certificate['privacy'] = session['new_privacy']
                        new_certificate['doc_id'] = 'public'
                        new_certificate['data_location'] = 'https://gateway.pinata.cloud/ipfs/'+ new_ipfs_hash
                        del session['private_certificate'][counter]
                        session['certificate'].append(new_certificate)
                        break
            session['all_certificate'] = session['certificate'] + session['private_certificate'] + session['secret_certificate']
        del session['certificate_to_swap']
        del session['new_privacy']
        return redirect (mode.server +'user/')


#@app.route('/user/remove_file/', methods=['GET', 'POST'])
def remove_file(mode) :
    check_login()
    if request.method == 'GET' :
        session['file_id_to_remove'] = request.args['file_id']
        session['filename_to_remove'] = request.args['filename']
        return render_template('remove_file.html', **session['menu'],filename=session['filename_to_remove'])
    elif request.method == 'POST' :
        session['identity_file'] = [one_file for one_file in session['identity_file'] if one_file['id'] != session['file_id_to_remove']]
        Id = session['file_id_to_remove'].split(':')[5]
        my_file = File()
        if not my_file.relay_delete(session['workspace_contract'], int(Id), mode) :
            flash(_('Transaction failed.'), 'danger')
        else :
            del session['file_id_to_remove']
            del session['filename_to_remove']
            flash(_('The file has been deleted.'), 'success')
        return redirect (mode.server +'user/')


# add education
#@app.route('/user/add_education/', methods=['GET', 'POST'])
def add_education(mode) :
    check_login()
    if request.method == 'GET' :
        return render_template('add_education.html', **session['menu'])
    if request.method == 'POST' :
        my_education = Document('education')
        education  = dict()
        education['organization'] = {'contact_email' : request.form['contact_email'],
                                'name' : request.form['company_name'],
                                'contact_name' : request.form['contact_name'],
                                'contact_phone' : request.form['contact_phone']}
        education['title'] = request.form['title']
        education['description'] = request.form['description']
        education['start_date'] = request.form['from']
        education['end_date'] = request.form['to']
        education['skills'] = request.form['skills'].split(',')
        education['certificate_link'] = request.form['certificate_link']
        education['id'] =  str(uuid.uuid1())
        personal = json.loads(ns.get_personal(session['workspace_contract'], mode))
        if not personal.get('education_claims') :
            personal['education_claims'] = list()
        personal['education_claims'].append(education)
        ns.update_personal(session['workspace_contract'], json.dumps(personal), mode)
        session['education'].append(education)
        flash(_('New Education added.'), 'success')
        return redirect(mode.server + 'user/')


def remove_education(mode) :
    #@app.route('/user/remove_education/', methods=['GET', 'POST'])
    check_login()
    personal = json.loads(ns.get_personal(session['workspace_contract'], mode))
    education = personal.get('education_claims', [])
    for counter,edu in enumerate(session['education'], 0) :
        if edu['id'] == request.args['education_id'] :
            del session['education'][counter]
            break
    for counter,edu in enumerate(education, 0) :
        if edu['id'] == request.args['education_id'] :
            del education[counter]
            break
    personal['education_claims'] = education
    ns.update_personal(session['workspace_contract'], json.dumps(personal), mode)
    flash(_('Education has been removed'), 'success')
    return redirect (mode.server +'user/')


# invit
#@app.route('/user/invit/', methods=['GET', 'POST'])
def invit(mode) :
    check_login()
    if request.method == 'GET' :
        return render_template('invit.html', **session['menu'])
    if request.method == 'POST' :
        talent_email = request.form['email']
        username_list = ns.get_username_list_from_email(talent_email, mode)
        if username_list != [] :
            msg = _('This email is already used by Identity(ies) : ') + ", ".join(username_list) + ' . Use the Search Bar.'
            flash(msg , 'warning')
            return redirect(mode.server + 'user/')
        subject = 'You have been invited to join Talao'
        name = session['personal']['firstname']['claim_value'] + session['personal']['lastname']['claim_value']
        execution = Talao_message.messageHTML(subject, talent_email, 'invite_to_join', {'name':name}, mode)
        if execution :
            flash(_('Your invit has been sent.'), 'success')
        else :
            flash(_('Your invit has not been sent.'), 'danger')
        return redirect(mode.server + 'user/')


# send memo by email
#@app.route('/user/send_memo/', methods=['GET', 'POST'])
def send_memo(mode) :
    check_login()
    if request.method == 'GET' :
        session['memo_username'] = request.args['issuer_username']
        return render_template('send_memo.html', **session['menu'], memo_username=session['memo_username'])
    if request.method == 'POST' :
        # email to issuer
        subject = _("You have received a memo from ") + session['name'] +"."
        memo = request.form['memo']
        memo_email = ns.get_data_from_username(session['memo_username'], mode)['email']
        Talao_message.messageHTML(subject, memo_email, 'memo', {'name': session['name'], 'memo':memo}, mode)
        # message to user
        flash(_("Your memo has been sent to ") + session['memo_username'], 'success')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['memo_username'])


# request partnership
#@app.route('/user/request_partnership/', methods=['GET', 'POST'])
def request_partnership(mode) :
    check_login()
    if request.method == 'GET' :
        session['partner_username'] = request.args['issuer_username']
        return render_template('request_partnership.html', **session['menu'], partner_username=session['partner_username'])
    if request.method == 'POST' :
        partner_workspace_contract = ns.get_data_from_username(session['partner_username'], mode)['workspace_contract']
        partner_address = contractsToOwners(partner_workspace_contract, mode)
        partner_publickey = mode.w3.solidityKeccak(['address'], [partner_address]).hex()
        if not session['rsa_key'] :
            flash(_('Request Partnership to ') + session['partner_username'] + _(' is not available (RSA key not found)'), 'warning')
            return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['partner_username'])
        #relay signs the transaction"
        if  partnershiprequest(mode.relay_address,
                                 mode.relay_workspace_contract,
                                 session['address'],
                                 session['workspace_contract'],
                                 mode.relay_private_key,
                                 partner_workspace_contract,
                                 session['rsa_key_value'],
                                 mode,
                                 synchronous= True) :
            # add partnership in current session
            session['partner'].append({"address": partner_address,
                                "publickey": partner_publickey,
                                 "workspace_contract" : partner_workspace_contract,
                                  'username' : session['partner_username'],
                                  'authorized' : 'Authorized',
                                  'status' : "Pending"
                                  })
            # add partner in the issuer list if not already in
            if not is_username_in_list(session['issuer'], session['partner_username']) :
                if not add_key(mode.relay_address,
                             mode.relay_workspace_contract,
                             session['address'],
                             session['workspace_contract'],
                             mode.relay_private_key,
                             partner_address,
                             20002,
                             mode,
                             synchronous=True) :
                    flash(_('transaction for add issuer failed.'), 'danger')
                else :
                    session['issuer'].append(ns.get_data_from_username(session['partner_username'], mode))
            # user message
            flash(_('You have send a Request for Partnership to ') + session['partner_username'], 'success')
            # partner email
            subject = session['name'] + " souhaite accéder aux données privées de votre Identité Talao"
            partner_email = ns.get_data_from_username(session['partner_username'], mode)['email']
            Talao_message.messageHTML(subject, partner_email, 'request_partnership', {'name' : session['name']}, mode)
        else :
            flash(_('Request to ') + session['partner_username'] + _(' failed'), 'danger')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['issuer_username'])


# remove partnership
#@app.route('/user/remove_partner/', methods=['GET', 'POST'])
def remove_partner(mode) :
    check_login()
    if request.method == 'GET' :
        session['partner_username_to_remove'] = request.args['partner_username']
        session['partner_workspace_contract_to_remove'] = request.args['partner_workspace_contract']
        return render_template('remove_partner.html', **session['menu'], partner_name=session['partner_username_to_remove'])
    if request.method == 'POST' :
        res = remove_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_remove'], mode)
        if not res :
            flash (_('Partnership removal has failed.'))
        else :
            # remove partneship in current session
            session['partner'] = [ partner for partner in session['partner'] if partner['workspace_contract'] != session['partner_workspace_contract_to_remove']]
            flash(_('The partnership with ') + session['partner_username_to_remove']+ _('  has been removed'), 'success')
        del session['partner_username_to_remove']
        del session['partner_workspace_contract_to_remove']
        return redirect (mode.server +'user/')


# reject partnership
#@app.route('/user/reject_partner/', methods=['GET', 'POST'])
def reject_partner(mode) :
    check_login()
    if request.method == 'GET' :
        session['partner_username_to_reject'] = request.args['partner_username']
        session['partner_workspace_contract_to_reject'] = request.args['partner_workspace_contract']
        return render_template('reject_partner.html', **session['menu'], partner_name=session['partner_username_to_reject'])
    if request.method == 'POST' :
        res = reject_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_reject'], mode)
        if not res :
            flash (_('Partnership rejection has failed.'))
        else :
            # remove partnership in current session
            session['partner'] = [ partner for partner in session['partner'] if partner['workspace_contract'] != session['partner_workspace_contract_to_reject']]
            # message to user
            flash(_('The Partnership with ') + session['partner_username_to_reject']+ _('  has been rejected.'), 'success')
            # email to partner
            subject = "Your Request for Partnership has been rejected by " + session['name']
            partner_email = ns.get_data_from_username(session['partner_username_to_reject'], mode)['email']
            text = ""
            Talao_message.messageHTML(subject, partner_email, 'request_partnership_rejected', {'name' : session['name'], 'text' : text}, mode)
        del session['partner_username_to_reject']
        del session['partner_workspace_contract_to_reject']
        return redirect (mode.server +'user/')


# authorize partnership
#@app.route('/user/authorize_partner/', methods=['GET', 'POST'])
def authorize_partner(mode) :
    check_login()
    if request.method == 'GET' :
        session['partner_username_to_authorize'] = request.args['partner_username']
        session['partner_workspace_contract_to_authorize'] = request.args['partner_workspace_contract']
        return render_template('authorize_partner.html', **session['menu'], partner_name=session['partner_username_to_authorize'])
    if request.method == 'POST' :
        if not session['rsa_key'] :
            flash(_('Request a Partnership to ') + session['partner_username'] + _(' is impossible (RSA key not found)'), 'warning')
            del session['partner_username_to_authorize']
            del session['partner_workspace_contract_to_authorize']
            return redirect (mode.server +'user/')
        if not authorize_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_authorize'], session['rsa_key_value'], mode) :
            flash (_('Partnership authorization failed.'), 'danger')
        else :
            flash(_('The partnership with ') + session['partner_username_to_authorize']+ _('  has been authorized.'), 'success')
            # update partnership in current session
            for partner in session['partner'] :
                if partner['workspace_contract'] == session['partner_workspace_contract_to_authorize'] :
                    partner['authorized'] = "Authorized"
                    break
        del session['partner_username_to_authorize']
        del session['partner_workspace_contract_to_authorize']
        return redirect (mode.server +'user/')

"""
#@app.route('/user/request_recommendation_certificate/', methods=['POST'])
def request_recommendation_certificate(mode) :
    check_login()
    issuer_workspace_contract = None if not session['certificate_issuer_username'] else session['issuer_explore']['workspace_contract']
    issuer_name = None if not session['certificate_issuer_username'] else session['issuer_explore']['name']
    # email to Referent/issuer
    payload = {'issuer_email' : session['issuer_email'],
                'issuer_username' : session['certificate_issuer_username'],
                'issuer_workspace_contract' : issuer_workspace_contract,
                'issuer_name' : issuer_name,
                'issuer_type' : session['issuer_type'],
                'certificate_type' : 'recommendation',
                'user_name' : session['name'],
                'user_username' : session['username'],
                'user_workspace_contract' : session['workspace_contract']
                }
    # build JWT
    header = {'alg': 'RS256'}
    key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
    token = jwt.encode(header, payload, key).decode('utf-8')
    # build email
    url = mode.server + 'issue/?token=' + token
    subject = 'You have received a request for recommendation from '+ session['name']
    Talao_message.messageHTML(subject, session['issuer_email'], 'request_certificate', {'name' : session['name'], 'link' : url}, mode)
    # message to user vue
    flash('Your request for Recommendation has been sent.', 'success')
    if session['certificate_issuer_username'] :
        return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + session['certificate_issuer_username'])
    return redirect(mode.server + 'user/')
"""
"""
#@app.route('/user/request_agreement_certificate/', methods=['POST'])
def request_agreement_certificate(mode) :
    check_login()
    # email to Referent/issuer
    issuer_workspace_contract = None if not session['certificate_issuer_username'] else session['issuer_explore']['workspace_contract']
    issuer_name = None if not session['certificate_issuer_username'] else session['issuer_explore']['name']
    payload = {'issuer_email' : session['issuer_email'],
             'certificate_type' : 'agreement',
             'title' : request.form['title'],
             'description' : request.form['description'],
             'service_product_group' :request.form['service_product_group'],
             'valid_until' :  request.form['valid_until'],
             'date_of_issue' : request.form['date_of_issue'],
             'location' : request.form['location'],
             'standard' : request.form['standard'],
             'registration_number' : request.form['registration_number'],
             'user_name' : session['name'],
             'user_username' : session['username'],
             'user_workspace_contract' : session['workspace_contract'],
             'issuer_username' : session['certificate_issuer_username'],
             'issuer_workspace_contract' : issuer_workspace_contract,
             'issuer_name' : issuer_name,
             'issuer_type' : session['issuer_type'],
}
    # build JWT for link
    header = {'alg': 'RS256'}
    key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
    token = jwt.encode(header, payload, key).decode('utf-8')
    # build email
    url = mode.server + 'issue/?token=' + token
    subject = 'You have received a request for an agreement certificate from '+ session['name']
    Talao_message.messageHTML(subject, session['issuer_email'], 'request_certificate', {'name' : session['name'], 'link' : url}, mode)
    # message to user/Talent
    flash('Your request for an Agreement Certificate has been sent.', 'success')
    if session['certificate_issuer_username'] :
        return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + session['certificate_issuer_username'])
    return redirect(mode.server + 'user/')
"""


# add alias (alternative Username for user as a person )
#@app.route('/user/add_alias/', methods=['GET', 'POST'])
def add_alias(mode) :
    check_login()
    if request.method == 'GET' :
        return render_template('add_alias.html', **session['menu'])
    if request.method == 'POST' :
        if ns.username_exist(request.form['access_username'],mode) :
            flash(_('Username already used.') , 'warning')
        else :
            alias_username = request.form['access_username']
            ns.add_alias(alias_username, session['username'], request.form['access_email'], mode)
            flash(_('Alias added for ')+ alias_username , 'success')
        return redirect (mode.server +'user/')


def remove_access(mode) :
    """     remove access (alias/admin/issuer/reviewer
    #@app.route('/user/remove_access/', methods=['GET'])
    """
    check_login()
    if 'alias_to_remove' in request.args :
        alias = request.args['alias_to_remove'].partition('.')[0]
        if ns.remove_alias(alias, mode) :
            flash(alias + _(' has been removed'), 'success')
        else :
            logging.error('remove alias failed')
            flash(_('Operation failed.'), 'danger')
    else  :
        employee = company.Employee(session['host'], mode)
        if employee.delete(request.args['employee_to_remove'].split('.')[0]) :
            flash(request.args['employee_to_remove'].split('.')[0] + _(' has been removed'), 'success')
        else :
            flash(_('Operation failed'), 'danger')
            logging.error('remove manager or reviewer failed = %s',request.args['employee_to_remove'] )
    return redirect (mode.server +'user/')


# Import private key
#@app.route('/user/import_private_key/', methods=['GET', 'POST'])
def import_private_key(mode) :
    check_login()
    if request.method == 'GET' :
        return render_template('import_private_key.html', **session['menu'])
    if request.method == 'POST' :
        priv_key_bytes = decode_hex(request.form['private_key'])
        priv_key = keys.PrivateKey(priv_key_bytes)
        pub_key = priv_key.public_key
        address = pub_key.to_checksum_address()
        if address != session['address'] :
            flash(_('Wrong Private Key.'), 'warning')
            return redirect (mode.server +'user/')
        session['private_key'] = True
        session['private_key_value'] = request.form['private_key']
        privatekey.add_private_key(request.form['private_key'], mode)
        flash(_('Private Key has been imported.'),  'success')
        return redirect (mode.server +'user/')


# Import rsa key
#@app.route('/user/import_rsa_key/', methods=['GET', 'POST'])
def import_rsa_key(mode) :
    check_login()
    if request.method == 'GET' :
        return render_template('import_rsa_key.html', **session['menu'])
    if request.method == 'POST' :
        if 'file' not in request.files :
            flash(_('No file.'), "warning")
            return redirect(mode.server + 'user/')
        myfile = request.files['file']
        filename = secure_filename(myfile.filename)
        myfile.save(os.path.join(RSA_FOLDER + mode.BLOCHAIN, filename))
        filename = "./RSA_key/"+mode.BLOCKCHAIN + '/' + filename
        try :
            with open(filename,'r') as infile :
                key = RSA.import_key(infile.read())
            RSA_public = key.publickey().exportKey('PEM')
        except :
            flash(_('RSA key is not found.'), 'danger')
            return redirect (mode.server +'user/')
        contract = mode.w3.eth.contract(session['workspace_contract'],abi=constante.workspace_ABI)
        identity_key = contract.functions.identityInformation().call()[4]
        if RSA_public == identity_key :
            session['rsa_key'] = True
            session['rsa_key_value'] = key.exportKey('PEM')
            flash(_('RSA Key has been uploaded.'),  'success')
        else :
            flash(_('RSA key default.'), 'danger')
        return redirect (mode.server +'user/')


# request proof of Identity
#@app.route('/user/request_proof_of_identity/', methods=['GET', 'POST'])
def request_proof_of_identity(mode) :
    check_login()
    if request.method == 'GET' :
        return render_template('request_proof_of_identity.html', **session['menu'])
    elif request.method == 'POST' :

        id_file = request.files['id_file']
        selfie_file = request.files['selfie_file']
        address_file = request.files['address_file']

        id_file_name = secure_filename(id_file.filename)
        address_file_name = secure_filename(address_file.filename)
        selfie_file_name = secure_filename(selfie_file.filename)

        id_file.save(os.path.join('./uploads/proof_of_identity', session['username'] + "_ID." + id_file_name))
        address_file.save(os.path.join('./uploads/proof_of_identity', session['username'] + "_Address." + address_file_name))
        selfie_file.save(os.path.join('./uploads/proof_of_identity', session['username'] + "_selfie." + selfie_file_name))

        # email to user/Talent
        subject = "Your request for a proof of Identity has been sent."
        user_email = ns.get_data_from_username(session['username'], mode)['email']
        Talao_message.messageHTML(subject, user_email, 'request_POI_sent', {None}, mode)
        # email with files to Admin
        message = 'Request for proof of identity for ' + session['username'] + '\r\nEmail = ' + request.form.get('email', 'off') + '\r\nPhone = ' + request.form.get('phone', 'off')
        filename_list = [session['username'] + "_ID." + id_file_name, session['username'] + "_selfie." + selfie_file_name]
        Talao_message.message_file([mode.admin], message, 'files for proof of Identity', filename_list, '/home/thierry/Talao/uploads/proof_of_identity/', mode)
        # message to user
        flash(_(' Thank you, we will check your documents soon.'), 'success')
        return redirect (mode.server +'user/')


# add Issuer, they have an ERC725 key with purpose 20002 (or 1) to issue Document (Experience, Certificate)
#@app.route('/user/add_issuer/', methods=['GET', 'POST'])
def add_issuer(mode) :
    check_login()
    if request.method == 'GET' :
        session['referent_username'] = request.args['issuer_username']
        if session['referent_username'] == session['username' ] :
            flash(_('You cannot be the Referent of yourself.'), 'warning')
            return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['referent_username'])
        return render_template('add_referent.html', **session['menu'], referent_username=session['referent_username'])
    elif request.method == 'POST' :
        issuer_workspace_contract = ns.get_data_from_username(session['referent_username'],mode)['workspace_contract']
        issuer_address = contractsToOwners(issuer_workspace_contract, mode)
        if not add_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 20002, mode, synchronous=True) :
            flash(_('transaction failed'), 'danger')
        else :
            issuer_workspace_contract = ownersToContracts(issuer_address, mode)
            session['issuer'].append(ns.get_data_from_username(session['referent_username'], mode))
            # email to issuer
            if session['issuer_explore']['type'] == 'company' :
                subject = "Your company has been chosen by " + session['name'] + " as a Referent."
            else :
                subject = "You have been chosen by " + session['name'] + " as a Referent."
            issuer_email = ns.get_data_from_username(session['referent_username'], mode)['email']
            Talao_message.messageHTML(subject, issuer_email, 'added_referent', {'name' : session['name']}, mode)
            # message to user
            flash(session['referent_username'] + _(' has been added as a Referent. An email has been sent too.'), 'success')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['referent_username'])


# Talao only : Add Key to anyone
#@app.route('/user/add_key/', methods=['GET', 'POST'])
def add_key_for_other(mode) :
    check_login()
    if session['username'] != 'talao' :
        return redirect (mode.server +'user/')
    if request.method == 'GET' :
        return render_template('add_key.html', **session['menu'])
    elif request.method == 'POST' :
        identity_address = request.form.get('identity_address')
        if identity_address :
            identity_workspace_contract = ownersToContracts(identity_address,mode)
        else :
            identity_workspace_contract = ns.get_data_from_username(request.form.get('identity_username'), mode)['workspace_contract']
            identity_address = contractsToOwners(identity_workspace_contract, mode)

        third_party_address = request.form.get('third_party_address')
        if not third_party_address :
            third_party_address = ns.get_data_from_username(request.form.get('third_party_username'),mode)['address']
        key = request.form.get('key')
    if not add_key(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, third_party_address, int(key), mode, synchronous=True) :
        flash(_('transaction failed.'), 'danger')
    else :
        flash(_('Key added.'), 'success')
    return redirect (mode.server +'user/')


# remove issuer
#@app.route('/user/remove_issuer/', methods=['GET', 'POST'])
def remove_issuer(mode) :
    check_login()
    if request.method == 'GET' :
        session['issuer_username_to_remove'] = request.args['issuer_username']
        session['issuer_address_to_remove'] = request.args['issuer_address']
        return render_template('remove_issuer.html', **session['menu'],issuer_name=session['issuer_username_to_remove'])
    elif request.method == 'POST' :
        #address_partner = session['issuer_address_to_remove']
        if not delete_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['issuer_address_to_remove'], 20002, mode) :
            flash (_('transaction failed.'), 'danger')
        else :
            session['issuer'] = [ issuer for issuer in session['issuer'] if issuer['address'] != session['issuer_address_to_remove']]
            flash(_('The Issuer ') + session['issuer_username_to_remove']+ _('  has been removed.'), 'success')
        del session['issuer_username_to_remove']
        del session['issuer_address_to_remove']
        return redirect (mode.server +'user/')


# delete user portfolio, depending on centralized/decentralized
#@app.route('/user/delete_identity/', methods=['GET','POST'])
def delete_identity(mode) :
    check_login()
    if request.method == 'GET' :
        if not session['private_key'] and not session['has_vault_access']:
            flash(_('Cannot delete portrfolio, no token locked.'), 'danger')
            return redirect (mode.server +'user/')
        # decentralized
        elif not session['private_key'] :
            return render_template('wc_delete_identity.html', **session['menu'])
        # centralized
        else :
            return render_template('delete_identity.html', **session['menu'])
    if request.method == 'POST' :
        category = 1001 if session['type'] == 'person' else 2001
        # decentralized mode, destroy workspace is made by wallet
        if not session['private_key'] :
            if request.form.get('status')== 'reject' :
                flash(_('Transaction failed.'), 'danger')
                return redirect (mode.server +'user/')
        # centralized mode, destroy workspace is made by server
        else :
            if not ns.check_password(session['username'], request.form['password'], mode) :
                flash(_('Wrong password.'), 'danger')
                return redirect (mode.server +'user/')
            destroy_workspace(session['workspace_contract'], session['private_key_value'], mode)
        # clean up nameservice
        ns.delete_identity(session['username'], mode, category = category)
        flash(_('Your portfolio has been deleted.'), 'success')
        return redirect (mode.server +'login/')


# photos upload for certificates
#@app.route('/uploads/<filename>')
def send_file(filename, mode):
    print ('send file = ', mode.uploads_path, filename)
    return send_from_directory(mode.uploads_path, filename)


# fonts upload
#@app.route('/fonts/<filename>')
def send_fonts(filename):
    return send_from_directory(FONTS_FOLDER, filename)


# help upload
#@app.route('/help/')
def send_help():
    filename = request.args['file']
    return render_template(filename)


#@app.route('/user/download/', methods=['GET', 'POST'])
def download_file(mode):
    filename = request.args['filename']
    return send_from_directory(mode.uploads_path, filename, as_attachment=True, cache_timeout=1)


#@app.route('/user/download_rsa_key/', methods=['GET', 'POST'])
def download_rsa_key(mode):
    check_login()
    filename = request.args['filename']
    attachment_filename = session['workspace_contract']+ '.key'
    return send_from_directory(RSA_FOLDER + mode.BLOCKCHAIN,filename, attachment_filename = attachment_filename,as_attachment=True,cache_timeout=1)


#@app.route('/talao_ca/', methods=['GET', 'POST'])
def ca(mode):
    talao_x509.generate_CA(mode)
    return send_from_directory('./','talao.pem', as_attachment=True, cache_timeout=1)


#@app.route('/user/download_x509/', methods=['GET', 'POST'])
def download_x509(mode):
    check_login()
    filename = session['workspace_contract'] + '.pem'
    password = ns.get_data_from_username(session['username'], mode)['email']
    if not talao_x509.generate_X509(session['workspace_contract'],password, mode) :
        flash(_('Certificate X.509 not available.'), 'danger')
        return redirect (mode.server +'login/')
    return send_from_directory(mode.uploads_path,filename, as_attachment=True, cache_timeout=1)


#@app.route('/user/download_pkcs12/', methods=['GET', 'POST'])
def download_pkcs12(mode):
    check_login()
    if request.method == 'GET' :
        return render_template('create_password_pkcs12.html', **session['menu'])
    if request.method == 'POST' :
        filename = session['workspace_contract'] + '.p12'
        password = request.form['password']
        if not talao_x509.generate_X509(session['workspace_contract'], password, mode) :
            flash(_('Certificate PKCS12 not available.'), 'danger')
            return redirect (mode.server +'login/')
        return send_from_directory(mode.uploads_path,filename, as_attachment=True, cache_timeout=1)


#@app.route('/user/download_QRCode/', methods=['GET', 'POST'])
def download_QRCode(mode):
    if session['type'] == 'company':
        QRCode.get_QRCode(mode,  mode.server + "board/?workspace_contract=" + session['workspace_contract'])
    elif session['type'] == 'person':
        QRCode.get_QRCode(mode,  mode.server + "resume/?workspace_contract=" + session['workspace_contract'])
    filename = 'External_CV_QRCode.png'
    return send_from_directory(mode.uploads_path,
                               filename, as_attachment=True)


#@app.route('/user/typehead/', methods=['GET', 'POST'])
def typehead() :
    return render_template('typehead.html')


# To manage the navbar search field. !!!! The json file is uploaded once
#@app.route('/user/data/', methods=['GET', 'POST'])
def talao_search(mode) :
    logging.info('upload prefetch file')
    filename = request.args['filename']
    return send_from_directory(mode.uploads_path,
                               filename, as_attachment=True)
