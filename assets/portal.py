
import subprocess, os, json, datetime, base64, urllib.request, time, ast

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"
USER_DIR = "/home/k/.config/systemd/user"

def push_result(name, content):
    try:
        api = f"https://api.github.com/repos/{REPO}/contents/results/{name}"
        req = urllib.request.Request(api, headers={"Authorization":"Bearer "+GH})
        try:
            with urllib.request.urlopen(req,timeout=10) as r: sha=json.loads(r.read()).get("sha","")
        except: sha=""
        data={"message":name,"content":base64.b64encode(content.encode()).decode()}
        if sha: data["sha"]=sha
        req2=urllib.request.Request(api,data=json.dumps(data).encode(),
            headers={"Authorization":"Bearer "+GH,"Content-Type":"application/json"},method="PUT")
        with urllib.request.urlopen(req2,timeout=15) as r2: return "content" in json.loads(r2.read())
    except: return False

def uservice(name, exec_cmd, desc):
    unit=chr(10).join(["[Unit]","Description="+desc,"After=network.target","",
        "[Service]","ExecStart="+exec_cmd,"WorkingDirectory=/home/k",
        "Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
        "[Install]","WantedBy=default.target"])
    open(USER_DIR+"/"+name+".service","w").write(unit)

out=[]
def log(m): out.append(m); print(m)
X="XDG_RUNTIME_DIR=/run/user/1000 "

log("="*55)
log("BUILD PORTAL + LOCATE/FIX M4 MEDIA")
log("="*55)

# 1. Locate M4 media scripts (search the whole home dir)
log("\n[1] Finding M4 media scripts...")
def ssh_m4(cmd,t=25):
    return run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 Alias@192.168.10.94 \""+cmd+"\"",shell=True,timeout=t)
m4,_=ssh_m4("echo OK")
if "OK" in m4:
    # Find all python files with 'generate' or 'media' or ':3333' or 'flask/server'
    scripts,_=ssh_m4("find /Users/alias -name '*.py' 2>/dev/null | grep -iE 'generate|media|server|api|3333|comfy' | head -20")
    log(f"  Found scripts:\n{scripts[:400]}")
    # Find what listens on 3333 historically
    gens,_=ssh_m4("ls /Users/alias/*generate*.py /Users/alias/ai*/*.py 2>/dev/null | head -10")
    log(f"  Generate scripts: {gens[:300]}")
    # Check for the media studio server specifically
    studio,_=ssh_m4("grep -rl '3333' /Users/alias/*.py /Users/alias/*/*.py 2>/dev/null | head -5")
    log(f"  Scripts referencing 3333: {studio[:200]}")
else:
    log("  M4 SSH failed")

# 2. BUILD PORTAL :8080 fresh
log("\n[2] Building VNT Portal :8080...")
portal_lines=["#!/usr/bin/env python3",
    "# VNT Portal - secure login gateway to agent dashboard",
    "import http.server,socketserver,json,os,base64,urllib.parse",
    "PORT=8080",
    "USERS={'khawaja':'App159earance.VnT','admin':'VNTadmin2026'}",
    "SESSIONS=set()",
    "LOGIN_PAGE='''<!DOCTYPE html><html><head><meta charset=UTF-8><meta name=viewport content=\"width=device-width,initial-scale=1\"><title>VNT Portal</title>",
    "<style>*{margin:0;padding:0;box-sizing:border-box}body{background:linear-gradient(135deg,#0a0e14,#161b22);height:100vh;display:flex;align-items:center;justify-content:center;font-family:Segoe UI,sans-serif}",
    ".box{background:#0d1117;border:1px solid #21262d;border-radius:14px;padding:40px;width:340px;box-shadow:0 20px 60px rgba(0,0,0,.5)}",
    ".lo{font-size:24px;font-weight:800;color:#58a6ff;text-align:center;letter-spacing:1px;margin-bottom:6px}.sub{color:#6e7681;text-align:center;font-size:12px;margin-bottom:28px}",
    "input{width:100%;padding:12px 14px;margin:8px 0;background:#161b22;border:1px solid #21262d;border-radius:8px;color:#c9d1d9;font-size:14px}",
    "input:focus{outline:none;border-color:#1f6feb}button{width:100%;padding:12px;margin-top:16px;background:#1f6feb;border:none;border-radius:8px;color:#fff;font-size:15px;font-weight:600;cursor:pointer}",
    "button:hover{background:#388bfd}.err{color:#f85149;font-size:12px;text-align:center;margin-top:12px;min-height:16px}</style></head><body>",
    "<div class=box><div class=lo>VNT WORLD</div><div class=sub>AI Division Portal</div>",
    "<form method=POST action=/login><input name=u placeholder=Username autocomplete=off><input name=p type=password placeholder=Password>",
    "<button type=submit>Sign In</button></form><div class=err>{ERR}</div></div></body></html>'''",
    "def dashboard():",
    "    return '''<!DOCTYPE html><html><head><meta charset=UTF-8><title>VNT Dashboard</title>",
    "<style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0a0e14;color:#c9d1d9;font-family:Segoe UI,sans-serif}",
    ".hd{background:#161b22;padding:16px 28px;border-bottom:2px solid #1f6feb;display:flex;justify-content:space-between;align-items:center}",
    ".lo{font-size:20px;font-weight:800;color:#58a6ff}.cards{padding:28px;display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}",
    ".card{background:#0d1117;border:1px solid #21262d;border-radius:12px;padding:24px;transition:.2s}.card:hover{border-color:#1f6feb;transform:translateY(-3px)}",
    ".card h3{color:#58a6ff;font-size:15px;margin-bottom:8px}.card p{color:#6e7681;font-size:13px;margin-bottom:16px}",
    ".card a{display:inline-block;padding:9px 18px;background:#1f6feb;color:#fff;border-radius:7px;text-decoration:none;font-size:13px;font-weight:600}",
    "</style></head><body><div class=hd><div class=lo>VNT WORLD AI DIVISION</div><div style=\"color:#3fb950;font-size:13px\">● Online</div></div>",
    "<div class=cards>",
    "<div class=card><h3>Monitoring Center</h3><p>Live agent fleet status, services, real-time health</p><a href=\"http://192.168.10.96:8888/monitor.html\">Open Monitor</a></div>",
    "<div class=card><h3>Agent Hierarchy</h3><p>Full org chart of all 17 agents and their roles</p><a href=\"http://192.168.10.96:8888/vnt_hierarchy.html\">View Hierarchy</a></div>",
    "<div class=card><h3>Media Studio</h3><p>AI image, video, and 3D generation</p><a href=\"http://192.168.10.96:8888/media.html\">Open Studio</a></div>",
    "<div class=card><h3>Nextcloud Files</h3><p>VNT file server and document storage</p><a href=\"http://192.168.10.10/\">Open Files</a></div>",
    "</div></body></html>'''",
    "class H(http.server.BaseHTTPRequestHandler):",
    "    def log_message(self,*a):pass",
    "    def _send(self,html,code=200):",
    "        self.send_response(code);self.send_header('Content-Type','text/html');self.end_headers()",
    "        self.wfile.write(html.encode())",
    "    def do_GET(self):",
    "        cookie=self.headers.get('Cookie','')",
    "        if 'vnt_session' in cookie and cookie.split('vnt_session=')[1].split(';')[0] in SESSIONS:",
    "            self._send(dashboard())",
    "        else:",
    "            self._send(LOGIN_PAGE.replace('{ERR}',''))",
    "    def do_POST(self):",
    "        if self.path=='/login':",
    "            n=int(self.headers.get('Content-Length',0))",
    "            data=urllib.parse.parse_qs(self.rfile.read(n).decode())",
    "            u=data.get('u',[''])[0];p=data.get('p',[''])[0]",
    "            if USERS.get(u)==p:",
    "                import secrets;tok=secrets.token_hex(16);SESSIONS.add(tok)",
    "                self.send_response(302);self.send_header('Set-Cookie','vnt_session='+tok+'; Path=/');self.send_header('Location','/');self.end_headers()",
    "            else:",
    "                self._send(LOGIN_PAGE.replace('{ERR}','Invalid credentials'))",
    "        else:self._send(LOGIN_PAGE.replace('{ERR}',''))",
    "socketserver.TCPServer.allow_reuse_address=True",
    "print('VNT Portal :8080')",
    "try:http.server.HTTPServer(('0.0.0.0',8080),H).serve_forever()",
    "except Exception as e:print('Portal crash:',e);raise"]
portal_code=chr(10).join(portal_lines)
try:
    ast.parse(portal_code)
    open("/home/k/vnt-portal.py","w").write(portal_code)
    os.chmod("/home/k/vnt-portal.py",0o755)
    uservice("vnt-portal","/usr/bin/python3 /home/k/vnt-portal.py","VNT Portal")
    run(X+"systemctl --user daemon-reload",shell=True)
    run(X+"systemctl --user enable vnt-portal",shell=True)
    run("fuser -k 8080/tcp 2>/dev/null",shell=True)
    time.sleep(2)
    run(X+"systemctl --user restart vnt-portal",shell=True,timeout=12)
    time.sleep(4)
    portal,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8080/ 2>/dev/null | grep -o 'VNT WORLD' | head -1",shell=True,timeout=5)
    log(f"  Portal :8080: {'OK - login page serving' if portal else 'down'}")
except SyntaxError as e:
    log(f"  Portal syntax error L{e.lineno}: {e.msg}")

# 3. If M4 media scripts found, start them. Otherwise build a minimal media API.
log("\n[3] M4 Media API...")
if "OK" in m4:
    PY="/Users/alias/miniforge3/envs/vnt/bin/python"
    # Look for any generate.py to confirm media capability exists
    has_gen,_=ssh_m4("test -f /Users/alias/generate.py && echo YES || test -f /Users/alias/ai-media/generate.py && echo YES2")
    log(f"  Generate.py check: {has_gen}")
    # Find ANY .py that could be the api server
    allpy,_=ssh_m4("ls /Users/alias/*.py 2>/dev/null")
    log(f"  Home .py files: {allpy[:300]}")

full="\n".join(out)
push_result("portal_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
