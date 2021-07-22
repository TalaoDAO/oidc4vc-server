from components import Talao_message

import environment
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')
if not myenv :
   myenv='liveboxh'
mychain = 'talaonet'

logging.info('start to init environment')
mode = environment.currentMode(mychain,myenv)
logging.info('end of init environment')

Talao_message.messageHTML('Your professional credential has been issued.', 'subject', 'certificate_issued', {'username': 'Talao', 'link': 'https://talao.co'}, mode)
