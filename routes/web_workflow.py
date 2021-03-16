
import os
from flask import Flask, session, send_from_directory, flash, send_file
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
from datetime import timedelta, datetime
import time
import json
import random
import logging
import secrets
logging.basicConfig(level=logging.INFO)

# dependances
from core import Talao_message, Talao_ipfs, ns, sms, directory, privatekey, credential
import constante
from protocol import ownersToContracts, contractsToOwners, save_image,  token_balance
from protocol import Document, read_profil, get_image


def check_login() :
	""" check if the user is correctly logged. This function is called everytime a user function is called """
	if not session.get('workspace_contract') and not session.get('username') :
		abort(403)
	else :
		return True



def add_employee(mode) :
    """
    # add admin or manager or reviewer in table manager of host
    #@app.route('/user/add_employee/', methods=['GET', 'POST'])
     add_employee(employee_name, identity_name, role, referent, host_name, email, mode, phone=None, password='identity') :
    """
    check_login()
    if request.method == 'GET' :
        session['role_to_add'] = request.args.get('role_to_add')

        if  session['role_to_add'] == 'issuer' :
            return render_template('./workflow/add_issuer.html', **session['menu'])

        elif  session['role_to_add'] == 'reviewer' :
            issuer_list = ns.get_employee_list(session['host'],'issuer', 'all', mode)
            issuer_select = ""
            for issuer in issuer_list :
                issuer_select += """<option value=""" + issuer['username'].split('.')[0]  + """>""" + issuer['username'].split('.')[0] + """</option>"""
            return render_template('./workflow/add_reviewer.html', **session['menu'], issuer_select=issuer_select)

        elif  session['role_to_add'] == 'admin' :
            return render_template('./workflow/add_admin.html', **session['menu'])

    if request.method == 'POST' :
        # check if username is new
        if not ns.username_exist(request.form['identity_username'].lower(),mode)  :
            flash('This username is already used, lets trys an another one !' , 'warning')
        else :
            employee_username = request.form['employee_username']
            identity_username = request.form['identity_username']

            # let check  who is the referent 
            if session['role_to_add'] == 'reviewer' :
                if not session['role'] or session['role'] == 'admin' :
                    referent = request.form['referent_username']
                else :
                    referent = session['employee']
            else :
                referent = None

            if ns.add_employee(employee_username, identity_username, session['role_to_add'], referent, session['host'], request.form['employee_email'], mode) :
                flash(employee_username.lower() + " has been added" , 'success')

        del session['role_to_add']
        return redirect (mode.server +'user/')



def request_certificate(mode) :
    """ The request call comes from the Search Bar or from the Identity page
    # request credential to be completed with email
    #@app.route('/user/request_certificate/', methods=['GET', 'POST'])
    """
    check_login()

    if request.method == 'GET' :
        session['certificate_issuer_username'] = request.args.get('issuer_username')
        # Check if issuer has private key
        if session['certificate_issuer_username'] :
            if not privatekey.get_key(session['issuer_explore']['address'], 'private_key', mode) :
                flash('Sorry, this referent cannot issue Certificates.', 'warning')
                return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['certificate_issuer_username'])
        return render_template('request_certificate.html', **session['menu'])

    if request.method == 'POST' :
        # From Menu, if issuer does not exist, we request to user his email and type.
        if not session['certificate_issuer_username'] :
            session['issuer_email'] = request.form['issuer_email']
            session['issuer_type'] = 'person' if request.form['certificate_type']=='personal_recommendation' else 'company'

            # we check if the issuer exists
            username_list = ns.get_username_list_from_email(request.form['issuer_email'], mode)
            if username_list :
                msg = 'This email is already used by Identity(ies) : ' + ", ".join(username_list) + ' . Use the Search Bar to check their identities and request a certificate.'
                flash(msg , 'warning')
                return redirect(mode.server + 'user/')
        else :
            session['issuer_type'] = session['issuer_explore']['type']
            session['issuer_email'] = ns.get_data_from_username(session['certificate_issuer_username'], mode)['email']

        select = ""
        reviewer_list = ns.get_employee_list(session['certificate_issuer_username'], 'reviewer', 'all', mode)
        for reviewer in reviewer_list :
            select = select + """<option value=""" + reviewer['username'].split('.')[0]  + """>""" + reviewer['username'].split('.')[0] + """</option>"""

        if request.form['certificate_type'] == 'experience' :
            return render_template('request_experience_certificate.html', **session['menu'], select=select)

        elif request.form['certificate_type'] in ['personal_recommendation', 'company_recommendation'] :
            return render_template('request_recommendation_certificate.html', **session['menu'])

        elif request.form['certificate_type'] == 'agreement' :
            return render_template('request_agreement_certificate.html', **session['menu'])

        elif request.form['certificate_type'] == 'reference' :
            return render_template('request_reference_certificate.html', **session['menu'])

        else :
            flash('certificate not available' , 'warning')
            return redirect(mode.server + 'user/')

#@app.route('/user/request_experience_certificate/', methods=['POST'])
def request_experience_certificate(mode) :
    check_login()
    issuer_username = ns.get_username_from_resolver(session['issuer_explore']['workspace_contract'], mode)
    id = str(secrets.randbits(64))
    unsigned_credential = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://schema.org/JobPosting",
                  ],
            "id": session['did'] + '#experience'+ id,
            "type": ["VerifiableCredential",],
            "issuer": session['issuer_explore']['did'],
            "issuanceDate": "",
            "expirationDate" : "",
            "credentialStatus": "",
            "credentialSubject":
                {
                "id": session['did'],
                "name" : session['name'],
                "credentialCategory" : "experience",
                "title" : request.form['title'],
                "description" : request.form['description'],
                "employmentType" : "",
                "startDate" : request.form['start_date'],
                "endDate" : request.form['end_date'],
                "skills" : request.form['skills'].split(','),
                "questionRecommendation" : "How likely are you to recommend this talent to others ?",
                "scoreRecommendation" : "",
                "questionDelivery" : "How satisfied are you with the overall delivery ?",
                "scoreDelivery" : "",
                "questionSchedule" : "How would you rate his/her ability to deliver to schedule ?",
                "scoreSchedule" : "",
                "questionCommunication" : "How would you rate his/her overall communication skills ?",
                "scoreCommunication" : "",
                "companyLogo" : session['issuer_explore']['picture'],
                "managerSignature" : "",
                "companyName" : session['issuer_explore']['name'],
                "managerName" : "",
                "reviewerName" : "",
                },
            }
    manager_username = ns.get_data_from_username(request.form['reviewer_username'] + '.' + issuer_username, mode)['referent']
    ns.add_verifiable_credential(issuer_username,
                        session['username'],
                        request.form['reviewer_username'],
                        manager_username,
                        "drafted",
                        id,
                        json.dumps(unsigned_credential),
                        mode)
    reviewer_email = ns.get_data_from_username(request.form['reviewer_username'] + '.' + issuer_username, mode)['email']
    print('reviewer email = ', reviewer_email)
    subject = 'You have received a professional credential from '+ session['name'] + ' to review'
    Talao_message.messageHTML(subject, reviewer_email, 'request_certificate', {'name' : session['name'], 'link' : 'https://talao.co'}, mode)
    # message to user/Talent
    flash('Your request for an experience credential has been registered for review.', 'success')
    return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + issuer_username)

def company_dashboard(mode) :
    """
    # @route /user/company_dashboard/
    """
    # created, user_name, reviewer_name, manager_name, status, credential, id
    issuer_select = ""
    issuer_list = ns.get_employee_list(session['host'],'issuer', 'all', mode)
    for issuer in issuer_list :
        issuer_select += """<option value=""" + issuer['username'].split('.')[0]  + """>""" + issuer['username'].split('.')[0] + """</option>"""

    reviewer_select = ""
    reviewer_list = ns.get_employee_list(session['host'], 'reviewer', 'all', mode)
    for reviewer in reviewer_list :
        reviewer_select += """<option value=""" + reviewer['username'].split('.')[0]  + """>""" + reviewer['username'].split('.')[0] + """</option>"""

    if request.method == 'GET' :

        # init of dashboard display
        if session['role'] == 'reviewer' :
            manager_query = 'all'
            reviewer_query = session['employee']
        elif session['role'] == 'issuer' :
            manager_query = session['employee']
            reviewer_query = 'all'
        else :
            manager_query = 'all'
            reviewer_query = 'all'

        signed = drafted = reviewed = ""
        if session['role'] == 'issuer' :
            reviewed = "checked"
            status = ("reviewed","","")
        elif session['role'] == 'reviewer' :
            drafted = 'checked'
            status = ('drafted',"","")
        else :
            drafted =  reviewed = "checked"
            status = ('drafted', 'reviewed', '')

        credential_list = credential_list_html(session['host'], manager_query, reviewer_query, status, mode)
        return render_template('./workflow/company_dashboard.html',
                                **session['menu'],
                                credential_list=credential_list,
                                drafted=drafted,
                                reviewed=reviewed,
                                signed=signed,
                                reviewer_select=reviewer_select,
                                manager_select=issuer_select)

    if request.method == 'POST' :
        status = (request.form.get('draftedbox', ""), request.form.get('reviewedbox', ""), request.form.get('signedbox', ""))
        drafted = "checked" if request.form.get('draftedbox') else ""
        signed = "checked" if request.form.get('signedbox') else ""
        reviewed = "checked" if request.form.get('reviewedbox') else ""

        if session['role'] == 'reviewer' :
            manager_query = 'all'
            reviewer_query = session['employee']
        else :
            manager_query = request.form['issuer']
            reviewer_query = request.form['reviewer']
        print('status = ', status)
        credential_list = credential_list_html(session['host'], manager_query, reviewer_query, status, mode)
        return render_template('./workflow/company_dashboard.html',
                                 **session['menu'],
                                credential_list=credential_list,
                                drafted=drafted,
                                reviewed=reviewed,
                                signed=signed,
                                reviewer_select=reviewer_select,
                                manager_select=issuer_select)

def credential_list_html(host, manager_username, reviewer_username, status, mode) :
    """
    helper
    return the table list to display in dashboard in html
    """
    mylist = ns.get_verifiable_credential(host, manager_username, reviewer_username, status, mode)
    credential_list = ""
    if mylist :
        for mycredential in mylist :
            credential = """<tr>
                <td><a href=/user/issue_experience_certificate_workflow/?id=""" + str(json.loads(mycredential[6])) + """> """ + mycredential[6][:4] + '...' + mycredential[6][-4:]  + """</a></td>
                <td>""" + json.loads(mycredential[5])['credentialSubject']['name'] + """</td>
                <td>""" + json.loads(mycredential[5])['credentialSubject']['title'] + """</td>
                <td>""" + json.loads(mycredential[5])['credentialSubject']['description'] + """</td>
                <td>""" + mycredential[0][:10] + """</td>
                <td>""" + json.loads(mycredential[5])['credentialSubject']['credentialCategory'].capitalize() + """</td>
                <td>""" + mycredential[2] + """</td>
                <td>""" + mycredential[3] + """ </td>
                <td>""" + mycredential[4] +  """</td>
            </tr>"""
            credential_list += credential
    return credential_list

def issue_experience_certificate_workflow(mode) :
    """
    @route /user/issue_exerience_certificate_workflow/?id=xxxx
    call = (created, user_name, reviewer_name, manager_name, status, credential, id)
    update = update_verifiable_credential(id, host_name, reviewer_username, manager_username, status, credential, mode)
    """
    if request.method == 'GET' :
        session['credential_id'] = request.args['id']
        session['call'] = ns.get_verifiable_credential_by_id(session['host'], session['credential_id'], mode)

        # credential cannot be updated if already signed
        field = "disabled" if session['call'][4] == 'signed' else ""

        # credential is loaded as a dict and pass to view as field have same names
        my_credential = json.loads(session['call'][5])['credentialSubject']
        return render_template ('./workflow/issue_experience_certificate_workflow.html',
                        credential_id=request.args['id'],
                        picturefile = session['picture'],
						clipboard = mode.server  + "board/?did=" + session['did'],
                        **my_credential,
                        skills_str= ",".join(my_credential['skills']),
                        field= field,
                        )

    if request.method == 'POST' :
        # credential is removed from database only
        if request.form['exit'] == 'delete' :
            ns.delete_verifiable_credential(session['credential_id'], session['host'], mode)
            del session['credential_id']
            del session['call']
            return redirect (mode.server +'user/company_dashboard/')

        # get form data to update credential
        username = session['host'] if session['host'] == session['username'] else session['username'].split('.')[0]
        my_credential =  json.loads(session['call'][5])
        my_credential['credentialSubject']['scoreDelivery'] =request.form['scoreDelivery']
        my_credential['credentialSubject']['scoreRecommendation'] =request.form['scoreRecommendation']
        my_credential['credentialSubject']['scoreSchedule'] =request.form['scoreSchedule']
        my_credential['credentialSubject']['scoreCommunication'] =request.form['scoreCommunication']
        my_credential['credentialSubject']['title'] =request.form['title']
        my_credential['credentialSubject']['description'] =request.form['description']
        my_credential['credentialSubject']['startDate'] =request.form['startDate']
        my_credential['credentialSubject']['endDate'] =request.form['endDate']
        my_credential['credentialSubject']['skills'] =request.form['skills_str'].split(',')
        my_credential['credentialSubject']['managerName'] =request.form['managerName']
        my_credential['credentialSubject']['reviewerName'] =request.form['reviewerName']

        # update without review and signature
        if request.form.get('exit') == 'update' :
            ns.update_verifiable_credential(session['credential_id'],
                                        session['host'],
                                        session['call'][2],
                                        session['call'][3],
                                        session['call'][4],
                                        json.dumps(my_credential),
                                        mode)

        # credential has been signed
        elif request.form.get('exit') == 'sign' :
            # add manager signature ipfs file id
            manager_workspace_contract = ns.get_data_from_username(session['username'], mode)['identity_workspace_contract']
            my_credential['credentialSubject']['managerSignature'] = get_image(manager_workspace_contract, 'signature', mode)

            # sign credential with company key
            signed_credential = credential.sign_credential(my_credential, session['rsa_key_value'])
            ns.update_verifiable_credential(session['credential_id'],
                                        session['host'],
                                        session['call'][2],
                                        username,
                                        "signed",
                                        json.dumps(signed_credential),
                                        mode)
            # ulpoad credential to Ethereum with company key signature
            subject_workspace_contract = '0x' + signed_credential['credentialSubject']['id'].split(':')[3]
            subject_address = contractsToOwners(subject_workspace_contract, mode)
            my_certificate = Document('certificate')
            doc_id = my_certificate.add(session['address'],
                        session['workspace_contract'],
                        subject_address,
                        subject_workspace_contract,
                        session['private_key_value'],
                        signed_credential,
                        mode,
                        mydays=0,
                        privacy='public',
                         synchronous=True)[0] 
            if not doc_id :
                flash('Operation failed ', 'danger')
                logging.error('transaction certificate add failed')
            else :
                flash('Credential has been issued', 'success')
                link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + subject_workspace_contract[2:] + ':document:' + str(doc_id)
                subject_username = ns.get_username_from_resolver(subject_workspace_contract, mode)
                subject_email = ns.get_data_from_username(subject_username, mode)['email']
                Talao_message.messageHTML('Your professional credential has been issued.', subject_email, 'certificate_issued', {'username': subject_username, 'link': link}, mode)

        # credential has been reviewed
        elif request.form['exit'] == 'validate' :
            ns.update_verifiable_credential(session['credential_id'],
                                        session['host'],
                                        username,
                                        session['call'][3],
                                        "reviewed",
                                        json.dumps(my_credential),
                                        mode)
            issuer_email = ns.get_data_from_username(session['referent'] + '.' + session['host'], mode)['email']
            talent_name = my_credential['credentialSubject']['name']
            subject = 'You have received a professional credential from ' + talent_name + ' to issue'
            Talao_message.messageHTML(subject, issuer_email, 'request_certificate', {'name' : talent_name, 'link' : 'https://talao.co'}, mode)
            flash('Credential has been reviewed and validated', 'success')


        # all exit except delete
        del session['credential_id']
        del session['call']
        return redirect (mode.server +'user/company_dashboard/')



