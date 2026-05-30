
import subprocess,os,ast,time
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
SYSTEMD="/etc/systemd/system"
def run(c,shell=False,t=20):
    r=subprocess.run(c,shell=shell,capture_output=True,text=True,timeout=t)
    return r.stdout.strip()
def save(e):
    import datetime
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try:open(MP,"a").write("\n### Svc ["+ts+"]\n"+str(e)+"\n")
    except:pass
print("STEP4: SERVICES")
AGENTS=[("lee-agent","/home/k/lee-agent.py","Lee","Marketing",7782,"Alias"),
    ("amr-agent","/home/k/amr-agent.py","Amr","Legal",7783,"Alias"),
    ("nova-agent","/home/k/nova-agent.py","Nova","Architect",7784,"Alias"),
    ("specter-agent","/home/k/specter-agent.py","Specter","CyberSec",7788,"Alias"),
    ("luc-agent","/home/k/luc-agent.py","Luc","Developer",7787,"Zeus"),
    ("ben-agent","/home/k/ben-agent.py","Ben","IT Ops",7789,"Zeus"),
    ("dina-agent","/home/k/dina-agent.py","Dina","Nurse",7786,"Ethan"),
    ("jodi-agent","/home/k/jodi-agent.py","Jodi","Research",7790,"Alias"),
    ("rick-agent","/home/k/rick-agent.py","Rick","TechRes",7791,"Alias"),
    ("vnt-simulation","/home/k/vnt-simulation.py","Sim","Simulation",7785,"Alias"),]
def make_code(name,role,port,rt):
    return chr(10).join(["#!/usr/bin/env python3",
        "import json,datetime,subprocess,http.server,socketserver,os",
        "NAME='"+name+"';ROLE='"+role+"';PORT="+str(port),
        "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
        "CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'",
        "BRAIN='/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json'",
        "def save(e):",
        "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
        "    try:open(MP,'a').write('\\n### '+NAME+' ['+ts+']\\n'+str(e)+'\\n')",
        "    except:pass",
        "def llm(task):",
        "    try:cfg=json.load(open(CFG));groq=cfg.get('groq_key','')",
        "    except:return NAME+' done'",
        "    if not groq:return NAME+' done'",
        "    try:b=json.load(open(BRAIN)) if os.path.exists(BRAIN) else {};model=b.get('active_model','llama-3.3-70b-versatile')",
        "    except:model='llama-3.3-70b-versatile'",
        "    msgs=[{'role':'system','content':'You are '+NAME+', '+ROLE+' at VNT. Report to "+rt+". Concise.'},{'role':'user','content':task}]",
        "    r=subprocess.run(['curl','-s','-X','POST','https://api.groq.com/openai/v1/chat/completions',",
        "        '-H','Authorization: Bearer '+groq,'-H','Content-Type: application/json',",
        "        '-d',json.dumps({'model':model,'messages':msgs,'max_tokens':200,'temperature':0.7})],capture_output=True,text=True,timeout=20)",
        "    try:return json.loads(r.stdout)['choices'][0]['message']['content'].strip()",
        "    except:return NAME+' done'",
        "class H(http.server.BaseHTTPRequestHandler):",
        "    def log_message(self,*a):pass",
        "    def do_GET(self):",
        "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
        "        self.wfile.write(json.dumps({'agent':NAME,'role':ROLE,'status':'active'}).encode())",
        "    def do_POST(self):",
        "        try:n=int(self.headers.get('Content-Length',0));d=json.loads(self.rfile.read(n));task=d.get('task','')",
        "        except:task=''",
        "        save('T:'+task[:60]);r=llm(task);save('D:'+r[:60])",
        "        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()",
        "        self.wfile.write(json.dumps({'result':r,'agent':NAME}).encode())",
        "socketserver.TCPServer.allow_reuse_address=True",
        "save(NAME+' :'+str(PORT))",
        "print(NAME+' :'+str(PORT))",
        "try:http.server.HTTPServer(('0.0.0.0',PORT),H).serve_forever()",
        "except Exception as e:save('crash:'+str(e));raise"])
for svc,script,name,role,port,rt in AGENTS:
    if not os.path.exists(script):
        code=make_code(name,role,port,rt)
        try:
            ast.parse(code)
            open(script,"w").write(code);os.chmod(script,0o755)
        except SyntaxError as e:print("  Skip "+name)
    svc_path=SYSTEMD+"/"+svc+".service"
    if not os.path.exists(svc_path):
        sf=chr(10).join(["[Unit]","Description=VNT "+name,"After=network.target","",
            "[Service]","User=k","ExecStart=/usr/bin/python3 "+script,
            "Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
            "[Install]","WantedBy=multi-user.target"])
        open("/tmp/"+svc+".s","w").write(sf)
        subprocess.run(["sudo","cp","/tmp/"+svc+".s",svc_path],capture_output=True)
run(["sudo","systemctl","daemon-reload"])
for svc,script,name,role,port,rt in AGENTS:
    run(["sudo","systemctl","enable",svc]);run(["sudo","systemctl","restart",svc],t=10);time.sleep(0.2)
run("sudo apt-get install -y samba -q",shell=True,t=120)
for u,p in [("administrator","0568116899"),("khawaja","App159earance.VnT")]:
    run("sudo useradd -M -s /sbin/nologin "+u+" 2>/dev/null||true",shell=True)
    subprocess.run("sudo smbpasswd -a "+u,input=(p+"\n"+p+"\n").encode(),shell=True,capture_output=True,timeout=10)
    run("sudo smbpasswd -e "+u,shell=True)
run(["sudo","systemctl","restart","smbd","nmbd"],t=15)
run(["sudo","loginctl","enable-linger","k"])
run(["systemctl","--user","restart","alias-whatsapp"])
print("  Samba:"+run(["systemctl","is-active","smbd"])+" WA:"+run(["systemctl","--user","is-active","alias-whatsapp"]))
save("Services step done")
print("STEP4 DONE")
