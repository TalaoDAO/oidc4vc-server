from flask import render_template, request, jsonify, Response, session
import uuid 
import json

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/dapp/use_case',  view_func=dapp_use_case, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/dapp/use_case/webhook',  view_func=dapp_use_case_webhook, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/sandbox/dapp/use_case/stream',  view_func=dapp_use_case_stream, methods = ['GET', 'POST'], defaults={'red' : red})
    global payload_over18, payload_student, payload_loyalty
    if mode.myenv == 'aws':
        payload_over18 = 'I confirm i am 18 yo or over#https://talao.co/sandbox/op/beacon/verifier/lhvnwdhczp?id='
        payload_student = 'I have a student card#https://talao.co/sandbox/op/beacon/verifier/wfzovnsjrg?id='
        payload_loyalty =  'Get your loyalty card !#https://talao.co/sandbox/op/beacon/zbsjclrass?id='
    else :
        payload_over18 = 'I confirm i am 18 yo or over#http://192.168.0.65:3000/sandbox/op/beacon/verifier/nebmmcdkva?id='
        payload_student =  'I have a student card#http://192.168.0.65:3000/sandbox/op/beacon/verifier/avtfbpsebn?id='
        payload_loyalty = 'Get your loyalty card !#http://192.168.0.65:3000/sandbox/op/beacon/mmibrdplfm?id='
    return


def dapp_use_case():
    #if request.method == 'GET' :
    global payload_over18, payload_student, payload_loyalty
    id = str(uuid.uuid1())
    return render_template('./use_case/dapp_use_case.html',
                             id = id,
                             payload_over18 = payload_over18 + id,
                             payload_student = payload_student + id,
                             payload_loyalty = payload_loyalty + id)
  


def dapp_use_case_webhook(red) :
    data = request.get_json()
    if data['event'] == 'VERIFICATION' :
        if  "Over18" in data["vc_type"] :
            event_data = json.dumps({"over18" : 'ok',
                                     'id' : data['id'],
                                     'data' : json.dumps(data)})
            red.publish('use_case', event_data)
        if "LearningAchievement" in data["vc_type"] :
            event_data = json.dumps({"student" : 'ok',
                                    'id' : data['id'],
                                     'data' : json.dumps(data)})
            red.publish('use_case', event_data)
    if data['event'] == 'SIGNED_CREDENTIAL' :
        event_data = json.dumps({"welcome" : 'ok',
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
