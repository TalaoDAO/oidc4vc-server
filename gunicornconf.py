# local call --> gunicorn -c gunicornconf.py  --reload wsgi:app

workers = 5
loglevel = 'info'

worker_class = 'gevent' 

errorlog = "-"
accesslog = "-"

timeout = 180  # sec
keepalive = 504  # sec
capture_output = True
#timeout = 3 * 60  # 3 minutes
#keepalive = 5 * 24 * 60 * 60  # 5 days

# Environment variables
raw_env = [ "MYENV=aws"]
