
import subprocess, os, json, datetime, base64, urllib.request

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def run(cmd, shell=False, timeout=20):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Results ["+ts+"]\n"+str(e)+"\n")
    except: pass

# Read GH token from relay file
relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"

def push_result(name, content):
    """Push command output back to GitHub results/ folder so Claude can read it"""
    try:
        api = f"https://api.github.com/repos/{REPO}/contents/results/{name}"
        req = urllib.request.Request(api, headers={"Authorization":"Bearer "+GH})
        try:
            with urllib.request.urlopen(req,timeout=10) as r: sha=json.loads(r.read()).get("sha","")
        except: sha=""
        data={"message":"result "+name,"content":base64.b64encode(content.encode()).decode()}
        if sha: data["sha"]=sha
        req2=urllib.request.Request(api,data=json.dumps(data).encode(),
            headers={"Authorization":"Bearer "+GH,"Content-Type":"application/json"},method="PUT")
        with urllib.request.urlopen(req2,timeout=15) as r2: return "content" in json.loads(r2.read())
    except Exception as e:
        return False

ts = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")

# ── GATHER COMPLETE SYSTEM STATE ────────────────────────
output = []
output.append("="*60)
output.append("VNT SYSTEM STATE REPORT - "+ts)
output.append("="*60)

# Services
output.append("\n[SERVICES]")
SVCS=["alias-voice-agent","zeus-agent","zeus-monitor","maya-agent","ava-agent",
      "julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent","specter-agent",
      "mia-agent","luc-agent","ben-agent","dina-agent","jodi-agent","rick-agent",
      "alias-email-reader","github-relay","vnt-portal","cf-tunnel",
      "rustdesk-hbbs","rustdesk-hbbr","smbd"]
for s in SVCS:
    st,_=run(["systemctl","is-active",s])
    output.append(f"  {s}: {st}")
wa,_=run(["systemctl","--user","is-active","alias-whatsapp"])
output.append(f"  alias-whatsapp: {wa}")

# Voice agent test
output.append("\n[VOICE AGENT TEST]")
va,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null",shell=True,timeout=6)
output.append(f"  :8443 response: {va[:200] if va else 'NO RESPONSE'}")

# Portal test
output.append("\n[PORTAL TEST]")
portal,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8080/ 2>/dev/null | head -c 100",shell=True,timeout=6)
output.append(f"  :8080 response: {portal[:100] if portal else 'NO RESPONSE'}")

# LangGraph
output.append("\n[LANGGRAPH]")
lg,_=run(["python3","-c","import langgraph;print(langgraph.__version__)"])
output.append(f"  Version: {lg if lg else 'NOT INSTALLED'}")

# Voice agent syntax + langgraph check
output.append("\n[ALIAS CODE]")
if os.path.exists("/home/k/alias-voice-agent.py"):
    c=open("/home/k/alias-voice-agent.py").read()
    output.append(f"  Has langgraph: {'langgraph' in c.lower()}")
    output.append(f"  Has Flow: {'flow' in c.lower() and 'langgraph' not in c.lower()}")
    import ast
    try: ast.parse(c); output.append("  Syntax: valid")
    except SyntaxError as e: output.append(f"  Syntax: BROKEN L{e.lineno}")

# WhatsApp TTS check
output.append("\n[WHATSAPP TTS]")
wa_log,_=run("journalctl --user -u alias-whatsapp -n 15 --no-pager --quiet 2>/dev/null",shell=True)
tts_errors=[l for l in wa_log.split("\n") if "TTS error" in l]
output.append(f"  TTS errors in recent log: {len(tts_errors)}")
idx_voice,_=run("grep -o 'en-US-[A-Za-z]*Neural' /home/k/alias-baileys/index.js | head -1",shell=True)
output.append(f"  Configured voice: {idx_voice if idx_voice else 'not found'}")

# Relay health
output.append("\n[RELAY]")
relay_log,_=run("tail -3 /home/k/github-relay.log",shell=True)
output.append(f"  Last log lines:\n{relay_log}")
gh_check,_=run("sed -n '3p' /home/k/github-relay.py",shell=True)
output.append(f"  GH line: {gh_check[:30]}")

# Asusi7
output.append("\n[ASUSI7]")
a7,_=run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 Alias@192.168.10.114 'echo OK && hostname' 2>&1",shell=True,timeout=10)
output.append(f"  SSH: {a7[:60]}")
a7_agent,_=run("curl -s --connect-timeout 4 http://192.168.10.114:7900/ 2>/dev/null",shell=True,timeout=6)
output.append(f"  Device agent :7900: {a7_agent[:80] if a7_agent else 'not responding'}")

# CF Tunnel URL
output.append("\n[CLOUDFLARE]")
import re
cf_log,_=run("journalctl -u cf-tunnel -n 40 --no-pager --quiet 2>/dev/null",shell=True)
m=re.search(r'https://[a-z0-9-]+\.trycloudflare\.com',cf_log or "")
output.append(f"  URL: {m.group(0) if m else 'NOT FOUND'}")

# Agent health checks - actually hit each port
output.append("\n[AGENT PORT TESTS]")
for name,port in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),
                  ("Julian",7780),("Ethan",7781),("Lee",7782),("Amr",7783),
                  ("Nova",7784),("Specter",7788),("Luc",7787),("Ben",7789),
                  ("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999)]:
    resp,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=4)
    status="OK" if resp else "DOWN"
    output.append(f"  {name} :{port}: {status}")

full_output = "\n".join(output)

# Save locally and push back to GitHub
save(full_output)
pushed = push_result(f"state_{ts}.txt", full_output)
pushed_latest = push_result("latest_state.txt", full_output)

print(full_output)
print("\n"+"="*60)
print(f"Result pushed to GitHub results/: {pushed and pushed_latest}")
print("Claude can now read: results/latest_state.txt")
