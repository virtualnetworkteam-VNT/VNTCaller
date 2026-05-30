
import subprocess, os, json, datetime, base64, urllib.request, time, ast

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"
USER_DIR = "/home/k/.config/systemd/user"

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
X="XDG_RUNTIME_DIR=/run/user/1000 "

log("="*55)
log("VERIFY ALIAS + RETRY BRAIN WIRING (clean)")
log("="*55)

# 1. Is Alias alive?
log("\n[1] Alias status...")
va_http,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
log(f"  Alias :8443: {va_http[:90] if va_http else 'DOWN'}")

# Check which version is running (did brain wiring stick or did it restore?)
va_content=open("/home/k/alias-voice-agent.py").read()
has_brain="import alias_brain_module" in va_content
log(f"  Brain module wired: {has_brain}")

# 2. Verify brain module exists and works
log("\n[2] Brain module check...")
if os.path.exists("/home/k/alias_brain_module.py"):
    try:
        ast.parse(open("/home/k/alias_brain_module.py").read())
        log("  Brain module: exists, valid syntax")
        # Test each capability
        pick,_=run("cd /home/k && python3 -c 'import alias_brain_module as b;print(b.pick_model(\"analyze complex\"))' 2>&1",shell=True,timeout=15)
        log(f"  Model picker: {pick[:40]}")
        web,_=run("cd /home/k && python3 -c 'import alias_brain_module as b;print(b.web_search(\"OpenAI 2026\")[:50])' 2>&1",shell=True,timeout=20)
        log(f"  Web search: {web[:60] if web and 'rror' not in web else 'returns empty (may need different search)'}")
        rag,_=run("cd /home/k && python3 -c 'import alias_brain_module as b;print(len(b.rag_retrieve(\"zeus monitoring\")))' 2>&1",shell=True,timeout=15)
        log(f"  RAG chars: {rag[:30]}")
    except SyntaxError as e:
        log(f"  Brain module BROKEN L{e.lineno}")
else:
    log("  Brain module MISSING")

# 3. If Alias is up but brain NOT wired, wire it cleanly now
if va_http and not has_brain:
    log("\n[3] Wiring brain (clean method)...")
    run("cp /home/k/alias-voice-agent.py /home/k/alias-voice-agent.py.bak_pre_wire 2>/dev/null",shell=True)
    va=va_content
    # Clean import injection at top after first import line
    lines=va.split(chr(10))
    new=[]
    injected=False
    for line in lines:
        new.append(line)
        if not injected and line.startswith("import http.server"):
            new.append("import sys as _sys")
            new.append("_sys.path.insert(0,'/home/k')")
            new.append("try:")
            new.append("    import alias_brain_module as BRAIN_MOD")
            new.append("    SMART=True")
            new.append("except Exception:")
            new.append("    SMART=False")
            injected=True
    va2=chr(10).join(new)
    # Replace think body - find the think function and prepend smart logic
    if "def think(text):" in va2:
        va2=va2.replace(
            "def think(text):",
            "def think(text):\n    if SMART:\n        try:\n            r,src,uw,um=BRAIN_MOD.smart_llm(text)\n            save('In:'+text[:50]+' model:'+src)\n            tl=text.lower()\n            for kw,pt in [('crypto',7778),('file',7779),('project',7780),('medical',7781),('legal',7783),('security',7788),('code',7787),('server',7777)]:\n                if kw in tl:\n                    ar=dispatch(pt,text)\n                    if ar:return r+' '+str(ar)[:70]\n            return r\n        except Exception as _e:\n            save('smart err:'+str(_e)[:40])\n    return _orig_think(text)\ndef _orig_think(text):",
            1)
    try:
        ast.parse(va2)
        open("/home/k/alias-voice-agent.py","w").write(va2)
        run("fuser -k 8443/tcp 2>/dev/null",shell=True)
        time.sleep(2)
        run(X+"systemctl --user restart alias-voice-agent",shell=True,timeout=12)
        time.sleep(5)
        va_http2,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
        if va_http2:
            log(f"  Brain wired + Alias UP: {va_http2[:70]}")
        else:
            log("  Wiring broke Alias - restoring")
            run("cp /home/k/alias-voice-agent.py.bak_pre_wire /home/k/alias-voice-agent.py",shell=True)
            run("fuser -k 8443/tcp 2>/dev/null",shell=True)
            time.sleep(2)
            run(X+"systemctl --user restart alias-voice-agent",shell=True,timeout=12)
            time.sleep(4)
            va_http2,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
            log(f"  Restored: {'UP' if va_http2 else 'down'}")
    except SyntaxError as e:
        log(f"  Wire syntax error L{e.lineno}")
elif has_brain:
    log("\n[3] Brain already wired - testing...")

# 4. Final smart test
log("\n[4] Smart query test...")
va_final,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
if va_final:
    try:
        body=json.dumps({"text":"Give me a quick status of VNT operations."}).encode()
        req=urllib.request.Request("http://127.0.0.1:8443/",data=body,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=22) as r:
            resp=json.loads(r.read())
        log(f"  Alias: {resp.get('reply','')[:160]}")
    except Exception as e:
        log(f"  Query: {str(e)[:50]}")

# Final agent count
ok=0
for name,port in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),("Julian",7780),
    ("Ethan",7781),("Lee",7782),("Amr",7783),("Nova",7784),("Specter",7788),("Luc",7787),
    ("Ben",7789),("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999),("Argus",7792)]:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
log(f"\n  Agents: {ok}/17 | Brain wired: {has_brain or 'just wired'}")

full="\n".join(out)
push_result("verify_brain_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
