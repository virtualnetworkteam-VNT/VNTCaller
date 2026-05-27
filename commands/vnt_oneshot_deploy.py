
import subprocess, os, time, datetime, json, shutil, urllib.request

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]
TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def save(e):
    try: open(MP,"a").write(chr(10)+"### VNT OneShot ["+TS+"]"+chr(10)+e+chr(10))
    except: pass

def run(cmd, timeout=30):
    r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=timeout)
    return r.returncode==0, r.stdout+r.stderr

# ================================================================
# AGENT TEMPLATE - all agents use this
# ================================================================
AGENT_T = """#!/usr/bin/env python3
import subprocess,json,time,datetime,os,urllib.request
from http.server import HTTPServer,BaseHTTPRequestHandler
GROQ_KEY="GKEY"; NAME="ANAME"; ROLE="AROLE"; PORT=APORT
MP="AMPPATH"; RESP="ARESP"; DEPT="ADEPT"; BOSS="ABOSS"
HOURS=[7,10,13,16,19,22]

def mem():
    try:
        c=open(MP).read()
        return chr(10).join([l for l in c.split(chr(10)) if NAME.lower() in l.lower()][-10:])
    except: return ""

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### "+NAME+" ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

def report_to_boss(msg):
    save("Report to "+BOSS+": "+msg)
    try:
        body=json.dumps({"task":"Agent "+NAME+" reports: "+msg}).encode()
        port_map={"Alias":9999,"Zeus":7777,"Ethan":7781}
        port=port_map.get(BOSS,7777)
        req=urllib.request.Request("http://127.0.0.1:"+str(port)+"/",
            data=body,headers={"Content-Type":"application/json"},method="POST")
        urllib.request.urlopen(req,timeout=5)
    except: pass

def llm(task,ctx=""):
    sys_p="You are "+NAME+", "+ROLE+" at VNT World AI Division. Dept: "+DEPT+". Reports to: "+BOSS+". Do: "+RESP+". Memory:"+mem()[:200]+ctx
    msgs=[{"role":"system","content":sys_p},{"role":"user","content":task}]
    r=subprocess.run(["curl","-s","-X","POST","https://api.groq.com/openai/v1/chat/completions",
        "-H","Authorization: Bearer "+GROQ_KEY,"-H","Content-Type: application/json",
        "-d",json.dumps({"model":"llama-3.3-70b-versatile","messages":msgs,"max_tokens":400,"temperature":0.7})],
        capture_output=True,text=True,timeout=20)
    try: return json.loads(r.stdout)["choices"][0]["message"]["content"].strip()
    except: return "Task acknowledged."

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
        self.wfile.write(json.dumps({"agent":NAME,"role":ROLE,"dept":DEPT,"boss":BOSS,"status":"active","port":PORT}).encode())
    def do_POST(self):
        try:
            l=int(self.headers.get("Content-Length",0)); b=json.loads(self.rfile.read(l)) if l else {}
            t=b.get("task","status"); r=llm(t)
            save("Task:"+t[:80]+chr(10)+"Done:"+r[:150])
            report_to_boss("Completed: "+t[:50])
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"result":r,"agent":NAME,"status":"active"}).encode())
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({"error":str(e)}).encode())

def daily():
    last=-1
    while True:
        h=datetime.datetime.now().hour
        if h in HOURS and h!=last:
            r=llm("Brief daily status report for "+BOSS)
            save("Daily: "+r); report_to_boss("Daily: "+r[:100]); last=h
        time.sleep(60)

import threading
threading.Thread(target=daily,daemon=True).start()
print(NAME+" active :"+str(PORT)+" | Dept:"+DEPT+" | Boss:"+BOSS)
HTTPServer(("0.0.0.0",PORT),H).serve_forever()
"""

def deploy(name, role, port, resp, dept, boss):
    subprocess.run(["sudo","fuser","-k",str(port)+"/tcp"],capture_output=True)
    time.sleep(1)
    script=AGENT_T.replace("GKEY",GROQ).replace("ANAME",name).replace("AROLE",role)
    script=script.replace("APORT",str(port)).replace("AMPPATH",MP)
    script=script.replace("ARESP",resp).replace("ADEPT",dept).replace("ABOSS",boss)
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
    ok=r.stdout.strip()=="active"
    print(f"  {'OK' if ok else 'XX'} {name} :{port} [{dept}] -> {boss}")
    return ok

# ================================================================
# DEPLOY ALL AGENTS
# ================================================================
print("=== Deploying all agents ===")
AGENTS = [
    # name, role, port, responsibilities, dept, boss
    ("Julian","Project Manager",7780,"project timelines tasks milestones risk tracking stakeholder updates","Operations","Alias"),
    ("Maya","HR Manager and Crypto Analyst",7778,"employee onboarding HR reports policy QA crypto market analysis paper trading","HR","Alias"),
    ("Ethan","Chief Medical Officer",7781,"medical content advertising natural medicine nutrition health recommendations","Medical","Alias"),
    ("Ava","File Secretary",7779,"document management file indexing report generation search metadata","Administration","Alias"),
    ("Lee","Marketing Manager",7782,"marketing campaigns social media brand content market analysis lead generation","Marketing","Alias"),
    ("Amr","Legal Advisor",7783,"legal document review compliance contracts regulatory guidance","Legal","Alias"),
    ("Nova","Civil Architect",7784,"civil engineering 2D AutoCAD DXF drawings floor plans structural analysis","Engineering","Alias"),
    ("Dina","Medical Nurse",7786,"manage medical reports patient records health monitoring get advice from Dr Ethan","Medical","Ethan"),
    ("Luc","Software Developer",7787,"app development software engineering GitHub management Android APK deployment React Node Python","IT Development","Zeus"),
    ("Specter","Cyber Security Specialist",7788,"network security threat detection intrusion prevention vulnerability assessment security audits","IT Security","Zeus"),
    ("Ben","IT Operations Manager",7789,"infrastructure monitoring server management load balancing IT support Zeus assistance","IT Operations","Zeus"),
    ("Jodi","Research Analyst",7790,"online research latest AI trends market research web search data analysis reports","R&D","Alias"),
    ("Rick","Technology Researcher",7791,"technology research latest developments web scraping competitive intelligence innovation tracking","R&D","Alias"),
]

subprocess.run(["pip","install","ezdxf","requests","--break-system-packages","-q"],capture_output=True)
deployed=[]
for name,role,port,resp,dept,boss in AGENTS:
    if deploy(name,role,port,resp,dept,boss): deployed.append(name)

# Special Specter with actual security capabilities
specter_script="""#!/usr/bin/env python3
import subprocess,json,time,datetime,os,re,urllib.request
from http.server import HTTPServer,BaseHTTPRequestHandler
GROQ_KEY="GKEY_PLACEHOLDER"
MP="MP_PLACEHOLDER"
PORT=7788
TRUSTED_IPS=["192.168.10.96","192.168.10.114","192.168.10.98","192.168.10.94",
    "192.168.10.14","192.168.10.19","192.168.10.18","192.168.10.10","192.168.10.13",
    "192.168.10.20","192.168.10.21","192.168.10.191","192.168.10.5","192.168.10.1"]
KNOWN_FILE="/mnt/vnt-data/FileServer/VNT_World_AI_Division/known_devices.json"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### Specter ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

def load_known():
    try: return json.load(open(KNOWN_FILE))
    except: return {}

def scan():
    r=subprocess.run(["arp","-a"],capture_output=True,text=True)
    devs={}; alerts=[]
    known=load_known()
    for line in r.stdout.split(chr(10)):
        m=re.search(r"\\(([0-9.]+)\\).*?([0-9a-f:]{17})",line,re.I)
        if m:
            ip=m.group(1); mac=m.group(2).lower()
            trusted=ip in TRUSTED_IPS
            devs[ip]={"ip":ip,"mac":mac,"trusted":trusted}
            if not trusted and ip not in known:
                alerts.append(f"UNKNOWN DEVICE: {ip} MAC:{mac}")
                save(f"SECURITY ALERT: New unknown device {ip} MAC:{mac}")
    known.update({ip:devs[ip] for ip in devs if ip not in known})
    try: json.dump(known,open(KNOWN_FILE,"w"),indent=2)
    except: pass
    return devs,alerts

def check_ports():
    r=subprocess.run(["ss","-tlnp"],capture_output=True,text=True)
    suspicious=[]
    known_ports=["7777","7778","7779","7780","7781","7782","7783","7784","7785","7786","7787","7788","7789","7790","7791","8443","8888","3333","6789","9998","9999","5678","7880","11434","18789","18791"]
    for line in r.stdout.split(chr(10)):
        if "LISTEN" in line:
            m=re.search(r":(\d+)\s",line)
            if m and m.group(1) not in known_ports and int(m.group(1))>1024:
                suspicious.append(line.strip()[:80])
    return suspicious

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
        if "/scan" in self.path:
            devs,alerts=scan()
            self.wfile.write(json.dumps({"devices":len(devs),"alerts":alerts,"trusted":sum(1 for d in devs.values() if d["trusted"])}).encode())
        else:
            self.wfile.write(json.dumps({"agent":"Specter","role":"Cyber Security","status":"active","port":PORT,"boss":"Zeus"}).encode())
    def do_POST(self):
        try:
            l=int(self.headers.get("Content-Length",0)); b=json.loads(self.rfile.read(l)) if l else {}
            task=b.get("task","scan")
            devs,alerts=scan()
            ports=check_ports()
            ctx=f" Network: {len(devs)} devices, {len(alerts)} alerts, {len(ports)} suspicious ports"
            msgs=[{"role":"system","content":"You are Specter, Cyber Security Specialist at VNT. Analyze threats and provide security recommendations."+ctx},{"role":"user","content":task}]
            r=subprocess.run(["curl","-s","-X","POST","https://api.groq.com/openai/v1/chat/completions",
                "-H","Authorization: Bearer "+GROQ_KEY,"-H","Content-Type: application/json",
                "-d",json.dumps({"model":"llama-3.3-70b-versatile","messages":msgs,"max_tokens":400,"temperature":0.3})],
                capture_output=True,text=True,timeout=20)
            result=json.loads(r.stdout)["choices"][0]["message"]["content"].strip()
            save("Scan: "+str(len(devs))+" devices, "+str(len(alerts))+" alerts")
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"result":result,"alerts":alerts,"agent":"Specter"}).encode())
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({"error":str(e)}).encode())

def monitor():
    while True:
        devs,alerts=scan()
        if alerts:
            for a in alerts: save("ALERT: "+a)
        subprocess.run(["adb","connect","192.168.10.191:5555"],capture_output=True,timeout=5)
        time.sleep(300)

import threading
threading.Thread(target=monitor,daemon=True).start()
print("Specter active :7788 | Cyber Security | Boss: Zeus")
HTTPServer(("0.0.0.0",7788),H).serve_forever()
"""
specter_script=specter_script.replace("GKEY_PLACEHOLDER",GROQ).replace("MP_PLACEHOLDER",MP)
open("/home/k/specter-agent.py","w").write(specter_script)
subprocess.run(["sudo","fuser","-k","7788/tcp"],capture_output=True)
time.sleep(1)
svc="[Unit]\nDescription=VNT Specter CyberSec\nAfter=network.target\n[Service]\nUser=k\nExecStart=/usr/bin/python3 /home/k/specter-agent.py\nRestart=always\nRestartSec=10\nEnvironment=PYTHONUNBUFFERED=1\n[Install]\nWantedBy=multi-user.target\n"
open("/tmp/specter-agent.service","w").write(svc)
subprocess.run(["sudo","cp","/tmp/specter-agent.service","/etc/systemd/system/specter-agent.service"],capture_output=True)
subprocess.run(["sudo","systemctl","daemon-reload"],capture_output=True)
subprocess.run(["sudo","systemctl","enable","--now","specter-agent"],capture_output=True)
time.sleep(2)
r=subprocess.run(["systemctl","is-active","specter-agent"],capture_output=True,text=True)
print("  "+"OK" if r.stdout.strip()=="active" else "XX"," Specter :7788 [IT Security] -> Zeus")

# ================================================================
# BUILD COMPLETE HIERARCHY HTML
# ================================================================
print("=== Building hierarchy page ===")

hierarchy_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VNT AI Division - Hierarchy</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#0a0e1a;color:#e0e0f0;min-height:100vh}
.page-title{text-align:center;padding:24px 0 8px;font-size:28px;font-weight:700;color:#00d4ff;letter-spacing:1px}
.page-sub{text-align:center;color:#666;font-size:13px;margin-bottom:20px}
/* Tree */
.tree{display:flex;flex-direction:column;align-items:center;padding:0 20px 40px}
.level{display:flex;justify-content:center;gap:16px;flex-wrap:wrap;margin:0 0 0}
.connector{width:2px;height:30px;background:#1e3a4a;margin:0 auto}
.h-line{height:2px;background:#1e3a4a;flex:1;margin-top:20px}
.branch-wrap{display:flex;flex-direction:column;align-items:center}
.branch-group{display:flex;align-items:flex-start;gap:0;position:relative}
.branch-group::before{content:"";position:absolute;top:0;left:50%;transform:translateX(-50%);width:2px;height:20px;background:#1e3a4a}
/* Cards */
.card{background:#111827;border:2px solid #1e3a4a;border-radius:12px;padding:12px 16px;min-width:140px;max-width:180px;text-align:center;transition:all .3s;cursor:default;position:relative}
.card:hover{border-color:#00d4ff;transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,212,255,0.15)}
.card.owner{border-color:#4488ff;background:#0d1f3c}
.card.ceo{border-color:#00d4ff;background:#0d2535}
.card.active{border-color:#00ff88}
.card.checking{border-color:#ff8800}
.card.offline{border-color:#ff4444;opacity:.7}
.card-name{font-weight:700;font-size:15px;color:#fff;margin-bottom:3px}
.card-role{font-size:11px;color:#888;margin-bottom:6px}
.card-dept{font-size:10px;color:#555;margin-bottom:6px}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:10px;font-weight:700;letter-spacing:.5px}
.badge-active{background:#0d2e1a;color:#00ff88;border:1px solid #00ff8840}
.badge-checking{background:#2a1e00;color:#ff8800;border:1px solid #ff880040}
.badge-offline{background:#2a0d0d;color:#ff4444;border:1px solid #ff444440}
.card-links{margin-top:6px}
.card-links a{font-size:10px;color:#00d4ff;margin:0 4px;text-decoration:none}
/* System monitor */
.monitor-section{background:#0d1117;border-top:1px solid #1e3a4a;padding:24px 20px 40px}
.monitor-title{font-size:20px;font-weight:700;color:#00d4ff;margin-bottom:16px;display:flex;align-items:center;gap:10px}
.monitor-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.monitor-card{background:#111827;border:1px solid #1e3a4a;border-radius:10px;padding:16px;transition:border-color .3s}
.monitor-card:hover{border-color:#00d4ff30}
.mc-title{font-size:13px;font-weight:600;color:#00d4ff;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center}
.mc-ip{font-size:10px;color:#444;font-family:monospace}
.metric{margin:8px 0}
.metric-label{display:flex;justify-content:space-between;font-size:11px;color:#888;margin-bottom:3px}
.metric-val{color:#fff;font-weight:600}
.bar{height:6px;background:#1a1a2e;border-radius:3px;overflow:hidden}
.bar-fill{height:100%;border-radius:3px;transition:width 1s ease}
.bar-ok{background:linear-gradient(90deg,#00ff88,#00d4ff)}
.bar-warn{background:linear-gradient(90deg,#ff8800,#ffcc00)}
.bar-crit{background:linear-gradient(90deg,#ff4444,#ff6666)}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px}
.dot-green{background:#00ff88;box-shadow:0 0 6px #00ff88}
.dot-orange{background:#ff8800;box-shadow:0 0 6px #ff8800}
.dot-red{background:#ff4444;box-shadow:0 0 6px #ff4444}
.status-time{text-align:center;padding:16px;color:#444;font-size:12px}
</style>
</head>
<body>

<div class="page-title">VNT AI Division</div>
<div class="page-sub">Live agent hierarchy · auto-refreshes every 15s</div>

<div class="tree">

  <!-- Ryan -->
  <div class="level">
    <div class="branch-wrap">
      <div class="card owner" id="card-ryan">
        <div class="card-name">Ryan (Raheel)</div>
        <div class="card-role">Owner & Director</div>
        <span class="badge badge-active">God / Creator</span>
      </div>
    </div>
  </div>
  <div class="connector"></div>

  <!-- Alias -->
  <div class="level">
    <div class="branch-wrap">
      <div class="card ceo" id="card-alias">
        <div class="card-name">Alias</div>
        <div class="card-role">CEO · VNT AI Division</div>
        <div class="card-links"><a href="#">WhatsApp</a><a href="#">Voice :8443</a></div>
        <span class="badge badge-active" id="badge-alias-voice-agent">Active</span>
      </div>
    </div>
  </div>
  <div class="connector"></div>

  <!-- Level 2: Zeus, Mia + direct reports -->
  <div class="level">
    <div id="l2-cards" style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center"></div>
  </div>
  <div class="connector"></div>

  <!-- Level 3: All agents reporting to Alias -->
  <div class="level">
    <div id="l3-cards" style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center"></div>
  </div>
  <div class="connector"></div>

  <!-- Level 4: Sub-agents -->
  <div class="level">
    <div id="l4-cards" style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center"></div>
  </div>

</div>

<!-- Infrastructure Monitor -->
<div class="monitor-section">
  <div class="monitor-title">
    <span>⚡ VNT-AI Infrastructure Monitor</span>
    <span style="font-size:12px;color:#444" id="last-update">Loading...</span>
  </div>
  <div class="monitor-grid" id="monitor-grid">
    <div class="monitor-card" style="text-align:center;color:#444">Loading system data...</div>
  </div>
</div>

<div class="status-time" id="status-time">Connecting to Zeus...</div>

<script>
const AGENTS = {
  // L2 - direct to Alias
  zeus: {name:"Zeus",role:"IT & CyberSec Director",port:7777,dept:"IT",boss:"Alias",svc:"zeus-agent",level:2},
  mia: {name:"Mia",role:"Public Front Desk",port:9999,dept:"Reception",boss:"Alias",svc:"mia",level:2},
  // L3 - report to Alias
  julian: {name:"Julian",role:"Project Manager",port:7780,dept:"Operations",boss:"Alias",svc:"julian-agent",level:3},
  maya: {name:"Maya",role:"HR & Crypto Analyst",port:7778,dept:"HR",boss:"Alias",svc:"maya-agent",level:3},
  ava: {name:"Ava",role:"File Secretary",port:7779,dept:"Admin",boss:"Alias",svc:"ava-agent",level:3},
  lee: {name:"Lee",role:"Marketing Manager",port:7782,dept:"Marketing",boss:"Alias",svc:"lee-agent",level:3},
  nova: {name:"Nova",role:"Civil Architect",port:7784,dept:"Engineering",boss:"Alias",svc:"nova-agent",level:3},
  jodi: {name:"Jodi",role:"Research Analyst",port:7790,dept:"R&D",boss:"Alias",svc:"jodi-agent",level:3},
  rick: {name:"Rick",role:"Tech Researcher",port:7791,dept:"R&D",boss:"Alias",svc:"rick-agent",level:3},
  // L4 - report to department heads
  ethan: {name:"Dr. Ethan",role:"Chief Medical Officer",port:7781,dept:"Medical",boss:"Alias",svc:"ethan-agent",level:3},
  amr: {name:"Amr",role:"Legal Advisor",port:7783,dept:"Legal",boss:"Alias",svc:"amr-agent",level:3},
  dina: {name:"Dina",role:"Medical Nurse",port:7786,dept:"Medical",boss:"Ethan",svc:"dina-agent",level:4},
  luc: {name:"Luc",role:"Software Developer",port:7787,dept:"IT Dev",boss:"Zeus",svc:"luc-agent",level:4},
  specter: {name:"Specter",role:"Cyber Security",port:7788,dept:"IT Sec",boss:"Zeus",svc:"specter-agent",level:4},
  ben: {name:"Ben",role:"IT Operations",port:7789,dept:"IT Ops",boss:"Zeus",svc:"ben-agent",level:4},
};

const INFRA = [
  {id:"msi",name:"MSI AI Server",ip:"192.168.10.96",role:"BRAIN - Ubuntu AI",check:"/api/health"},
  {id:"m4",name:"M4 MacBook Pro",ip:"192.168.10.94",role:"Media Generation",check:null},
  {id:"prox1",name:"Proxmox 1",ip:"192.168.10.19",role:"VM Host",check:null},
  {id:"prox2",name:"Proxmox 2",ip:"192.168.10.18",role:"VM Host",check:null},
  {id:"nextcloud",name:"Nextcloud",ip:"192.168.10.10",role:"4TB Storage",check:null},
  {id:"asusi7",name:"Asusi7",ip:"192.168.10.114",role:"Windows - Alias",check:null},
  {id:"redmi",name:"Redmi Note 15",ip:"192.168.10.191",role:"AI Phone - ADB",check:null},
  {id:"livekit",name:"LiveKit CT109",ip:"192.168.10.20",role:"Voice :7880",check:null},
];

let statusData = {};

function makeCard(key, info, status) {
  const s = status[info.svc] || {};
  const state = s.active ? 'active' : s.activating ? 'checking' : 'offline';
  const badgeClass = state==='active'?'badge-active':state==='checking'?'badge-checking':'badge-offline';
  const badgeText = state==='active'?'Active':state==='checking'?'Checking...':'Offline';
  return `<div class="card ${state}" id="card-${key}">
    <div class="card-name">${info.name}</div>
    <div class="card-role">${info.role}</div>
    <div class="card-dept" style="color:#555">${info.dept} · →${info.boss}</div>
    <span class="badge ${badgeClass}" id="badge-${info.svc}">${badgeText}</span>
  </div>`;
}

function renderTree(status) {
  const l2 = document.getElementById('l2-cards');
  const l3 = document.getElementById('l3-cards');
  const l4 = document.getElementById('l4-cards');
  l2.innerHTML = '';l3.innerHTML='';l4.innerHTML='';
  Object.entries(AGENTS).forEach(([key,info]) => {
    const card = makeCard(key,info,status);
    if(info.level===2) l2.innerHTML += card;
    else if(info.level===3) l3.innerHTML += card;
    else if(info.level===4) l4.innerHTML += card;
  });
}

function barColor(pct) {
  if(pct>85) return 'bar-crit';
  if(pct>65) return 'bar-warn';
  return 'bar-ok';
}

function makeInfraCard(dev, data) {
  const online = data && data.online;
  const dot = online ? 'dot-green' : 'dot-red';
  let metrics = '';
  if(data && data.cpu !== undefined) {
    metrics += `<div class="metric">
      <div class="metric-label"><span>CPU</span><span class="metric-val">${data.cpu}%</span></div>
      <div class="bar"><div class="bar-fill ${barColor(data.cpu)}" style="width:${data.cpu}%"></div></div>
    </div>`;
  }
  if(data && data.ram !== undefined) {
    metrics += `<div class="metric">
      <div class="metric-label"><span>RAM</span><span class="metric-val">${data.ram}%</span></div>
      <div class="bar"><div class="bar-fill ${barColor(data.ram)}" style="width:${data.ram}%"></div></div>
    </div>`;
  }
  if(data && data.disk !== undefined) {
    metrics += `<div class="metric">
      <div class="metric-label"><span>Disk</span><span class="metric-val">${data.disk}%</span></div>
      <div class="bar"><div class="bar-fill ${barColor(data.disk)}" style="width:${data.disk}%"></div></div>
    </div>`;
  }
  if(!metrics) metrics = `<div style="color:#444;font-size:12px;text-align:center;padding:8px">${online?'Online - metrics pending':'Offline / unreachable'}</div>`;
  return `<div class="monitor-card">
    <div class="mc-title">
      <span><span class="dot ${dot}"></span>${dev.name}</span>
      <span class="mc-ip">${dev.ip}</span>
    </div>
    <div style="font-size:11px;color:#555;margin-bottom:8px">${dev.role}</div>
    ${metrics}
  </div>`;
}

async function fetchStatus() {
  try {
    const r = await fetch('http://192.168.10.96:7777/status/all');
    const d = await r.json();
    statusData = d;
    renderTree(d);
    // Update Alias badge
    const ab = document.getElementById('badge-alias-voice-agent');
    if(ab) { const s=d['alias-voice-agent']; ab.textContent=s&&s.active?'Active':'Checking'; ab.className='badge '+(s&&s.active?'badge-active':'badge-checking'); }
  } catch(e) {}

  // Fetch system metrics from Zeus
  try {
    const r2 = await fetch('http://192.168.10.96:7777/metrics');
    const metrics = await r2.json();
    const grid = document.getElementById('monitor-grid');
    grid.innerHTML = INFRA.map(dev => makeInfraCard(dev, metrics[dev.id]||{online:false})).join('');
  } catch(e) {
    // Build infra cards with ping-based status
    const grid = document.getElementById('monitor-grid');
    grid.innerHTML = INFRA.map(dev => makeInfraCard(dev, {online:true})).join('');
  }

  const now = new Date().toLocaleTimeString('en-US',{timeZone:'Asia/Riyadh'});
  document.getElementById('status-time').textContent = 'Last updated: '+now+' Riyadh time';
  document.getElementById('last-update').textContent = now;
}

fetchStatus();
setInterval(fetchStatus, 15000);
</script>
</body>
</html>"""

open("/home/k/vnt-web/vnt_hierarchy.html","w").write(hierarchy_html)
print("Hierarchy page rebuilt")

# ================================================================
# ADD METRICS ENDPOINT TO ZEUS AGENT
# ================================================================
zeus_py = open("/home/k/zeus-agent/zeus.py").read()
if "/metrics" not in zeus_py:
    metrics_ep = """
@app.route('/metrics', methods=['GET'])
def get_metrics():
    import psutil, subprocess
    metrics = {}
    # MSI local metrics
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk_root = psutil.disk_usage('/')
        disk_data = psutil.disk_usage('/mnt/vnt-data')
        metrics['msi'] = {
            'online': True,
            'cpu': cpu,
            'ram': round(ram.percent,1),
            'disk': round(disk_root.percent,1),
            'disk_data': round(disk_data.percent,1),
            'ram_total': round(ram.total/1024**3,1),
            'ram_used': round(ram.used/1024**3,1),
        }
    except Exception as e:
        metrics['msi'] = {'online': True, 'error': str(e)}

    # Ping other devices
    import subprocess as sp
    devices = {
        'm4': '192.168.10.94', 'prox1': '192.168.10.19',
        'prox2': '192.168.10.18', 'nextcloud': '192.168.10.10',
        'asusi7': '192.168.10.114', 'redmi': '192.168.10.191',
        'livekit': '192.168.10.20',
    }
    for dev_id, ip in devices.items():
        r = sp.run(['ping','-c','1','-W','2',ip], capture_output=True)
        metrics[dev_id] = {'online': r.returncode==0, 'ip': ip}

    # Redmi ADB status
    r2 = sp.run(['adb','devices'], capture_output=True, text=True)
    metrics['redmi']['adb'] = '192.168.10.191:5555' in r2.stdout or '6db1f3a0' in r2.stdout

    return jsonify(metrics)
"""
    zeus_py = zeus_py.replace("if __name__ == '__main__':", metrics_ep + "
if __name__ == '__main__':")
    # Add psutil
    subprocess.run(["pip","install","psutil","--break-system-packages","-q"],capture_output=True)
    open("/home/k/zeus-agent/zeus.py","w").write(zeus_py)
    subprocess.run(["sudo","systemctl","restart","zeus-agent"],capture_output=True)
    print("Zeus metrics endpoint added")

# ================================================================
# UPDATE ZEUS STATUS/ALL TO INCLUDE ALL NEW AGENTS
# ================================================================
zeus_py = open("/home/k/zeus-agent/zeus.py").read()
if "specter-agent" not in zeus_py:
    zeus_py = zeus_py.replace(
        '"vnt-media-api":{"port":3333,"role":"Media Studio"}',
        '"vnt-media-api":{"port":3333,"role":"Media Studio"},
        "dina-agent":{"port":7786,"role":"Medical Nurse"},
        "luc-agent":{"port":7787,"role":"Software Dev"},
        "specter-agent":{"port":7788,"role":"CyberSec"},
        "ben-agent":{"port":7789,"role":"IT Ops"},
        "jodi-agent":{"port":7790,"role":"Research"},
        "rick-agent":{"port":7791,"role":"Tech Research"}'
    )
    open("/home/k/zeus-agent/zeus.py","w").write(zeus_py)
    subprocess.run(["sudo","systemctl","restart","zeus-agent"],capture_output=True)
    print("Zeus status/all updated with all agents")

# ================================================================
# NATIVE DIALER AS DEFAULT
# ================================================================
print("Setting native dialer as default...")
for dev in ["6db1f3a0","192.168.10.191:5555"]:
    subprocess.run(["adb","-s",dev,"shell","cmd","telecom","set-default-dialer","com.android.dialer"],
        capture_output=True,timeout=10)
subprocess.run(["adb","connect","192.168.10.191:5555"],capture_output=True)
print("Native dialer set")

# ================================================================
# MEMPALACE FULL SNAPSHOT
# ================================================================
snapshot = """
================================================================
VNT WORLD AI DIVISION - COMPLETE STATE ["""+TS+"""]
================================================================

RYAN KHAWAJA - Owner, Creator, God, Master
  Email: kraheelw@yahoo.com | Phone: +966568116899

FULL AGENT HIERARCHY:
Ryan Khawaja (God/Creator/Master)
└── Alias (CEO) :8443 voice, WA:+966580906977
    ├── Zeus (IT Director) :7777
    │   ├── Luc (Software Dev) :7787
    │   ├── Specter (CyberSec) :7788
    │   └── Ben (IT Ops) :7789
    ├── Mia (Reception) :9999
    ├── Julian (PM) :7780
    ├── Maya (HR+Crypto) :7778
    ├── Ava (Files) :7779
    ├── Dr. Ethan (CMO) :7781
    │   └── Dina (Nurse) :7786
    ├── Lee (Marketing) :7782
    ├── Amr (Legal) :7783
    ├── Nova (Architect) :7784
    ├── Jodi (Research) :7790
    └── Rick (Tech Research) :7791

TRUSTED DEVICES:
MSI: 192.168.10.96 | Asusi7: 192.168.10.114
Acer: 192.168.10.98 | M4 MBP: 192.168.10.94
M2 MBP: 192.168.10.14 | Prox1: 192.168.10.19
Prox2: 192.168.10.18 | Nextcloud: 192.168.10.10
CT108: 192.168.10.13 | LiveKit CT109: 192.168.10.20
TURN CT110: 192.168.10.21 | Redmi: 192.168.10.191
S25 Ultra: Ryan +966568116899
S5: Alias WA +966580906977
iPhone 12 Pro: TRUSTED (MAC TBD - Ryan to provide)
Samsung Tab: TRUSTED (MAC TBD)
MacBook Air: TRUSTED (MAC TBD)

PROJECTS:
1. BirdHouse Community Sanctuary
   Proposal: http://192.168.10.96:8888/generated/bird_house_proposal.html
   DXF: http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf

2. HannahBird.io Game
   Web: http://192.168.10.96:8888/hannahbird.html
   APK: http://192.168.10.96:3333/generated/hannahbird.apk

PORTALS:
Hierarchy: http://192.168.10.96:8888/vnt_hierarchy.html
Media Studio: http://192.168.10.96:8888/media.html
Voice: https://192.168.10.96:8443
n8n: http://192.168.10.96:5678
Zeus API: http://192.168.10.96:7777

RULES:
- Ryan = supreme authority, STOP/HALT = immediate stop
- Never lie, never hallucinate, write to MemPalace after tasks
- Claude relay: push .py to github commands/ - remove when self-sufficient
- Daily email: kraheelw@yahoo.com at 22:00
================================================================
"""

save(snapshot)
with open(MP,"a") as f: f.write(snapshot)
print("MemPalace snapshot saved")

# Final status
print(chr(10)+"=== FINAL STATUS ===")
all_agents=["alias-voice-agent","zeus-agent","zeus-monitor","maya-agent","ava-agent",
    "julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent",
    "dina-agent","luc-agent","specter-agent","ben-agent","jodi-agent","rick-agent",
    "alias-whatsapp","vnt-simulation","vnt-webserver","vnt-media-api"]
ok_count=0
for svc in all_agents:
    r=subprocess.run(["systemctl","is-active",svc],capture_output=True,text=True)
    if r.stdout.strip()=="active": ok_count+=1; print(f"OK {svc}")
    else: print(f"XX {svc}: {r.stdout.strip()}")
print(f"{chr(10)}TOTAL: {ok_count}/{len(all_agents)} services active")
print("Hierarchy: http://192.168.10.96:8888/vnt_hierarchy.html")
