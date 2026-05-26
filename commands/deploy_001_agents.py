
import subprocess, os, time, json

# Read GROQ key from MSI local config
GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]
MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

AGENTS = [["Julian", "Project Manager", 7780, "projects timelines tasks stakeholder updates risk tracking"], ["Maya", "HR Manager", 7778, "employee onboarding HR reports policy QA candidate screening"], ["Ethan", "Medical Expert", 7781, "medical content nutrition natural medicine herbal treatments"], ["Ava", "File Secretary", 7779, "document management file indexing report generation search"], ["Lee", "Marketing Manager", 7782, "campaigns social media brand content market analysis"], ["Amr", "Legal Advisor", 7783, "legal documents compliance contracts regulatory guidance"], ["Nova", "Civil Architect", 7784, "civil engineering 2D AutoCAD DXF floor plans structural analysis"]]

T = '''#!/usr/bin/env python3
import subprocess, json, time, datetime, os
from http.server import HTTPServer, BaseHTTPRequestHandler
GROQ_KEY = "GKEY"
NAME = "ANAME"; ROLE = "AROLE"; PORT = APORT; MP = "AMPPATH"; RESP = "ARESP"
HOURS = [7,10,13,16,19,22]
def mem():
    try:
        c=open(MP).read(); return "\\n".join([l for l in c.split("\\n") if NAME.lower() in l.lower()][-10:])
    except: return ""
def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\\n### "+NAME+" ["+ts+"]\\n"+e+"\\n")
    except: pass
def llm(task):
    msgs=[{"role":"system","content":"You are "+NAME+", "+ROLE+" at VNT. Do: "+RESP+". Report what you actually did. Memory:"+mem()[:200]},{"role":"user","content":task}]
    r=subprocess.run(["curl","-s","-X","POST","https://api.groq.com/openai/v1/chat/completions","-H","Authorization: Bearer "+GROQ_KEY,"-H","Content-Type: application/json","-d",json.dumps({"model":"llama-3.3-70b-versatile","messages":msgs,"max_tokens":300,"temperature":0.7})],capture_output=True,text=True,timeout=20)
    try: return json.loads(r.stdout)["choices"][0]["message"]["content"].strip()
    except: return "Done."
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
        self.wfile.write(json.dumps({"agent":NAME,"role":ROLE,"status":"active","port":PORT}).encode())
    def do_POST(self):
        try:
            l=int(self.headers.get("Content-Length",0)); b=json.loads(self.rfile.read(l)) if l else {}
            t=b.get("task","status"); r=llm(t); save("Task:"+t[:80]+"\\nDone:"+r[:150])
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"result":r,"agent":NAME}).encode())
        except Exception as e:
            self.send_response(500); self.end_headers(); self.wfile.write(json.dumps({"error":str(e)}).encode())
import threading
def rpt():
    last=-1
    while True:
        h=datetime.datetime.now().hour
        if h in HOURS and h!=last: save("Daily:"+llm("Brief status report.")); last=h
        time.sleep(60)
threading.Thread(target=rpt,daemon=True).start()
print(NAME+" on :"+str(PORT)); HTTPServer(("0.0.0.0",PORT),H).serve_forever()
'''

def deploy(name,role,port,resp):
    script=T.replace("GKEY",GROQ).replace("ANAME",name).replace("AROLE",role)
    script=script.replace("APORT",str(port)).replace("AMPPATH",MP).replace("ARESP",resp)
    path=f"/home/k/{name.lower()}-agent.py"
    open(path,"w").write(script); os.chmod(path,0o755)
    svc=f"[Unit]\nDescription=VNT {name}\nAfter=network.target\n[Service]\nUser=k\nExecStart=/usr/bin/python3 {path}\nRestart=always\nRestartSec=10\nEnvironment=PYTHONUNBUFFERED=1\n[Install]\nWantedBy=multi-user.target\n"
    sn=f"{name.lower()}-agent"
    open(f"/tmp/{sn}.service","w").write(svc)
    subprocess.run(["sudo","cp",f"/tmp/{sn}.service",f"/etc/systemd/system/{sn}.service"],capture_output=True)
    subprocess.run(["sudo","systemctl","daemon-reload"],capture_output=True)
    subprocess.run(["sudo","systemctl","enable","--now",sn],capture_output=True)
    time.sleep(2)
    r=subprocess.run(["systemctl","is-active",sn],capture_output=True,text=True)
    ok=r.stdout.strip()=="active"; print(f"  {'OK' if ok else 'XX'} {name} :{port}"); return ok

subprocess.run(["pip","install","ezdxf","--break-system-packages","-q"],capture_output=True)
deployed=[]
for name,role,port,resp in AGENTS:
    if deploy(name,role,port,resp): deployed.append(name)

# Update Zeus monitoring
zm=open("/home/k/zeus-monitor.py").read()
for ag in ["julian-agent","maya-agent","ethan-agent","ava-agent","lee-agent","amr-agent","nova-agent"]:
    if ag not in zm: zm=zm.replace('"ethan-agent"',f'"ethan-agent","{ag}"')
open("/home/k/zeus-monitor.py","w").write(zm)
subprocess.run(["sudo","systemctl","restart","zeus-monitor"],capture_output=True)

with open(MP,"a") as f:
    f.write(f"\n### ALL AGENTS DEPLOYED [{time.strftime('%Y-%m-%d %H:%M')}]\nActive: {', '.join(deployed)}\n")
print("DONE:", ", ".join(deployed))
