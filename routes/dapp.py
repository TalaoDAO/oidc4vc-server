from flask import render_template, request, jsonify, redirect, Response
import uuid 
import json


issuer_and_verifier_list = ['c8f90f24-5506-11ed-b15e-0a1628958560',
'80591e33-551a-11ed-a72f-0a1628958560',
'd461d33c-550f-11ed-90f5-0a1628958560',
'92ae7061-5375-11ed-a418-0a1628958560',
'35025a33-5853-11ed-9eff-0a1628958560',
# houdan test
'3cdc3aea-543d-11ed-9758-47cea17512cf',
'50d8ee38-584f-11ed-b9b3-612d467283a7',
'2c279852-543d-11ed-9758-47cea17512cf',
'bcd7a908-586d-11ed-b9b3-612d467283a7'
]

# https://github.com/airgap-it/beacon-sdk
# https://tezostaquito.io/docs/signing/

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/saas4ssi/dapp',  view_func=dapp_wallet, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/sandbox/saas4ssi/dapp/demo',  view_func=dapp_demo, methods = ['GET', 'POST'], defaults={'red' : red})
    
    app.add_url_rule('/sandbox/dapp/demo/webhook',  view_func=dapp_demo_webhook, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/sandbox/dapp/demo/stream',  view_func=dapp_demo_stream, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/sandbox/dapp/demo',  view_func=dapp_demo, methods = ['GET', 'POST'], defaults={'red' : red})

    app.add_url_rule('/sandbox/saas4ssi/dapp/webhook',  view_func=dapp_webhook, methods = ['GET', 'POST'], defaults={'red' : red})
    global link, client_secret
    if mode.myenv == 'aws':
        link = 'https://talao.co/sandbox/op/issuer/kfvuelfugb'
        client_secret = "c8a7ce61-52e7-11ed-96ff-0a1628958560"
    else :
        link = "http://192.168.0.220:3000/sandbox/op/issuer/ovjyigjpbc"
        client_secret = '9828d8f8-52d1-11ed-9758-47cea17512cf'

    return


def dapp_demo(red):
    #if request.method == 'GET' :
    return render_template('dapp_demo.html')
  


def dapp_wallet(red):
    if request.method == 'GET' :
        return render_template('dapp.html')
    else :
        id = str(uuid.uuid1())
        red.set(id, json.dumps({"associatedAddress" : request.form["address"],
                                "accountName" : request.form["wallet"],
                                "issuedBy" : {"name" : "Altme"}}))

        return redirect (link + "?id=" + id)

def dapp_webhook(red) :
    if request.headers.get("key") != client_secret :
        return jsonify("Forbidden"), 403
    data = request.get_json()
    try :
        data_returned = json.loads(red.get(data["id"]).decode())   
    except :
        print("error redis")
        data_returned = ""
    # send back data to issue credential
    if data['event'] == 'ISSUANCE' :
        return jsonify(data_returned)
    else :
        return jsonify('ok')


def dapp_demo_webhook(red) :
    if request.headers.get("key") not in issuer_and_verifier_list :
        return jsonify("Forbidden"), 403
    data = request.get_json()
    event_data = json.dumps({"data" : json.dumps(data)})
    if data['event'] != 'SIGNED_CREDENTIAL' :           
        red.publish('dapp_demo', event_data)
    return jsonify('ok')


def dapp_demo_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('dapp_demo')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)
