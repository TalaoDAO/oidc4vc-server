from flask import render_template, request, jsonify, Response
import uuid 
import json


def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/dapp/check_tezid_over13',  view_func=check_tezid_over13, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/dapp/check_over13/stream',  view_func=check_tezid_over13_stream, methods = ['GET', 'POST'], defaults={'red' : red})
    global payload
    if mode.myenv == 'aws':
        payload = 'I am over 13 years old #https://talao.co/sandbox/op/beacon/verifier/tuaitvcrkl?id='
    else :
        payload = 'I am over 13#http://192.168.0.65:3000/sandbox/op/tezid/verifier/smbgvxvzfl?id='
    return


def check_tezid_over13():
    global payload_gamer_pass
    id = str(uuid.uuid1())
    return render_template('./use_case/check_tezid_over13.html',
                             id = id,
                             payload_gamer_pass = payload + id)
  

def check_tezid_over13_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('check_tezid_over13')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)
