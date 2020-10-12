"""

The two main functions are ipfs_add and ipfs_get , only for json data (dict format).

Strategy : one first tries to load from local ipfs server (timeout = 5s) then one loads from pinata

"""
import requests
import json
import shutil


def ipfs_add(json_dict, mode, name=None) :
	name = 'Unknown' if name is None else name
	ipfs_hash_pinata = add_dict_to_pinata(json_dict, name, mode)
	ipfs_hash_local = add_dict_to_local(json_dict)
	if ipfs_hash_pinata  != ipfs_hash_local :
		print('hash different')
	return ipfs_hash_pinata

def add_dict_to_pinata (data_dict, name, mode) :
	api_key = mode.pinata_api_key
	secret = mode.pinata_secret_api_key
	headers = {'Content-Type': 'application/json',
				'pinata_api_key': api_key,
               'pinata_secret_api_key': secret}
	data = { 'pinataMetadata' : {'name' : name}, 'pinataContent' : data_dict}
	response = requests.post('https://api.pinata.cloud/pinning/pinJSONToIPFS', data=json.dumps(data), headers=headers)
	return response.json()['IpfsHash']

def add_dict_to_local (data_dict) :
	data = {"json" : json.dumps(data_dict, separators=(',', ':'), ensure_ascii=False )}
	response = requests.post('http://127.0.0.1:5001/api/v0/add', files=data)
	return response.json()['Hash']

def file_add(filename, mode) :
	ipfs_hash_pinata = add_file_to_pinata(filename, mode)
	ipfs_hash_local = add_file_to_local(filename)
	if ipfs_hash_pinata  != ipfs_hash_local :
		print('hash different')
	return ipfs_hash_pinata

def add_file_to_pinata (filename, mode) :
	try :
		this_file = open(filename, mode='rb')  # b is important -> binary
	except IOError :
		print('IOEroor open file ')
	file_data = this_file.read()
	api_key = mode.pinata_api_key
	secret = mode.pinata_secret_api_key
	headers = {	'pinata_api_key': api_key,
              'pinata_secret_api_key': secret}
	payload = { 'file' : file_data}
	response = requests.post('https://api.pinata.cloud/pinning/pinFileToIPFS', files=payload, headers=headers)
	this_file.close()
	return response.json()['IpfsHash']

def add_file_to_local (filename) :
	try :
		this_file = open(filename, mode='rb')  # b is important -> binary
	except IOError :
		print('IOEroor open file ')
	file_data = this_file.read()
	payload = { 'file' : file_data}
	response = requests.post('http://127.0.0.1:5001/api/v0/add', files=payload)
	this_file.close()
	return response.json()['Hash']

def ipfs_get_pinata(ipfs_hash) :
	response = requests.get('https://gateway.pinata.cloud/ipfs/'+ipfs_hash)
	return response.json()

def ipfs_get_local(ipfs_hash) :
	response = requests.get('http://127.0.0.1:8080/ipfs/'+ipfs_hash, timeout=5)
	return(response.json())

def ipfs_get(ipfs_hash) :
	try :
		data = ipfs_get_local(ipfs_hash)
		print('get ipfs local', ipfs_hash)
		return data
	except :
		print('get ipfs pinata', ipfs_hash)
		data = ipfs_get_pinata(ipfs_hash)
		add_dict_to_local(data)
		return data

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
	try :
		response = requests.get('http://127.0.0.1:8080/ipfs/'+ipfs_hash, stream=True, timeout=5)
	except :
		response = requests.get('https://gateway.pinata.cloud/ipfs/'+ipfs_hash, stream=True)
	with open(filename, 'wb') as out_file:
		shutil.copyfileobj(response.raw, out_file)
		del response
	out_file.close()
	return True

#https://fr.python-requests.org/en/latest/user/quickstart.html#creer-une-requete


if __name__ == '__main__':
	pass

	ipfs_hash ='Qme3vLZP6n8xNQj6qmL8piGyWVUhm4oYhmYXMqvczzN3Z1'

