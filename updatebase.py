import environment
import constante
import os

from core import ns

# Environment variables set in gunicornconf.py  and transfered to environment.py
mychain = os.getenv('MYCHAIN')
myenv = os.getenv('MYENV')
mode = environment.currentMode(mychain,myenv)


#wc = "0x2e06194D1F093509E10490Da5426A373A79eE44A"
#ns.alter_manager_table(database, mode)
#ns.alter_credential_table(database, mode)
#ns.add_table_employee(database, mode)
database = input('company name ? ')
ns.init_host(database, mode)
