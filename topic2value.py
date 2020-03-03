

topic=input('topic name = ')
claimId =''
for i in range(0, len(topic))  :
	a = str(ord(topic[i]))
	if int(a) < 100 :
		a='0'+a
	claimId=claimId+a
claimIddata=int(claimId)
print(claimIddata)
