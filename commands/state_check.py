
import subprocess, os, json, datetime, ast

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
SNAP= "/mnt/vnt-data/FileServer/VNT_World_AI_Division/snapshots"

def run(cmd,shell=False,timeout=15):
    r=subprocess.run(cmd,shell=shell,capture_output=True,text=True,timeout=timeout)
    return r.stdout.strip(),r.stderr.strip()

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\n### State Check ["+ts+"]\n"+e+"\n")

print("="*55)
print("STATE CHECK - BEFORE TOUCHING ANYTHING")
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*55)

# 1. Every service - exact status
ALL=[
    "alias-voice-agent","zeus-agent","zeus-monitor","maya-agent","ava-agent",
    "julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent",
    "specter-agent","vnt-webserver","luc-agent","ben-agent","dina-agent",
    "jodi-agent","rick-agent","alias-email-reader","vnt-simulation",
    "github-relay","smbd","alias-si","alias-desktop-agent","alias-upgrade-engine"
]
ok=0; down=[]; activating=[]
for s in ALL:
    st,_=run(["systemctl","is-active",s])
    if st=="active": ok+=1; print(f"  OK  {s}")
    elif st=="activating": activating.append(s); print(f"  >> {s}: activating")
    else:
        down.append(s)
        # Get the actual error
        log,_=run(["journalctl","-u",s,"-n","3","--no-pager","--quiet"])
        err_line=next((l for l in log.split("\n") if any(x in l.lower() for x in ["error","failed","except","killed","exit"])),log[-80:] if log else "no logs")
        print(f"  XX  {s}: {st} | {err_line[:70]}")

wa,_=run(["systemctl","--user","is-active","alias-whatsapp"])
print(f"  {'OK' if wa=='active' else 'XX'}  alias-whatsapp: {wa}")

print(f"\nSUMMARY: {ok}/{len(ALL)} active | activating: {activating} | down: {down}")

# 2. Check voice agent syntax specifically
print("\n=== VOICE AGENT CHECK ===")
va="/home/k/alias-voice-agent.py"
if os.path.exists(va):
    content=open(va).read()
    try:
        ast.parse(content)
        print("Syntax: VALID")
        print("Size:",len(content),"bytes")
        # Check if it's listening
        port,_=run("ss -tlnp | grep 8443",shell=True)
        print("Port 8443:",port if port else "NOT LISTENING")
    except SyntaxError as e:
        print(f"SYNTAX ERROR line {e.lineno}: {e.msg}")
        start=max(0,e.lineno-2)
        lines=content.split("\n")
        for i,l in enumerate(lines[start:e.lineno+1],start+1):
            print(f"  {i}: {l}")
else:
    print("MISSING")

# 3. Check relay
print("\n=== RELAY CHECK ===")
relay="/home/k/github-relay.py"
if os.path.exists(relay):
    content=open(relay).read()
    try:
        ast.parse(content)
        print("Relay syntax: VALID")
    except SyntaxError as e:
        print(f"Relay BROKEN line {e.lineno}: {e.msg}")
        lines=content.split("\n")
        start=max(0,e.lineno-2)
        for i,l in enumerate(lines[start:e.lineno+1],start+1):
            print(f"  {i}: {l}")

# 4. Check snapshots available
print("\n=== SNAPSHOTS ===")
if os.path.exists(SNAP):
    snaps=sorted(os.listdir(SNAP),reverse=True)
    print("Available:",snaps[:5])
    # Check which has valid voice agent
    for snap in snaps[:3]:
        va_snap=SNAP+"/"+snap+"/alias-voice-agent.py"
        if os.path.exists(va_snap):
            try:
                ast.parse(open(va_snap).read())
                print(f"  VALID voice backup: {snap}")
            except:
                print(f"  BROKEN voice backup: {snap}")
else:
    print("No snapshots directory")

# 5. Check what LLMs available
print("\n=== LLM OPTIONS ===")
# Check Ollama
ollama,_=run("ollama list 2>/dev/null",shell=True)
print("Ollama models:",ollama[:200] if ollama else "ollama not running or no models")

# Check if any API keys configured
try:
    cfg=json.load(open(CFG))
    print("Groq key:",bool(cfg.get("groq_key")))
    print("OpenAI key:",bool(cfg.get("openai_key")))
    print("Anthropic key:",bool(cfg.get("anthropic_key")))
    print("Active model:",cfg.get("active_llm_model","not set"))
except: print("Config read error")

# 6. Check Asusi7 SSH
print("\n=== ASUSI7 SSH ===")
ssh_test,ssh_err=run(
    "sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 Alias@192.168.10.114 echo SSH_OK",
    shell=True,timeout=10)
print("SSH test:",ssh_test if ssh_test else "FAILED: "+ssh_err[:60])

# 7. Read last 20 lines of MemPalace
print("\n=== MEMPALACE TAIL ===")
try:
    mp=open(MP).read()
    print(mp[-800:])
except: print("MemPalace unreadable")

save(f"State check: {ok}/{len(ALL)} active. Down: {down}. Voice: {'valid' if os.path.exists(va) else 'missing'}. SSH: {ssh_test[:20] if ssh_test else 'failed'}")
print("\nSTATE CHECK COMPLETE")
