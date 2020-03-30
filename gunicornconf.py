import environment
import multiprocessing

mode=environment.currentMode('test', 'rinkeby')

bind = mode.flaskserver+':'+mode.port
workers = 3
#workers = multiprocessing.cpu_count()*2


loglevel = 'info'
# errorlog = os.path.join(_VAR, 'log/api-error.log')
# accesslog = os.path.join(_VAR, 'log/api-access.log')
errorlog = "-"
accesslog = "-"

timeout = 3 * 60  # 3 minutes
keepalive = 24 * 60 * 60  # 1 day
capture_output = True
