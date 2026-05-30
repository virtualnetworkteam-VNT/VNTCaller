
import subprocess,os,json,datetime,ast
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
def run(c,shell=False,t=10):
    r=subprocess.run(c,shell=shell,capture_output=True,text=True,timeout=t)
    return r.stdout.strip()
def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try:open(MP,"a").write("\n### Check ["+ts+"]\n"+e+"\n")
    except:pass

ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
print("MSI STATE CHECK - "+ts)
print("="*50)

# Services
ALL=["alias-voice-agent","zeus-agent","zeus-monitor","maya-agent","ava-agent",
     "julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent","specter-agent",
     "mia-agent","luc-agent","ben-agent","dina-agent","jodi-agent","rick-agent",
     "alias-email-reader","github-relay","smbd"]
ok=0;down=[]
for s in ALL:
    st=run(["systemctl","is-active",s])
    if st=="active":ok+=1
    else:down.append(s)
wa=run(["systemctl","--user","is-active","alias-whatsapp"])
va_st=run(["systemctl","is-active","alias-voice-agent"])

# Voice syntax
va_syn="OK"
if os.path.exists("/home/k/alias-voice-agent.py"):
    try:ast.parse(open("/home/k/alias-voice-agent.py").read())
    except SyntaxError as e:va_syn="BROKEN:L"+str(e.lineno)
else:va_syn="MISSING"

# LangGraph installed?
lg=run(["python3","-c","import langgraph;print(langgraph.__version__)"])

# Asusi7 SSH
ssh=run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 Alias@192.168.10.114 echo SSH_OK 2>&1",shell=True,t=10)

# Disk space
disk=run("df -h /home/k | tail -1 | awk '{print $4}'",shell=True)

print(f"Services: {ok}/{len(ALL)} | Voice: {va_st} | WA: {wa}")
print(f"Voice syntax: {va_syn}")
print(f"LangGraph: {lg if lg else 'NOT installed'}")
print(f"Asusi7 SSH: {'OK' if 'SSH_OK' in ssh else 'FAIL'}")
print(f"Disk free: {disk}")
print(f"DOWN: {down}")

save(f"State: {ok}/{len(ALL)} voice:{va_st} wa:{wa} lg:{bool(lg)} ssh:{'OK' if 'SSH_OK' in ssh else 'FAIL'}")
print("CHECK DONE")
