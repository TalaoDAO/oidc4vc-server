from flask import session, flash, request, redirect, render_template, abort
from datetime import  date, datetime
import json
import random
import uuid
import logging
logging.basicConfig(level=logging.INFO)

# dependances
from components import Talao_message, Talao_ipfs, ns, sms, directory, privatekey, company
from signaturesuite import RsaSignatureSuite2017, EcdsaSecp256k1RecoverySignature2020, helpers
import constante
from protocol import ownersToContracts, contractsToOwners, save_image,  token_balance, Document, read_profil, get_image


def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if not session.get('workspace_contract') and not session.get('username') :
		abort(403)
	return True


def add_employee(mode) :
    """
    # add admin or issuer or reviewer in table issuer of host
    #@app.route('/user/add_employee/', methods=['GET', 'POST'])
     add_employee(employee_name, identity_name, role, referent, host_name, email, mode, phone=None, password='identity') :
    """
    check_login()

    # init employee db access
    employee = company.Employee(session['host'], mode)

    if request.method == 'GET' :
        session['role_to_add'] = request.args.get('role_to_add')

        if  session['role_to_add'] == 'issuer' :
            return render_template('./workflow/add_issuer.html', **session['menu'])

        elif  session['role_to_add'] == 'reviewer' :
            issuer_list = employee.get_list('issuer', 'all')
            issuer_select = ""
            for issuer in issuer_list :
                issuer_select += """<option value=""" + issuer['username'].split('.')[0]  + """>""" + issuer['username'].split('.')[0] + """</option>"""
            return render_template('./workflow/add_reviewer.html', **session['menu'], issuer_select=issuer_select)

        elif  session['role_to_add'] == 'admin' :
            return render_template('./workflow/add_admin.html', **session['menu'])

    if request.method == 'POST' :

        # check if username is new
        if ns.username_exist(request.form['employee_username'],mode)  or employee.exist(request.form['employee_username']) :
            flash('This username is already used, lets try an another one !' , 'warning')
        else :
            employee_username = request.form['employee_username']
            identity_username = request.form['identity_username']

            # let check  who is the referent 
            if session['role_to_add'] == 'reviewer' :
                if session['role'] in ['admin', 'creator'] :
                    referent = request.form['referent_username']
                else :
                    referent = session['employee']
            else :
                referent = None

            #add_employee(employee_name, identity_name, role, referent, host_name, email, mode, phone=None, password='identity') :
            if employee.add(employee_username, identity_username, session['role_to_add'], referent, request.form['employee_email']) :
                flash(employee_username.lower() + " has been added as " + session['role_to_add'] , 'success')

        # clean up
        del session['role_to_add']
        return redirect (mode.server +'user/')


def request_certificate(mode) :
    """ The request call comes from the Search Bar or from the Identity page

    request credential to be completed with email

    #@app.route('/user/request_certificate/', methods=['GET', 'POST'])
    """
    check_login()

    if request.method == 'GET' :
        if session['issuer_username'] != request.args.get('issuer_username') :
            logging.warning('problem init')
            return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])

        if not privatekey.get_key(session['issuer_explore']['address'], 'private_key', mode) :
            flash('This issuer cannot issue Certificates.', 'warning')
            logging.warning('no private key available')
            return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])

        return render_template('request_certificate.html', **session['menu'])

    if request.method == 'POST' :
        # From Menu, if issuer does not exist, we request to user his email and type.
        if not session['issuer_username'] :
            session['issuer_email'] = request.form['issuer_email']
            session['issuer_type'] = 'person' if request.form['certificate_type']=='personal_recommendation' else 'company'

            # we check if issuer exists
            username_list = ns.get_username_list_from_email(request.form['issuer_email'], mode)
            if username_list :
                msg = 'This email is already used by Identity(ies) : ' + ", ".join(username_list) + ' . Use the Search Bar to check their identities and request a certificate.'
                flash(msg , 'warning')
                return redirect(mode.server + 'user/')
        else :
            session['issuer_type'] = session['issuer_explore']['type']
            session['issuer_email'] = ns.get_data_from_username(session['certificate_issuer_username'], mode)['email']

        select = ""
        employee = company.Employee(session['host'], mode) 
        reviewer_list = employee.get_list(session['certificate_issuer_username'], 'reviewer', 'all')
        for reviewer in reviewer_list :
            session['select'] = select + """<option value=""" + reviewer['username'].split('.')[0]  + """>""" + reviewer['username'].split('.')[0] + """</option>"""

        if request.form['certificate_type'] == 'experience' :
            return render_template('./workflow/request_experience_certificate.html', **session['menu'], select=session['select'])

        elif request.form['certificate_type'] in ['personal_recommendation', 'company_recommendation'] :
            return render_template('request_recommendation_certificate.html', **session['menu'])

        elif request.form['certificate_type'] == 'agreement' :
            return render_template('request_agreement_certificate.html', **session['menu'])

        elif request.form['certificate_type'] == 'reference' :
            return render_template('request_reference_certificate.html', **session['menu'])

        else :
            flash('certificate not available' , 'warning')
            return redirect(mode.server + 'user/')


def request_experience_certificate(mode) :
    """ Basic request for experience credential

    @app.route('/user/request_experience_certificate/', methods=['POST'])

    """
    check_login()

    # check if campaign exist
    reference = request.form['reference']
    try :
        my_campaign = reference.split(':')[0]
    except :
        flash('This reference is incorrect.' , 'warning')
        logging.warning('reference malformed')
        return render_template('./workflow/request_experience_certificate.html', **session['menu'], select=session['select'])
    campaign = company.Campaign(session['certificate_issuer_username'], mode)
    if not campaign.get(my_campaign, mode) :
        flash('This reference does not exist.' , 'warning')
        logging.warning('campaign does ot exist')
        return render_template('./workflow/request_experience_certificate.html', **session['menu'], select=session['select'])

    # load templates for verifiable credential
    unsigned_credential = json.load(open('./verifiable_credentials/experience.jsonld', 'r'))

    # update credential with form data
    id = str(uuid.uuid1())
    method = ns.get_method(session['workspace_contract'], mode)
    unsigned_credential["id"] = "data:" + id
    unsigned_credential["credentialSubject"]["id"] = helpers.ethereum_pvk_to_DID(session['private_key_value'], method)
    unsigned_credential["credentialSubject"]["name"] = session['name']
    unsigned_credential["credentialSubject"]["title"] = request.form['title']
    unsigned_credential["credentialSubject"]["description"] = request.form['description']
    unsigned_credential["credentialSubject"]["startDate"] = request.form['start_date']
    unsigned_credential["credentialSubject"]["endDate"] = request.form['end_date']
    unsigned_credential["credentialSubject"]["skills"] = list()
    for skill in request.form['skills'].split(',') :
        unsigned_credential["credentialSubject"]["skills"].append(
            {
            "@type": "DefinedTerm",
            "description": skill
            })
    unsigned_credential["credentialSubject"]["companyLogo"] = session['issuer_explore']['picture']
    unsigned_credential["credentialSubject"]["companyName"] = session['issuer_explore']['name']
    unsigned_credential["credentialSubject"]["managerName"] = ""
    unsigned_credential["credentialSubject"]["reviewerName"] = ""

    # update local issuer database
    manager_username = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['issuer_username'], mode)['referent']
    credential = company.Credential(session['host'], mode)
    credential.add(session['username'],
                        request.form['reviewer_username'],
                        manager_username,
                        "drafted",
                        id,
                        json.dumps(unsigned_credential),
                        reference)

    # send an email to reviewer for workflow
    reviewer_email = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['issuer_username'], mode)['email']
    subject = 'You have received a professional credential from '+ session['name'] + ' to review'
    try :
        Talao_message.messageHTML(subject, reviewer_email, 'request_certificate', {'name' : session['name'], 'link' : 'https://talao.co'}, mode)
    except :
        logging.error('email failed')

    # send email to user
    flash('Your request for an experience credential has been registered for review.', 'success')

    # clean up and return
    issuer_username = session['issuer_username']
    del session['select']
    del session['issuer_username']
    del session['issuer_email']
    del session['issuer_type']
    return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + issuer_username)


def company_dashboard(mode) :
    """
    # @route /company/dashboard/
    """
    # created, user_name, reviewer_name, issuer_name, status, credential, id
    issuer_select = ""
    employee = company.Employee(session['host'], mode)
    issuer_list = employee.get_list('issuer', 'all')
    for issuer in issuer_list :
        issuer_select += """<option value=""" + issuer['username'].split('.')[0]  + """>""" + issuer['username'].split('.')[0] + """</option>"""

    reviewer_select = ""
    reviewer_list = employee.get_list('reviewer', 'all')
    for reviewer in reviewer_list :
        reviewer_select += """<option value=""" + reviewer['username'].split('.')[0]  + """>""" + reviewer['username'].split('.')[0] + """</option>"""

    if request.method == 'GET' :

        # init of dashboard display / role
        if session['role'] == 'reviewer' :
            issuer_query = 'all'
            reviewer_query = session['employee']
        elif session['role'] == 'issuer' :
            issuer_query = session['employee']
            reviewer_query = 'all'
        else :
            issuer_query = 'all'
            reviewer_query = 'all'

        # init of dashboard display / credential status
        signed = drafted = reviewed = ""
        if session['role'] == 'issuer' :
            reviewed = "checked"
            status = ("reviewed","","")
        elif session['role'] == 'reviewer' :
            drafted = 'checked'
            status = ('drafted',"","")
        else :
            drafted =  reviewed = signed = "checked"
            status = ('drafted', 'reviewed', 'signed')

        # display dashboard
        credential_list = credential_list_html(session['host'], issuer_query, reviewer_query, status, mode)
        return render_template('./workflow/company_dashboard.html',
                                **session['menu'],
                                credential_list=credential_list,
                                drafted=drafted,
                                reviewed=reviewed,
                                signed=signed,
                                reviewer_select=reviewer_select,
                                manager_select=issuer_select)

    if request.method == 'POST' :

        # update dashboard with select
        status = (request.form.get('draftedbox', ""), request.form.get('reviewedbox', ""), request.form.get('signedbox', ""))
        drafted = "checked" if request.form.get('draftedbox') else ""
        signed = "checked" if request.form.get('signedbox') else ""
        reviewed = "checked" if request.form.get('reviewedbox') else ""

        if session['role'] == 'reviewer' :
            issuer_query = 'all'
            reviewer_query = session['employee']
        else :
            issuer_query = request.form['issuer']
            reviewer_query = request.form['reviewer']
        credential_list = credential_list_html(session['host'], issuer_query, reviewer_query, status, mode)
        return render_template('./workflow/company_dashboard.html',
                                 **session['menu'],
                                credential_list=credential_list,
                                drafted=drafted,
                                reviewed=reviewed,
                                signed=signed,
                                reviewer_select=reviewer_select,
                                manager_select=issuer_select)


def credential_list_html(host, issuer_username, reviewer_username, status, mode) :
    """ helper

    return the table list to display in dashboard in html

    """
    credential = company.Credential(host, mode)
    mylist = credential.get(issuer_username, reviewer_username, status)
    credential_list = ""
    if mylist :
        for mycredential in mylist :
            subject_resume_link = mode.server + 'resume/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
            credential = """<tr>
                <td><a href=/company/issue_credential_workflow/?id=""" + mycredential[6] + """> """ + mycredential[6][:2] + '...' + mycredential[6][-2:]  + """</a></td>
                <td><a href=""" + subject_resume_link + """>""" + json.loads(mycredential[5])['credentialSubject']['name'] + """</a></td>
                <td>""" + json.loads(mycredential[5])['credentialSubject']['title'][:20] + """...</td>
                <td>""" + json.loads(mycredential[5])['credentialSubject']['description'] + """</td>
                <td>""" + mycredential[7] + """</td>
                <td>""" + mycredential[0][:10] + """</td>
                <td>""" + json.loads(mycredential[5])['credentialSubject']['credentialCategory'].capitalize() + """</td>
                <td>""" + mycredential[2] + """</td>
                <td>""" + mycredential[3] + """ </td>
                <td>""" + mycredential[4] +  """</td>
            </tr>"""
            credential_list += credential
    return credential_list


def issue_credential_workflow(mode) :
    """
    @route /company/issue_credential_workflow/?id=xxxx
    call = (created, user_name, reviewer_name, issuer_name, status, credential, id)
    update = update_verifiable_credential(id, host_name, reviewer_username, issuer_username, status, credential, mode)
    """
    if request.method == 'GET' :
        session['credential_id'] = request.args['id']
        credential = company.Credential(session['host'], mode)
        session['call'] = credential.get_by_id(session['credential_id'])

        # credential cannot be updated if already signed
        field = "disabled" if session['call'][4] == 'signed' or session['role'] in ['admin', 'creator'] else ""

        # credential is loaded as a dict and pass to view as field have same names
        my_credential = json.loads(session['call'][5])['credentialSubject']
        skills_str = ""
        for skill in my_credential['skills'] :
            skills_str += skill['description'] + ','
        return render_template ('./workflow/issue_experience_certificate_workflow.html',
                        credential_id=request.args['id'],
                        picturefile = session['picture'],
						clipboard = mode.server  + "board/?did=" + session['did'],
                        **my_credential,
                        scoreRecommendation =  my_credential["reviewRecommendation"]["reviewRating"]["ratingValue"],
                        questionRecommendation = my_credential["reviewRecommendation"]["reviewBody"],
                        scoreSchedule =  my_credential["reviewSchedule"]["reviewRating"]["ratingValue"],
                        questionSchedule = my_credential["reviewSchedule"]["reviewBody"],
                        scoreCommunication =  my_credential["reviewCommunication"]["reviewRating"]["ratingValue"],
                        questionCommunication = my_credential["reviewCommunication"]["reviewBody"],
                        scoreDelivery =  my_credential["reviewDelivery"]["reviewRating"]["ratingValue"],
                        questionDelivery = my_credential["reviewDelivery"]["reviewBody"],
                        skills_str= skills_str,
                        field= field,
                        )

    if request.method == 'POST' :
        # credential is removed from database
        if request.form['exit'] == 'delete' :
            credential = company.Credential(session['host'], mode)
            credential.delete(session['credential_id'])
            del session['credential_id']
            del session['call']
            return redirect (mode.server +'company/dashboard/')

        # nothing is done
        if request.form['exit'] == 'back' :
            del session['credential_id']
            del session['call']
            return redirect (mode.server +'company/dashboard/')

        # get form data to update credential
        my_credential =  json.loads(session['call'][5])
        get_form_data(my_credential, request.form)

        # update without review and signature
        if request.form.get('exit') == 'update' :
            credential = company.Credential(session['host'], mode)
            credential.update(session['credential_id'],
                                        session['call'][2],
                                        session['call'][3],
                                        session['call'][4],
                                        json.dumps(my_credential),
                                        )

        # credential has been signed by issuer
        elif request.form.get('exit') == 'sign' :

            # sign credential with company key
            manager_workspace_contract = ns.get_data_from_username(session['username'], mode)['identity_workspace_contract']
            my_credential['credentialSubject']['managerSignature'] = get_image(manager_workspace_contract, 'signature', mode)
            my_credential["issuanceDate"] = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            my_credential['issuer'] = helpers.ethereum_pvk_to_DID(session['private_key_value'], session['method'])
            signed_credential = EcdsaSecp256k1RecoverySignature2020.sign(my_credential, session['private_key_value'], method=session['method'])

            # update local company database
            credential = company.Credential(session['host'], mode)
            credential.update(session['credential_id'],
                                        session['call'][2],
                                        session['employee'],
                                        "signed",
                                        signed_credential,
                                        )

            # ulpoad credential to repository repository with company key signature
            subject_username = session['call'][1]
            db_ns_call = ns.get_data_from_username(subject_username, mode)
            subject_workspace_contract = db_ns_call['workspace_contract']
            subject_address = db_ns_call['address']
            subject_email = db_ns_call['email']
            my_certificate = Document('certificate')
            doc_id = my_certificate.add(session['address'],
                        session['workspace_contract'],
                        subject_address,
                        subject_workspace_contract,
                        session['private_key_value'],
                        json.loads(signed_credential),
                        mode,
                        mydays=0,
                        privacy='public',
                         synchronous=True)[0]
            if not doc_id :
                flash('Operation failed ', 'danger')
                logging.error('certificate to repository failed')
            else :
                flash('The credential has been added to the user repository', 'success')
            # send an email to user
            link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + subject_workspace_contract[2:] + ':document:' + str(doc_id)
            try :
                Talao_message.messageHTML('Your professional credential has been issued.', subject_email, 'certificate_issued', {'username': session['name'], 'link': link}, mode)
            except :
                logging.error('email to subject failed')

            # store signed credential on server
            try :
                filename = session['credential_id'] + '_credential.jsonld'
                path = "./signed_credentials/"
                fp = open(path + filename, 'w')
                fp.write((json.dumps(json.loads(signed_credential), indent=4, ensure_ascii=False)))
                fp.close()
            except :
                logging.error('store credential on server failed')

            # send email to user
            try :
                signature = '\r\n\r\n\r\n\r\nThe Talao team.\r\nhttps://talao.io/'
                text = "\r\nHello\r\nYou will find attached your professional credential signed by your issuer." + signature
                Talao_message.message_file([subject_email], text, "Your professional credential", [filename], path, mode) 
            except :
                logging.error('email credential to subject failed')

            # TODO delete credential
        # credential has been reviewed
        elif request.form['exit'] == 'validate' :
            # update local database
            credential = company.Credential[session['host'], mode]
            credential.update(session['credential_id'],
                                        session['employee'],
                                        session['call'][3],
                                        "reviewed",
                                        json.dumps(my_credential),
                                        )
            # send an email to issuer to go forward
            issuer_email = ns.get_data_from_username(session['referent'] + '.' + session['host'], mode)['email']
            subject_name = my_credential['credentialSubject']['name']
            subject = 'You have received a professional credential from ' + subject_name + ' to issue'
            try :
                Talao_message.messageHTML(subject, issuer_email, 'request_certificate', {'name' : subject_name, 'link' : 'https://talao.co'}, mode)
            except :
                logging.error('email error')

            flash('Credential has been reviewed and validated', 'success')

        # all exits except delete and back
        del session['credential_id']
        del session['call']
        return redirect (mode.server +'company/dashboard/')


def get_form_data(my_credential, form) :
    """
    This function udates credential from the form depending on the credential
    """
    my_credential['credentialSubject']["reviewRecommendation"]["reviewRating"]["ratingValue"] = form["scoreRecommendation"]
    my_credential['credentialSubject']["reviewSchedule"]["reviewRating"]["ratingValue"] = form["scoreSchedule"]
    my_credential['credentialSubject']["reviewDelivery"]["reviewRating"]["ratingValue"] = form["scoreDelivery"]
    my_credential['credentialSubject']["reviewCommunication"]["reviewRating"]["ratingValue"] = form["scoreCommunication"]
    my_credential['credentialSubject']['title'] = form['title']
    my_credential['credentialSubject']['description'] = form['description']
    my_credential['credentialSubject']['startDate'] = form['startDate']
    my_credential['credentialSubject']['endDate'] = form['endDate']
    my_credential['credentialSubject']['skills'] = list()
    for skill in form['skills_str'].split(',') :
        if skill :
            my_credential["credentialSubject"]["skills"].append(
                            {
                            "@type": "DefinedTerm",
                            "description": skill
                            })
    my_credential['credentialSubject']['managerName'] = form['managerName']
    my_credential['credentialSubject']['reviewerName'] = form['reviewerName']
    return