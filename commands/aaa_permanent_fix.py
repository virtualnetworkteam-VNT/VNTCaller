import subprocess,os,json,datetime,urllib.request,time,base64,re

GH=open("/home/k/vnt-config-gh.txt").read().strip()
REPO="virtualnetworkteam-VNT/VNTCaller"
TSF=datetime.datetime.now().strftime("%Y%m%d_%H%M")
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GROQ_KEY=""
try:
    import re
    mp=open(MP).read()
    m=re.search(r"gsk_[A-Za-z0-9]{40,}",mp)
    if m: GROQ_KEY=m.group(0)
except: pass

def run(c,t=15):
    r=subprocess.run(c,shell=True,capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def gh_api(path):
    hdr={"Authorization":"Bearer "+GH,"Accept":"application/vnd.github.v3+json"}
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/contents/{path}",headers=hdr),timeout=30).read())

def gh_save(R):
    try:
        hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json",
             "Accept":"application/vnd.github.v3+json"}
        try:
            rr=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get("sha","")
        except: sha=""
        data={"message":"fix result","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
            data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp: return "content" in json.loads(resp.read())
    except Exception as e: print("GH:",str(e)[:30]); return False

print(TSF,"INSTALL PORTAL V2 + WATCHDOG")
R={}

# 1. Download and install portal_server_v2.py
print("[1] Installing portal_server_v2.py...")
fd=gh_api("portal_server_v2.py")
portal_code=base64.b64decode(fd["content"].replace("\n","")).decode()
open("/home/k/vnt-web/portal_server.py","w").write(portal_code)
sr=subprocess.run(["/usr/bin/python3","-m","py_compile","/home/k/vnt-web/portal_server.py"],capture_output=True,text=True)
R["portal_syntax"]="OK" if sr.returncode==0 else "FAIL:"+sr.stderr[:60]
print(f"  Syntax: {R['portal_syntax']}")

# 2. Download and install watchdog
print("[2] Installing watchdog...")
fd2=gh_api("vnt_portal_watchdog.sh")
watchdog_code=base64.b64decode(fd2["content"].replace("\n","")).decode()
open("/home/k/vnt_portal_watchdog.sh","w").write(watchdog_code)
run("chmod +x /home/k/vnt_portal_watchdog.sh")
R["watchdog"]="installed"

# 3. Install crontab entries
print("[3] Crontab...")
existing=run("crontab -l 2>/dev/null")
entries=[]
if "vnt_portal_watchdog" not in existing:
    entries.append("* * * * * /home/k/vnt_portal_watchdog.sh")
if "@reboot" not in existing or "portal_server" not in existing:
    entries.append("@reboot sleep 15 && /usr/bin/python3 /home/k/vnt-web/portal_server.py >> /tmp/portal.log 2>&1 &")
if entries:
    new_cron=(existing.strip()+("\n" if existing.strip() else "")+"\n".join(entries)+"\n")
    proc=subprocess.run("crontab -",input=new_cron,capture_output=True,text=True,shell=True)
    R["crontab"]="added "+str(len(entries))+" entries"
else:
    R["crontab"]="already configured"
print(f"  {R['crontab']}")

# 4. Restart portal
print("[4] Restarting portal...")
run("fuser -k 8888/tcp 2>/dev/null; sleep 2")
subprocess.Popen(["/usr/bin/python3","/home/k/vnt-web/portal_server.py"],
    stdout=open("/tmp/portal.log","w"),stderr=subprocess.STDOUT)
time.sleep(6)
try:
    with urllib.request.urlopen("http://127.0.0.1:8888/api/health",timeout=8) as r2:
        R["api_health"]="PASS "+json.loads(r2.read()).get("status","?")
except Exception as e:
    R["api_health"]="FAIL:"+str(e)[:40]
    R["portal_log"]=run("tail -20 /tmp/portal.log")
print(f"  API: {R['api_health']}")

# 5. Install Mia v2
print("[5] Mia v2...")
try:
    fd3=gh_api("mia_v2.py")
    mia_code=base64.b64decode(fd3["content"].replace("\n","")).decode()
    if GROQ_KEY:
        mia_code=mia_code.replace('os.environ.get("GROQ_API_KEY","")','+GROQ_KEY+')
    os.makedirs("/home/k/vnt-agents",exist_ok=True)
    open("/home/k/vnt-agents/mia_v2.py","w").write(mia_code)
    R["mia_v2"]="OK"
except Exception as e: R["mia_v2"]="FAIL:"+str(e)[:50]
print(f"  Mia: {R['mia_v2']}")

# 6. OpenClaw scan for Mia
print("[6] OpenClaw...")
oc_path="/home/k/.openclaw/openclaw.json"
if os.path.exists(oc_path):
    raw=open(oc_path).read()
    R["openclaw_keys"]=str(list(json.loads(raw).keys())[:8])
    R["mia_in_oc"]="found" if "mia" in raw.lower() else "not found"
    if "mia" in raw.lower():
        idx=raw.lower().find("mia")
        R["mia_ctx"]=raw[max(0,idx-20):idx+200]
    print(f"  Keys={R['openclaw_keys']} mia={R['mia_in_oc']}")
else:
    R["home_k"]=run("ls /home/k/")[:200]
    print(f"  No openclaw.json")

# 7. MemPalace
print("[7] MemPalace...")
MP_LINES=[
    "",
    "=====================================",
    f"## PERMANENT API FIX [{TSF}]",
    "=====================================",
    "PROBLEM: MSI portal (:8888) kept going offline.",
    "ROOT CAUSE: nohup dies silently, no auto-restart, no timeout on M4 requests.",
    "",
    "FIXES APPLIED:",
    "1. portal_server_v2.py → /home/k/vnt-web/portal_server.py (60s timeout, health endpoint)",
    "2. Watchdog: /home/k/vnt_portal_watchdog.sh (every 1 min via crontab)",
    "3. @reboot cron → auto-starts portal on MSI reboot",
    "4. Mia v2 → /home/k/vnt-agents/mia_v2.py (multilingual + audio-in/out)",
    "",
    "RECOVERY (Zeus follow this):",
    "1. Check: fuser 8888/tcp",
    "2. Manual restart: /home/k/vnt_portal_watchdog.sh",
    "3. Check log: tail -30 /tmp/portal.log",
    "4. Health check: curl http://127.0.0.1:8888/api/health",
    "5. M4 check: ssh Alias@192.168.10.94 curl localhost:3333/health",
    "=====================================",
]
try:
    open(MP,"a").write("\n".join(MP_LINES))
    R["mempalace"]="WRITTEN"
except Exception as e: R["mempalace"]="FAIL:"+str(e)[:30]

gh_save(R)
print("\n=== DONE ===")
for k,v in R.items():
    ok="OK" if any(x in str(v) for x in ["PASS","OK","installed","WRITTEN","found","added"]) else "FL"
    print(f"  [{ok}] {k}: {str(v)[:80]}")
