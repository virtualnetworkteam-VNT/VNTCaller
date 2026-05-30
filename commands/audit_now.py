
import subprocess, os, json, datetime, ast

MP   = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
BRAIN= "/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json"

def run(cmd, shell=False, timeout=10):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Audit ["+ts+"]\n"+e+"\n")
    except: pass

print("="*55)
print("FULL DEPLOYMENT AUDIT")
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*55)

results = {}

# 1. LangGraph
print("\n[1] LangGraph status...")
lg = run(["python3","-c","import langgraph;print(langgraph.__version__)"])
print("  LangGraph:", lg if lg else "NOT INSTALLED")
results["langgraph"] = lg if lg else "NOT INSTALLED"

# 2. Voice agent - is it LangGraph or old Flow?
print("\n[2] Voice agent type...")
va_path = "/home/k/alias-voice-agent.py"
if os.path.exists(va_path):
    content = open(va_path).read()
    has_lg = "langgraph" in content.lower()
    has_flow = "flow" in content.lower() and "langgraph" not in content.lower()
    try: ast.parse(content); syntax = "valid"
    except SyntaxError as e: syntax = "BROKEN L"+str(e.lineno)
    va_st = run(["systemctl","is-active","alias-voice-agent"])
    va_http = run("curl -s --connect-timeout 3 http://127.0.0.1:8443/ 2>/dev/null", shell=True, timeout=6)
    print("  Syntax:", syntax)
    print("  Service:", va_st)
    print("  HTTP test:", va_http[:60] if va_http else "not responding")
    print("  LangGraph in code:", has_lg)
    print("  Still uses Flow:", has_flow)
    results["voice_agent"] = {"syntax":syntax,"service":va_st,"langgraph":has_lg,"http":bool(va_http)}
else:
    print("  MISSING")
    results["voice_agent"] = "MISSING"

# 3. All services
print("\n[3] All services...")
SVCS = ["alias-voice-agent","zeus-agent","zeus-monitor","maya-agent","ava-agent",
        "julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent",
        "specter-agent","mia-agent","luc-agent","ben-agent","dina-agent",
        "jodi-agent","rick-agent","alias-email-reader","github-relay",
        "vnt-portal","cf-tunnel","rustdesk-hbbs","rustdesk-hbbr","smbd"]
active=[];inactive=[]
for s in SVCS:
    st = run(["systemctl","is-active",s])
    if st=="active": active.append(s)
    else: inactive.append(s+"="+st)
wa = run(["systemctl","--user","is-active","alias-whatsapp"])
print(f"  Active: {len(active)}/{len(SVCS)}")
print(f"  WA: {wa}")
print(f"  Inactive: {inactive}")
results["services"] = {"active":len(active),"total":len(SVCS),"wa":wa,"inactive":inactive}

# 4. VNT Agent App
print("\n[4] VNT Agent App...")
web_dir = "/home/k/vnt-web/vnt-agent"
portal_ok = os.path.exists("/home/k/vnt-portal.py")
app_ok = os.path.exists(web_dir+"/index.html")
device_agent_ok = os.path.exists("/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/VNT_Agent_App/backend/vnt_device_agent.py")
extension_ok = os.path.exists("/mnt/vnt-data/FileServer/VNT_World_AI_Division/Projects/VNT_Agent_App/extension/manifest.json")
portal_st = run(["systemctl","is-active","vnt-portal"])
portal_http = run("curl -s --connect-timeout 3 http://127.0.0.1:8080/ 2>/dev/null | grep -o 'VNT\|Login'",shell=True,timeout=6)
print(f"  Portal service: {portal_st}")
print(f"  Portal HTTP: {portal_http if portal_http else 'not responding'}")
print(f"  Web app: {app_ok}")
print(f"  Device agent: {device_agent_ok}")
print(f"  Browser extension: {extension_ok}")
results["app"] = {"portal":portal_st,"web_app":app_ok,"device_agent":device_agent_ok,"extension":extension_ok}

# 5. Asusi7 full access
print("\n[5] Asusi7 access...")
def ssh7(cmd,t=10):
    return run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 Alias@192.168.10.114 \""+cmd+"\"",shell=True,timeout=t)
conn = ssh7("echo OK")
if "OK" in conn:
    shortcut = ssh7("powershell -Command \"Test-Path ([Environment]::GetFolderPath('Desktop')+'\\VNT Agent.lnk')\"")
    agent_test = run("curl -s --connect-timeout 3 http://192.168.10.114:7900/ 2>/dev/null",shell=True,timeout=6)
    py_v = ssh7("python --version 2>&1")
    print(f"  SSH: connected")
    print(f"  Desktop shortcut: {shortcut}")
    print(f"  Device agent :7900: {'running' if agent_test else 'not running'}")
    print(f"  Python: {py_v[:20]}")
    results["asusi7"] = {"ssh":"ok","shortcut":shortcut,"agent":bool(agent_test)}
else:
    print("  SSH: FAILED")
    results["asusi7"] = "SSH_FAILED"

# 6. CF Tunnel URL
print("\n[6] Cloudflare tunnel...")
cf_st = run(["systemctl","is-active","cf-tunnel"])
import re
cf_log = run("journalctl -u cf-tunnel -n 40 --no-pager --quiet 2>/dev/null",shell=True)
cf_url = ""
if cf_log:
    m = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', cf_log)
    if m: cf_url = m.group(0)
print(f"  Service: {cf_st}")
print(f"  URL: {cf_url if cf_url else 'not found in logs'}")
results["cf"] = {"status":cf_st,"url":cf_url}

# 7. Self-healing (Zeus monitor)
print("\n[7] Self-healing...")
zm_st = run(["systemctl","is-active","zeus-monitor"])
zm_path = "/home/k/zeus-monitor.py"
zm_ok = False
if os.path.exists(zm_path):
    try: ast.parse(open(zm_path).read()); zm_ok=True
    except: pass
print(f"  Zeus monitor service: {zm_st}")
print(f"  Zeus monitor syntax: {'valid' if zm_ok else 'broken'}")
results["zeus"] = {"service":zm_st,"syntax_ok":zm_ok}

# SUMMARY
print("\n"+"="*55)
print("AUDIT SUMMARY")
print("="*55)
print(f"LangGraph:     {results['langgraph']}")
print(f"Voice agent:   service={results.get('voice_agent',{}).get('service','?')} http={results.get('voice_agent',{}).get('http','?')} langgraph={results.get('voice_agent',{}).get('langgraph','?')}")
print(f"Services:      {results.get('services',{}).get('active','?')}/{results.get('services',{}).get('total','?')} active | WA={results.get('services',{}).get('wa','?')}")
print(f"Portal:        {results.get('app',{}).get('portal','?')} | http={bool(portal_http)}")
print(f"VNT Agent app: web={results.get('app',{}).get('web_app','?')} device={results.get('app',{}).get('device_agent','?')}")
print(f"Asusi7:        {results.get('asusi7',{}).get('ssh','?')} | shortcut={results.get('asusi7',{}).get('shortcut','?')}")
print(f"CF Tunnel:     {results.get('cf',{}).get('status','?')} | {results.get('cf',{}).get('url','no url')}")
print(f"Zeus monitor:  {results.get('zeus',{}).get('service','?')}")
print("="*55)

save("Audit: "+json.dumps(results, indent=2)[:500])
