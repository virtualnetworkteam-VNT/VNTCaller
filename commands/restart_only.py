
import subprocess,json,datetime,os,urllib.request,base64,time

P1="192.168.10.19"
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GH=open("/home/k/vnt-config-gh.txt").read().strip()
REPO="virtualnetworkteam-VNT/VNTCaller"
TSF=datetime.datetime.now().strftime("%Y%m%d_%H%M")

def pct(ctid,c,t=15):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5","root@"+P1,
        "pct exec "+str(ctid)+" -- bash -c "+json.dumps(c)],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def rx1(c,t=12):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5","root@"+P1,c],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

print(TSF,"MINIMAL RESTART")

# Kill old server
pct(108,"pkill -9 -f python3 2>/dev/null; fuser -k 80/tcp 2>/dev/null; sleep 1; echo KILLED")
time.sleep(3)

# Start simple http.server (most reliable)
pct(108,"cd /var/www/html && nohup python3 -m http.server 80 --bind 0.0.0.0 > /tmp/web.log 2>&1 & echo STARTED")
time.sleep(4)

# Verify from Prox1
r1=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' http://192.168.10.13/ --connect-timeout 6")
r2=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' http://vntworld.com/dashboard.html --connect-timeout 8")
ps=pct(108,"ps aux | grep http.server | grep -v grep | head -2")

print("CT108 web:",r1)
print("vntworld.com:",r2)
print("Process:",ps[:100])

# Save to local file
result={"ts":TSF,"ct108_web":r1,"vntworld":r2,"process":ps[:80]}
open("/home/k/vnt-status.json","w").write(json.dumps(result,indent=2))
try: open(MP,"a").write("\n### Restart ["+TSF+"]\n"+json.dumps(result)+"\n")
except: pass

# Try gh_push
try:
    hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
    try:
        rr=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
        with urllib.request.urlopen(rr,timeout=6) as resp: sha=json.loads(resp.read()).get("sha","")
    except: sha=""
    data={"message":"restart result","content":base64.b64encode(json.dumps({"ts":TSF,"results":result}).encode()).decode()}
    if sha: data["sha"]=sha
    req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
        data=json.dumps(data).encode(),headers=hdr,method="PUT")
    with urllib.request.urlopen(req,timeout=10) as resp:
        ok="content" in json.loads(resp.read())
        print("GH push: OK" if ok else "GH push: FAIL")
except Exception as e:
    print("GH push error:",str(e)[:60])

print("DONE")
