import ns
import environment
import os


# Environment variables set in gunicornconf.py  and transfered to environment.py
mychain = 'talaonet'
myenv = 'aws'
mode = environment.currentMode(mychain,myenv)

ns.alter_add_wallet_field(mode)

