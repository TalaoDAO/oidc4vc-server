# local call --> gunicorn -c gunicornconf.py  --reload wsgi:app

workers = 5
loglevel = 'info'

#worker_class = 'gevent' 

errorlog = "-"
accesslog = "-"

timeout = 300  # sec
keepalive = 504  # sec
capture_output = True


# Environment variables
raw_env = [ "MYENV=aws"]
