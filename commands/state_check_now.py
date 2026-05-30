
import subprocess,os,json,datetime
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG="/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
BRAIN="/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json"

def run(c,shell=False,t=10):
    r=subprocess.run(c,shell=shell,capture_output=True,text=True,timeout=t)
    return r.stdout.strip()

ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
print("="*50)
print("CURRENT STATE CHECK - "+ts)
print("="*50)

# Services
ALL=["alias-voice-agent","zeus-agent","zeus-monitor","maya-agent","ava-agent",
     "julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent","specter-agent",
     "vnt-webserver","luc-agent","ben-agent","dina-agent","jodi-agent","rick-agent",
     "alias-email-reader","vnt-simulation","github-relay","smbd"]
ok=0;down=[]
for s in ALL:
    st=run(["systemctl","is-active",s])
    if st=="active":ok+=1
    else:down.append(s)
wa=run(["systemctl","--user","is-active","alias-whatsapp"])
va=run(["systemctl","is-active","alias-voice-agent"])

print(f"Services: {ok}/{len(ALL)} active")
print(f"Voice: {va} | WA: {wa}")
print(f"Down: {down}")

# Check brain version
try:
    b=json.load(open(BRAIN))
    print("Brain version: "+b.get("version","?"))
    print("Active model: "+b.get("active_model","?")+" / "+b.get("active_model_source","?"))
    print("M4 in brain: "+str("M4" in str(b.get("infrastructure",{}))))
    print("M2 retired: "+str("RETIRED" in str(b.get("infrastructure",{}))))
except Exception as e:
    print("Brain error: "+str(e)[:50])

# Check voice syntax
import ast
if os.path.exists("/home/k/alias-voice-agent.py"):
    try:ast.parse(open("/home/k/alias-voice-agent.py").read());print("Voice syntax: VALID")
    except SyntaxError as e:print("Voice syntax: BROKEN line "+str(e.lineno))

# Check crewai
r=subprocess.run(["python3","-c","import crewai;print(crewai.__version__)"],capture_output=True,text=True,timeout=10)
print("CrewAI: "+(r.stdout.strip() if r.returncode==0 else "not installed - "+r.stderr[:40]))

# Asusi7 SSH
ssh=run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 Alias@192.168.10.114 echo OK 2>&1",shell=True,timeout=10)
print("Asusi7 SSH: "+("OK" if "OK" in ssh else "FAIL: "+ssh[:40]))

# Save to mempalace
def save(e):
    try:open(MP,"a").write("\n### State ["+ts+"]\n"+str(e)+"\n")
    except:pass
save(f"State check: {ok}/{len(ALL)} active. Voice:{va}. WA:{wa}. Down:{down}")
print("STATE CHECK DONE")
