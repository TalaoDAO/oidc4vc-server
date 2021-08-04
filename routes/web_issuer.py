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

def translated_credentials () :
    return {'pass' : _('Identity pass'),
                'experience' : _('Professional experience assessment'),
                'skill' : _('Skill certificate'),
                'training' : _('Training certificate'),
                'recommendation' : _('Recommendation letter'),
                'work' : _('Certificate of employment'),
                'vacation' : _('Employee vacation time certificate'),
                'internship' : _('Certificate of participation'),
                'relocation' : _('Transfer certificate'),
                'hiring' : _('Promise to hire letter')}



def init_app(app, mode) :
    app.add_url_rule('/company/add_employee/',  view_func=add_employee, methods = ['GET','POST'], defaults={'mode' : mode})
    app.add_url_rule('/user/request_certificate',  view_func=request_certificate, methods = ['GET','POST'], defaults={'mode' : mode})
    app.add_url_rule('/user/request_experience_credential',  view_func=request_experience_credential, methods = ['POST'], defaults={'mode' : mode})
    app.add_url_rule('/user/request_skill_credential',  view_func=request_skill_credential, methods = ['POST'], defaults={'mode' : mode})
    app.add_url_rule('/user/request_reference_credential',  view_func=request_reference_credential, methods = ['POST'], defaults={'mode' : mode})
    app.add_url_rule('/user/request_pass_credential',  view_func=request_pass_credential, methods = ['GET'], defaults={'mode' : mode})
    app.add_url_rule('/user/request_work_credential',  view_func=request_work_credential, methods = ['POST'], defaults={'mode' : mode})
    app.add_url_rule('/company/dashboard/',  view_func=company_dashboard, methods = ['GET','POST'], defaults={'mode' : mode})
    app.add_url_rule('/company/issue_credential_workflow',  view_func=issue_credential_workflow, methods = ['GET','POST'], defaults={'mode' : mode})
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
                flash(employee_username.lower() + " has been added as " + session['role_to_add'] + '.' , 'success')

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
            flash(_('This company has no active campaign.'), 'warning')
            return redirect(mode.server + 'user/')
        return render_template('./issuer/campaign_code.html', **session['menu'], company_name=session['issuer_explore']['name'])

    if request.method == 'POST' :
        if request.form.get('choice') == 'reference_code' :
            campaign = company.Campaign(session['credential_issuer_username'], mode)
            session['reference'] = request.form['reference_code']
            campaign_data =  campaign.get(session['reference'].split(':')[0])
            if not campaign_data :
                flash(_('Reference not found.'), 'warning')
                return redirect(mode.server + 'user/issuer_explore/?issuer_username='+ session['credential_issuer_username'])
            # get credential selected
            credentials_list = ''
            for credential in json.loads(campaign_data)['credentials_supported'] :
                credentials_list += """<option value='""" + credential +"""'>""" + translated_credentials()[credential] + """</option>"""
            return render_template('./issuer/request_certificate.html', **session['menu'], company_name=session['issuer_explore']['name'], credentials_list=credentials_list)

        # switch with credentiel type
        if request.form['certificate_type'] == 'experience' : #ProfessionalExperienceAssessment
            # get reviewers available
            select = ""
            reviewer = company.Employee(session['credential_issuer_username'], mode) 
            reviewer_list = reviewer.get_list('reviewer', 'all')
            for reviewer in reviewer_list :
                session['select'] = select + """<option value=""" + reviewer['username'].split('.')[0]  + """>""" + reviewer['username'].split('.')[0] + """</option>"""
            return render_template('./issuer/request_experience_credential.html', **session['menu'], select=session['select'])
        
        elif request.form['certificate_type'] == 'skill' : #ProfessionalSkillAssessment
            # get reviewers available
            select = ""
            reviewer = company.Employee(session['credential_issuer_username'], mode) 
            reviewer_list = reviewer.get_list('reviewer', 'all')
            for reviewer in reviewer_list :
                session['select'] = select + """<option value=""" + reviewer['username'].split('.')[0]  + """>""" + reviewer['username'].split('.')[0] + """</option>"""
            return render_template('./issuer/request_skill_credential.html', **session['menu'], select=session['select'])

        elif request.form['certificate_type'] == 'work' : #CertificateOfEmployment
            return render_template('./issuer/request_work_credential.html', **session['menu'])
        
        elif request.form['certificate_type'] == 'pass' : #IdentityPass
            return redirect (mode.server + 'user/request_pass_credential')
        
        elif request.form['certificate_type'] == 'reference' :
            # get reviewers available
            select = ""
            reviewer = company.Employee(session['credential_issuer_username'], mode) 
            reviewer_list = reviewer.get_list('reviewer', 'all')
            for reviewer in reviewer_list :
                session['select'] = select + """<option value=""" + reviewer['username'].split('.')[0]  + """>""" + reviewer['username'].split('.')[0] + """</option>"""
            return render_template('./issuer/request_reference_credential.html', **session['menu'], select=session['select'])
        
        else :
            flash(_('Credential not available.') , 'warning')
            return redirect(mode.server + 'user/')


def request_reference_credential(mode) :
    """ Basic request for experience credential
    """
    check_login()

    # load templates for verifibale credential and init with view form and session
    unsigned_credential = json.load(open('./verifiable_credentials/reference.jsonld', 'r'))
    unsigned_credential["id"] =  "urn:uuid:" + str(uuid.uuid1())
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
    unsigned_credential["credentialSubject"]["author"]["logo"] = mode.ipfs_gateway + session['issuer_explore']['picture']
    unsigned_credential["credentialSubject"]["author"]["name"] = session['issuer_explore']['name']
    unsigned_credential["credentialSubject"]["signatureLines"]["name"] = ""

    # update local issuer database
    manager_username = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['referent']
    credential = company.Credential(session['credential_issuer_username'], mode)
    credential.add(session['username'],
                        request.form['reviewer_username'],
                        manager_username,
                        "drafted",
                        unsigned_credential["id"],
                        json.dumps(unsigned_credential),
                        session['reference'])

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


def request_pass_credential(mode) :
    """ Request for IdentityPass   
    https://github.com/TalaoDAO/context/blob/main/vocab.md#identitypass

    """
    check_login()
    
    # load JSON-LD model for IdentityPass
    unsigned_credential = json.load(open('./verifiable_credentials/IdentityPass.jsonld', 'r'))

    # update credential with form data, all those datat are required in the data model 
    unsigned_credential["id"] =  "urn:uuid:" + str(uuid.uuid1())
    unsigned_credential["credentialSubject"]["id"] = ns.get_did(session['workspace_contract'],mode)
    unsigned_credential["credentialSubject"]['recipient']["familyName"] = session['personal']["lastname"]['claim_value']
    try :
        unsigned_credential["credentialSubject"]['recipient']["email"] = session['personal']["contact_email"]['claim_value']
    except :
        unsigned_credential["credentialSubject"]['recipient']["email"] = "should_be_there"
    unsigned_credential["credentialSubject"]['recipient']["givenName"] = session['personal']['firstname']['claim_value']
    unsigned_credential["credentialSubject"]['recipient']["image"] = mode.ipfs_gateway + session['personal']['picture']
    unsigned_credential["credentialSubject"]['author']["logo"] = mode.ipfs_gateway + session['issuer_explore']['picture']
    unsigned_credential["credentialSubject"]['author']["name"] = session['issuer_explore']['name']

    # update local issuer database
    credential = company.Credential(session['credential_issuer_username'], mode)
    credential.add(session['username'],
                        session['credential_issuer_username'],
                        session['credential_issuer_username'],
                        "drafted",
                        unsigned_credential["id"],
                        json.dumps(unsigned_credential, ensure_ascii=False),
                        session['reference'])

    # send an email to reviewer for workflow
    reviewer_email = ns.get_data_from_username(session['credential_issuer_username'], mode)['email']
    subject = _('You have received a request for an identity pass from ')+ session['name'] + _(' to review')
    try :
        Talao_message.messageHTML(subject, reviewer_email, 'request_certificate', {'name' : session['name'], 'link' : 'https://talao.co'}, mode)
    except :
        logging.error('email failed')

    # send email to user
    flash(_('Your request for an identity pass has been registered for review.'), 'success')

    return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + session['credential_issuer_username'])


def request_work_credential(mode) :
    """ Request for CertrificateOfEmployment   
    https://github.com/TalaoDAO/context/blob/main/vocab.md#certificateofemployment

    """
    check_login()
    
    # load JSON-LD model for IdentityPass
    unsigned_credential = json.load(open('./verifiable_credentials/CertificateOfEmployment.jsonld', 'r'))
    
    # update credential with form data
    unsigned_credential["id"] =  "urn:uuid:" + str(uuid.uuid1())
    unsigned_credential["credentialSubject"]["id"] = ns.get_did(session['workspace_contract'],mode)
    unsigned_credential["credentialSubject"]["familyName"] = session['personal']["lastname"]['claim_value']
    unsigned_credential["credentialSubject"]["givenName"] = session['personal']['firstname']['claim_value']
    unsigned_credential["credentialSubject"]['workFor']["logo"] = mode.ipfs_gateway + session['issuer_explore']['picture']
    unsigned_credential["credentialSubject"]['workFor']["name"] = session['issuer_explore']['name']
    unsigned_credential["credentialSubject"]['workFor']["address"] = session['issuer_explore']['personal']['postal_address']['claim_value']
    unsigned_credential["credentialSubject"]['signatureLines']["image"] = mode.ipfs_gateway + session['issuer_explore']['personal']['signature']
    # optional properties
    if request.form.get('employmentType') == 'on' :
        unsigned_credential["credentialSubject"]['employmentType'] = "required"
    if request.form.get('baseSalary') == 'on' :
        unsigned_credential["credentialSubject"]['baseSalary'] = "required"
    if request.form.get('jobTitle') == 'on' :
        unsigned_credential["credentialSubject"]['jobTitle'] = "required"

    # update local issuer database
    credential = company.Credential(session['credential_issuer_username'], mode)
    credential.add(session['username'],
                        session['credential_issuer_username'],
                        session['credential_issuer_username'],
                        "drafted",
                        unsigned_credential["id"],
                        json.dumps(unsigned_credential, ensure_ascii=False),
                        session['reference'])

    # send an email to reviewer for workflow
    reviewer_email = ns.get_data_from_username(session['credential_issuer_username'], mode)['email']
    subject = _('You have received a request for a certificate of employment from ')+ session['name'] + _(' to review')
    try :
        Talao_message.messageHTML(subject, reviewer_email, 'request_certificate', {'name' : session['name'], 'link' : 'https://talao.co'}, mode)
    except :
        logging.error('email failed')

    # send email to user
    flash(_('Your request for a certificate of employment has been registered for review.'), 'success')

    return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + session['credential_issuer_username'])

def request_experience_credential(mode) :
    """ Basic request for experience credential

    """
    check_login()
    
    # load JSON-LD model for ProfessionalExperiencAssessment
    unsigned_credential = json.load(open('./verifiable_credentials/ProfessionalExperienceAssessment.jsonld', 'r'))

    # update credential with form data
    unsigned_credential["id"] =  "urn:uuid:" + str(uuid.uuid1())
    unsigned_credential["credentialSubject"]["id"] = ns.get_did(session['workspace_contract'],mode)
    unsigned_credential["credentialSubject"]['recipient']["familyName"] = session['personal']["lastname"]['claim_value']
    unsigned_credential["credentialSubject"]['recipient']["givenName"] = session['personal']['firstname']['claim_value']
    unsigned_credential["credentialSubject"]['recipient']["image"] = mode.ipfs_gateway + session['personal']['picture']
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
    unsigned_credential["credentialSubject"]['author']["logo"] = mode.ipfs_gateway + session['issuer_explore']['picture']
    unsigned_credential["credentialSubject"]['author']["name"] = session['issuer_explore']['name']
    unsigned_credential["credentialSubject"]['signatureLines']["name"] = ""

    # update local issuer database
    manager_username = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['referent']
    credential = company.Credential(session['credential_issuer_username'], mode)
    credential.add(session['username'],
                        request.form['reviewer_username'],
                        manager_username,
                        "drafted",
                        unsigned_credential["id"],
                        json.dumps(unsigned_credential, ensure_ascii=False),
                        session['reference'])

    # send an email to reviewer for workflow
    reviewer_email = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['email']
    subject = _('You have received a request for professional experience assessment from ')+ session['name'] + _(' to review')
    try :
        Talao_message.messageHTML(subject, reviewer_email, 'request_certificate', {'name' : session['name'], 'link' : 'https://talao.co'}, mode)
    except :
        logging.error('email failed')

    # send email to user
    flash(_('Your request for an experience professional assessment has been registered for review.'), 'success')

    # clean up and return
    del session['select']
    return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + session['credential_issuer_username'])


def request_skill_credential(mode) :
    """ Basic request for skill credential

    """
    check_login()
    
    # load JSON-LD model for ProfessionalSkillAssessment
    unsigned_credential = json.load(open('./verifiable_credentials/ProfessionalSkillAssessment.jsonld', 'r'))

    # update credential with form data
    unsigned_credential["id"] =  "urn:uuid:" + str(uuid.uuid1())
    unsigned_credential["credentialSubject"]["id"] = ns.get_did(session['workspace_contract'],mode)
    unsigned_credential["credentialSubject"]['recipient']["familyName"] = session['personal']["lastname"]['claim_value']
    unsigned_credential["credentialSubject"]['recipient']["givenName"] = session['personal']['firstname']['claim_value']
    unsigned_credential["credentialSubject"]['recipient']["image"] = mode.ipfs_gateway + session['personal']['picture']
    unsigned_credential["credentialSubject"]["skills"] = list()
    for skill in request.form['skills'].split(',') :
        unsigned_credential["credentialSubject"]["skills"].append(
            {
            "@type": "Skill",
            "description": skill
            })
    unsigned_credential["credentialSubject"]['author']["logo"] = mode.ipfs_gateway + session['issuer_explore']['picture']
    unsigned_credential["credentialSubject"]['author']["name"] = session['issuer_explore']['name']
    unsigned_credential["credentialSubject"]['signatureLines']["name"] = ""

    # update local issuer database
    manager_username = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['referent']
    credential = company.Credential(session['credential_issuer_username'], mode)
    credential.add(session['username'],
                        request.form['reviewer_username'],
                        manager_username,
                        "drafted",
                        unsigned_credential["id"],
                        json.dumps(unsigned_credential, ensure_ascii=False),
                        session['reference'])

    # send an email to reviewer for workflow
    reviewer_email = ns.get_data_from_username(request.form['reviewer_username'] + '.' + session['credential_issuer_username'], mode)['email']
    subject = _('You have received a request for a professional skill assessment from ')+ session['name'] + _(' to review')
    try :
        Talao_message.messageHTML(subject, reviewer_email, 'request_certificate', {'name' : session['name'], 'link' : 'https://talao.co'}, mode)
    except :
        logging.error('email failed')

    # send email to user
    flash(_('Your request for a skill professional assessment has been registered for review.'), 'success')

    # clean up and return
    del session['select']
    return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + session['credential_issuer_username'])


def company_dashboard(mode) :
    """
    # @route /company/dashboard/
    """

    check_login()

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
        signed = drafted = reviewed = ''
        if session['role'] == 'issuer' :
            reviewed = 'checked'
            status = ('reviewed','','')
        elif session['role'] == 'reviewer' :
            drafted = 'checked'
            status = ('drafted','','')
        else :
            drafted =  reviewed =  'checked'
            status = ('drafted', 'reviewed', '')

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
    check_login()
    credential = company.Credential(host, mode)
    mylist = credential.get(issuer_username, reviewer_username, status)
    credential_list = ""
    for mycredential in mylist :

        if json.loads(mycredential[5])['credentialSubject']['type'] == "ProfessionalExperienceAssessment" :
                subject_link = mode.server + 'resume/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
                title = json.loads(mycredential[5])['credentialSubject']['title'][:20]
                description = json.loads(mycredential[5])['credentialSubject']['description'][:200] + "..."
                type = "ProfessionalExperienceAssessment"
                name = json.loads(mycredential[5])['credentialSubject']["recipient"]['givenName'] + ' ' + json.loads(mycredential[5])['credentialSubject']["recipient"]['familyName']
        elif json.loads(mycredential[5])['credentialSubject']['type'] == "ProfessionalSkillAssessment" :
                subject_link = mode.server + 'resume/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
                title = "N/A"
                description = "N/A"
                type = "ProfessionalSkillAssessment"
                name = json.loads(mycredential[5])['credentialSubject']["recipient"]['givenName'] + ' ' + json.loads(mycredential[5])['credentialSubject']["recipient"]['familyName']
        elif json.loads(mycredential[5])['credentialSubject']['type'] == "IdentityPass" :
                subject_link = mode.server + 'resume/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
                type = "IdentityPass"
                title = description = "N/A"
                name = json.loads(mycredential[5])['credentialSubject']["recipient"]['givenName'] + ' ' + json.loads(mycredential[5])['credentialSubject']["recipient"]['familyName']
        elif json.loads(mycredential[5])['credentialSubject']['type'] == "CertificateOfEmployment" :
                subject_link = mode.server + 'resume/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
                type = "CertificateOfEmployment"
                title = description = "N/A"
                name = json.loads(mycredential[5])['credentialSubject']['givenName'] + ' ' + json.loads(mycredential[5])['credentialSubject']['familyName']
        else :
            subject_link = mode.server + 'resume/?did=' + json.loads(mycredential[5])['credentialSubject']['id']
            type = _("Not Supported")
            title = description = "N/A"
            name = 'N/A'
        
        credential = """<tr>
                <td><a href=/company/issue_credential_workflow?id=""" + mycredential[6] + """> """ + mycredential[6][:2] + '...' + mycredential[6][-2:]  + """</a></td>
                <!-- <td><a href=""" + subject_link + """>""" + name + """</a></td> -->
                <td>""" + name + """</td>
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
    check_login()

    if request.method == 'GET' :
        session['credential_id'] = request.args['id']
        credential = company.Credential(session['host'], mode)
        session['call'] = credential.get_by_id(session['credential_id'])

        # credential cannot be updated if already signed
        field = "disabled" if session['call'][4] == 'signed' or session['role'] in ['admin'] else ""
        
        # credential is loaded  as dict
        my_credential = json.loads(session['call'][5])['credentialSubject']    
        
        # switch
        if my_credential['type'] == "ProfessionalExperienceAssessment" :
            skills_str = ""
            for skill in my_credential['skills'] :
                skills_str += skill['description'] + ','

            reviewRecommendation, reviewDelivery, reviewSchedule, reviewCommunication = 0,1,2,3

            for i in [0,1] :
                if my_credential["review"][reviewRecommendation]["reviewBody"][i]["@language"] == session['language'] :
                    questionRecommendation = my_credential["review"][reviewRecommendation]["reviewBody"][i]['@value']
                    break
            for i in [0,1] :
                if my_credential["review"][reviewDelivery]["reviewBody"][i]["@language"] == session['language'] :
                    questionDelivery = my_credential["review"][reviewDelivery]["reviewBody"][i]['@value']
                    break
            for i in [0,1] :
                if my_credential["review"][reviewSchedule]["reviewBody"][i]["@language"] == session['language'] :
                    questionSchedule = my_credential["review"][reviewSchedule]["reviewBody"][i]['@value']
                    break
            for i in [0,1] :
                if my_credential["review"][reviewCommunication]["reviewBody"][i]["@language"] == session['language'] :
                    questionCommunication = my_credential["review"][reviewCommunication]["reviewBody"][i]['@value']
                    break

            return render_template ('./issuer/issue_experience_credential_workflow.html',
                credential_id=request.args['id'],
                picturefile = mode.ipfs_gateway + session['picture'],
				clipboard = mode.server  + "board/?did=" + session['did'],
                **my_credential,
                recipient_name = my_credential["recipient"]["givenName"] + ' ' + my_credential["recipient"]["familyName"],
                author_name = my_credential["author"]["name"],
                signer_name = my_credential["signatureLines"]["name"],
                scoreRecommendation =  my_credential["review"][reviewRecommendation]["reviewRating"]["ratingValue"],
                questionRecommendation = questionRecommendation,
                scoreSchedule =  my_credential["review"][reviewSchedule]["reviewRating"]["ratingValue"],
                questionSchedule = questionSchedule,
                scoreCommunication =  my_credential["review"][reviewCommunication]["reviewRating"]["ratingValue"],
                questionCommunication = questionCommunication,
                scoreDelivery =  my_credential["review"][reviewDelivery]["reviewRating"]["ratingValue"],
                questionDelivery = questionDelivery,
                skills_str= skills_str,
                field= field)
        
        elif my_credential['type'] == "ProfessionalSkillAssessment" :
            skill_html = ""
            for count,skill in enumerate(my_credential['skills']):
                skill_count = 'skill_' + str(count)
                skill_html += """
                        <div class="form-row">
                            <div class="col">
                                <div class="form-group">
                                    <label><strong>""" + _('Skill') + """ : </strong>""" + skill['description'] + """</label>
                                    <input class="form-control"  placeholder='""" + _("Draft an assessment of this skill") + """' type="text" name='""" + skill_count + """' required>
                                </div>
                            </div>
                        </div>
                        """
            return render_template('./issuer/issue_skill_credential.html',
                credential_id=request.args['id'],
                picturefile = mode.ipfs_gateway + session['picture'],
                reference= session['call'][6],
				skill_html = skill_html,
                signer_name = my_credential["signatureLines"]["name"],
                givenName = my_credential["recipient"].get("givenName"),
                familyName = my_credential["recipient"].get("familyName"),
                clipboard = mode.server  + "board/?did=" + session['did'],
                image = my_credential["recipient"].get("image"),
                field= field)
                
        elif my_credential['type'] == "IdentityPass" :
            return render_template('./issuer/issue_identity_credential.html',
                credential_id=request.args['id'],
                picturefile = mode.ipfs_gateway + session['picture'],
                reference= session['call'][6],
				clipboard = mode.server  + "board/?did=" + session['did'],
                jobTitle = my_credential["recipient"].get("jobTitle"),
                givenName = my_credential["recipient"].get("givenName"),
                familyName = my_credential["recipient"].get("familyName"),
                address = my_credential["recipient"].get("address"),
                birthDate = my_credential["recipient"].get("birthDate"),
                email = my_credential["recipient"].get("email"),
                telephone = my_credential["recipient"].get("telephone"),
                gender = my_credential["recipient"].get("gender"),
                image = my_credential["recipient"].get("image"),
                field= field)

        elif my_credential['type'] == "CertificateOfEmployment" :
            return render_template('./issuer/issue_work_credential.html',
                credential_id=request.args['id'],
                picturefile = mode.ipfs_gateway + session['picture'],
                reference= session['call'][6],
				clipboard = mode.server  + "board/?did=" + session['did'],
                jobTitle = my_credential.get("jobTitle"),
                givenName = my_credential.get("givenName"),
                familyName = my_credential.get("familyName"),
                startDate = my_credential.get("startDate"),
                employmentType = my_credential.get("employmentType"),
                baseSalary = my_credential.get("baseSalary"),
                field= field)
        else : 
            flash(_('view not yet available.'), 'warning')
            return redirect (mode.server +'company/dashboard/')

    if request.method == 'POST' :

        if request.form['exit'] == 'delete' :
            # credential is removed from database
            credential = company.Credential(session['host'], mode)
            credential.delete(session['credential_id'])
            del session['credential_id']
            del session['call']
            return redirect (mode.server +'company/dashboard/')

        if request.form['exit'] == 'back' :
            # nothing is done
            del session['credential_id']
            del session['call']
            return redirect (mode.server +'company/dashboard/')

        # get form data to update credential
        my_credential = json.loads(session['call'][5])
        my_credential['credentialSubject'] = get_form_data(json.loads(session['call'][5])['credentialSubject'], request.form)

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
            
            # add signature Lines if needed
            if my_credential['credentialSubject']['type'] in ['ProfessionalExperienceAssessment', 'ProfessionalSkillAssessment'] :
                manager_workspace_contract = ns.get_data_from_username(session['username'], mode)['identity_workspace_contract']
                my_credential['credentialSubject']['signatureLines']['image'] = mode.ipfs_gateway + json.loads(ns.get_personal(manager_workspace_contract, mode))['signature']
            elif my_credential['credentialSubject']['type'] in ['IdentityPass', 'CertificateOfEmployment'] :
                pass

            # sign credential with company key
            my_credential["issuanceDate"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            my_credential['issuer'] = ns.get_did(session['workspace_contract'], mode)
            signed_credential = vc_signature.sign(my_credential,
                                                session['private_key_value'],
                                                my_credential['issuer'])
            if not signed_credential :
                flash(_('Operation failed.'), 'danger')
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
                flash(_('Add credential to repository failed.'), 'danger')
                logging.error('certificate to repository failed')
            else :
                flash(_('The credential has been added to the user repository.'), 'success')

            # send an email to user
            #link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + subject['workspace_contract'][2:] + ':document:' + str(doc_id)
            link= mode.server
            certificate_issued = 'certificate_issued_fr' if session['language'] == 'fr' else 'certificate_issued'
            try :
                Talao_message.messageHTML(_('Your professional credential has been issued.'), subject['email'], certificate_issued, {'username': session['name'], 'link': link}, mode)
            except :
                logging.error('email to subject failed')
            
            # store signed credential on server
            try :
                filename = session['credential_id'] + '.jsonld'
                path = "./signed_credentials/"
                with open(path + filename, 'w') as outfile :
                    json.dump(json.loads(signed_credential), outfile, indent=4, ensure_ascii=False)
            except :
                logging.error('signed credential not stored')

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

            flash(_('Credential has been reviewed.'), 'success')

        # all exits except delete and back
        del session['credential_id']
        del session['call']
        return redirect (mode.server +'company/dashboard/')


def get_form_data(my_credential, form) :
    """
    This function updates credential with form data
    """ 
    if my_credential['type'] == "ProfessionalExperienceAssessment" :
        reviewRecommendation, reviewDelivery, reviewSchedule, reviewCommunication = 0,1,2,3
        my_credential["review"][reviewRecommendation]["reviewRating"]["ratingValue"] = form["scoreRecommendation"]
        my_credential["review"][reviewSchedule]["reviewRating"]["ratingValue"] = form["scoreSchedule"]
        my_credential["review"][reviewDelivery]["reviewRating"]["ratingValue"] = form["scoreDelivery"]
        my_credential["review"][reviewCommunication]["reviewRating"]["ratingValue"] = form["scoreCommunication"]
        my_credential['title'] = form['title']
        my_credential['description'] = form['description']
        my_credential['startDate'] = form['startDate']
        my_credential['endDate'] = form['endDate']
        my_credential['skills'] = list()
        for skill in form['skills_str'].split(',') :
            if skill :
                my_credential["skills"].append(
                            {
                            "@type": "Skill",
                            "description": skill
                            })
        my_credential["signatureLines"]['name'] = form.get('managerName', " ")

    elif my_credential['type'] == "ProfessionalSkillAssessment" :
        my_credential['recipient']['familyName'] = form['familyName']
        my_credential['recipient']['givenName'] = form['givenName']
        my_credential['datePublished'] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        skill_list = list()
        for count,skill in enumerate(my_credential['skills']):
            skill_count = 'skill_' + str(count)
            skill_list.append(
                            {
                            "@type": "Skill",
                            "description": form[skill_count]
                            })
        my_credential['skills'] = skill_list
        my_credential["signatureLines"]['name'] = form.get('managerName', " ")

    elif my_credential['type'] == "IdentityPass" :
        my_credential['recipient']['familyName'] = form['familyName']
        my_credential['recipient']['jobTitle'] = form['jobTitle']
        my_credential['recipient']['givenName'] = form['givenName']
        my_credential['recipient']['email'] = form['email']
        my_credential['recipient']['image'] = form['image']
        if form.get('birthDate') :
            my_credential['recipient']['birthDate'] = form['birthDate']
        if form.get('gender') :
            my_credential['recipient']['gender'] = form['gender']
        if form.get('telephone') :
            my_credential['recipient']['telephone'] = form['telephone']
        if form.get('address') and form.get('address') != 'None' :
            my_credential['recipient']['address'] = form['address']
    
    elif my_credential['type'] == "CertificateOfEmployment" :
        my_credential['familyName'] = form['familyName']
        my_credential['givenName'] = form['givenName']
        my_credential['startDate'] = form['startDate']
        if my_credential.get('baseSalary')  :
            my_credential['baseSalary'] = form['baseSalary'] 
        if  my_credential.get('jobTitle') :
            my_credential['jobTitle'] = form['jobTitle'] 
        if my_credential.get('employmentType')  :
            my_credential['employmentType'] = form['employmentType']
    
    return my_credential


def add_campaign(mode) :
    """ create a new campaign 
    """
    check_login()
    if request.method == 'GET' :
        # display all credentials supported of teh company other a disabled
        personal = ns.get_personal(session['workspace_contract'], mode)
        credentials_supported = json.loads(personal).get('credentials_supported',[])
        checkbox = dict()
        for topic in [*translated_credentials()] :
            checkbox['box_' + topic] = "checked" if topic in credentials_supported else "disabled"
        return render_template('./issuer/add_campaign.html', **session['menu'], **checkbox, **translated_credentials())
    if request.method == 'POST' :
        new_campaign = company.Campaign(session['username'], mode)
        data = {'description' : request.form['description'],
                'nb_subject' : 0,
                'startDate' : '',
                'endDate' : '',
                'credentials_supported' : []}
        credentials_supported = list()
        for topic in  [*translated_credentials()] :
            if request.form.get(str(topic)) :
                credentials_supported.append(request.form.get(str(topic)))
        data['credentials_supported'] = credentials_supported
        new_campaign.add(request.form['name'], json.dumps(data, ensure_ascii=False))
        flash(_('New campaign added.'), 'success')
        return redirect(mode.server + 'user/')


def remove_campaign(mode) :
    """ create a new campaign 
    """
    check_login()
    new_campaign = company.Campaign(session['username'], mode)
    new_campaign.delete(request.args['campaign_name'])
    flash(_('Campaign removed'), 'success')
    return redirect(mode.server + 'user/')