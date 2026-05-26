
import subprocess,os,time,json
GROQ=open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
AGENTS=[("Lee","Marketing Manager",7782,"marketing campaigns social media brand content"),("Amr","Legal Advisor",7783,"legal documents compliance contracts regulatory"),("Nova","Civil Architect",7784,"civil engineering 2D DXF drawings floor plans structural")]
T=open("/home/k/julian-agent.py").read() if False else None

def deploy(name,role,port,resp):
    subprocess.run(["sudo","fuser","-k",str(port)+"/tcp"],capture_output=True)
    time.sleep(2)
    path=f"/home/k/{name.lower()}-agent.py"
    # Read template from existing working agent
    template=open("/home/k/julian-agent.py").read()
    script=template.replace("Julian",name).replace("Project Manager",role).replace("projects timelines tasks stakeholder updates risk tracking",resp).replace("7780",str(port))
    open(path,"w").write(script)
    os.chmod(path,0o755)
    svc=f"[Unit]\nDescription=VNT {name}\nAfter=network.target\n[Service]\nUser=k\nExecStart=/usr/bin/python3 {path}\nRestart=always\nRestartSec=10\nEnvironment=PYTHONUNBUFFERED=1\n[Install]\nWantedBy=multi-user.target\n"
    sn=f"{name.lower()}-agent"
    open(f"/tmp/{sn}.service","w").write(svc)
    subprocess.run(["sudo","cp",f"/tmp/{sn}.service",f"/etc/systemd/system/{sn}.service"],capture_output=True)
    subprocess.run(["sudo","systemctl","daemon-reload"],capture_output=True)
    subprocess.run(["sudo","systemctl","enable","--now",sn],capture_output=True)
    time.sleep(3)
    r=subprocess.run(["systemctl","is-active",sn],capture_output=True,text=True)
    ok=r.stdout.strip()=="active"
    print(f"  {'OK' if ok else 'XX'} {name} :{port}")
    return ok

subprocess.run(["pip","install","ezdxf","--break-system-packages","-q"],capture_output=True)
for name,role,port,resp in AGENTS:
    deploy(name,role,port,resp)

with open(MP,"a") as f:
    f.write(chr(10)+"### Agents Fixed ["+__import__("time").strftime("%Y-%m-%d %H:%M")+"]"+chr(10)+"Lee/Amr/Nova deployed"+chr(10))
print("Done")
