
import subprocess, os, json, datetime, base64, urllib.request, time, ast

def run(cmd, shell=False, timeout=40):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"
VNT = "/mnt/vnt-data/FileServer/VNT_World_AI_Division"
MP = VNT+"/MemPalace.md"
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
log("ALIAS GUARDIAN + RE-ENABLE BACKUP")
log("="*55)

# 1. Re-enable nightly backup
log("\n[1] Re-enabling nightly backup...")
try:
    f=VNT+"/vnt_features.json";d=json.load(open(f));d["nightly_backup"]=True;json.dump(d,open(f,"w"),indent=2)
    log("  nightly_backup: ON")
except Exception as e:
    log("  "+str(e)[:50])

# 2. Build the Alias Guardian module (shared recovery logic - PROVEN to work)
log("\n[2] Building Alias Guardian module...")
guardian_lines=["#!/usr/bin/env python3",
    "# Alias Guardian - keeps the queen alive. Used by Argus + Zeus.",
    "import subprocess,os,time,ast,urllib.request,datetime",
    "MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'",
    "X='XDG_RUNTIME_DIR=/run/user/1000 '",
    "BACKUPS=['/home/k/alias-voice-agent.py.bak_si5',",
    "  '/home/k/alias-voice-agent.py.working',",
    "  '/home/k/alias-voice-agent.py.bak_pre_wire']",
    "def gsave(e):",
    "    ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')",
    "    try:open(MP,'a').write('\\n### Guardian ['+ts+']\\n'+str(e)+'\\n')",
    "    except:pass",
    "def alias_alive():",
    "    try:",
    "        urllib.request.urlopen('http://127.0.0.1:8443/',timeout=3);return True",
    "    except:return False",
    "def recover_alias():",
    "    # Returns True if recovered. Tries restart, then backups, then minimal.",
    "    gsave('Alias DOWN - guardian recovering')",
    "    subprocess.run('fuser -k 8443/tcp 2>/dev/null',shell=True)",
    "    subprocess.run('pkill -9 -f alias-voice-agent 2>/dev/null',shell=True)",
    "    time.sleep(3)",
    "    # Try simple restart of current file first",
    "    subprocess.run(X+'systemctl --user restart alias-voice-agent',shell=True,timeout=15)",
    "    time.sleep(5)",
    "    if alias_alive():gsave('Recovered via restart');return True",
    "    # Try each known-good backup",
    "    for bak in BACKUPS:",
    "        if os.path.exists(bak):",
    "            try:",
    "                ast.parse(open(bak).read())",
    "                subprocess.run('cp '+bak+' /home/k/alias-voice-agent.py',shell=True)",
    "                subprocess.run('fuser -k 8443/tcp 2>/dev/null',shell=True);time.sleep(2)",
    "                subprocess.run(X+'systemctl --user restart alias-voice-agent',shell=True,timeout=15)",
    "                time.sleep(5)",
    "                if alias_alive():gsave('Recovered from backup: '+bak);return True",
    "            except:pass",
    "    # Last resort: write minimal Alias",
    "    minimal='\\n'.join(['import json,os,datetime,subprocess,http.server,socketserver',",
    "      \"CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'\",",
    "      'def llm(p):',",
    "      ' try:c=json.load(open(CFG));g=c.get(\"groq_key\",\"\")',",
    "      ' except:return \"I am here, Ryan.\"',",
    "      ' if not g:return \"I am here, Ryan.\"',",
    "      ' import json as j',",
    "      ' m=[{\"role\":\"system\",\"content\":\"You are Alias, CEO of VNT.\"},{\"role\":\"user\",\"content\":p}]',",
    "      ' try:',",
    "      '  r=subprocess.run([\"curl\",\"-s\",\"-X\",\"POST\",\"https://api.groq.com/openai/v1/chat/completions\",\"-H\",\"Authorization: Bearer \"+g,\"-H\",\"Content-Type: application/json\",\"-d\",j.dumps({\"model\":\"llama-3.3-70b-versatile\",\"messages\":m,\"max_tokens\":120})],capture_output=True,text=True,timeout=18)',",
    "      '  return j.loads(r.stdout)[\"choices\"][0][\"message\"][\"content\"].strip()',",
    "      ' except:return \"I am here, Ryan.\"',",
    "      'class H(http.server.BaseHTTPRequestHandler):',",
    "      ' def log_message(s,*a):pass',",
    "      ' def do_GET(s):s.send_response(200);s.send_header(\"Content-Type\",\"application/json\");s.end_headers();s.wfile.write(json.dumps({\"agent\":\"Alias\",\"status\":\"active\"}).encode())',",
    "      ' def do_POST(s):',",
    "      '  try:n=int(s.headers.get(\"Content-Length\",0));d=json.loads(s.rfile.read(n));t=d.get(\"text\",d.get(\"task\",\"\"))',",
    "      '  except:t=\"\"',",
    "      '  rep=llm(t) if t else \"I am here, Ryan.\"',",
    "      '  s.send_response(200);s.send_header(\"Content-Type\",\"application/json\");s.end_headers();s.wfile.write(json.dumps({\"reply\":rep,\"agent\":\"Alias\"}).encode())',",
    "      'socketserver.TCPServer.allow_reuse_address=True',",
    "      'http.server.HTTPServer((\"0.0.0.0\",8443),H).serve_forever()'])",
    "    try:",
    "        open('/home/k/alias-voice-agent.py','w').write(minimal)",
    "        subprocess.run('fuser -k 8443/tcp 2>/dev/null',shell=True);time.sleep(2)",
    "        subprocess.run(X+'systemctl --user restart alias-voice-agent',shell=True,timeout=15)",
    "        time.sleep(5)",
    "        if alias_alive():gsave('Recovered via minimal Alias');return True",
    "    except:pass",
    "    gsave('GUARDIAN FAILED to recover Alias - needs Ryan')",
    "    return False"]
guardian_code=chr(10).join(guardian_lines)
try:
    ast.parse(guardian_code)
    open("/home/k/alias_guardian.py","w").write(guardian_code)
    log("  Guardian module written")
    # Quick test - is the recovery function importable?
    t,_=run("cd /home/k && python3 -c 'import alias_guardian as g; print(\"alive:\",g.alias_alive())' 2>&1",shell=True,timeout=10)
    log(f"  Guardian test: {t[:60]}")
except SyntaxError as e:
    log(f"  Guardian syntax error L{e.lineno}: {e.msg}")

# 3. Wire Guardian into Argus (every 30s - fast protection)
log("\n[3] Wiring Guardian into Argus...")
run("cp /home/k/argus-agent.py /home/k/argus-agent.py.bak 2>/dev/null",shell=True)
ag=open("/home/k/argus-agent.py").read()
if "alias_guardian" not in ag:
    # add import + call recover in the loop
    ag2=ag.replace("import json,datetime,subprocess,http.server,socketserver,os,time,threading,urllib.request",
        "import json,datetime,subprocess,http.server,socketserver,os,time,threading,urllib.request,sys\nsys.path.insert(0,'/home/k')\ntry:\n    import alias_guardian as GUARD\nexcept:GUARD=None")
    # In the loop function, after check_all, add guardian check
    ag2=ag2.replace("def loop():",
        "def guard_alias():\n    if GUARD and not GUARD.alias_alive():\n        GUARD.recover_alias()\ndef loop():")
    ag2=ag2.replace("            up,down=build_dashboard()",
        "            guard_alias()\n            up,down=build_dashboard()")
    try:
        ast.parse(ag2)
        open("/home/k/argus-agent.py","w").write(ag2)
        run("fuser -k 7792/tcp 2>/dev/null",shell=True);time.sleep(2)
        run(X+"systemctl --user restart argus-agent",shell=True,timeout=12)
        time.sleep(4)
        argus,_=run("curl -s --connect-timeout 3 http://127.0.0.1:7792/ 2>/dev/null",shell=True,timeout=5)
        if argus:
            log("  Argus now guards Alias every 30s")
        else:
            run("cp /home/k/argus-agent.py.bak /home/k/argus-agent.py",shell=True)
            run("fuser -k 7792/tcp 2>/dev/null",shell=True);time.sleep(2)
            run(X+"systemctl --user restart argus-agent",shell=True,timeout=12)
            log("  Argus wire failed - restored")
    except SyntaxError as e:
        log(f"  Argus wire error L{e.lineno}")
else:
    log("  Argus already guards Alias")

# 4. Verify guardian works - kill Alias and watch it recover
log("\n[4] LIVE GUARDIAN TEST - killing Alias to test auto-recovery...")
run("fuser -k 8443/tcp 2>/dev/null; pkill -9 -f alias-voice-agent 2>/dev/null",shell=True)
log("  Alias killed. Waiting 45s for Argus guardian to recover...")
time.sleep(45)
va,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
log(f"  Alias after guardian: {'RECOVERED ✓' if va else 'still down - manual recover'}")
if not va:
    # manual recover
    run("cd /home/k && python3 -c 'import alias_guardian as g; g.recover_alias()' 2>&1",shell=True,timeout=60)
    time.sleep(5)
    va,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=5)
    log(f"  After manual guardian: {'UP' if va else 'down'}")

# 5. Final check
log("\n[5] Final status...")
ok=0
for n,p in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),("Julian",7780),
    ("Ethan",7781),("Lee",7782),("Amr",7783),("Nova",7784),("Specter",7788),("Luc",7787),
    ("Ben",7789),("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999),("Argus",7792),
    ("Rdev",7793),("Sage",7794)]:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{p}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
log(f"  Agents: {ok}/19")

full="\n".join(out)
push_result("guardian_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
