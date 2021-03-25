
from web3.auto.infura import w3
import json
import requests
import threading
import random

import constante

Talao_token_contract = '0x1D4cCC31dAB6EA20f461d329a0562C1c58412515'
Talao_wallet_ethereum = '0x379CEd2E6E0815Dcc9332408419EE4F2369732bC'
Talao_wallet_ethereum_private_key = '' # global variable
exporting_threads = {}

# Multithreading
class ExportingThread(threading.Thread):
	def __init__(self, address, private_key):
		super().__init__()
		self.address = address
		self.private_key = private_key

	def run(self):
		return _bridge(self.address, self.private_key)


# Send ether same as talao token transaction
def _ether_transfer(address_to, value):

     # get saleLow price from Ethereum Gas Sation 
    response = requests.get('https://ethgasstation.info/json/ethgasAPI.json')
    gas_price = int((int(response.json()['safeLow'])/10))
    print('gas price safeLow = ', gas_price, ' gwei')

    nonce = w3.eth.getTransactionCount(Talao_wallet_ethereum)
    transaction = {'to': address_to, 'value': value, 'gas': 25000, 'gasPrice': w3.toWei(gas_price, 'gwei'), 'nonce': nonce, 'chainId': 1}
	#sign transaction with TalaoGen wallet
    signed_txn = w3.eth.account.sign_transaction(transaction, Talao_wallet_ethereum_private_key)
    try :
        w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    except :
        return None
    hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    print('ether transfer transaction = ', hash)
    receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000)
    if receipt['status'] == 0:
        return None
    return hash

# Token transfer same as talao token transaction
def _token_transfer(address_to, value):

    # get saleLow price from Ethereum Gas Sation 
    response = requests.get('https://ethgasstation.info/json/ethgasAPI.json')
    gas_price = int((int(response.json()['safeLow'])/10))
    print('gas price safeLow = ', gas_price, ' gwei')

    contract = w3.eth.contract(
       Talao_token_contract, abi=constante.Talao_Token_ABI)
    nonce = w3.eth.getTransactionCount(Talao_wallet_ethereum)
    txn = contract.functions.transfer(address_to, value).buildTransaction(
	    {'chainId': 1, 'gas': 60000, 'gasPrice': w3.toWei(gas_price, 'gwei'), 'nonce': nonce, })
    signed_txn = w3.eth.account.signTransaction(txn, Talao_wallet_ethereum_private_key)
    
    w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    
    hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    print('token transfer transaction = ', hash)
    receipt = w3.eth.waitForTransactionReceipt(
        hash, timeout=2000, poll_latency=1)
    if receipt['status'] == 0:
        return None
    return hash


# Create Vault Access same as talao token transaction
def _createVaultAccess(address, private_key):

    # get saleLow price from Ethereum Gas Sation 
    response = requests.get('https://ethgasstation.info/json/ethgasAPI.json')
    gas_price = int((int(response.json()['safeLow'])/10))
    print('gas price safeLow = ', gas_price, ' gwei')

    contract = w3.eth.contract(
        Talao_token_contract, abi=constante.Talao_Token_ABI)
    nonce = w3.eth.getTransactionCount(address)
    txn = contract.functions.createVaultAccess(0).buildTransaction(
	    {'chainId': 1, 'gas': 100000, 'gasPrice': w3.toWei(gas_price, 'gwei'), 'nonce': nonce, })
    signed_txn = w3.eth.account.signTransaction(txn, private_key)
    
    w3.eth.sendRawTransaction(signed_txn.rawTransaction)

    hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    print('create vault access transaction = ', hash)
    receipt = w3.eth.waitForTransactionReceipt(hash, timeout=2000, poll_latency=1)
    if receipt['status'] == 0 :
    	return None		
    return hash

# Get back unused ether
def get_back_eth(address, private_key) :
    
    # get saleLow price from Ethereum Gas Sation 
    response = requests.get('https://ethgasstation.info/json/ethgasAPI.json')
    gas_price = int((int(response.json()['safeLow'])/10))
    print('gas price safeLow = ', gas_price, ' gwei')

    # get balance and sub transation fees
    balance = w3.eth.getBalance(address)
    print('Remaining balance (wei) ', balance)
    cost = w3.toWei(gas_price, 'gwei') * 21000
    if cost > balance :
        print('Not enough Eth to get them back from ', address) 
        return 0 
    
    eth_value = balance - cost
    print('Eth to transfer back (wei) : ', eth_value)
    nonce = w3.eth.getTransactionCount(address)
    transaction = {'to': Talao_wallet_ethereum, 'value': eth_value, 'gas': 21000, 'gasPrice': w3.toWei(gas_price, 'gwei'), 'nonce': nonce, 'chainId': 1}
	#sign transaction with address private key
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
    w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    print('Get back ether transaction = ', hash)
    return hash 

# main script
def _bridge(address, private_key) :

    # Get private key for Talao Wallet
    global Talao_wallet_ethereum_private_key
    keys = json.load(open('./keys.json'))
    Talao_wallet_ethereum_private_key = keys['ethereum']['talao_wallet_ethereum_private_key']
    print('wallet private key = ', Talao_wallet_ethereum_private_key)

    # confirm that the connection succeeded
    if not w3.isConnected() :
        print('Blockchain non connectée')
        return False

    # get current vault deposit on TALAO token smart contract on Ethereum 
    contract=w3.eth.contract(Talao_token_contract,abi=constante.Talao_Token_ABI)
    vault_deposit = contract.functions.vaultDeposit().call() 

    """
    # Get estimate of Eth to transfer
    response = requests.get('https://ethgasstation.info/json/ethgasAPI.json')
    gas_price = int((int(response.json()['safeLow'])/10))
    print('gas price safeLow = ', gas_price, ' gwei')
    value = (115000 + 30000) * w3.toWei(gas_price, 'gwei')
    print('to be transfered to address (Ether)  = ',w3.fromWei(value, 'ether'))

    # Transfert Eth to address to complete create workspace transaction
    if _ether_transfer(address, value) is None :
        print('pb transfer Eth')
        return False

    # Transfert Talao token to complete create workspace transaction
    if _token_transfer(address, vault_deposit) is None :
       print('pb trasnfer token')
       return False

    # Create Vault Access on Ethereum Talao Token smart contract
    if _createVaultAccess(address, private_key) is None :
       print('pb create vault access')
       return False
    
    # Get Eth back to Talao Wallet
    if get_back_eth(address, private_key) is None :
        print('pb get back ether')
        return False

    print('Ethereum Talao Token synchronization is over for ', address)
"""
# en attendant que les transaction fee baissent...on transfer les token du vault depsoit sur le token
    response = requests.get('https://ethgasstation.info/json/ethgasAPI.json')
    gas_price = int((int(response.json()['safeLow'])/10))
    print('Warning : gas price safeLow = ', gas_price, ' gwei')
    if gas_price > 40 :
        gas_price = 40
    address_to = Talao_token_contract
    value = vault_deposit
    contract = w3.eth.contract(
       Talao_token_contract, abi=constante.Talao_Token_ABI)
    nonce = w3.eth.getTransactionCount(Talao_wallet_ethereum)
    print('Warning : nonce =', nonce)
    txn = contract.functions.transfer(address_to, value).buildTransaction(
	    {'chainId': 1, 'gas': 100000, 'gasPrice': w3.toWei(gas_price, 'gwei'), 'nonce': nonce, })
    signed_txn = w3.eth.account.signTransaction(txn, Talao_wallet_ethereum_private_key)
    try :
        w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
        print('Warning : token transfer transaction brdge_ethereum.py= ', hash)
        #receipt = w3.eth.waitForTransactionReceipt(
        #    hash, timeout=2000, poll_latency=1)
        #if receipt['status'] == 0:
        #    print('transaction failed')
        #    return None
        #print('Ethereum Talao Token synchronization is done for ', address)
        return hash
    except :
        print('transaction refused')
        return None

def lock_ico_token(address, private_key) :
    thread_id = str(random.randint(0,10000 ))
    exporting_threads[thread_id] = ExportingThread(address, private_key)
    exporting_threads[thread_id].start()
    return True


#lock_ico_token(None, None)