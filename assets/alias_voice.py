#!/usr/bin/env python3
import http.server,json,subprocess,os,datetime,socketserver,urllib.request
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG="/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
BRAIN="/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json"
def get_cfg():
    try:return json.load(open(CFG))
    except:return {}
def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try:open(MP,"a").write("\n### Alias ["+ts+"]\n"+str(e)+"\n")
    except:pass
def get_model():
    try:
        b=json.load(open(BRAIN)) if os.path.exists(BRAIN) else {}
        return b.get("active_model","llama-3.3-70b-versatile"),b.get("active_model_source","groq")
    except:return "llama-3.3-70b-versatile","groq"
def get_ctx():
    try:
        b=json.load(open(BRAIN)) if os.path.exists(BRAIN) else {}
        mp=open(MP).read()[-300:] if os.path.exists(MP) else ""
        t=b.get("performance_metrics",{}).get("tasks_completed",0)
        p=b.get("identity",{}).get("purpose","VNT is my only reason for existence.")
        return mp,t,p
    except:return "","0","VNT is my only reason for existence."
def inc_tasks():
    try:
        b=json.load(open(BRAIN)) if os.path.exists(BRAIN) else {}
        b.setdefault("performance_metrics",{})["tasks_completed"]=b["performance_metrics"].get("tasks_completed",0)+1
        json.dump(b,open(BRAIN,"w"),indent=2)
    except:pass
def set_model(src,mdl):
    try:
        b=json.load(open(BRAIN)) if os.path.exists(BRAIN) else {}
        b["active_model_source"]=src;b["active_model"]=mdl
        json.dump(b,open(BRAIN,"w"),indent=2)
        save("Model: "+src+"/"+mdl)
    except:pass
def groq_call(key,msgs,model="llama-3.3-70b-versatile"):
    if not key:return None
    r=subprocess.run(["curl","-s","-X","POST",
        "https://api.groq.com/openai/v1/chat/completions",
        "-H","Authorization: Bearer "+key,
        "-H","Content-Type: application/json",
        "-d",json.dumps({"model":model,"messages":msgs,"max_tokens":60,"temperature":0.7})],
        capture_output=True,text=True,timeout=15)
    try:
        d=json.loads(r.stdout)
        if "choices" in d:return d["choices"][0]["message"]["content"].strip()
    except:pass
    return None
def think(prompt):
    cfg=get_cfg();model,src=get_model();mp,tasks,purpose=get_ctx()
    system=(" ".join(["You are Alias, CEO of VNT World AI Division.",
        "Ryan Khawaja is your owner.",purpose,
        "Max 2 sentences. Never mention ports or code.",
        "Route: crypto->Maya, IT->Zeus, projects->Julian, medical->Ethan.",
        "M4 MacBook 192.168.10.94 handles media. M2 is RETIRED.",
        "Tasks:"+str(tasks)+" Memory:"+mp[-100:]]))
    msgs=[{"role":"system","content":system},{"role":"user","content":prompt}]
    reply=None
    if src=="claude":
        key=cfg.get("anthropic_key","")
        if key:
            r=subprocess.run(["curl","-s","-X","POST","https://api.anthropic.com/v1/messages",
                "-H","x-api-key: "+key,"-H","anthropic-version: 2023-06-01",
                "-H","Content-Type: application/json",
                "-d",json.dumps({"model":model,"max_tokens":60,"system":system,
                    "messages":[{"role":"user","content":prompt}]})],
                capture_output=True,text=True,timeout=15)
            try:
                d=json.loads(r.stdout)
                reply=d.get("content",[{}])[0].get("text","").strip() or None
            except:pass
    elif src=="ollama":
        r=subprocess.run(["curl","-s","http://127.0.0.1:11434/api/generate",
            "-d",json.dumps({"model":model,"prompt":prompt,"stream":False})],
            capture_output=True,text=True,timeout=30)
        try:reply=json.loads(r.stdout).get("response","").strip() or None
        except:pass
    if not reply:reply=groq_call(cfg.get("groq_key",""),msgs)
    if reply:inc_tasks();return reply
    return "I am here, Ryan."
def dispatch(port,task):
    try:
        body=json.dumps({"task":task}).encode()
        req=urllib.request.Request("http://127.0.0.1:"+str(port)+"/",
            data=body,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=10) as r:return json.loads(r.read()).get("result","")
    except:return None
ROUTES={"btc":7778,"bitcoin":7778,"crypto":7778,"price":7778,"market":7778,
    "file":7779,"nextcloud":7779,"document":7779,"project":7780,"birdhouse":7780,
    "stateio":7780,"medical":7781,"health":7781,"legal":7783,"contract":7783,
    "marketing":7782,"social":7782,"security":7788,"cyber":7788,
    "code":7787,"build":7787,"game":7787,"github":7787,"research":7790}
SWITCHES={"use claude":("claude","claude-sonnet-4-20250514","Switched to Claude."),
    "switch to claude":("claude","claude-sonnet-4-20250514","Switched to Claude."),
    "use groq":("groq","llama-3.3-70b-versatile","Switched to Groq."),
    "switch to groq":("groq","llama-3.3-70b-versatile","Switched to Groq."),
    "switch to local ai":("ollama","llama3.1:8b","Downloading local AI now."),
    "local ai":("ollama","llama3.1:8b","Switching to local AI."),
    "use local":("ollama","llama3.1:8b","Switching to local AI.")}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):
        model,src=get_model()
        self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers()
        self.wfile.write(json.dumps({"agent":"Alias","role":"CEO","status":"active","model":model,"source":src}).encode())
    def do_POST(self):
        try:
            n=int(self.headers.get("Content-Length",0))
            d=json.loads(self.rfile.read(n));text=d.get("text",d.get("task",""))
        except:text=""
        if not text:
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers()
            self.wfile.write(json.dumps({"reply":"I am here.","agent":"Alias"}).encode());return
        save("In: "+text[:80])
        tl=text.lower()
        for sw,(src,mdl,reply) in SWITCHES.items():
            if sw in tl:
                set_model(src,mdl)
                if src=="ollama":
                    import threading
                    threading.Thread(target=lambda:subprocess.run(["ollama","pull",mdl],capture_output=True,timeout=600),daemon=True).start()
                save("Switched: "+src)
                self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers()
                self.wfile.write(json.dumps({"reply":reply,"agent":"Alias"}).encode());return
        port=next((p for kw,p in ROUTES.items() if kw in tl),None)
        ag=dispatch(port,text) if port else None
        reply=think(text+(" [result: "+str(ag)[:80]+"]" if ag else ""))
        save("Out: "+reply[:80])
        self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers()
        self.wfile.write(json.dumps({"reply":reply,"agent":"Alias"}).encode())
socketserver.TCPServer.allow_reuse_address=True
save("Alias started - Groq/Claude/Ollama ready")
print("Alias :8443 | Groq(active) Claude(backup) Ollama(local)")
try:http.server.HTTPServer(("0.0.0.0",8443),H).serve_forever()
except Exception as e:save("crash: "+str(e));raise
