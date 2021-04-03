
from components import ns
import environment
import os

# environment setup
mode = environment.currentMode("talaonet", "airbox")
w3 = mode.w3

ns.alter_resolver_table(mode)
