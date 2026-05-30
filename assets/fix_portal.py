import subprocess, os, json, datetime, ast, time

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
WEB = "/home/k/vnt-web"

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Portal ["+ts+"]\n"+e+"\n")
    except: pass

try:
    cfg = json.load(open(CFG))
    GROQ  = cfg.get("groq_key","")
    GMAIL = cfg.get("gmail_user","aliasvnt@gmail.com")
    GPASS = cfg.get("gmail_app_password","xkuzasikrrukorvg")
    RYAN  = cfg.get("ryan_email","kraheelw@yahoo.com")
except:
    GROQ=""; GMAIL="aliasvnt@gmail.com"; GPASS="xkuzasikrrukorvg"; RYAN="kraheelw@yahoo.com"

ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
print("="*55)
print("FIX: PORTAL LOGIN + ASUSI7 INSTALL")
print(ts)
print("="*55)

# ── 1. TEST PUBLIC IP FIRST ──────────────────────────────
print("\n[1] Testing public IP access...")
pub_test,_ = run("curl -s --connect-timeout 5 http://94.49.29.97:8888/ | head -c 50",shell=True,timeout=10)
print("  Public IP 94.49.29.97:8888:",pub_test[:40] if pub_test else "NOT REACHABLE")
# Check what port is actually forwarded
ports_test = []
for port in [8888, 80, 443, 8080, 3000]:
    o,_ = run(f"curl -s --connect-timeout 3 http://94.49.29.97:{port}/ -o /dev/null -w '%{{http_code}}'",shell=True,timeout=5)
    if o and o != "000":
        ports_test.append(str(port)+"="+o)
print("  Reachable ports:",ports_test if ports_test else "NONE - router port forwarding not set up")
save("Public IP test: ports="+str(ports_test))

# ── 2. BUILD SECURE LOGIN PORTAL ────────────────────────
print("\n[2] Building secure download portal...")

# Portal users - Ryan's credentials
PORTAL_USERS = {
    "khawaja": "App159earance.VnT",
    "administrator": "0568116899",
}

portal_code = """#!/usr/bin/env python3
\"\"\"
VNT Secure Portal - login-protected download + agent access
Only accessible with username/password
\"\"\"
import http.server, json, os, hashlib, base64, datetime
import urllib.parse, socketserver, subprocess, mimetypes, time

PORT   = 8080
WEB    = "/home/k/vnt-web"
PROJ   = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects"
MP     = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG    = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

# Auth - read from config or use defaults
try:
    cfg   = json.load(open(CFG))
    USERS = {
        cfg.get("nc_user","khawaja").split(" /")[0]: cfg.get("khawaja_pass","App159earance.VnT"),
        cfg.get("nc_admin","administrator").split(" /")[0]: cfg.get("nc_pass","0568116899"),
    }
except:
    USERS = {"khawaja":"App159earance.VnT","administrator":"0568116899"}

SESSIONS = {}

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\\n### Portal ["+ts+"]\\n"+str(e)+"\\n")
    except: pass

def make_session(user):
    token = hashlib.sha256((user+str(time.time())).encode()).hexdigest()[:32]
    SESSIONS[token] = {"user":user,"ts":time.time()}
    return token

def check_session(token):
    if not token: return None
    s = SESSIONS.get(token)
    if s and time.time()-s["ts"] < 86400:
        return s["user"]
    return None

def get_cookie(headers):
    cookie = headers.get("Cookie","")
    for part in cookie.split(";"):
        p = part.strip()
        if p.startswith("vnt_session="):
            return p.split("=",1)[1]
    return None

LOGIN_HTML = \"\"\"<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VNT Portal - Login</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif;
  min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:32px;width:320px}
.logo{font-size:20px;font-weight:700;color:#58a6ff;text-align:center;margin-bottom:6px}
.sub{font-size:12px;color:#484f58;text-align:center;margin-bottom:24px}
label{font-size:12px;color:#7ab87a;display:block;margin-bottom:4px}
input{width:100%;background:#0d1117;border:1px solid #21262d;color:#c9d1d9;
  padding:10px 12px;border-radius:6px;font-size:13px;margin-bottom:14px;outline:none}
input:focus{border-color:#1f6feb}
.btn{width:100%;background:#1f6feb;color:#fff;border:none;padding:11px;
  border-radius:6px;font-size:14px;font-weight:600;cursor:pointer}
.btn:hover{opacity:.85}
.err{background:rgba(218,54,51,.15);border:1px solid #da3633;color:#f85149;
  padding:8px 12px;border-radius:6px;font-size:12px;margin-bottom:12px;display:none}
</style></head><body>
<div class="box">
  <div class="logo">VNT World AI Division</div>
  <div class="sub">Secure Portal</div>
  {error}
  <form method="POST" action="/login">
    <label>Username</label>
    <input type="text" name="username" placeholder="Enter username" autocomplete="username">
    <label>Password</label>
    <input type="password" name="password" placeholder="Enter password" autocomplete="current-password">
    <button class="btn" type="submit">Sign In</button>
  </form>
</div>
</body></html>\"\"\"

def portal_page(user):
    return \"\"\"<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VNT Portal</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif}
.hdr{background:#161b22;border-bottom:1px solid #21262d;padding:14px 24px;
  display:flex;justify-content:space-between;align-items:center}
.logo{font-size:17px;font-weight:700;color:#58a6ff}
.sub{font-size:11px;color:#484f58;margin-top:2px}
.user-tag{font-size:12px;color:#3fb950}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;padding:20px}
.card{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:18px}
.card-title{font-size:14px;font-weight:600;color:#e0ffe0;margin-bottom:6px;display:flex;align-items:center;gap:8px}
.card-desc{font-size:12px;color:#484f58;line-height:1.5;margin-bottom:14px}
.btn{padding:8px 14px;border-radius:6px;font-size:12px;font-weight:500;
  text-decoration:none;border:1px solid;display:inline-block;cursor:pointer;background:none}
.bg{border-color:#238636;color:#3fb950}.bb{border-color:#1f6feb;color:#58a6ff}
.bo{border-color:#9e6a03;color:#d29922}.br{border-color:#da3633;color:#f85149}
.sep{grid-column:1/-1;border-top:1px solid #21262d;padding-top:4px;
  font-size:10px;color:#484f58;text-transform:uppercase;letter-spacing:2px}
</style></head><body>
<div class="hdr">
  <div><div class="logo">VNT World AI Division</div><div class="sub">Secure Portal</div></div>
  <div style="display:flex;align-items:center;gap:12px">
    <span class="user-tag">Logged in as: \"\"\"+user+\"\"\"</span>
    <a href="/logout" class="btn br" style="font-size:11px;padding:5px 10px">Logout</a>
  </div>
</div>
<div class="grid">
  <div class="sep">Quick Access</div>
  <div class="card">
    <div class="card-title">&#127908; Voice - Alias</div>
    <div class="card-desc">Talk directly to Alias CEO via voice call</div>
    <a href="https://192.168.10.96:8443" class="btn bg">Open Voice</a>
  </div>
  <div class="card">
    <div class="card-title">&#129302; VNT Agent App</div>
    <div class="card-desc">Full device control portal - chat, terminal, files, screen</div>
    <a href="/vnt-agent/" class="btn bb">Open App</a>
  </div>
  <div class="card">
    <div class="card-title">&#9729; Nextcloud Files</div>
    <div class="card-desc">Access all VNT files and documents</div>
    <a href="http://192.168.10.10" class="btn bg">Open Files</a>
  </div>
  <div class="card">
    <div class="card-title">&#127912; Media Studio</div>
    <div class="card-desc">Generate images, video, 3D via M4 MacBook</div>
    <a href="/media.html" class="btn bo">Open Studio</a>
  </div>
  <div class="card">
    <div class="card-title">&#128202; Hierarchy</div>
    <div class="card-desc">Live agent status and infrastructure</div>
    <a href="/vnt_hierarchy.html" class="btn bb">Open Hierarchy</a>
  </div>

  <div class="sep">Downloads - VNT Agent App</div>
  <div class="card">
    <div class="card-title">&#128187; Windows Agent</div>
    <div class="card-desc">Install on any Windows PC. Alias gets full control. Run as Administrator.</div>
    <a href="/downloads/install_vnt_agent.bat" class="btn bg">Download .bat</a>
    &nbsp;
    <a href="/downloads/vnt_device_agent.py" class="btn bb">Download .py</a>
  </div>
  <div class="card">
    <div class="card-title">&#128241; Android / iOS</div>
    <div class="card-desc">Open VNT Agent in Chrome and tap Add to Home Screen for instant app</div>
    <a href="/vnt-agent/" class="btn bg">Open Web App</a>
    &nbsp;
    <a href="/downloads/android_setup.md" class="btn bb">Setup Guide</a>
  </div>
  <div class="card">
    <div class="card-title">&#127758; Browser Extension</div>
    <div class="card-desc">Chrome/Edge/Brave extension - Ask Alias from any webpage</div>
    <a href="/downloads/vnt_extension.zip" class="btn bg">Download Extension</a>
    &nbsp;
    <a href="/downloads/extension_guide.md" class="btn bb">Install Guide</a>
  </div>
  <div class="card">
    <div class="card-title">&#127880; Device Agent (Python)</div>
    <div class="card-desc">Cross-platform agent. Runs on Linux, Mac, Windows, Android (Termux)</div>
    <a href="/downloads/vnt_device_agent.py" class="btn bg">Download</a>
  </div>

  <div class="sep">Projects</div>
  <div class="card">
    <div class="card-title">&#127981; BirdHouse Sanctuary</div>
    <div class="card-desc">Community bird sanctuary project - full proposal, DXF, PPTX</div>
    <a href="/generated/bird_house_proposal.html" class="btn bg">View Proposal</a>
    &nbsp;
    <a href="/generated/BirdHouse_Presentation.pptx" class="btn bb">PPTX</a>
    &nbsp;
    <a href="/generated/birdhouse_site_plan.dxf" class="btn bo">DXF</a>
  </div>
  <div class="card">
    <div class="card-title">&#127918; HannahBird Game</div>
    <div class="card-desc">Bird game APK and web version</div>
    <a href="/HannahBird.html" class="btn bg">Play Web</a>
  </div>
</div>
</body></html>\"\"\"

class PortalHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send_html(self, html, status=200, headers=None):
        encoded = html.encode()
        self.send_response(status)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(encoded)))
        if headers:
            for k,v in headers.items(): self.send_header(k,v)
        self.end_headers()
        self.wfile.write(encoded)

    def check_auth(self):
        token = get_cookie(self.headers)
        return check_session(token)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/logout":
            token = get_cookie(self.headers)
            if token: SESSIONS.pop(token,None)
            self.send_response(302)
            self.send_header("Location","/")
            self.send_header("Set-Cookie","vnt_session=; Max-Age=0; Path=/")
            self.end_headers()
            return

        if path in ["/","/login","/portal"]:
            user = self.check_auth()
            if user:
                self.send_html(portal_page(user))
            else:
                self.send_html(LOGIN_HTML.replace("{error}",""))
            return

        # Protected paths
        user = self.check_auth()
        if not user:
            self.send_response(302)
            self.send_header("Location","/")
            self.end_headers()
            return

        # Serve downloads
        if path.startswith("/downloads/"):
            fname = path.split("/downloads/")[1]
            download_map = {
                "install_vnt_agent.bat": "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/VNT_Agent_App/windows/install_vnt_agent.bat",
                "vnt_device_agent.py":   "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/VNT_Agent_App/backend/vnt_device_agent.py",
                "android_setup.md":      "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/VNT_Agent_App/android/SETUP.md",
                "extension_guide.md":    "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/VNT_Agent_App/android/SETUP.md",
            }
            fpath = download_map.get(fname,"")
            if fpath and os.path.exists(fpath):
                content = open(fpath,"rb").read()
                self.send_response(200)
                self.send_header("Content-Type","application/octet-stream")
                self.send_header("Content-Disposition","attachment; filename="+fname)
                self.send_header("Content-Length",str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                save("Download: "+fname+" by "+user)
                return
            else:
                self.send_html("<h3>File not found: "+fname+"</h3>",404)
                return

        # Serve static files from web folder
        file_path = WEB + path
        if os.path.isdir(file_path):
            file_path = file_path + "/index.html"
        if os.path.exists(file_path):
            content = open(file_path,"rb").read()
            mime,_ = mimetypes.guess_type(file_path)
            self.send_response(200)
            self.send_header("Content-Type", mime or "text/plain")
            self.send_header("Content-Length",str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_html("<h3>Not found: "+path+"</h3>",404)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        n = int(self.headers.get("Content-Length",0))
        body = self.rfile.read(n).decode()

        if path == "/login":
            params = dict(urllib.parse.parse_qsl(body))
            username = params.get("username","").strip()
            password = params.get("password","").strip()
            if USERS.get(username) == password:
                token = make_session(username)
                save("Login: "+username)
                self.send_response(302)
                self.send_header("Location","/")
                self.send_header("Set-Cookie","vnt_session="+token+"; Path=/; HttpOnly; Max-Age=86400")
                self.end_headers()
            else:
                save("Failed login attempt: "+username)
                err = '<div class="err" style="display:block">Wrong username or password</div>'
                self.send_html(LOGIN_HTML.replace("{error}",err))
            return

        # Proxy to Alias agent
        user = self.check_auth()
        if not user:
            self.send_response(401)
            self.end_headers()
            return

        # Forward to Alias
        try:
            import urllib.request as ul
            req = ul.Request("http://127.0.0.1:8443/",
                data=body.encode(),headers={"Content-Type":"application/json"},method="POST")
            with ul.urlopen(req,timeout=15) as r:
                result = r.read()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(result)
        except Exception as e:
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"reply":"Alias is restarting. Try again in a moment.","error":str(e)}).encode())

save("VNT Secure Portal started on :"+str(PORT))
print("VNT Secure Portal running on :"+str(PORT))
print("Login: khawaja / App159earance.VnT")
print("Login: administrator / 0568116899")
socketserver.TCPServer.allow_reuse_address = True
try:
    http.server.HTTPServer(("0.0.0.0",PORT),PortalHandler).serve_forever()
except Exception as e:
    save("Portal crash: "+str(e)); raise
"""

try:
    ast.parse(portal_code)
    open("/home/k/vnt-portal.py","w").write(portal_code)
    print("  Portal: written and validated")
except SyntaxError as e:
    print(f"  Portal syntax: {e}")
    import sys; sys.exit(1)

# Install portal service
svc = "\n".join(["[Unit]","Description=VNT Secure Portal","After=network.target","",
    "[Service]","User=k","ExecStart=/usr/bin/python3 /home/k/vnt-portal.py",
    "Restart=always","RestartSec=5","Environment=PYTHONUNBUFFERED=1","",
    "[Install]","WantedBy=multi-user.target"])
open("/tmp/vnt-portal.service","w").write(svc)
run(["sudo","cp","/tmp/vnt-portal.service","/etc/systemd/system/vnt-portal.service"])
run(["sudo","systemctl","daemon-reload"])
run(["sudo","systemctl","enable","vnt-portal"])
run(["sudo","systemctl","restart","vnt-portal"],timeout=15)
time.sleep(2)
portal_st,_ = run(["systemctl","is-active","vnt-portal"])
print("  Portal service: "+portal_st)

# Test portal locally
test,_ = run("curl -s --connect-timeout 3 http://127.0.0.1:8080/ | grep -o 'VNT Portal\\|VNT World'",shell=True,timeout=8)
print("  Portal test: "+test if test else "  Portal test: starting up...")

# ── 3. SET UP DOWNLOADS FOLDER ──────────────────────────
print("\n[3] Setting up downloads folder...")
dl_dir = WEB+"/downloads"
os.makedirs(dl_dir, exist_ok=True)
agent_proj = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/VNT_Agent_App"
import shutil
for f,dst in [
    (agent_proj+"/windows/install_vnt_agent.bat","install_vnt_agent.bat"),
    (agent_proj+"/backend/vnt_device_agent.py","vnt_device_agent.py"),
    (agent_proj+"/android/SETUP.md","android_setup.md"),
]:
    if os.path.exists(f):
        shutil.copy(f, dl_dir+"/"+dst)
        print("  Download ready: "+dst)

# Extension guide
ext_guide = """# VNT Browser Extension - Install Guide

## Chrome / Edge / Brave

1. Download and extract the extension files
2. Open: chrome://extensions/
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select the extension folder
6. Done - VNT Agent icon appears in toolbar

## What it does
- Click icon to ask Alias anything
- Right-click any text -> Ask Alias
- Right-click code -> Fix with Alias
- Summarize any page with one click

## Connect to Alias
Extension connects to: http://192.168.10.96:8443
Make sure you're on the VNT network or connected via VPN.
"""
open(dl_dir+"/extension_guide.md","w").write(ext_guide)

# ── 4. PORT FORWARDING GUIDE FOR PUBLIC ACCESS ──────────
print("\n[4] Checking public IP setup...")
# Check if port 8080 is forwarded
pub_test,_ = run("curl -s --connect-timeout 5 http://94.49.29.97:8080/ | head -c 30",shell=True,timeout=10)
if pub_test:
    print("  Port 8080: REACHABLE from internet")
    save("Public portal: http://94.49.29.97:8080/ - WORKING")
else:
    print("  Port 8080: not forwarded - need router config")
    # Also try the webserver port
    pub_test2,_ = run("curl -s --connect-timeout 5 http://94.49.29.97:8888/ | head -c 30",shell=True,timeout=10)
    if pub_test2:
        print("  Port 8888: REACHABLE")
    else:
        print("  ROUTER FORWARDING NEEDED:")
        print("  Forward port 8080 -> 192.168.10.96:8080 on your router")
        print("  Then access: http://94.49.29.97:8080/")
    save("Public IP needs router port forwarding: 8080->192.168.10.96:8080")

# Update config with portal info
try:
    cfg = json.load(open(CFG))
    cfg["portal_port"] = 8080
    cfg["portal_local"] = "http://192.168.10.96:8080/"
    cfg["portal_users"] = {"khawaja":"configured","administrator":"configured"}
    json.dump(cfg, open(CFG,"w"), indent=2)
except: pass

# ── 5. INSTALL VNT AGENT ON ASUSI7 ──────────────────────
print("\n[5] Installing VNT Agent on Asusi7 via SSH...")
def ssh7(cmd, timeout=20):
    return run(
        "sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "
        "Alias@192.168.10.114 \""+cmd+"\"",
        shell=True, timeout=timeout)

# Test connection
test_out,test_err = ssh7("echo CONNECTED && whoami && hostname")
if "CONNECTED" in test_out:
    print("  SSH: CONNECTED to Asusi7")
    print("  User: "+test_out.split("\n")[1] if "\n" in test_out else test_out)

    # Create directories
    ssh7("mkdir C:\\\\VNT 2>nul & mkdir C:\\\\temp 2>nul")

    # Check Python
    py_v,_ = ssh7("python --version 2>&1")
    print("  Python: "+py_v[:30])

    if "Python" in py_v:
        # Copy device agent via SCP alternative - write line by line using PowerShell here-string
        agent_src = open(agent_proj+"/backend/vnt_device_agent.py").read()
        # Write using powershell Set-Content with escaped content
        # Split into chunks to avoid command length limits
        lines = agent_src.split("\n")
        # Write first line
        first = lines[0].replace("'","''").replace('"','\\"')
        ssh7("powershell -Command \"Set-Content -Path C:\\\\VNT\\\\vnt_device_agent.py -Value '"+first+"' -Encoding UTF8\"")
        # Append remaining lines
        for line in lines[1:]:
            escaped = line.replace("'","''").replace('"','\\"')
            ssh7("powershell -Command \"Add-Content -Path C:\\\\VNT\\\\vnt_device_agent.py -Value '"+escaped+"' -Encoding UTF8\"")

        # Start the agent
        start_out,_ = ssh7("powershell -Command \"Start-Process python -ArgumentList 'C:\\\\VNT\\\\vnt_device_agent.py' -WindowStyle Hidden\"")

        # Add firewall rule
        ssh7("netsh advfirewall firewall add rule name=\"VNT Agent\" dir=in action=allow protocol=TCP localport=7900 2>nul")

        # Add to startup
        ssh7("powershell -Command \"$action=New-ScheduledTaskAction -Execute 'python' -Argument 'C:\\\\VNT\\\\vnt_device_agent.py'; $trigger=New-ScheduledTaskTrigger -AtStartup; Register-ScheduledTask -TaskName 'VNT Agent' -Action $action -Trigger $trigger -Force\"")

        time.sleep(3)
        # Test it
        test_agent,_ = run("curl -s --connect-timeout 5 http://192.168.10.114:7900/",shell=True,timeout=8)
        if test_agent:
            print("  VNT Agent on Asusi7: RUNNING ✓")
            print("  Response: "+test_agent[:80])
            save("VNT Device Agent installed and running on Asusi7 192.168.10.114:7900")
        else:
            print("  VNT Agent started (may take a moment to be reachable)")
    else:
        print("  Python not found on Asusi7 - installing...")
        ssh7("winget install Python.Python.3 -h --accept-package-agreements 2>nul || echo manual_install_needed",timeout=120)
else:
    print("  SSH to Asusi7 FAILED: "+test_err[:60])
    save("Asusi7 SSH failed: "+test_err[:60])

save("\n".join([
    "PORTAL + ASUSI7 COMPLETE "+ts,
    "Portal: http://192.168.10.96:8080/ (login required)",
    "Portal service: "+portal_st,
    "Logins: khawaja/App159earance.VnT | administrator/0568116899",
    "Downloads: install_vnt_agent.bat, vnt_device_agent.py, extension guide",
    "Asusi7: VNT Agent install attempted via SSH",
    "Public IP: needs router port forward 8080->192.168.10.96:8080",
]))

print("\n"+"="*55)
print("DONE")
print("Portal: http://192.168.10.96:8080/")
print("Login: khawaja / App159earance.VnT")
print("Portal service: "+portal_st)
print("="*55)
