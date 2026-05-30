
import subprocess, os, json, datetime, base64, urllib.request, time

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

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
log("KILLING STUCK PROCESSES + DIAGNOSING SERVICES")
log("="*55)

# 1. Kill ALL processes holding agent ports
log("\n[1] Killing stuck processes on agent ports...")
for port in [8443,7777,9999,8080,8888,7785]:
    pids,_=run(f"fuser {port}/tcp 2>/dev/null",shell=True,timeout=5)
    if pids:
        run(f"fuser -k {port}/tcp 2>/dev/null",shell=True,timeout=5)
        log(f"  Port {port}: killed {pids}")
    else:
        log(f"  Port {port}: clear")

# Kill any orphaned python agent processes
run("pkill -f 'alias-voice-agent.py' 2>/dev/null",shell=True)
run("pkill -f 'mia-agent.py' 2>/dev/null",shell=True)
run("pkill -f 'zeus-agent.py' 2>/dev/null",shell=True)
time.sleep(3)
log("  Orphaned processes killed")

# 2. Why won't services start? Check each one's actual error
log("\n[2] Diagnosing why services fail...")
for svc in ["alias-voice-agent","zeus-agent","mia-agent","vnt-portal","smbd"]:
    run(["sudo","systemctl","restart",svc],timeout=12)
    time.sleep(2)
    st,_=run(["systemctl","is-active",svc])
    if st!="active":
        err,_=run(f"journalctl -u {svc} -n 5 --no-pager --quiet",shell=True)
        log(f"  {svc}: {st}")
        log(f"    Error: {err[-200:]}")
    else:
        log(f"  {svc}: {st} OK")

# 3. Check if scripts exist and have valid syntax
log("\n[3] Checking agent scripts...")
import ast
for name,path in [("alias","/home/k/alias-voice-agent.py"),
                  ("zeus","/home/k/zeus-agent.py"),
                  ("mia","/home/k/mia-agent.py"),
                  ("portal","/home/k/vnt-portal.py")]:
    if os.path.exists(path):
        try:
            ast.parse(open(path).read())
            log(f"  {name}: exists, syntax valid")
        except SyntaxError as e:
            log(f"  {name}: SYNTAX ERROR L{e.lineno}: {e.msg}")
    else:
        log(f"  {name}: MISSING FILE")

# 4. Test Alias directly by running it manually to see real error
log("\n[4] Running Alias manually to capture error...")
test_out,test_err=run("timeout 5 python3 /home/k/alias-voice-agent.py 2>&1 | head -10",shell=True,timeout=10)
log(f"  Manual run output: {(test_out+test_err)[:300]}")

# 5. Now restart cleanly
log("\n[5] Clean restart of core services...")
run(["sudo","systemctl","daemon-reload"])
for svc in ["alias-voice-agent","zeus-agent","mia-agent"]:
    run(f"fuser -k $(systemctl show {svc} -p ExecStart | grep -o '[0-9]*' | head -1)/tcp 2>/dev/null",shell=True)
    run(["sudo","systemctl","restart",svc],timeout=12)
    time.sleep(3)
    st,_=run(["systemctl","is-active",svc])
    http_test=""
    port={"alias-voice-agent":8443,"zeus-agent":7777,"mia-agent":9999}.get(svc)
    if port:
        h,_=run(f"curl -s --connect-timeout 3 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=5)
        http_test="HTTP OK" if h else "HTTP DOWN"
    log(f"  {svc}: {st} | {http_test}")

# 6. Install LangGraph with full error capture
log("\n[6] LangGraph install (full output)...")
r,e=run("pip install langgraph --break-system-packages 2>&1 | tail -5",shell=True,timeout=180)
log(f"  Output: {(r+e)[-300:]}")
lg,_=run(["python3","-c","import langgraph;print(langgraph.__version__)"])
log(f"  LangGraph: {lg if lg else 'still not installed'}")

full="\n".join(out)
push_result("diag_result.txt",full)
push_result("latest_state.txt",full)
log("\nDONE")
