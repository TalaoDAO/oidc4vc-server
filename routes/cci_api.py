"""
CCI API

"""
from sys import int_info
from flask import jsonify, request, make_response
import logging
logging.basicConfig(level=logging.INFO)
import constante
from components import ns, directory
from protocol import Document


def credential_list (mode) :
    """ request GET , arguments
    @app.route('/api/v1/credential', methods=['GET'], defaults={'mode' : mode})
    "siret" : required, only siren is used (9 first numbers)
    "data : optionam to get content
    """
    print(request.args)
    data = request.args.get('data')
    try :
        siren = request.args['siret'][:9]
    except :
        logging.info('request malformed %s', request.args)
        return make_response (jsonify(
                    message="Malformed request syntax or invalid request message parameters.",
                    category="error",
                    status=400
                    ), 400)

    username = directory.search_siren(siren, mode)
    if not username or not ns.username_exist(username, mode) :
        logging.info('username not found for siren = %s', siren)
        return make_response (  jsonify(
                    message="SIRET not found.",
                    category="error",
                    status=404
                    ), 404)

    try :
        workspace_contract = ns.get_data_from_username(username, mode)['workspace_contract']
        contract = mode.w3.eth.contract(workspace_contract,abi = constante.workspace_ABI)
        doc_list =  contract.functions.getDocuments().call()
    except :
        logging.error('talaonet call failed')
        return make_response (  jsonify(
                    message="Internal server error.",
                    category="error",
                    status=500
                    ), 200)

    result = []

    if data  :
        for doc_id in doc_list :
            if contract.functions.getDocument(doc_id).call()[0] == 20000 :
                credential = Document('credential')
                credential.relay_get_credential(workspace_contract, doc_id, mode)
                result.append(credential.__dict__)
        message = "Credential data"
    else :
        for doc_id in doc_list :
            if contract.functions.getDocument(doc_id).call()[0] == 20000 : # doctype for public credential
                link = mode.server + 'certificate/?certificate_id=did:talao:talaonet:' + workspace_contract[2:] + ':document:' + str(doc_id)
                result.append(link)
        message = "Credential link list"

    return make_response( jsonify(
                    message= message,
                    category="success",
                    data= result,
                    status=200
                    ),
                 200)



def resolver (mode) :
    """ request GET , arguments
    @app.route('/api/v1/credential', methods=['GET'], defaults={'mode' : mode})
    "siret" : required, only siren is used (9 first numbers)
    """
    try :
        siren = request.args['siret'][:9]
    except :
        logging.info('request malformed %s', request.args)
        data =  jsonify(
                    message="Malformed request syntax or invalid request message parameters.",
                    category="error",
                    status=400
                )
        return make_response(data,400)

    username = directory.search_siren(siren, mode)
    if not username or not ns.username_exist(username, mode) :
        logging.info('username not found for siren = %s', siren)
        data =  jsonify(
                    message="SIRET not found.",
                    category="error",
                    status=404
                )
        return make_response(data,404)
    try :
        workspace_contract = ns.get_data_from_username(username, mode)['workspace_contract']
    except :
        logging.error('talaonet call failed')
        data =  jsonify(
                    message="Internal server error.",
                    category="error",
                    status=500
                )
        return make_response(data,500)

    did = ns.get_did(workspace_contract, mode)
    data = jsonify(
                message= "DID",
                category="success",
                data=did,
                status=200
            )
    return make_response(data,200)

