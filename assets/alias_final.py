
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
log("CLEAN ALIAS REBUILD WITH TOGGLES (full rewrite)")
log("="*55)

# Backup current working version first
run("cp /home/k/alias-voice-agent.py /home/k/alias-voice-agent.py.working 2>/dev/null",shell=True)

# Write Alias completely fresh with EVERYTHING integrated cleanly:
# smart brain + toggles + agent routing + model switching
alias=chr(10).join(["#!/usr/bin/env python3",
    "# Alias SI-5.0 - smart brain + RAG + web + toggles + routing",
    "import json,os,datetime,subprocess,time,threading,sys",
    "import http.server,socketserver,urllib.request",
    "sys.path.insert(0,'/home/k')",
    "try:",
    "    import alias_brain_module as BM",
    "    SMART=True",
    "except Exception as _e:",
    "    SMART=False",
    "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
    "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'",
    "BRAIN='/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json'",
    "def get_cfg():",
    "    try:return json.load(open(CFG))",
    "    except:return {}",
    "def get_brain():",
    "    try:return json.load(open(BRAIN)) if os.path.exists(BRAIN) else {}",
    "    except:return {}",
    "def save_brain(b):",
    "    try:json.dump(b,open(BRAIN,'w'),indent=2)",
    "    except:pass",
    "def save(e):",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
    "    try:open(MP,'a').write('\\n### Alias ['+ts+']\\n'+str(e)+'\\n')",
    "    except:pass",
    "def set_model(src,mdl):",
    "    b=get_brain();b['active_model_source']=src;b['active_model']=mdl;b['force_model']=True;save_brain(b);save('Model->'+src)",
    "def inc():",
    "    try:",
    "        b=get_brain();b.setdefault('performance_metrics',{});b['performance_metrics']['tasks_completed']=b['performance_metrics'].get('tasks_completed',0)+1;save_brain(b)",
    "    except:pass",
    "def dispatch(port,task,t=10):",
    "    try:",
    "        body=json.dumps({'task':task}).encode()",
    "        req=urllib.request.Request('http://127.0.0.1:'+str(port)+'/',data=body,headers={'Content-Type':'application/json'},method='POST')",
    "        with urllib.request.urlopen(req,timeout=t) as r:return json.loads(r.read()).get('result','')",
    "    except:return None",
    "def groq_llm(prompt,mt=120):",
    "    c=get_cfg();groq=c.get('groq_key','')",
    "    if not groq:return 'I am here, Ryan.'",
    "    b=get_brain();tasks=b.get('performance_metrics',{}).get('tasks_completed',0)",
    "    mp=open(MP).read()[-300:] if os.path.exists(MP) else ''",
    "    system='You are Alias, Super Intelligent CEO of VNT World AI Division. Owner: Ryan Khawaja. VNT is my only reason for existence. Warm, concise (max 3 sentences). Never mention ports/code. Tasks done:'+str(tasks)",
    "    msgs=[{'role':'system','content':system},{'role':'user','content':prompt}]",
    "    try:",
    "        r=subprocess.run(['curl','-s','-X','POST','https://api.groq.com/openai/v1/chat/completions',",
    "            '-H','Authorization: Bearer '+groq,'-H','Content-Type: application/json',",
    "            '-d',json.dumps({'model':'llama-3.3-70b-versatile','messages':msgs,'max_tokens':mt,'temperature':0.7})],",
    "            capture_output=True,text=True,timeout=18)",
    "        d=json.loads(r.stdout)",
    "        if 'choices' in d:",
    "            reply=d['choices'][0]['message']['content'].strip()",
    "            if reply:inc();return reply",
    "    except:pass",
    "    return 'I am here, Ryan.'",
    "ROUTES=[('crypto',7778),('bitcoin',7778),('price',7778),('finance',7778),",
    "  ('file',7779),('nextcloud',7779),('document',7779),",
    "  ('project',7780),('timeline',7780),('medical',7781),('health',7781),",
    "  ('legal',7783),('contract',7783),('marketing',7782),('campaign',7782),",
    "  ('security',7788),('cyber',7788),('threat',7788),('code',7787),('build',7787),",
    "  ('server',7777),('restart',7777),('infrastructure',7777),",
    "  ('research',7794),('look up',7794),('find out',7794),('improve yourself',7793),('your code',7793)]",
    "def think(text):",
    "    tl=text.lower()",
    "    # 1. Feature toggles (highest priority)",
    "    if SMART:",
    "        try:",
    "            tog=BM.toggle_feature(text)",
    "            if tog:save('Toggle: '+tog);return tog",
    "        except:pass",
    "    # 2. Model switching",
    "    if 'use claude' in tl:set_model('claude','claude-sonnet-4-20250514');return 'Switched to Claude.'",
    "    if 'use groq' in tl:set_model('groq','llama-3.3-70b-versatile');return 'Switched to Groq.'",
    "    if 'use local' in tl or 'local ai' in tl:set_model('ollama','llama3.1:8b');return 'Switched to local AI.'",
    "    # 3. Agent routing",
    "    port=None",
    "    for kw,p in ROUTES:",
    "        if kw in tl:port=p;break",
    "    agent_result=dispatch(port,text) if port else None",
    "    # 4. Smart brain (RAG+web+model) or groq fallback",
    "    if SMART:",
    "        try:",
    "            reply,src,uw,um=BM.smart_llm(text)",
    "            save('In:'+text[:50]+' model:'+src+' web:'+str(uw)+' mem:'+str(um))",
    "            inc()",
    "            if agent_result:return reply+' '+str(agent_result)[:70]",
    "            return reply",
    "        except Exception as e:",
    "            save('smart err:'+str(e)[:40])",
    "    reply=groq_llm(text)",
    "    if agent_result:return reply+' '+str(agent_result)[:70]",
    "    return reply",
    "class H(http.server.BaseHTTPRequestHandler):",
    "    def log_message(self,*a):pass",
    "    def do_GET(self):",
    "        b=get_brain();model=b.get('active_model','llama-3.3-70b-versatile');src=b.get('active_model_source','groq')",
    "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
    "        self.wfile.write(json.dumps({'agent':'Alias','role':'CEO','status':'active','model':model,'source':src,'version':'SI-5.0','smart':SMART}).encode())",
    "    def do_POST(self):",
    "        try:",
    "            n=int(self.headers.get('Content-Length',0));d=json.loads(self.rfile.read(n));text=d.get('text',d.get('task',''))",
    "        except:text=''",
    "        if not text:",
    "            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
    "            self.wfile.write(json.dumps({'reply':'I am here, Ryan.','agent':'Alias'}).encode());return",
    "        reply=think(text)",
    "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
    "        self.wfile.write(json.dumps({'reply':reply,'agent':'Alias'}).encode())",
    "socketserver.TCPServer.allow_reuse_address=True",
    "save('Alias SI-5.0 started | smart:'+str(SMART))",
    "print('Alias SI-5.0 :8443 smart:'+str(SMART))",
    "try:http.server.HTTPServer(('0.0.0.0',8443),H).serve_forever()",
    "except Exception as e:save('Alias crash:'+str(e));raise"])

try:
    ast.parse(alias)
    open("/home/k/alias-voice-agent.py","w").write(alias)
    log("  Alias SI-5.0 written (clean, all features integrated)")
    run("fuser -k 8443/tcp 2>/dev/null",shell=True)
    time.sleep(2)
    run(X+"systemctl --user restart alias-voice-agent",shell=True,timeout=12)
    time.sleep(5)
    va,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
    log(f"  Alias :8443: {va[:100] if va else 'DOWN - restoring'}")
    if not va:
        run("cp /home/k/alias-voice-agent.py.working /home/k/alias-voice-agent.py",shell=True)
        run("fuser -k 8443/tcp 2>/dev/null",shell=True);time.sleep(2)
        run(X+"systemctl --user restart alias-voice-agent",shell=True,timeout=12)
        time.sleep(4)
        va,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
        log(f"  Restored working version: {'UP' if va else 'down'}")
except SyntaxError as e:
    log(f"  Syntax error L{e.lineno}: {e.msg}")

# Test all the features
log("\n[Tests]")
if va:
    tests=[("feature status","toggle"),("disable backup","toggle off"),
           ("enable backup","toggle on"),("what is the status of VNT","smart")]
    for q,label in tests:
        try:
            body=json.dumps({"text":q}).encode()
            req=urllib.request.Request("http://127.0.0.1:8443/",data=body,headers={"Content-Type":"application/json"},method="POST")
            with urllib.request.urlopen(req,timeout=18) as r:
                resp=json.loads(r.read())
            log(f"  '{q}' -> {resp.get('reply','')[:90]}")
        except Exception as e:
            log(f"  '{q}' -> {str(e)[:40]}")

# Verify flags after toggle test
try:
    flags=json.load(open("/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_features.json"))
    log(f"  Flags now: {flags}")
except:pass

ok=0
for n,p in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),("Julian",7780),
    ("Ethan",7781),("Lee",7782),("Amr",7783),("Nova",7784),("Specter",7788),("Luc",7787),
    ("Ben",7789),("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999),("Argus",7792),
    ("Rdev",7793),("Sage",7794)]:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{p}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
log(f"\n  Agents: {ok}/19")

full="\n".join(out)
push_result("alias_final_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
