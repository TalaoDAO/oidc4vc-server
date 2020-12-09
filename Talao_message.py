import smtplib
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import codecs

import constante

signature = '\r\n\r\n\r\n\r\nThe Talao team.\r\nhttp://talao.io/'

""" Envoi du code secret """
def messageAuth (email_to, random, mode) :

	password = mode.smtp_password

	# debut de la fonction
	fromaddr = "relay@talao.io"
	toaddr = [email_to, ]
#	toaddr = ['thierry.thevenet@talao.io' , 'thevenet_thierry@yahoo.fr']

	# instance of MIMEMultipart
	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] = 'Talao : Email authentification  '

	# string to store the body of the mail
	body = 'Your verification code is : '+ random
	msg.attach(MIMEText(body, 'plain'))
	#p = MIMEBase('application', 'octet-stream')

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('Error : sending mail')
	s.quit()
	return True

""" email envoyé a la creation d'un workspace  """
def messageLog(name, firstname, username, email,status,eth_a, eth_p, workspace_contract_address, backend_Id, login, SECRET, AES_key,mode)  :

	password = mode.smtp_password

	# debut de la fonction
	fromaddr = 'relay@talao.io'
	toaddr = [mode.admin, 'alexandre.leclerc@gadz.org', 'victor.baconnet@talao.io']
#	toaddr = ['thierry.thevenet@talao.io' , 'thevenet_thierry@yahoo.fr']

	# instance of MIMEMultipart
	msg = MIMEMultipart()
	# storing the senders email address
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	# storing the receivers email address
	msg['To'] = ", ".join(toaddr)
	# storing the subject
	msg['Subject'] = 'Workspace Log : New Identity '
	# string to store the body of the mail
	body = "".join(['A new Talao workspace has been deployed\r\nUsername : ',
					username,
					'\r\n\r\nEmail : ',
					email,
					'\r\nChain : ',
					mode.BLOCKCHAIN,
					'\r\nAddress : ',
					str(eth_a),
					'\r\nWorkspace Address : ',
					str(workspace_contract_address),
					'\r\nStatus : ',
					status,
					])
	# attach the body with the msg instance
	msg.attach(MIMEText(body, 'plain'))
	"""
	# open the file to be sent
	path = "./RSA_key/"+mode.BLOCKCHAIN+'/'+eth_a+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
	filename = eth_a+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1.txt"
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
	"""
	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	# start TLS for security
	s.starttls()
	# Authentication
	s.login(fromaddr, password)
	# Converts the Multipart msg into a string
	text = msg.as_string()
	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
		print ('Success : email sent')
	except:
		print ('Error : sending mail')
	s.quit()
	return True


def messageUser(name, firstname, username, email,eth_a, eth_p, workspace_contract_address,mode)  :

	password = mode.smtp_password
	fromaddr = "relay@talao.io"
	toaddr = [email]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] = 'Your professional Identity by Talao'
	# string to store the body of the mail

	html = str(codecs.open("templates/emails/register.html", 'r', 'utf-8').read()).format(username = username)
	msg.attach(MIMEText(html, 'html', 'utf-8'))
	#p = MIMEBase('application', 'octet-stream')

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
		print ('Success : email sent')
	except:
		print ('Error : sending mail')
	s.quit()
	return True

def message(subject, to, messagetext, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject
	body = messagetext + signature
	msg.attach(MIMEText(body, 'plain'))
	#p = MIMEBase('application', 'octet-stream')

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('Error : sending mail')
		return False
	s.quit()
	return True

def certificate_issued(subject, to, username, link, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/certificate_issued.html", 'r', 'utf-8').read()).format(username = username,
                                                      link = link)
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('Error : sending mail')
		return False
	s.quit()
	return True


def certificate_issued_issuer(subject, to, name, link, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/certificate_issued_issuer.html", 'r', 'utf-8').read()).format(name = name,
                                                      link = link)
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('Error : sending mail')
		return False
	s.quit()
	return True

def request_partnership(subject, to, name, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/request_partnership.html", 'r', 'utf-8').read()).format(name = name)
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('Error : sending mail')
		return False
	s.quit()
	return True

def request_partnership_rejected(subject, to, name, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/request_partnership_rejected.html", 'r', 'utf-8').read()).format(name = name, text=text)
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('Error : sending mail')
		return False
	s.quit()
	return True

def forgot_password(subject, to, link, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/forgot_password.html", 'r', 'utf-8').read()).format(link=link)
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('Error : sending mail')
		return False
	s.quit()
	return True

def added_referent(subject, to, name, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/added_referent.html", 'r', 'utf-8').read()).format(name=name)
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('Error : sending mail')
		return False
	s.quit()
	return True

def request_POI_sent(subject, to, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/request_POI_sent.html", 'r', 'utf-8').read())
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('Error : sending mail')
		return False
	s.quit()
	return True

def POI_isssued(subject, to, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/POI_issued.html", 'r', 'utf-8').read())
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('Error : sending mail')
		return False
	s.quit()
	return True


def invite(subject, to, name, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/invite_to_join.html", 'r', 'utf-8').read()).format(name = name)
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('error sending mail')
		return False
	s.quit()
	return True

def joboffer(subject, to, name, job, link, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/job_offer.html", 'r', 'utf-8').read()).format(name = name, job = job, link = link)
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('error sending mail')
		return False
	s.quit()
	return True

def memo(subject, to, name, memo, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/memo.html", 'r', 'utf-8').read()).format(name = name, memo = memo)
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('error sending mail')
		return False
	s.quit()
	return True

def request_certificate(subject, to, name, link, mode) :

	password = mode.smtp_password

	fromaddr = "relay@talao.io"
	toaddr = [to]

	msg = MIMEMultipart()
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
	msg['To'] = ", ".join(toaddr)
	msg['Subject'] =  subject

	html = str(codecs.open("templates/emails/request_certificate.html", 'r', 'utf-8').read()).format(name = name, link = link)
	msg.attach(MIMEText(html, 'html', 'utf-8'))

	# creates SMTP session
	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(fromaddr, password)
	text = msg.as_string()

	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
	except:
		print ('error sending mail')
		return False
	s.quit()
	return True

def message_file(to, text, subject, filename, path, mode)  :
	""" @to is list of email, @filename is a list of files """

	password = mode.smtp_password

	# debut de la fonction
	fromaddr = "relay@talao.io"
	toaddr = to
#	toaddr = ['thierry.thevenet@talao.io' , 'thevenet_thierry@yahoo.fr']

	# instance of MIMEMultipart
	msg = MIMEMultipart()
	# storing the senders email address
	msg['From'] = formataddr((str(Header('Talao', 'utf-8')), fromaddr))
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
	# Authentication
	s.login(fromaddr, password)
	# Converts the Multipart msg into a string
	text = msg.as_string()
	# sending the mail
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text)
		print ('Success : email sent')
	except:
		print ('Error : sending mail')
	s.quit()
	return True
