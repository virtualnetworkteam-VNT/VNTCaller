
import subprocess, os, json, datetime, base64, urllib.request, time

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

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
log("FORCE FIX ZEUS + MIA SYSTEMD")
log("="*55)

# 1. Find ALL zeus unit files (there's a duplicate)
log("\n[1] Finding all zeus unit files...")
units,_=run("find /etc/systemd /run/systemd /home/k/.config/systemd -iname '*zeus*' 2>/dev/null",shell=True)
log(f"  Zeus units found:\n{units}")
frag,_=run("systemctl show zeus-agent -p FragmentPath --value",shell=True)
log(f"  Active FragmentPath: {frag}")
drops,_=run("systemctl show zeus-agent -p DropInPaths --value",shell=True)
log(f"  Drop-ins: {drops}")

# 2. Stop zeus, kill old process, disable, remove ALL old units
log("\n[2] Cleaning Zeus completely...")
run(["sudo","systemctl","stop","zeus-agent"],timeout=10)
run(["sudo","systemctl","disable","zeus-agent"],timeout=10)
run("pkill -9 -f 'zeus-agent/zeus.py' 2>/dev/null",shell=True)
run("pkill -9 -f 'zeus.py' 2>/dev/null",shell=True)
run("fuser -k 7777/tcp 2>/dev/null",shell=True)
time.sleep(3)

# Write the unit fresh at the standard location, overwrite whatever's there
zeus_unit=chr(10).join(["[Unit]","Description=VNT Zeus IT Director","After=network.target","",
    "[Service]","User=k","ExecStart=/usr/bin/python3 /home/k/zeus-agent.py",
    "WorkingDirectory=/home/k","Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
    "[Install]","WantedBy=multi-user.target"])
open("/tmp/zeus-agent.service","w").write(zeus_unit)
run("sudo cp /tmp/zeus-agent.service /etc/systemd/system/zeus-agent.service",shell=True)
# Remove any old zeus-agent dir unit that might override
run("sudo rm -f /etc/systemd/system/zeus-agent.service.d/*.conf 2>/dev/null",shell=True)
run(["sudo","systemctl","daemon-reload"])
run(["sudo","systemctl","enable","zeus-agent"])
run("fuser -k 7777/tcp 2>/dev/null",shell=True)
time.sleep(2)
run(["sudo","systemctl","start","zeus-agent"],timeout=12)
time.sleep(5)
zh,_=run("curl -s --connect-timeout 3 http://127.0.0.1:7777/ 2>/dev/null",shell=True,timeout=5)
zexec,_=run("systemctl show zeus-agent -p ExecStart --value",shell=True)
log(f"  Zeus ExecStart now: {zexec[:70]}")
log(f"  Zeus :7777: {'OK '+zh[:50] if zh else 'DOWN'}")

# 3. MIA - the file isn't being found. Check /etc/systemd/system perms and recreate
log("\n[3] Mia - force create unit...")
mia_unit=chr(10).join(["[Unit]","Description=VNT Mia Receptionist","After=network.target","",
    "[Service]","User=k","ExecStart=/usr/bin/python3 /home/k/mia-agent.py",
    "WorkingDirectory=/home/k","Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
    "[Install]","WantedBy=multi-user.target"])
open("/tmp/mia-agent.service","w").write(mia_unit)
# Use tee with sudo to ensure write
r_cp,e_cp=run("sudo tee /etc/systemd/system/mia-agent.service < /tmp/mia-agent.service",shell=True)
exists,_=run("ls -la /etc/systemd/system/mia-agent.service 2>&1",shell=True)
log(f"  Mia unit file: {exists[:80]}")
run(["sudo","systemctl","daemon-reload"])
run(["sudo","systemctl","enable","mia-agent"])
run("fuser -k 9999/tcp 2>/dev/null",shell=True)
time.sleep(2)
run(["sudo","systemctl","start","mia-agent"],timeout=12)
time.sleep(5)
mh,_=run("curl -s --connect-timeout 3 http://127.0.0.1:9999/ 2>/dev/null",shell=True,timeout=5)
log(f"  Mia :9999: {'OK '+mh[:50] if mh else 'DOWN'}")
if not mh:
    ms,_=run("systemctl status mia-agent -n 6 --no-pager 2>&1",shell=True)
    log(f"  Mia status: {ms[-250:]}")

# 4. FINAL ALL 16
log("\n[4] FINAL STATUS...")
ok=0;down=[]
agents=[("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),
        ("Julian",7780),("Ethan",7781),("Lee",7782),("Amr",7783),
        ("Nova",7784),("Specter",7788),("Luc",7787),("Ben",7789),
        ("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999)]
for name,port in agents:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
    else:down.append(name)
    log(f"  {name} :{port}: {'OK' if h else 'DOWN'}")

wa_proc,_=run("pgrep -f alias-baileys 2>/dev/null",shell=True)
log(f"\n  AGENTS: {ok}/16 | Down: {down}")
log(f"  WhatsApp: {'running' if wa_proc else 'down'}")

# Update hierarchy page with real status
statuses={name:(name not in down) for name,port in agents}
try:
    rows=""
    for name,port in agents:
        a=statuses[name]
        dot="#00cc55" if a else "#cc2222"
        st="Active" if a else "Offline"
        col="#00cc55" if a else "#cc4444"
        rows+="<tr><td style='padding:8px 14px'><span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:"+dot+"'></span></td><td style='padding:8px 12px;font-weight:600;color:#e0ffe0'>"+name+"</td><td style='padding:8px 12px;font-family:monospace;color:#334433;font-size:11px'>:"+str(port)+"</td><td style='padding:8px 14px;color:"+col+";font-weight:600'>"+st+"</td></tr>"
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    html="<!DOCTYPE html><html><head><meta charset='UTF-8'><title>VNT</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,sans-serif}.h{background:#161b22;padding:14px 24px;border-bottom:1px solid #21262d}.lo{font-size:17px;font-weight:700;color:#58a6ff}table{width:100%;border-collapse:collapse;margin:16px 0}thead th{background:#0d1117;color:#484f58;font-size:10px;text-transform:uppercase;padding:8px 14px;text-align:left}tbody tr{border-bottom:1px solid #1a2030}</style><script>setTimeout(()=>location.reload(),60000)</script></head><body><div class='h'><div class='lo'>VNT World AI Division</div><div style='font-size:11px;color:#484f58'>"+str(ok)+"/16 active | "+ts+"</div></div><div style='padding:16px 24px'><table><thead><tr><th></th><th>Agent</th><th>Port</th><th>Status</th></tr></thead><tbody>"+rows+"</tbody></table></div></body></html>"
    open("/home/k/vnt-web/vnt_hierarchy.html","w").write(html)
    log("  Hierarchy page updated")
except Exception as e:
    log("  Hierarchy err: "+str(e)[:50])

full="\n".join(out)
push_result("force_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
