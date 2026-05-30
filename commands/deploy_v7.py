import subprocess,datetime,json,urllib.request,time,os,re

P1   = "192.168.10.19"
WEB  = "/var/www/html"
MSI  = "/home/k/vnt-web"
CFG  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
MP   = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GH   = open("/home/k/vnt-config-gh.txt").read().strip()
REPO = "virtualnetworkteam-VNT/VNTCaller"
TSF  = datetime.datetime.now().strftime("%Y%m%d_%H%M")
DL_URL = "https://raw.githubusercontent.com/virtualnetworkteam-VNT/VNTCaller/main/dashboard_v7.html"

def rx1(c,t=20):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=6","root@"+P1,c],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def scp_p1(l,r,t=20):
    return subprocess.run(["scp","-o","StrictHostKeyChecking=no",l,"root@"+P1+":"+r],
        capture_output=True,timeout=t).returncode==0

def gh_save(R):
    try:
        hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
        try:
            rr=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get("sha","")
        except: sha=""
        import base64
        data={"message":"v7 result","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
            data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp: return "content" in json.loads(resp.read())
    except Exception as e: print("GH:",str(e)[:30]); return False

print(TSF,"DEPLOY v7 FROM GH")
R={}

# 1. Download clean HTML
print("[1] Downloading v7 HTML...")
with urllib.request.urlopen(DL_URL,timeout=30) as r: raw=r.read().decode()
print(f"  Downloaded: {len(raw)} chars")

# 2. Read Groq key from MSI config
print("[2] Reading config...")
groq_key = ""
try:
    cfg=json.load(open(CFG))
    groq_key=cfg.get("groq_key","")
    if not groq_key:
        # Try from MemPalace
        mp=open(MP).read()
        m=re.search(r"gsk_[A-Za-z0-9]+",mp)
        if m: groq_key=m.group(0)
except: pass
print(f"  Groq key: {'found' if groq_key else 'not found'}")

# 3. Patch secrets back into HTML
if groq_key:
    raw=raw.replace("GROQ_KEY_FROM_CONFIG", groq_key)
    raw=raw.replace("// loaded from config", "// loaded")

# Fix passwords in USERS dict — read from known locations
# Use the actual VNT credentials
raw=raw.replace(
    "'ryan':       {pass:'***',",
    "'ryan':       {pass:'116899',"
)
raw=raw.replace(
    "'khawaja':    {pass:'***',",
    "'khawaja':    {pass:'App159earance.VnT',"
)
raw=raw.replace(
    "'administrator':{pass:'***',",
    "'administrator':{pass:'0568116899',"
)
raw=raw.replace(
    "'kraheelw':   {pass:'***',",
    "'kraheelw':   {pass:'116899',"
)
raw=raw.replace(
    "'kraheelw@vntworld.com':{pass:'***',",
    "'kraheelw@vntworld.com':{pass:'116899',"
)

# 4. Write and deploy
html=raw.encode()
print(f"[3] HTML ready: {len(html)} bytes")
open("/tmp/dash_v7.html","wb").write(html)
open(MSI+"/dashboard.html","wb").write(html)
open(MSI+"/dashboard_v7.html","wb").write(html)

ok=scp_p1("/tmp/dash_v7.html","/tmp/dash_v7.html")
print("[4] SCP to Prox1:",ok)

push=rx1("pct push 108 /tmp/dash_v7.html "+WEB+"/dashboard.html",t=20)
print("[5] pct push:",push or "OK")

sz=rx1("pct exec 108 -- bash -c 'stat -c %s "+WEB+"/dashboard.html'",t=8)
print("[6] CT108 size:",sz,"b")
R["dashboard"]=f"PASS {sz}b" if int(sz or 0)>90000 else f"FAIL {sz}b"

# Check web server
ps=rx1("pct exec 108 -- ps aux 2>/dev/null | grep http.server | grep -v grep | wc -l",t=8)
if ps.strip()=="0":
    subprocess.Popen(["ssh","-o","StrictHostKeyChecking=no","root@"+P1,
        "pct exec 108 -- bash -c 'cd /var/www/html && nohup python3 -m http.server 80 --bind 0.0.0.0 >> /tmp/web.log 2>&1 &'"],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(4)

ct108=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' http://192.168.10.13/ --connect-timeout 5")
vnt=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' https://vntworld.com/dashboard.html --connect-timeout 8")
print(f"[7] CT108:{ct108}  vnt:{vnt}")
R["ct108"]=ct108; R["vntworld"]=vnt

try: open(MP,"a").write("\n### v7 ["+TSF+"]\nLayout+Auth+OrgChart+API fixes\n")
except: pass

gh_save(R)
for k,v in R.items(): print(f"  {'OK' if '200' in str(v) or 'PASS' in str(v) else 'FL'} {k}: {str(v)[:60]}")
print("DONE")
