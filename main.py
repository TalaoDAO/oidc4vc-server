"""
test
Main script to start web server through Gunicorn
Arguments of main.py are in gunicornconf.py (global variables) :
$ gunicorn -c gunicornconf.py  --reload wsgi:app

if script is launched without Gunicorn, setup environment variables first :
$ export MYCHAIN=talaonet
$ export MYENV=livebox
$ export AUTHLIB_INSECURE_TRANSPORT=1
$ python main.py

Many views are inside this script, others are in web_modules.py. See Centralized routes.

"""

from Crypto.PublicKey import RSA
import sys
import os
import os.path, time
from flask import Flask, session, send_from_directory, flash, jsonify, render_template_string
from flask import request, redirect, render_template,abort, Response
from flask_session import Session
from flask_fontawesome import FontAwesome
import random
import csv
from datetime import timedelta, datetime
import json
from werkzeug.utils import secure_filename
import threading
import copy
import urllib.parse
import unidecode
from eth_keys import keys
from eth_utils import decode_hex
import redis
import requests
from Crypto.PublicKey import RSA
from authlib.jose import jwt

# dependances
import Talao_message
import Talao_ipfs
import createcompany
import createidentity
import constante
from protocol import ownersToContracts, contractsToOwners, save_image, partnershiprequest, remove_partnership, get_image, authorize_partnership, reject_partnership, destroy_workspace
from protocol import delete_key, has_key_purpose, add_key
from protocol import Claim, File, Identity, Document, read_profil
import environment
import hcode
import ns
import analysis
import history
import privatekey
import sms
import QRCode
import directory
import siren
import talao_x509

# Centralized  routes
import web_create_identity
import web_create_company_cci
import web_certificate
import web_data_user
import web_issue_certificate
import web_skills
import web_CV_blockchain
import web_issuer_explore

# API server
from config_apiserver import config_api_server

# Environment variables set in gunicornconf.py  and transfered to environment.py
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')

if not mychain or not myenv :
    print('Error : environment variables missing')
    print('Error : export MYCHAIN=talaonet, export MYENV=livebox, export AUTHLIB_INSECURE_TRANSPORT=1')
    exit()
if mychain not in ['mainet', 'ethereum', 'rinkeby', 'talaonet'] :
    print('Error : wrong chain')
    exit()

# Environment setup
print('Success : start to init environment')
mode = environment.currentMode(mychain,myenv)
print('Success : end of init')

# Global variable
exporting_threads = {}

# Constants
FONTS_FOLDER='templates/assets/fonts'
RSA_FOLDER = './RSA_key/' + mode.BLOCKCHAIN
VERSION = "0.4.0"
API_SERVER = True

# Flask and Session setup
app = Flask(__name__)
app.jinja_env.globals['Version'] = VERSION
app.jinja_env.globals['Created'] = time.ctime(os.path.getctime('main.py'))
app.jinja_env.globals['Chain'] = mychain.capitalize()
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_COOKIE_NAME'] = 'talao'
app.config['SESSION_TYPE'] = 'redis' # Redis server side session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=180) # cookie lifetime
app.config['SESSION_FILE_THRESHOLD'] = 100
app.config['SECRET_KEY'] = "OCML3BRawWEUeaxcuKHLpw" + mode.password
app.config['RSA_FOLDER'] = RSA_FOLDER
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["jpeg", "jpg", "png", "gif"]

sess = Session()
sess.init_app(app)

# define everything about API server, constante and route for endpoints
if API_SERVER :
    print('Info : API server init')
    config_api_server(app, mode)

# bootstrap font managment  -> recheck if needed !!!!!
fa = FontAwesome(app)

# info release
print('Info : ',__file__, " created: %s" % time.ctime(os.path.getctime(__file__)))

# Centralized @route for create identity
app.add_url_rule('/register/',  view_func=web_create_identity.register, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/register/password/',  view_func=web_create_identity.register_password, methods = [ 'GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/register/code/', view_func=web_create_identity.register_code, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/register/post_code/', view_func=web_create_identity.register_post_code, methods = ['POST', 'GET'], defaults={'mode': mode})

# Centralized @route for create company CCI
app.add_url_rule('/create_company_cci/',  view_func=web_create_company_cci.cci, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/create_company_cci/password/',  view_func=web_create_company_cci.cci_password, methods = [ 'GET','POST'], defaults={'mode': mode})
app.add_url_rule('/create_company_cci/code/', view_func=web_create_company_cci.cci_code, methods = ['GET','POST'], defaults={'mode': mode})
app.add_url_rule('/create_company_cci/post_code/', view_func=web_create_company_cci.cci_post_code, methods = ['GET','POST'], defaults={'mode': mode})

# Centralized @route to display certificates
app.add_url_rule('/certificate/',  view_func=web_certificate.show_certificate, defaults={'mode': mode})
app.add_url_rule('/guest/certificate/',  view_func=web_certificate.show_certificate, defaults={'mode': mode})  # idem previous
app.add_url_rule('/certificate/verify/',  view_func=web_certificate.certificate_verify, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/certificate/issuer_explore/',  view_func=web_certificate.certificate_issuer_explore, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/guest/',  view_func=web_certificate.certificate_issuer_explore, methods = ['GET'], defaults={'mode': mode}) # idem previous
app.add_url_rule('/certificate/data/',  view_func=web_certificate.certificate_data, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/certificate/certificate_data_analysis/',  view_func=web_certificate.certificate_data_analysis, methods = ['GET'], defaults={'mode': mode})

# Centralized route for the Blockchain CV
app.add_url_rule('/resume/', view_func=web_CV_blockchain.resume, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/board/', view_func=web_CV_blockchain.board, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route fo Issuer explore
app.add_url_rule('/user/issuer_explore/', view_func=web_issuer_explore.issuer_explore, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route for user, data, login
app.add_url_rule('/wc_login/',  view_func=web_data_user.wc_login, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/wc_login_sign/',  view_func=web_data_user.wc_login_sign, methods = ['GET', 'POST'], defaults={'mode': mode})

app.add_url_rule('/user/',  view_func=web_data_user.user, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/data/',  view_func=web_data_user.data, methods = ['GET'], defaults={'mode': mode})
app.add_url_rule('/logout/',  view_func=web_data_user.logout, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/forgot_username/',  view_func=web_data_user.forgot_username, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/forgot_password/',  view_func=web_data_user.forgot_password, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/forgot_password_2/',  view_func=web_data_user.forgot_password_2, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/login/authentification/',  view_func=web_data_user.login_authentification, methods = ['POST'], defaults={'mode': mode})
app.add_url_rule('/login/',  view_func=web_data_user.login, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/',  view_func=web_data_user.login, methods = ['GET', 'POST'], defaults={'mode': mode}) # idem previous
app.add_url_rule('/starter/',  view_func=web_data_user.starter, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/use_my_own_address/',  view_func=web_data_user.use_my_own_address, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/user/advanced/',  view_func=web_data_user.user_advanced, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/user/account/',  view_func=web_data_user.user_account, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/company/',  view_func=web_data_user.company, methods = ['GET', 'POST'])
app.add_url_rule('/privacy/',  view_func=web_data_user.privacy, methods = ['GET', 'POST'])
app.add_url_rule('/user/two_factor/',  view_func=web_data_user.two_factor, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route issuer for issue certificate for guest
app.add_url_rule('/issue/',  view_func=web_issue_certificate.issue_certificate_for_guest, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/issue/create_authorize_issue/',  view_func=web_issue_certificate.create_authorize_issue, methods = ['GET', 'POST'], defaults={'mode': mode})
app.add_url_rule('/issue/logout/',  view_func=web_issue_certificate.issue_logout, methods = ['GET', 'POST'], defaults={'mode': mode})

# Centralized route issuer for skills
app.add_url_rule('/user/update_skills/',  view_func=web_skills.update_skills, methods = ['GET', 'POST'], defaults={'mode': mode})

@app.errorhandler(403)
def page_abort(e):
    print('Warning : appel abort 403')
    # note that we set the 403 status explicitly
    return redirect(mode.server + 'login/')

# Check if session is active and access is fine. To be used for all routes, excetp external call
def check_login() :
    """ check if the user is correctly logged. This function is called everytime a user function is called """
    if not session.get('username') :
        abort(403)
    else :
        return session['username']

# helper
def is_username_in_list(my_list, username) :
    for user in my_list :
        if user['username'] == username :
            return True
    return False
# helper
def is_username_in_list_for_partnership(partner_list, username) :
    for partner in partner_list :
        if partner['username'] == username and partner['authorized'] not in ['Removed',"Unknown", "Rejected"]:
            return True
    return False

#HomePage
@app.route('/homepage/', methods=['GET'])
def homepage() :
    check_login()
    if request.method == 'GET' :
        return render_template('homepage.html', **session['menu'])

# picture
""" This is to download the user picture or company logo to the uploads folder """
@app.route('/user/picture/', methods=['GET', 'POST'])
def picture() :
    check_login()
    if request.method == 'GET' :
        if request.args.get('badtype') == 'true' :
            flash('Only "JPEG", "JPG", "PNG" files accepted', 'warning')
        return render_template('picture.html',**session['menu'])
    if request.method == 'POST' :
        myfile = request.files['croppedImage']
        filename = "profile_pic.jpg"
        myfile.save(os.path.join(mode.uploads_path, filename))
        picturefile = mode.uploads_path  + filename
        session['picture'] = save_image(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, picturefile, 'picture',mode, synchronous = False)
        Talao_ipfs.get_picture(session['picture'], mode.uploads_path+ '/' + session['picture'])
        session['menu']['picturefile'] = session['picture']
        return redirect(mode.server + 'user/')

@app.route('/user/success/', methods=['GET'])
def success() :
    check_login()
    if request.method == 'GET' :
        if session['type'] == 'person' :
            flash('Picture has been updated', 'success')
        else :
            flash('Logo has been updated', 'success')
        return redirect(mode.server + 'user/')

@app.route('/user/update_search_setting/', methods=['POST'])
def update_search_setting() :
    check_login()
    try:
        response = directory.update_user(mode, session, request.form["CheckBox"] == "on")
        if response == "User already in database":
            flash('Your Name was already in the search bar', 'success')
        elif response:
            flash('Your Name has been added to the search bar', 'success')
        else:
            flash('There has been an error, please contact support', 'warning')
    except:
        directory.update_user(mode, session, False)
        flash('Your Name has been removed from the search bar', 'success')
    return redirect(mode.server + 'user/')


@app.route('/user/update_phone/', methods=['GET', 'POST'])
def update_phone() :
    check_login()
    if request.method == 'GET' :
        return render_template('update_phone.html', **session['menu'], phone=session['phone'])
    if request.method == 'POST' :
        _phone = request.form['phone']
        code = request.form['code']
        phone = code + _phone
        if _phone == "" :
            flash('Your phone number has been deleted.', 'success')
            ns.update_phone(session['username'], None, mode)
            session['phone'] = ""
        elif sms.check_phone(phone, mode) :
            ns.update_phone(session['username'], phone, mode)
            session['phone'] = phone
            flash('Your phone number has been updated.', 'success')
        else :
            flash('Incorrect phone number.', 'warning')
        return redirect(mode.server + 'user/')

@app.route('/user/update_password/', methods=['GET', 'POST'])
def update_password() :
    check_login()
    if request.method == 'GET' :
        return render_template('update_password.html', **session['menu'])
    if request.method == 'POST' :
        current_password = request.form['current_password']
        new_password = request.form['password']
        if not ns.check_password(session['username'],current_password, mode) :
            flash ('Wrong password', 'warning')
            return render_template('update_password.html', **session['menu'])
        ns.update_password(session['username'], new_password, mode)
        flash ('Password updated', 'success')
        return redirect(mode.server + 'user/')

# signature
@app.route('/user/signature/', methods=['GET', 'POST'])
def signature() :
    check_login()
    my_signature = session['signature']
    if request.method == 'GET' :
        if request.args.get('badtype') == 'true' :
            flash('Only "JPEG", "JPG", "PNG" files accepted', 'warning')
        return render_template('signature.html', **session['menu'], signaturefile=my_signature)
    if request.method == 'POST' :
        myfile = request.files['croppedImage']
        filename = "signature.png"
        myfile.save(os.path.join(mode.uploads_path, filename))
        signaturefile = mode.uploads_path + '/' + filename
        session['signature'] = save_image(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, signaturefile, 'signature', mode, synchronous = False)
        Talao_ipfs.get_picture(session['signature'], mode.uploads_path+ '/' + session['signature'])
        flash('Your signature has been updated', 'success')
        return redirect(mode.server + 'user/')

@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'GET' :
        return render_template('report.html', **session['menu'])
    if request.method == 'POST' :
        email = "thierry.thevenet@talao.io"
        email2 = "alexandre.leclerc@talao.io"
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
        Talao_message.message(subject, email2, messagetext, mode)
        flash('The bug has been reported ! Thank you for your help ! ', "success")
        return redirect(mode.server + 'homepage/')

# Job offer
@app.route('/view_job_offer', methods=['GET', 'POST'])
def view_job_offer() :
    check_login()
    if request.method == 'GET' :
        offer_num = request.args.get('offer')
        offer = dict()
        if offer_num == "1":
            offer['number'] = 1
            offer['title'] = "Senior Software Engineer"
            offer['company'] = "Message Bird"
            offer['location'] = "(remote) Time zone: Worldwide"
            offer['position'] = "CDD"
            offer['logo'] = "https://remoteok.io/assets/jobs/9c5575e19af49e0b36f113ca19c070111606338825.png?1606338826"
            offer['description'] = """What you’ll do<br><br>- Help design and build a performant, scalable and fault-tolerant communication platform.<br><br>- Team with engineers to solve system design and implementation problems (and get a thrill out of every triumph!).<br><br>- Work with and enable engineers from other teams who interact with the platform.<br><br>- Problem-solve issues based on business/customer need and impact, working with technical and non-technical stakeholders.<br><br>- Teach others: One of the most meaningful tasks of a Senior Engineer is improving the knowledge level of the team members.<br><br>- You will flourish working in a hyper-growth environment where the next project is ready to be picked up.<br><br>What you’ll bring<br><br>- At least 5 years of relevant software development experience<br><br>- Strong experience in Golang is a must<br><br>- Strong experience working with relational databases and non-relational data stores (like MySQL, Cassandra & Redis).<br><br>- Experience with Docker, Containers and Kubernetes.<br><br>- Practical and theoretical knowledge of development patterns, software architectures and design patterns (TDD, Event-Driven, SOLID, Hexagonal, DDD).<br><br>- Knowledge of (cloud) infrastructure principles (load balancing, high availability, containerized services, database configurations) is a bonus.<br><br>- Strong verbal and written communication skills in English.<br><br>- Ability of teaching others and helping them grow.<br><br>Psst… some added perks<br><br>- The ability to Work Anywhere — literally anywhere you want, as long as it’s in the same time zone as your team (yup… you read that right!). This comes with the added benefit of finding the right work-life balance for you by following our 80/20 rule.<br><br>- WFH office set-up allowance to make sure you have all you need to “get shit done” in an ergonomically-friendly manner.<br><br>- Top-notch work equipment (including Bose headphones!).<br><br>- MessageBird swag to keep you well-dressed.<br><br>- The occasional (virtual) company-wide and team events. <br><br>- A team of (fast-)forward-thinking, talented and fun colleagues from more than 50 countries!<br><br>MessageBird is an equal opportunity employer. If you think you’re a match for this role and can bring some great skills to the MessageBird team, please apply! We’re excited to get to know you. """
        if offer_num == "2":
            offer['number'] = 2
            offer['title'] = "Head of Demand Generation"
            offer['company'] = "Catapult"
            offer['location'] = "(remote) Time zone: Worldwide"
            offer['position'] = "CDD"
            offer['logo'] = "https://remoteok.io/assets/jobs/e2010fabb8ee4790893304be300b1a1a1606338563.png?1606338563"
            offer['description'] = """We’re looking for a candidate who has a proven track record of driving growth in a B2B SaaS environment. As Head of Demand Generation you’ll be responsible for all aspects of developing and executing Catapult’s demand generation strategy. It’s a broad role that includes demand generation, ABM, online advertising, content marketing, SEO, email, web and more. It’s a fantastic opportunity for a candidate who is looking to have a significant impact on the growth trajectory of an exciting, young tech company that’s transforming the way people work.<br><br>**Responsibilities:**<br>* Grow pipeline and sales qualified opportunities through effective creation of a high quality and scalable demand generation operation<br>* Design, execute and track performance of ABM marketing programs to engage and influence our key segments<br>* Excel within marketing automation platforms to optimize our lead generation & lead nurturing processes through email campaigns, content marketing, paid media and social media channels<br>* Manage the demand generation budget thoughtfully, making strategic bets on key investments<br>* Establish data-oriented practices to optimize performance and continually improve the efficiency and impact of marketing channels; SEM, SEO, email, display and retargeting<br>* Work closely with Product Marketing to manage Catapult’s website and optimise conversion of leads through organic and paid traffic<br>* Take responsibility for Catapult’s marketing tech stack, review current stack and make recommendations for tech investments that support growth<br>* Stay current on growth marketing trends, best practices and benchmarks and drive experimentation and evolution of our marketing channels<br>* Monitor pipeline data and performance regularly, and identify opportunities and strategies to improve<br><br><br>**Requirements**<br>* Proven track record of driving growth through varied marketing channels at a B2B company targeting the enterprise and/or mid-market segment<br>* 5+ years of experience in B2B marketing and demand generation<br>* A strong understanding of ABM, marketing automation, lead-scoring, segmentation, revenue attribution, influence, and ROI<br>* Proficient in digital advertising / paid social platforms - Google Adwords, LinkedIn, and Twitter<br>* Data-driven with excellent Analytical skills; you take data-driven decisions based on thorough analysis of campaign performances<br>* Excellent communication skills; you are able to clearly and concisely craft messages to internal and external stakeholders<br>* Design skills are a plus<br><br><br>**Benefits of working at Catapult**<br>* Competitive salary & Equity<br><br>* Remote working: Catapult is a fully remote company with our small team spread across 6 countries currently. We believe in doing work we love, from places we love! Whether you prefer to work from home or an office, we support with coworking costs and a solid home-office setup.<br><br>* Flexible hours: We believe that performance should be measured on output, and not when and how you work, so at Catapult you will find a lot of flexibility to design your own rhythm of work.<br><br>* A social work-life: We are a small and sociable group. When we're in lock-down we make an effort to stay connected with Zoom kick-offs every morning, 1-1s, and social catch-ups over quizzes and beer. Post Covid we expect to meet up every quarter for a few days of workshops and fun.<br><br>* Professional development: We think learning is key to winning so we have created a learning budget of £1,000 per person to spend on courses, conferences, coaching or whatever you think will help you improve and grow. Additionally we have a 'free books' policy which covers anything you want to read both fiction and nonfiction.<br><br>* Health insurance: We have Vitality health insurance (full package) for those based in the UK and strive to find similar options for other countries.<br><br><br>**About Catapult**<br><br>Catapult’s vision is to make work work. Millions of people work frontline jobs that provide income but fail to provide flexibility, control and balance. Catapult’s technology allows frontline employers to get more from their workforce, by giving their workforce more of the work they need.<br><br>We’re a small and ambitious team that work closely in sync while each taking real ownership of our respective areas. We are motivated by building intelligent solutions that drive meaningful value to both employers and employees.	<br><br>#Salary<br>$100,000 — $140,000<br><br><br>#Location<br>🌏 Worldwide """
        if offer_num == "3":
            offer['number'] = 3
            offer['title'] = "WP All Import Customer Support"
            offer['company'] = "Soflyy"
            offer['location'] = "(remote) Time zone: Worldwide"
            offer['position'] = "CDD"
            offer['logo'] = "https://remoteok.io/assets/jobs/cc56ebc7b233b6f48fecad5a443a6ced1606287634.png?1606287634"
            offer['description'] = """## $30 per hour, 30 hours per week.<br>Our team is 100% remote and distributed across the world. We have team members in Australia, the US, Canada, Thailand, Germany, Argentina, South Africa, the UK, and Romania. It doesn't matter where you live or what time zone you're in.<br><br>Your main responsibility will be to reply to customers asking for help with WP All Export and WP All Import. You need to love to help others and be able to keep it friendly even when dealing with difficult customers. You need to enjoy the whole process of turning anxious, confused, or angry customers into happy ones. You must be an excellent writer. We want our support replies to be friendly, easy to understand, and concise.<br><br>--------<br><br>### Flexibility<br>We are a small team but we try to give everyone as much flexibility as possible. Flexibility means that you can work in the mornings, or the evenings, or both, or in the middle of the night, or whatever. It means you can take two weeks off to go on a trip. It means you can wake up and decide you don't feel like working and take the day off without telling anyone.<br><br>It doesn't mean you can work 50hrs one week and then 20hrs the next. It doesn't mean that you can work two 15hr days and then take the rest of the week off.<br><br>--------<br><br>### Responsibilities<br>- Responding to customer support inquiries<br>- Adding to and improving our documentation<br>- Aggregating customer feedback and assisting us with development/product roadmap decisions<br>- Writing concise bug reports based on support tickets that are a result of bugs in WP All Export or WP All Import<br>- Testing development versions of WP All Import and WP All Export<br>- Developing add-ons for WP All Import<br><br>--------<br><br>### Requirements<br>- The only thing we care about is the ability to provide high-quality customer support to our clients. The more of these boxes you can tick the better, in descending order of importance:<br>- Minimum availability of 30 hours per week.<br>- Flawless written English.<br>- Expert-level WordPress knowledge. Extensive experience with WordPress including troubleshooting, debugging, plugin development, and WordPress database structure.<br>- At least intermediate-level PHP knowledge. Ability to write PHP functions, work with arrays, and make use of our API: http://www.wpallimport.com/documentation/developers/execute-php/, http://www.wpallimport.com/documentation/developers/action-reference/, and http://www.wpallimport.com/documentation/addon-dev/overview/<br>- Fast and hands-on learner. Able to quickly become familiar with our software and learn new things about WordPress, PHP, and related technologies.<br>- Experience with WooCommerce.<br>- Familiarity with XML and CSV file formats, phpMyAdmin, XPath, debugging and troubleshooting WordPress themes and plugins via FTP, and cPanel and other web hosting control panels.<br><br>--------<br><br>### To Apply<br>Visit https://www.wpallimport.com/hiring/#apply.	<br><br>#Salary<br>$40,000 — $60,000<br><br><br>#Location<br>🌏 Worldwide"""
        if offer_num == "4":
            offer['number'] = 4
            offer['title'] = "Web Developer"
            offer['company'] = "LearnCube"
            offer['location'] = "(remote) Time zone: Worldwide"
            offer['position'] = "CDD"
            offer['logo'] = "https://remoteok.io/assets/jobs/fad53491c6ead3968bd151440ca6474c1606240028.png?1606240028"
            offer['description'] = """Looking to join a fun, highly-talented team that’s working on an edtech product the world really needs right now?<br><br>LearnCube is on a mission to transform live online education across the globe. Through our award-winning online classroom and online school, we help education entrepreneurs to succeed online. We also have a special strength in online language education, where we work with iconic language education companies like Babbel.<br><br>We're growing fast and need your help.<br><br><br>**More about LearnCube and our development stack:**<br> <br>LearnCube is a leading edtech SAAS provider. Our Virtual Classroom and Online School platform makes it easy for language teachers and tutors to teach online professionally. <br> <br>LearnCube’s customers are individual tutors, edupreneurs, online language schools and tutoring companies.<br> <br>We’re a fast-growing company founded in 2014, based in London but with a “remote-first” culture. <br> <br>As a web developer for LearnCube, you will be working with a close, highly-talented team on our online classroom and online school products.<br> <br>You will have so much more opportunity to learn, contribute and grow professionally with a startup like LearnCube, than you would from working for a big but soulless technology company.<br><br>We use vue.js, Python and Django to build our cutting-edge solution but there’s also plenty of room to build your skills, experiment and play with other exciting technologies.<br><br><br>**What you’ll do:**<br><br>- Contribute to online classroom features and new products. For example, in the last year, we released new homework, large group classroom and breakout room features for our online classroom. <br>Improve the experience for our school administrators, teachers and students through learning analytics and data logging. <br>- Scaling infrastructure is not the focus of your work but we offer a unique opportunity to gain experience if you’re curious. COVID-19 has increased the number of classes we deliver by more than 10-fold with more high-potential opportunities on the horizon. <br>- Collaborate with other areas of LearnCube - customer support, customer success and sales - to improve the business, user experience and customer experience.<br>- Provide some technical customer support for customer queries, especially for our VIP customers using our API products.<br>- Keep up-to-date with best practices and technology.<br>- Support research and development of our most innovative ideas within our “Learncube Labs” including smart ways to improve education through A.I.<br><br><br>**More about the role:**<br><br>- Initial 3-month fixed term contract (remote position) followed by full-time contract if it goes well.<br>- Market-related, competitive salary with a generous vacation policy.<br>- Salary with company bonus.<br>- This a remote position. There is no office!<br>- Think of this also as a 'spring-board' position with lots more opportunity to grow your career into a leadership role if that is your desired path.<br><br><br>**Criteria for a successful candidate:**<br><br>- Honest, humble, highly competent, fast-learner, self-starter and motivated by the mission<br>- Minimum of 2+ years of software development experience<br>- Excellent communication skills and ability to work in a team<br>- Attention to detail<br>- Shows initiative and not shy from taking on responsibility and projects<br>- Ability to adapt and grow (startup life isn’t a straight line)<br>- Able to overlap with European business hours at least once per day<br><br><br>**Bonus points for a successful candidate:**<br><br>- Some experience with VueJS<br>- Some experience with Django<br>- Some experience with MySQL<br>- Experience with WebRTC / Websockets<br>- Experience with Redis<br>- Experience with AWS tech stack<br>- API gateway, Lambda, DynamoDB, ELB, EC2, RDS<br>- Experience with Elasticsearch<br>- Design / UX skills<br>- Association or experience with tutoring or learning spoken languages<br>- Startup experience<br>- Evidence of creating your own products and solutions<br><br><br>**Non-negotiables**<br><br>- Are you a team player and a good person? We have a strict no d///head policy and are not looking for “programming purists”.<br>- Do you have a strong interest in education and edtech? <br>- Are you fluent in spoken and written English? Note, you don’t have to be a perfect native speaker.<br>- Do you already share our values: honesty, trust, grit, motivation, and energy?<br>- Can you demonstrate strong skills in customer support and care, understanding how to work with people and getting them the help they need?<br>- Can you provide evidence of at least 6-12 months of experience working at least 20 hours a week remotely?<br> <br> <br>**LearnCube perks and path**<br><br>- Freedom to live wherever you like as long as you have reliable internet and a permanent residence.<br>- Annual all-expenses-paid team trip to an exciting location in Europe (when it's properly safe to travel again).<br>- A clear career path to lead part of our development and product team as we grow.<br>- We offer a supportive, safe and fun work environment. Whatever gender, race, sexuality, nationality, religion, education, languages or quirks you have (or don’t), we don’t mind. Just bring strong values of honesty, trust, grit, motivation, and energy.<br>- We’ll provide a monthly contribution towards your home-office or favourite local co-working space.<br>- Loads of opportunity for professional development.<br>- Oh… and you’ll feel much more motivated knowing you’re changing the world for the better; improving both the access to and quality of education across the world.<br><br><br>**Final words**<br> <br>Aside from the non-negotiables, please don’t worry if you can’t check absolutely every criteria above (you’re probably more awesome than you think).<br><br><br><br>#Location<br>🌏 Worldwide """
        return render_template('view_job_offer.html', **session['menu'], offer = offer)
    if request.method == 'POST' :
        offer_num = request.args.get('offer')
        email = "alexandre.leclerc@talao.io"
        subject = "New application for your job offer"
        job = ""
        if offer_num == "1":
            job = '"Senior Software Engineer at Message Bird"'
        elif offer_num == "2":
            job = '"Head of Demand Generation at Catapult"'
        elif offer_num == "3":
            job = '"WP All Import Customer Support at Soflyy"'
        elif offer_num == "4":
            job = '"Web Developer at LearnCube"'
        link = session['menu']['clipboard']
        if Talao_message.messageHTML(subject, email, 'job_offer', {'job' : job, 'link': link, 'name' : session['name']}, mode):
            flash('You have succesfulllly applied to this job offer', "success")
            return redirect(mode.server + 'homepage/')
        else:
            flash('Something went wrong please try again or report the bug with the question mark on the bottom right of your screen', 'error')
            return redirect(mode.server + 'homepage/')

# Dashboard, Analysis, history
@app.route('/user/data_analysis/', methods=['GET'])
def data_analysis() :
    check_login()
    if request.method == 'GET' :
        if request.args.get('user') == 'issuer_explore' :
            my_analysis = analysis.dashboard(session['issuer_explore']['workspace_contract'],session['issuer_explore'], mode)
            history_string = history.history_html(session['issuer_explore']['workspace_contract'],15, mode)
        else :
            my_analysis = analysis.dashboard(session['workspace_contract'],session['resume'], mode)
            history_string = history.history_html(session['workspace_contract'],15, mode)
        return render_template('dashboard.html', **session['menu'],    history=history_string,    **my_analysis)

# Test only
@app.route('/user/test/', methods=['GET'])
def test() :
    check_login()
    return render_template('test.html', **session['menu'],test=json.dumps(session['resume'], indent=4))

# Tutorial
@app.route('/user/tutorial/', methods=['GET'])
def tutorial() :
    check_login()
    return render_template('tutorial.html', **session['menu'])

#Prefetch for typehead
@app.route('/prefetch', methods=['GET', 'POST'])
def prefetch() :
    user_list = directory.user_list_search(request.args['q'], mode)
    return json.dumps(user_list)

# search
@app.route('/user/search/', methods=['GET', 'POST'])
def search() :
    check_login()
    if request.method == 'GET' :
        return render_template('search.html', **session['menu'])
    if request.method == 'POST' :
        username_to_search = request.form['username_to_search'].lower()
        if username_to_search == session['username'] :
            flash('Here you are !', 'success')
            return redirect(mode.server + 'user/')
        if not ns.username_exist(username_to_search, mode) :
            flash('Username not found', "warning")
            return redirect(mode.server + 'user/')
        else :
            return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + username_to_search)

# issue certificate
@app.route('/user/issue_certificate/', methods=['GET', 'POST'])
def issue_certificate():
    check_login()
    if not session['private_key'] :
        flash('Relay does not have your Private Key to issue a Certificate', 'warning')
        return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])
    if request.method == 'GET' :
        return render_template('issue_certificate.html',
                                **session['menu'],
                                issuer_username=session['issuer_username'])
    if request.method == 'POST' :
        if request.form['certificate_type'] == 'experience' :
            if len(session['username'].split('.')) == 2 :
                # look for signature of manager
                manager_username = session['username'].split('.')[0]
                manager_workspace_contract = ns.get_data_from_username(manager_username, mode)['workspace_contract']
                session['certificate_signature'] = get_image(manager_workspace_contract, 'signature', mode)
                # look for firstname, lasname and name of manager
                firstname_claim = Claim()
                lastname_claim = Claim()
                firstname_claim.get_by_topic_name(None, None, manager_workspace_contract, 'firstname', mode)
                lastname_claim.get_by_topic_name(None, None, manager_workspace_contract, 'lastname', mode)
                session['certificate_signatory'] = firstname_claim.claim_value + ' ' + lastname_claim.claim_value
            elif session['type'] == 'company' :
                session['certificate_signature'] = session['signature']
                session['certificate_signatory'] = 'Director'
            else :
                session['certificate_signature'] = session['signature']
                session['certificate_signatory'] = session['name']

            return render_template("issue_experience_certificate.html",
                                    **session['menu'],
                                    manager_name=session['certificate_signatory'],
                                    issuer_username=session['issuer_username'],
                                    talent_name=session['issuer_explore']['name'] )
        elif request.form['certificate_type'] == 'skill' :
            return render_template("create_skill_certificate.html",
                                    **session['menu'],
                                    identity_username=session['issuer_username'] )
        elif request.form['certificate_type'] == 'recommendation'  :
            return render_template('issue_recommendation.html',
                                    **session['menu'],
                                    issuer_username=session['issuer_username'],
                                    issuer_name = session['issuer_explore']['name'])
        else :
            flash('This certificate is not implemented yet !', 'warning')
            return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])

# issue experience certificate for person with  with two factor check
@app.route('/user/issuer_experience_certificate/', methods=['GET','POST'])
def issue_experience_certificate():
    """ The signature is the manager's signature except if the issuer is the company """
    check_login()
    # call from two factor checking function
    if request.method == 'GET' :
        if request.args.get('two_factor') == "True" :     # code is correct
            workspace_contract_to = ns.get_data_from_username(session['issuer_username'], mode)['workspace_contract']
            address_to = contractsToOwners(workspace_contract_to, mode)
            execution = Document('certificate').add(session['address'],
                        session['workspace_contract'],
                        address_to,
                        workspace_contract_to,
                        session['private_key_value'],
                        session['certificate_to_sign'],
                        mode,
                        mydays=0,
                        privacy='public',
                        synchronous=True,
                        request=request)
            if not execution[0] :
                flash('Transaction failed ', 'danger')
            else :
                flash('Certificate has been issued', 'success')
        else :   # fail to check code
            print('Warning : incorrect code in issue experience certificate ', request.args.get('two_factor'))
        del session['certificate_signature']
        del session['certificate_signatory']
        del session['certificate_to_sign']
        return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])
    # call from issue_experience_certificate.html
    if request.method == 'POST' :
        session['certificate_to_sign'] = {
                    "version" : 1,
                    "type" : "experience",
                    "title" : request.form['title'],
                    "description" : request.form['description'],
                    "start_date" : request.form['start_date'],
                    "end_date" : request.form['end_date'],
                    "skills" : request.form['skills'].split(','),
                    "score_recommendation" : request.form['score_recommendation'],
                    "score_delivery" : request.form['score_delivery'],
                    "score_schedule" : request.form['score_schedule'],
                    "score_communication" : request.form['score_communication'],
                    "logo" : session['picture'],
                    "signature" : session['certificate_signature'],
                    "manager" : session['certificate_signatory'],
                    "reviewer" : request.form['reviewer_name']}
        # call the two factor checking function :
        return redirect(mode.server + 'user/two_factor/?callback=user/issuer_experience_certificate/')

# issue recommendation for person with two factor check
@app.route('/user/issue_recommendation/', methods=['GET', 'POST'])
def issue_recommendation():
    check_login()
     # call from two factor checking function
    if request.method == 'GET' :
        if request.args.get('two_factor') == "True" :     # code is correct
            execution = Document('certificate').add(session['address'],
                                        session['workspace_contract'],
                                        session['issuer_explore']['address'],
                                        session['issuer_explore']['workspace_contract'],
                                        session['private_key_value'],
                                        session['recommendation_to_sign'],
                                        mode,
                                        mydays=0,
                                        privacy='public',
                                        synchronous=True,
                                        request=request)
            if not execution[0] :
                flash('Operation failed ', 'danger')
            else :
                flash('Certificate has been issued', 'success')
        else : # fail to check code
            print('Warning : incorrect code in issue recommendation ', request.args.get('two_factor'))
        del session['recommendation_to_sign']
        return redirect(mode.server + 'user/issuer_explore/?issuer_username=' + session['issuer_username'])
    if request.method == 'POST' :
        session['recommendation_to_sign'] = {"version" : 1,
                    "type" : "recommendation",
                    "description" : request.form['description'],
                    "relationship" : request.form['relationship'],
			        "picture" : session['picture'],
			        "title" : session['title']}
        # call the two factor checking function :
        return redirect(mode.server + 'user/two_factor/?callback=user/issue_recommendation/')

# personal settings
@app.route('/user/update_personal_settings/', methods=['GET', 'POST'])
def update_personal_settings() :
    check_login()
    personal = copy.deepcopy(session['personal'])
    convert(personal)
    if request.method == 'GET' :
        privacy=dict()
        for topicname in session['personal'].keys() :
            if session['personal'][topicname]['privacy']=='secret' :
                (p1,p2,p3) = ("", "", "selected")
            if session['personal'][topicname]['privacy']=='private' :
                (p1,p2,p3) = ("", "selected", "")
            if session['personal'][topicname]['privacy']=='public' :
                (p1,p2,p3) = ("selected", "", "")
            if session['personal'][topicname]['privacy'] is None :
                (p1,p2,p3) = ("", "", "")
            privacy[topicname] = """
                    <optgroup>
                    <option """+ p1 + """ value="public">Public</option>
                    <option """ + p2 +""" value="private">Private</option>
                    <option """ + p3 + """ value="secret">Secret</option>
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
        form_value = dict()
        form_privacy['contact_phone'] = request.form['contact_phone_select']
        form_privacy['contact_email'] = request.form['contact_email_select']
        form_privacy['birthdate'] = request.form['birthdate_select']
        form_privacy['postal_address'] = request.form['postal_address_select']
        form_privacy['firstname'] = 'public'
        form_privacy['lastname'] = 'public'
        form_privacy['about'] = 'public'
        form_privacy['profil_title'] = 'public'
        form_privacy['education'] = 'public'
        change = False
        for topicname in session['personal'].keys() :
            form_value[topicname] = None if request.form[topicname] in ['None', '', ' '] else request.form[topicname]
            if     form_value[topicname] != session['personal'][topicname]['claim_value'] or session['personal'][topicname]['privacy'] != form_privacy[topicname] :
                if form_value[topicname] is not None :
                    claim_id = Claim().relay_add( session['workspace_contract'],topicname, form_value[topicname], form_privacy[topicname], mode)[0]
                    if claim_id is None :
                        flash('Update impossible (RSA not found ?)', 'danger')
                        return redirect(mode.server + 'user/')
                    change = True
                    session['personal'][topicname]['claim_value'] = form_value[topicname]
                    session['personal'][topicname]['privacy'] = form_privacy[topicname]
                    session['personal'][topicname]['claim_id'] = claim_id[2:]
        if change :
            flash('Personal has been updated', 'success')
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
@app.route('/user/update_company_settings/', methods=['GET', 'POST'])
def update_company_settings() :
    check_login()
    personal = copy.deepcopy(session['personal'])
    convert(personal)
    if request.method == 'GET' :
        privacy=dict()
        for topicname in session['personal'].keys() :
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
            if settings ==  None:
                flash('Company not found in SIREN database', 'warning')
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
                                        about=settings['activity'] + """

""" + personal['about']['claim_value'],
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
        form_value = dict()
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

        change = False
        for topicname in session['personal'].keys() :
            form_value[topicname] = None if request.form[topicname] in ['None', '', ' '] else request.form[topicname]
            if form_value[topicname] != session['personal'][topicname]['claim_value'] or session['personal'][topicname]['privacy'] != form_privacy[topicname] :
                if form_value[topicname] :
                    claim_id = Claim().relay_add( session['workspace_contract'],topicname, form_value[topicname], form_privacy[topicname], mode)[0]
                    change = True
                    session['personal'][topicname]['claim_value'] = form_value[topicname]
                    session['personal'][topicname]['privacy'] = form_privacy[topicname]
                    session['personal'][topicname]['claim_id'] = claim_id[2:]
        if change :
            session['menu']['name'] = session['personal']['name']['claim_value']
            flash('Company Settings has been updated', 'success')
        return redirect(mode.server + 'user/')

# digital vault
@app.route('/user/store_file/', methods=['GET', 'POST'])
def store_file() :
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
            flash('Transaction failed', "danger")
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
            flash('File ' + filename + ' has been uploaded.', "success")
        return redirect(mode.server + 'user/')



# create a user/identity
@app.route('/user/create_person/', methods=['GET', 'POST'])
def create_person() :
    check_login()
    if request.method == 'GET' :
        return render_template('create_identity.html', **session['menu'])
    if request.method == 'POST' :
        person_email = request.form['email']
        person_firstname = request.form['firstname']
        person_lastname = request.form['lastname']
        person_username = ns.build_username(person_firstname, person_lastname, mode)
        workspace_contract = createidentity.create_user(person_username, person_email, mode, creator=session['address'], partner=True)[2]
        if workspace_contract :
            claim=Claim()
            claim.relay_add(workspace_contract, 'firstname', person_firstname, 'public', mode)
            claim=Claim()
            claim.relay_add(workspace_contract, 'lastname', person_lastname, 'public', mode)
            flash('New Identity = ' + person_username + ' has been created.', 'success')
        else :
            flash('Identity Creation failed', 'danger')
        return redirect(mode.server + 'user/')

# add experience
@app.route('/user/add_experience/', methods=['GET', 'POST'])
def add_experience() :
	check_login()
	if request.method == 'GET' :
		return render_template('add_experience.html',**session['menu'])
	if request.method == 'POST' :
		my_experience = Document('experience')
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
		privacy = 'public'
		# issue experience document
		doc_id_exp = my_experience.relay_add(session['workspace_contract'], experience, mode, privacy=privacy)[0]
		if not doc_id_exp  :
			flash('Transaction failed', 'danger')
		else :
			if experience['skills']!= [''] :
				# add skills  in document skill
				for skill in experience['skills'] :
					skill_code = unidecode.unidecode(skill.lower())
					skill_code = skill_code.replace(" ", "")
					skill_code = skill_code.replace("-", "")
					my_skill = {'skill_code' : skill_code,
									'skill_name' : skill.capitalize(),
									'skill_level' : "Intermediate",
									'skill_domain' : ""}
					if session['skills'] is None  :
						session['skills'] = dict()
						session['skills']['description'] = []
						session['skills']['version'] = 1
					for one_skill in session['skills']['description'] :
						if one_skill['skill_code'] == skill_code :
							pass
						else :
							session['skills']['description'].append(my_skill)
							break
				# update skills
				my_skills = Document('skills')
				skill_data = {'version' : session['skills']['version'],  'description' : session['skills']['description']}
				# issue new skill document
				data = my_skills.relay_add(session['workspace_contract'], skill_data, mode)
				if not data[0] :
					flash('Transaction to add skill failed', 'danger')
					return redirect( mode.server + 'user/')
				doc_id = data[0]
				session['skills']['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] +':document:' + str(doc_id)

			# add experience in current session
			experience['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':document:'+str(doc_id_exp)
			experience['doc_id'] = doc_id_exp
			experience['created'] = str(datetime.now())
			experience['issuer'] = {'workspace_contract' : mode.relay_workspace_contract, 'category' : 2001}
			session['experience'].append(experience)
			flash('New experience added', 'success')
		return redirect(mode.server + 'user/')

# issue kyc (Talao only)
@app.route('/user/issue_kyc/', methods=['GET', 'POST'])
def create_kyc() :
    check_login()
    if request.method == 'GET' :
        return render_template('issue_kyc.html', **session['menu'])
    if request.method == 'POST' :
        my_kyc = dict()
        kyc_username = request.form['username'].lower()
        kyc_workspace_contract = ns.get_data_from_username(kyc_username,mode).get('workspace_contract')
        if not kyc_workspace_contract :
            flash(kyc_username + ' does not exist ', 'danger')
            return redirect(mode.server + 'user/')
        my_kyc['firstname'] = request.form['firstname']
        my_kyc['lastname'] = request.form['lastname']
        my_kyc['birthdate'] = request.form['birthdate']
        my_kyc['authority'] = request.form['authority']
        my_kyc['card_id'] = request.form['card_id']
        my_kyc['nationality'] = request.form['nationality']
        my_kyc['date_of_issue'] = request.form['date_of_issue']
        my_kyc['date_of_expiration'] = request.form['date_of_expiration']
        my_kyc['sex'] = request.form['sex']
        my_kyc['country'] = request.form['country']
        kyc_workspace_contract = ns.get_data_from_username(kyc_username, mode)['workspace_contract']
        kyc = Document('kyc')
        data = kyc.talao_add(kyc_workspace_contract, my_kyc, mode)[0]
        if not data :
            flash('Transaction failed', 'danger')
        else :
            flash('New kyc added for '+ kyc_username, 'success')
            subject = 'Your proof of Identity'
            kyc_email = ns.get_data_from_username(kyc_username, mode)['email']
            Talao_message.messageHTML(subject, kyc_email,'POI_issued', {None}, mode)
        return redirect(mode.server + 'user/')


# Create skill certificate A reprendre !!!!
@app.route('/user/issue_skill_certificate/', methods=['GET', 'POST'])
def create_skill_certificate() :
    check_login()
    if request.method == 'GET' :
        return render_template('issue_skill_certificate.html', **session['menu'])
    if request.method == 'POST' :
        identity_username = request.form['identity_username'].lower()
        certificate = {
                    "version" : 1,
                    "type" : "skill",
                    "title" : request.form['title'],
                    "description" : request.form['description'],
                    "end_date" : request.form['date'],
                    "date_of_issue" : "",
                    "logo" : session['picture'],
                    "signature" : session['signature'],
                    "manager" : "Director",
                    "reviewer" : ""}
        workspace_contract_to = ns.get_data_from_username(identity_username, mode)['workspace_contract']
        address_to = contractsToOwners(workspace_contract_to, mode)
        my_certificate = Document('certificate')
        #doc_id = my_certificate.talao_add(workspace_contract_to, certificate, mode)[0]
        doc_id = my_certificate.add(session['address'],
                        session['workspace_contract'],
                        address_to,
                        workspace_contract_to,
                        session['private_key_value'],
                        certificate,
                        mode,
                        mydays=0,
                        privacy='public',
                         synchronous=True)[0]
        if not doc_id :
            flash('Operation failed ', 'danger')
        else :
            flash('Certificate has been issued', 'success')
            link = mode.server + 'guest/certificate/?certificate_id=did:talao:' + mode.BLOCKCHAIN + ':' + workspace_contract_to[2:] + ':document:' + str(doc_id)
            subject = 'Your skill certificate'
            identity_email = ns.get_data_from_username(identity_username, mode)['email']
            Talao_message.messageHTML(subject, identity_email, 'certificate_issued', {'username': identity_username, 'link': link}, mode)
        return redirect(mode.server + 'user/')

# remove kyc
@app.route('/user/remove_kyc/', methods=['GET', 'POST'])
def remove_kyc() :
    check_login()
    if request.method == 'GET' :
        session['kyc_to_remove'] = request.args['kyc_id']
        return render_template('remove_kyc.html', **session['menu'])
    if request.method == 'POST' :
        session['kyc'] = [kyc for kyc in session['kyc'] if kyc['id'] != session['kyc_to_remove']]
        doc_id = session['kyc_to_remove'].split(':')[5]
        my_kyc = Document('kyc')
        if session['private_key'] :
            my_kyc.delete(session['workspace_contract'], session['private_key_value'], int(doc_id), mode)
            for counter,kyc in enumerate(session['kyc'], 0) :
                if kyc['doc_id'] == doc_id :
                    del session['kyc'][counter]
                    break
            del session['kyc_to_remove']
            flash('The Proof of Identity has been removed', 'success')
        else :
            flash('You cannot remove theis Proof of Identy (No Private Key found)', 'warning')
        return redirect (mode.server +'user/')



# create kbis (Talao only)
@app.route('/user/issue_kbis/', methods=['GET', 'POST'])
def issue_kbis() :
    check_login()
    if request.method == 'GET' :
        return render_template('issue_kbis.html', **session['menu'])
    if request.method == 'POST' :
        kbis = Document('kbis')
        my_kbis = dict()
        kbis_username = request.form['username']
        kbis_workspace_contract = ns.get_data_from_username(kbis_username,mode).get('workspace_contract')
        if not kbis_workspace_contract :
            flash(kbis_username + ' does not exist ', 'danger')
            return redirect(mode.server + 'user/')
        my_kbis['name'] = request.form['name']
        my_kbis['date'] = request.form['date']
        my_kbis['legal_form'] = request.form['legal_form']
        my_kbis['capital'] = request.form['capital']
        my_kbis['naf'] = request.form['naf']
        my_kbis['activity'] = request.form['activity']
        my_kbis['address'] = request.form['address']
        my_kbis['ceo'] = request.form['ceo']
        my_kbis['siren'] = request.form['siren']
        my_kbis['managing_director'] = request.form['managing_director']
        data = kbis.talao_add(kbis_workspace_contract, my_kbis, mode)[0]
        if not data :
            flash('Transaction failed', 'danger')
        else :
            flash('New kbis added for '+ kbis_username, 'success')
        return redirect(mode.server + 'user/')


# remove kbis
@app.route('/user/remove_kbis/', methods=['GET', 'POST'])
def remove_kbis() :
    check_login()
    if request.method == 'GET' :
        session['kbis_to_remove'] = request.args['kbis_id']
        return render_template('remove_kbis.html', **session['menu'])
    if request.method == 'POST' :
        session['kbis'] = [kbis for kbis in session['kbis'] if kbis['id'] != session['kbis_to_remove']]
        doc_id = session['kbis_to_remove'].split(':')[5]
        my_kbis = Document('kbis')
        if session['private_key'] :
            my_kbis.delete(session['workspace_contract'], session['private_key_value'], int(doc_id), mode)
            for counter,kbis in enumerate(session['kbis'], 0) :
                if kbis['doc_id'] == doc_id :
                    del session['kbis'][counter]
                    break
            del session['kbis_to_remove']
            flash('The Proof of Identity has been removed', 'success')
        else :
            flash('You cannot remove this Proof of Identy (No Private Key found)', 'warning')
        return redirect (mode.server +'user/')

@app.route('/user/remove_experience/', methods=['GET', 'POST'])
def remove_experience() :
    check_login()
    if request.method == 'GET' :
        session['experience_to_remove'] = request.args['experience_id']
        session['experience_title'] = request.args['experience_title']
        return render_template('remove_experience.html', **session['menu'], experience_title=session['experience_title'])
    elif request.method == 'POST' :
        session['experience'] = [experience for experience in session['experience'] if experience['id'] != session['experience_to_remove']]
        Id = session['experience_to_remove'].split(':')[5]
        my_experience = Document('experience')
        data = my_experience.relay_delete(session['workspace_contract'], int(Id), mode)
        if not data :
            flash('Transaction failed', 'danger')
        else :
            del session['experience_to_remove']
            del session['experience_title']
            flash('The experience has been removed', 'success')
        return redirect (mode.server +'user/')

# create company with two factor checking function
@app.route('/user/create_company/', methods=['GET', 'POST'])
def create_company() :
    check_login()
    if request.method == 'GET' :
        # code is correct
        if request.args.get('two_factor') == "True" :
            workspace_contract =  createcompany.create_company(session['company_email'], session['company_username'], mode, siren=session['company_siren'])[2]
            if workspace_contract :
                Claim().relay_add(workspace_contract, 'name', session['company_name'], 'public', mode)
                directory.add_user(mode, session['company_name'], session['company_username'], session['company_siren'])
                flash(session['company_username'] + ' has been created as company', 'success')
            else :
                flash('Company Creation failed', 'danger')
            return redirect(mode.server + 'user/')
        # code is incorrect
        elif request.args.get('two_factor') == "False" :
            flash('Incorrect code', 'danger')
            return redirect(mode.server + 'user/')
        # first call
        else :
            return render_template('create_company.html', **session['menu'])
    if request.method == 'POST' :
        session['company_email'] = request.form['email']
        session['company_name'] = request.form['name']
        session['company_username'] = session['company_name'].lower()
        session['company_siren'] = request.form['siren']
        if ns.username_exist(session['company_username'], mode)   :
            session['company_username'] = session['company_username'] + str(random.randint(1, 100))
        # call the two factor checking function :
        return redirect(mode.server + 'user/two_factor/?callback=user/create_company/')

# delete a certificate with two factor checking
@app.route('/user/remove_certificate/', methods=['GET', 'POST'])
def remove_certificate() :
    check_login()
    if request.method == 'GET' :
         # call from two factor checking function, code is ok
        if request.args.get('two_factor') == "True" :
            session['certificate'] = [certificate for certificate in session['certificate'] if certificate['id'] != session['certificate_to_remove']]
            Id = session['certificate_to_remove'].split(':')[5]
            data = Document('certificate').relay_delete(session['workspace_contract'], int(Id), mode)
            if not data :
                flash('Transaction failed', 'danger')
            else :
                flash('The certificate has been removed', 'success')
            del session['certificate_to_remove']
            del session['certificate_title']
            return redirect (mode.server +'user/')
        # call from two factor checking function, code incorrect
        elif request.args.get('two_factor') == "False" :
            del session['certificate_to_remove']
            del session['certificate_title']
            return redirect (mode.server +'user/')
        # first call
        else :
            session['certificate_to_remove'] = request.args['certificate_id']
            session['certificate_title'] = request.args['certificate_title']
            return render_template('remove_certificate.html', **session['menu'], certificate_title=session['certificate_title'])
    elif request.method == 'POST' :
        # call the two factor checking function :
        return redirect(mode.server + 'user/two_factor/?callback=user/remove_certificate/')


@app.route('/user/remove_file/', methods=['GET', 'POST'])
def remove_file() :
    check_login()
    if request.method == 'GET' :
        session['file_id_to_remove'] = request.args['file_id']
        session['filename_to_remove'] = request.args['filename']
        return render_template('remove_file.html', **session['menu'],filename=session['filename_to_remove'])
    elif request.method == 'POST' :
        session['identity_file'] = [one_file for one_file in session['identity_file'] if one_file['id'] != session['file_id_to_remove']]
        Id = session['file_id_to_remove'].split(':')[5]
        my_file = File()
        data = my_file.relay_delete(session['workspace_contract'], int(Id), mode)
        if not data :
            flash('Transaction failed', 'danger')
        else :
            del session['file_id_to_remove']
            del session['filename_to_remove']
            flash('The file has been deleted', 'success')
        return redirect (mode.server +'user/')

# add education
@app.route('/user/add_education/', methods=['GET', 'POST'])
def add_education() :
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
        privacy = 'public'
        doc_id = my_education.relay_add(session['workspace_contract'], education, mode, privacy=privacy)[0]
        if not doc_id[0]  :
            flash('Transaction failed', 'danger')
        else :
            # add experience in session
            education['id'] = 'did:talao:' + mode.BLOCKCHAIN + ':' + session['workspace_contract'][2:] + ':document:'+str(doc_id)
            education['doc_id'] = doc_id
            education['created'] = str(datetime.now())
            education['issuer'] = {'workspace_contract' : mode.relay_workspace_contract, 'category' : 2001}
            session['education'].append(education)
            flash('New Education added', 'success')
        return redirect(mode.server + 'user/')

@app.route('/user/remove_education/', methods=['GET', 'POST'])
def remove_education() :
    check_login()
    if request.method == 'GET' :
        session['education_to_remove'] = request.args['education_id']
        session['education_title'] = request.args['education_title']
        return render_template('remove_education.html', **session['menu'], education_title=session['education_title'])
    elif request.method == 'POST' :
        session['education'] = [education for education in session['education'] if education['id'] != session['education_to_remove']]
        doc_id = session['education_to_remove'].split(':')[5]
        my_education = Document('education')
        data = my_education.relay_delete(session['workspace_contract'], int(doc_id), mode)
        if not data :
            flash('Transaction failed', 'danger')
        else :
            for counter,edu in enumerate(session['education'], 0) :
                if edu['doc_id'] == doc_id :
                    del session['education'][counter]
                    break
            del session['education_to_remove']
            del session['education_title']
            flash('The Education has been removed', 'success')
        return redirect (mode.server +'user/')

# invit
@app.route('/user/invit/', methods=['GET', 'POST'])
def invit() :
    check_login()
    if request.method == 'GET' :
        return render_template('invit.html', **session['menu'])
    if request.method == 'POST' :
        talent_email = request.form['email']
        username_list = ns.get_username_list_from_email(talent_email, mode)
        if username_list != [] :
            msg = 'This email is already used by Identity(ies) : ' + ", ".join(username_list) + ' . Use the Search Bar.'
            flash(msg , 'warning')
            return redirect(mode.server + 'user/')
        subject = 'You have been invited to join Talao'
        name = session['personal']['firstname']['claim_value'] + session['personal']['lastname']['claim_value']
        execution = Talao_message.messageHTML(subject, talent_email, 'invite_to_join', {'name':name}, mode)
        if execution :
            flash('Your invit has been sent', 'success')
        else :
            flash('Your invit has not been sent', 'danger')
        return redirect(mode.server + 'user/')

# send memo by email
@app.route('/user/send_memo/', methods=['GET', 'POST'])
def send_memo() :
    check_login()
    if request.method == 'GET' :
        session['memo_username'] = request.args['issuer_username']
        return render_template('send_memo.html', **session['menu'], memo_username=session['memo_username'])
    if request.method == 'POST' :
        # email to issuer
        subject = "You have received a memo from " + session['name'] +"."
        memo = request.form['memo']
        memo_email = ns.get_data_from_username(session['memo_username'], mode)['email']
        Talao_message.messageHTML(subject, memo_email, 'memo', {'name': session['name'], 'memo':memo}, mode)
        # message to user
        flash("Your memo has been sent to " + session['memo_username'], 'success')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['memo_username'])

# request partnership
@app.route('/user/request_partnership/', methods=['GET', 'POST'])
def resquest_partnership() :
    check_login()
    if request.method == 'GET' :
        session['partner_username'] = request.args['issuer_username']
        return render_template('request_partnership.html', **session['menu'], partner_username=session['partner_username'])
    if request.method == 'POST' :
        partner_workspace_contract = ns.get_data_from_username(session['partner_username'], mode)['workspace_contract']
        partner_address = contractsToOwners(partner_workspace_contract, mode)
        partner_publickey = mode.w3.solidityKeccak(['address'], [partner_address]).hex()
        if not session['rsa_key'] :
            flash('Request Partnership to ' + session['partner_username'] + ' is not available (RSA key not found)', 'warning')
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
                    flash('transaction for add issuer failed', 'danger')
                else :
                    session['issuer'].append(ns.get_data_from_username(session['partner_username'], mode))
            # user message
            flash('You have send a Request for Partnership to ' + session['partner_username'], 'success')
            # partner email
            subject = session['name'] + " souhaite accéder aux données privées de votre Identité Talao"
            partner_email = ns.get_data_from_username(session['partner_username'], mode)['email']
            Talao_message.messageHTML(subject, partner_email, 'request_partnership', {'name' : session['name']}, mode)
        else :
            flash('Request to ' + session['partner_username'] + ' failed', 'danger')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['issuer_username'])

# remove partnership
@app.route('/user/remove_partner/', methods=['GET', 'POST'])
def remove_partner() :
    check_login()
    if request.method == 'GET' :
        session['partner_username_to_remove'] = request.args['partner_username']
        session['partner_workspace_contract_to_remove'] = request.args['partner_workspace_contract']
        return render_template('remove_partner.html', **session['menu'], partner_name=session['partner_username_to_remove'])
    if request.method == 'POST' :
        res = remove_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_remove'], mode)
        if not res :
            flash ('Partnership removal has failed')
        else :
            # remove partneship in current session
            session['partner'] = [ partner for partner in session['partner'] if partner['workspace_contract'] != session['partner_workspace_contract_to_remove']]
            flash('The partnership with '+session['partner_username_to_remove']+ '  has been removed', 'success')
        del session['partner_username_to_remove']
        del session['partner_workspace_contract_to_remove']
        return redirect (mode.server +'user/')

# reject partnership
@app.route('/user/reject_partner/', methods=['GET', 'POST'])
def reject_partner() :
    check_login()
    if request.method == 'GET' :
        session['partner_username_to_reject'] = request.args['partner_username']
        session['partner_workspace_contract_to_reject'] = request.args['partner_workspace_contract']
        return render_template('reject_partner.html', **session['menu'], partner_name=session['partner_username_to_reject'])
    if request.method == 'POST' :
        res = reject_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_reject'], mode)
        if not res :
            flash ('Partnership rejection has failed')
        else :
            # remove partnership in current session
            session['partner'] = [ partner for partner in session['partner'] if partner['workspace_contract'] != session['partner_workspace_contract_to_reject']]
            # message to user
            flash('The Partnership with '+session['partner_username_to_reject']+ '  has been rejected', 'success')
            # email to partner
            subject = "Your Request for Partnership has been rejected by " + session['name']
            partner_email = ns.get_data_from_username(session['partner_username_to_reject'], mode)['email']
            text = ""
            Talao_message.messageHTML(subject, partner_email, 'request_partnership_rejected', {'name' : session['name'], 'text' : text}, mode)
        del session['partner_username_to_reject']
        del session['partner_workspace_contract_to_reject']
        return redirect (mode.server +'user/')

# authorize partnership
@app.route('/user/authorize_partner/', methods=['GET', 'POST'])
def authorize_partner() :
    check_login()
    if request.method == 'GET' :
        session['partner_username_to_authorize'] = request.args['partner_username']
        session['partner_workspace_contract_to_authorize'] = request.args['partner_workspace_contract']
        return render_template('authorize_partner.html', **session['menu'], partner_name=session['partner_username_to_authorize'])
    if request.method == 'POST' :
        if not session['rsa_key'] :
            flash('Request a Partnership to ' + session['partner_username'] + ' is impossible (RSA key not found)', 'warning')
            del session['partner_username_to_authorize']
            del session['partner_workspace_contract_to_authorize']
            return redirect (mode.server +'user/')
        if not authorize_partnership(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['partner_workspace_contract_to_authorize'], session['rsa_key_value'], mode) :
            flash ('Partnership authorize has failed', 'danger')
        else :
            flash('The partnership with '+session['partner_username_to_authorize']+ '  has been authorized', 'success')
            # update partnership in current session
            for partner in session['partner'] :
                if partner['workspace_contract'] == session['partner_workspace_contract_to_authorize'] :
                    partner['authorized'] = "Authorized"
                    break
        del session['partner_username_to_authorize']
        del session['partner_workspace_contract_to_authorize']
        return redirect (mode.server +'user/')


# request certificate to be completed with email
@app.route('/user/request_certificate/', methods=['GET', 'POST'])
def request_certificate() :
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
        print('type = ', session['issuer_type'])
        if request.form['certificate_type'] == 'experience' :
            return render_template('request_experience_certificate.html', **session['menu'])
        elif request.form['certificate_type'] in ['personal_recommendation', 'company_recommendation'] :
            return render_template('request_recommendation_certificate.html', **session['menu'])
        elif request.form['certificate_type'] == 'agreement' :
            return render_template('request_agreement_certificate.html', **session['menu'])
        elif request.form['certificate_type'] == 'reference' :
            return render_template('request_reference_certificate.html', **session['menu'])

@app.route('/user/request_recommendation_certificate/', methods=['POST'])
def request_recommendation_certificate() :
    """ With this view one sends an email with link to the Referent"""
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

@app.route('/user/request_experience_certificate/', methods=['POST'])
def request_experience_certificate() :
    """ This is to send the email with link """
    check_login()
    # email to Referent/issuer
    issuer_workspace_contract = None if not session['certificate_issuer_username'] else session['issuer_explore']['workspace_contract']
    issuer_name = None if not session['certificate_issuer_username']  else session['issuer_explore']['name']
    payload = {'issuer_email' : session['issuer_email'],
            'certificate_type' : 'experience',
            'title' : request.form['title'],
             'description' : request.form['description'],
             'skills' :request.form['skills'],
             'end_date' :  request.form['end_date'],
             'start_date' : request.form['start_date'],
             'user_name' : session['name'],
             'user_username' : session['username'],
             'user_workspace_contract' : session['workspace_contract'],
             'issuer_username' : session['certificate_issuer_username'],
             'issuer_workspace_contract' : issuer_workspace_contract,
             'issuer_name' : issuer_name,
             'issuer_type' : session['issuer_type'],}
    # build JWT for link
    header = {'alg': 'RS256'}
    key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
    token = jwt.encode(header, payload, key).decode('utf-8')
    # build email
    url = mode.server + 'issue/?token=' + token
    subject = 'You have received a request for a professional certificate from '+ session['name']
    Talao_message.messageHTML(subject, session['issuer_email'], 'request_certificate', {'name' : session['name'], 'link' : url}, mode)
    # message to user/Talent
    flash('Your request for an Experience Certificate has been sent.', 'success')
    if session['certificate_issuer_username'] :
        return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + session['certificate_issuer_username'])
    return redirect(mode.server + 'user/')

@app.route('/user/request_agreement_certificate/', methods=['POST'])
def request_agreement_certificate() :
    """ This is to send the email with link """
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

@app.route('/user/request_reference_certificate/', methods=['POST'])
def request_reference_certificate() :
    """ This is to send the email with link """
    check_login()
    # email to Referent/issuer
    issuer_workspace_contract = None if not session['certificate_issuer_username'] else session['issuer_explore']['workspace_contract']
    issuer_name = None if not session['certificate_issuer_username'] else session['issuer_explore']['name']
    payload = {'issuer_email' : session['issuer_email'],
             'certificate_type' : 'reference',
             'title' : request.form['title'],
             'description' : request.form['description'],
             'competencies' :request.form['competencies'],
             'end_date' :  request.form['end_date'],
             'start_date' : request.form['start_date'],
             'project_location' : request.form['project_location'],
             'project_staff' : request.form['project_staff'],
             'project_budget' : request.form['project_budget'],
             'user_name' : session['name'],
             'user_username' : session['username'],
             'user_workspace_contract' : session['workspace_contract'],
             'issuer_username' : session['certificate_issuer_username'],
             'issuer_workspace_contract' : issuer_workspace_contract,
             'issuer_name' : issuer_name,
             'issuer_type' : session['issuer_type'],}
    # build JWT for link
    header = {'alg': 'RS256'}
    key = privatekey.get_key(mode.owner_talao, 'rsa_key', mode)
    token = jwt.encode(header, payload, key).decode('utf-8')
    # build email
    url = mode.server + 'issue/?token=' + token
    subject = 'You have received a request for a reference claim from '+ session['name']
    Talao_message.messageHTML(subject, session['issuer_email'], 'request_certificate', {'name' : session['name'], 'link' : url}, mode)
    # message to user/Talent
    flash('Your request for an Agreement Certificate has been sent.', 'success')
    if session['certificate_issuer_username'] :
        return redirect (mode.server + 'user/issuer_explore/?issuer_username=' + session['certificate_issuer_username'])
    return redirect(mode.server + 'user/')

# add alias (alternative Username for user as a person )
@app.route('/user/add_alias/', methods=['GET', 'POST'])
def add_alias() :
    check_login()
    if request.method == 'GET' :
        return render_template('add_alias.html', **session['menu'])
    if request.method == 'POST' :
        if ns.username_exist(request.form['access_username'],mode) :
            flash('Username already used' , 'warning')
        else :
            alias_username = request.form['access_username']
            ns.add_alias(alias_username, session['username'], request.form['access_email'], mode)
            flash('Alias added for '+ alias_username , 'success')
        return redirect (mode.server +'user/')

# remove alias
@app.route('/user/remove_access/', methods=['GET'])
def remove_access() :
    check_login()
    username_to_remove = request.args['username_to_remove']
    manalias_name,s,host_name = username_to_remove.partition('.')
    if host_name != "" :
        execution = ns.remove_manager(manalias_name, host_name, mode)
    else :
        execution = ns.remove_alias(manalias_name, mode)
    if execution :
        flash(username_to_remove + ' has been removed', 'success')
    else :
        flash('Operation failed', 'danger')
    return redirect (mode.server +'user/')

# Import private key
@app.route('/user/import_private_key/', methods=['GET', 'POST'])
def import_private_key() :
    check_login()
    if request.method == 'GET' :
        return render_template('import_private_key.html', **session['menu'])
    if request.method == 'POST' :
        priv_key_bytes = decode_hex(request.form['private_key'])
        priv_key = keys.PrivateKey(priv_key_bytes)
        pub_key = priv_key.public_key
        address = pub_key.to_checksum_address()
        if address != session['address'] :
            flash('Wrong Private Key', 'warning')
            return redirect (mode.server +'user/')
        session['private_key'] = True
        session['private_key_value'] = request.form['private_key']
        privatekey.add_private_key(request.form['private_key'], mode)
        flash('Private Key has been imported',  'success')
        return redirect (mode.server +'user/')

# Import rsa key
@app.route('/user/import_rsa_key/', methods=['GET', 'POST'])
def import_rsa_key() :
    check_login()
    if request.method == 'GET' :
        return render_template('import_rsa_key.html', **session['menu'])
    if request.method == 'POST' :
        if 'file' not in request.files :
            flash('no file', "warning")
            return redirect(mode.server + 'user/')
        myfile = request.files['file']
        filename = secure_filename(myfile.filename)
        myfile.save(os.path.join(app.config['RSA_FOLDER'], filename))
        filename = "./RSA_key/"+mode.BLOCKCHAIN + '/' + filename
        try :
            f = open(filename,'r')
            key = RSA.import_key(f.read())
            RSA_public = key.publickey().exportKey('PEM')
        except :
            flash('RSA key is not found', 'danger')
            return redirect (mode.server +'user/')
        contract = mode.w3.eth.contract(session['workspace_contract'],abi=constante.workspace_ABI)
        identity_key = contract.functions.identityInformation().call()[4]
        if RSA_public == identity_key :
            session['rsa_key'] = True
            session['rsa_key_value'] = key.exportKey('PEM')
            flash('RSA Key has been uploaded',  'success')
        else :
            flash('RSA key is not correct', 'danger')
        return redirect (mode.server +'user/')


# add manager
@app.route('/user/add_manager/', methods=['GET', 'POST'])
def add_manager() :
    check_login()
    if request.method == 'GET' :
        if request.args.get('issuer_username') :
            manager_username = request.args.get('issuer_username')
        else:
            manager_username = ''
        return render_template('add_manager.html', **session['menu'], manager_username = manager_username)
    if request.method == 'POST' :
        if not ns.username_exist(request.form['manager_username'].lower(),mode)  :
            flash('Username not found' , 'warning')
        else :
            manager_username = request.form['manager_username']
            ns.add_manager(manager_username, manager_username, session['username'], request.form['manager_email'], mode)
            flash('Manager added for '+ manager_username.lower() , 'success')
        return redirect (mode.server +'user/')


# request proof of Identity
@app.route('/user/request_proof_of_identity/', methods=['GET', 'POST'])
def request_proof_of_identity() :
    check_login()
    if request.method == 'GET' :
        return render_template('request_proof_of_identity.html', **session['menu'])
    elif request.method == 'POST' :
        id_file = request.files['id_file']
        selfie_file = request.files['selfie_file']

        id_file_name = secure_filename(id_file.filename)
        selfie_file_name = secure_filename(selfie_file.filename)

        id_file.save(os.path.join('./uploads/proof_of_identity', session['username'] + "_ID." + id_file_name))
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
        flash(' Thank you, we will check your documents soon.', 'success')
        return redirect (mode.server +'user/')

# add Issuer, they have an ERC725 key with purpose 20002 (or 1) to issue Document (Experience, Certificate)
@app.route('/user/add_issuer/', methods=['GET', 'POST'])
def add_issuer() :
    check_login()
    if request.method == 'GET' :
        session['referent_username'] = request.args['issuer_username']
        if session['referent_username'] == session['username' ] :
            flash('You cannot be the Referent of yourself.', 'warning')
            return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['referent_username'])
        return render_template('add_referent.html', **session['menu'], referent_username=session['referent_username'])
    elif request.method == 'POST' :
        issuer_workspace_contract = ns.get_data_from_username(session['referent_username'],mode)['workspace_contract']
        issuer_address = contractsToOwners(issuer_workspace_contract, mode)
        if not add_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 20002, mode, synchronous=True) :
            flash('transaction failed', 'danger')
        else :
            issuer_workspace_contract = ownersToContracts(issuer_address, mode)
            session['issuer'].append(ns.get_data_from_username(session['referent_username'], mode))
            # email to issuer
            if session['issuer_explore']['category'] == 2001 :
                subject = "Your company has been chosen by " + session['name'] + " as a Referent."
            else :
                subject = "You have been chosen by " + session['name'] + " as a Referent."
            issuer_email = ns.get_data_from_username(session['referent_username'], mode)['email']
            Talao_message.messageHTML(subject, issuer_email, 'added_referent', {'name' : session['name']}, mode)
            # message to user
            flash(session['referent_username'] + ' has been added as a Referent. An email has been sent too.', 'success')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['referent_username'])

# Talao only : Add Key to anyone
@app.route('/user/add_key/', methods=['GET', 'POST'])
def add_key_for_other() :
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
        flash('transaction failed', 'danger')
    else :
        flash('Key added', 'success')
    return redirect (mode.server +'user/')

# remove issuer
@app.route('/user/remove_issuer/', methods=['GET', 'POST'])
def remove_issuer() :
    check_login()
    if request.method == 'GET' :
        session['issuer_username_to_remove'] = request.args['issuer_username']
        session['issuer_address_to_remove'] = request.args['issuer_address']
        return render_template('remove_issuer.html', **session['menu'],issuer_name=session['issuer_username_to_remove'])
    elif request.method == 'POST' :
        #address_partner = session['issuer_address_to_remove']
        if not delete_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['issuer_address_to_remove'], 20002, mode) :
            flash ('transaction failed', 'danger')
        else :
            session['issuer'] = [ issuer for issuer in session['issuer'] if issuer['address'] != session['issuer_address_to_remove']]
            flash('The Issuer '+session['issuer_username_to_remove']+ '  has been removed', 'success')
        del session['issuer_username_to_remove']
        del session['issuer_address_to_remove']
        return redirect (mode.server +'user/')


# add  White Issuer or WhiteList They all have an ERC725 key with purpose 5
@app.route('/user/add_white_issuer/', methods=['GET', 'POST'])
def add_white_issuer() :
    check_login()
    if request.method == 'GET' :
        session['whitelist_username'] = request.args['issuer_username']
        return render_template('add_white_issuer.html', **session['menu'], whitelist_username=session['whitelist_username'])
    elif request.method == 'POST' :
        issuer_workspace_contract = ns.get_data_from_username(session['whitelist_username'],mode)['workspace_contract']
        issuer_address = contractsToOwners(issuer_workspace_contract, mode)
        if not add_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, issuer_address, 5, mode, synchronous=True) :
            flash('transaction failed', 'danger')
        else :
            # update issuer list in session
            #issuer_key = mode.w3.soliditySha3(['address'], [issuer_address])
            #contract = mode.w3.eth.contract(mode.foundation_contract,abi = constante.foundation_ABI)
            issuer_workspace_contract = ownersToContracts(issuer_address, mode)
            session['whitelist'].append(ns.get_data_from_username(session['whitelist_username'], mode))
            flash(session['whitelist_username'] + ' has been added as Issuer in your White List', 'success')
        return redirect (mode.server +'user/issuer_explore/?issuer_username=' + session['whitelist_username'])

# remove white issuer
@app.route('/user/remove_white_issuer/', methods=['GET', 'POST'])
def remove_white_issuer() :
    check_login()
    if request.method == 'GET' :
        session['issuer_username_to_remove'] = request.args['issuer_username']
        session['issuer_address_to_remove'] = request.args['issuer_address']
        return render_template('remove_white_issuer.html', **session['menu'], issuer_name=session['issuer_username_to_remove'])
    elif request.method == 'POST' :
        #address_partner = session['issuer_address_to_remove']
        if not delete_key(mode.relay_address, mode.relay_workspace_contract, session['address'], session['workspace_contract'], mode.relay_private_key, session['issuer_address_to_remove'], 5, mode) :
            flash('transaction failed', 'danger')
        else :
            session['whitelist'] = [ issuer for issuer in session['whitelist'] if issuer['address'] != session['issuer_address_to_remove']]
            flash('The Issuer '+session['issuer_username_to_remove']+ '  has been removed from your White list', 'success')
        del session['issuer_username_to_remove']
        del session['issuer_address_to_remove']
        return redirect (mode.server +'user/')


# delete user identity
@app.route('/user/delete_identity/', methods=['GET', 'POST'])
def delete_identity() :
    check_login()
    if request.method == 'GET' :
        if not session['private_key'] :
            flash('Identity deletion is not possible as there is no private key', 'danger')
            return redirect (mode.server +'user/')
        else :
            return render_template('delete_identity.html', **session['menu'])
    elif request.method == 'POST' :
        if not ns.check_password(session['username'], request.form['password'], mode) :
            flash('Wrong password', 'danger')
            return redirect (mode.server +'user/')
        else :
            destroy_workspace(session['workspace_contract'], session['private_key_value'], mode)
            category = 1001 if session['type'] == 'person' else 2001
            ns.delete_identity(session['username'], mode, category = category)
            flash('Your Identity has been deleted from Blockchain', 'success')
            return redirect (mode.server +'login/')


# photos upload for certificates
@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(mode.uploads_path, filename)

# fonts upload
@app.route('/fonts/<filename>')
def send_fonts(filename):
    return send_from_directory(FONTS_FOLDER, filename)

# help upload
@app.route('/help/')
def send_help():
    filename = request.args['file']
    return render_template(filename)

@app.route('/user/download/', methods=['GET', 'POST'])
def download_file():
    filename = request.args['filename']
    return send_from_directory(mode.uploads_path, filename, as_attachment=True, cache_timeout=1)

@app.route('/user/download_rsa_key/', methods=['GET', 'POST'])
def download_rsa_key():
    check_login()
    filename = request.args['filename']
    attachment_filename = session['workspace_contract']+ '.key'
    print(attachment_filename)
    return send_from_directory(app.config['RSA_FOLDER'],filename, attachment_filename = attachment_filename,as_attachment=True,cache_timeout=1)

@app.route('/talao_ca/', methods=['GET', 'POST'])
def ca():
    talao_x509.generate_CA()
    return send_from_directory('./','talao.pem', as_attachment=True, cache_timeout=1)

@app.route('/user/download_x509/', methods=['GET', 'POST'])
def download_x509():
    check_login()
    filename = session['workspace_contract'] + '.pem'
    password = ns.get_data_from_username(session['username'], mode)['email']
    if not talao_x509.generate_X509(session['workspace_contract'],password, mode) :
        flash('Certificate X.509 not available', 'danger')
        return redirect (mode.server +'login/')
    return send_from_directory(mode.uploads_path,filename, as_attachment=True, cache_timeout=1)

@app.route('/user/download_pkcs12/', methods=['GET', 'POST'])
def download_pkcs12():
    check_login()
    if request.method == 'GET' :
        return render_template('create_password_pkcs12.html', **session['menu'])
    if request.method == 'POST' :
        filename = session['workspace_contract'] + '.p12'
        password = request.form['password']
        if not talao_x509.generate_X509(session['workspace_contract'], password, mode) :
            flash('Certificate PKCS12 not available', 'danger')
            return redirect (mode.server +'login/')
        return send_from_directory(mode.uploads_path,filename, as_attachment=True, cache_timeout=1)


@app.route('/user/download_QRCode/', methods=['GET', 'POST'])
def download_QRCode():
    if session['type'] == 'company':
        QRCode.get_QRCode(mode,  mode.server + "board/?workspace_contract=" + session['workspace_contract'])
    elif session['type'] == 'person':
        QRCode.get_QRCode(mode,  mode.server + "resume/?workspace_contract=" + session['workspace_contract'])
    filename = 'External_CV_QRCode.png'
    return send_from_directory(mode.uploads_path,
                               filename, as_attachment=True)

@app.route('/user/typehead/', methods=['GET', 'POST'])
def typehead() :
    return render_template('typehead.html')

# To manage the navbar search field. !!!! The json file is uploaded once
@app.route('/user/data/', methods=['GET', 'POST'])
def talao_search() :
    print('Warning : upload prefetch file')
    filename = request.args['filename']
    return send_from_directory(mode.uploads_path,
                               filename, as_attachment=True)


# This is the DID proof
@app.route('/did/', methods=['GET', 'POST'])
def did_check () :
    if request.method == 'GET' :
	    html = """<!DOCTYPE html>
		<html lang="en">
			<body>
				<h1>Talao - https://talao.co</h1>
                <h2>Our Decentralized IDentifiers are : </h2>
                <p>
                    <li><b>did:talao:talaonet:4562DB03D8b84C5B10FfCDBa6a7A509FF0Cdcc68</b></li>
                    <li><b>did:talao:rinkeby:fafDe7ae75c25d32ec064B804F9D83F24aB14341</b></li>
                </p>
			</body>
		</html>"""
	    return render_template_string(html)
    if request.method == 'POST' :
        return jsonify({"code" : request.form.get('code')}), 200



#######################################################
#                        MAIN, server launch
#######################################################
# setup du registre nameservice

print('Warning : flask serveur init')


if __name__ == '__main__':
    app.run(host = mode.flaskserver, port= mode.port, debug = mode.test)
