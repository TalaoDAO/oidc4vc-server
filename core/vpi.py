"""
Check proof of identity vs whitelist
if no proof of identity ---> 0% (round = 0)
if issuer of proof of identity in white list ---> 100% (round = 1)
if issuer of proof of identity of issuer of proof of identity in white list ---> 50% (round = 2)
....

"""
import ns
from protocol import contractsToOwners, ownersToContracts
import constante


def get_white_list(identity_workspace_contract, mode) :
    white_list = list()
    contract = mode.w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
    key_list = contract.functions.getKeysByPurpose(5).call()
    print('***** Beginning of White list *****')
    for i in key_list :
        key = contract.functions.getKey(i).call()
        issuer = ns.get_data_from_publickey('0x' + key[2].hex(), mode)
        print('white list  address  = ', issuer)
        if issuer :
            white_list.append(issuer['address'])
    print('***** End of White List ****')
    return white_list

def get_proof_list(workspace_contract, mode) :
        contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
        category = contract.functions.identityInformation().call()[1]
        proof_list = list()
        type = 15000 if category == 1001 else 10000
        for doc_id in contract.functions.getDocuments().call() :
            doc = contract.functions.getDocument(doc_id).call()
            if doc[0] == type :
                proof_list.append(doc)
        return proof_list

def check_proof_of_identity(identity_workspace_contract, user_workspace_contract, mode) :
    global counter
    counter = 0

    def _check_proof_of_identity(identity_workspace_contract, user_workspace_contract, white_list, mode) :
        global counter
        if identity_workspace_contract == user_workspace_contract :
            return True
        if contractsToOwners(user_workspace_contract, mode) in white_list :
            print('One issuer in round ',counter,' is in white list')
            return True
        proof_list = get_proof_list(user_workspace_contract, mode)
        print('There are ', len(proof_list), ' proof(s) of identity')
        if not proof_list :
            return False
        for proof in proof_list :
            issuer_workspace_contract = ownersToContracts(proof[3], mode)
            counter += 1
            if _check_proof_of_identity(identity_workspace_contract, issuer_workspace_contract, white_list, mode) :
                return True
            counter -= 1
        print('No Proof of Identity with a white listed issuer')
        return False

    # display input parameters
    #identity_username = ns.get_username_from_resolver(identity_workspace_contract, mode)
    #user_username = ns.get_username_from_resolver(user_workspace_contract, mode)
    #print('Identity ' + identity_workspace_contract + '/'+ identity_username  + ' is checking the Identity ' + user_workspace_contract + '/' + user_username)

    # setup white list
    white_list = get_white_list(identity_workspace_contract, mode)
    if not white_list :
        print('No whitelist for ', identity_workspace_contract)
        return 0

    # call recursive function to look for one issuer in white list
    if _check_proof_of_identity(identity_workspace_contract, user_workspace_contract, white_list, mode) :
        return  0.5**counter
    return 0


# for test only
if __name__ == '__main__':

    import os
    import environment

    # Environment variables set in gunicornconf.py  and transfered to environment.py
    mychain = os.getenv('MYCHAIN')
    myenv = os.getenv('MYENV')
    # Environment setup
    mode = environment.currentMode(mychain,myenv)

    # test1 address
    test1_address = '0x106A53E31557296Ed1a81643d81c52334bb6F435'
    test1_workspace_contract =   '0x3B4bA595955c8E783aB565a9564D0E7F14a6CaaC'

    # thierry thevenet address
    tt_address = '0xE474E9a6DFD6D8A3D60A36C2aBC428Bf54d2B1E8'
    tt_workspace_contract = ownersToContracts(tt_address, mode)

    # wc de masociete
    workspace_contract = '0xc5C1B070b46138AC3079cD9Bce10010d6e1fCD8D'
    talao_workspace_contract = '0x4562DB03D8b84C5B10FfCDBa6a7A509FF0Cdcc68'

    # wc de newco 0xC15e3A2f17cD01c5A85F816165c455D9F954cBa9
    newco_workspace_contract = '0xC15e3A2f17cD01c5A85F816165c455D9F954cBa9'

    print('proof index= ', check_proof_of_identity(newco_workspace_contract, workspace_contract, mode))

