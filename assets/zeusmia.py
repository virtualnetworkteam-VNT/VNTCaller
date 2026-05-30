
import subprocess, os, json, datetime, base64, urllib.request, time, ast

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
log("FIX ZEUS + MIA + LANGGRAPH")
log("="*55)

# 1. ZEUS - the unit file points to old path. Find and fix the actual unit file.
log("\n[1] Fixing Zeus service path...")
# Where is the unit file?
unit_path,_=run("systemctl show zeus-agent -p FragmentPath --value",shell=True)
log(f"  Unit file location: {unit_path}")
# Old script path
old_zeus="/home/k/zeus-agent/zeus.py"
new_zeus="/home/k/zeus-agent.py"
# Check if old zeus.py exists and works
if os.path.exists(old_zeus):
    try:
        ast.parse(open(old_zeus).read())
        log(f"  Old zeus.py: exists, valid - using it")
        # Just kill port and restart with old path
        run("fuser -k 7777/tcp 2>/dev/null",shell=True)
        time.sleep(2)
        run(["sudo","systemctl","restart","zeus-agent"],timeout=12)
    except SyntaxError as e:
        log(f"  Old zeus.py BROKEN L{e.lineno} - replacing path with new script")
        # Rewrite unit to use new script
        unit=chr(10).join(["[Unit]","Description=VNT Zeus IT Director","After=network.target","",
            "[Service]","User=k","ExecStart=/usr/bin/python3 "+new_zeus,
            "Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
            "[Install]","WantedBy=multi-user.target"])
        open("/tmp/zeus-agent.s","w").write(unit)
        run(["sudo","cp","/tmp/zeus-agent.s",unit_path if unit_path else "/etc/systemd/system/zeus-agent.service"])
        run(["sudo","systemctl","daemon-reload"])
        run("fuser -k 7777/tcp 2>/dev/null",shell=True)
        time.sleep(2)
        run(["sudo","systemctl","restart","zeus-agent"],timeout=12)
else:
    # Old path doesn't exist - point unit to new script
    log("  Old zeus.py missing - pointing unit to new script")
    unit=chr(10).join(["[Unit]","Description=VNT Zeus IT Director","After=network.target","",
        "[Service]","User=k","ExecStart=/usr/bin/python3 "+new_zeus,
        "Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
        "[Install]","WantedBy=multi-user.target"])
    open("/tmp/zeus-agent.s","w").write(unit)
    run(["sudo","cp","/tmp/zeus-agent.s",unit_path if unit_path else "/etc/systemd/system/zeus-agent.service"])
    run(["sudo","systemctl","daemon-reload"])
    run("fuser -k 7777/tcp 2>/dev/null",shell=True)
    time.sleep(2)
    run(["sudo","systemctl","restart","zeus-agent"],timeout=12)

time.sleep(4)
zeus_st,_=run(["systemctl","is-active","zeus-agent"])
zeus_http,_=run("curl -s --connect-timeout 3 http://127.0.0.1:7777/ 2>/dev/null",shell=True,timeout=5)
log(f"  Zeus: service={zeus_st} http={'OK' if zeus_http else 'DOWN'}")
if not zeus_http:
    zerr,_=run("journalctl -u zeus-agent -n 5 --no-pager --quiet",shell=True)
    log(f"  Zeus error: {zerr[-200:]}")

# 2. MIA - service file is empty. Recreate it properly.
log("\n[2] Fixing Mia service...")
mia_unit_path,_=run("systemctl show mia-agent -p FragmentPath --value",shell=True)
log(f"  Mia unit: {mia_unit_path}")
# mia-agent.py was written in last fix. Create proper service.
unit=chr(10).join(["[Unit]","Description=VNT Mia Receptionist","After=network.target","",
    "[Service]","User=k","ExecStart=/usr/bin/python3 /home/k/mia-agent.py",
    "Restart=always","RestartSec=10","Environment=PYTHONUNBUFFERED=1","",
    "[Install]","WantedBy=multi-user.target"])
open("/tmp/mia-agent.s","w").write(unit)
run(["sudo","cp","/tmp/mia-agent.s","/etc/systemd/system/mia-agent.service"])
run(["sudo","systemctl","daemon-reload"])
run(["sudo","systemctl","enable","mia-agent"])
run("fuser -k 9999/tcp 2>/dev/null",shell=True)
time.sleep(2)
run(["sudo","systemctl","restart","mia-agent"],timeout=12)
time.sleep(4)
mia_st,_=run(["systemctl","is-active","mia-agent"])
mia_http,_=run("curl -s --connect-timeout 3 http://127.0.0.1:9999/ 2>/dev/null",shell=True,timeout=5)
log(f"  Mia: service={mia_st} http={'OK' if mia_http else 'DOWN'}")
if not mia_http:
    merr,_=run("journalctl -u mia-agent -n 5 --no-pager --quiet",shell=True)
    log(f"  Mia error: {merr[-200:]}")

# 3. LANGGRAPH - broken folder shadowing real package
log("\n[3] Fixing LangGraph import conflict...")
# Find what's shadowing it
shadow,_=run("python3 -c 'import langgraph;print(langgraph.__file__)' 2>&1",shell=True)
log(f"  langgraph location: {shadow[:120]}")
# Check for empty/broken langgraph dirs
for path in ["/home/k/langgraph","/home/k/langgraph.py","./langgraph","/home/k/.local/lib/python3.12/site-packages/langgraph"]:
    if os.path.exists(path):
        log(f"  Found: {path}")
# Clean reinstall
run("pip uninstall langgraph -y --break-system-packages 2>/dev/null",shell=True,timeout=60)
run("rm -rf /home/k/.local/lib/python3.12/site-packages/langgraph* 2>/dev/null",shell=True)
r,e=run("pip install langgraph --break-system-packages 2>&1 | tail -2",shell=True,timeout=180)
# Test import from a neutral directory
lg,_=run("cd /tmp && python3 -c 'import langgraph;print(langgraph.__version__)' 2>&1",shell=True)
log(f"  LangGraph (from /tmp): {lg[:80]}")

# 4. WhatsApp check
log("\n[4] WhatsApp...")
wa,_=run(["systemctl","--user","is-active","alias-whatsapp"])
if wa!="active":
    run(["systemctl","--user","restart","alias-whatsapp"])
    time.sleep(3)
    wa,_=run(["systemctl","--user","is-active","alias-whatsapp"])
log(f"  WhatsApp: {wa}")

# 5. FINAL TEST ALL 16
log("\n[5] Final test all agents...")
ok=0
for name,port in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),
                  ("Julian",7780),("Ethan",7781),("Lee",7782),("Amr",7783),
                  ("Nova",7784),("Specter",7788),("Luc",7787),("Ben",7789),
                  ("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999)]:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=4)
    st="OK" if h else "DOWN"
    if h:ok+=1
    log(f"  {name} :{port}: {st}")
log(f"\n  TOTAL: {ok}/16 agents | WhatsApp: {wa}")

full="\n".join(out)
push_result("zeusmia_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
