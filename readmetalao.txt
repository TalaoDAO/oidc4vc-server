Debian 10 buster

install ntp pour synchro
sudo apt-get install ntp

git clone https://github.com/ethereum/web3.py.git


python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -e .[dev] # pour lier l environnement de dev


instal de NGINX en dehors de venv (inutile pour un pc de test)
sudo apt-get install nginx
sudo apt-get install python3-pip python3-dev nginx
https://medium.com/faun/deploy-flask-app-with-nginx-using-gunicorn-7fda4f50066a

installation du serveur ipfs en dehors de venv
https://www.abyssproject.net/2019/01/installation-dun-serveur-ipfs-sous-debian-9-et-mise-a-jour/
pour arm (rasbeprry lire https://github.com/claudiobizzotto/ipfs-rpi
l install b ets pas la meme pour ce ARM

demarrage bootstrap ./Bootstrap\ Studio.AppImage --no-sandbox (Bootstrap Studio outils de design de vue html sous bootstrap)


Requirements :


instal de redis en dehors de venv
sudo apt install redis-server
retirer le PIDfile de redis.service /etc/systeld/system/redis.service

sudo apt install python3-pip

sous venv

pip install pyjwt
pip install flask
pip install Flask-FontAwesome
sudo apt-get install gunicorn (sous venv ou pas)
pip3 install flask-session redis

pip install -U numpy
pip install -U nltk 
sous python :
  >>> import nltk
  >>> nltk.download('punkt')
  >>>> nltk.download('stopwords')

pip install 'unidecode'
pip install authlib  (attention vers 0.15 . ne pas upgrader a la 1.0.)
pip install Flask-SQLAlchemy
pip install qrcode[pil]


"""
INFURA 
PROJECT ID
f2be8a3bf04d4a528eb416566f7b5ad6
PROJECT SECRET
3ca0226861a24074bdc206f9f89a8bf5

export WEB3_INFURA_PROJECT_ID=f2be8a3bf04d4a528eb416566f7b5ad6

MAINNET
https://mainnet.infura.io/v3/f2be8a3bf04d4a528eb416566f7b5ad6
wss://mainnet.infura.io/ws/v3/f2be8a3bf04d4a528eb416566f7b5ad6
********************************
