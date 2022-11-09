from flask import render_template, request, jsonify, Response
import uuid 
import json


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/dapp/check_gamer_pass',  view_func=check_gamer_pass, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/dapp/check_gamer_pass/webhook',  view_func=check_gamer_pass_webhook, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/sandbox/dapp/check_gamer_pass/stream',  view_func=check_gamer_pass_stream, methods = ['GET', 'POST'], defaults={'red' : red})
    global payload_gamer_pass
    if mode.myenv == 'aws':
        payload_gamer_pass = 'I have a Gamer Pass #https://talao.co/sandbox/op/beacon/verifier/wfzovnsjrg?id='
    else :
        payload_gamer_pass =  'I have a Gamer Pass  #http://192.168.0.65:3000/sandbox/op/beacon/verifier/gkbekftugx?id='
    return


def check_gamer_pass():
    global payload_gamer_pass
    id = str(uuid.uuid1())
    return render_template('./use_case/check_gamer_pass.html',
                             id = id,
                             payload_gamer_pass = payload_gamer_pass + id)
  

def check_gamer_pass_webhook(red) :
    data = request.get_json()
    print('webhook data = ', data)
    if data['event'] == 'VERIFICATION' :
        if  "BloometaPass" in data["vc_type"]  :
            event_data = json.dumps({"gamer_pass" : 'verified',
                                    'id' : data['id'],
                                     'data' : json.dumps(data)})
            red.publish('check_gamer_pass', event_data)
    return jsonify('ok')


def check_gamer_pass_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('check_gamer_pass')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)
