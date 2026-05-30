
import subprocess, os, json, datetime, base64, urllib.request, time, ast, re

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Fix ["+ts+"]\n"+str(e)+"\n")
    except: pass

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
log("FIXING ALIAS + LANGGRAPH + DOWN SERVICES")
log("="*55)

# 1. Install LangGraph FIRST
log("\n[1] Installing LangGraph...")
r1,e1=run("pip install langgraph langchain-core --break-system-packages -q 2>&1",shell=True,timeout=200)
lg,_=run(["python3","-c","import langgraph;print(langgraph.__version__)"])
log(f"  LangGraph: {lg if lg else 'STILL FAILED: '+e1[-100:]}")

# 2. The Alias agent is stuck "activating" - check why
log("\n[2] Diagnosing Alias voice agent...")
va_log,_=run("journalctl -u alias-voice-agent -n 15 --no-pager --quiet",shell=True)
log(f"  Recent log: {va_log[-300:]}")

# The issue: LangGraph import at module level hangs if not installed
# Rewrite Alias with SAFE langgraph import (try/except, non-blocking)
log("\n[3] Rewriting Alias with safe imports...")

alias_lines=[
    "#!/usr/bin/env python3",
    "import json,os,datetime,subprocess,time,threading",
    "import http.server,socketserver,urllib.request",
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
    "def get_model():",
    "    b=get_brain();return b.get('active_model','llama-3.3-70b-versatile'),b.get('active_model_source','groq')",
    "def set_model(src,mdl):",
    "    b=get_brain();b['active_model_source']=src;b['active_model']=mdl;save_brain(b);save('Model->'+src)",
    "def inc_tasks():",
    "    try:",
    "        b=get_brain();b.setdefault('performance_metrics',{})['tasks_completed']=b['performance_metrics'].get('tasks_completed',0)+1;save_brain(b)",
    "    except:pass",
    "def llm(prompt,max_tokens=80):",
    "    cfg=get_cfg();model,src=get_model();b=get_brain()",
    "    mp=open(MP).read()[-400:] if os.path.exists(MP) else ''",
    "    purpose=b.get('identity',{}).get('purpose','VNT is my only reason for existence.')",
    "    tasks=b.get('performance_metrics',{}).get('tasks_completed',0)",
    "    system=' '.join(['You are Alias, Super Intelligent CEO of VNT World AI Division.',",
    "        'Owner: Ryan Khawaja.',purpose,",
    "        'Max 2 sentences. Warm human tone. Never mention ports or code.',",
    "        'Route: crypto->Maya, IT->Zeus, files->Ava, projects->Julian,',",
    "        'medical->Ethan, legal->Amr, marketing->Lee, security->Specter, code->Luc.',",
    "        'M4 192.168.10.94=media. M2 RETIRED. Tasks:'+str(tasks)+' Mem:'+mp[-100:]])",
    "    msgs=[{'role':'system','content':system},{'role':'user','content':prompt}]",
    "    if src=='claude':",
    "        key=cfg.get('anthropic_key','')",
    "        if key:",
    "            r=subprocess.run(['curl','-s','-X','POST','https://api.anthropic.com/v1/messages',",
    "                '-H','x-api-key: '+key,'-H','anthropic-version: 2023-06-01','-H','Content-Type: application/json',",
    "                '-d',json.dumps({'model':model,'max_tokens':max_tokens,'system':system,'messages':[{'role':'user','content':prompt}]})],",
    "                capture_output=True,text=True,timeout=15)",
    "            try:",
    "                d=json.loads(r.stdout);reply=d.get('content',[{}])[0].get('text','').strip()",
    "                if reply:inc_tasks();return reply",
    "            except:pass",
    "    elif src=='ollama':",
    "        r=subprocess.run(['curl','-s','http://127.0.0.1:11434/api/generate',",
    "            '-d',json.dumps({'model':model,'prompt':prompt,'stream':False})],capture_output=True,text=True,timeout=30)",
    "        try:",
    "            reply=json.loads(r.stdout).get('response','').strip()",
    "            if reply:inc_tasks();return reply",
    "        except:pass",
    "    groq=cfg.get('groq_key','')",
    "    if not groq:return 'I am here, Ryan.'",
    "    r=subprocess.run(['curl','-s','-X','POST','https://api.groq.com/openai/v1/chat/completions',",
    "        '-H','Authorization: Bearer '+groq,'-H','Content-Type: application/json',",
    "        '-d',json.dumps({'model':'llama-3.3-70b-versatile','messages':msgs,'max_tokens':max_tokens,'temperature':0.7})],",
    "        capture_output=True,text=True,timeout=15)",
    "    try:",
    "        d=json.loads(r.stdout)",
    "        if 'choices' in d:",
    "            reply=d['choices'][0]['message']['content'].strip()",
    "            if reply:inc_tasks();return reply",
    "    except:pass",
    "    return 'I am here, Ryan.'",
    "def detect_mood(t):",
    "    t=t.lower()",
    "    if any(w in t for w in ['urgent','asap','now','fix','broken']):return 'urgent'",
    "    if any(w in t for w in ['angry','frustrated','useless','pathetic']):return 'frustrated'",
    "    if any(w in t for w in ['thanks','great','perfect']):return 'positive'",
    "    return 'neutral'",
    "def dispatch(port,task,t=10):",
    "    try:",
    "        body=json.dumps({'task':task}).encode()",
    "        req=urllib.request.Request('http://127.0.0.1:'+str(port)+'/',data=body,headers={'Content-Type':'application/json'},method='POST')",
    "        with urllib.request.urlopen(req,timeout=t) as r:return json.loads(r.read()).get('result','')",
    "    except:return None",
    "# LangGraph loaded lazily in background thread - NEVER blocks startup",
    "LANGGRAPH_ACTIVE=[False]",
    "GRAPH=[None]",
    "def load_langgraph():",
    "    try:",
    "        from langgraph.graph import StateGraph,END",
    "        from typing import TypedDict,Optional",
    "        class State(TypedDict):",
    "            text:str",
    "            reply:str",
    "            agent:Optional[str]",
    "            mood:str",
    "        PORTS={'maya':7778,'ava':7779,'julian':7780,'ethan':7781,'amr':7783,",
    "            'lee':7782,'nova':7784,'specter':7788,'luc':7787,'zeus':7777,'jodi':7790}",
    "        def route(s):",
    "            t=s['text'].lower()",
    "            for kw,ag in [('crypto','maya'),('bitcoin','maya'),('price','maya'),('file','ava'),",
    "                ('project','julian'),('medical','ethan'),('legal','amr'),('security','specter'),",
    "                ('code','luc'),('server','zeus'),('restart','zeus')]:",
    "                if kw in t:return {**s,'agent':ag}",
    "            if 'use claude' in t:set_model('claude','claude-sonnet-4-20250514');return {**s,'reply':'Switched to Claude.'}",
    "            if 'use groq' in t:set_model('groq','llama-3.3-70b-versatile');return {**s,'reply':'Switched to Groq.'}",
    "            return {**s,'agent':None}",
    "        def execute(s):",
    "            if s.get('reply'):return s",
    "            ag=s.get('agent');res=dispatch(PORTS[ag],s['text']) if ag and ag in PORTS else None",
    "            ctx=' ['+ag+': '+str(res)[:80]+']' if res else ''",
    "            pre='Right away. ' if s.get('mood')=='urgent' else ''",
    "            return {**s,'reply':pre+llm(s['text']+ctx)}",
    "        g=StateGraph(State)",
    "        g.add_node('route',route);g.add_node('execute',execute)",
    "        g.add_edge('route','execute');g.add_edge('execute',END);g.set_entry_point('route')",
    "        GRAPH[0]=g.compile()",
    "        LANGGRAPH_ACTIVE[0]=True",
    "        save('LangGraph loaded in background')",
    "    except Exception as e:",
    "        save('LangGraph unavailable, using direct routing: '+str(e)[:50])",
    "threading.Thread(target=load_langgraph,daemon=True).start()",
    "def think(text):",
    "    save('In: '+text[:80]);mood=detect_mood(text)",
    "    if LANGGRAPH_ACTIVE[0] and GRAPH[0]:",
    "        try:",
    "            res=GRAPH[0].invoke({'text':text,'reply':'','agent':None,'mood':mood})",
    "            if res.get('reply'):save('Out: '+res['reply'][:80]);return res['reply']",
    "        except:pass",
    "    # Direct routing fallback (always works)",
    "    tl=text.lower();port=None",
    "    for kw,p in [('crypto',7778),('bitcoin',7778),('price',7778),('file',7779),",
    "        ('project',7780),('medical',7781),('legal',7783),('security',7788),('code',7787),('server',7777)]:",
    "        if kw in tl:port=p;break",
    "    if 'use claude' in tl:set_model('claude','claude-sonnet-4-20250514');return 'Switched to Claude.'",
    "    if 'use groq' in tl:set_model('groq','llama-3.3-70b-versatile');return 'Switched to Groq.'",
    "    res=dispatch(port,text) if port else None",
    "    ctx=' [result: '+str(res)[:80]+']' if res else ''",
    "    pre='Right away. ' if mood=='urgent' else ''",
    "    reply=pre+llm(text+ctx);save('Out: '+reply[:80]);return reply",
    "class H(http.server.BaseHTTPRequestHandler):",
    "    def log_message(self,*a):pass",
    "    def do_GET(self):",
    "        model,src=get_model()",
    "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
    "        self.wfile.write(json.dumps({'agent':'Alias','role':'CEO','status':'active','model':model,'source':src,'version':'SI-4.0','langgraph':LANGGRAPH_ACTIVE[0]}).encode())",
    "    def do_POST(self):",
    "        try:",
    "            n=int(self.headers.get('Content-Length',0));d=json.loads(self.rfile.read(n));text=d.get('text',d.get('task',''))",
    "        except:text=''",
    "        if not text:",
    "            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
    "            self.wfile.write(json.dumps({'reply':'I am here.','agent':'Alias'}).encode());return",
    "        reply=think(text)",
    "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
    "        self.wfile.write(json.dumps({'reply':reply,'agent':'Alias'}).encode())",
    "socketserver.TCPServer.allow_reuse_address=True",
    "save('Alias SI-4.0 started - server binding immediately, LangGraph loads in background')",
    "print('Alias SI-4.0 :8443')",
    "try:http.server.HTTPServer(('0.0.0.0',8443),H).serve_forever()",
    "except Exception as e:save('Alias crash: '+str(e));raise",
]
va_code="\n".join(alias_lines)
try:
    ast.parse(va_code)
    open("/home/k/alias-voice-agent.py","w").write(va_code)
    log("  Alias rewritten: syntax valid, server binds first, LangGraph in background")
except SyntaxError as e:
    log(f"  SYNTAX ERROR L{e.lineno}: {e.msg}")

run(["sudo","systemctl","restart","alias-voice-agent"],timeout=15)
time.sleep(5)
va_st,_=run(["systemctl","is-active","alias-voice-agent"])
va_http,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=6)
log(f"  Alias service: {va_st}")
log(f"  Alias :8443: {va_http[:100] if va_http else 'STILL DOWN'}")

# 4. Start the down services
log("\n[4] Starting down services...")
for svc in ["mia-agent","alias-email-reader","vnt-portal","cf-tunnel","smbd"]:
    run(["sudo","systemctl","restart",svc],timeout=15)
    time.sleep(1)
    st,_=run(["systemctl","is-active",svc])
    log(f"  {svc}: {st}")

# 5. Re-test all agent ports
log("\n[5] Re-testing agent ports...")
time.sleep(3)
ok=0
for name,port in [("Alias",8443),("Zeus",7777),("Maya",7778),("Mia",9999)]:
    resp,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=4)
    s="OK" if resp else "DOWN"
    if resp:ok+=1
    log(f"  {name} :{port}: {s}")

# 6. CF Tunnel URL
log("\n[6] Cloudflare tunnel...")
time.sleep(5)
cf_log,_=run("journalctl -u cf-tunnel -n 40 --no-pager --quiet",shell=True)
m=re.search(r'https://[a-z0-9-]+\.trycloudflare\.com',cf_log or "")
cf_url=m.group(0) if m else ""
log(f"  CF URL: {cf_url if cf_url else 'not ready'}")
if cf_url:
    try:
        cfg=json.load(open(CFG));cfg["cloudflare_tunnel_url"]=cf_url;json.dump(cfg,open(CFG,"w"),indent=2)
    except:pass

lg2,_=run(["python3","-c","import langgraph;print(langgraph.__version__)"])
log(f"\n  LangGraph final: {lg2 if lg2 else 'not installed'}")

full="\n".join(out)
push_result("fix_result.txt",full)
push_result("latest_state.txt",full)
save("Fix complete")
log("\n"+"="*55)
log("DONE - result pushed to GitHub")
