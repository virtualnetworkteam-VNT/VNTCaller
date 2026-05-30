
import subprocess, os, json, datetime, base64, urllib.request, time, ast

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"
MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
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
ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

log("="*55)
log("FIX: WEB, PORTAL, MEDIA, SMBD + NEW AGENTS")
log("="*55)
os.makedirs(USER_DIR,exist_ok=True)
X="XDG_RUNTIME_DIR=/run/user/1000 "

# 1. WEB SERVER :8888 - simple python http.server as user service
log("\n[1] Fixing web server :8888...")
run("fuser -k 8888/tcp 2>/dev/null",shell=True)
run(X+"systemctl --user stop vnt-webserver 2>/dev/null",shell=True)
run("echo '116899' | sudo -S systemctl stop vnt-webserver 2>/dev/null",shell=True,timeout=8)
time.sleep(2)
# Write a robust web server script
web_lines=["#!/usr/bin/env python3",
    "import http.server,socketserver,os",
    "os.chdir('/home/k/vnt-web')",
    "socketserver.TCPServer.allow_reuse_address=True",
    "PORT=8888",
    "Handler=http.server.SimpleHTTPRequestHandler",
    "print('Web server :8888 serving /home/k/vnt-web')",
    "with socketserver.TCPServer(('0.0.0.0',PORT),Handler) as httpd:",
    "    httpd.serve_forever()"]
open("/home/k/vnt-webserver.py","w").write(chr(10).join(web_lines))
uservice("vnt-webserver","/usr/bin/python3 /home/k/vnt-webserver.py","VNT Web Server")
run(X+"systemctl --user daemon-reload",shell=True)
run(X+"systemctl --user enable vnt-webserver",shell=True)
run("fuser -k 8888/tcp 2>/dev/null",shell=True)
time.sleep(2)
run(X+"systemctl --user restart vnt-webserver",shell=True,timeout=12)
time.sleep(4)
hier,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8888/vnt_hierarchy.html 2>/dev/null | head -c 50",shell=True,timeout=5)
log(f"  Hierarchy: {'OK SERVING' if hier else 'still down'}")
media_pg,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8888/media.html 2>/dev/null | head -c 50",shell=True,timeout=5)
log(f"  Media studio page: {'OK SERVING' if media_pg else 'page missing'}")

# 2. PORTAL :8080
log("\n[2] Fixing portal :8080...")
if os.path.exists("/home/k/vnt-portal.py"):
    try:
        ast.parse(open("/home/k/vnt-portal.py").read())
        run("fuser -k 8080/tcp 2>/dev/null",shell=True)
        uservice("vnt-portal","/usr/bin/python3 /home/k/vnt-portal.py","VNT Portal")
        run(X+"systemctl --user daemon-reload",shell=True)
        run(X+"systemctl --user enable vnt-portal",shell=True)
        time.sleep(2)
        run(X+"systemctl --user restart vnt-portal",shell=True,timeout=12)
        time.sleep(4)
        portal,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8080/ 2>/dev/null | head -c 50",shell=True,timeout=5)
        log(f"  Portal: {'OK' if portal else 'down'}")
    except SyntaxError as e:
        log(f"  Portal script broken L{e.lineno}")
else:
    log("  Portal script missing - skipping")

# 3. MEDIA API on M4 - restart via SSH to Mac
log("\n[3] Restarting Media API :3333 on M4...")
def ssh_m4(cmd,t=20):
    return run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 Alias@192.168.10.94 \""+cmd+"\"",shell=True,timeout=t)
m4,_=ssh_m4("echo OK")
if "OK" in m4:
    log("  M4 SSH: connected")
    # Find media server script
    find_media,_=ssh_m4("ls ~/ai-media/*.py ~/media-api/*.py ~/*media* 2>/dev/null | head -5")
    log(f"  Media scripts: {find_media[:150]}")
    # Kill old and restart media API
    ssh_m4("pkill -f 'media' 2>/dev/null; pkill -f ':3333' 2>/dev/null")
    time.sleep(2)
    # Try common media server locations with the venv python
    PY="/Users/alias/miniforge3/envs/vnt/bin/python"
    for script in ["~/ai-media/media_api.py","~/media-api/server.py","~/ai-media/server.py","~/media_server.py"]:
        check,_=ssh_m4(f"test -f {script} && echo EXISTS")
        if "EXISTS" in check:
            ssh_m4(f"nohup {PY} {script} > /tmp/media.log 2>&1 &")
            log(f"  Started: {script}")
            break
    time.sleep(4)
    media_api,_=run("curl -s --connect-timeout 4 http://192.168.10.94:3333/ 2>/dev/null | head -c 60",shell=True,timeout=6)
    log(f"  Media API :3333: {'OK '+media_api[:40] if media_api else 'still down - check /tmp/media.log on M4'}")
else:
    log(f"  M4 SSH failed: {m4[:40]}")

# 4. SMBD - fix with sudo -S
log("\n[4] Fixing smbd...")
run("echo '116899' | sudo -S systemctl restart smbd 2>/dev/null",shell=True,timeout=10)
time.sleep(2)
smbd,_=run("systemctl is-active smbd 2>&1",shell=True)
log(f"  smbd: {smbd}")
if smbd!="active":
    smbd_err,_=run("echo '116899' | sudo -S journalctl -u smbd -n 5 --no-pager 2>/dev/null",shell=True,timeout=8)
    log(f"  smbd error: {smbd_err[-200:]}")
    # Maybe not installed
    inst,_=run("which smbd 2>/dev/null",shell=True)
    if not inst:
        log("  smbd not installed - installing...")
        run("echo '116899' | sudo -S apt-get install -y samba 2>/dev/null | tail -1",shell=True,timeout=120)
        run("echo '116899' | sudo -S systemctl restart smbd 2>/dev/null",shell=True,timeout=10)
        time.sleep(2)
        smbd,_=run("systemctl is-active smbd 2>&1",shell=True)
        log(f"  smbd after install: {smbd}")

# 5. NEW MONITORING AGENT - "Argus" (takes monitoring load off Zeus)
log("\n[5] Creating Argus monitoring agent (:7792)...")
argus_lines=["#!/usr/bin/env python3",
    "# Argus - Dedicated Monitoring Agent. Reports to Alias. Frees Zeus for IT work.",
    "import json,datetime,subprocess,http.server,socketserver,os,time,threading,urllib.request",
    "NAME='Argus';PORT=7792",
    "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
    "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'",
    "WEB='/home/k/vnt-web'",
    "def save(e):",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
    "    try:open(MP,'a').write('\\n### Argus ['+ts+']\\n'+str(e)+'\\n')",
    "    except:pass",
    "AGENTS=[('Alias',8443),('Zeus',7777),('Maya',7778),('Ava',7779),('Julian',7780),",
    "  ('Ethan',7781),('Lee',7782),('Amr',7783),('Nova',7784),('Specter',7788),",
    "  ('Luc',7787),('Ben',7789),('Dina',7786),('Jodi',7790),('Rick',7791),('Mia',9999)]",
    "STATE={'last_check':'','agents_up':0,'history':[]}",
    "def check_all():",
    "    up=0;down=[]",
    "    for name,port in AGENTS:",
    "        try:",
    "            urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/',timeout=2);up+=1",
    "        except:down.append(name)",
    "    return up,down",
    "def build_dashboard():",
    "    up,down=check_all()",
    "    STATE['agents_up']=up;STATE['last_check']=datetime.datetime.now().strftime('%H:%M:%S')",
    "    # services",
    "    svcs={}",
    "    for s,port in [('Web',8888),('Portal',8080),('Media-M4',3333),('Nextcloud',80)]:",
    "        host='192.168.10.94' if s=='Media-M4' else ('192.168.10.10' if s=='Nextcloud' else '127.0.0.1')",
    "        try:urllib.request.urlopen('http://'+host+':'+str(port)+'/',timeout=2);svcs[s]=True",
    "        except:svcs[s]=False",
    "    rows=''",
    "    for name,port in AGENTS:",
    "        a=name not in down;dot='#3fb950' if a else '#f85149';st='Online' if a else 'Offline'",
    "        rows+='<tr><td><span class=d style=\"background:'+dot+'\"></span></td><td>'+name+'</td><td class=p>:'+str(port)+'</td><td style=\"color:'+dot+'\">'+st+'</td></tr>'",
    "    srows=''",
    "    for s,ok2 in svcs.items():",
    "        dot='#3fb950' if ok2 else '#f85149';st='Up' if ok2 else 'Down'",
    "        srows+='<div class=sc><span class=d style=\"background:'+dot+'\"></span> '+s+': <b style=\"color:'+dot+'\">'+st+'</b></div>'",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')",
    "    html='<!DOCTYPE html><html><head><meta charset=UTF-8><title>VNT Monitor</title>'",
    "    html+='<style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0a0e14;color:#c9d1d9;font-family:Segoe UI,sans-serif;padding:0}'",
    "    html+='.hd{background:linear-gradient(90deg,#161b22,#1c2333);padding:16px 28px;border-bottom:2px solid #1f6feb;display:flex;justify-content:space-between;align-items:center}'",
    "    html+='.lo{font-size:19px;font-weight:800;color:#58a6ff;letter-spacing:1px}.sub{font-size:11px;color:#6e7681;margin-top:2px}'",
    "    html+='.big{display:flex;gap:28px}.bn{text-align:center}.bnum{font-size:26px;font-weight:800}.blab{font-size:9px;color:#6e7681;text-transform:uppercase;letter-spacing:1px}'",
    "    html+='.wrap{padding:20px 28px;display:grid;grid-template-columns:2fr 1fr;gap:20px}'",
    "    html+='table{width:100%;border-collapse:collapse;background:#0d1117;border:1px solid #21262d;border-radius:8px;overflow:hidden}'",
    "    html+='th{background:#161b22;color:#6e7681;font-size:10px;text-transform:uppercase;padding:9px 14px;text-align:left}'",
    "    html+='td{padding:9px 14px;border-bottom:1px solid #161b22;font-size:13px}tr:hover{background:#161b22}'",
    "    html+='.d{display:inline-block;width:9px;height:9px;border-radius:50%}.p{font-family:monospace;color:#484f58;font-size:11px}'",
    "    html+='.panel{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:16px}.panel h3{font-size:11px;color:#6e7681;text-transform:uppercase;margin-bottom:12px}'",
    "    html+='.sc{padding:7px 0;font-size:13px;border-bottom:1px solid #161b22}.qa a{display:block;padding:8px 12px;margin:4px 0;background:#161b22;border:1px solid #21262d;border-radius:6px;color:#58a6ff;text-decoration:none;font-size:12px}'",
    "    html+='.ft{padding:12px 28px;text-align:center;color:#30363d;font-size:10px;border-top:1px solid #161b22}</style>'",
    "    html+='<script>setTimeout(()=>location.reload(),30000)</script></head><body>'",
    "    html+='<div class=hd><div><div class=lo>VNT MONITORING CENTER</div><div class=sub>Argus Agent | auto-refresh 30s | '+ts+'</div></div>'",
    "    html+='<div class=big><div class=bn><div class=bnum style=\"color:#3fb950\">'+str(up)+'</div><div class=blab>Agents Up</div></div>'",
    "    html+='<div class=bn><div class=bnum style=\"color:#f85149\">'+str(len(down))+'</div><div class=blab>Down</div></div>'",
    "    html+='<div class=bn><div class=bnum style=\"color:#58a6ff\">16</div><div class=blab>Total</div></div></div></div>'",
    "    html+='<div class=wrap><div class=panel><h3>Agent Fleet</h3><table><tr><th></th><th>Agent</th><th>Port</th><th>Status</th></tr>'+rows+'</table></div>'",
    "    html+='<div><div class=panel style=\"margin-bottom:20px\"><h3>Services</h3>'+srows+'</div>'",
    "    html+='<div class=panel qa><h3>Quick Access</h3>'",
    "    html+='<a href=\"http://192.168.10.96:8080/\">VNT Portal</a>'",
    "    html+='<a href=\"http://192.168.10.96:8888/vnt_hierarchy.html\">Hierarchy</a>'",
    "    html+='<a href=\"http://192.168.10.96:8888/media.html\">Media Studio</a>'",
    "    html+='<a href=\"http://192.168.10.10/\">Nextcloud</a></div></div></div>'",
    "    html+='<div class=ft>VNT World AI Division | Argus Monitoring | Reports to Alias</div></body></html>'",
    "    try:open(WEB+'/monitor.html','w').write(html)",
    "    except:pass",
    "    return up,down",
    "def loop():",
    "    while True:",
    "        try:",
    "            up,down=build_dashboard()",
    "            if down:save('Monitor: '+str(len(down))+' down: '+str(down))",
    "        except Exception as e:save('Argus loop err: '+str(e)[:50])",
    "        time.sleep(30)",
    "threading.Thread(target=loop,daemon=True).start()",
    "class H(http.server.BaseHTTPRequestHandler):",
    "    def log_message(self,*a):pass",
    "    def do_GET(self):",
    "        up,down=check_all()",
    "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
    "        self.wfile.write(json.dumps({'agent':'Argus','role':'Monitoring','status':'active','agents_up':up,'down':down}).encode())",
    "    def do_POST(self):",
    "        up,down=check_all()",
    "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
    "        self.wfile.write(json.dumps({'result':str(up)+'/16 agents up. Down: '+str(down),'agent':'Argus'}).encode())",
    "socketserver.TCPServer.allow_reuse_address=True",
    "save('Argus monitoring :7792 started');print('Argus :7792')",
    "try:http.server.HTTPServer(('0.0.0.0',7792),H).serve_forever()",
    "except Exception as e:save('Argus crash: '+str(e));raise"]
argus_code=chr(10).join(argus_lines)
try:
    ast.parse(argus_code)
    open("/home/k/argus-agent.py","w").write(argus_code)
    os.chmod("/home/k/argus-agent.py",0o755)
    uservice("argus-agent","/usr/bin/python3 /home/k/argus-agent.py","VNT Argus Monitoring")
    run(X+"systemctl --user daemon-reload",shell=True)
    run(X+"systemctl --user enable argus-agent",shell=True)
    run("fuser -k 7792/tcp 2>/dev/null",shell=True)
    time.sleep(2)
    run(X+"systemctl --user restart argus-agent",shell=True,timeout=12)
    time.sleep(4)
    ag,_=run("curl -s --connect-timeout 3 http://127.0.0.1:7792/ 2>/dev/null",shell=True,timeout=5)
    log(f"  Argus :7792: {'OK '+ag[:60] if ag else 'down'}")
    mon_pg,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8888/monitor.html 2>/dev/null | head -c 40",shell=True,timeout=5)
    log(f"  Monitor dashboard: {'OK at :8888/monitor.html' if mon_pg else 'building...'}")
except SyntaxError as e:
    log(f"  Argus syntax error L{e.lineno}: {e.msg}")

# FINAL
log("\n[6] Final status...")
ok=0
for name,port in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),("Julian",7780),
    ("Ethan",7781),("Lee",7782),("Amr",7783),("Nova",7784),("Specter",7788),("Luc",7787),
    ("Ben",7789),("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999),("Argus",7792)]:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
web,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8888/vnt_hierarchy.html 2>/dev/null | head -c 20",shell=True,timeout=5)
portal,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8080/ 2>/dev/null | head -c 20",shell=True,timeout=5)
media,_=run("curl -s --connect-timeout 4 http://192.168.10.94:3333/ 2>/dev/null | head -c 20",shell=True,timeout=6)
smbd,_=run("systemctl is-active smbd 2>&1",shell=True)
log(f"  Agents: {ok}/17 (incl Argus)")
log(f"  Web/Hierarchy: {'OK' if web else 'down'} | Portal: {'OK' if portal else 'down'}")
log(f"  Media M4: {'OK' if media else 'down'} | smbd: {smbd}")

full="\n".join(out)
push_result("fixall_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
