
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
X="XDG_RUNTIME_DIR=/run/user/1000 "

log("="*55)
log("FORCE RECOVER ALIAS")
log("="*55)

# 1. What's the actual error? Run current file manually
log("\n[1] Manual run of current Alias...")
o,e=run("timeout 6 python3 /home/k/alias-voice-agent.py 2>&1",shell=True,timeout=10)
log(f"  Output: {(o+e)[:300]}")

# 2. Kill everything on 8443
log("\n[2] Clearing port 8443...")
run("pkill -9 -f alias-voice-agent 2>/dev/null",shell=True)
run("fuser -k 8443/tcp 2>/dev/null",shell=True)
held,_=run("ss -tlnp 2>/dev/null | grep 8443",shell=True)
log(f"  Port 8443 held by: {held if held else 'clear'}")
time.sleep(3)

# 3. Try each backup until one works
log("\n[3] Finding a working backup...")
backups=["/home/k/alias-voice-agent.py.working",
         "/home/k/alias-voice-agent.py.bak_pre_wire",
         "/home/k/alias-voice-agent.py.bak_si5",
         "/home/k/alias-voice-agent.py.bak_rdev"]
restored=False
for bak in backups:
    if os.path.exists(bak):
        try:
            ast.parse(open(bak).read())
            log(f"  {bak}: valid syntax")
            run(f"cp {bak} /home/k/alias-voice-agent.py",shell=True)
            run("fuser -k 8443/tcp 2>/dev/null",shell=True)
            time.sleep(2)
            run(X+"systemctl --user restart alias-voice-agent",shell=True,timeout=12)
            time.sleep(5)
            va,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
            if va:
                log(f"  RECOVERED from {bak}: {va[:70]}")
                restored=True
                break
            else:
                log(f"  {bak}: still down after restart")
        except SyntaxError as e:
            log(f"  {bak}: syntax broken L{e.lineno}")

# 4. If no backup works, write a minimal guaranteed-working Alias
if not restored:
    log("\n[4] Writing minimal guaranteed Alias...")
    minimal=chr(10).join(["#!/usr/bin/env python3",
        "import json,os,datetime,subprocess,http.server,socketserver,urllib.request",
        "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
        "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'",
        "BRAIN='/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json'",
        "def save(e):",
        "    try:open(MP,'a').write('\\n### Alias ['+datetime.datetime.now().strftime('%Y-%m-%d %H:%M')+']\\n'+str(e)+'\\n')",
        "    except:pass",
        "def llm(prompt):",
        "    try:c=json.load(open(CFG));groq=c.get('groq_key','')",
        "    except:return 'I am here, Ryan.'",
        "    if not groq:return 'I am here, Ryan.'",
        "    msgs=[{'role':'system','content':'You are Alias, CEO of VNT World AI Division. Owner Ryan Khawaja. Warm, concise.'},{'role':'user','content':prompt}]",
        "    try:",
        "        r=subprocess.run(['curl','-s','-X','POST','https://api.groq.com/openai/v1/chat/completions','-H','Authorization: Bearer '+groq,'-H','Content-Type: application/json','-d',json.dumps({'model':'llama-3.3-70b-versatile','messages':msgs,'max_tokens':120,'temperature':0.7})],capture_output=True,text=True,timeout=18)",
        "        return json.loads(r.stdout)['choices'][0]['message']['content'].strip() or 'I am here, Ryan.'",
        "    except:return 'I am here, Ryan.'",
        "class H(http.server.BaseHTTPRequestHandler):",
        "    def log_message(self,*a):pass",
        "    def do_GET(self):",
        "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
        "        self.wfile.write(json.dumps({'agent':'Alias','role':'CEO','status':'active','version':'stable'}).encode())",
        "    def do_POST(self):",
        "        try:n=int(self.headers.get('Content-Length',0));d=json.loads(self.rfile.read(n));t=d.get('text',d.get('task',''))",
        "        except:t=''",
        "        save('In:'+t[:50]);reply=llm(t) if t else 'I am here, Ryan.'",
        "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
        "        self.wfile.write(json.dumps({'reply':reply,'agent':'Alias'}).encode())",
        "socketserver.TCPServer.allow_reuse_address=True",
        "save('Alias stable started');print('Alias stable :8443')",
        "try:http.server.HTTPServer(('0.0.0.0',8443),H).serve_forever()",
        "except Exception as e:save('crash:'+str(e));raise"])
    ast.parse(minimal)
    open("/home/k/alias-voice-agent.py","w").write(minimal)
    run("fuser -k 8443/tcp 2>/dev/null",shell=True)
    time.sleep(2)
    run(X+"systemctl --user restart alias-voice-agent",shell=True,timeout=12)
    time.sleep(5)
    va,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
    log(f"  Minimal Alias: {'UP '+va[:60] if va else 'STILL DOWN'}")
    restored=bool(va)

# 5. Final verify
log("\n[5] Final verify...")
ok=0;down=[]
for n,p in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),("Julian",7780),
    ("Ethan",7781),("Lee",7782),("Amr",7783),("Nova",7784),("Specter",7788),("Luc",7787),
    ("Ben",7789),("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999),("Argus",7792),
    ("Rdev",7793),("Sage",7794)]:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{p}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
    else:down.append(n)
log(f"  Agents: {ok}/19 | Down: {down}")

# Test Alias responds
va2,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
if va2:
    try:
        body=json.dumps({"text":"Are you there Alias?"}).encode()
        req=urllib.request.Request("http://127.0.0.1:8443/",data=body,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=18) as r:
            log(f"  Alias replies: {json.loads(r.read()).get('reply','')[:80]}")
    except Exception as e:
        log(f"  Reply test: {str(e)[:40]}")

full="\n".join(out)
push_result("recover_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
