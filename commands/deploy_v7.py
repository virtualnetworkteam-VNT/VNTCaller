import subprocess,datetime,json,urllib.request,time,os,re,base64

P1   = "192.168.10.19"
WEB  = "/var/www/html"
MSI  = "/home/k/vnt-web"
CFG  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
MP   = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GH   = open("/home/k/vnt-config-gh.txt").read().strip()
REPO = "virtualnetworkteam-VNT/VNTCaller"
TSF  = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx1(c,t=20):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=6","root@"+P1,c],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def scp_p1(l,r,t=20):
    return subprocess.run(["scp","-o","StrictHostKeyChecking=no",l,"root@"+P1+":"+r],
        capture_output=True,timeout=t).returncode==0

def gh_get(path):
    hdr={"Authorization":"Bearer "+GH,"Accept":"application/vnd.github.v3+json"}
    req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",headers=hdr)
    with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read())

def gh_save(R):
    try:
        hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
        try:
            rr=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get("sha","")
        except: sha=""
        data={"message":"v7 result","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
            data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp: return "content" in json.loads(resp.read())
    except Exception as e: print("GH:",str(e)[:30]); return False

print(TSF,"DEPLOY v7 FROM GH API")
R={}

# 1. Download clean HTML via GitHub API (handles private repo auth)
print("[1] Fetching v7 HTML via GH API...")
file_data=gh_get("dashboard_v7.html")
raw=base64.b64decode(file_data["content"].replace("\n","")).decode()
print(f"  Downloaded: {len(raw)} chars")

# 2. Read Groq key from MSI config/MemPalace
print("[2] Reading Groq key...")
groq_key = ""
try:
    cfg=json.load(open(CFG))
    groq_key=cfg.get("groq_key","")
except: pass
if not groq_key:
    try:
        mp=open(MP).read()
        m=re.search(r"gsk_[A-Za-z0-9]{40,}",mp)
        if m: groq_key=m.group(0)
    except: pass
print(f"  Groq key: {'found ('+groq_key[:8]+')' if groq_key else 'not found'}")

# 3. Patch
if groq_key:
    raw=raw.replace("GROQ_KEY_FROM_CONFIG",groq_key)

# Patch passwords
for old,new in [
    ("'ryan':       {pass:'***',","'ryan':       {pass:'116899',"),
    ("'khawaja':    {pass:'***',","'khawaja':    {pass:'App159earance.VnT',"),
    ("'administrator':{pass:'***',","'administrator':{pass:'0568116899',"),
    ("'kraheelw':   {pass:'***',","'kraheelw':   {pass:'116899',"),
    ("'kraheelw@vntworld.com':{pass:'***',","'kraheelw@vntworld.com':{pass:'116899',"),
]:
    raw=raw.replace(old,new)

html=raw.encode()
print(f"[3] HTML ready: {len(html)}b")

# 4. Write + deploy
open("/tmp/dash_v7.html","wb").write(html)
open(MSI+"/dashboard.html","wb").write(html)
open(MSI+"/dashboard_v7.html","wb").write(html)

ok=scp_p1("/tmp/dash_v7.html","/tmp/dash_v7.html")
print("[4] SCP:",ok)

push=rx1("pct push 108 /tmp/dash_v7.html "+WEB+"/dashboard.html",t=20)
print("[5] pct push:",push or "OK")

sz=rx1("pct exec 108 -- bash -c 'stat -c %s "+WEB+"/dashboard.html'",t=8)
print("[6] Size:",sz,"b")
R["dashboard"]=f"PASS {sz}b" if int(sz or 0)>90000 else f"FAIL {sz}b"

# Web server check
ps=rx1("pct exec 108 -- ps aux 2>/dev/null | grep http.server | grep -v grep | wc -l",t=8)
if ps.strip()=="0":
    subprocess.Popen(["ssh","-o","StrictHostKeyChecking=no","root@"+P1,
        "pct exec 108 -- bash -c 'cd /var/www/html && nohup python3 -m http.server 80 --bind 0.0.0.0 >> /tmp/web.log 2>&1 &'"],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(4)
    print("Web server restarted")

ct108=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' http://192.168.10.13/ --connect-timeout 5")
vnt=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' https://vntworld.com/dashboard.html --connect-timeout 8")
print(f"[7] CT108:{ct108}  vnt:{vnt}")
R["ct108"]=ct108; R["vntworld"]=vnt

try: open(MP,"a").write("\n### v7 ["+TSF+"]\nLayout+Auth+OrgChart fixes deployed\n")
except: pass

gh_save(R)
for k,v in R.items(): print(f"  {'OK' if '200' in str(v) or 'PASS' in str(v) else 'FL'} {k}: {str(v)[:60]}")
print("DONE")
