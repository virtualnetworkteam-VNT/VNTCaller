
import urllib.request,json,base64,os,subprocess
relay=open("/home/k/github-relay.py").read()
if "GH = '" in relay: GH=relay.split("GH = '")[1].split("'")[0]
else: GH=relay.split('GH = "')[1].split('"')[0]
for asset in ["vnt_final_master.py","vnt_agent_app.py"]:
    req=urllib.request.Request(
        "https://api.github.com/repos/virtualnetworkteam-VNT/VNTCaller/contents/assets/"+asset,
        headers={"Authorization":"Bearer "+GH})
    with urllib.request.urlopen(req,timeout=15) as r:
        code=base64.b64decode(json.loads(r.read())["content"]).decode()
    print("Running: "+asset)
    exec(code)
    print("Done: "+asset)
