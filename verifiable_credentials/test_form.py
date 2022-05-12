import urllib3


import urllib
import urllib2

name = "emai"

data = { "name" : name}

encoded_data = urllib.urlencode(data)

content = urllib2.urlopen("https://talao.co/emailpass?action=/emailpass", encoded_data)

print(content.readlines())
