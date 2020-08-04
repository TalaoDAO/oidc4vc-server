
installation de geth avec snap


pour installer web3.py et venv
cf le lien https://github.com/ethereum/web3.py/blob/master/docs/README-linux.md

git clone https://github.com/ethereum/web3.py.git
cd web3.py
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -e .[dev] # pour installer l environnement de dev



Pour actver l enviropnnement virtuel python de mon compte
. venv/bin/activate


pour lancer le client geth en mode light et rpc (Http) par defaut en mode ipc
/usr/local/bin/geth --syncmode light --rpc
/usr/local/bin/geth --rinkeby --syncmode 'light'  --rpcapi="db,eth,net,web3,personal,web3" --cache=4096 --rpc --gcmode full


pour lancer la console geth
 sudo /usr/local/bin/geth attach rpc:http://127.0.0.1:8545



Gstion du fichier service geth.service de /etc/systemd/system/
sudo systemctl status geth.service
 sudo systemctl start geth.service
 sudo systemctl stop geth.service
 sudo systemctl enable geth.service pour creer un alias et en faire un service de demarrage


pour installer le JWT pour flask dans env
pip install pyjwt



dans venv
pip install flask


install des fonts pour boostrap
 pip install Flask-FontAwesome

install de gunicorn sous venv
sudo apt-get install gunicorn


instal de NGINX en dehors de venv
sudo apt-get install nginx
sudo apt-get install python3-pip python3-dev nginx
https://medium.com/faun/deploy-flask-app-with-nginx-using-gunicorn-7fda4f50066a

instal de redis en dehors de venv
sudo apt install redis-server
retirer le PIDfile de redis.service /etc/systeld/system/redis.service

import des libs python
https://hackersandslackers.com/managing-user-session-variables-with-flask-sessions-and-redis/
 pip3 install flask-session redis

update du git dans /Talao sous venv
git pull https://github.com/thierrythevenet1963/Talao.git

installation du serveur ipfs (pas sous venv)
https://www.abyssproject.net/2019/01/installation-dun-serveur-ipfs-sous-debian-9-et-mise-a-jour/
pour arm (rasbeprry lire https://github.com/claudiobizzotto/ipfs-rpi
l install b ets pas la meme pour ce ARM

instal ntp pour synchro
sudo apt-get install ntp


demarrage botstrap ./Bootstrap\ Studio.AppImage --no-sandbox


sous venv, nltk
sudo apt update
sudo apt install python3-pip
pip install -U numpy
pip install -U nltk (pas de sudo)
sous python :
  >>> import nltk
  >>> nltk.download('punkt')
  >>>> nltk.download('stopwords')

sous venv
 pip install 'unidecode'



