
import subprocess, os, json, datetime, time

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

def run(cmd, shell=False, timeout=30):
    r=subprocess.run(cmd,shell=shell,capture_output=True,text=True,timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\n### Diagnosis ["+ts+"]\n"+e+"\n")

print("="*60)
print("REAL DIAGNOSIS - NO BULLSHIT")
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*60)

# 1. WHATSAPP LOGS - actual content
print("\n=== WHATSAPP LOGS ===")
wa_paths = [
    "/home/k/alias-baileys/baileys.log",
    "/home/k/alias-baileys/wa.log",
    "/home/k/.baileys/baileys.log",
    "/tmp/wa.log",
]
wa_found = False
for p in wa_paths:
    if os.path.exists(p):
        content = open(p).read()
        print(f"LOG: {p}")
        print(content[-1000:])
        wa_found = True
        break

if not wa_found:
    # Check systemd log
    wa_log,_ = run(["journalctl","--user","-u","alias-whatsapp","-n","30","--no-pager"])
    print("WA systemd log:")
    print(wa_log[-800:] if wa_log else "NO LOGS FOUND")
    
    # Check process
    wa_proc,_ = run("ps aux | grep baileys | grep -v grep",shell=True)
    print("WA process:", wa_proc or "NOT RUNNING")
    
    # Check files
    wa_dir,_ = run("ls -la /home/k/alias-baileys/ 2>/dev/null | head -20",shell=True)
    print("WA dir:", wa_dir)

# 2. VOICE AGENT STATUS
print("\n=== VOICE AGENT :8443 ===")
va_status,_ = run(["systemctl","is-active","alias-voice-agent"])
print("Service:", va_status)

va_log,_ = run(["journalctl","-u","alias-voice-agent","-n","20","--no-pager"])
print("Log:")
print(va_log[-600:] if va_log else "no logs")

# Check port
port_check,_ = run("ss -tlnp | grep 8443",shell=True)
print("Port 8443:", port_check or "NOT LISTENING")

# Check script
if os.path.exists("/home/k/alias-voice-agent.py"):
    # Check for syntax errors
    syntax,_ = run(["python3","-m","py_compile","/home/k/alias-voice-agent.py"])
    print("Script syntax:", "OK" if not syntax else "ERROR: "+syntax[:200])
else:
    print("Voice script: MISSING")

# 3. ALL SERVICE STATUS
print("\n=== ALL SERVICES ===")
SVCS=[
    "alias-voice-agent","zeus-agent","zeus-monitor","maya-agent","ava-agent",
    "julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent",
    "specter-agent","vnt-webserver","alias-email-reader","vnt-simulation",
    "luc-agent","ben-agent","dina-agent","jodi-agent","rick-agent",
    "github-relay","smbd","alias-si","alias-upgrade-engine","zeus-monitor"
]
ok=0; down=[]
for s in SVCS:
    st,_ = run(["systemctl","is-active",s])
    if st=="active": ok+=1; print(f"  OK  {s}")
    else: down.append(s); print(f"  XX  {s}: {st}")

wa,_ = run(["systemctl","--user","is-active","alias-whatsapp"])
print(f"  {'OK' if wa=='active' else 'XX'}  alias-whatsapp: {wa}")

print(f"\nSummary: {ok}/{len(SVCS)} active")
print(f"Down: {down}")

# 4. VOICE AGENT SCRIPT CHECK - what went wrong
print("\n=== VOICE SCRIPT ANALYSIS ===")
va_path = "/home/k/alias-voice-agent.py"
if os.path.exists(va_path):
    content = open(va_path).read()
    lines = content.split("\n")
    print(f"Script size: {len(content)} chars, {len(lines)} lines")
    # Check for common issues
    issues = []
    if "BRAIN" in content and "alias_brain.json" not in content:
        issues.append("BRAIN variable undefined")
    if content.count("async def groq_llm") > 1:
        issues.append("Duplicate groq_llm function")
    if "SyntaxError" in content:
        issues.append("SyntaxError string in code")
    # Try to find actual syntax error
    try:
        import ast
        ast.parse(content)
        print("Syntax: VALID")
    except SyntaxError as e:
        issues.append(f"SYNTAX ERROR line {e.lineno}: {e.msg}")
        # Show the problematic area
        if e.lineno:
            start=max(0,e.lineno-3)
            end=min(len(lines),e.lineno+3)
            print("Problem area:")
            for i,l in enumerate(lines[start:end],start+1):
                print(f"  {i}: {l}")
    print("Issues found:", issues if issues else "none detected")
else:
    print("Voice script MISSING")

save("Diagnosis run - checking all systems")
print("\nDIAGNOSIS COMPLETE")
