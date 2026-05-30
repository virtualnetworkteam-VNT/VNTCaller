
import subprocess, os, json, datetime, base64, urllib.request, time, ast

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"
VNT = "/mnt/vnt-data/FileServer/VNT_World_AI_Division"
MP = VNT+"/MemPalace.md"
FLAGS = VNT+"/vnt_features.json"

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
log("TOGGLE CONTROLS + GUIDE + M4 FIX")
log("="*55)

# 1. Wire feature toggles into Alias WhatsApp commands
log("\n[1] Adding toggle commands to Alias brain...")
# Add toggle handling to the brain module so 'enable/disable X' works via WhatsApp
bm=open("/home/k/alias_brain_module.py").read()
if "def toggle_feature" not in bm:
    toggle_fn=chr(10).join(["",
        "def toggle_feature(text):",
        "    FLAGS='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_features.json'",
        "    tl=text.lower()",
        "    feat_map={'daily routine':'daily_routine','daily report':'daily_routine','backup':'nightly_backup',",
        "        'growth':'alias_growth','self improve':'auto_self_improve','self-improve':'auto_self_improve',",
        "        'health':'hourly_health','monitoring':'hourly_health'}",
        "    matched=None",
        "    for phrase,key in feat_map.items():",
        "        if phrase in tl:matched=key;break",
        "    if not matched:return None",
        "    try:flags=json.load(open(FLAGS))",
        "    except:flags={}",
        "    if any(w in tl for w in ['enable','turn on','start','activate']):",
        "        flags[matched]=True;json.dump(flags,open(FLAGS,'w'),indent=2)",
        "        return 'Enabled: '+matched",
        "    elif any(w in tl for w in ['disable','turn off','stop','deactivate']):",
        "        flags[matched]=False;json.dump(flags,open(FLAGS,'w'),indent=2)",
        "        return 'Disabled: '+matched",
        "    elif 'status' in tl or 'which' in tl:",
        "        return 'Features: '+json.dumps(flags)",
        "    return None"])
    bm=bm+toggle_fn
    try:
        ast.parse(bm)
        open("/home/k/alias_brain_module.py","w").write(bm)
        log("  Toggle function added to brain")
    except SyntaxError as e:
        log(f"  Toggle syntax error L{e.lineno}")

# Wire toggle into Alias think() - check toggle BEFORE normal processing
va=open("/home/k/alias-voice-agent.py").read()
if "BRAIN_MOD.toggle_feature" not in va and "SMART" in va:
    va=va.replace(
        "    if SMART:\n        try:\n            r,src,uw,um=BRAIN_MOD.smart_llm(text)",
        "    if SMART:\n        try:\n            _tog=BRAIN_MOD.toggle_feature(text)\n            if _tog:save('Toggle: '+_tog);return _tog\n            r,src,uw,um=BRAIN_MOD.smart_llm(text)")
    try:
        ast.parse(va)
        open("/home/k/alias-voice-agent.py","w").write(va)
        run("fuser -k 8443/tcp 2>/dev/null",shell=True)
        time.sleep(2)
        run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart alias-voice-agent",shell=True,timeout=12)
        time.sleep(5)
        va_test,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
        log(f"  Alias with toggles: {'UP' if va_test else 'restoring backup'}")
        if not va_test:
            run("cp /home/k/alias-voice-agent.py.bak_pre_wire /home/k/alias-voice-agent.py 2>/dev/null",shell=True)
            run("fuser -k 8443/tcp 2>/dev/null",shell=True);time.sleep(2)
            run("XDG_RUNTIME_DIR=/run/user/1000 systemctl --user restart alias-voice-agent",shell=True,timeout=12)
    except SyntaxError as e:
        log(f"  Wire toggle error L{e.lineno}")
else:
    log("  Toggles already wired or SMART not present")

# 2. Fix M4 media - ensure LaunchAgent keeps it alive
log("\n[2] Restarting M4 media + ensuring persistence...")
def ssh_m4(cmd,t=20):
    return run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 Alias@192.168.10.94 \""+cmd+"\"",shell=True,timeout=t)
m4,_=ssh_m4("echo OK")
if "OK" in m4:
    PY="/Users/alias/miniforge3/envs/vnt/bin/python"
    ssh_m4("launchctl unload /Users/alias/Library/LaunchAgents/com.vnt.mediaapi.plist 2>/dev/null")
    ssh_m4("lsof -ti:3333 | xargs kill -9 2>/dev/null")
    time.sleep(2)
    ssh_m4("launchctl load /Users/alias/Library/LaunchAgents/com.vnt.mediaapi.plist 2>/dev/null")
    time.sleep(4)
    media,_=run("curl -s --connect-timeout 5 http://192.168.10.94:3333/ 2>/dev/null",shell=True,timeout=7)
    log(f"  Media API :3333: {'OK' if media else 'will retry via LaunchAgent KeepAlive'}")
else:
    log("  M4 not reachable now")

# 3. Write the control guide to MemPalace AND a standalone file
log("\n[3] Writing control guide...")
guide="""
================================================================
VNT CONTROL GUIDE - FOR RYAN
================================================================

## WHAT RUNS AUTOMATICALLY NOW:

1. DAILY ROUTINE (every day 8:00 AM)
   - Checks: relay/Claude access, all 19 agents, chain of command,
     all 6 VNT devices, services, Alias growth, runs backup
   - Sends you: email report + WhatsApp summary
   - WHY: you wake up knowing everything is healthy without checking

2. NIGHTLY BACKUP (every day 2:00 AM)
   - Archives entire VNT brain (~100KB): all agents, memory, configs
   - Keeps 30 daily + 12 weekly copies on the 1TB drive
   - WHY: if disaster hits, restore everything in one command

3. ZEUS MONITOR (every 5 min) - auto-heals dead services
4. ARGUS MONITOR (every 30 sec) - live dashboard
5. SAGE RESEARCH (every 6 hrs) - feeds Alias new knowledge

## HOW TO CONTROL (tell Alias on WhatsApp +966580906977):

  'disable daily routine'   -> stops daily reports
  'enable daily routine'    -> resumes
  'disable backup'          -> stops nightly backup
  'enable backup'           -> resumes
  'disable monitoring'      -> stops health emails
  'enable self-improve'     -> lets Rdev auto-edit Alias code
  'disable self-improve'    -> Rdev only advises (default, safer)
  'feature status'          -> shows what's on/off

## DISASTER RECOVERY (if VNT breaks):

  Restore latest backup (one command on AI server):
    python3 /home/k/vnt-restore.py
  
  Restore a specific backup:
    python3 /home/k/vnt-restore.py /mnt/vnt-data/.../vnt_backup_DATE.tar.gz
  
  Backups live in:
    /mnt/vnt-data/FileServer/VNT_World_AI_Division/disaster_recovery/

## RUN ANYTHING MANUALLY:

  Daily routine now:  python3 /home/k/vnt-daily-routine.py
  Backup now:         python3 /home/k/vnt-backup.py
  Check all agents:   (the daily routine does this)

## THE 1TB DRIVE (/mnt/vnt-data):

  - 880GB total, was 1% used
  - Now hosts: FileServer + MemPalace + disaster_recovery backups
     + knowledge_base (Alias growth) + room for local AI models
  - Plenty of space for Alias to grow

## DASHBOARDS:

  Portal:     http://192.168.10.96:8080/  (khawaja / App159earance.VnT)
  Monitor:    http://192.168.10.96:8888/monitor.html
  Hierarchy:  http://192.168.10.96:8888/vnt_hierarchy.html
  Media:      http://192.168.10.96:8888/media.html
================================================================
"""
try:
    open(MP,"a").write(guide)
    open(VNT+"/CONTROL_GUIDE.md","w").write(guide)
    log("  Guide saved to MemPalace + CONTROL_GUIDE.md")
except Exception as e:
    log("  Guide save: "+str(e)[:50])

# 4. Show current feature flags
log("\n[4] Current feature flags:")
try:
    flags=json.load(open(FLAGS))
    for k,v in flags.items():
        log(f"  {k}: {'ON' if v else 'OFF'}")
except Exception as e:
    log("  "+str(e)[:50])

# 5. Test a toggle command end-to-end
log("\n[5] Testing toggle command...")
va_up,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
if va_up:
    try:
        body=json.dumps({"text":"feature status"}).encode()
        req=urllib.request.Request("http://127.0.0.1:8443/",data=body,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=15) as r:
            resp=json.loads(r.read())
        log(f"  'feature status' -> {resp.get('reply','')[:120]}")
    except Exception as e:
        log(f"  Toggle test: {str(e)[:50]}")

# Final agent count
ok=0
for n,p in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),("Julian",7780),
    ("Ethan",7781),("Lee",7782),("Amr",7783),("Nova",7784),("Specter",7788),("Luc",7787),
    ("Ben",7789),("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999),("Argus",7792),
    ("Rdev",7793),("Sage",7794)]:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{p}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
log(f"\n  Agents: {ok}/19")

full="\n".join(out)
push_result("toggle_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
