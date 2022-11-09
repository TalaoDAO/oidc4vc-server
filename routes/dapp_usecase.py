from flask import render_template, request, jsonify, Response
import uuid 
import json

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/dapp/use_case',  view_func=dapp_use_case, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/dapp/use_case/webhook',  view_func=dapp_use_case_webhook, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/sandbox/dapp/use_case/stream',  view_func=dapp_use_case_stream, methods = ['GET', 'POST'], defaults={'red' : red})
    global payload_over13, payload_gamer_pass, payload_download_gamer_pass, payload_account
    if mode.myenv == 'aws':
        payload_over13 = 'I confirm i am over 13 years old #https://talao.co/sandbox/op/beacon/verifier/lhvnwdhczp?id='
        payload_gamer_pass = 'I have a Gamer Pass #https://talao.co/sandbox/op/beacon/verifier/wfzovnsjrg?id='
        payload_download_gamer_pass =  'Get your Gamer Pass ! #https://talao.co/sandbox/op/beacon/zbsjclrass?id='
    else :
        payload_over13 = 'I confirm i am over 13 years old #http://192.168.0.65:3000/sandbox/op/beacon/verifier/nebmmcdkva?id='
        payload_gamer_pass =  'I have a Gamer Pass #http://192.168.0.65:3000/sandbox/op/beacon/verifier/qvlbdmdziv?id='
        payload_download_gamer_pass = 'Get your Gamer Pass ! #http://192.168.0.65:3000/sandbox/op/beacon/mmibrdplfm?id='
        payload_account = 'Select an account #http://192.168.0.65:3000/sandbox/op/beacon/verifier/yusbbdwdnv?id='
    return


def dapp_use_case():
    #if request.method == 'GET' :
    global payload_over13, payload_gamer_pass, payload_download_gamer_pass, payload_account
    id = str(uuid.uuid1())
    return render_template('./use_case/dapp_use_case.html',
                             id = id,
                             payload_over13 = payload_over13 + id,
                             payload_gamer_pass = payload_gamer_pass + id,
                             payload_download_gamer_pass = payload_download_gamer_pass + id,
                             payload_account = payload_account + id)
  


def dapp_use_case_webhook(red) :
    data = request.get_json()
    if data['event'] == 'VERIFICATION' :

        if  "Over13" in data["vc_type"] :
            event_data = json.dumps({"over13" : 'verified',
                                     'id' : data['id'],
                                     'data' : json.dumps(data)})
            red.publish('use_case', event_data)
        if  "TezosAssociatedAddress" in data["vc_type"] :
            event_data = json.dumps({"account" : 'verified',
                                     'id' : data['id'],
                                     'data' : json.dumps(data)})
            red.publish('use_case', event_data)
        if "BloometaPass" in data["vc_type"]  :
            event_data = json.dumps({"gamer_pass" : 'verified',
                                    'id' : data['id'],
                                     'data' : json.dumps(data)})
            red.publish('use_case', event_data)
            print(event_data)
    if data['event'] == 'SIGNED_CREDENTIAL' :
        event_data = json.dumps({"gamer_pass" : 'issued',
                                    'id' : data['id'],
                                    'data' : json.dumps(data)})
        red.publish('use_case', event_data)
    return jsonify('ok')



def dapp_use_case_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('use_case')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)
