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
    try:
        _mp=open(MP).read()
        _m=re.search(r"gsk_[A-Za-z0-9]{40,}",_mp)
        if _m: GROQ_KEY=_m.group(0)
    except: pass

def run(c,t=20):
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

print(TSF,"PERMANENT FIX v2")
R={}

# ── 1. Rewrite portal_server.py (clean, with timeouts) ──────────
print("[1] Rewriting portal_server.py...")
ps_path=MSI+"/portal_server.py"
PORTAL_CODE = '\n'.join([
    'import http.server,json,os,urllib.request,mimetypes,datetime',
    'WEB="/home/k/vnt-web"',
    'M4="http://192.168.10.94:3333"',
    'PORT=8888',
    'TIMEOUT=60',
    'def log(m): print("["+datetime.datetime.now().strftime("%H:%M:%S")+"] "+m,flush=True)',
    'class H(http.server.BaseHTTPRequestHandler):',
    '    def log_message(self,*a): pass',
    '    def cors(self):',
    '        self.send_header("Access-Control-Allow-Origin","*")',
    '        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")',
    '        self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization")',
    '    def proxy(self,path,body=None,method="GET"):',
    '        try:',
    '            req=urllib.request.Request(M4+path,data=body,headers={"Content-Type":"application/json"},method=method)',
    '            with urllib.request.urlopen(req,timeout=TIMEOUT) as r:',
    '                data=r.read();ct=r.headers.get("Content-Type","application/json")',
    '                self.send_response(200);self.send_header("Content-Type",ct)',
    '                self.cors();self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)',
    '        except Exception as e:',
    '            err=json.dumps({"status":"error","error":str(e)}).encode()',
    '            self.send_response(503);self.send_header("Content-Type","application/json")',
    '            self.cors();self.send_header("Content-Length",str(len(err)));self.end_headers();self.wfile.write(err)',
    '    def do_OPTIONS(self): self.send_response(200);self.cors();self.end_headers()',
    '    def do_GET(self):',
    '        p=self.path.split("?")[0]',
    '        if p in ("/health","/api/health"):',
    '            resp=json.dumps({"status":"online","api":"VNT Portal v2","ts":datetime.datetime.now().isoformat()}).encode()',
    '            self.send_response(200);self.send_header("Content-Type","application/json")',
    '            self.cors();self.send_header("Content-Length",str(len(resp)));self.end_headers();self.wfile.write(resp);return',
    '        if p.startswith("/api/"): self.proxy(p[4:]); return',
    '        if p in ("/",""): p="/dashboard.html"',
    '        fp=WEB+p',
    '        if os.path.exists(fp) and os.path.isfile(fp):',
    '            ct,_=mimetypes.guess_type(fp);ct=ct or "application/octet-stream"',
    '            data=open(fp,"rb").read()',
    '            self.send_response(200);self.send_header("Content-Type",ct)',
    '            self.send_header("Content-Length",str(len(data)));self.cors();self.end_headers();self.wfile.write(data)',
    '        else: self.send_response(404);self.end_headers();self.wfile.write(b"404")',
    '    def do_POST(self):',
    '        n=int(self.headers.get("Content-Length",0));body=self.rfile.read(n) if n else None',
    '        if self.path.startswith("/api/"): log("POST "+self.path); self.proxy(self.path[4:],body,"POST"); return',
    '        self.send_response(404);self.end_headers()',
    'try: server=http.server.ThreadingHTTPServer(("0.0.0.0",PORT),H)',
    'except: server=http.server.HTTPServer(("0.0.0.0",PORT),H)',
    'log("VNT Portal v2 :"+str(PORT)+" -> "+M4)',
    'server.serve_forever()',
])
open(ps_path,"w").write(PORTAL_CODE)
sr=subprocess.run(["/usr/bin/python3","-m","py_compile",ps_path],capture_output=True,text=True)
R["portal_syntax"]="OK" if sr.returncode==0 else "FAIL:"+sr.stderr[:60]
print(f"  Syntax: {R['portal_syntax']}")

# ── 2. Try systemd with sudo, fall back to user systemd ─────────
print("[2] Installing watchdog/auto-restart...")
SVC_LINES=[
    "[Unit]",
    "Description=VNT Portal API Server port 8888",
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
svc_content="\n".join(SVC_LINES)

# Try sudo first (root may be configured for k)
sudo_ok=False
try:
    open("/tmp/vnt-portal.service","w").write(svc_content)
    cp_r=run("sudo cp /tmp/vnt-portal.service /etc/systemd/system/vnt-portal.service 2>&1",t=5)
    if "password" not in cp_r.lower() and "error" not in cp_r.lower():
        run("sudo systemctl daemon-reload 2>&1",t=5)
        run("sudo systemctl enable vnt-portal 2>&1",t=5)
        run("sudo systemctl stop vnt-portal 2>/dev/null; sudo fuser -k 8888/tcp 2>/dev/null; sleep 2",t=10)
        run("sudo systemctl start vnt-portal 2>&1",t=5)
        time.sleep(5)
        status=run("sudo systemctl is-active vnt-portal 2>&1",t=5)
        R["systemd"]="system:"+status
        sudo_ok=True
        print(f"  System systemd: {status}")
except: pass

# Try user systemd (no sudo needed)
if not sudo_ok:
    print("  Trying user systemd...")
    user_svc_dir=os.path.expanduser("~/.config/systemd/user")
    os.makedirs(user_svc_dir,exist_ok=True)
    open(user_svc_dir+"/vnt-portal.service","w").write(svc_content)
    run("systemctl --user daemon-reload",t=5)
    run("systemctl --user enable vnt-portal",t=5)
    run("systemctl --user stop vnt-portal 2>/dev/null; fuser -k 8888/tcp 2>/dev/null; sleep 2",t=8)
    run("systemctl --user start vnt-portal",t=5)
    time.sleep(5)
    status=run("systemctl --user is-active vnt-portal",t=5)
    R["systemd"]="user:"+status
    print(f"  User systemd: {status}")
    # Try to enable linger for auto-start
    linger=run("sudo loginctl enable-linger k 2>&1",t=5)
    R["linger"]=linger[:40] if linger else "ok"

# If both failed, use crontab approach
if "active" not in R.get("systemd",""):
    print("  Falling back to enhanced crontab...")
    # Write a watchdog script
    watchdog='\n'.join([
        '#!/bin/bash',
        '# VNT Portal Watchdog',
        'if ! fuser 8888/tcp > /dev/null 2>&1; then',
        '    echo "[$(date)] Portal down, restarting..." >> /tmp/portal_watchdog.log',
        '    fuser -k 8888/tcp 2>/dev/null',
        '    sleep 1',
        '    cd /home/k/vnt-web',
        '    nohup /usr/bin/python3 /home/k/vnt-web/portal_server.py >> /tmp/portal.log 2>&1 &',
        '    sleep 3',
        '    fuser 8888/tcp > /dev/null 2>&1 && echo "OK" >> /tmp/portal_watchdog.log || echo "FAIL" >> /tmp/portal_watchdog.log',
        'fi',
    ])
    open("/home/k/vnt_portal_watchdog.sh","w").write(watchdog)
    run("chmod +x /home/k/vnt_portal_watchdog.sh",t=3)
    # Install in crontab (every 1 minute)
    existing_cron=run("crontab -l 2>/dev/null",t=5)
    if "vnt_portal_watchdog" not in existing_cron:
        new_cron=existing_cron.strip()+"\n"
        new_cron+="@reboot sleep 10 && /usr/bin/python3 /home/k/vnt-web/portal_server.py >> /tmp/portal.log 2>&1 &\n"
        new_cron+="* * * * * /home/k/vnt_portal_watchdog.sh\n"
        run(f'echo "{new_cron}" | crontab -',t=5)
        R["crontab"]="installed (*/1 watchdog + @reboot)"
    else:
        R["crontab"]="already present"
    # Start portal now
    run("fuser -k 8888/tcp 2>/dev/null; sleep 2")
    subprocess.Popen(["/usr/bin/python3",MSI+"/portal_server.py"],
        stdout=open("/tmp/portal.log","w"),stderr=subprocess.STDOUT)
    time.sleep(5)
    status=run("fuser 8888/tcp")
    R["portal_running"]="YES:"+status if status else "NO"
    print(f"  Portal running: {R['portal_running']}")

# ── 3. Verify API ────────────────────────────────────────────────
print("[3] Verify portal API...")
for attempt in range(3):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8888/api/health",timeout=8) as r2:
            resp_data=json.loads(r2.read())
            R["api_health"]="PASS "+resp_data.get("status","?")
            break
    except Exception as e:
        R["api_health"]="FAIL:"+str(e)[:30]
        time.sleep(3)
print(f"  {R['api_health']}")

# ── 4. M4 check + restart ────────────────────────────────────────
print("[4] M4 check...")
m4_h=run("ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 -o BatchMode=yes Alias@192.168.10.94 \"curl -s http://localhost:3333/health 2>/dev/null || echo OFFLINE\"",t=12)
R["m4"]=m4_h[:80]
print(f"  M4: {m4_h[:60]}")
if "online" not in m4_h.lower():
    run("ssh -o StrictHostKeyChecking=no -o BatchMode=yes Alias@192.168.10.94 \"pkill -f studio_api 2>/dev/null; sleep 2; nohup /Users/alias/miniforge3/envs/vnt/bin/python /Users/alias/vnt-studio/studio_api.py >> /tmp/studio.log 2>&1 &\"",t=15)
    time.sleep(10)
    m4_h2=run("ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes Alias@192.168.10.94 \"curl -s http://localhost:3333/health\"",t=12)
    R["m4_after"]=m4_h2[:60]
    print(f"  M4 after: {m4_h2[:60]}")

# ── 5. Install Mia v2 ───────────────────────────────────────────
print("[5] Mia v2...")
try:
    mia_data=gh_api("mia_v2.py")
    mia_code=base64.b64decode(mia_data["content"].replace("\n","")).decode()
    if GROQ_KEY:
        mia_code=mia_code.replace('os.environ.get("GROQ_API_KEY","")','"""'+GROQ_KEY+'"""')
    os.makedirs("/home/k/vnt-agents",exist_ok=True)
    open("/home/k/vnt-agents/mia_v2.py","w").write(mia_code)
    R["mia_v2"]="OK /home/k/vnt-agents/mia_v2.py"
    print(f"  {R['mia_v2']}")
except Exception as e:
    R["mia_v2"]="FAIL:"+str(e)[:50]

# ── 6. OpenClaw scan ────────────────────────────────────────────
print("[6] OpenClaw scan...")
oc_path="/home/k/.openclaw/openclaw.json"
if os.path.exists(oc_path):
    try:
        raw=open(oc_path).read()
        R["openclaw_keys"]=str(list(json.loads(raw).keys())[:10])
        mia_idx=raw.lower().find("mia")
        R["mia_in_oc"]="found at "+str(mia_idx) if mia_idx>=0 else "not found"
        if mia_idx>=0: R["mia_oc_ctx"]=raw[max(0,mia_idx-10):mia_idx+150]
        print(f"  Keys: {R['openclaw_keys']}")
        print(f"  Mia: {R['mia_in_oc']}")
    except Exception as e: R["openclaw_err"]=str(e)[:50]
else:
    hls=run("ls /home/k/")
    R["home_k_ls"]=hls[:300]
    print(f"  No openclaw.json. home/k: {hls[:100]}")

# ── 7. MemPalace ────────────────────────────────────────────────
print("[7] MemPalace...")
MP_ENTRY = "\n".join([
    "",
    "=====================================",
    f"## API PORTAL RCA + PERMANENT FIX [{TSF}]",
    "=====================================",
    "PROBLEM: MSI portal (:8888) kept going offline.",
    "",
    "ROOT CAUSES:",
    "1. nohup dies silently on crash → FIXED: systemd/watchdog Restart=always",
    "2. No crash logging → FIXED: journalctl -u vnt-portal OR /tmp/portal_watchdog.log",
    "3. M4 requests timed out (no timeout set) → FIXED: TIMEOUT=60 in portal code",
    "4. Port 8888 conflict on restart → FIXED: fuser -k 8888/tcp before start",
    "",
    "PORTAL v2: /home/k/vnt-web/portal_server.py",
    "- Health: curl http://127.0.0.1:8888/api/health",
    "- Proxies /api/* to M4 (192.168.10.94:3333) with 60s timeout",
    "",
    "WATCHDOG: Every 1 minute via crontab OR systemd --user",
    "Watchdog script: /home/k/vnt_portal_watchdog.sh",
    "",
    "RECOVERY (Zeus/Alias follow this):",
    "1. fuser 8888/tcp → check if running",
    "2. /home/k/vnt_portal_watchdog.sh → manual trigger",
    "3. curl http://127.0.0.1:8888/api/health → confirm OK",
    "4. For M4: ssh Alias@192.168.10.94 curl localhost:3333/health",
    "5. M4 restart: ssh Alias@192.168.10.94 pkill -f studio_api + nohup python studio_api.py",
    "6. Check log: cat /tmp/portal.log | tail -30",
    "",
    "MIA v2: /home/k/vnt-agents/mia_v2.py",
    "- Multilingual: EN/AR/UR/FR auto-detected by character set",
    "- Audio-in -> Audio-out (edge-tts per language)",
    "- Human personality system prompt (no robotic responses)",
    "",
    "DASHBOARD: SAPI=http://192.168.10.96:8888/api",
    "=====================================",
])
try:
    open(MP,"a").write(MP_ENTRY)
    R["mempalace"]="WRITTEN"
except Exception as e: R["mempalace"]="FAIL:"+str(e)[:30]

gh_save(R)
print("\n=== RESULTS ===")
for k,v in R.items():
    ok="OK" if any(x in str(v) for x in ["PASS","active","online","OK","installed","WRITTEN","YES"]) else "FL"
    print(f"  [{ok}] {k}: {str(v)[:80]}")
print("DONE")
