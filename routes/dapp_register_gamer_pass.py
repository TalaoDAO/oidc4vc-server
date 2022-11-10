from flask import render_template, request, jsonify, Response
import uuid 
import json

def init_app(app,red, mode) :
    app.add_url_rule('/sandbox/dapp/register_gamer_pass',  view_func=dapp_use_case, methods = ['GET', 'POST'])
    app.add_url_rule('/sandbox/dapp/use_case/webhook',  view_func=dapp_use_case_webhook, methods = ['GET', 'POST'], defaults={'red' : red})
    app.add_url_rule('/sandbox/dapp/use_case/stream',  view_func=dapp_use_case_stream, methods = ['GET', 'POST'], defaults={'red' : red})
    global payload_over13, payload_gamer_pass, payload_download_gamer_pass, payload_account
    if mode.myenv == 'aws':
        payload_over13 = 'I confirm i am over 13 years old #https://talao.co/sandbox/op/beacon/verifier/lhvnwdhczp?id='
        payload_download_gamer_pass =  'Get your Gamer Pass ! #https://talao.co/sandbox/op/beacon/zbsjclrass?id='
        payload_account = "I want to associate another account #https://talao.co/sandbox/op/beacon/verifier/wfzovnsjrg?id="
    else :
        payload_over13 = 'I confirm i am over 13 years old #http://192.168.0.65:3000/sandbox/op/beacon/verifier/nebmmcdkva?id='
        payload_download_gamer_pass = 'Get your Gamer Pass ! #http://192.168.0.65:3000/sandbox/op/beacon/mmibrdplfm?id='
        payload_account = 'I want to associate another account #http://192.168.0.65:3000/sandbox/op/beacon/verifier/yusbbdwdnv?id='
    return


def dapp_use_case():
    #if request.method == 'GET' :
    global payload_over13, payload_download_gamer_pass, payload_account
    id = str(uuid.uuid1())
    return render_template('./use_case/register_gamer_pass.html',
                             id = id,
                             payload_over13 = payload_over13 + id,
                             payload_download_gamer_pass = payload_download_gamer_pass + id,
                             payload_account = payload_account + id)
  


def dapp_use_case_webhook(red) :
    data = request.get_json()
    if data['event'] == 'VERIFICATION' :    
        if  "Over13" in data["vc_type"] :
            event_data = json.dumps({ 'id' : data['id'],
                                    "over13" : 'verified'})
            red.publish('use_case', event_data)
            red.setex(data['id'] + "_over13", 180, "true")
            return jsonify('ok')

        if  "TezosAssociatedAddress" in data["vc_type"] :
            event_data = json.dumps({ 'id' : data['id'],
                                    "account" : 'verified'})
            red.publish('use_case', event_data)
            try :
                tezosAddress = list()
                tezosAddress.append(red.get(data['id'] +'_TezosAssociatedAddress').decode())
                tezosAddress.append(data['associatedAddress'])
                red.setex(data['id'] + "_TezosAssociatedAddress", 180, json.dumps(tezosAddress))
            except :
                red.setex(data['id'] + "_TezosAssociatedAddress", 180, data['associatedAddress'])
            print (red.get(data['id'] + "_TezosAssociatedAddress").decode())
            return jsonify('ok')

        if  "EthereumAssociatedAddress" in data["vc_type"] :
            event_data = json.dumps({ 'id' : data['id'],
                                    "account" : 'verified'})
            red.publish('use_case', event_data)
            try :
                tezosAddress = list()
                tezosAddress.append(red.get(data['id'] +'_EthereumAssociatedAddress').decode())
                tezosAddress.append(data['associatedAddress'])
                red.setex(data['id'] + "_EthereumAssociatedAddress", 180, json.dumps(tezosAddress))
            except :
                red.setex(data['id'] + "_EthereumAssociatedAddress", 180, data['associatedAddress'])
            print (red.get(data['id'] + "_EthereumAssociatedAddress").decode())
            return jsonify('ok')
    
    if data['event'] == 'ISSUANCE' :
        credentialSubject = dict()
        try :
            credentialSubject['over13'] = red.get(data['id'] +'_over13').decode()
        except :
            print('No credential Over13')
        try :
            credentialSubject['tezosAddress'] = red.get(data['id'] +'_TezosAssociatedAddress').decode()
        except :
            print('No Tezos Address')
        try :
            credentialSubject['ethereumAddress'] = red.get(data['id'] +'_EthereumAssociatedAddress').decode()
        except :
            print('No Ethereum Address')
        credentialSubject.update({
            "alternateName" : "Unknown",
            "type" : "BloometaPass",
            "issuedBy" : {"name" : "Bloometa"}
        })
        print("data sent back to Issuer = ", credentialSubject)
        return jsonify(credentialSubject)

    if data['event'] == 'SIGNED_CREDENTIAL' :
        event_data = json.dumps({"gamer_pass" : 'issued',
                                    'id' : data['id'],
                                    'data' : json.dumps(data)})
        red.publish('use_case', event_data)
        return jsonify('ok')

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
