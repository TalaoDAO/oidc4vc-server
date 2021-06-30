from web3.contract import ContractEvent
import os
from eth_account._utils.signing import extract_chain_id, to_standard_v
from eth_account._utils.transactions import ALLOWED_TRANSACTION_KEYS
from eth_account._utils.transactions import serializable_unsigned_transaction_from_dict
import logging
logging.basicConfig(level=logging.INFO)

import constante

def get_key(workspace_contract, address, days, mode) :

    contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
    block_number = mode.w3.eth.getBlock('latest')['number']
    # 30 days behind, one transaction every 15s except for Talaonet...

    if mode.BLOCKCHAIN == 'talaonet' :
        fromblock = 0
    else :
        fromblock = block_number - (days * 24 * 60 * 4)

    filter = contract.events.KeyAdded.createFilter(fromBlock=fromblock,toBlock = 'latest')
    eventlist = filter.get_all_entries()
    for i in range(0, len(eventlist)) :
        event = eventlist[i]
        transaction_hash = event['transactionHash']
        tx = mode.w3.eth.getTransaction(transaction_hash)
        if tx['from'] == address :
            break
    logging.info('transaction hash = %s', transaction_hash)
    tx.hash

    s = mode.w3.eth.account._keys.Signature(vrs=(
        to_standard_v(extract_chain_id(tx.v)[1]),
        mode.w3.toInt(tx.r),
        mode.w3.toInt(tx.s)
        ))

    tt = {k:tx[k] for k in ALLOWED_TRANSACTION_KEYS - {'chainId', 'data'}}
    tt['data']=tx.input
    tt['chainId']=extract_chain_id(tx.v)[0]

    ut = serializable_unsigned_transaction_from_dict(tt)
    pubkey = s.recover_public_key_from_msg_hash(ut.hash())
    logging.info('public key = %s', pubkey)
    return str(pubkey)


if __name__ == '__main__':

    import environment
    test_workspace_1 = "0xc5C1B070b46138AC3079cD9Bce10010d6e1fCD8D"
    test_workspace_2 = "0x81d8800eDC8f309ccb21472d429e039E0d9C79bB"
    address = '0x194d92A8798c14Dc59080aF4Baf4588140F34F49'
    address = '0x5f736A4A69Cc9A6F859be788A9f59483A2219d1C'
    mychain = os.getenv('MYCHAIN')
    myenv = os.getenv('MYENV')
    mode = environment.currentMode(mychain,myenv)
    a =get_key(test_workspace_1, address, 0, mode)
