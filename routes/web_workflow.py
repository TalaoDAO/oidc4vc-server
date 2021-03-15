
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


# request credential to be completed with email
#@app.route('/user/request_certificate/', methods=['GET', 'POST'])
def request_certificate(mode) :
    """ The request call comes from the Search Bar or from the Identity page"""
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
                "signature" : "",
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
                        "draft",
                        id,
                        json.dumps(unsigned_credential),
                        mode)
    reviewer_email = ns.get_data_from_username(request.form['reviewer_username'] + '.' + issuer_username, mode)['email']
    subject = 'You have received a professional certificate from '+ session['name'] + ' for review'
    Talao_message.messageHTML(subject, reviewer_email, 'request_certificate', {'name' : session['name']}, mode)
    # message to user/Talent
    flash('Your request for an Experience Certificate has been registered for review.', 'success')
    return redirect (mode.server + 'userte/issuer_explore/?issuer_username=' + issuer_username)

def company_dashboard(mode) :
    """
    # @route
    """
    # created, user_name, reviewer_name, manager_name, status, credential, id
    manager_select = ""
    manager_list = ns.get_employee_list(session['host'],'manager', 'all', mode)
    for manager in manager_list :
        manager_select += """<option value=""" + manager['username'].split('.')[0]  + """>""" + manager['username'].split('.')[0] + """</option>"""

    reviewer_select = ""
    reviewer_list = ns.get_employee_list(session['host'], 'reviewer', 'all', mode)
    for reviewer in reviewer_list :
        reviewer_select += """<option value=""" + reviewer['username'].split('.')[0]  + """>""" + reviewer['username'].split('.')[0] + """</option>"""

    if session['role'] == 'reviewer' :
        manager_query = 'all'
        reviewer_query = session['username'].split('.')[0]
    else :
        manager_query = 'all'
        reviewer_query = 'all'

    if request.method == 'GET' :

        signed = draft = unsigned = ""
        if session['role'] == 'manager' :
            unsigned = "checked"
            status = ("unsigned","","")
        elif session['role'] == 'reviewer' :
            draft = 'checked'
            status = ('draft',"","")
        else :
            draft = signed = unsigned = "checked"
            status = ('draft', 'unsigned', 'signed')

        credential_list = credential_list_html(session['host'], manager_query, reviewer_query, status, mode)
        return render_template('company_dashboard.html',
                                **session['menu'],
                                credential_list=credential_list,
                                draft=draft,
                                unsigned=unsigned,
                                signed=signed,
                                reviewer_select=reviewer_select,
                                manager_select=manager_select)

    if request.method == 'POST' :
        status = (request.form.get('draftbox', ""), request.form.get('unsignedbox', ""), request.form.get('signedbox', ""))
        draft = "checked" if request.form.get('draftbox') else ""
        signed = "checked" if request.form.get('signedbox') else ""
        unsigned = "checked" if request.form.get('unsignedbox') else ""
        credential_list = credential_list_html(session['host'], manager_query, reviewer_query, status, mode)
        return render_template('company_dashboard.html',
                                 **session['menu'],
                                credential_list=credential_list,
                                draft=draft,
                                unsigned=unsigned,
                                signed=signed,
                                reviewer_select=reviewer_select,
                                manager_select=manager_select)

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
        return render_template ('issue_experience_certificate_workflow.html',
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

        # credential signature
        elif request.form.get('exit') == 'sign' :
            # add manager signature ipfs file id
            manager_workspace_contract = ns.get_data_from_username(session['username'], mode)['identity_workspace_contract']
            my_credential['credentialSubject']['signature'] = get_image(manager_workspace_contract, 'signature', mode)

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
                Talao_message.messageHTML('Your skill certificate', subject_email, 'certificate_issued', {'username': subject_username, 'link': link}, mode)

        # review fo credential
        elif request.form['exit'] == 'validate' :
              ns.update_verifiable_credential(session['credential_id'],
                                        session['host'],
                                        username,
                                        session['call'][3],
                                        "unsigned",
                                        json.dumps(my_credential),
                                        mode)

        # all exit except delete
        del session['credential_id']
        del session['call']
        return redirect (mode.server +'user/company_dashboard/')



