
import subprocess, os, datetime, json

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
PROJECT_DIR = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/BirdHouse_Project"
GEN_DIR = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/generated_media"
WEB_GEN = "/home/k/vnt-web/generated"
GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]

print("="*55)
print("VNT FULL STATUS CHECK")
print("="*55)

# 1. All services
print(chr(10)+"=== SERVICES ===")
services = [
    ("alias-voice-agent","Alias Voice :8443"),
    ("alias-whatsapp","Alias WhatsApp"),
    ("zeus-agent","Zeus :7777"),
    ("zeus-monitor","Zeus Monitor"),
    ("maya-agent","Maya :7778"),
    ("ava-agent","Ava :7779"),
    ("julian-agent","Julian :7780"),
    ("ethan-agent","Ethan :7781"),
    ("lee-agent","Lee :7782"),
    ("amr-agent","Amr :7783"),
    ("nova-agent","Nova :7784"),
    ("dina-agent","Dina :7786"),
    ("luc-agent","Luc :7787"),
    ("specter-agent","Specter :7788"),
    ("ben-agent","Ben :7789"),
    ("jodi-agent","Jodi :7790"),
    ("rick-agent","Rick :7791"),
    ("vnt-simulation","Simulation :7785"),
    ("vnt-webserver","Web Portal :8888"),
    ("vnt-media-api","Media API :3333"),
    ("vnt-call-bridge","Call Bridge :9999"),
    ("github-relay","GitHub Relay"),
]
ok_count = 0
down = []
for svc, label in services:
    r=subprocess.run(["systemctl","is-active",svc],capture_output=True,text=True)
    status=r.stdout.strip()
    icon = "OK" if status=="active" else "XX"
    if status=="active": ok_count+=1
    else: down.append(label)
    print(f"  {icon} {label}: {status}")

r2=subprocess.run(["systemctl","--user","is-active","alias-whatsapp"],capture_output=True,text=True)
wa=r2.stdout.strip()
print(f"  {'OK' if wa=='active' else 'XX'} WhatsApp (user): {wa}")

print(f"\nServices: {ok_count}/{len(services)} active")
if down: print("DOWN:", ", ".join(down))

# 2. Email - check if postfix configured
print(chr(10)+"=== EMAIL STATUS ===")
r3=subprocess.run(["which","sendmail"],capture_output=True,text=True)
r4=subprocess.run(["systemctl","is-active","postfix"],capture_output=True,text=True)
print("sendmail:", "found" if r3.returncode==0 else "NOT installed")
print("postfix:", r4.stdout.strip())

# Check if any emails were sent
r5=subprocess.run(["ls","/var/mail/"],capture_output=True,text=True)
print("Mail queue:", r5.stdout.strip() or "empty/no mail dir")

# Check daily report script
report_exists = os.path.exists("/home/k/vnt-daily-report.py")
print("Daily report script:", "exists" if report_exists else "MISSING")

# Check cron
r6=subprocess.run(["crontab","-l"],capture_output=True,text=True)
print("Cron jobs:", r6.stdout.strip() if r6.stdout.strip() else "NONE")

# 3. BirdHouse project files
print(chr(10)+"=== BIRDHOUSE PROJECT ===")
if os.path.exists(PROJECT_DIR):
    docs = os.listdir(PROJECT_DIR+"/documents") if os.path.exists(PROJECT_DIR+"/documents") else []
    reports = os.listdir(PROJECT_DIR+"/reports") if os.path.exists(PROJECT_DIR+"/reports") else []
    drawings = os.listdir(PROJECT_DIR+"/drawings") if os.path.exists(PROJECT_DIR+"/drawings") else []
    print("Documents:", docs)
    print("Reports:", reports)
    print("Drawings:", drawings)
else:
    print("Project directory NOT FOUND")

# Check web proposal
proposal = "/home/k/vnt-web/generated/bird_house_proposal.html"
dxf = "/home/k/vnt-web/generated/birdhouse_site_plan.dxf"
print("Proposal HTML:", "EXISTS" if os.path.exists(proposal) else "MISSING")
print("DXF Drawing:", "EXISTS" if os.path.exists(dxf) else "MISSING")

# 4. Generated media
print(chr(10)+"=== GENERATED MEDIA ===")
gen_dirs = [GEN_DIR, WEB_GEN, "/home/k/vnt-web/generated"]
for d in gen_dirs:
    if os.path.exists(d):
        files = os.listdir(d)
        imgs = [f for f in files if f.endswith((".png",".jpg",".jpeg"))]
        vids = [f for f in files if f.endswith((".mp4",".avi",".mov"))]
        models = [f for f in files if f.endswith((".obj",".glb",".dxf",".aab"))]
        print(f"{d}:")
        print(f"  Images: {len(imgs)} | Videos: {len(vids)} | 3D/Other: {len(models)}")
        if imgs: print(f"  Latest images: {imgs[-3:]}")
        if vids: print(f"  Videos: {vids}")
        break

# 5. Fix what is down and send proper email
print(chr(10)+"=== FIXING DOWN SERVICES ===")
for svc, label in services:
    r=subprocess.run(["systemctl","is-active",svc],capture_output=True,text=True)
    if r.stdout.strip() != "active":
        print(f"Restarting {svc}...")
        subprocess.run(["sudo","systemctl","restart",svc],capture_output=True)

# Fix WhatsApp
subprocess.run(["systemctl","--user","restart","alias-whatsapp"],capture_output=True)

# 6. Setup email properly
print(chr(10)+"=== SETTING UP EMAIL ===")
# Install postfix if not present
r7=subprocess.run(["which","sendmail"],capture_output=True,text=True)
if r7.returncode != 0:
    print("Installing postfix...")
    subprocess.run(["sudo","DEBIAN_FRONTEND=noninteractive","apt-get","install","-y","postfix","mailutils","libsasl2-modules"],
        capture_output=True,timeout=120)

# Configure postfix for Gmail relay
postfix_main = "/etc/postfix/main.cf"
if os.path.exists(postfix_main):
    content = open(postfix_main).read()
    if "smtp.gmail.com" not in content:
        relay_config = """
# Gmail relay
relayhost = [smtp.gmail.com]:587
smtp_use_tls = yes
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
"""
        with open(postfix_main,"a") as f:
            f.write(relay_config)
        print("Postfix Gmail relay configured")
        print("NOTE: Need Gmail app password for kraheelw@yahoo.com or aliasvnt@gmail.com")
    else:
        print("Postfix already configured")

# 7. Write the full status to MemPalace and send via WhatsApp to Ryan
import urllib.request
status_msg = f"""VNT STATUS REPORT [{datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}]
Services Active: {ok_count}/{len(services)}
Down: {", ".join(down) if down else "None"}

BirdHouse Proposal: {"READY" if os.path.exists(proposal) else "MISSING"}
DXF Drawing: {"READY" if os.path.exists(dxf) else "MISSING"}
Proposal URL: http://192.168.10.96:8888/generated/bird_house_proposal.html

EMAIL: {"postfix installed" if os.path.exists(postfix_main) else "NOT configured"} - needs Gmail app password to send

Images/Videos: check http://192.168.10.96:3333/generated/
"""

open(MP,"a").write(chr(10)+"### Status Check "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+chr(10)+status_msg+chr(10))

# Try to send via WhatsApp bridge
try:
    body=json.dumps({"task":"Send Ryan this status report via WhatsApp: "+status_msg[:500]}).encode()
    req=urllib.request.Request("http://127.0.0.1:7777/task",data=body,headers={"Content-Type":"application/json"},method="POST")
    urllib.request.urlopen(req,timeout=10)
    print("Status sent to Zeus to forward to Ryan")
except: pass

print(chr(10)+"="*55)
print(status_msg)
print("="*55)
