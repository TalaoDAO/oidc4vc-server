"""
install d un serveur ipfs sur debian
https://www.abyssproject.net/2019/01/installation-dun-serveur-ipfs-sous-debian-9-et-mise-a-jour/

The two main functions arr ipfs_add and ipfs_get , only for json data (dict format).

"""
import requests
import json
import shutil

#client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https', chunk_size=3500)


def ipfs_add(json_dict, name=None) :
	name = 'Unknown' if name is None else name
	ipfs_hash_pinata = add_to_pinata(json_dict, name)
	ipfs_hash_local = add_to_local(json_dict)
	if ipfs_hash_pinata  != ipfs_hash_local :
		print('hash different')
	return ipfs_hash_pinata

def add_to_pinata (data_dict, name) :
	api_key = '5bbb5c18e623c9b663ab'
	secret = '3d310e3acc5d1b51b5f20ed89d2ee221e157db8571d0d2f45f58d316f629e5dc'
	headers = {'Content-Type': 'application/json',
				'pinata_api_key': api_key,
               'pinata_secret_api_key': secret}
	data = { 'pinataMetadata' : {'name' : name}, 'pinataContent' : data_dict}		 
	response = requests.post('https://api.pinata.cloud/pinning/pinJSONToIPFS', data=json.dumps(data), headers=headers)
	return response.json()['IpfsHash']

def add_to_local (data_dict) :
	data = {"json" : json.dumps(data_dict, separators=(',', ':'), ensure_ascii=False )}
	response = requests.post('http://127.0.0.1:5001/api/v0/add', files=data)
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
		add_to_local(data)
		return data


		
def pin_to_pinata (my_hash) :
	api_key = '5bbb5c18e623c9b663ab'
	secret = '3d310e3acc5d1b51b5f20ed89d2ee221e157db8571d0d2f45f58d316f629e5dc'
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
	
#https://fr.python-requests.org/en/latest/user/quickstart.html#creer-une-requete

	
if __name__ == '__main__':
	pass
	
	
	ipfs_hash ='Qme3vLZP6n8xNQj6qmL8piGyWVUhm4oYhmYXMqvczzN3Z1'
	
