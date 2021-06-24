from flask import session, flash, request, redirect, render_template, abort
from datetime import  datetime
from flask_babel import _

import json
import uuid
import logging
logging.basicConfig(level=logging.INFO)

# dependances
from components import Talao_message, ns, company
from signaturesuite import vc_signature
from protocol import Document


CREDENTIALS = {'experience' : _('Experience credential'),
                     'training' : _('Training certificate'),
                      'recommendation' : _('Recomendation letter'),
                      'work' : _('Employer certificate'),
                      'vacation' : _('Employee vacation time certificate'),
                     'internship' : _('Certificate of participation'),
                      'relocation' : _('Transfer certificate'),
                       'end_of_work' :_('Labour certificate'),
                      'hiring' : _('Promise to hire letter')}

def init_app(app, mode) :
    app.add_url_rule('/company/add_employee/',  view_func=add_employee, methods = ['GET','POST'], defaults={'mode' : mode})
    app.add_url_rule('/user/request_certificate',  view_func=request_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
    app.add_url_rule('/user/request_experience_credential/',  view_func=request_experience_credential, methods = ['POST'], defaults={'mode' : mode})
    app.add_url_rule('/user/request_reference_credential/',  view_func=request_reference_credential, methods = ['POST'], defaults={'mode' : mode})
    app.add_url_rule('/company/dashboard/',  view_func=company_dashboard, methods = ['GET','POST'], defaults={'mode' : mode})
    app.add_url_rule('/company/issue_credential_workflow/',  view_func=issue_credential_workflow, methods = ['GET','POST'], defaults={'mode' : mode})
    app.add_url_rule('/company/add_campaign/',  view_func=add_campaign, methods = ['GET','POST'], defaults={'mode' : mode})
    app.add_url_rule('/company/remove_campaign/',  view_func=remove_campaign, methods = ['GET','POST'], defaults={'mode' : mode})
    return

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
    """
    check_login()
    if request.method == 'GET' :
        session['credential_issuer_username'] = request.args.get('issuer_username')
         # check if campaign exist
        campaign = company.Campaign(session['credential_issuer_username'], mode)
        if not campaign.get_list() :
            flash(_('This company has no active campaign'), 'warning')
            return redirect(mode.server + 'user/')
        return render_template('./issuer/campaign_code.html', **session['menu'], company_name=session['issuer_explore']['name'])


    if request.method == 'POST' :
        if request.form.get('choice') == 'campaign_code' :
            campaign = company.Campaign(session['credential_issuer_username'], mode)
            data = campaign.get(request.form['campaign_code'])
            if not data :
                flash(_('Campaign not found'), 'warning')
                return redirect(mode.server + 'user/issuer_explore/?issuer_username='+ session['credential_issuer_username'])
            credentials_list = ''
            for credential in json.loads(data)['credentials_supported'] :
                credentials_list += """<option value='""" + credential +"""'>""" + CREDENTIALS[credential] + """</option>"""
            return render_template('./issuer/request_certificate.html', **session['menu'], company_name=session['issuer_explore']['name'], credentials_list=credentials_list)

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
            flash(_('credential not available') , 'warning')
            return redirect(mode.server + 'user/')


def request_reference_credential(mode) :
    """ Basic request for experience credential
    """
    check_login()
    # check if campaign exist
    reference = request.form['reference']
    #campaign = company.Campaign(session['credential_issuer_username'], mode)
    #if not campaign.get(reference.split(':')[0]) :
    #    flash(_('This reference does not exist.') , 'warning')
    #    logging.warning('campaign does ot exist')
    #    return render_template('./issuer/request_reference_credential.html', **session['menu'], select=session['select'])

    #workspace_contract_to = ns.get_data_from_username(session['issuer_username'], mode)['workspace_contract']

    # load templates for verifibale credential and init with view form and session
    unsigned_credential = json.load(open('./verifiable_credentials/reference.jsonld', 'r'))
    id = str(uuid.uuid1())
    unsigned_credential["id"] =  "data:" + id
    unsigned_credential[ "credentialSubject"]["id"] = ns.get_did(session['workspace_contract'], mode)
    unsigned_credential[ "credentialSubject"]["name"] = session["name"]
    unsigned_credential[ "credentialSubject"]["offers"]["title"] = request.form['title']
    unsigned_credential[ "credentialSubject"]["offers"]["description"] = request.form['description']
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
    unsigned_credential["credentialSubject"]["author"]["logo"] = session['issuer_explore']['picture']
    unsigned_credential["credentialSubject"]["author"]["name"] = session['issuer_explore']['name']
    unsigned_credential["credentialSubject"]["signatureLines"]["name"] = ""
    #unsigned_credential["credentialSubject"]["reviewerName"] = ""

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
    flash(_('Your request for a reference credential has been sent.'), 'success')

    # clean up and return
    issuer_username = session['credential_issuer_username']
    del session['select']
    return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + issuer_username)


def request_experience_credential(mode) :
    """ Basic request for experience credential
    """
    check_login()
    # load JSON-LD model for ProfessionalExperiencAssessment
    unsigned_credential = json.load(open('./verifiable_credentials/experience_' + session['language'] + '.jsonld', 'r'))

    # update credential with form data
    id = str(uuid.uuid1())
    unsigned_credential["id"] = "data:" + id
    unsigned_credential["credentialSubject"]["id"] = ns.get_did(session['workspace_contract'],mode)
    unsigned_credential["credentialSubject"]["recipient"]["name"] = session['name']
    unsigned_credential["credentialSubject"]["title"] = request.form['title']
    unsigned_credential["credentialSubject"]["description"] = request.form['description']
    unsigned_credential["credentialSubject"]["startDate"] = request.form['start_date']
    unsigned_credential["credentialSubject"]["endDate"] = request.form['end_date']
    unsigned_credential["credentialSubject"]["skills"] = list()
    for skill in request.form['skills'].split(',') :
        unsigned_credential["credentialSubject"]["skills"].append(
            {
            "@type": "Skill",
            "description": skill
            })
    unsigned_credential["credentialSubject"]['author']["logo"] = session['issuer_explore']['picture']
    unsigned_credential["credentialSubject"]['author']["name"] = session['issuer_explore']['name']
    unsigned_credential["credentialSubject"]['signatureLines']["name"] = ""

    # update local issuer database
    manager_username = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['referent']
    credential = company.Credential(session['credential_issuer_username'], mode)
    credential.add(session['username'],
                        request.form['reviewer_username'],
                        manager_username,
                        "drafted",
                        id,
                        json.dumps(unsigned_credential, ensure_ascii=False),
                        request.form['reference'])

    # send an email to reviewer for workflow
    reviewer_email = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['email']
    subject = _('You have received a professional credential from ')+ session['name'] + _(' to review')
    try :
        Talao_message.messageHTML(subject, reviewer_email, 'request_certificate', {'name' : session['name'], 'link' : 'https://talao.co'}, mode)
    except :
        logging.error('email failed')

    # send email to user
    flash(_('Your request for an experience credential has been registered for review.'), 'success')

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
        if "ProfessionalExperienceAssessment" in json.loads(mycredential[5])['type'] :
            subject_link = mode.server + 'resume/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
            title = json.loads(mycredential[5])['credentialSubject']['title'][:20]
            description = json.loads(mycredential[5])['credentialSubject']['description'][:200] + "..."
            type = "ProfessionalExperienceAssessment"

        elif "IdentityCredential" in json.loads(mycredential[5])['type'] :
            subject_link = mode.server + 'resume/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
            title = json.loads(mycredential[5])['credentialSubject']['title'][:20]
            description = json.loads(mycredential[5])['credentialSubject']['description'][:200] + "..."
            type = "IdentityCredential"

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
                <!-- <td><a href=""" + subject_link + """>""" + json.loads(mycredential[5])['credentialSubject']["recipient"]['name'] + """</a></td> -->
                <td>""" + json.loads(mycredential[5])['credentialSubject']["recipient"]['name'] + """</td>
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
    call = (created, user_name, reviewer_name, issuer_name, status, credential, id)
    update = update_verifiable_credential(id, host_name, reviewer_username, issuer_username, status, credential, mode)
    """
    if request.method == 'GET' :
        session['credential_id'] = request.args['id']
        credential = company.Credential(session['host'], mode)
        session['call'] = credential.get_by_id(session['credential_id'])

        # credential cannot be updated if already signed
        field = "disabled" if session['call'][4] == 'signed' or session['role'] in ['admin'] else ""

        # credential is loaded  as dict
        my_credential = json.loads(session['call'][5])['credentialSubject']

        # en attendant 
        if not "ProfessionalExperienceAssessment" in json.loads(session['call'][5])['type'] :
            flash(_('view not yet available'), 'warning')
            return redirect (mode.server +'company/dashboard/')

        skills_str = ""
        for skill in my_credential['skills'] :
            skills_str += skill['description'] + ','
        reviewRecommendation, reviewDelivery, reviewSchedule, reviewCommunication = 0,1,2,3
        return render_template ('./issuer/issue_experience_credential_workflow.html',
                        credential_id=request.args['id'],
                        picturefile = session['picture'],
						clipboard = mode.server  + "board/?did=" + session['did'],
                        **my_credential,
                        recipient_name = my_credential["recipient"]["name"],
                        author_name = my_credential["author"]["name"],
                        signer_name = my_credential["signatureLines"]["name"],
                        scoreRecommendation =  my_credential["review"][reviewRecommendation]["reviewRating"]["ratingValue"],
                        questionRecommendation = my_credential["review"][reviewRecommendation]["reviewBody"],
                        scoreSchedule =  my_credential["review"][reviewSchedule]["reviewRating"]["ratingValue"],
                        questionSchedule = my_credential["review"][reviewSchedule]["reviewBody"],
                        scoreCommunication =  my_credential["review"][reviewCommunication]["reviewRating"]["ratingValue"],
                        questionCommunication = my_credential["review"][reviewCommunication]["reviewBody"],
                        scoreDelivery =  my_credential["review"][reviewDelivery]["reviewRating"]["ratingValue"],
                        questionDelivery = my_credential["review"][reviewDelivery]["reviewBody"],
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
            my_credential['credentialSubject']['signatureLines']['image'] = json.loads(ns.get_personal(manager_workspace_contract, mode))['signature']
            my_credential["issuanceDate"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            my_credential['issuer'] = ns.get_did(session['workspace_contract'], mode)
            signed_credential = vc_signature.sign(my_credential,
                                                session['private_key_value'],
                                                my_credential['issuer'])
            if not signed_credential :
                flash(_('Operation failed '), 'danger')
                logging.error('credential signature failed')
                del session['credential_id']
                del session['call']
                return redirect (mode.server +'company/dashboard/')

            # update local company database
            credential = company.Credential(session['host'], mode)
            signer = session['employee'] if session['employee'] else session['host']
            credential.update(session['credential_id'],
                                        session['call'][2],
                                        signer,
                                        "signed",
                                        signed_credential,
                                        )

            # ulpoad credential to repository with company key signature
            subject_username = session['call'][1]
            subject = ns.get_data_from_username(subject_username, mode)
            my_certificate = Document('certificate')
            try :
                doc_id = my_certificate.relay_add(subject['workspace_contract'],json.loads(signed_credential), mode, privacy='public')[0]
            except :
                doc_id = None
            if not doc_id :
                flash(_('Add credential to repository failed '), 'danger')
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
            subject = _('You have received a professional credential from ') + subject_name + ' to issue'
            try :
                Talao_message.messageHTML(subject, issuer_email, 'request_certificate', {'name' : subject_name, 'link' : 'https://talao.co'}, mode)
            except :
                logging.error('email error')

            flash(_('Credential has been reviewed and validated'), 'success')

        # all exits except delete and back
        del session['credential_id']
        del session['call']
        return redirect (mode.server +'company/dashboard/')


def get_form_data(my_credential, form) :
    """
    This function updates credential with form data
    """
    reviewRecommendation, reviewDelivery, reviewSchedule, reviewCommunication = 0,1,2,3
    my_credential['credentialSubject']["review"][reviewRecommendation]["reviewRating"]["ratingValue"] = form["scoreRecommendation"]
    my_credential['credentialSubject']["review"][reviewSchedule]["reviewRating"]["ratingValue"] = form["scoreSchedule"]
    my_credential['credentialSubject']["review"][reviewDelivery]["reviewRating"]["ratingValue"] = form["scoreDelivery"]
    my_credential['credentialSubject']["review"][reviewCommunication]["reviewRating"]["ratingValue"] = form["scoreCommunication"]
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
    my_credential['credentialSubject']["signatureLines"]['name'] = form.get('managerName', " ")
    return


def add_campaign(mode) :
    """ create a new campaign 
    """
    check_login()
    if request.method == 'GET' :
        return render_template('./issuer/add_campaign.html', **session['menu'])
    if request.method == 'POST' :
        new_campaign = company.Campaign(session['username'], mode)
        data = {'description' : request.form['description'],
                'nb_subject' : 0,
                'startDate' : '',
                'endDate' : '',
                'credentials_supported' : []}
        new_campaign.add(request.form['name'], json.dumps(data, ensure_ascii=False))
        flash(_('New campaign added'), 'success')
        return redirect(mode.server + 'user/')


def remove_campaign(mode) :
    """ create a new campaign 
    """
    check_login()
    new_campaign = company.Campaign(session['username'], mode)
    new_campaign.delete(request.args['campaign_name'])
    flash(_('Campaign removed'), 'success')
    return redirect(mode.server + 'user/')