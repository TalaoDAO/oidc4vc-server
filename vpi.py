"""
Check proof of identity vs whitelist
if no proof of identity ---> 0% (round = 0)
if issuer of proof of identity in white list ---> 100% (round = 1)
if issuer of proof of identity of issuer of proof of identity in white list ---> 50% (round = 2)
....

"""
import os
import ns
import environment
from protocol import contractsToOwners, ownersToContracts
import constante

# Environment variables set in gunicornconf.py  and transfered to environment.py
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')
# Environment setup
mode = environment.currentMode(mychain,myenv)

white_list = []
round = 0

def get_white_list(identity_workspace_contract, mode) :
    contract = mode.w3.eth.contract(identity_workspace_contract,abi = constante.workspace_ABI)
    key_list = contract.functions.getKeysByPurpose(5).call()
    for i in key_list :
        key = contract.functions.getKey(i).call()
        issuer = ns.get_data_from_publickey('0x' + key[2].hex(), mode)
        if issuer is None :
            pass
        else :
            white_list.append(issuer['address'])
    return white_list

def get_proof_list(workspace_contract, mode) :
    contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
    category = contract.functions.identityInformation().call()[1]
    proof_list = []
    type = 15000 if category == 1001 else 10000
    for doc_id in contract.functions.getDocuments().call() :
        doc = contract.functions.getDocument(doc_id).call()
        if doc[0] == type :
            proof_list.append(doc)
    return proof_list

def check_claim(identity_workspace_contract, user_workspace_contract, mode) :
    global round
    global white_list
    if round == 0 :
        identity_username = ns.get_username_from_resolver(identity_workspace_contract, mode)
        user_username = ns.get_username_from_resolver(user_workspace_contract, mode)
        print('Identity ' + identity_workspace_contract + '/'+ identity_username  + ' is checking the Identity ' + user_workspace_contract + '/' + user_username)
        white_list = get_white_list(identity_workspace_contract, mode)
        if white_list == [] :
            print('No whitelist for ', identity_workspace_contract)
            return 0
        for white_issuer_address in white_list :
            white_issuer_workspace_contract = ownersToContracts(white_issuer_address, mode)
            username = ns.get_username_from_resolver(white_issuer_workspace_contract, mode)
            print('White list -->', white_issuer_address + '/' + username)
    proof_list = get_proof_list(user_workspace_contract, mode)
    username = ns.get_username_from_resolver(user_workspace_contract,mode)
    print(user_workspace_contract+'/'+username, ' has ', len(proof_list), ' proof of identity')
    if proof_list == [] :
        print('No Proof of Identity.')
        return False
    else :
        for proof in proof_list :
            issuer_address = proof[3]
            if issuer_address in white_list :
                username = ns.get_username_from_resolver(ownersToContracts(issuer_address, mode), mode)
                print('issuer of proof of identity -->', issuer_address +'/' + username, ' is found in the whitelist at round = ', round)
                return True
        for proof in proof_list :
            issuer_address = proof[3]
            issuer_workspace_contract = ownersToContracts(issuer_address, mode)
            round += 1
            if check_claim(identity_workspace_contract, issuer_workspace_contract, mode) :
                return True
            round -= 1
        print('No Proof of Identity with white listed issuer')
        return False




# test1 address
test1_address = '0x106A53E31557296Ed1a81643d81c52334bb6F435'
# wc de test1  0x3B4bA595955c8E783aB565a9564D0E7F14a6CaaC
# thierry thevenet address
tt_address = '0xE474E9a6DFD6D8A3D60A36C2aBC428Bf54d2B1E8'
# wc de masociete
workspace_contract = '0xc5C1B070b46138AC3079cD9Bce10010d6e1fCD8D'

tt_workspace_contract = ownersToContracts(tt_address, mode)

check_claim(workspace_contract, tt_workspace_contract, mode)
print(round)