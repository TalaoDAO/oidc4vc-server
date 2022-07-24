from flask import Flask, jsonify
import flask
from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from flask_pyoidc.user_session import UserSession

# Init Flask
app = Flask(__name__)
app.config.update(
    OIDC_REDIRECT_URI = 'http://127.0.0.1:4000/callback',
    SECRET_KEY = "lkjhlkjh"
)

"""
Init OpenID Connect client with parameters :  client_id, client_secret and issuer URL
"""
client_metadata = ClientMetadata(
    client_id='llsiaepgnf',
    client_secret= "ca969c0a-0059-11ed-92c8-719c6cd35d00",
    post_logout_redirect_uris=['http://127.0.0.1:4000/logout'])
provider_config = ProviderConfiguration(issuer='http://192.168.0.65:3000/sandbox/op',
                                        client_metadata=client_metadata)
auth = OIDCAuthentication({'default': provider_config}, app)



""" 
Verifiable Credential presented by user is transfered through vp_token in OAuth2 userinfo endpoint

"""
@app.route('/')
@auth.oidc_auth('default')
def index():
    user_session = UserSession(flask.session)
    return jsonify(access_token=user_session.access_token,
                   id_token=user_session.id_token,
                   userinfo=user_session.userinfo)


if __name__ == '__main__':
    IP = "127.0.0.1"
    app.run( host = IP, port=4000, debug =True)
