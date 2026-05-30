
import subprocess, os, json, datetime, base64, urllib.request, time

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"

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
log("1TB DRIVE INVESTIGATION + BACKUP SIZING")
log("="*55)

# 1. All disks and mounts
log("\n[1] All disks:")
disks,_=run("df -h | grep -vE 'tmpfs|loop|udev'",shell=True)
log(disks)

# 2. What's the 1TB? Find it
log("\n[2] Block devices:")
lsblk,_=run("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT 2>/dev/null | grep -vE 'loop'",shell=True)
log(lsblk)

# 3. /mnt mounts
log("\n[3] /mnt mounts:")
mnt,_=run("ls -la /mnt/ 2>/dev/null && echo '---' && mount | grep /mnt",shell=True)
log(mnt[:400])

# 4. vnt-data usage (the FileServer)
log("\n[4] /mnt/vnt-data usage:")
vnt_du,_=run("du -sh /mnt/vnt-data 2>/dev/null && echo '---contents---' && du -sh /mnt/vnt-data/* 2>/dev/null | sort -rh | head -15",shell=True,timeout=30)
log(vnt_du[:500])

# 5. The VNT AI Division folder specifically
log("\n[5] VNT_World_AI_Division contents:")
vnt_ai,_=run("ls -la /mnt/vnt-data/FileServer/VNT_World_AI_Division/ 2>/dev/null | head -25",shell=True)
log(vnt_ai[:600])

# 6. How big would a backup be? Size the critical files
log("\n[6] Backup sizing (critical VNT files):")
# Agent scripts + configs + memory
agent_size,_=run("du -ch /home/k/*-agent.py /home/k/alias-voice-agent.py /home/k/alias_brain_module.py /home/k/zeus-monitor.py /home/k/github-relay.py /home/k/vnt-portal.py /home/k/vnt-webserver.py 2>/dev/null | tail -1",shell=True)
log(f"  Agent scripts: {agent_size}")
mem_size,_=run("du -ch /mnt/vnt-data/FileServer/VNT_World_AI_Division/*.md /mnt/vnt-data/FileServer/VNT_World_AI_Division/*.json 2>/dev/null | tail -1",shell=True)
log(f"  Memory+configs: {mem_size}")
wa_size,_=run("du -sh /home/k/alias-baileys/index.js 2>/dev/null",shell=True)
log(f"  WhatsApp bot: {wa_size}")
svc_size,_=run("du -ch /home/k/.config/systemd/user/*.service 2>/dev/null | tail -1",shell=True)
log(f"  Service units: {svc_size}")

# 7. Is there free space for backups + models?
log("\n[7] Free space on vnt-data:")
free,_=run("df -h /mnt/vnt-data 2>/dev/null | tail -1",shell=True)
log(f"  {free}")

# 8. Check for existing backups/snapshots
log("\n[8] Existing snapshots:")
snaps,_=run("ls -la /mnt/vnt-data/FileServer/VNT_World_AI_Division/snapshots/ 2>/dev/null | head -10",shell=True)
log(snaps[:300] if snaps else "  No snapshots folder")

# 9. Ollama models size (potential growth use)
log("\n[9] Ollama models (Alias growth storage):")
ollama,_=run("du -sh ~/.ollama 2>/dev/null; ollama list 2>/dev/null | head -5",shell=True)
log(ollama[:200])

full="\n".join(out)
push_result("disk_result.txt",full)
push_result("latest_state.txt",full)
log("\nDONE")
