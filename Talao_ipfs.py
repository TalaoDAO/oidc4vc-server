import ipfshttpclient
import json

# retourne une chaine str
# en entrée un dictionnaire {"user": { "ethereum_account": '123' , "ethereum_contract": '234' ,"first_name" : 'Jean' ,"last_name" : 'Pierre' }}
def IPFS_add(json_data) :
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	response=client.add_json(json_data)
	response2=client.pin.add(response)
	return response



def IPFS_get(ipfs_hash) :
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	return(client.get_json(ipfs_hash))

#res=client.get_json('QmSifSzujmUq2w9nAJFLuAS9BVGDyM2jqw7dCgkD47igL3')
#res = client.add_json( {"user": { "ethereum_account": '123' , "ethereum_contract": '234' ,"first_name" : 'Jean' ,"last_name" : 'Pierre' }} )

