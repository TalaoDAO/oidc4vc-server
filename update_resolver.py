
import environment
from components import ns
# environment setup
mode = environment.currentMode('talaonet', 'aws')
w3 = mode.w3
ns.alter_resolver_table(mode)
