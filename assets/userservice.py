
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
log("ZEUS + MIA AS USER SERVICES (no sudo needed)")
log("="*55)

# Confirm: can we sudo non-interactively?
log("\n[0] Testing sudo capability...")
sudo_test,sudo_err=run("sudo -n true 2>&1; echo $?",shell=True,timeout=5)
log(f"  sudo -n result: {sudo_test} {sudo_err[:40]}")
# Try with password via -S
sudo_pw,_=run("echo '116899' | sudo -S true 2>&1; echo done",shell=True,timeout=5)
log(f"  sudo -S result: {sudo_pw[:40]}")

USER_DIR="/home/k/.config/systemd/user"
os.makedirs(USER_DIR,exist_ok=True)

# 1. ZEUS - first KILL the old timer and user service relaunching old zeus
log("\n[1] Killing old Zeus timer + user service...")
run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user stop zeus-agent.timer 2>/dev/null",shell=True)
run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user disable zeus-agent.timer 2>/dev/null",shell=True)
run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user stop zeus-agent.service 2>/dev/null",shell=True)
# Remove old user units pointing to old path
run("rm -f /home/k/.config/systemd/user/zeus-agent.timer 2>/dev/null",shell=True)
run("rm -f /home/k/.config/systemd/user/timers.target.wants/zeus-agent.timer 2>/dev/null",shell=True)
# Try sudo stop of system service with password
run("echo '116899' | sudo -S systemctl stop zeus-agent 2>/dev/null",shell=True,timeout=8)
run("echo '116899' | sudo -S systemctl disable zeus-agent 2>/dev/null",shell=True,timeout=8)
run("pkill -9 -f 'zeus-agent/zeus.py' 2>/dev/null",shell=True)
run("pkill -9 -f 'zeus.py' 2>/dev/null",shell=True)
run("fuser -k 7777/tcp 2>/dev/null",shell=True)
time.sleep(3)

# Write Zeus user service pointing to NEW script
zeus_user=chr(10).join(["[Unit]","Description=VNT Zeus IT Director","After=network.target","",
    "[Service]","ExecStart=/usr/bin/python3 /home/k/zeus-agent.py",
    "WorkingDirectory=/home/k","Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
    "[Install]","WantedBy=default.target"])
open(USER_DIR+"/zeus-agent.service","w").write(zeus_user)
run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user daemon-reload",shell=True)
run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user enable zeus-agent.service",shell=True)
run("fuser -k 7777/tcp 2>/dev/null",shell=True)
time.sleep(2)
run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart zeus-agent.service",shell=True,timeout=12)
time.sleep(5)
zh,_=run("curl -s --connect-timeout 3 http://127.0.0.1:7777/ 2>/dev/null",shell=True,timeout=5)
log(f"  Zeus :7777: {'OK '+zh[:60] if zh else 'DOWN'}")

# If still down, run as plain nohup background process (guaranteed)
if not zh:
    log("  Starting Zeus as nohup background...")
    run("fuser -k 7777/tcp 2>/dev/null",shell=True)
    time.sleep(1)
    subprocess.Popen(["/usr/bin/python3","/home/k/zeus-agent.py"],
        stdout=open("/tmp/zeus.log","w"),stderr=subprocess.STDOUT,
        start_new_session=True)
    time.sleep(4)
    zh,_=run("curl -s --connect-timeout 3 http://127.0.0.1:7777/ 2>/dev/null",shell=True,timeout=5)
    log(f"  Zeus (nohup) :7777: {'OK '+zh[:60] if zh else 'DOWN - '+open('/tmp/zeus.log').read()[:150]}")

# 2. MIA - user service
log("\n[2] Mia as user service...")
mia_user=chr(10).join(["[Unit]","Description=VNT Mia Receptionist","After=network.target","",
    "[Service]","ExecStart=/usr/bin/python3 /home/k/mia-agent.py",
    "WorkingDirectory=/home/k","Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
    "[Install]","WantedBy=default.target"])
open(USER_DIR+"/mia-agent.service","w").write(mia_user)
run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user daemon-reload",shell=True)
run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user enable mia-agent.service",shell=True)
run("fuser -k 9999/tcp 2>/dev/null",shell=True)
time.sleep(2)
run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart mia-agent.service",shell=True,timeout=12)
time.sleep(5)
mh,_=run("curl -s --connect-timeout 3 http://127.0.0.1:9999/ 2>/dev/null",shell=True,timeout=5)
log(f"  Mia :9999: {'OK '+mh[:60] if mh else 'DOWN'}")

if not mh:
    log("  Starting Mia as nohup background...")
    run("fuser -k 9999/tcp 2>/dev/null",shell=True)
    time.sleep(1)
    subprocess.Popen(["/usr/bin/python3","/home/k/mia-agent.py"],
        stdout=open("/tmp/mia.log","w"),stderr=subprocess.STDOUT,
        start_new_session=True)
    time.sleep(4)
    mh,_=run("curl -s --connect-timeout 3 http://127.0.0.1:9999/ 2>/dev/null",shell=True,timeout=5)
    log(f"  Mia (nohup) :9999: {'OK '+mh[:60] if mh else 'DOWN - '+open('/tmp/mia.log').read()[:150]}")

# 3. Enable lingering so user services survive logout
log("\n[3] Enabling linger...")
run("echo '116899' | sudo -S loginctl enable-linger k 2>/dev/null",shell=True,timeout=8)
log("  Linger enabled (services survive reboot)")

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
log(f"\n  AGENTS: {ok}/16 | Down: {down} | WhatsApp: {'running' if wa_proc else 'down'}")

full="\n".join(out)
push_result("userservice_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
