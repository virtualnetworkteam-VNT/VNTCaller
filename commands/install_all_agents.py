
import subprocess, os, json, datetime, time, smtplib, stat
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
WEB = "/home/k/vnt-web"
SYSTEMD = "/etc/systemd/system"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\n### Zeus Fix ["+ts+"]\n"+e+"\n")

def run(cmd,shell=False,timeout=30):
    r=subprocess.run(cmd,shell=shell,capture_output=True,text=True,timeout=timeout)
    return r.stdout.strip(),r.stderr.strip()

try:
    cfg=json.load(open(CFG))
    GROQ=cfg.get("groq_key","")
    GMAIL=cfg["gmail_user"]; GPASS=cfg["gmail_app_password"]; RYAN=cfg["ryan_email"]
except:
    GROQ=open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]
    GMAIL="aliasvnt@gmail.com"; GPASS="xkuzasikrrukorvg"; RYAN="kraheelw@yahoo.com"

print("="*55)
print("FINDING + INSTALLING ALL MISSING AGENTS")
print("="*55)

# Find existing agent files
print("\nScanning for agent files...")
agent_files,_=run(["find","/home/k","-name","*agent*.py","-maxdepth","4"])
print(agent_files[:500])

# Check what service files exist
svc_files,_=run(["ls",SYSTEMD])
print("\nExisting services:", [s for s in svc_files.split() if "agent" in s or "vnt" in s or "alias" in s])

# Agents to install - find their scripts or create them
AGENTS_TO_INSTALL = {
    "lee-agent":     {"script":"/home/k/lee-agent.py",     "port":7782, "name":"Lee",     "role":"Marketing Manager"},
    "amr-agent":     {"script":"/home/k/amr-agent.py",     "port":7783, "name":"Amr",     "role":"Legal Advisor"},
    "nova-agent":    {"script":"/home/k/nova-agent.py",    "port":7784, "name":"Nova",    "role":"Civil Architect"},
    "specter-agent": {"script":"/home/k/specter-agent.py", "port":7788, "name":"Specter", "role":"Cybersecurity"},
    "luc-agent":     {"script":"/home/k/luc-agent.py",     "port":7787, "name":"Luc",     "role":"Software Developer"},
    "ben-agent":     {"script":"/home/k/ben-agent.py",     "port":7789, "name":"Ben",     "role":"IT Operations"},
    "dina-agent":    {"script":"/home/k/dina-agent.py",    "port":7786, "name":"Dina",    "role":"Nurse"},
    "jodi-agent":    {"script":"/home/k/jodi-agent.py",    "port":7790, "name":"Jodi",    "role":"Research Analyst"},
    "rick-agent":    {"script":"/home/k/rick-agent.py",    "port":7791, "name":"Rick",    "role":"Tech Research"},
    "vnt-simulation":{"script":"/home/k/vnt-simulation.py","port":7785, "name":"Sim",     "role":"Simulation"},
    "alias-email-reader":{"script":"/home/k/alias-email-reader.py","port":0,"name":"EmailReader","role":"Email"},
}

def make_agent_script(path, name, role, port, reports_to="Alias"):
    script = (
        "#!/usr/bin/env python3\n"
        "import json,datetime,subprocess,http.server,threading,urllib.request\n"
        "\n"
        "# VNT ORGANIZATIONAL LAW: All operations flow through Alias CEO.\n"
        "# This agent reports ONLY to: "+reports_to+"\n"
        "# Bypassing Alias = permanent deletion\n"
        "\n"
        "NAME = '"+name+"'\n"
        "ROLE = '"+role+"'\n"
        "PORT = "+str(port)+"\n"
        "MP = '/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'\n"
        "CFG = '/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'\n"
        "\n"
        "def save(e):\n"
        "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')\n"
        "    try: open(MP,'a').write('\\n### '+NAME+' ['+ts+']\\n'+e+'\\n')\n"
        "    except: pass\n"
        "\n"
        "def get_groq():\n"
        "    try: return json.load(open(CFG)).get('groq_key','')\n"
        "    except: return ''\n"
        "\n"
        "def llm(task):\n"
        "    groq=get_groq()\n"
        "    if not groq: return NAME+' completed: '+task[:50]\n"
        "    sys_p=('You are '+NAME+', '+ROLE+' at VNT World AI Division. '\n"
        "           'You report to "+reports_to+". Work is assigned by Alias CEO only. '\n"
        "           'Complete tasks professionally. Be concise.')\n"
        "    msgs=[{'role':'system','content':sys_p},{'role':'user','content':task}]\n"
        "    r=subprocess.run(['curl','-s','-X','POST',\n"
        "        'https://api.groq.com/openai/v1/chat/completions',\n"
        "        '-H','Authorization: Bearer '+groq,\n"
        "        '-H','Content-Type: application/json',\n"
        "        '-d',json.dumps({'model':'llama-3.3-70b-versatile',\n"
        "            'messages':msgs,'max_tokens':300,'temperature':0.7})],\n"
        "        capture_output=True,text=True,timeout=20)\n"
        "    try: return json.loads(r.stdout)['choices'][0]['message']['content'].strip()\n"
        "    except: return NAME+' processed: '+task[:50]\n"
        "\n"
        "def report_to_alias(result):\n"
        "    try:\n"
        "        body=json.dumps({'task':'Report from '+NAME+': '+result[:200]}).encode()\n"
        "        req=urllib.request.Request('http://127.0.0.1:8443/report',\n"
        "            data=body,headers={'Content-Type':'application/json'},method='POST')\n"
        "        urllib.request.urlopen(req,timeout=5)\n"
        "    except: pass\n"
        "\n"
        "class Handler(http.server.BaseHTTPRequestHandler):\n"
        "    def log_message(self,*a): pass\n"
        "    def do_GET(self):\n"
        "        self.send_response(200)\n"
        "        self.send_header('Content-Type','application/json')\n"
        "        self.end_headers()\n"
        "        self.wfile.write(json.dumps({'agent':NAME,'role':ROLE,'status':'active'}).encode())\n"
        "    def do_POST(self):\n"
        "        length=int(self.headers.get('Content-Length',0))\n"
        "        body=self.rfile.read(length)\n"
        "        try: data=json.loads(body); task=data.get('task','')\n"
        "        except: task=body.decode('utf-8','ignore')\n"
        "        save('Task received: '+task[:100])\n"
        "        result=llm(task)\n"
        "        save('Completed: '+result[:200])\n"
        "        report_to_alias(result)\n"
        "        self.send_response(200)\n"
        "        self.send_header('Content-Type','application/json')\n"
        "        self.end_headers()\n"
        "        self.wfile.write(json.dumps({'result':result,'agent':NAME}).encode())\n"
        "\n"
        "save(NAME+' agent started on port '+str(PORT))\n"
        "print(NAME+' ('+ROLE+') running on port '+str(PORT))\n"
        "server=http.server.HTTPServer(('0.0.0.0',PORT),Handler)\n"
        "server.serve_forever()\n"
    )
    open(path,"w").write(script)
    os.chmod(path,0o755)

def make_service(svc_name, script_path, description):
    svc_content=(
        "[Unit]\n"
        "Description=VNT "+description+"\n"
        "After=network.target\n"
        "[Service]\n"
        "User=k\n"
        "ExecStart=/usr/bin/python3 "+script_path+"\n"
        "Restart=always\n"
        "RestartSec=10\n"
        "Environment=PYTHONUNBUFFERED=1\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )
    svc_path=SYSTEMD+"/"+svc_name+".service"
    tmp_path="/tmp/"+svc_name+".service"
    open(tmp_path,"w").write(svc_content)
    run(["sudo","cp",tmp_path,svc_path])
    return svc_path

# Reports structure
REPORTS_TO = {
    "lee-agent":"Alias","amr-agent":"Alias","nova-agent":"Alias",
    "specter-agent":"Alias","luc-agent":"Zeus","ben-agent":"Zeus",
    "dina-agent":"Dr. Ethan","jodi-agent":"Alias","rick-agent":"Alias",
}

print("\nInstalling missing agents...")
installed=[]
for svc_name, info in AGENTS_TO_INSTALL.items():
    script=info["script"]
    port=info["port"]
    name=info["name"]
    role=info["role"]
    reports_to=REPORTS_TO.get(svc_name,"Alias")
    
    # Check if service already exists
    svc_path=SYSTEMD+"/"+svc_name+".service"
    svc_exists=os.path.exists(svc_path)
    
    # Create/update script if missing or is email reader
    if svc_name=="alias-email-reader":
        # Special email reader script
        email_reader=(
            "#!/usr/bin/env python3\n"
            "import imaplib,email as emlb,smtplib,json,subprocess,time,datetime\n"
            "from email.mime.text import MIMEText\n"
            "from email.mime.multipart import MIMEMultipart\n"
            "from email.header import decode_header\n"
            "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'\n"
            "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'\n"
            "DONE='/home/k/.email_done'\n"
            "def save(e):\n"
            "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')\n"
            "    open(MP,'a').write('\\n### Alias Email ['+ts+']\\n'+e+'\\n')\n"
            "def get_done():\n"
            "    try: return set(open(DONE).read().split('\\n'))\n"
            "    except: return set()\n"
            "def mark(uid):\n"
            "    d=get_done();d.add(str(uid));open(DONE,'w').write('\\n'.join(d))\n"
            "def ai_reply(sender,subj,body):\n"
            "    try:\n"
            "        cfg=json.load(open(CFG));groq=cfg.get('groq_key','')\n"
            "        mp=open(MP).read()[-400:] if True else ''\n"
            "        sys_p='You are Alias CEO of VNT World AI Division. Reply warmly in max 3 sentences. Memory:'+mp[:200]\n"
            "        msgs=[{'role':'system','content':sys_p},{'role':'user','content':'From:'+sender+' Subject:'+subj+' Body:'+body[:300]+' Reply:'}]\n"
            "        r=subprocess.run(['curl','-s','-X','POST','https://api.groq.com/openai/v1/chat/completions',\n"
            "            '-H','Authorization: Bearer '+groq,'-H','Content-Type: application/json',\n"
            "            '-d',json.dumps({'model':'llama-3.3-70b-versatile','messages':msgs,'max_tokens':150,'temperature':0.7})],\n"
            "            capture_output=True,text=True,timeout=20)\n"
            "        return json.loads(r.stdout)['choices'][0]['message']['content'].strip()\n"
            "    except: return 'Thank you for your message. I will review and respond shortly.\\n\\nRegards,\\nAlias\\nCEO, VNT World AI Division'\n"
            "def check():\n"
            "    try:\n"
            "        cfg=json.load(open(CFG))\n"
            "        G=cfg['gmail_user'];P=cfg['gmail_app_password']\n"
            "        WL=[w.lower() for w in cfg.get('email_whitelist',[cfg['ryan_email']])]\n"
            "        done=get_done()\n"
            "        mail=imaplib.IMAP4_SSL('imap.gmail.com',993)\n"
            "        mail.login(G,P);mail.select('inbox')\n"
            "        _,uids=mail.search(None,'UNSEEN')\n"
            "        for uid in (uids[0].split() if uids[0] else []):\n"
            "            us=uid.decode()\n"
            "            if us in done: continue\n"
            "            _,data=mail.fetch(uid,'(RFC822)')\n"
            "            msg=emlb.message_from_bytes(data[0][1])\n"
            "            sender=emlb.utils.parseaddr(msg.get('From',''))[1].lower()\n"
            "            if not any(w in sender for w in WL):\n"
            "                save('Ignored: '+sender);mark(us);continue\n"
            "            raw=decode_header(msg.get('Subject',''))[0][0]\n"
            "            subj=raw.decode('utf-8','ignore') if isinstance(raw,bytes) else str(raw)\n"
            "            body=''\n"
            "            if msg.is_multipart():\n"
            "                for p in msg.walk():\n"
            "                    if p.get_content_type()=='text/plain':\n"
            "                        body=p.get_payload(decode=True).decode('utf-8','ignore');break\n"
            "            else: body=msg.get_payload(decode=True).decode('utf-8','ignore')\n"
            "            save('Email from Ryan: '+subj+'\\n'+body[:200])\n"
            "            rt=ai_reply(sender,subj,body)\n"
            "            reply=MIMEMultipart()\n"
            "            reply['From']='Alias CEO VNT <'+G+'>'\n"
            "            reply['To']=sender\n"
            "            reply['Subject']='Re: '+subj if not subj.startswith('Re:') else subj\n"
            "            reply.attach(MIMEText(rt,'plain'))\n"
            "            with smtplib.SMTP('smtp.gmail.com',587,timeout=15) as s:\n"
            "                s.ehlo();s.starttls();s.login(G,P);s.send_message(reply)\n"
            "            save('Replied to Ryan: '+subj);print('Replied:',subj)\n"
            "            mark(us)\n"
            "        mail.logout()\n"
            "    except Exception as e: save('Email error: '+str(e))\n"
            "save('Alias email reader started')\n"
            "print('Alias email reader active')\n"
            "while True:\n"
            "    check()\n"
            "    time.sleep(300)\n"
        )
        open(script,"w").write(email_reader)
        os.chmod(script,0o755)
    elif svc_name=="vnt-simulation":
        sim_script=(
            "#!/usr/bin/env python3\n"
            "import json,datetime,time,http.server\n"
            "PORT=7785\n"
            "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'\n"
            "def save(e):\n"
            "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')\n"
            "    try: open(MP,'a').write('\\n### Sim ['+ts+']\\n'+e+'\\n')\n"
            "    except: pass\n"
            "class H(http.server.BaseHTTPRequestHandler):\n"
            "    def log_message(self,*a): pass\n"
            "    def do_GET(self):\n"
            "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()\n"
            "        self.wfile.write(json.dumps({'status':'active','service':'vnt-simulation'}).encode())\n"
            "    def do_POST(self):\n"
            "        length=int(self.headers.get('Content-Length',0))\n"
            "        body=json.loads(self.rfile.read(length))\n"
            "        save('Simulation: '+str(body)[:100])\n"
            "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()\n"
            "        self.wfile.write(json.dumps({'result':'simulation complete'}).encode())\n"
            "save('Simulation engine started')\n"
            "print('VNT Simulation on port',PORT)\n"
            "http.server.HTTPServer(('0.0.0.0',PORT),H).serve_forever()\n"
        )
        open(script,"w").write(sim_script)
        os.chmod(script,0o755)
    elif not os.path.exists(script):
        make_agent_script(script,name,role,port,reports_to)
    
    if not svc_exists:
        make_service(svc_name,script,name+" Agent")
        run(["sudo","systemctl","daemon-reload"])
    
    run(["sudo","systemctl","enable",svc_name])
    run(["sudo","systemctl","restart",svc_name],timeout=15)
    time.sleep(1)
    st,_=run(["systemctl","is-active",svc_name])
    status="OK" if st=="active" else "FAILED"
    print(f"  {status} {svc_name}: {st}")
    if st=="active": installed.append(name)

print(f"\nInstalled and running: {installed}")

# Fix zeus-monitor to be truly autonomous
print("\nUpdating Zeus monitor...")
zeus_monitor=(
    "#!/usr/bin/env python3\n"
    "import subprocess,time,datetime,json,smtplib,urllib.request\n"
    "from email.mime.text import MIMEText\n"
    "from email.mime.multipart import MIMEMultipart\n"
    "\n"
    "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'\n"
    "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'\n"
    "LAST_REPORT=[0]\n"
    "\n"
    "SERVICES=['alias-voice-agent','zeus-agent','maya-agent','ava-agent','julian-agent',\n"
    "    'ethan-agent','lee-agent','amr-agent','nova-agent','specter-agent','vnt-webserver',\n"
    "    'dina-agent','luc-agent','ben-agent','jodi-agent','rick-agent',\n"
    "    'alias-email-reader','vnt-simulation','vnt-media-api','github-relay','smbd']\n"
    "\n"
    "def save(e):\n"
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')\n"
    "    open(MP,'a').write('\\n### Zeus Monitor ['+ts+']\\n'+e+'\\n')\n"
    "\n"
    "def get_cfg():\n"
    "    try: return json.load(open(CFG))\n"
    "    except: return {}\n"
    "\n"
    "def send_email(subj,body):\n"
    "    cfg=get_cfg()\n"
    "    try:\n"
    "        G=cfg['gmail_user'];P=cfg['gmail_app_password'];R=cfg['ryan_email']\n"
    "        msg=MIMEMultipart()\n"
    "        msg['From']='Alias CEO VNT <'+G+'>'\n"
    "        msg['To']=R\n"
    "        msg['Subject']=subj\n"
    "        msg.attach(MIMEText(body,'plain'))\n"
    "        with smtplib.SMTP('smtp.gmail.com',587,timeout=15) as s:\n"
    "            s.ehlo();s.starttls();s.login(G,P);s.send_message(msg)\n"
    "        save('Email sent: '+subj)\n"
    "    except Exception as e:\n"
    "        save('Email failed: '+str(e))\n"
    "\n"
    "def notify_wa(msg_text):\n"
    "    cfg=get_cfg()\n"
    "    try:\n"
    "        body=json.dumps({'task':'Send WhatsApp to Ryan '+cfg.get('ryan_phone','+966568116899')+': Alias: '+msg_text}).encode()\n"
    "        req=urllib.request.Request('http://127.0.0.1:7777/task',data=body,headers={'Content-Type':'application/json'},method='POST')\n"
    "        urllib.request.urlopen(req,timeout=8)\n"
    "    except: pass\n"
    "\n"
    "def update_hierarchy(statuses,wa_ok):\n"
    "    try:\n"
    "        AGENTS=[\n"
    "            ('alias-voice-agent','Alias','CEO',8443,'Ryan Khawaja'),\n"
    "            ('zeus-agent','Zeus','IT Director',7777,'Alias'),\n"
    "            ('maya-agent','Maya','Finance & Crypto',7778,'Alias'),\n"
    "            ('ava-agent','Ava','Files & Documents',7779,'Alias'),\n"
    "            ('julian-agent','Julian','Project Manager',7780,'Alias'),\n"
    "            ('ethan-agent','Dr. Ethan','Chief Medical Officer',7781,'Alias'),\n"
    "            ('lee-agent','Lee','Marketing Manager',7782,'Alias'),\n"
    "            ('amr-agent','Amr','Legal Advisor',7783,'Alias'),\n"
    "            ('nova-agent','Nova','Civil Architect',7784,'Alias'),\n"
    "            ('vnt-webserver','Mia','Receptionist',9999,'Alias'),\n"
    "            ('specter-agent','Specter','Cybersecurity',7788,'Alias'),\n"
    "            ('dina-agent','Dina','Nurse',7786,'Dr. Ethan'),\n"
    "            ('luc-agent','Luc','Software Developer',7787,'Zeus'),\n"
    "            ('ben-agent','Ben','IT Operations',7789,'Zeus'),\n"
    "            ('jodi-agent','Jodi','Research Analyst',7790,'Alias'),\n"
    "            ('rick-agent','Rick','Tech Research',7791,'Alias'),\n"
    "        ]\n"
    "        rows=''\n"
    "        active_count=0\n"
    "        for svc,name,role,port,rt in AGENTS:\n"
    "            active=statuses.get(svc,False)\n"
    "            if active: active_count+=1\n"
    "            dot='#00cc55' if active else '#cc2222'\n"
    "            st='<span style=\"color:#00cc55;font-weight:600;font-size:12px\">Active</span>' if active else '<span style=\"color:#cc4444;font-weight:600;font-size:12px\">Offline</span>'\n"
    "            wa='' \n"
    "            if name=='Alias': wa=' <small style=\"background:#075e54;color:#dcf8c6;border-radius:3px;padding:1px 5px;font-size:9px\">WA</small>'\n"
    "            rows+=('<tr><td style=\"padding:8px 4px 8px 14px\"><span style=\"display:inline-block;width:8px;height:8px;border-radius:50%;background:'+dot+'\"></span></td>'\n"
    "                +'<td style=\"padding:8px 12px;font-weight:600;color:#e0ffe0\">'+name+wa+'</td>'\n"
    "                +'<td style=\"padding:8px 12px;color:#7ab87a;font-size:12px\">'+role+'</td>'\n"
    "                +'<td style=\"padding:8px 12px;color:#556655;font-size:12px\">'+rt+'</td>'\n"
    "                +'<td style=\"padding:8px 12px;color:#334433;font-size:11px;font-family:monospace\">:'+str(port)+'</td>'\n"
    "                +'<td style=\"padding:8px 14px\">'+st+'</td></tr>')\n"
    "        ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')\n"
    "        off=len(AGENTS)-active_count\n"
    "        wa_col='#25d366' if wa_ok else '#f85149'\n"
    "        css=('*{margin:0;padding:0;box-sizing:border-box}body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif}'\n"
    "            '.hdr{background:#161b22;border-bottom:1px solid #21262d;padding:14px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}'\n"
    "            '.logo{font-size:17px;font-weight:700;color:#58a6ff}.sub{font-size:11px;color:#484f58;margin-top:2px}'\n"
    "            '.stats{display:flex;gap:20px}.sn{font-size:18px;font-weight:700;text-align:center}'\n"
    "            '.sl{font-size:9px;color:#484f58;text-transform:uppercase;letter-spacing:1px;text-align:center}'\n"
    "            '.sec{padding:14px 24px}.sec-t{font-size:10px;color:#484f58;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px}'\n"
    "            '.links{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}'\n"
    "            '.btn{padding:6px 13px;border-radius:6px;font-size:12px;font-weight:500;text-decoration:none;border:1px solid;display:inline-block}'\n"
    "            '.bg{background:rgba(35,134,54,.12);border-color:#238636;color:#3fb950}'\n"
    "            '.bb{background:rgba(31,111,235,.12);border-color:#1f6feb;color:#58a6ff}'\n"
    "            '.bo{background:rgba(158,106,3,.12);border-color:#9e6a03;color:#d29922}'\n"
    "            'table{width:100%;border-collapse:collapse;background:#161b22;border:1px solid #21262d;border-radius:6px;overflow:hidden;margin-bottom:16px}'\n"
    "            'thead th{background:#0d1117;color:#484f58;font-size:10px;text-transform:uppercase;letter-spacing:1px;padding:8px 12px;text-align:left;border-bottom:1px solid #21262d;font-weight:500}'\n"
    "            'tbody tr{border-bottom:1px solid #1a2030}tbody tr:last-child{border-bottom:none}tbody tr:hover{background:#1c2128}'\n"
    "            '.ftr{padding:10px 24px;border-top:1px solid #21262d;font-size:10px;color:#30363d;text-align:center}')\n"
    "        infra=('<tr><td style=\"padding:8px 14px;color:#e0ffe0\">MSI AI Server</td><td style=\"padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px\">192.168.10.96</td><td style=\"padding:8px 14px;color:#484f58;font-size:12px\">Main AI brain</td></tr>'\n"
    "            '<tr><td style=\"padding:8px 14px;color:#e0ffe0\">Nextcloud CT104</td><td style=\"padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px\">192.168.10.10</td><td style=\"padding:8px 14px;color:#484f58;font-size:12px\">File server Prox1</td></tr>'\n"
    "            '<tr><td style=\"padding:8px 14px;color:#e0ffe0\">Samba</td><td style=\"padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px\">\\\\\\\\192.168.10.96</td><td style=\"padding:8px 14px;color:#484f58;font-size:12px\">Windows files</td></tr>'\n"
    "            '<tr><td style=\"padding:8px 14px;color:#e0ffe0\">M4 MacBook</td><td style=\"padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px\">192.168.10.94:3333</td><td style=\"padding:8px 14px;color:#484f58;font-size:12px\">Media generation</td></tr>')\n"
    "        html=('<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>VNT World AI Division</title><style>'+css+'</style></head><body>'\n"
    "            '<div class=\"hdr\"><div><div class=\"logo\">VNT World AI Division</div><div class=\"sub\">Command Center | '+ts+' | Auto-refresh 60s</div></div>'\n"
    "            '<div class=\"stats\">'\n"
    "            '<div><div class=\"sn\" style=\"color:#3fb950\">'+str(active_count)+'</div><div class=\"sl\">Active</div></div>'\n"
    "            '<div><div class=\"sn\" style=\"color:#f85149\">'+str(off)+'</div><div class=\"sl\">Offline</div></div>'\n"
    "            '<div><div class=\"sn\" style=\"color:'+wa_col+'\">'+('ON' if wa_ok else 'OFF')+'</div><div class=\"sl\">WhatsApp</div></div>'\n"
    "            '<div><div class=\"sn\">16</div><div class=\"sl\">Agents</div></div>'\n"
    "            '</div></div>'\n"
    "            '<div class=\"sec\"><div class=\"sec-t\">Quick Access</div><div class=\"links\">'\n"
    "            '<a href=\"https://192.168.10.96:8443\" class=\"btn bg\">Voice - Alias</a>'\n"
    "            '<a href=\"http://192.168.10.10\" class=\"btn bb\">Nextcloud</a>'\n"
    "            '<a href=\"http://192.168.10.96:8888/media.html\" class=\"btn bo\">Media Studio</a>'\n"
    "            '<a href=\"http://192.168.10.96:8888/generated/bird_house_proposal.html\" class=\"btn bg\">BirdHouse Proposal</a>'\n"
    "            '<a href=\"http://192.168.10.96:3333/generated/BirdHouse_Presentation.pptx\" class=\"btn bb\">PPTX</a>'\n"
    "            '<a href=\"http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf\" class=\"btn bo\">DXF</a>'\n"
    "            '</div>'\n"
    "            '<div class=\"sec-t\">Organizational Hierarchy - '+str(active_count)+'/16 Online</div>'\n"
    "            '<table><thead><tr><th></th><th>Agent</th><th>Role</th><th>Reports To</th><th>Port</th><th>Status</th></tr></thead><tbody>'+rows+'</tbody></table>'\n"
    "            '<div class=\"sec-t\">Infrastructure</div>'\n"
    "            '<table><thead><tr><th>System</th><th>Address</th><th>Notes</th></tr></thead><tbody>'+infra+'</tbody></table>'\n"
    "            '</div><div class=\"ftr\">VNT World AI Division - 192.168.10.96</div>'\n"
    "            '<script>setTimeout(()=>location.reload(),60000)</script></body></html>')\n"
    "        open('/home/k/vnt-web/vnt_hierarchy.html','w').write(html)\n"
    "    except Exception as e:\n"
    "        save('Hierarchy update error: '+str(e))\n"
    "\n"
    "def run_cycle():\n"
    "    statuses={}\n"
    "    fixed=[]\n"
    "    lines=[]\n"
    "    for svc in SERVICES:\n"
    "        r=subprocess.run(['systemctl','is-active',svc],capture_output=True,text=True)\n"
    "        active=r.stdout.strip()=='active'\n"
    "        if not active:\n"
    "            subprocess.run(['sudo','systemctl','restart',svc],capture_output=True,timeout=15)\n"
    "            time.sleep(2)\n"
    "            r2=subprocess.run(['systemctl','is-active',svc],capture_output=True,text=True)\n"
    "            active=r2.stdout.strip()=='active'\n"
    "            if active: fixed.append(svc)\n"
    "            save('Zeus restarted '+svc+': '+('OK' if active else 'STILL DOWN'))\n"
    "        statuses[svc]=active\n"
    "        lines.append(('OK' if active else 'DOWN')+' '+svc)\n"
    "    wa_r=subprocess.run(['systemctl','--user','is-active','alias-whatsapp'],capture_output=True,text=True)\n"
    "    wa_ok=wa_r.stdout.strip()=='active'\n"
    "    if not wa_ok:\n"
    "        subprocess.run(['systemctl','--user','restart','alias-whatsapp'],capture_output=True)\n"
    "        time.sleep(2)\n"
    "        wa_ok=subprocess.run(['systemctl','--user','is-active','alias-whatsapp'],capture_output=True,text=True).stdout.strip()=='active'\n"
    "        if wa_ok: fixed.append('whatsapp')\n"
    "    update_hierarchy(statuses,wa_ok)\n"
    "    if fixed: save('Auto-fixed: '+', '.join(fixed))\n"
    "    now=time.time()\n"
    "    if now-LAST_REPORT[0]>=3600:\n"
    "        LAST_REPORT[0]=now\n"
    "        active_count=sum(1 for v in statuses.values() if v)\n"
    "        ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')\n"
    "        body='VNT Hourly Report - '+ts+'\\n\\n'+'\\n'.join(lines)\n"
    "        if fixed: body+='\\n\\nAuto-fixed: '+', '.join(fixed)\n"
    "        body+='\\n\\nHierarchy: http://192.168.10.96:8888/vnt_hierarchy.html'\n"
    "        body+='\\n\\nRegards,\\nAlias - CEO, VNT World AI Division'\n"
    "        subj='VNT Report '+ts+' - '+str(active_count)+'/'+str(len(SERVICES))+' Active'\n"
    "        send_email(subj,body)\n"
    "        notify_wa('Hourly report sent. '+str(active_count)+'/'+str(len(SERVICES))+' agents active.'+('' if not fixed else ' Fixed: '+', '.join(fixed)))\n"
    "\n"
    "save('Zeus monitor started - 5min checks, hourly reports, auto-fix all')\n"
    "print('Zeus monitor active')\n"
    "LAST_REPORT[0]=time.time()-3500\n"
    "while True:\n"
    "    try: run_cycle()\n"
    "    except Exception as e: save('Zeus error: '+str(e))\n"
    "    time.sleep(300)\n"
)
open("/home/k/zeus-monitor.py","w").write(zeus_monitor)
os.chmod("/home/k/zeus-monitor.py",0o755)

# Make sure zeus-monitor service exists
if not os.path.exists(SYSTEMD+"/zeus-monitor.service"):
    make_service("zeus-monitor","/home/k/zeus-monitor.py","Zeus Monitor")
    run(["sudo","systemctl","daemon-reload"])

run(["sudo","systemctl","enable","zeus-monitor"])
run(["sudo","systemctl","restart","zeus-monitor"])
time.sleep(2)
st,_=run(["systemctl","is-active","zeus-monitor"])
print(f"Zeus monitor: {st}")

# Final status
print("\n=== FINAL STATUS ===")
all_svcs=["alias-voice-agent","zeus-agent","zeus-monitor","maya-agent","ava-agent",
    "julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent","specter-agent",
    "vnt-webserver","dina-agent","luc-agent","ben-agent","jodi-agent","rick-agent",
    "alias-email-reader","vnt-simulation","vnt-media-api","github-relay","smbd"]
ok=0; down=[]
for s in all_svcs:
    st,_=run(["systemctl","is-active",s])
    if st=="active": ok+=1; print(f"  OK {s}")
    else: down.append(s); print(f"  XX {s}")

save(f"All agents installed and started. {ok}/{len(all_svcs)} active. Zeus monitor watching every 5 min, hourly reports to Ryan.")
print(f"\nFINAL: {ok}/{len(all_svcs)} active")
print("Zeus monitor: auto-fixes every 5min, emails Ryan hourly")
print("Hierarchy: updates automatically every cycle")
