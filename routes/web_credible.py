
from socket import socket, AF_INET, SOCK_DGRAM
from flask import jsonify, request, render_template
import json


def init_app(app) :
    app.add_url_rule('/qr/<id>',  view_func=index, methods = ['GET', 'POST'])
    app.add_url_rule('/credential/<id>',  view_func=credential, methods = ['GET', 'POST'])
    app.add_url_rule('/wallet/<id>',  view_func=wallet, methods = ['GET', 'POST'])
    return


def index(id):
    s = socket(AF_INET, SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()

    url = (request.is_secure and "https://" or "http://") + IP + \
        ":" + request.host.split(':')[-1] + "/wallet/" + id
    return render_template('qr.html', url=url, id=id)


def credential(id):
    filename = id + ".jsonld"
    credential = open('./signed_credentials/' + filename, 'r').read()
    return render_template('credential.html', credential=credential)


def wallet(id):
    print('request = ', request.args, request.form)
    filename = id + ".jsonld"
    credential = json.load(open('./signed_credentials/' + filename, 'r'))
    if request.method == 'GET':
        return jsonify({
            "type": "CredentialOffer",
            "credentialPreview": credential
        })
    elif request.method == 'POST':
        return jsonify(credential)
