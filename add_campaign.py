
from components import ns
import environment
import os

# environment setup
mode = environment.currentMode("talaonet", "airbox")
w3 = mode.w3

while True :
    host= input('company ? : ')
    ns.add_table_campaign(host, mode)
