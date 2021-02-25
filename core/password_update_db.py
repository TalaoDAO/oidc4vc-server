from core import ns
import constante
import environment

mode = environment.currentMode()
w3 = mode.w3


	
	
ns.alter_add_password_field('nameservice.db', mode)
	
ns.alter_add_password_field_manager('edf.db', mode)
ns.alter_add_password_field_manager('thales.db', mode)
ns.alter_add_password_field_manager('orange.db',  mode)
ns.alter_add_password_field_manager('skillvalue.db', mode)
ns.alter_add_password_field_manager('talao.db', mode)
ns.alter_add_password_field_manager('relay.db', mode)
ns.alter_add_password_field_manager('bnp.db',mode)