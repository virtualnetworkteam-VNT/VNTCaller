
import urllib.request, base64, os, json, subprocess

GH_TOKEN = open("/home/k/github-relay.py").read().split('GH = "')[1].split('"')[0]
req = urllib.request.Request(
    "https://api.github.com/repos/virtualnetworkteam-VNT/VNTCaller/contents/game/vnt_hierarchy.html",
    headers={"Authorization":"Bearer "+GH_TOKEN,"Accept":"application/vnd.github.v3+json"})
with urllib.request.urlopen(req,timeout=15) as r:
    content = base64.b64decode(json.loads(r.read())["content"])

open("/home/k/vnt-web/vnt_hierarchy.html","wb").write(content)
print("Hierarchy updated:", len(content), "bytes")

# Also enforce org law in mempalace
MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
import datetime
law = chr(10).join([
    "",
    "="*60,
    "VNT ORGANIZATIONAL LAW - Ryan Khawaja - "+datetime.datetime.now().strftime("%Y-%m-%d"),
    "="*60,
    "ALL operations flow through ALIAS (CEO). NO EXCEPTIONS.",
    "Hierarchy: Ryan -> Alias -> Direct Reports -> Alias -> Ryan",
    "Direct reports to Alias: Zeus,Maya,Ava,Julian,Dr.Ethan,Lee,Amr,Nova,Mia,Specter,Jodi,Rick",
    "Under Ethan: Dina",
    "Under Zeus: Luc, Ben",
    "Bypassing Alias = permanent deletion.",
    "="*60,
    "",
])
open(MP,"a").write(law)
print("Org law saved to MemPalace")

# Restart all offline agents
AGENTS = [
    ("alias-voice-agent","Alias"),("zeus-agent","Zeus"),("maya-agent","Maya"),
    ("ava-agent","Ava"),("julian-agent","Julian"),("ethan-agent","Dr.Ethan"),
    ("lee-agent","Lee"),("amr-agent","Amr"),("nova-agent","Nova"),
    ("specter-agent","Specter"),("dina-agent","Dina"),("luc-agent","Luc"),
    ("ben-agent","Ben"),("jodi-agent","Jodi"),("rick-agent","Rick"),
    ("vnt-webserver","Mia"),("alias-email-reader","Email"),("zeus-monitor","ZeusMonitor"),
    ("vnt-simulation","Sim"),("vnt-media-api","Media"),("github-relay","Relay"),
]
fixed=[]
for svc,name in AGENTS:
    r=subprocess.run(["systemctl","is-active",svc],capture_output=True,text=True)
    if r.stdout.strip()!="active":
        subprocess.run(["sudo","systemctl","restart",svc],capture_output=True,timeout=15)
        fixed.append(name)
subprocess.run(["systemctl","--user","restart","alias-whatsapp"],capture_output=True)
print("Fixed:", fixed if fixed else "none - all running")
print("Hierarchy live: http://192.168.10.96:8888/vnt_hierarchy.html")
