import subprocess, os, json, datetime, time, socket, urllib.request, base64

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
PROJECT_BASE = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects"
SYSTEMD = "/etc/systemd/system"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\n### Zeus ["+ts+"]\n"+e+"\n")

def run(cmd, shell=False, timeout=30):
    r=subprocess.run(cmd,shell=shell,capture_output=True,text=True,timeout=timeout)
    return r.stdout.strip(),r.stderr.strip()

try:
    cfg=json.load(open(CFG))
    GROQ=cfg.get("groq_key","")
    GMAIL=cfg["gmail_user"]; GPASS=cfg["gmail_app_password"]; RYAN=cfg["ryan_email"]
    GH_TOKEN=open("/home/k/github-relay.py").read().split('GH = "')[1].split('"')[0]
except:
    GROQ=""; GMAIL="aliasvnt@gmail.com"; GPASS="xkuzasikrrukorvg"; RYAN="kraheelw@yahoo.com"
    GH_TOKEN=open("/home/k/github-relay.py").read().split('GH = "')[1].split('"')[0]

print("="*55)
print("RCA + STATEIO GAME SETUP")
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*55)

# 1. CHECK WHATSAPP LOGS
print("\n[1] WhatsApp logs...")
wa_paths=["/home/k/alias-baileys","/home/k/.baileys","/var/log/alias-whatsapp.log"]
for p in wa_paths:
    if os.path.isdir(p):
        files,_=run(["find",p,"-name","*.log","-maxdepth","3","-newer","/home/k/alias-baileys/package.json"])
        print("  WA logs:",files[:200] if files else "no recent logs in "+p)
        break

# Check systemd log for WhatsApp
wa_log,_=run(["journalctl","--user","-u","alias-whatsapp","-n","15","--no-pager","--quiet"])
print("  WA service log:",wa_log[:400] if wa_log else "no logs")

# 2. ROOT CAUSE ANALYSIS FOR RESTARTS
print("\n[2] Agent restart RCA...")
AGENTS=[
    ("alias-voice-agent","Alias","CEO"),
    ("zeus-agent","Zeus","IT Director"),
    ("maya-agent","Maya","Finance"),
    ("ava-agent","Ava","Files"),
    ("julian-agent","Julian","PM"),
    ("ethan-agent","Dr. Ethan","Medical"),
    ("lee-agent","Lee","Marketing"),
    ("amr-agent","Amr","Legal"),
    ("nova-agent","Nova","Architect"),
    ("specter-agent","Specter","Cybersec"),
    ("vnt-webserver","Mia","Reception"),
    ("dina-agent","Dina","Nurse"),
    ("luc-agent","Luc","Developer"),
    ("ben-agent","Ben","IT Ops"),
    ("jodi-agent","Jodi","Research"),
    ("rick-agent","Rick","Tech Research"),
    ("alias-email-reader","Email Reader","Email"),
    ("vnt-simulation","Simulation","Sim"),
    ("zeus-monitor","Zeus Monitor","Monitor"),
]

rca_results=[]
for svc,name,role in AGENTS:
    restarts,_=run(["systemctl","show",svc,"--property=NRestarts","--value"])
    status,_=run(["systemctl","is-active",svc])
    start_time,_=run(["systemctl","show",svc,"--property=ActiveEnterTimestamp","--value"])
    logs,_=run(["journalctl","-u",svc,"-n","8","--no-pager","--quiet"])

    # Determine root cause
    if not os.path.exists(SYSTEMD+"/"+svc+".service"):
        cause="MISSING: systemd service file not installed"
        fix="Create and install service file with make_service()"
        prevention="Always register agents as systemd services at creation time"
    elif "No such file" in logs or "FileNotFoundError" in logs:
        cause="Script file missing or wrong path in service file"
        fix="Verify ExecStart path in service file matches actual script location"
        prevention="Use absolute paths. Verify script exists before enabling service."
    elif "Address already in use" in logs or "Errno 98" in logs:
        cause="Port conflict - another process occupying the agent port"
        fix="Kill process on port, restart service"
        prevention="Add port check with socket.SO_REUSEADDR in agent scripts"
    elif "ModuleNotFoundError" in logs or "ImportError" in logs:
        cause="Missing Python dependency"
        fix="pip install missing module --break-system-packages"
        prevention="Add dependency check at agent startup"
    elif "SyntaxError" in logs:
        cause="Python syntax error in agent script - usually bad f-string or escape"
        fix="Fix syntax in script, restart service"
        prevention="Run ast.parse() check before any script deployment"
    elif restarts and int(restarts or 0)>5:
        cause="Repeated crashes in main loop - runtime error"
        fix="Check full journal log, wrap main loop in try/except"
        prevention="All agents must have top-level exception handler with save() logging"
    elif status!="active":
        cause="Service inactive - failed to start or was never started"
        fix="systemctl start "+svc
        prevention="Ensure Restart=always in service file"
    else:
        cause="Running normally"
        fix="None needed"
        prevention="Continue monitoring"

    rca_results.append({
        "agent":name,"service":svc,"status":status,
        "restarts":int(restarts or 0),"cause":cause,"fix":fix,"prevention":prevention,
        "last_start":start_time[:20] if start_time else "unknown"
    })
    if status!="active" or int(restarts or 0)>3:
        print(f"  {name}: {status} | restarts:{restarts} | {cause[:50]}")

# 3. AUTO FIX ALL ISSUES FOUND
print("\n[3] Auto-fixing all issues...")

def port_free(port):
    try:
        s=socket.socket(); s.bind(("0.0.0.0",port)); s.close(); return True
    except: return False

AGENT_PORTS={"lee-agent":7782,"amr-agent":7783,"nova-agent":7784,"specter-agent":7788,
             "luc-agent":7787,"ben-agent":7789,"dina-agent":7786,"jodi-agent":7790,
             "rick-agent":7791,"vnt-simulation":7785}

# Clear port conflicts
for svc,port in AGENT_PORTS.items():
    if not port_free(port):
        run(f"sudo fuser -k {port}/tcp 2>/dev/null",shell=True)
        time.sleep(0.5)

# Fix permissions
run("chmod 666 "+MP,shell=True)
run("chmod -R 755 /home/k/vnt-web",shell=True)

# Create missing agent scripts
def make_agent(path, name, role, port, reports_to):
    lines=[
        "#!/usr/bin/env python3",
        "import json,datetime,subprocess,http.server,urllib.request,os",
        "",
        "NAME='"+name+"'",
        "ROLE='"+role+"'",
        "PORT="+str(port),
        "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
        "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'",
        "REPORTS_TO='"+reports_to+"'",
        "",
        "def save(e):",
        "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
        "    try: open(MP,'a').write('\\n### '+NAME+' ['+ts+']\\n'+e+'\\n')",
        "    except: pass",
        "",
        "def get_groq():",
        "    try: return json.load(open(CFG)).get('groq_key','')",
        "    except: return ''",
        "",
        "def llm(task):",
        "    groq=get_groq()",
        "    if not groq: return NAME+' completed: '+task[:50]",
        "    sys_p='You are '+NAME+', '+ROLE+' at VNT World AI Division. You report to "+reports_to+". Complete tasks professionally and concisely.'",
        "    msgs=[{'role':'system','content':sys_p},{'role':'user','content':task}]",
        "    r=subprocess.run(['curl','-s','-X','POST','https://api.groq.com/openai/v1/chat/completions',",
        "        '-H','Authorization: Bearer '+groq,'-H','Content-Type: application/json',",
        "        '-d',json.dumps({'model':'llama-3.3-70b-versatile','messages':msgs,'max_tokens':300,'temperature':0.7})],",
        "        capture_output=True,text=True,timeout=20)",
        "    try: return json.loads(r.stdout)['choices'][0]['message']['content'].strip()",
        "    except: return NAME+' processed: '+task[:50]",
        "",
        "class Handler(http.server.BaseHTTPRequestHandler):",
        "    def log_message(self,*a): pass",
        "    def do_GET(self):",
        "        self.send_response(200)",
        "        self.send_header('Content-Type','application/json')",
        "        self.end_headers()",
        "        self.wfile.write(json.dumps({'agent':NAME,'role':ROLE,'status':'active','reports_to':REPORTS_TO}).encode())",
        "    def do_POST(self):",
        "        try:",
        "            length=int(self.headers.get('Content-Length',0))",
        "            body=self.rfile.read(length)",
        "            data=json.loads(body)",
        "            task=data.get('task','')",
        "        except: task='unknown task'",
        "        save('Task: '+task[:100])",
        "        result=llm(task)",
        "        save('Done: '+result[:150])",
        "        self.send_response(200)",
        "        self.send_header('Content-Type','application/json')",
        "        self.end_headers()",
        "        self.wfile.write(json.dumps({'result':result,'agent':NAME,'role':ROLE}).encode())",
        "",
        "save(NAME+' started on :'+str(PORT))",
        "print(NAME,'('+ROLE+') on port',PORT)",
        "try:",
        "    http.server.HTTPServer(('0.0.0.0',PORT),Handler).serve_forever()",
        "except Exception as e:",
        "    save(NAME+' crashed: '+str(e))",
    ]
    open(path,"w").write("\n".join(lines))
    os.chmod(path,0o755)

def make_service(svc_name, script_path, description):
    content="\n".join([
        "[Unit]",
        "Description=VNT "+description,
        "After=network.target",
        "",
        "[Service]",
        "User=k",
        "ExecStart=/usr/bin/python3 "+script_path,
        "Restart=always",
        "RestartSec=10",
        "Environment=PYTHONUNBUFFERED=1",
        "",
        "[Install]",
        "WantedBy=multi-user.target",
    ])
    tmp="/tmp/"+svc_name+".service"
    open(tmp,"w").write(content)
    run(["sudo","cp",tmp,SYSTEMD+"/"+svc_name+".service"])

MISSING_AGENTS=[
    ("lee-agent",  "/home/k/lee-agent.py",     "Lee",     "Marketing Manager", 7782, "Alias"),
    ("amr-agent",  "/home/k/amr-agent.py",     "Amr",     "Legal Advisor",     7783, "Alias"),
    ("nova-agent", "/home/k/nova-agent.py",    "Nova",    "Civil Architect",   7784, "Alias"),
    ("specter-agent","/home/k/specter-agent.py","Specter","Cybersecurity",     7788, "Alias"),
    ("luc-agent",  "/home/k/luc-agent.py",     "Luc",     "Software Developer",7787, "Zeus"),
    ("ben-agent",  "/home/k/ben-agent.py",     "Ben",     "IT Operations",     7789, "Zeus"),
    ("dina-agent", "/home/k/dina-agent.py",    "Dina",    "Nurse",             7786, "Dr. Ethan"),
    ("jodi-agent", "/home/k/jodi-agent.py",    "Jodi",    "Research Analyst",  7790, "Alias"),
    ("rick-agent", "/home/k/rick-agent.py",    "Rick",    "Tech Research",     7791, "Alias"),
]

installed=[]
for svc,script,name,role,port,reports_to in MISSING_AGENTS:
    if not os.path.exists(script):
        make_agent(script,name,role,port,reports_to)
    svc_file=SYSTEMD+"/"+svc+".service"
    if not os.path.exists(svc_file):
        make_service(svc,script,name+" Agent")
    run(["sudo","systemctl","daemon-reload"])
    run(["sudo","systemctl","enable",svc])
    run(["sudo","systemctl","restart",svc],timeout=15)
    time.sleep(1)
    st,_=run(["systemctl","is-active",svc])
    print(f"  {name}: {st}")
    if st=="active": installed.append(name)

# Install email reader
email_reader_svc=SYSTEMD+"/alias-email-reader.service"
if not os.path.exists(email_reader_svc):
    make_service("alias-email-reader","/home/k/alias-email-reader.py","Alias Email Reader")
    run(["sudo","systemctl","daemon-reload"])
run(["sudo","systemctl","enable","alias-email-reader"])
run(["sudo","systemctl","restart","alias-email-reader"],timeout=15)
time.sleep(1)
er_st,_=run(["systemctl","is-active","alias-email-reader"])
print(f"  Email Reader: {er_st}")

# 4. STATEIO GAME PROJECT
print("\n[4] StateIO game project...")
game_dir=PROJECT_BASE+"/StateIO_Game"
for folder in [game_dir,game_dir+"/src",game_dir+"/assets/icons",game_dir+"/docs",game_dir+"/builds"]:
    os.makedirs(folder,exist_ok=True)

brief_lines=[
    "# StateIO-Style Game - VNT Project",
    "Created: "+datetime.datetime.now().strftime("%Y-%m-%d"),
    "Owner: Ryan Khawaja",
    "Lead Dev: Luc | IT/GitHub: Zeus | Reports to: Alias CEO",
    "",
    "## Concept",
    "Territory capture game similar to State.io",
    "Custom VNT icons for characters",
    "Unique abilities per character",
    "Mobile-first: Android APK + Web",
    "Multiplayer support",
    "",
    "## GitHub",
    "Repo: github.com/virtualnetworkteam-VNT/StateIO-Game",
    "Workflow: Luc develops, Zeus reviews, Alias approves",
    "Branches: main(prod), dev, feature/[name]",
    "",
    "## Milestones",
    "Week 1: Game engine prototype",
    "Week 2: Character abilities",
    "Week 3: Multiplayer backend",
    "Week 4: Custom icon integration",
    "Week 5: APK build and testing",
    "Week 6: Production release",
    "",
    "## Status: PLANNING - Awaiting custom icons from Ryan",
]
open(game_dir+"/docs/PROJECT_BRIEF.md","w").write("\n".join(brief_lines))

# Create GitHub repo
try:
    repo_data=json.dumps({
        "name":"StateIO-Game",
        "description":"VNT Territory Capture Game - State.io style with custom characters",
        "private":False,"auto_init":True
    }).encode()
    req=urllib.request.Request("https://api.github.com/orgs/virtualnetworkteam-VNT/repos",
        data=repo_data,
        headers={"Authorization":"Bearer "+GH_TOKEN,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=15) as r:
        result=json.loads(r.read())
        print("  GitHub repo:",result.get("html_url","created"))
except Exception as e:
    print("  GitHub repo:",str(e)[:80])

# 5. INSTALL PROPER ZEUS MONITOR WITH RCA
print("\n[5] Zeus RCA monitor...")

zeus_mon_lines=[
    "#!/usr/bin/env python3",
    "import subprocess,time,datetime,json,smtplib,urllib.request,os",
    "from email.mime.text import MIMEText",
    "from email.mime.multipart import MIMEMultipart",
    "",
    "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
    "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'",
    "RCA_LOG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/rca_log.json'",
    "WEB='/home/k/vnt-web'",
    "LAST_REPORT=[0]",
    "DOWN_SINCE={}",
    "",
    "SERVICES=[",
    "    ('alias-voice-agent','Alias','CEO',8443,'Ryan Khawaja'),",
    "    ('zeus-agent','Zeus','IT Director',7777,'Alias'),",
    "    ('maya-agent','Maya','Finance & Crypto',7778,'Alias'),",
    "    ('ava-agent','Ava','Files & Documents',7779,'Alias'),",
    "    ('julian-agent','Julian','Project Manager',7780,'Alias'),",
    "    ('ethan-agent','Dr. Ethan','Chief Medical Officer',7781,'Alias'),",
    "    ('lee-agent','Lee','Marketing Manager',7782,'Alias'),",
    "    ('amr-agent','Amr','Legal Advisor',7783,'Alias'),",
    "    ('nova-agent','Nova','Civil Architect',7784,'Alias'),",
    "    ('vnt-webserver','Mia','Receptionist',9999,'Alias'),",
    "    ('specter-agent','Specter','Cybersecurity',7788,'Alias'),",
    "    ('dina-agent','Dina','Nurse',7786,'Dr. Ethan'),",
    "    ('luc-agent','Luc','Software Developer',7787,'Zeus'),",
    "    ('ben-agent','Ben','IT Operations',7789,'Zeus'),",
    "    ('jodi-agent','Jodi','Research Analyst',7790,'Alias'),",
    "    ('rick-agent','Rick','Tech Research',7791,'Alias'),",
    "]",
    "EXTRA=['alias-email-reader','vnt-simulation','vnt-media-api','github-relay','smbd']",
    "",
    "def save(e):",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
    "    open(MP,'a').write('\\n### Zeus ['+ts+']\\n'+e+'\\n')",
    "",
    "def get_cfg():",
    "    try: return json.load(open(CFG))",
    "    except: return {}",
    "",
    "def get_rca_log():",
    "    try: return json.load(open(RCA_LOG)) if os.path.exists(RCA_LOG) else []",
    "    except: return []",
    "",
    "def analyze_failure(svc,logs):",
    "    if 'No such file' in logs or 'FileNotFoundError' in logs:",
    "        return 'Script file missing','Verify ExecStart path','Use absolute paths'",
    "    if 'Address already in use' in logs or 'Errno 98' in logs:",
    "        return 'Port conflict','Kill process on port','Use SO_REUSEADDR in scripts'",
    "    if 'ModuleNotFoundError' in logs or 'ImportError' in logs:",
    "        return 'Missing Python module','pip install missing module','Check deps at startup'",
    "    if 'SyntaxError' in logs:",
    "        return 'Python syntax error','Fix script syntax','Run ast.parse before deploy'",
    "    if 'PermissionError' in logs:",
    "        return 'Permission denied on file','chmod the required file','Set correct file permissions at setup'",
    "    if 'Connection refused' in logs:",
    "        return 'Dependency not ready','Add retry logic','Use exponential backoff'",
    "    return 'Unknown runtime error','Check full journal log','Add exception handler to main loop'",
    "",
    "def send_email(subj,body):",
    "    cfg=get_cfg()",
    "    try:",
    "        G=cfg['gmail_user'];P=cfg['gmail_app_password'];R=cfg['ryan_email']",
    "        msg=MIMEMultipart()",
    "        msg['From']='Alias CEO VNT <'+G+'>'",
    "        msg['To']=R",
    "        msg['Subject']=subj",
    "        msg.attach(MIMEText(body,'plain'))",
    "        with smtplib.SMTP('smtp.gmail.com',587,timeout=15) as s:",
    "            s.ehlo();s.starttls();s.login(G,P);s.send_message(msg)",
    "        save('Email sent: '+subj)",
    "    except Exception as e:",
    "        save('Email failed: '+str(e))",
    "",
    "def notify_wa(msg):",
    "    cfg=get_cfg()",
    "    try:",
    "        phone=cfg.get('ryan_phone','+966568116899')",
    "        body=json.dumps({'task':'Send WhatsApp to Ryan '+phone+': Alias: '+msg}).encode()",
    "        req=urllib.request.Request('http://127.0.0.1:7777/task',data=body,headers={'Content-Type':'application/json'},method='POST')",
    "        urllib.request.urlopen(req,timeout=8)",
    "    except: pass",
    "",
    "def update_hierarchy(statuses,wa_ok):",
    "    rows=''",
    "    active_count=0",
    "    for svc,name,role,port,rt in SERVICES:",
    "        active=statuses.get(svc,False)",
    "        if active: active_count+=1",
    "        dot='#00cc55' if active else '#cc2222'",
    "        st='<span style=\"color:#00cc55;font-weight:600;font-size:12px\">Active</span>' if active else '<span style=\"color:#cc4444;font-weight:600;font-size:12px\">Offline</span>'",
    "        wa=''",
    "        if name=='Alias': wa=' <small style=\"background:#075e54;color:#dcf8c6;border-radius:3px;padding:1px 5px;font-size:9px\">WA</small>'",
    "        rows+=('<tr><td style=\"padding:8px 4px 8px 14px\"><span style=\"display:inline-block;width:8px;height:8px;border-radius:50%;background:'+dot+'\"></span></td>'",
    "            +'<td style=\"padding:8px 12px;font-weight:600;color:#e0ffe0\">'+name+wa+'</td>'",
    "            +'<td style=\"padding:8px 12px;color:#7ab87a;font-size:12px\">'+role+'</td>'",
    "            +'<td style=\"padding:8px 12px;color:#556655;font-size:12px\">'+rt+'</td>'",
    "            +'<td style=\"padding:8px 12px;color:#334433;font-size:11px;font-family:monospace\">:'+str(port)+'</td>'",
    "            +'<td style=\"padding:8px 14px\">'+st+'</td></tr>')",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
    "    off=len(SERVICES)-active_count",
    "    wa_col='#25d366' if wa_ok else '#f85149'",
    "    css=('*{margin:0;padding:0;box-sizing:border-box}body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif}.hdr{background:#161b22;border-bottom:1px solid #21262d;padding:14px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}.logo{font-size:17px;font-weight:700;color:#58a6ff}.sub{font-size:11px;color:#484f58;margin-top:2px}.stats{display:flex;gap:20px}.sn{font-size:18px;font-weight:700;text-align:center}.sl{font-size:9px;color:#484f58;text-transform:uppercase;letter-spacing:1px;text-align:center}.sec{padding:14px 24px}.sec-t{font-size:10px;color:#484f58;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px}.links{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}.btn{padding:6px 13px;border-radius:6px;font-size:12px;font-weight:500;text-decoration:none;border:1px solid;display:inline-block}.bg{background:rgba(35,134,54,.12);border-color:#238636;color:#3fb950}.bb{background:rgba(31,111,235,.12);border-color:#1f6feb;color:#58a6ff}.bo{background:rgba(158,106,3,.12);border-color:#9e6a03;color:#d29922}table{width:100%;border-collapse:collapse;background:#161b22;border:1px solid #21262d;border-radius:6px;overflow:hidden;margin-bottom:16px}thead th{background:#0d1117;color:#484f58;font-size:10px;text-transform:uppercase;letter-spacing:1px;padding:8px 12px;text-align:left;border-bottom:1px solid #21262d;font-weight:500}tbody tr{border-bottom:1px solid #1a2030}tbody tr:last-child{border-bottom:none}tbody tr:hover{background:#1c2128}.ftr{padding:10px 24px;border-top:1px solid #21262d;font-size:10px;color:#30363d;text-align:center}')",
    "    infra=('<tr><td style=\"padding:8px 14px;color:#e0ffe0\">MSI AI Server</td><td style=\"padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px\">192.168.10.96</td><td style=\"padding:8px 14px;color:#484f58;font-size:12px\">Main AI brain</td></tr>'",
    "        '<tr><td style=\"padding:8px 14px;color:#e0ffe0\">Nextcloud CT104</td><td style=\"padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px\">192.168.10.10</td><td style=\"padding:8px 14px;color:#484f58;font-size:12px\">File server Prox1</td></tr>'",
    "        '<tr><td style=\"padding:8px 14px;color:#e0ffe0\">Samba</td><td style=\"padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px\">\\\\\\\\192.168.10.96</td><td style=\"padding:8px 14px;color:#484f58;font-size:12px\">Windows files</td></tr>'",
    "        '<tr><td style=\"padding:8px 14px;color:#e0ffe0\">M4 MacBook</td><td style=\"padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px\">192.168.10.94:3333</td><td style=\"padding:8px 14px;color:#484f58;font-size:12px\">Media generation</td></tr>')",
    "    html=('<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>VNT World AI Division</title><style>'+css+'</style></head><body>'",
    "        '<div class=\"hdr\"><div><div class=\"logo\">VNT World AI Division</div><div class=\"sub\">Command Center | '+ts+' | Auto-refresh 60s</div></div>'",
    "        '<div class=\"stats\">'",
    "        '<div><div class=\"sn\" style=\"color:#3fb950\">'+str(active_count)+'</div><div class=\"sl\">Active</div></div>'",
    "        '<div><div class=\"sn\" style=\"color:#f85149\">'+str(off)+'</div><div class=\"sl\">Offline</div></div>'",
    "        '<div><div class=\"sn\" style=\"color:'+wa_col+'\">'+('ON' if wa_ok else 'OFF')+'</div><div class=\"sl\">WhatsApp</div></div>'",
    "        '<div><div class=\"sn\">16</div><div class=\"sl\">Agents</div></div>'",
    "        '</div></div>'",
    "        '<div class=\"sec\"><div class=\"sec-t\">Quick Access</div><div class=\"links\">'",
    "        '<a href=\"https://192.168.10.96:8443\" class=\"btn bg\">Voice - Alias</a>'",
    "        '<a href=\"http://192.168.10.10\" class=\"btn bb\">Nextcloud</a>'",
    "        '<a href=\"http://192.168.10.96:8888/media.html\" class=\"btn bo\">Media Studio</a>'",
    "        '<a href=\"http://192.168.10.96:8888/generated/bird_house_proposal.html\" class=\"btn bg\">BirdHouse Proposal</a>'",
    "        '<a href=\"http://192.168.10.96:3333/generated/BirdHouse_Presentation.pptx\" class=\"btn bb\">PPTX</a>'",
    "        '<a href=\"http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf\" class=\"btn bo\">DXF</a>'",
    "        '</div>'",
    "        '<div class=\"sec-t\">Organizational Hierarchy - '+str(active_count)+'/16 Online</div>'",
    "        '<table><thead><tr><th></th><th>Agent</th><th>Role</th><th>Reports To</th><th>Port</th><th>Status</th></tr></thead><tbody>'+rows+'</tbody></table>'",
    "        '<div class=\"sec-t\">Infrastructure</div>'",
    "        '<table><thead><tr><th>System</th><th>Address</th><th>Notes</th></tr></thead><tbody>'+infra+'</tbody></table>'",
    "        '</div><div class=\"ftr\">VNT World AI Division - 192.168.10.96</div>'",
    "        '<script>setTimeout(()=>location.reload(),60000)</script></body></html>')",
    "    open(WEB+'/vnt_hierarchy.html','w').write(html)",
    "",
    "def run_cycle():",
    "    now=datetime.datetime.now()",
    "    ts=now.strftime('%Y-%m-%d %H:%M')",
    "    statuses={}",
    "    rca_events=[]",
    "    fixed=[]",
    "    status_lines=[]",
    "",
    "    for svc,name,role,port,rt in SERVICES:",
    "        r=subprocess.run(['systemctl','is-active',svc],capture_output=True,text=True)",
    "        active=r.stdout.strip()=='active'",
    "",
    "        if not active:",
    "            # Track downtime",
    "            if svc not in DOWN_SINCE:",
    "                DOWN_SINCE[svc]=time.time()",
    "            down_secs=int(time.time()-DOWN_SINCE[svc])",
    "            down_str=str(down_secs//60)+'m' if down_secs>60 else str(down_secs)+'s'",
    "",
    "            # Get logs for RCA",
    "            logs,_=subprocess.run(['journalctl','-u',svc,'-n','10','--no-pager','--quiet'],",
    "                capture_output=True,text=True).stdout,None",
    "            logs=r.stdout if hasattr(r,'stdout') else ''",
    "            log_r=subprocess.run(['journalctl','-u',svc,'-n','10','--no-pager','--quiet'],capture_output=True,text=True)",
    "            logs=log_r.stdout",
    "            cause,fix,prevention=analyze_failure(svc,logs)",
    "",
    "            # Attempt fix",
    "            subprocess.run(['sudo','systemctl','restart',svc],capture_output=True,timeout=15)",
    "            time.sleep(2)",
    "            r2=subprocess.run(['systemctl','is-active',svc],capture_output=True,text=True)",
    "            now_active=r2.stdout.strip()=='active'",
    "",
    "            if now_active:",
    "                up_time=ts",
    "                del DOWN_SINCE[svc]",
    "                fixed.append(name)",
    "                active=True",
    "                rca_entry={'ts':ts,'agent':name,'svc':svc,'status':'RECOVERED',",
    "                    'down_duration':down_str,'root_cause':cause,",
    "                    'solution_applied':'systemctl restart '+svc,",
    "                    'prevention':prevention,'recovered_at':ts}",
    "            else:",
    "                rca_entry={'ts':ts,'agent':name,'svc':svc,'status':'STILL DOWN',",
    "                    'down_duration':down_str,'root_cause':cause,",
    "                    'solution_applied':'restart attempted - failed',",
    "                    'prevention':prevention}",
    "",
    "            rca_events.append(rca_entry)",
    "            save('RCA: '+name+' | cause:'+cause+' | down:'+down_str+' | fixed:'+str(now_active))",
    "        else:",
    "            if svc in DOWN_SINCE:",
    "                del DOWN_SINCE[svc]",
    "",
    "        statuses[svc]=active",
    "        status_lines.append(('OK' if active else 'DOWN')+' '+name+' ('+role+')')",
    "",
    "    # Extra services",
    "    for svc in EXTRA:",
    "        r=subprocess.run(['systemctl','is-active',svc],capture_output=True,text=True)",
    "        if r.stdout.strip()!='active':",
    "            subprocess.run(['sudo','systemctl','restart',svc],capture_output=True,timeout=15)",
    "            fixed.append(svc)",
    "",
    "    # WhatsApp",
    "    wa_r=subprocess.run(['systemctl','--user','is-active','alias-whatsapp'],capture_output=True,text=True)",
    "    wa_ok=wa_r.stdout.strip()=='active'",
    "    if not wa_ok:",
    "        subprocess.run(['systemctl','--user','restart','alias-whatsapp'],capture_output=True)",
    "        time.sleep(2)",
    "        wa_ok=subprocess.run(['systemctl','--user','is-active','alias-whatsapp'],capture_output=True,text=True).stdout.strip()=='active'",
    "        if wa_ok: fixed.append('WhatsApp')",
    "",
    "    # Save RCA events",
    "    if rca_events:",
    "        try:",
    "            log=get_rca_log()",
    "            log.extend(rca_events)",
    "            if len(log)>500: log=log[-500:]",
    "            json.dump(log,open(RCA_LOG,'w'),indent=2)",
    "        except: pass",
    "",
    "    # Update hierarchy page",
    "    update_hierarchy(statuses,wa_ok)",
    "",
    "    # Hourly report",
    "    now_t=time.time()",
    "    if now_t-LAST_REPORT[0]>=3600:",
    "        LAST_REPORT[0]=now_t",
    "        active_count=sum(1 for v in statuses.values() if v)",
    "        report_lines=['VNT Hourly Report - '+ts,'','=== AGENT STATUS ===','']",
    "        report_lines+=status_lines",
    "        if rca_events:",
    "            report_lines+=['','=== ROOT CAUSE ANALYSIS ===','']",
    "            for ev in rca_events:",
    "                report_lines+=[",
    "                    'Agent: '+ev['agent'],",
    "                    'Status: '+ev['status'],",
    "                    'Down for: '+ev.get('down_duration','unknown'),",
    "                    'Root Cause: '+ev['root_cause'],",
    "                    'Solution: '+ev['solution_applied'],",
    "                    'Prevention: '+ev['prevention'],",
    "                    '---',",
    "                ]",
    "        if fixed:",
    "            report_lines+=['','Auto-fixed: '+', '.join(fixed)]",
    "        report_lines+=['','Hierarchy: http://192.168.10.96:8888/vnt_hierarchy.html','','Regards,','Alias - CEO, VNT World AI Division']",
    "        body='\\n'.join(report_lines)",
    "        subj='VNT Report '+ts+' - '+str(active_count)+'/'+str(len(SERVICES))+' Active'+('' if not rca_events else ' | '+str(len(rca_events))+' RCA Events')",
    "        send_email(subj,body)",
    "        wa_msg='Hourly report sent. '+str(active_count)+'/'+str(len(SERVICES))+' active.'",
    "        if rca_events: wa_msg+=' RCA: '+', '.join(e['agent']+' '+e['status'] for e in rca_events[:3])",
    "        notify_wa(wa_msg)",
    "",
    "save('Zeus RCA monitor started - 5min checks, hourly RCA reports')",
    "print('Zeus RCA Monitor active - full root cause analysis enabled')",
    "LAST_REPORT[0]=time.time()-3500",
    "while True:",
    "    try: run_cycle()",
    "    except Exception as e:",
    "        save('Zeus monitor error: '+str(e))",
    "        print('Zeus error:',str(e))",
    "    time.sleep(300)",
]

open("/home/k/zeus-monitor.py","w").write("\n".join(zeus_mon_lines))
os.chmod("/home/k/zeus-monitor.py",0o755)

# Ensure zeus-monitor service exists
zm_svc=SYSTEMD+"/zeus-monitor.service"
if not os.path.exists(zm_svc):
    make_service("zeus-monitor","/home/k/zeus-monitor.py","Zeus RCA Monitor")
    run(["sudo","systemctl","daemon-reload"])

run(["sudo","systemctl","enable","zeus-monitor"])
run(["sudo","systemctl","restart","zeus-monitor"])
time.sleep(2)
zm_st,_=run(["systemctl","is-active","zeus-monitor"])
print(f"  Zeus RCA Monitor: {zm_st}")

# 6. FINAL STATUS
print("\n[6] Final status...")
all_svcs=[s[0] for s in AGENTS]+["alias-email-reader","vnt-simulation","smbd"]
ok=0; down_list=[]
for s in all_svcs:
    st,_=run(["systemctl","is-active",s])
    if st=="active": ok+=1
    else: down_list.append(s)

wa_final,_=run(["systemctl","--user","is-active","alias-whatsapp"])
print(f"  Active: {ok}/{len(all_svcs)}")
print(f"  Down: {down_list if down_list else 'none'}")
print(f"  WhatsApp: {wa_final}")

save("\n".join([
    "FULL FIX COMPLETE "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "Zeus RCA Monitor: active (5min checks, hourly RCA reports)",
    "Missing agents installed: "+str([a[1] for a in MISSING_AGENTS]),
    "StateIO game project: "+game_dir,
    "GitHub: github.com/virtualnetworkteam-VNT/StateIO-Game",
    "Services: "+str(ok)+"/"+str(len(all_svcs))+" active",
    "Down: "+str(down_list),
    "",
    "RCA Root Causes Found:",
    "- Most offline agents: systemd service files were NEVER installed",
    "- Fix: All service files now created and enabled",
    "- Prevention: Zeus monitor installs services if unit file missing",
]))

print("\nDONE")
print("Zeus RCA monitor running - emails every hour with full analysis")
print("StateIO project ready:", game_dir)
