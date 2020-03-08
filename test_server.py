#import http.client, urllib.parse
from flask import Flask, jsonify
from flask import request
from flask_api import FlaskAPI

import json
import GETdata
import GETresolver
import GETresume

# https://flask.palletsprojects.com/en/1.1.x/quickstart/


app = FlaskAPI(__name__)

@app.route('/talao/api/<data>', methods=['GET'])
def Main(data) :
	return GETdata.getdata(data)
	
@app.route('/talao/api/resolver/<did>', methods=['GET'])
def Resolver(did) :
	return GETresolver.getresolver(did)

@app.route('/talao/api/data/<data>', methods=['GET'])
def Data(data) :
	return GETdata.getdata(data)

@app.route('/talao/api/resume/<did>', methods=['GET'])
def Resume(did) :
	return GETresume.getresume(did)
	
@app.route('/talao/api/doc/')
def doc() :
	doc ={ "API" : [
		
			{'name' : 'data',
			'endpoint' : '/talao/api/<data>',
			'method' : "",
			'description' : 'Retourne la description du user ou de la data' 
				},	
			{'name' : 'resolver',
			'endpoint' : '/talao/api/resolver/<data>',
			'method' : "",
			'description' : 'Retourne la description du user ou de la data' 
				}
	]}

	return doc
	
"""
@app.route('/api/v1.0/profil', methods=['GET'])
def get_profil():
	address=request.data.get("address")
	return jsonify(Talao_token_transaction.readProfil(address))

@app.route('/api/v1.0/experience', methods=['GET'])
def get_experience():
	address=request.data.get("address")	
	index=Talao_token_transaction.getDocumentIndex(address, 50000)
	return jsonify(Talao_token_transaction.getDocument(address,50000, index-1))

@app.route('/api/v1.0/diploma', methods=['GET'])
def get_diploma():
	address=request.data.get("address")
	index=Talao_token_transaction.getDocumentIndex(address, 40000)
	return jsonify(Talao_token_transaction.getDocument(address,40000, index-1))

@app.route('/api/v1.0/skill', methods=['GET'])
def get_skill():
	address=request.data.get("address")
	index=Talao_token_transaction.getDocumentIndex(address, 50000)
	i=0
	_skills=[]
	while i < index :
		_skills.extend(Talao_token_transaction.getDocument(address,50000, i)['certificate']['skills'])
		i=i+1
	return jsonify({'skills': _skills})
"""

if __name__ == '__main__':
    app.run(debug=True)
