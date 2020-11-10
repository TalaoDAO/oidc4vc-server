import web_oauth
from models import db
from oauth2 import config_oauth


def config_api_server(app, mode) :

    oauth_config = {
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + mode.db_path + '/db.sqlite',
    'OAUTH2_TOKEN_EXPIRES_IN' : {
        'authorization_code': 300,
        #'implicit': 3000,
        #'password': 3000,
        'client_credentials': 3000
        }
    }
    app.config.update(oauth_config)
    db.init_app(app)
    config_oauth(app)

    # Main routes (Endpointd) for OAuth Authorization Server
    app.add_url_rule('/api/v1', view_func=web_oauth.home, methods = ['GET', 'POST'])
    app.add_url_rule('/api/v1/oauth_logout', view_func=web_oauth.oauth_logout, methods = ['GET', 'POST'])
    app.add_url_rule('/api/v1/oauth_login', view_func=web_oauth.oauth_login, methods = ['GET', 'POST'], defaults ={'mode' : mode})
    app.add_url_rule('/api/v1/create_client', view_func=web_oauth.create_client, methods = ['GET', 'POST'])
    app.add_url_rule('/api/v1/authorize', view_func=web_oauth.authorize, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/api/v1/oauth/token', view_func=web_oauth.issue_token, methods = ['POST'])
    
    # authorization code flow
    app.add_url_rule('/api/v1/oauth_revoke', view_func=web_oauth.revoke_token, methods = ['GET', 'POST'])
    app.add_url_rule('/api/v1/user_info', view_func=web_oauth.user_info, methods = ['GET', 'POST'], defaults={'mode' : mode})

    app.add_url_rule('/api/v1/user_accepts_status_request', view_func=web_oauth.user_accepts_status_request, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/api/v1/user_issues_certificate', view_func=web_oauth.oauth_user_issues_certificate, methods = ['GET', 'POST'], defaults={'mode' : mode})



    # client credentials code flow
    app.add_url_rule('/api/v1/create_person_identity', view_func=web_oauth.oauth_create_person_identity, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/api/v1/create_company_identity', view_func=web_oauth.oauth_create_company_identity, methods = ['GET', 'POST'], defaults={'mode' : mode})
    
    app.add_url_rule('/api/v1/issue_agreement', view_func=web_oauth.oauth_issue_agreement, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/api/v1/issue_reference', view_func=web_oauth.oauth_issue_reference, methods = ['GET', 'POST'], defaults={'mode' : mode})

    app.add_url_rule('/api/v1/get_certificate_list', view_func=web_oauth.oauth_get_certificate_list, methods = ['GET', 'POST'], defaults={'mode' : mode})

    app.add_url_rule('/api/v1/issue_experience', view_func=web_oauth.oauth_issue_experience, methods = ['GET', 'POST'], defaults={'mode' : mode})
    app.add_url_rule('/api/v1/get_status', view_func=web_oauth.oauth_get_status, methods = ['GET', 'POST'], defaults={'mode' : mode})

    return