from flask import session, flash, request, redirect, render_template, abort
from datetime import  date, datetime
import json
import random
import uuid
import logging
logging.basicConfig(level=logging.INFO)

# dependances
from components import Talao_message, Talao_ipfs, ns, sms, directory, privatekey, company
from signaturesuite import RsaSignatureSuite2017, vc_signature, helpers
import constante
from protocol import ownersToContracts, contractsToOwners, token_balance, Document, read_profil


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
            return render_template('./issuer/add_issuer.html', **session['menu'])

        elif  session['role_to_add'] == 'reviewer' :
            issuer_list = employee.get_list('issuer', 'all')
            issuer_select = ""
            for issuer in issuer_list :
                issuer_select += """<option value=""" + issuer['username'].split('.')[0]  + """>""" + issuer['username'].split('.')[0] + """</option>"""
            return render_template('./issuer/add_reviewer.html', **session['menu'], issuer_select=issuer_select)

        elif  session['role_to_add'] == 'admin' :
            return render_template('./issuer/add_admin.html', **session['menu'])

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
    #@app.route('/user/request_certificate/', methods=['GET', 'POST'])
    """
    check_login()
    if request.method == 'GET' :
        session['credential_issuer_username'] = request.args.get('issuer_username')
         # check if campaign exist
        campaign = company.Campaign(session['credential_issuer_username'], mode)
        if not campaign.get_list() :
            flash('This company as no active campaign', 'warning')
            return redirect(mode.server + 'user/')
        return render_template('./issuer/request_certificate.html', **session['menu'])

    if request.method == 'POST' :
        select = ""
        reviewer = company.Employee(session['credential_issuer_username'], mode) 
        reviewer_list = reviewer.get_list('reviewer', 'all')
        for reviewer in reviewer_list :
            session['select'] = select + """<option value=""" + reviewer['username'].split('.')[0]  + """>""" + reviewer['username'].split('.')[0] + """</option>"""

        if request.form['certificate_type'] == 'experience' :
            return render_template('./issuer/request_experience_credential.html', **session['menu'], select=session['select'])

        elif request.form['certificate_type'] == 'reference' :
            return render_template('./issuer/request_reference_credential.html', **session['menu'], select=session['select'])

        else :
            flash('credential not available' , 'warning')
            return redirect(mode.server + 'user/')


def request_reference_credential(mode) :
    """ Basic request for experience credential

    @app.route('/user/request_reference_credential/', methods=['POST'])

    """
    check_login()

    # check if campaign exist
    reference = request.form['reference']
    campaign = company.Campaign(session['credential_issuer_username'], mode)
    if not campaign.get(reference.split(':')[0]) :
        flash('This reference does not exist.' , 'warning')
        logging.warning('campaign does ot exist')
        return render_template('./issuer/request_reference_credential.html', **session['menu'], select=session['select'])

    workspace_contract_to = ns.get_data_from_username(session['issuer_username'], mode)['workspace_contract']

    # load templates for verifibale credential and init with view form and session
    unsigned_credential = json.load(open('./verifiable_credentials/reference.jsonld', 'r'))
    id = str(uuid.uuid1())
    unsigned_credential["id"] =  "data:" + id
    unsigned_credential[ "credentialSubject"]["id"] = ns.get_did(session['workspace_contract'], mode)
    unsigned_credential[ "credentialSubject"]["name"] = session["name"]
    unsigned_credential[ "credentialSubject"]["offers"]["title"] = request.form['title']
    unsigned_credential[ "credentialSubject"]["offers"]["description"] = request.form['description']
    print('request form description= ', request.form['description'])
    unsigned_credential[ "credentialSubject"]["offers"]["startDate"] = request.form['startDate']
    unsigned_credential[ "credentialSubject"]["offers"]["endDate"] = request.form['endDate']
    unsigned_credential[ "credentialSubject"]["offers"]["price"] = request.form['budget']
    unsigned_credential[ "credentialSubject"]["offers"]["location"] = request.form['location']
    unsigned_credential[ "credentialSubject"]["offers"]["staff"] = request.form['staff']

    for skill in request.form['competencies'].split(',') :
        unsigned_credential["credentialSubject"]["offers"]["skills"].append(
            {
            "@type": "DefinedTerm",
            "description": skill
            })
    unsigned_credential["credentialSubject"]["companyLogo"] = session['issuer_explore']['picture']
    unsigned_credential["credentialSubject"]["companyName"] = session['issuer_explore']['name']
    unsigned_credential["credentialSubject"]["managerName"] = ""
    unsigned_credential["credentialSubject"]["reviewerName"] = ""

    print('unsigned credential = ', unsigned_credential)

    # update local issuer database
    manager_username = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['referent']
    credential = company.Credential(session['credential_issuer_username'], mode)
    credential.add(session['username'],
                        request.form['reviewer_username'],
                        manager_username,
                        "drafted",
                        id,
                        json.dumps(unsigned_credential),
                        reference)

    # send an email to reviewer for workflow
    reviewer_email = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['email']
    subject = 'You have received a reference credential from '+ session['name'] + ' to review'
    try :
        Talao_message.messageHTML(subject, reviewer_email, 'request_certificate', {'name' : session['name'], 'link' : 'https://talao.co'}, mode)
    except :
        logging.error('email failed')

    # send email to user
    flash('Your request for a reference credential has been snt.', 'success')

    # clean up and return
    issuer_username = session['credential_issuer_username']
    del session['select']
    return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + issuer_username)



def request_experience_credential(mode) :
    """ Basic request for experience credential

    @app.route('/user/request_experience_certificate/', methods=['POST'])

    """
    check_login()

    # check if campaign exist
    reference = request.form['reference']
    campaign = company.Campaign(session['credential_issuer_username'], mode)
    if not campaign.get(reference.split(':')[0]) :
        flash('This reference does not exist.' , 'warning')
        logging.warning('campaign does ot exist')
        return render_template('./issuer/request_experience_credential.html', **session['menu'], select=session['select'])

    # load templates for verifiable credential template
    unsigned_credential = json.load(open('./verifiable_credentials/experience.jsonld', 'r'))

    # update credential with form data
    id = str(uuid.uuid1())
    method = ns.get_method(session['workspace_contract'], mode)
    for did in ns.get_did(session['workspace_contract'],mode) :
        if method == did.split(':')[1] :
            subject_did = did
            break
    unsigned_credential["id"] = "data:" + id
    unsigned_credential["credentialSubject"]["id"] = subject_did
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
    manager_username = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['referent']
    credential = company.Credential(session['credential_issuer_username'], mode)
    credential.add(session['username'],
                        request.form['reviewer_username'],
                        manager_username,
                        "drafted",
                        id,
                        json.dumps(unsigned_credential),
                        reference)

    # send an email to reviewer for workflow
    reviewer_email = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['email']
    subject = 'You have received a professional credential from '+ session['name'] + ' to review'
    try :
        Talao_message.messageHTML(subject, reviewer_email, 'request_certificate', {'name' : session['name'], 'link' : 'https://talao.co'}, mode)
    except :
        logging.error('email failed')

    # send email to user
    flash('Your request for an experience credential has been registered for review.', 'success')

    # clean up and return
    issuer_username = session['credential_issuer_username']
    del session['select']
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
        return render_template('./issuer/company_dashboard.html',
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
        return render_template('./issuer/company_dashboard.html',
                                 **session['menu'],
                                credential_list=credential_list,
                                drafted=drafted,
                                reviewed=reviewed,
                                signed=signed,
                                reviewer_select=reviewer_select,
                                manager_select=issuer_select)


def credential_list_html(host, issuer_username, reviewer_username, status, mode) :
    """ build the html list
    return the table list to display in dashboard in html
    """
    credential = company.Credential(host, mode)
    mylist = credential.get(issuer_username, reviewer_username, status)
    credential_list = ""
    for mycredential in mylist :
        if json.loads(mycredential[5])['credentialSubject']['credentialCategory'] == "experience" :
            subject_link = mode.server + 'resume/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
            title = json.loads(mycredential[5])['credentialSubject']['title'][:20]
            description = json.loads(mycredential[5])['credentialSubject']['description'][:200] + "..."
            type = json.loads(mycredential[5])['credentialSubject']['credentialCategory'].capitalize()

        elif json.loads(mycredential[5])['credentialSubject']['credentialCategory'] == "reference" :
            subject_link = mode.server + 'board/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
            title = json.loads(mycredential[5])['credentialSubject']['offers']['title'][:20]
            description = json.loads(mycredential[5])['credentialSubject']['offers']['description'][:200] +"..."
            type = json.loads(mycredential[5])['credentialSubject']['credentialCategory'].capitalize()

        elif "IdentityCredential" in json.loads(mycredential[5])['type'] :
            subject_link = mode.server + 'resume/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
            type = "Identity"
            title = description = "N/A"

        credential = """<tr>
                <td><a href=/company/issue_credential_workflow/?id=""" + mycredential[6] + """> """ + mycredential[6][:2] + '...' + mycredential[6][-2:]  + """</a></td>
                <!-- <td><a href=""" + subject_link + """>""" + json.loads(mycredential[5])['credentialSubject']['name'] + """</a></td> -->
                <td>""" + json.loads(mycredential[5])['credentialSubject']['name'] + """</td>
                <td>""" + mycredential[7] + """</td>
                <td>""" + title + """...</td>
                <td>""" + description + """</td>
                <td>""" + mycredential[0][:10] + """</td>
                <td>""" + type + """</td>
                <td>""" + mycredential[2] + """</td>
                <td>""" + mycredential[3] + """ </td>
                <td>""" + mycredential[4] + """</td>
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

        # credential is loaded  as dict
        my_credential = json.loads(session['call'][5])['credentialSubject']

        if my_credential["credentialCategory"] != 'experience' :
            flash('view not yet available', 'warning')
            return redirect (mode.server +'company/dashboard/')

        skills_str = ""
        for skill in my_credential['skills'] :
            skills_str += skill['description'] + ','
        return render_template ('./issuer/issue_experience_credential_workflow.html',
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
            my_credential['credentialSubject']['managerSignature'] = json.loads(ns.get_personal(manager_workspace_contract, mode))['signature']
            my_credential["issuanceDate"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            my_credential['issuer'] = ns.get_did(session['workspace_contract'], mode)
            signed_credential = vc_signature.sign(my_credential,
                                                session['private_key_value'],
                                                my_credential['issuer'])

            # update local company database
            credential = company.Credential(session['host'], mode)
            credential.update(session['credential_id'],
                                        session['call'][2],
                                        session['employee'],
                                        "signed",
                                        signed_credential,
                                        )

            # ulpoad credential to repository with company key signature
            subject_username = session['call'][1]
            subject = ns.get_data_from_username(subject_username, mode)
            my_certificate = Document('certificate')
            doc_id = my_certificate.add(session['address'],
                                        session['workspace_contract'],
                                        subject['address'],
                                        subject['workspace_contract'],
                                        session['private_key_value'],
                                        json.loads(signed_credential),
                                        mode,
                                        privacy='public',
                                        synchronous=False)[0]
            if not doc_id :
                flash('Operation failed ', 'danger')
                logging.error('certificate to repository failed')
            else :
                flash('The credential has been added to the user repository', 'success')
            """
            # send an email to user
            link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + subject['workspace_contract'][2:] + ':document:' + str(doc_id)
            try :
                Talao_message.messageHTML('Your professional credential has been issued.', subject['email'], 'certificate_issued', {'username': session['name'], 'link': link}, mode)
            except :
                logging.error('email to subject failed')
            """
            # store signed credential on server
            try :
                filename = session['credential_id'] + '_credential.jsonld'
                path = "./signed_credentials/"
                with open(path + filename, 'w') as outfile :
                    json.dump(json.loads(signed_credential), outfile, indent=4, ensure_ascii=False)
            except :
                logging.error('signed credential not stored')

            # send email to user
            try :
                signature = '\r\n\r\n\r\n\r\nThe Talao team.\r\nhttps://talao.io/'
                text = "\r\nHello\r\nYou will find attached your professional credential signed by your issuer." + signature
                Talao_message.message_file(subject['email'], text, "Your professional credential", [filename], path, mode)
            except :
                logging.error('email credential to subject failed')

            # TODO delete credential
        # credential has been reviewed
        elif request.form['exit'] == 'validate' :
            # update local database
            credential = company.Credential(session['host'], mode)
            credential.update(session['credential_id'],
                                        session['employee'],
                                        session['call'][3],
                                        "reviewed",
                                        json.dumps(my_credential, ensure_ascii=False),
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
    This function updates credential with form data
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


def add_campaign(mode) :
    """ create a new campaign 
    """
    check_login()
    if request.method == 'GET' :
        return render_template('./issuer/add_campaign.html', **session['menu'])
    if request.method == 'POST' :
        new_campaign = company.Campaign(session['username'], mode)
        new_campaign.add(request.form['name'], request.form['description'])
        flash('New campaign added', 'success')
        return redirect(mode.server + 'user/')


def remove_campaign(mode) :
    """ create a new campaign 
    """
    check_login()
    new_campaign = company.Campaign(session['username'], mode)
    new_campaign.delete(request.args['campaign_name'])
    flash('Campaign removed', 'success')
    return redirect(mode.server + 'user/')