
import subprocess,os,json,datetime,shutil,ast

MP  ="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG ="/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
SNAP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/snapshots"

def run(cmd,shell=False,timeout=20):
    r=subprocess.run(cmd,shell=shell,capture_output=True,text=True,timeout=timeout)
    return r.stdout.strip(),r.stderr.strip()

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try:open(MP,"a").write("\n### ["+ts+"]\n"+str(e)+"\n")
    except:pass

ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
print("="*50)
print("STEP 1: SNAPSHOT + STATE CHECK")
print(ts)
print("="*50)

snap_dir=SNAP+"/snap_"+ts.replace(" ","_").replace(":",".")
os.makedirs(snap_dir,exist_ok=True)
for f in ["/home/k/alias-voice-agent.py","/home/k/zeus-monitor.py",
          "/home/k/alias-baileys/index.js",CFG,
          "/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json"]:
    if os.path.exists(f):
        shutil.copy(f,snap_dir+"/"+os.path.basename(f))
run("cp /etc/systemd/system/*agent*.service "+snap_dir+"/ 2>/dev/null||true",shell=True)
run("cp /etc/systemd/system/zeus*.service "+snap_dir+"/ 2>/dev/null||true",shell=True)
run("cp /etc/systemd/system/vnt*.service "+snap_dir+"/ 2>/dev/null||true",shell=True)
run("cp /etc/systemd/system/alias*.service "+snap_dir+"/ 2>/dev/null||true",shell=True)
save("SNAPSHOT: "+snap_dir+" | files: "+str(len(os.listdir(snap_dir))))
print("Snapshot: "+snap_dir)

ALL=["alias-voice-agent","zeus-agent","zeus-monitor","maya-agent","ava-agent",
     "julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent","specter-agent",
     "vnt-webserver","luc-agent","ben-agent","dina-agent","jodi-agent","rick-agent",
     "alias-email-reader","vnt-simulation","github-relay","smbd"]
ok=0;down=[]
for s in ALL:
    st,_=run(["systemctl","is-active",s])
    if st=="active":ok+=1
    else:down.append(s+"="+st)
wa,_=run(["systemctl","--user","is-active","alias-whatsapp"])
ssh,_=run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 Alias@192.168.10.114 echo OK 2>&1",shell=True,timeout=10)

va_syntax="valid"
if os.path.exists("/home/k/alias-voice-agent.py"):
    try:ast.parse(open("/home/k/alias-voice-agent.py").read())
    except SyntaxError as e:va_syntax="BROKEN line "+str(e.lineno)+": "+e.msg

print("Services: "+str(ok)+"/"+str(len(ALL)))
print("Down: "+str(down))
print("WhatsApp: "+wa)
print("Asusi7 SSH: "+("OK" if "OK" in ssh else "FAIL"))
print("Voice syntax: "+va_syntax)
save("State: "+str(ok)+"/"+str(len(ALL))+" | WA:"+wa+" | SSH:"+ssh[:10]+" | voice:"+va_syntax)
print("STEP 1 DONE")
