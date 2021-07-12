from flask import jsonify, request, render_template, session, redirect, flash
import json
import redis
red = redis.Redis()

def init_app(app,mode) :
    app.add_url_rule('/credible/credentialOffer/<id>',  view_func=credentialOffer_qrcode, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/credible/credential/<id>',  view_func=credential_display, methods = ['GET', 'POST'])
    app.add_url_rule('/credible/wallet_credential/<id>',  view_func=credentialOffer, methods = ['GET', 'POST'])
    return


# credential offer

def credentialOffer_qrcode(mode,id) :
    filename = id + ".jsonld"
    try :
        json.load(open('./signed_credentials/' + filename, 'r'))
    except :
        flash('no credential available on server', 'warning')
        return redirect("/user")
    url = mode.server + "credible/wallet_credential/" + id
    return render_template('credible/credential_qr.html', url=url, id=id, **session['menu'])


def credential_display(id):
    if id != 'presentation' :
        filename = id + ".jsonld"
        credential = open('./signed_credentials/' + filename, 'r').read()
    else :
        credential = "No credential available"
    return render_template('credible/credential.html', credential=credential)


def credentialOffer(id):
    filename = id + ".jsonld"
    credential = json.load(open('./signed_credentials/' + filename, 'r'))
    if request.method == 'GET':   
        print('request form = ', request.form, request.data)
        return jsonify({
            "type": "CredentialOffer",
            "credentialPreview": credential
        })
    elif request.method == 'POST':
        return jsonify(credential)
     
