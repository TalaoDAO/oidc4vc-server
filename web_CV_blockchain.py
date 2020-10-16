
import copy
import os.path
from os import path
from flask import Flask, session, send_from_directory, flash
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
import requests
import shutil
from flask_fontawesome import FontAwesome
import json
from sys import getsizeof
import time

# dependances
from protocol import Document, read_profil, Identity, Claim
#import environment
import constante
import ns
import analysis




#@app.route('/resume/', methods=['GET'])
def resume(mode) :
    """ This is always an external entry point"""

    issuer_workspace_contract = request.args. get('workspace_contract')
    if issuer_workspace_contract is None :
        abort(403)
    issuer_explore = Identity(issuer_workspace_contract, mode, authenticated=False)

    if issuer_explore.type == 'person' :
        session['resume']= issuer_explore.__dict__
        """ clean up """
        del session['resume']['mode']
        del session['resume']['file_list']
        del session['resume']['experience_list']
        del session['resume']['education_list']
        del session['resume']['other_list']
        del session['resume']['kbis_list']
        del session['resume']['kyc_list']
        del session['resume']['certificate_list']
        del session['resume']['partners']
        del session['resume']['synchronous']
        del session['resume']['authenticated']
        del session['resume']['rsa_key']
        del session['resume']['relay_activated']
        del session['resume']['private_key']
        del session['resume']['category']
        session['resume']['topic'] = 'resume'

        # personal
        Topic = {'firstname' : 'Firstname',
                'lastname' : 'Lastname',
                'about' : 'About',
                'profil_title' : 'Title',
                'birthdate' : 'Birth Date',
                'contact_email' : 'Contact Email',
                'contact_phone' : 'Contact Phone',
                'postal_address' : 'Postal Address',
                'education' : 'Education'}
        issuer_username =     ns.get_username_from_resolver(issuer_workspace_contract, mode)
        issuer_username = 'Unknown' if issuer_username is None else issuer_username
        issuer_personal = """<span><b>Username</b> : """ + issuer_username +"""<br>"""
        for topic_name in issuer_explore.personal.keys() :
            if issuer_explore.personal[topic_name]['claim_value'] is not None :
                topicname_id = 'did:talao:' + mode.BLOCKCHAIN + ':' + issuer_workspace_contract[2:] + ':claim:' + issuer_explore.personal[topic_name]['claim_id']
                issuer_personal = issuer_personal + """
                <span><b>"""+ Topic[topic_name] +"""</b> : """+ issuer_explore.personal[topic_name]['claim_value']+"""

                    <a class="text-secondary" href=/certificate/data/?dataId=""" + topicname_id + """:personal>
                        <i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
                    </a>
                </span><br>"""


        # kyc
        if len (issuer_explore.kyc) == 0:
            my_kyc = """<a class="text-danger">No Proof of Identity available</a>"""
        else :
            my_kyc = ""
            for kyc in issuer_explore.kyc :
                kyc_html = """
                <b>Firstname</b> : """+ kyc['firstname'] +"""<br>
                <b>Lastname</b> : """+ kyc['lastname'] +"""<br>
                <b>Birth Date</b> : """+ kyc['birthdate'] +"""<br>

                <b>Sex</b> : """+ kyc['sex'] +"""<br>
                <b>Nationality</b> : """+ kyc['nationality'] + """<br>
                <b>Date of Issue</b> : """+ kyc['date_of_issue']+"""<br>
                <b>Date of Expiration</b> : """+ kyc['date_of_expiration']+"""<br>
                <b>Authority</b> : """+ kyc['authority']+"""<br>
                <b>Country</b> : """+ kyc['country']+"""<br>
                <b>Id</b> : """+ kyc['id']+"""<br>
                <p>

                    <a class="text-secondary" href=/certificate/data/?dataId="""+ kyc['id'] + """:kyc>
                        <i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
                    </a>
                </p>"""
                my_kyc = my_kyc + kyc_html


        # experience
        issuer_experience = ''
        if issuer_explore.experience == [] :
            issuer_experience = """  <a class="text-info">No data available</a>"""
        else :
            for experience in issuer_explore.experience :
                exp_html = """
                    <b>Company</b> : """+experience['company']['name']+"""<br>
                    <b>Title</b> : """+experience['title']+"""<br>
                    <b>Description</b> : """+experience['description'][:100]+"""...<br>
                    <p>
                        <a class="text-secondary" href=/certificate/data/?dataId="""+experience['id'] + """:experience>
                            <i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
                        </a>
                    </p>"""
                issuer_experience = issuer_experience + exp_html + """<hr>"""

        # education
        issuer_education = ''
        if issuer_explore.education == [] :
            issuer_education = """  <a class="text-info">No data available</a>"""
        else :
            for education in issuer_explore.education :
                edu_html = """
                    <b>Organization</b> : """+education['organization']['name']+"""<br>
                    <b>Title</b> : """+education['title']+"""<br>
                    <b>Description</b> : """+education['description'][:100]+"""...<br>
                    <p>
                        <a class="text-secondary" href=/certificate/data/?dataId="""+education['id'] + """:education>
                            <i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
                        </a>
                    </p>"""
                issuer_education = issuer_education + edu_html + """<hr>"""

        # skills
        if issuer_explore.skills is None or issuer_explore.skills.get('id') is None :
            issuer_skills =  """<a class="text-info">No Skills Available</a>"""
        else :
            issuer_skills = ""
            for skill in issuer_explore.skills['description'] :
                skill_html = """
                """+ skill['skill_name'] + """ (""" + skill['skill_level'] + """)""" + """<br>
    <!--            <b>Domain</b> : """+skill['skill_domain'] + """<br>
                <b>Level</b> : """+ skill['skill_level'] + """...<br>
                <p>
                    <a class="text-secondary" href="/user/remove_experience/?experience_id="""  + """>
                        <i data-toggle="tooltip" class="fa fa-trash-o" title="Remove">&nbsp&nbsp&nbsp</i>
                    </a>

                    <a class="text-secondary" href=/certificate/data/?dataId=""" + """:experience>
                        <i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
                    </a>
                </p>  -->"""
                issuer_skills = issuer_skills + skill_html
            issuer_skills = issuer_skills + """
                <p>
                    <a class="text-secondary" href=/certificate/data/?dataId="""+ issuer_explore.skills['id'] + """:skills>
                        <i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
                    </a>
                </p>"""

        # file
        if issuer_explore.identity_file == []:
            my_file = """<a class="text-info">No Files available</a>"""
        else:
            my_file = ""
            is_encrypted = False
            for one_file in issuer_explore.identity_file:
                if one_file.get('content') == 'Encrypted':
                    is_encrypted = True
                    file_html = """
                    <b>File Name</b> : """ + one_file['filename'] + """ ( """ + 'Not available - Encrypted ' + """ ) <br>
                    <b>Created</b> : """ + one_file['created'] + """<br>"""
                else:
                    file_html = """
                    <b>File Name</b> : """ + one_file['filename'] + """ ( """ + one_file['privacy'] + """ ) <br>
                    <b>Created</b> : """ + one_file['created'] + """<br>
                    <a class="text-secondary" href=/user/download/?filename=""" + one_file['filename'] + """>
                        <i data-toggle="tooltip" class="fa fa-download" title="Download"></i>
                    </a>"""
                my_file = my_file + file_html + """<br>"""
            if is_encrypted:
                my_file = my_file + """<a href="/register/">Register to access encrypted Data.</a><br>"""

        # certificates
        issuer_certificates = ""
        if issuer_explore.certificate == [] :
            issuer_certificates = """<a class="text-info">No data available</a>"""
        else :
            for certificate in issuer_explore.certificate :

                certificate_issuer_username = ns.get_username_from_resolver(certificate['issuer']['workspace_contract'], mode)
                certificate_issuer_username = 'Unknown' if certificate_issuer_username is None else certificate_issuer_username
                if certificate['issuer']['category'] == 2001 :
                    certificate_issuer_name = certificate['issuer']['name']
                    certificate_issuer_type = 'Company'
                elif  certificate['issuer']['category'] == 1001 :
                    certificate_issuer_name = certificate['issuer']['firstname'] + ' ' + certificate['issuer']['lastname']
                    certificate_issuer_type = 'Person'
                else :
                    print ('issuer category error, data_user.py')

                if certificate['type'] == 'experience' :
                    cert_html = """
                        <b>Issuer Name</b> : """ + certificate_issuer_name +"""<br>
                        <b>Issuer Username</b> : """ + certificate_issuer_username +"""<br>
                        <b>Issuer Type</b> : """ + certificate_issuer_type +"""<br>
                        <b>Title</b> : """ + certificate['title']+"""<br>
                        <b>Description</b> : """ + certificate['description'][:100]+"""...<br>
                        <b></b><a href= """ + mode.server +  """guest/certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer_workspace_contract[2:] + """:document:""" + str(certificate['doc_id']) + """>Display Certificate</a><br>
                        <p>
                            <a class="text-secondary" href=/certificate/data/?dataId=""" + certificate['id'] + """:certificate>
                                <i data-toggle="tooltip" class="fa fa-search-plus" title="Data Check"></i>
                            </a>
                        </p>"""
                else :
                    cert_html = ""
                issuer_certificates = issuer_certificates + cert_html + """<hr>"""

        services ="""
                <a class="text-success" href="/certificate/certificate_data_analysis/" >Talent Dashboard</a></br>

                <a class="text-success" href="" >Send a memo to this Talent</a></br>

                <a href="/register/" class="text-warning"> Register to get access to other services.</a><br><br>"""

        experiences = []
        for experience in issuer_explore.certificate:
            if experience['type']=='experience':
                experiences.append(experience)
        for experience in issuer_explore.experience:
            experiences.append(experience)

        for i, experience in enumerate(experiences):
            min = i
            DTmin = time.strptime(experience['end_date'], "%Y-%m-%d")
            for j, certi in enumerate(experiences[i::]):
                DTcerti = time.strptime(certi['end_date'], "%Y-%m-%d")
                if DTcerti < DTmin:
                    min = j + i
                    DTmin = DTcerti
            experiences[i] , experiences[min] = experiences[min], experiences[i]
        experiences = experiences[::-1]

        carousel_indicators_experience = """<li data-target="#experience-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
        carousel_rows_experience = ""
        if experiences == []:
            pass
        else :
            nbr_rows = (len(experiences)-1)//3
            for i in range(nbr_rows):
                carousel_indicators_experience += '<li data-target="#experience-carousel" data-slide-to="{}"></li>'.format(i+1)
            for i, experience in enumerate(experiences):
                try:
                    logo = experience['logo']
                except:
                    try :
                        logo = experience['picture']
                    except:
                        logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'

                if logo != None:
                    if not path.exists(mode.uploads_path + logo) :
                        url = 'https://gateway.pinata.cloud/ipfs/'+ logo
                        response = requests.get(url, stream=True)
                        with open(mode.uploads_path + logo, 'wb') as out_file:
                            shutil.copyfileobj(response.raw, out_file)
                            del response

                if i%3==0:
                    carousel_rows_experience += '<div class="carousel-item px-2 {a}"><div class="row" style="flex-direction: row;">'.format(a = "active" if (i == 0) else '')
                carousel_rows_experience += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image text-center h-100" style="background-color: white;" ><img src="""
                #image
                try:
                    carousel_rows_experience +=""""{}" style="height: 200px;" alt="sample59"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
                except:
                    carousel_rows_experience +=""""https://s3-us-west-2.amazonaws.com/s.cdpn.io/331810/sample59.jpg" alt="sample59"/></div><figcaption >"""
                #verified
                if experience['topic']=='experience':
                    carousel_rows_experience += """<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="fa fa-pencil-square-o" style="color: #747474;font-size: 50px;"></i></div>"""
                else:
                    carousel_rows_experience += """<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="material-icons my-auto" style="color: rgb(60,158,255);font-size: 50px;">verified_user</i></div>"""
                #header
                carousel_rows_experience += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + experience['title'] + "</h4></div></div>"
                #body
                carousel_rows_experience += """<hr class="my-1"><p style="font-size: 1em"><b>Referent name: </b>"""

                if experience['issuer']['category']==2001:
                    carousel_rows_experience += experience['issuer']['name'] + """<br><b>Referent type: </b>Company <br>"""
                else:
                    carousel_rows_experience += experience['issuer']['firstname'] + ' ' + experience['issuer']['lastname'] + """<br><b>Referent type: </b>Person <br>"""

                carousel_rows_experience += """<b>Start Date</b> : """ + experience['start_date'] + """<br> """
                carousel_rows_experience += """<b>End Date</b> : """ + experience['end_date'] + """<br>"""

                carousel_rows_experience += "</p>"
                #Footer
                if experience['topic']=='experience':
                    carousel_rows_experience += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
                    carousel_rows_experience += """<a href= /certificate/data/?dataId=""" + experience['id'] + """:experience> </a>"""
                else:
                    carousel_rows_experience += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #1c5289; text-align:center;font-size: 1em;" >Certified by Talao</footer>"""
                    carousel_rows_experience += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer_explore.workspace_contract[2:] + """:document:""" + str(experience['doc_id']) + """></a>"""

                #Lien experiences
                #carousel_rows_experience += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer_explore.workspace_contract[2:] + """:document:""" + str(experience['doc_id']) + """></a>"""

                carousel_rows_experience += """</figure></div>"""
                if (i+1)%3==0 and len(experiences)%3!=0:
                    carousel_rows_experience += '</div></div>'
                if i == len(experiences)-1:
                    carousel_rows_experience += '</div></div>'

        recommendations = []
        for certificate in issuer_explore.certificate:
            if certificate['type'] == "recommendation":
                recommendations.append(certificate)

        carousel_indicators_recommendation = """<li data-target="#recommendation-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
        carousel_rows_recommendation = ""
        if recommendations == []:
            pass
        else:
            nbr_rows = (len(recommendations)-1)//3
            for i in range(nbr_rows):
                carousel_indicators_recommendation += '<li data-target="#recommendation-carousel" data-slide-to="{}"></li>'.format(i+1)
            for i, recommendation in enumerate(recommendations):
                try:
                    logo = recommendation['logo']
                except:
                    try :
                        logo = recommendation['picture']
                    except:
                        logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'

                if logo != None:
                    if not path.exists(mode.uploads_path + logo) :
                        url = 'https://gateway.pinata.cloud/ipfs/'+ logo
                        response = requests.get(url, stream=True)
                        with open(mode.uploads_path + logo, 'wb') as out_file:
                            shutil.copyfileobj(response.raw, out_file)
                            del response

                if i%3==0:
                    carousel_rows_recommendation += '<div class="carousel-item {a}"><div class="row">'.format(a = "active" if (i == 0) else '')
                carousel_rows_recommendation += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image text-center h-100" style="background-color: white;" ><img src="""
                #image
                try:
                    carousel_rows_recommendation +=""""{}" style="height: 200px;" alt="sample59"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
                except:
                    carousel_rows_recommendation +=""""https://s3-us-west-2.amazonaws.com/s.cdpn.io/331810/sample59.jpg" alt="sample59"/></div><figcaption >"""
                #verified
                carousel_rows_recommendation +="""<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="material-icons my-auto" style="color: rgb(60,158,255);font-size: 50px;">verified_user</i></div>"""
                #header
                carousel_rows_recommendation += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + recommendation['title'] + "</h4></div></div>"
                #body
                carousel_rows_recommendation += """<hr class="my-1"><p style="font-size: 1em"><b>Referent name: </b>""" + recommendation['issuer']['firstname'] + " " + recommendation['issuer']['lastname'] + "<br>"
                carousel_rows_recommendation += """<b> Relationship: </b>""" + recommendation['relationship'] + "<br>"
                carousel_rows_recommendation += """<b> Description: </b>""" + recommendation['description'][:150] + "..." +"<br>"

                carousel_rows_recommendation += "</p>"
                #Footer
                carousel_rows_recommendation += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
                #Lien certificates
                carousel_rows_recommendation += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer_explore.workspace_contract[2:] + """:document:""" + str(recommendation['doc_id']) + """></a>"""

                carousel_rows_recommendation += """</figure></div>"""
                if (i+1)%3==0 and len(recommendations)%3!=0:
                    carousel_rows_recommendation += '</div></div>'
                if i == len(recommendations)-1:
                    carousel_rows_recommendation += '</div></div>'

        carousel_indicators_education = """<li data-target="#education-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
        carousel_rows_education = ""
        if issuer_explore.education == []:
            pass
        else:
            educations = issuer_explore.education
            nbr_rows = (len(educations)-1)//3
            for i in range(nbr_rows):
                carousel_indicators_education += '<li data-target="#education-carousel" data-slide-to="{}"></li>'.format(i+1)
            for i, education in enumerate(issuer_explore.education):
                try:
                    logo = education['logo']
                except:
                    try :
                        logo = education['picture']
                    except:
                        logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'

                if logo != None:
                    if not path.exists(mode.uploads_path + logo) :
                        url = 'https://gateway.pinata.cloud/ipfs/'+ logo
                        response = requests.get(url, stream=True)
                        with open(mode.uploads_path + logo, 'wb') as out_file:
                            shutil.copyfileobj(response.raw, out_file)
                            del response

                if i%3==0:
                    carousel_rows_education += '<div class="carousel-item {a}"><div class="row">'.format(a = "active" if (i == 0) else '')
                carousel_rows_education += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image text-center h-100" style="background-color: white;" ><img src="""
                #image
                try:
                    carousel_rows_education +=""""{}" style="height: 200px;" alt="sample59"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
                except:
                    carousel_rows_education +=""""https://s3-us-west-2.amazonaws.com/s.cdpn.io/331810/sample59.jpg" alt="sample59"/></div><figcaption >"""
                #verified
                carousel_rows_education +="""<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="fa fa-pencil-square-o" style="color: #747474;font-size: 50px;"></i></div>"""
                #header
                carousel_rows_education += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + education['title'] + "</h4></div></div>"
                #body
                carousel_rows_education += """<hr class="my-1"><p style="font-size: 1em"><b>Name: </b>""" + education['organization']['name'] + '<br>'

                carousel_rows_education += """<b>Start Date</b> : """ + education['start_date'] + """<br> """
                carousel_rows_education += """<b>End Date</b> : """ + education['end_date'] + """<br>"""

                carousel_rows_education += "</p>"
                #Footer
                carousel_rows_education += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
                #Lien certificates
                carousel_rows_education += """<a href=  /certificate/data/?dataId="""+education['id'] + """:education></a>"""

                carousel_rows_education += """</figure></div>"""
                if (i+1)%3==0 and len(educations)%3!=0:
                    carousel_rows_education += '</div></div>'
                if i == len(educations)-1:
                    carousel_rows_education += '</div></div>'

        skills = []
        for certificate in issuer_explore.certificate:
            if certificate['type'] == "skill":
                print(certificate)
                skills.append(certificate)

        carousel_indicators_skill = """<li data-target="#skill-carousel" data-slide-to="0" class="active" style="margin-bottom: 0;"></li>"""
        carousel_rows_skill = ""
        if skills == []:
            if issuer_explore.skills['description'] != None:
                carousel_rows_skill += '<div class="carousel-item active"><div class="row">'
                carousel_rows_skill += """<div class="col-md-4 mb-2">
                        <figure class="snip1253 mw-100" style="height: 410px; ">
                          <div class="image text-center h-100" style="background-color: white;"><img src="/uploads/QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT" style="height: 200px;" alt="sample59" /></div>
                          <figcaption class="p-0">
                            <div class="row overflow-hidden" style="flex-direction: row;height: 50px">
                              <div class="col bg-transparent px-2" style="max-width:60px;"><i class="fa fa-pencil-square-o" style="color: #747474;font-size: 50px;"></i></div>
                              <div class='col px-0 my-auto'>
                                <h4 class='align-center' style='color: black;font-size: 1.4em'>Self claimed skills</h4>
                              </div>
                            </div>
                            <hr class="my-1">
                            <p class="text-center" style="font-size: 1em;">"""
                for i, skill in enumerate(issuer_explore.skills['description']) :
                    if i<4:
                        carousel_rows_skill += skill['skill_name'] + "<br>"
                    elif i==4:
                        carousel_rows_skill += "..."
                carousel_rows_skill += """</p></figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
                carousel_rows_skill += """<a href=  /data/?dataId="""+ issuer_explore.skills['id'] + """:skills></a>"""
                carousel_rows_skill += """</figure></div>"""
                carousel_rows_skill += '</div></div>'
                carousel_rows_skill += '</div></div>'
        else:
            nbr_rows = (len(skills)-1)//3
            for i in range(nbr_rows):
                carousel_indicators_skill += '<li data-target="#skill-carousel" data-slide-to="{}"></li>'.format(i+1)
            for i, skill in enumerate(skills):
                try:
                    logo = skill['logo']
                except:
                    logo = 'QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT'

                if logo != None:
                    if not path.exists(mode.uploads_path + logo) :
                        url = 'https://gateway.pinata.cloud/ipfs/'+ logo
                        response = requests.get(url, stream=True)
                        with open(mode.uploads_path + logo, 'wb') as out_file:
                            shutil.copyfileobj(response.raw, out_file)
                            del response

                if i%3==0:
                    carousel_rows_skill += '<div class="carousel-item {a}"><div class="row">'.format(a = "active" if (i == 0) else '')
                carousel_rows_skill += """<div class="col-md-4 mb-2" ><figure class="snip1253 mw-100" style="height: 410px; "><div class="image text-center h-100" style="background-color: white;" ><img src="""
                #image
                try:
                    carousel_rows_skill +=""""{}" style="height: 200px;" alt="sample59"/></div><figcaption class="p-0">""".format("/uploads/"+ logo)
                except:
                    carousel_rows_skill +=""""https://s3-us-west-2.amazonaws.com/s.cdpn.io/331810/sample59.jpg" alt="sample59"/></div><figcaption >"""
                #verified
                carousel_rows_skill +="""<div class="row overflow-hidden" style="flex-direction: row;height: 50px"><div class="col bg-transparent px-2" style="max-width:60px;" ><i class="material-icons my-auto" style="color: rgb(60,158,255);font-size: 50px;">verified_user</i></div>"""
                #header
                carousel_rows_skill += "<div class='col px-0 my-auto'><h4 class='align-center' style='color: black;font-size: 1.4em'>" + skill['title'] + "</h4></div></div>"
                #body
                carousel_rows_skill += """<hr class="my-1"><p class="text-center" style="font-size: 1em;">"""

                lines = skill['description'].split("\n")
                for l in lines:
                    print(l)
                    carousel_rows_skill +=  l.strip("\r") + "<br>"

                carousel_rows_skill += "</p>"
                #Footer
                carousel_rows_skill += """</figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #1c5289; text-align:center;font-size: 1em;" >Certified by Talao</footer>"""
                #Lien certificates
                carousel_rows_skill += """<a href=  """+ mode.server + """certificate/?certificate_id=did:talao:""" + mode.BLOCKCHAIN + """:""" + issuer_explore.workspace_contract[2:] + """:document:""" + str(skill['doc_id']) + """></a>"""

                carousel_rows_skill += """</figure></div>"""
                if (i+1)%3==0 and len(skills)%3!=0:
                    carousel_rows_skill += '</div></div>'
                if i == len(skills)-1:
                    created_row = False
                    if i%3==0:
                        carousel_rows_skill += '<div class="carousel-item"><div class="row">'
                        created_row = True
                    carousel_rows_skill += """<div class="col-md-4 mb-2">
                            <figure class="snip1253 mw-100" style="height: 410px; ">
                              <div class="image text-center h-100" style="background-color: white;"><img src="/uploads/QmSbxr8xkucse2C1aGMeQ5Wt12VmXL96AUUpiBuMhCrrAT" style="height: 200px;" alt="sample59" /></div>
                              <figcaption class="p-0">
                                <div class="row overflow-hidden" style="flex-direction: row;height: 50px">
                                  <div class="col bg-transparent px-2" style="max-width:60px;"><i class="fa fa-pencil-square-o" style="color: #747474;font-size: 50px;"></i></div>
                                  <div class='col px-0 my-auto'>
                                    <h4 class='align-center' style='color: black;font-size: 1.4em'>Self claimed skills</h4>
                                  </div>
                                </div>
                                <hr class="my-1">
                                <p class="text-center" style="font-size: 1em;">"""
                    for i, skill in enumerate(issuer_explore.skills['description']) :
                        if i<4:
                            carousel_rows_skill += skill['skill_name'] + "<br>"
                        elif i==4:
                            carousel_rows_skill += "..."
                    carousel_rows_skill += """</p></figcaption><footer class="w-100" style="position: absolute; bottom:0; background-color: #c9c9c9; text-align:center;font-size: 1em; color:black;">Self claim</footer>"""
                    carousel_rows_skill += """<a href=  /data/?dataId="""+ issuer_explore.skills['id'] + """:skills></a>"""
                    carousel_rows_skill += """</figure></div>"""

                    if created_row:
                        carousel_rows_skill += '</div></div>'
                    carousel_rows_skill += '</div></div>'

        return render_template('./CV_blockchain.html',
                            issuer_name=issuer_explore.name,
                            issuer_profil_title = issuer_explore.profil_title,
                            kyc=my_kyc,
                            personal=issuer_personal,
                            experience=issuer_experience,
                            skills=issuer_skills,
                            certificates=issuer_certificates,
                            education=issuer_education,
                            services=services,
                            issuer_picturefile=issuer_explore.picture,
                            digitalvault=my_file,
                            carousel_indicators_experience=carousel_indicators_experience,
                            carousel_indicators_recommendation=carousel_indicators_recommendation,
                            carousel_indicators_education=carousel_indicators_education,
                            carousel_indicators_skill=carousel_indicators_skill,
                            carousel_rows_experience=carousel_rows_experience,
                            carousel_rows_recommendation=carousel_rows_recommendation,
                            carousel_rows_education=carousel_rows_education,
                            carousel_rows_skill=carousel_rows_skill)
    # issuer is a company
    else :
        abort(403)
