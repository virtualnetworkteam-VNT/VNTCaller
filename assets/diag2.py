
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
log("ZEUS+MIA MANUAL RUN DIAGNOSIS")
log("="*55)

# 1. ZEUS - run the new script manually, capture the REAL crash
log("\n[1] Zeus manual run (full error)...")
run(["sudo","systemctl","stop","zeus-agent"],timeout=10)
run("pkill -9 -f zeus 2>/dev/null",shell=True)
run("fuser -k 7777/tcp 2>/dev/null",shell=True)
time.sleep(3)
zout,zerr=run("timeout 6 python3 /home/k/zeus-agent.py 2>&1",shell=True,timeout=10)
log(f"  Zeus output: {(zout+zerr)[:400]}")

# Check if port 7777 is held by something else
held,_=run("ss -tlnp 2>/dev/null | grep 7777",shell=True)
log(f"  Port 7777 held by: {held if held else 'nothing'}")

# 2. MIA - run manually
log("\n[2] Mia manual run (full error)...")
run(["sudo","systemctl","stop","mia-agent"],timeout=10)
run("pkill -9 -f mia-agent 2>/dev/null",shell=True)
run("fuser -k 9999/tcp 2>/dev/null",shell=True)
time.sleep(3)
mout,merr=run("timeout 6 python3 /home/k/mia-agent.py 2>&1",shell=True,timeout=10)
log(f"  Mia output: {(mout+merr)[:400]}")
held9,_=run("ss -tlnp 2>/dev/null | grep 9999",shell=True)
log(f"  Port 9999 held by: {held9 if held9 else 'nothing'}")

# 3. If manual run shows "started" with no error, the script WORKS
# The issue is systemd. Start them as background processes directly + via systemd
log("\n[3] Starting Zeus and Mia...")
run("fuser -k 7777/tcp 2>/dev/null",shell=True)
run("fuser -k 9999/tcp 2>/dev/null",shell=True)
time.sleep(2)
run(["sudo","systemctl","start","zeus-agent"],timeout=12)
run(["sudo","systemctl","start","mia-agent"],timeout=12)
time.sleep(5)

zh,_=run("curl -s --connect-timeout 3 http://127.0.0.1:7777/ 2>/dev/null",shell=True,timeout=5)
mh,_=run("curl -s --connect-timeout 3 http://127.0.0.1:9999/ 2>/dev/null",shell=True,timeout=5)
log(f"  Zeus :7777: {'OK '+zh[:50] if zh else 'DOWN'}")
log(f"  Mia :9999: {'OK '+mh[:50] if mh else 'DOWN'}")

# Get systemd status if still down
if not zh:
    zs,_=run("systemctl status zeus-agent -n 8 --no-pager 2>&1",shell=True)
    log(f"  Zeus status: {zs[-300:]}")
if not mh:
    ms,_=run("systemctl status mia-agent -n 8 --no-pager 2>&1",shell=True)
    log(f"  Mia status: {ms[-300:]}")

# 4. LANGGRAPH - test if it actually imports (version attr may just not exist)
log("\n[4] LangGraph real import test...")
lg_import,_=run("cd /tmp && python3 -c 'from langgraph.graph import StateGraph,END; print(\"LANGGRAPH_WORKS\")' 2>&1",shell=True)
log(f"  Import test: {lg_import[:120]}")

# 5. WHATSAPP - correct user session check
log("\n[5] WhatsApp (correct check)...")
wa,_=run("XDG_RUNTIME_DIR=/run/user/$(id -u k) systemctl --user is-active alias-whatsapp 2>&1",shell=True)
# Try via loginctl
wa2,_=run("sudo -u k XDG_RUNTIME_DIR=/run/user/1000 systemctl --user is-active alias-whatsapp 2>&1",shell=True)
wa_proc,_=run("pgrep -f alias-baileys 2>/dev/null",shell=True)
log(f"  WA systemctl: {wa}")
log(f"  WA process running: {'YES pid='+wa_proc if wa_proc else 'NO'}")

# 6. FINAL
log("\n[6] Final all 16...")
ok=0;down=[]
for name,port in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),
                  ("Julian",7780),("Ethan",7781),("Lee",7782),("Amr",7783),
                  ("Nova",7784),("Specter",7788),("Luc",7787),("Ben",7789),
                  ("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999)]:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
    else:down.append(name)
log(f"  TOTAL: {ok}/16 | Down: {down}")
log(f"  LangGraph: {'WORKS' if 'LANGGRAPH_WORKS' in lg_import else 'broken'}")
log(f"  WhatsApp process: {'running' if wa_proc else 'not running'}")

full="\n".join(out)
push_result("diag2_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
