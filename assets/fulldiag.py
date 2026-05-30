
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
ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

log("="*55)
log("FULL SYSTEM DIAGNOSTIC - "+ts)
log("="*55)

# 1. ALL 16 AGENTS - real test
log("\n[1] All 16 agents...")
agents=[("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),
        ("Julian",7780),("Ethan",7781),("Lee",7782),("Amr",7783),
        ("Nova",7784),("Specter",7788),("Luc",7787),("Ben",7789),
        ("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999)]
ok=0;down=[]
for name,port in agents:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
    else:down.append(name)
    log(f"  {name} :{port}: {'OK' if h else 'DOWN'}")
log(f"  AGENTS: {ok}/16 | Down: {down}")

# 2. User services status (did they survive?)
log("\n[2] User service status...")
for svc in ["zeus-agent","mia-agent","maya-agent","specter-agent"]:
    st,_=run(f"XDG_RUNTIME_DIR=/run/user/1000 systemctl --user is-active {svc} 2>&1",shell=True)
    log(f"  {svc}: {st}")

# 3. SPECTER - is it doing cybersec? Check its logs/activity
log("\n[3] Specter cybersecurity activity...")
spec_resp,_=run("curl -s --connect-timeout 3 http://127.0.0.1:7788/ 2>/dev/null",shell=True,timeout=5)
log(f"  Specter status: {spec_resp[:100] if spec_resp else 'DOWN'}")
# Check if specter has done any tasks (MemPalace entries)
spec_log,_=run("grep -c 'Specter' /mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md 2>/dev/null",shell=True)
log(f"  Specter MemPalace entries: {spec_log}")

# 4. WEB SERVER :8888 (serves hierarchy + studio)
log("\n[4] Web server :8888...")
web_st,_=run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user is-active vnt-webserver 2>&1",shell=True)
web_st2,_=run("systemctl is-active vnt-webserver 2>&1",shell=True)
listening,_=run("ss -tlnp 2>/dev/null | grep 8888",shell=True)
log(f"  vnt-webserver user: {web_st} | system: {web_st2}")
log(f"  Port 8888 listening: {listening if listening else 'NOTHING'}")
hier,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8888/vnt_hierarchy.html 2>/dev/null | head -c 60",shell=True,timeout=5)
log(f"  Hierarchy page: {hier[:60] if hier else 'NOT SERVING'}")
media_pg,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8888/media.html 2>/dev/null | head -c 60",shell=True,timeout=5)
log(f"  Media studio page: {media_pg[:60] if media_pg else 'NOT SERVING'}")
# Does the file exist?
hf,_=run("ls -la /home/k/vnt-web/vnt_hierarchy.html 2>&1",shell=True)
log(f"  Hierarchy file: {hf[:70]}")

# 5. MEDIA API :3333 on M4
log("\n[5] Media Studio API :3333 (M4)...")
m4_ping,_=run("ping -c 1 -W 2 192.168.10.94 2>&1 | grep -o '1 received' || echo 'no ping'",shell=True,timeout=6)
log(f"  M4 ping: {m4_ping}")
media_api,_=run("curl -s --connect-timeout 4 http://192.168.10.94:3333/ 2>/dev/null | head -c 80",shell=True,timeout=6)
log(f"  Media API :3333: {media_api[:80] if media_api else 'NOT RESPONDING'}")

# 6. PORTAL :8080
log("\n[6] Portal :8080...")
portal,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8080/ 2>/dev/null | head -c 60",shell=True,timeout=5)
log(f"  Portal: {portal[:60] if portal else 'DOWN'}")

# 7. SMBD file sharing
log("\n[7] smbd file sharing...")
smbd,_=run("systemctl is-active smbd 2>&1",shell=True)
log(f"  smbd: {smbd}")

# 8. PROX1 FILE SERVER investigation
log("\n[8] Prox1 file server (deep check)...")
def ssh_prox1(cmd,t=15):
    return run("sshpass -p '68116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.10.19 \""+cmd+"\"",shell=True,timeout=t)
p1,_=ssh_prox1("echo OK && hostname")
log(f"  Prox1 SSH: {p1[:40]}")
if "OK" in p1:
    # List containers
    cts,_=ssh_prox1("pct list 2>/dev/null")
    log(f"  Containers:\n{cts[:300]}")
    # Check storage
    stor,_=ssh_prox1("pvesm status 2>/dev/null")
    log(f"  Storage:\n{stor[:300]}")
    # Nextcloud CT104
    nc_status,_=ssh_prox1("pct status 104 2>/dev/null")
    log(f"  CT104 (Nextcloud): {nc_status[:40]}")

# 9. NEXTCLOUD file server :10
log("\n[9] Nextcloud 192.168.10.10...")
nc,_=run("curl -s --connect-timeout 4 http://192.168.10.10/ 2>/dev/null -o /dev/null -w '%{http_code}'",shell=True,timeout=6)
log(f"  Nextcloud HTTP: {nc}")

# 10. WhatsApp + voice
log("\n[10] WhatsApp + voice...")
wa,_=run("pgrep -f alias-baileys 2>/dev/null",shell=True)
voice,_=run("grep -o 'MichelleNeural' /home/k/alias-baileys/index.js | head -1",shell=True)
log(f"  WhatsApp: {'running' if wa else 'DOWN'} | Voice: {voice}")

# 11. Relay health
log("\n[11] Relay...")
relay_log,_=run("tail -2 /home/k/github-relay.log",shell=True)
log(f"  Last log:\n{relay_log}")

log("\n"+"="*55)
log(f"SUMMARY: {ok}/16 agents | Down: {down}")
log(f"Web:{web_st2} Media:{'OK' if media_api else 'down'} Portal:{'OK' if portal else 'down'}")
log(f"smbd:{smbd} Nextcloud:{nc} WhatsApp:{'OK' if wa else 'down'}")
log("="*55)

full="\n".join(out)
push_result("fulldiag_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
