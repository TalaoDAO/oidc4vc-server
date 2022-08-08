from flask import Flask, jsonify
import flask
from flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from flask_pyoidc.user_session import UserSession

# Init Flask
app = Flask(__name__)
app.config.update(
    OIDC_REDIRECT_URI = 'http://127.0.0.1:4000/callback', # your application redirect uri. Must be not used in your code
    SECRET_KEY = "lkjhlkjh" # your application secret code for session, random
)

"""
Init OpenID Connect client PYOIDC with teh 3 bridge parameters :  client_id, client_secret and issuer URL
"""
client_metadata = ClientMetadata(
    client_id='fhwrsmszjn',
    client_secret= "9bd6eeb0-0617-11ed-8fe6-8d54d1ffa6d3",
    post_logout_redirect_uris=['http://127.0.0.1:4000/logout']) # your post logout uri (optional)

provider_config = ProviderConfiguration(issuer='https://talao.co/sandblox/op',
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
                   userinfo=user_session.userinfo) # this is the user credential


if __name__ == '__main__':
    IP = "127.0.0.1"
    app.run( host = IP, port=4000, debug =True)