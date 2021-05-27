"""
CCI API

"""
from flask import jsonify, request, make_response
import logging
logging.basicConfig(level=logging.INFO)
import constante
from components import ns, directory


def credential_list (mode) :
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
    if not username :
        logging.info('username not found for siren = %s', siren)
        data =  jsonify(
                    message="SIRET not found.",
                    category="error",
                    status=404
                )
        return make_response(data,404)

    try :
        workspace_contract = ns.get_data_from_username(username, mode)['workspace_contract']
        contract = mode.w3.eth.contract(workspace_contract,abi = constante.workspace_ABI)
        doc_list =  contract.functions.getDocuments().call()
    except :
        logging.error('talaonet call failed')
        data =  jsonify(
                    message="Internal server error.",
                    category="error",
                    status=500
                )
        return make_response(data,500)

    credential_link_list = []
    for doc_id in doc_list :
        if contract.functions.getDocument(doc_id).call()[0] == 20000 : # doctype for public credential
            link = mode.server + 'certificate/?certificate_id=did:talao:talaonet:' + workspace_contract[2:] + ':document:' + str(doc_id)
            credential_link_list.append(link)
    data = jsonify(
                message= "Credential link list",
                category="success",
                data= credential_link_list,
                status=200
            )
    return make_response(data,200)



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
    if not username :
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

