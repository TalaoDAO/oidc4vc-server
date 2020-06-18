import ipfshttpclient
import json

def ipfs_add(json_dict) :
	""" add a json file as a dict example : ipfs_add({ 'data' : 123}) """
	#client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https', chunk_size=3500)
	client = ipfshttpclient.connect('/dns/127.0.0.1/tcp/5001/http', chunk_size=35000)
	try : 
		response=client.add_json(json_dict)
		response2=client.pin.add(response)
		return response
	except :
		print('ipfs http error dans document.py')
		return None


def ipfs_get(ipfs_hash) :
	#client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	client = ipfshttpclient.connect('/dns/127.0.0.1/tcp/5001/http', chunk_size=3500)
	return(client.get_json(ipfs_hash))




	
if __name__ == '__main__':
	print(IPFS_add({'data' : 123}))	
