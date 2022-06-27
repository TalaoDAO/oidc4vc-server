# local call --> gunicorn -c gunicornconf.py  --reload wsgi:app

workers = 5
loglevel = 'info'

errorlog = "-"
accesslog = "-"

timeout = 3 * 60  # 3 minutes
keepalive = 5 * 24 * 60 * 60  # 5 days
capture_output = True


# Environment variables
raw_env = [ "MYENV=aws"]
