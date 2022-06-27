# Installation

## Requirements

Python 3.9+
didkit 0.3.0

## Install

mkdir issuer  
cd issuer
python3.10 -m venv venv  
. venv/bin/activate  

pip install redis
pip install Flask-Session
pip install Flask[async]
pip install didkit==0.3.0
pip install  Flask-QRcode
pip install  jwcrypto
pip install  pyjwt
pip install  gunicorn
pip install base58
pip install requests
pip install eth_keys
pip install pytezos
pip install PyGithub
