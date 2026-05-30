
import subprocess, os, json, datetime, base64, urllib.request, time, re

def run(cmd, shell=False, timeout=60):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"
VNT = "/mnt/vnt-data/FileServer/VNT_World_AI_Division"
MP = VNT+"/MemPalace.md"

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
log("SPECTER NETWORK SCAN + DIRECTORY + MEMPALACE RULE")
log("="*55)

# ===== 1. SPECTER NETWORK SCAN =====
log("\n[1] Specter scanning all network devices...")
# Known authorized devices
AUTHORIZED={
    "192.168.10.96":"MSI AI Server (core)",
    "192.168.10.94":"M4 MacBook (media)",
    "192.168.10.114":"Asusi7 Windows",
    "192.168.10.19":"Proxmox1",
    "192.168.10.18":"Proxmox2",
    "192.168.10.10":"Nextcloud CT104",
    "192.168.10.5":"Omada Controller",
    "192.168.10.20":"LiveKit CT109",
    "192.168.10.21":"TURN CT110",
    "192.168.10.1":"Gateway/Router",
}
# Ping sweep the subnet to populate arp
log("  Ping-sweeping 192.168.10.0/24...")
run("for i in $(seq 1 254); do ping -c 1 -W 1 192.168.10.$i >/dev/null 2>&1 & done; wait",shell=True,timeout=60)
time.sleep(2)
# Read arp/neighbor table
arp,_=run("ip neigh show 2>/dev/null | grep 192.168.10 | grep -v FAILED",shell=True)
log(f"  Devices found in ARP:")
devices=[]
for line in arp.split(chr(10)):
    if line.strip():
        parts=line.split()
        ip=parts[0] if parts else ""
        mac=""
        for i,p in enumerate(parts):
            if p=="lladdr" and i+1<len(parts):mac=parts[i+1]
        if ip:devices.append((ip,mac))

# Also try nmap if available for better detail
nmap_check,_=run("which nmap",shell=True)
if nmap_check:
    log("  nmap available - detailed scan...")
    nmap_out,_=run("nmap -sn 192.168.10.0/24 2>/dev/null | grep -oE '192.168.10.[0-9]+'",shell=True,timeout=60)
    for ip in nmap_out.split(chr(10)):
        ip=ip.strip()
        if ip and ip not in [d[0] for d in devices]:
            devices.append((ip,"unknown"))

# Build authorized/rogue report
auth_list=[];rogue_list=[]
for ip,mac in sorted(set(devices),key=lambda x:[int(o) for o in x[0].split('.')]):
    if ip in AUTHORIZED:
        auth_list.append(f"  AUTHORIZED  {ip:16} {mac:18} {AUTHORIZED[ip]}")
    else:
        rogue_list.append(f"  REVIEW      {ip:16} {mac:18} (unknown device)")

log(f"  Total live devices: {len(devices)}")
log(f"  Authorized: {len(auth_list)} | Unknown/Review: {len(rogue_list)}")

# Save device list
scan_report=chr(10).join([
    "VNT NETWORK DEVICE SCAN - "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "By: Specter (Cybersecurity)",
    "="*60,"",
    "AUTHORIZED DEVICES:"]+auth_list+["",
    "UNKNOWN / NEEDS REVIEW:"]+(rogue_list if rogue_list else ["  None - all devices authorized"])+["",
    "="*60,
    "Note: 'Review' = device responded but not in VNT authorized list.",
    "Could be phones, IoT, guests. Specter flags for Ryan to confirm.",
])
try:
    open(VNT+"/network_device_list.txt","w").write(scan_report)
    log("  Saved: network_device_list.txt")
except:pass
# Show the report
log("\n"+scan_report[:600])

# Save to Specter's knowledge + MemPalace
try:
    open(MP,"a").write(chr(10)+"### Specter Network Scan ["+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+"]"+chr(10)+scan_report[:500]+chr(10))
except:pass

# ===== 2. DIRECTORY ORGANIZATION =====
log("\n[2] Organizing directory structure...")
# Create organized structure with Personal/Medical section
dirs=[
    VNT+"/00_PERSONAL",
    VNT+"/00_PERSONAL/Medical",
    VNT+"/00_PERSONAL/Medical/XRays",
    VNT+"/00_PERSONAL/Medical/Ultrasound",
    VNT+"/00_PERSONAL/Medical/Lab_Reports",
    VNT+"/00_PERSONAL/Medical/Diet_Nutrition",
    VNT+"/00_PERSONAL/Medical/Prescriptions",
    VNT+"/00_PERSONAL/Medical/Doctor_Notes",
    VNT+"/00_PERSONAL/Documents",
    VNT+"/00_PERSONAL/Finance",
    VNT+"/01_VNT_OPERATIONS",
    VNT+"/01_VNT_OPERATIONS/Agents",
    VNT+"/01_VNT_OPERATIONS/Memory",
    VNT+"/01_VNT_OPERATIONS/Backups",
    VNT+"/02_CLIENTS",
    VNT+"/02_CLIENTS/CulturalAssets",
    VNT+"/02_CLIENTS/Signsa",
    VNT+"/02_CLIENTS/Knowliom",
    VNT+"/03_MEDIA",
    VNT+"/03_MEDIA/Images",
    VNT+"/03_MEDIA/Videos",
    VNT+"/03_MEDIA/3D",
    VNT+"/04_SYSTEM",
    VNT+"/04_SYSTEM/disaster_recovery",
    VNT+"/04_SYSTEM/snapshots",
]
created=0
for d in dirs:
    if not os.path.exists(d):
        os.makedirs(d,exist_ok=True);created+=1
log(f"  Created {created} organized folders")

# Write the directory rule / organization guide
dir_rule=chr(10).join([
    "VNT FILE SERVER ORGANIZATION RULE",
    "="*50,
    "Last updated: "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"",
    "DIRECTORY STRUCTURE:",
    "",
    "00_PERSONAL/          <- Ryan's private files (restricted access)",
    "   Medical/           <- Health docs. Chain: Alias -> Dr.Ethan -> Dina(Nurse)",
    "      XRays/           <- X-ray images",
    "      Ultrasound/      <- Ultrasound scans",
    "      Lab_Reports/     <- Blood tests, lab results",
    "      Diet_Nutrition/  <- Diet plans, nutrition logs",
    "      Prescriptions/   <- Medication prescriptions",
    "      Doctor_Notes/    <- Consultation notes",
    "   Documents/         <- Personal documents",
    "   Finance/           <- Personal finance (Maya manages)",
    "",
    "01_VNT_OPERATIONS/    <- VNT division working files",
    "   Agents/ Memory/ Backups/",
    "",
    "02_CLIENTS/           <- Client work (CulturalAssets, Signsa, Knowliom)",
    "03_MEDIA/             <- Generated media (Images, Videos, 3D)",
    "04_SYSTEM/            <- Backups, snapshots, system files",
    "",
    "ACCESS CHAIN FOR MEDICAL:",
    "  Ryan uploads medical doc -> Alias receives & files it",
    "  -> routes to Dr.Ethan (:7781) for review/organization",
    "  -> Dr.Ethan delegates to Dina/Nurse (:7786) for record-keeping",
    "  Nothing medical is acted on without Ryan; agents organize & summarize only.",
    "",
    "RULE: Every agent files documents in the correct folder above.",
    "Personal/Medical is treated as confidential.",
    "="*50])
try:
    open(VNT+"/00_DIRECTORY_RULE.md","w").write(dir_rule)
    log("  Directory rule saved: 00_DIRECTORY_RULE.md")
except:pass

# ===== 3. MEMPALACE-FIRST RULE =====
log("\n[3] Establishing MemPalace-first rule...")
mp_rule=chr(10).join(["",
    "="*60,
    "MEMPALACE-FIRST RULE (ALL AGENTS MUST FOLLOW)",
    "="*60,
    "Updated: "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"",
    "1. BEFORE answering ANY question, every agent checks MemPalace first.",
    "   Path: /mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md",
    "   Alias already does this via RAG (alias_brain_module.rag_retrieve).",
    "",
    "2. AFTER completing ANY task, write the result to MemPalace.",
    "   Format: ### AgentName [timestamp] + what happened.",
    "",
    "3. MemPalace is the single source of truth. If solution exists there,",
    "   use it. If not, solve, then SAVE it so next time it's known.",
    "",
    "4. RCA guide + Control guide + Directory rule all live in MemPalace.",
    "   Agents consult these for troubleshooting before escalating.",
    "",
    "5. Argus ensures MemPalace is being written to (monitors freshness).",
    "="*60])
try:
    open(MP,"a").write(mp_rule+chr(10))
    log("  MemPalace-first rule saved")
except:pass

# Check MemPalace freshness/size
mp_size,_=run(f"ls -lh {MP} 2>/dev/null | awk '{{print $5}}'",shell=True)
mp_lines,_=run(f"wc -l {MP} 2>/dev/null | awk '{{print $1}}'",shell=True)
log(f"  MemPalace: {mp_size}, {mp_lines} lines")

# ===== 4. Final backup with new structure =====
log("\n[4] Taking fresh backup...")
bk,_=run("python3 /home/k/vnt-backup.py 2>&1",shell=True,timeout=60)
log(f"  {bk[:70]}")

# ===== 5. Final verify =====
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
push_result("specter_dir_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
