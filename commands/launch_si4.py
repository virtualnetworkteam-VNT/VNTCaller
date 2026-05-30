
import urllib.request,json,subprocess,base64,os
GH=open("/home/k/github-relay.py").read().split("GH = '")[1].split("'")[0] if "GH = '" in open("/home/k/github-relay.py").read() else open("/home/k/github-relay.py").read().split('GH = "')[1].split('"')[0]
req=urllib.request.Request(
    "https://api.github.com/repos/virtualnetworkteam-VNT/VNTCaller/contents/assets/vnt_final_master.py",
    headers={"Authorization":"Bearer "+GH})
with urllib.request.urlopen(req,timeout=15) as r:
    code=base64.b64decode(json.loads(r.read())["content"]).decode()
exec(code)
