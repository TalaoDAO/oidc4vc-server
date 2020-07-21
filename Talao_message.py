import smtplib
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders 

import constante

signature = '\r\n\r\n\r\n\r\n The Talao team.\r\nhttp://talao.co/'


def messageAuth (email_to, random) :


	# debut de la fonction
	fromaddr = "thierry.thevenet1963@gmail.com"
	toaddr = [email_to, ]
#	toaddr = ['thierry.thevenet@talao.io' , 'thevenet_thierry@yahoo.fr']

	# instance of MIMEMultipart 
	msg = MIMEMultipart() 
	msg['From'] = fromaddr 
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] = 'Talao : Authentification par email  ' 

	# string to store the body of the mail 
	body = 'Code a saisir : '+ random 
	msg.attach(MIMEText(body, 'plain')) 
	p = MIMEBase('application', 'octet-stream') 

	# creates SMTP session 
	s = smtplib.SMTP('smtp.gmail.com', 587) 
	s.starttls() 
	s.login(fromaddr, "Suc2cane22") 
	text = msg.as_string() 

	# sending the mail 
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text) 
	except:
		print ('error sending mail')
	s.quit()
	return


def messageLog(name, firstname, username, email,status,eth_a, eth_p, workspace_contract_address, backend_Id, login, SECRET, AES_key,mode)  :


	# debut de la fonction
	fromaddr = "thierry.thevenet1963@gmail.com"
	toaddr = ["thierry.thevenet@talao.io"]
#	toaddr = ['thierry.thevenet@talao.io' , 'thevenet_thierry@yahoo.fr']

	# instance of MIMEMultipart 
	msg = MIMEMultipart() 
	# storing the senders email address 
	msg['From'] = fromaddr 
	# storing the receivers email address 
	msg['To'] = ", ".join(toaddr)
	# storing the subject 
	msg['Subject'] = 'Workspace Log : New Identity '
	# string to store the body of the mail 
	body = 'A new Talao workspace has been deployed\r\nUsername : '+username+'\r\n\r\nEmail : '+email+ '\r\nChain : '+ mode.BLOCKCHAIN + '\r\nAddress : ' + str(eth_a) + '\r\nPrivate Key : '+ str(eth_p)+ '\r\nWorkspace Address : '+str(workspace_contract_address)+'\r\nStatus : '+status+'\r\nBackend Id : '+str(backend_Id) +'\r\nBackend Login : ' + login +'\r\nBackend Password : ' + SECRET +'\r\nAES key : ' + str(AES_key) + mode.DAPP_LINK + str(workspace_contract_address)
	# attach the body with the msg instance 
	msg.attach(MIMEText(body, 'plain')) 
	# open the file to be sent
	path = "./RSA_key/"+mode.BLOCKCHAIN+'/'+eth_a+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	filename = eth_a+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	attachment = open(path, "rb") 
	# instance of MIMEBase and named as p 
	p = MIMEBase('application', 'octet-stream') 
	# To change the payload into encoded form 
	p.set_payload((attachment).read()) 
	# encode into base64 
	encoders.encode_base64(p) 
	p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 
	# attach the instance 'p' to instance 'msg' 
	msg.attach(p) 
	# creates SMTP session 
	s = smtplib.SMTP('smtp.gmail.com', 587) 
	# start TLS for security 
	s.starttls() 
	# Authentication de thierry.thevenet1963@gmail.com
	s.login(fromaddr, "Suc2cane22") 
	# Converts the Multipart msg into a string 
	text = msg.as_string() 
	# sending the mail 
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text) 
		print ('email sent')
	except:
		print ('error sending mail')
	s.quit()
	return





def messageUser(name, firstname, username, email,eth_a, eth_p, workspace_contract_address,mode)  :

	fromaddr = "thierry.thevenet1963@gmail.com"
	toaddr = [email]

	msg = MIMEMultipart() 
	msg['From'] = fromaddr 
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] = 'Your professional Identity by Talao'
	# string to store the body of the mail 
	body = 'A new Professional Identity has been deployed for you. \r\nYour username for login  : ' +username+'\r\n\r\nEmail : '+email+'\r\nBlockchain : '+ mode.BLOCKCHAIN +'\r\nYour Blockchain Address : ' + str(eth_a) +'\r\nYour Private Key : '+ str(eth_p)+'\r\nYour Decentralized IDentitier (DID) : did:talao:'+mode.BLOCKCHAIN+':'+str(workspace_contract_address)[2:]
	footer='\r\n\r\nA RSA key is attached to this email, Keep it with your Private Key secretely.\r\n\r\nYour Identity is now available, you can log  -> '+mode.server + 'login/'
	body= body + footer + signature
	msg.attach(MIMEText(body, 'plain')) 

	# open the file to be sent
	path = "./RSA_key/"+mode.BLOCKCHAIN+'/'+eth_a+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	filename = eth_a+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	attachment = open(path, "rb") 

	# instance of MIMEBase and named as p 
	p = MIMEBase('application', 'octet-stream') 

	# To change the payload into encoded form 
	p.set_payload((attachment).read()) 

	# encode into base64 
	encoders.encode_base64(p) 
	p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 
	# attach the instance 'p' to instance 'msg' 
	msg.attach(p) 
	
	# creates SMTP session 
	s = smtplib.SMTP('smtp.gmail.com', 587) 
	s.starttls() 
	s.login(fromaddr, "Suc2cane22") 
	text = msg.as_string() 

	# sending the mail 
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text) 
		print ('email sent')
	except:
		print ('error sending mail')
	s.quit()
	return


def messageAdmin (subject, messagetext,mode) :

	# debut de la fonction
	fromaddr = "thierry.thevenet1963@gmail.com"
	toaddr = ["thierry.thevenet@talao.io"]
	msg = MIMEMultipart() 
	msg['From'] = fromaddr 
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] = "Admin message :" + subject
	body = messagetext
	msg.attach(MIMEText(body, 'plain')) 
	p = MIMEBase('application', 'octet-stream') 

	# creates SMTP session 
	s = smtplib.SMTP('smtp.gmail.com', 587) 
	s.starttls() 
	s.login(fromaddr, "Suc2cane22") 
	text = msg.as_string() 

	# sending the mail 
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text) 
	except:
		print ('error sending mail')
		return False
	s.quit()
	return True


def message(subject, to, messagetext) :

	fromaddr = "thierry.thevenet1963@gmail.com"
	toaddr = [to]

	msg = MIMEMultipart() 
	msg['From'] = fromaddr 
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject
	body = messagetext + signature
	msg.attach(MIMEText(body, 'plain')) 
	p = MIMEBase('application', 'octet-stream') 

	# creates SMTP session 
	s = smtplib.SMTP('smtp.gmail.com', 587) 
	s.starttls() 
	s.login(fromaddr, "Suc2cane22") 
	text = msg.as_string() 

	# sending the mail 
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text) 
	except:
		print ('error sending mail')
		return False
	s.quit()
	return True



def message_file(to, text, subject, filename, path)  :
	""" @to is list of email, @filename is a list of files """

	# debut de la fonction
	fromaddr = "thierry.thevenet1963@gmail.com"
	toaddr = to
#	toaddr = ['thierry.thevenet@talao.io' , 'thevenet_thierry@yahoo.fr']

	# instance of MIMEMultipart 
	msg = MIMEMultipart() 
	# storing the senders email address 
	msg['From'] = fromaddr 
	# storing the receivers email address 
	msg['To'] = ", ".join(toaddr)
	# storing the subject 
	msg['Subject'] = subject
	# string to store the body of the mail 
	body = text
	# attach the body with the msg instance 
	msg.attach(MIMEText(body, 'plain')) 
	
	for myfile in filename :
		print(myfile)
		# open the file to be sent
		file_with_path = path + myfile
		filename = myfile
		print(file_with_path)
		attachment = open(file_with_path, "rb") 
		# instance of MIMEBase and named as p 
		p = MIMEBase('application', 'octet-stream') 
		# To change the payload into encoded form 
		p.set_payload((attachment).read()) 
		# encode into base64 
		encoders.encode_base64(p) 
		p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 
		# attach the instance 'p' to instance 'msg' 
		msg.attach(p) 
	# creates SMTP session 
	s = smtplib.SMTP('smtp.gmail.com', 587) 
	# start TLS for security 
	s.starttls() 
	# Authentication de thierry.thevenet1963@gmail.com
	s.login(fromaddr, "Suc2cane22") 
	# Converts the Multipart msg into a string 
	text = msg.as_string() 
	# sending the mail 
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text) 
		print ('email sent')
	except:
		print ('error sending mail')
	s.quit()
	return

