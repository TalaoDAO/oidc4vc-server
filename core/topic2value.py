

topicname=input('topic name = ')
topicvaluestr =''
for i in range(0, len(topicname))  :
	a = str(ord(topicname[i]))
	if int(a) < 100 :
		a='0'+a
	topicvaluestr=topicvaluestr+a
topicvalue=int(topicvaluestr)
print(topicvalue)
