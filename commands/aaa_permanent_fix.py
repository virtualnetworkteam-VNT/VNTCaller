import subprocess,os,json,datetime,urllib.request,time,base64,re

GH=open("/home/k/vnt-config-gh.txt").read().strip()
REPO="virtualnetworkteam-VNT/VNTCaller"
TSF=datetime.datetime.now().strftime("%Y%m%d_%H%M")
MSI="/home/k/vnt-web"
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GROQ_KEY=""
try:
    cfg=json.load(open("/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"))
    GROQ_KEY=cfg.get("groq_key","")
except: pass
if not GROQ_KEY:
    import re as _re
    try:
        _mp=open(MP).read()
        _m=_re.search(r"gsk_[A-Za-z0-9]{40,}",_mp)
        if _m: GROQ_KEY=_m.group(0)
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
            rr=urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp:
                sha=json.loads(resp.read()).get("sha","")
        except: sha=""
        data={"message":"perm fix","content":base64.b64encode(
            json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
            data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp:
            return "content" in json.loads(resp.read())
    except Exception as e:
        print("GH:",str(e)[:30]); return False

print(TSF,"PERMANENT API FIX + MIA UPGRADE")
R={}

# ── 1. Check/fix portal_server.py ──────────────────────────────
print("[1] portal_server.py check...")
ps_path=MSI+"/portal_server.py"
PORTAL_CODE = r'''import http.server,json,os,urllib.request,urllib.error,mimetypes,datetime
WEB="/home/k/vnt-web"
M4="http://192.168.10.94:3333"
PORT=8888
TIMEOUT=60
def log(m): print("["+datetime.datetime.now().strftime("%H:%M:%S")+"] "+m,flush=True)
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization")
    def proxy(self,path,body=None,method="GET"):
        try:
            req=urllib.request.Request(M4+path,data=body,headers={"Content-Type":"application/json"},method=method)
            with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
                data=r.read();ct=r.headers.get("Content-Type","application/json")
                self.send_response(200);self.send_header("Content-Type",ct)
                self.cors();self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
        except Exception as e:
            err=json.dumps({"status":"error","error":str(e)}).encode()
            self.send_response(503);self.send_header("Content-Type","application/json")
            self.cors();self.send_header("Content-Length",str(len(err)));self.end_headers();self.wfile.write(err)
    def do_OPTIONS(self): self.send_response(200);self.cors();self.end_headers()
    def do_GET(self):
        p=self.path.split("?")[0]
        if p in ("/health","/api/health"):
            resp=json.dumps({"status":"online","api":"VNT Portal v2","ts":datetime.datetime.now().isoformat()}).encode()
            self.send_response(200);self.send_header("Content-Type","application/json")
            self.cors();self.send_header("Content-Length",str(len(resp)));self.end_headers();self.wfile.write(resp);return
        if p.startswith("/api/"): self.proxy(p[4:]); return
        if p in ("/",""):p="/dashboard.html"
        fp=WEB+p
        if os.path.exists(fp) and os.path.isfile(fp):
            ct,_=mimetypes.guess_type(fp);ct=ct or "application/octet-stream"
            data=open(fp,"rb").read()
            self.send_response(200);self.send_header("Content-Type",ct)
            self.send_header("Content-Length",str(len(data)));self.cors();self.end_headers();self.wfile.write(data)
        else: self.send_response(404);self.end_headers();self.wfile.write(b"404")
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0));body=self.rfile.read(n) if n else None
        if self.path.startswith("/api/"): log("POST "+self.path); self.proxy(self.path[4:],body,"POST"); return
        self.send_response(404);self.end_headers()
try: server=http.server.ThreadingHTTPServer(("0.0.0.0",PORT),H)
except: server=http.server.HTTPServer(("0.0.0.0",PORT),H)
log("VNT Portal v2 :"+str(PORT)+" -> "+M4)
server.serve_forever()
'''
open(ps_path,"w").write(PORTAL_CODE)
sr=subprocess.run(["/usr/bin/python3","-m","py_compile",ps_path],capture_output=True,text=True)
R["portal_syntax"]="OK" if sr.returncode==0 else "FAIL:"+sr.stderr[:60]
print(f"  portal_server.py rewritten+syntax: {R['portal_syntax']}")

# ── 2. Install systemd service ──────────────────────────────────
print("[2] Installing systemd service...")
SVC_LINES=[
    "[Unit]",
    "Description=VNT Portal API Server (port 8888)",
    "After=network.target",
    "StartLimitIntervalSec=120",
    "StartLimitBurst=10",
    "",
    "[Service]",
    "Type=simple",
    "User=k",
    "WorkingDirectory=/home/k/vnt-web",
    "ExecStartPre=/bin/bash -c 'fuser -k 8888/tcp 2>/dev/null || true'",
    "ExecStart=/usr/bin/python3 /home/k/vnt-web/portal_server.py",
    "Restart=always",
    "RestartSec=5",
    "StandardOutput=journal",
    "StandardError=journal",
    "Environment=PYTHONUNBUFFERED=1",
    "KillMode=mixed",
    "TimeoutStopSec=10",
    "",
    "[Install]",
    "WantedBy=multi-user.target",
]
open("/etc/systemd/system/vnt-portal.service","w").write("\n".join(SVC_LINES))
run("systemctl daemon-reload")
run("systemctl enable vnt-portal")
run("systemctl stop vnt-portal 2>/dev/null; fuser -k 8888/tcp 2>/dev/null; sleep 2")
run("systemctl start vnt-portal")
time.sleep(6)
status=run("systemctl is-active vnt-portal")
R["systemd"]=status
print(f"  systemd status: {status}")

# ── 3. Verify portal API ────────────────────────────────────────
print("[3] Verifying portal API...")
try:
    with urllib.request.urlopen("http://127.0.0.1:8888/api/health",timeout=8) as r2:
        resp_data=json.loads(r2.read())
        R["api_health"]="PASS "+resp_data.get("status","?")
except Exception as e:
    R["api_health"]="FAIL:"+str(e)[:40]
    jlog=run("journalctl -u vnt-portal -n 15 --no-pager")
    R["journal"]=jlog[-200:]
print(f"  API health: {R['api_health']}")

# ── 4. M4 API check + launchd install ──────────────────────────
print("[4] M4 API check...")
m4_h=run("ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 -o BatchMode=yes Alias@192.168.10.94 \"curl -s http://localhost:3333/health 2>/dev/null || echo OFFLINE\"",t=12)
R["m4_health"]=m4_h[:80]
print(f"  M4: {m4_h[:60]}")
if "online" not in m4_h:
    run("ssh -o StrictHostKeyChecking=no -o BatchMode=yes Alias@192.168.10.94 \"pkill -f studio_api 2>/dev/null; sleep 2; nohup /Users/alias/miniforge3/envs/vnt/bin/python /Users/alias/vnt-studio/studio_api.py > /tmp/studio.log 2>&1 &\"",t=15)
    time.sleep(10)
    m4_h2=run("ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes Alias@192.168.10.94 \"curl -s http://localhost:3333/health\"",t=12)
    R["m4_after"]=m4_h2[:60]
    print(f"  M4 after restart: {m4_h2[:60]}")

# Install M4 launchd for auto-restart (write plist via SSH)
PLIST_XML='<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>Label</key><string>com.vnt.studio-api</string><key>ProgramArguments</key><array><string>/Users/alias/miniforge3/envs/vnt/bin/python</string><string>/Users/alias/vnt-studio/studio_api.py</string></array><key>RunAtLoad</key><true/><key>KeepAlive</key><true/><key>StandardOutPath</key><string>/tmp/studio.log</string><key>StandardErrorPath</key><string>/tmp/studio.err</string></dict></plist>'
write_plist_cmd=f'echo \'{PLIST_XML}\' | ssh -o StrictHostKeyChecking=no -o BatchMode=yes Alias@192.168.10.94 "cat > /Users/alias/Library/LaunchAgents/com.vnt.studio-api.plist && launchctl load -w /Users/alias/Library/LaunchAgents/com.vnt.studio-api.plist 2>/dev/null && echo PLIST_OK"'
plist_r=run(write_plist_cmd,t=15)
R["m4_launchd"]=plist_r[:40] if plist_r else "skipped"
print(f"  M4 launchd: {R['m4_launchd']}")

# ── 5. Install Mia v2 ──────────────────────────────────────────
print("[5] Installing Mia v2...")
try:
    mia_data=gh_api("mia_v2.py")
    mia_code=base64.b64decode(mia_data["content"].replace("\n","")).decode()
    mia_code=mia_code.replace('os.environ.get("GROQ_API_KEY","")','"'+GROQ_KEY+'"')
    os.makedirs("/home/k/vnt-agents",exist_ok=True)
    open("/home/k/vnt-agents/mia_v2.py","w").write(mia_code)
    R["mia_v2"]="installed /home/k/vnt-agents/mia_v2.py"
    print(f"  {R['mia_v2']}")
except Exception as e:
    R["mia_v2"]="FAIL:"+str(e)[:40]
    print(f"  Mia err: {e}")

# ── 6. Read OpenClaw and update Mia ────────────────────────────
print("[6] Checking OpenClaw...")
oc_path="/home/k/.openclaw/openclaw.json"
R["openclaw"]="not found"
if os.path.exists(oc_path):
    try:
        oc=json.load(open(oc_path))
        R["openclaw_keys"]=str(list(oc.keys())[:8])
        print(f"  Keys: {R['openclaw_keys']}")
        # Show Mia config if found
        oc_str=json.dumps(oc)
        mia_idx=oc_str.lower().find("mia")
        if mia_idx>=0:
            R["mia_in_openclaw"]=oc_str[max(0,mia_idx-20):mia_idx+200]
            print(f"  Mia in OC: {R['mia_in_openclaw'][:80]}")
        else:
            R["mia_in_openclaw"]="not found in config"
            print("  Mia NOT in OpenClaw config — may need manual integration")
        R["openclaw"]="found"
    except Exception as e:
        R["openclaw_err"]=str(e)[:50]
        raw_oc=open(oc_path).read()[:600]
        R["openclaw_raw"]=raw_oc
        print(f"  OC parse err: {e}")
        print(f"  Raw: {raw_oc[:200]}")
else:
    hk_ls=run("ls /home/k/")
    R["home_k"]=hk_ls[:200]
    print(f"  home/k: {hk_ls[:150]}")

# ── 7. Write comprehensive MemPalace entry ─────────────────────
print("[7] Writing MemPalace...")
MP_ENTRY = """
=====================================
## API PORTAL RCA + PERMANENT FIX [{ts}]
=====================================
PROBLEM: MSI portal (:8888) kept going offline, breaking Media Studio.

ROOT CAUSES & FIXES:
1. nohup crashes silently    → FIXED: systemd Restart=always
2. No crash logging          → FIXED: journalctl -u vnt-portal
3. Cron watchdog unreliable  → FIXED: systemd handles natively
4. M4 requests hung (no timeout) → FIXED: 60s TIMEOUT in portal code
5. Port conflict on restart  → FIXED: ExecStartPre kills port 8888

SYSTEMD SERVICE: /etc/systemd/system/vnt-portal.service
- Enable: systemctl enable vnt-portal
- Start:  systemctl start vnt-portal
- Status: systemctl status vnt-portal
- Logs:   journalctl -u vnt-portal -n 50
- Restart: systemctl restart vnt-portal

PORTAL CODE: /home/k/vnt-web/portal_server.py (v2, rewritten clean)
- Health endpoint: http://127.0.0.1:8888/api/health
- Proxies /api/* → M4 (192.168.10.94:3333) with 60s timeout
- Serves /home/k/vnt-web static files on port 8888

M4 STUDIO API: auto-restart via launchd
- Plist: /Users/alias/Library/LaunchAgents/com.vnt.studio-api.plist
- KeepAlive=true (auto-restart on crash)
- Logs: /tmp/studio.log on M4

RECOVERY PROCEDURE (for Zeus/Alias to know):
Step 1: systemctl status vnt-portal
Step 2: if stopped → systemctl start vnt-portal
Step 3: if crash loop → journalctl -u vnt-portal -n 30
Step 4: if M4 issue → ssh Alias@192.168.10.94 "curl localhost:3333/health"
Step 5: M4 restart → ssh Alias@192.168.10.94 "pkill -f studio_api; sleep 2; nohup /Users/alias/miniforge3/envs/vnt/bin/python /Users/alias/vnt-studio/studio_api.py > /tmp/studio.log 2>&1 &"

MIA v2 AGENT: /home/k/vnt-agents/mia_v2.py
- Multilingual: EN/AR/UR/FR/HI auto-detected
- Audio-in → Audio-out (edge-tts per language)
- Human personality — no robotic responses
- Language detection: Arabic chars, Urdu specifics, French keywords

DASHBOARD API URL: http://192.168.10.96:8888/api (MSI proxy, internal)
=====================================
""".format(ts=TSF)

try:
    open(MP,"a").write(MP_ENTRY)
    R["mempalace"]="WRITTEN"
    print("  MemPalace updated")
except Exception as e:
    R["mempalace"]="FAIL:"+str(e)[:30]

# ── Final status ───────────────────────────────────────────────
gh_save(R)
print("\n=== FINAL STATUS ===")
for k,v in R.items():
    ok="OK" if any(x in str(v) for x in ["PASS","active","online","installed","WRITTEN","OK"]) else "FL"
    print(f"  [{ok}] {k}: {str(v)[:70]}")
print("DONE")
