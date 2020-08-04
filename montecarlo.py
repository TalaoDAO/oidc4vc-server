import math
import random
import datetime
import Talao_message

carre = 0
cercle = 0
display = 10  
iteration = 0

while True : 
	x = random.randint(0, 100000)
	y = random.randint(0, 100000)
	p = x*x + y*y
	if p < 10000000000 :
		cercle += 1	
		carre += 1
	else :
		carre += 1
	if carre == display :
		iteration +=1
		print(datetime.datetime.now(), ' iteration = 10 EXP', iteration , ' pi = ', cercle*4)
		display = 10 * display
		to = 'liz.thevenet@gmail.com'
		message = str(datetime.datetime.now()) + ' iteration = 10 EXP' + str(iteration) + ' pi = ' + str( cercle*4)
		Talao_message.message_perso ('calcul Pi', to, message,None) 
	
