from xml.dom.xmlbuilder import _DOMInputSourceCharacterStreamType
import requests

url = "https://hooks.slack.com/services/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"

data = {"payload" : "test"}
r = requests.post(url, data=data)
print(r.status_code)
