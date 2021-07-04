"""

The two main functions are ipfs_add and ipfs_get , only for json data (dict format).

Strategy : one first tries to load from local ipfs server (timeout = 5s) then one loads from pinata

"""
import requests
import json
import shutil
import logging
logging.basicConfig(level=logging.INFO)

def ipfs_add(json_dict, mode, name='unknown') :
	ipfs_hash_pinata = add_dict_to_pinata(json_dict, name, mode)
	return ipfs_hash_pinata

def add_dict_to_pinata (data_dict, name, mode) :
	api_key = mode.pinata_api_key
	secret = mode.pinata_secret_api_key
	headers = {'Content-Type': 'application/json',
				'pinata_api_key': api_key,
               'pinata_secret_api_key': secret}
	data = { 'pinataMetadata' : {'name' : name}, 'pinataContent' : data_dict}
	try :
		response = requests.post('https://api.pinata.cloud/pinning/pinJSONToIPFS', data=json.dumps(data), headers=headers)
	except :
		return None
	return response.json()['IpfsHash']


def file_add(filename, mode) :
	ipfs_hash_pinata = add_file_to_pinata(filename, mode)
	return ipfs_hash_pinata

def add_file_to_pinata (filename, mode) :
	try :
		this_file = open(filename, mode='rb')  # b is important -> binary
	except IOError :
		logging.error('IOEroor open file ')
		return None
	headers = {	'pinata_api_key': mode.pinata_api_key,
              'pinata_secret_api_key':  mode.pinata_secret_api_key}
	payload = { 'file' : this_file.read()}
	try :
		response = requests.post('https://api.pinata.cloud/pinning/pinFileToIPFS', files=payload, headers=headers)
	except :
		logging.error('IPFS connexion problem')
		return None
	this_file.close()
	return response.json()['IpfsHash']

def ipfs_get_pinata(ipfs_hash) :
	response = requests.get('https://gateway.pinata.cloud/ipfs/'+ipfs_hash)
	return response.json()


def ipfs_get(ipfs_hash, mode) :
		return ipfs_get_pinata(ipfs_hash)


def pin_to_pinata (my_hash, mode) :
	api_key = mode.pinata_api_key
	secret = mode.pinata_secret_api_key
	headers = {'Accept': 'application/json',
				'Content-type': 'application/json',
				'pinata_api_key': api_key,
                'pinata_secret_api_key': secret}

	payload = {'hashToPin' : my_hash}
	response = requests.post('https://api.pinata.cloud/pinning/pinByHash', data=json.dumps(payload), headers=headers)
	return response.json()['IpfsHash']

def get_picture(ipfs_hash, filename) :
	response = requests.get('https://gateway.pinata.cloud/ipfs/'+ipfs_hash, stream=True)
	with open(filename, 'wb') as out_file:
		shutil.copyfileobj(response.raw, out_file)
		del response
	out_file.close()
	return True


if __name__ == '__main__':
	pass

	ipfs_hash ='Qme3vLZP6n8xNQj6qmL8piGyWVUhm4oYhmYXMqvczzN3Z1'

