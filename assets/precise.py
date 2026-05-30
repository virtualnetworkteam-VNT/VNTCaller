
import subprocess, os, json, datetime, base64, urllib.request, time, ast

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"

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

out=[]
def log(m): out.append(m); print(m)

log("="*55)
log("PRECISE FIX: ZEUS CRASH, MIA UNIT, LANGGRAPH FOLDER")
log("="*55)

# 1. ZEUS - old zeus.py crashes. See exact error, then replace with clean one.
log("\n[1] Zeus - capturing exact crash...")
run(["sudo","systemctl","stop","zeus-agent"],timeout=10)
run("fuser -k 7777/tcp 2>/dev/null",shell=True)
time.sleep(2)
# Run old zeus.py manually to see crash
old_out,old_err=run("timeout 6 python3 /home/k/zeus-agent/zeus.py 2>&1 | head -15",shell=True,timeout=10)
log(f"  Old zeus.py crash:\n{(old_out+old_err)[:400]}")

# Replace with clean zeus-agent.py and update unit
clean_zeus=chr(10).join(["#!/usr/bin/env python3",
    "import json,datetime,subprocess,http.server,socketserver,os,urllib.request",
    "NAME='Zeus';ROLE='IT Director';PORT=7777",
    "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
    "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'",
    "BRAIN='/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json'",
    "def save(e):",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
    "    try:open(MP,'a').write('\\n### Zeus ['+ts+']\\n'+str(e)+'\\n')",
    "    except:pass",
    "def llm(task):",
    "    try:cfg=json.load(open(CFG));groq=cfg.get('groq_key','')",
    "    except:return 'Zeus done'",
    "    if not groq:return 'Zeus done'",
    "    try:b=json.load(open(BRAIN)) if os.path.exists(BRAIN) else {};model=b.get('active_model','llama-3.3-70b-versatile')",
    "    except:model='llama-3.3-70b-versatile'",
    "    msgs=[{'role':'system','content':'You are Zeus, IT Director at VNT World AI Division. Report to Alias. Handle IT, servers, infrastructure, cybersecurity. Concise.'},{'role':'user','content':task}]",
    "    r=subprocess.run(['curl','-s','-X','POST','https://api.groq.com/openai/v1/chat/completions',",
    "        '-H','Authorization: Bearer '+groq,'-H','Content-Type: application/json',",
    "        '-d',json.dumps({'model':model,'messages':msgs,'max_tokens':200,'temperature':0.7})],",
    "        capture_output=True,text=True,timeout=20)",
    "    try:return json.loads(r.stdout)['choices'][0]['message']['content'].strip()",
    "    except:return 'Zeus processed'",
    "def handle_task(task):",
    "    tl=task.lower()",
    "    if 'send whatsapp' in tl:",
    "        try:",
    "            num=task.split('to Ryan ')[1].split(':')[0].strip() if 'to Ryan ' in task else '+966568116899'",
    "            msg=task.split(': ',1)[1] if ': ' in task else task",
    "            cfg=json.load(open(CFG))",
    "            subprocess.run(['curl','-s','-X','POST','http://127.0.0.1:3001',",
    "                '-H','Content-Type: application/json',",
    "                '-d',json.dumps({'to':num,'message':msg})],capture_output=True,timeout=10)",
    "            return 'WhatsApp sent'",
    "        except:return 'WhatsApp failed'",
    "    if 'restart' in tl:",
    "        for word in tl.split():",
    "            if word.endswith('-agent') or word in ['nextcloud','smbd']:",
    "                subprocess.run(['sudo','systemctl','restart',word],capture_output=True,timeout=15)",
    "                return 'Restarted '+word",
    "    return llm(task)",
    "class H(http.server.BaseHTTPRequestHandler):",
    "    def log_message(self,*a):pass",
    "    def do_GET(self):",
    "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
    "        self.wfile.write(json.dumps({'agent':'Zeus','role':'IT Director','status':'active','port':7777}).encode())",
    "    def do_POST(self):",
    "        try:n=int(self.headers.get('Content-Length',0));d=json.loads(self.rfile.read(n));task=d.get('task','')",
    "        except:task=''",
    "        save('Task: '+task[:60]);result=handle_task(task);save('Done: '+str(result)[:60])",
    "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
    "        self.wfile.write(json.dumps({'result':result,'agent':'Zeus'}).encode())",
    "socketserver.TCPServer.allow_reuse_address=True",
    "save('Zeus :7777 started');print('Zeus :7777')",
    "try:http.server.HTTPServer(('0.0.0.0',7777),H).serve_forever()",
    "except Exception as e:save('Zeus crash: '+str(e));raise"])
try:
    ast.parse(clean_zeus)
    open("/home/k/zeus-agent.py","w").write(clean_zeus)
    os.chmod("/home/k/zeus-agent.py",0o755)
    # Force unit to new path
    unit=chr(10).join(["[Unit]","Description=VNT Zeus IT Director","After=network.target","",
        "[Service]","User=k","ExecStart=/usr/bin/python3 /home/k/zeus-agent.py",
        "Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
        "[Install]","WantedBy=multi-user.target"])
    open("/tmp/zeus-agent.service","w").write(unit)
    run(["sudo","cp","/tmp/zeus-agent.service","/etc/systemd/system/zeus-agent.service"])
    run(["sudo","systemctl","daemon-reload"])
    run("fuser -k 7777/tcp 2>/dev/null",shell=True)
    time.sleep(2)
    run(["sudo","systemctl","restart","zeus-agent"],timeout=12)
    time.sleep(4)
    zh,_=run("curl -s --connect-timeout 3 http://127.0.0.1:7777/ 2>/dev/null",shell=True,timeout=5)
    log(f"  Zeus now: {'OK '+zh[:60] if zh else 'still DOWN'}")
except SyntaxError as e:
    log(f"  Zeus syntax error L{e.lineno}")

# 2. MIA - unit not registering. Write directly and force.
log("\n[2] Mia - forcing service registration...")
# Verify mia-agent.py exists and is valid
if os.path.exists("/home/k/mia-agent.py"):
    try:
        ast.parse(open("/home/k/mia-agent.py").read())
        log("  mia-agent.py: valid")
    except SyntaxError as e:
        log(f"  mia-agent.py BROKEN L{e.lineno} - rewriting")
        # Rewrite clean
        mia=chr(10).join(["#!/usr/bin/env python3",
            "import json,datetime,subprocess,http.server,socketserver,os",
            "NAME='Mia';ROLE='Receptionist';PORT=9999",
            "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
            "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'",
            "def save(e):",
            "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
            "    try:open(MP,'a').write('\\n### Mia ['+ts+']\\n'+str(e)+'\\n')",
            "    except:pass",
            "def llm(task):",
            "    try:cfg=json.load(open(CFG));groq=cfg.get('groq_key','')",
            "    except:return 'Mia here'",
            "    if not groq:return 'Mia here'",
            "    msgs=[{'role':'system','content':'You are Mia, friendly Receptionist at VNT World AI Division. Warm professional. Report to Alias.'},{'role':'user','content':task}]",
            "    r=subprocess.run(['curl','-s','-X','POST','https://api.groq.com/openai/v1/chat/completions',",
            "        '-H','Authorization: Bearer '+groq,'-H','Content-Type: application/json',",
            "        '-d',json.dumps({'model':'llama-3.3-70b-versatile','messages':msgs,'max_tokens':150,'temperature':0.7})],",
            "        capture_output=True,text=True,timeout=20)",
            "    try:return json.loads(r.stdout)['choices'][0]['message']['content'].strip()",
            "    except:return 'Mia processed'",
            "class H(http.server.BaseHTTPRequestHandler):",
            "    def log_message(self,*a):pass",
            "    def do_GET(self):",
            "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
            "        self.wfile.write(json.dumps({'agent':'Mia','role':'Receptionist','status':'active','voice':'en-US-AriaNeural'}).encode())",
            "    def do_POST(self):",
            "        try:n=int(self.headers.get('Content-Length',0));d=json.loads(self.rfile.read(n));task=d.get('task','')",
            "        except:task=''",
            "        save('Task: '+task[:60]);result=llm(task)",
            "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
            "        self.wfile.write(json.dumps({'result':result,'agent':'Mia'}).encode())",
            "socketserver.TCPServer.allow_reuse_address=True",
            "save('Mia :9999 started');print('Mia :9999')",
            "try:http.server.HTTPServer(('0.0.0.0',9999),H).serve_forever()",
            "except Exception as e:save('Mia crash: '+str(e));raise"])
        open("/home/k/mia-agent.py","w").write(mia)
        os.chmod("/home/k/mia-agent.py",0o755)
else:
    log("  mia-agent.py MISSING")

# Force-create the unit file
unit=chr(10).join(["[Unit]","Description=VNT Mia Receptionist","After=network.target","",
    "[Service]","User=k","ExecStart=/usr/bin/python3 /home/k/mia-agent.py",
    "Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
    "[Install]","WantedBy=multi-user.target"])
open("/tmp/mia-agent.service","w").write(unit)
run(["sudo","cp","/tmp/mia-agent.service","/etc/systemd/system/mia-agent.service"])
run(["sudo","systemctl","daemon-reload"])
run(["sudo","systemctl","enable","mia-agent"])
run("fuser -k 9999/tcp 2>/dev/null",shell=True)
time.sleep(2)
run(["sudo","systemctl","start","mia-agent"],timeout=12)
time.sleep(4)
mh,_=run("curl -s --connect-timeout 3 http://127.0.0.1:9999/ 2>/dev/null",shell=True,timeout=5)
log(f"  Mia now: {'OK '+mh[:60] if mh else 'still DOWN'}")
if not mh:
    merr,_=run("journalctl -u mia-agent -n 6 --no-pager --quiet",shell=True)
    log(f"  Mia error: {merr[-200:]}")

# 3. LANGGRAPH - delete corrupt folder completely, reinstall
log("\n[3] LangGraph - removing corrupt folder...")
run("rm -rf /home/k/.local/lib/python3.12/site-packages/langgraph 2>/dev/null",shell=True)
run("rm -rf /home/k/.local/lib/python3.12/site-packages/langgraph-* 2>/dev/null",shell=True)
run("pip cache purge 2>/dev/null",shell=True,timeout=30)
r,e=run("pip install --no-cache-dir langgraph --break-system-packages 2>&1 | tail -2",shell=True,timeout=180)
log(f"  Install: {(r+e)[-150:]}")
lg,_=run("cd /tmp && python3 -c 'import langgraph;print(langgraph.__version__)' 2>&1",shell=True)
log(f"  LangGraph: {lg[:80]}")

# 4. WhatsApp
log("\n[4] WhatsApp...")
wa,_=run(["systemctl","--user","is-active","alias-whatsapp"])
if wa!="active":
    run(["systemctl","--user","restart","alias-whatsapp"])
    time.sleep(3)
    wa,_=run(["systemctl","--user","is-active","alias-whatsapp"])
log(f"  WhatsApp: {wa}")

# 5. FINAL ALL 16
log("\n[5] Final test...")
ok=0;down=[]
for name,port in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),
                  ("Julian",7780),("Ethan",7781),("Lee",7782),("Amr",7783),
                  ("Nova",7784),("Specter",7788),("Luc",7787),("Ben",7789),
                  ("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999)]:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
    else:down.append(name)
    log(f"  {name} :{port}: {'OK' if h else 'DOWN'}")
log(f"\n  TOTAL: {ok}/16 | Down: {down} | WhatsApp: {wa} | LangGraph: {lg[:20]}")

full="\n".join(out)
push_result("precise_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
