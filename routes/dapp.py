from flask import render_template, request, jsonify, redirect
import uuid 
import json


# https://github.com/airgap-it/beacon-sdk

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/saas4ssi/dapp',  view_func=dapp_wallet, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/sandbox/saas4ssi/dapp/webhook',  view_func=dapp_webhook, methods = ['GET', 'POST'], defaults={'red' : red})
    global link, client_secret
    if mode.myenv == 'aws':
        link = 'https://talao.co/sandbox/op/issuer/iagetctadx'
        client_secret = "1c6f9c32-1941-11ed-915c-0a1628958560"
    else :
        link = "http://192.168.0.220:3000/sandbox/op/issuer/ovjyigjpbc"
        client_secret = '9828d8f8-52d1-11ed-9758-47cea17512cf'

    return

def dapp_wallet(red):
    if request.method == 'GET' :
        return render_template('dapp.html')
    else :
        id = str(uuid.uuid1())
        red.set(id, json.dumps({"associatedAddress" : request.form["address"],
                                "accountName" : request.form["wallet"]}))
        return redirect (link + "?id=" + id)

def dapp_webhook(red) :
    if request.headers.get("key") != client_secret :
        return jsonify("Forbidden"), 403
    data = request.get_json()
    try :
        data_returned = json.loads(red.get(data["id"]).decode())   
    except :
        print("error redis")
    # send back data to issue credential
    if data['event'] == 'ISSUANCE' :
        return jsonify(data_returned)
    else :
        return jsonify('ok')