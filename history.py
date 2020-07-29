from datetime import datetime
from protocol import ownersToContracts, read_profil
import constante
from web3.contract import ContractEvent


def history_html(workspace_contract, days, mode) :
	history = dict()
	history_string = """ """
	contract = mode.w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	block = mode.w3.eth.getBlock('latest')
	block_number = block['number']
	# 30 days behind, one transaction every 15s
	fromblock = block_number - (days * 24 * 60 * 4) 
	filter_list = [	contract.events.PartnershipRequested.createFilter(fromBlock= fromblock,toBlock = 'latest'),
				contract.events.PartnershipAccepted.createFilter(fromBlock=fromblock,toBlock = 'latest'),
				contract.events.KeyAdded.createFilter(fromBlock=fromblock,toBlock = 'latest'),
				contract.events.DocumentAdded.createFilter(fromBlock=fromblock,toBlock = 'latest'),
				contract.events.DocumentRemoved.createFilter(fromBlock=fromblock,toBlock = 'latest'),
				contract.events.ClaimRemoved.createFilter(fromBlock=fromblock,toBlock = 'latest'),
				contract.events.ClaimAdded.createFilter(fromBlock=fromblock,toBlock = 'latest'),
				contract.events.KeyRemoved.createFilter(fromBlock=fromblock,toBlock = 'latest')]
	for i in range(0, len(filter_list)) :
		eventlist = filter_list[i].get_all_entries()
		for doc in eventlist :
			
			transactionhash = doc['transactionHash']
			transaction = mode.w3.eth.getTransaction(transactionhash)
			issuer = transaction['from']
			issuer_workspace_contract = ownersToContracts(issuer,mode)
			profil, category = read_profil(issuer_workspace_contract, mode, loading='light')
			if category == 1001:
				firstname = "Unknown" if profil['firstname'] is None else profil['firstname']					
				lastname = "Unknown" if profil['lastname'] is None else profil['lastname']
				issuer_name = firstname + ' ' + lastname
			if category == 2001 :				
				issuer_name = 'unknown' if  profil['name'] is None else profil['name']
			
			blockNumber = transaction['blockNumber']
			block = mode.w3.eth.getBlock(blockNumber)
			date = datetime.fromtimestamp(block['timestamp'])
			
			# html view preparation
			issuer_name = 'me' if issuer_name == 'Relay' else issuer_name	
			issuer_name = 'me' if issuer_workspace_contract == workspace_contract else issuer_name	
		
			if i == 4 :
				history[date] = 'Document ' + str(doc['args']['id'])  + ' removed by ' + issuer_name
			elif i == 3 :
				history[date] = 'Document ' + str(doc['args']['id']) + ' created by ' + issuer_name
			elif i == 2  and doc['args']['purpose'] == 20002 :
				history[date] = 'New Referent added'
			elif i == 2  and doc['args']['purpose'] == 5 :
				history[date] = 'New issuer for White List'
			elif i == 6  :
				history[date] = 'Personal Setting updated'
			elif i == 7  and doc['args']['purpose'] == 20002  :
				history[date] = 'Referent removed'
			elif i == 7  and doc['args']['purpose'] == 5  :
				history[date] = 'Issuer removed from White List'
			elif i == 7  and doc['args']['purpose'] == 3  :
				history[date] = 'Claim Key removed'
			else :
				history[date] = 'unknown ' + doc['event']		
		
	sorted_history = sorted(history.items(), key=lambda x: x[0], reverse=True)
	
	
	for event in sorted_history :
		history_string = history_string + str(event[0]) + ' - ' + event[1] + """<br>""" 	
	print(history_string)					
	return history_string


