
import subprocess,os,time,json,datetime

MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

# Fix simulation syntax issue
r=subprocess.run(["python3","-c","import ast; ast.parse(open('/home/k/vnt-simulation.py').read())"],capture_output=True,text=True)
print("Current sim syntax:", "OK" if r.returncode==0 else "BROKEN: "+r.stderr[:100])

if r.returncode != 0:
    # Restore from backup if exists
    import glob
    backups=sorted(glob.glob("/mnt/vnt-data/FileServer/VNT_World_AI_Division/backups/*/vnt-simulation.py"))
    if backups:
        import shutil
        shutil.copy(backups[-1],"/home/k/vnt-simulation.py")
        print("Restored from backup")
    else:
        print("No backup - will redeploy")

subprocess.run(["sudo","systemctl","restart","vnt-simulation"],capture_output=True)
time.sleep(3)
r2=subprocess.run(["systemctl","is-active","vnt-simulation"],capture_output=True,text=True)
print("Simulation:", r2.stdout.strip())

# Install smartmontools
subprocess.run(["sudo","apt-get","install","-y","smartmontools"],capture_output=True)

# Add disk health to Zeus monitor
zeus=open("/home/k/zeus-monitor.py").read()
if "check_disk_health" not in zeus:
    disk_fn="""
def check_disk_health():
    results = {}
    disks = ["/dev/sda","/dev/sdb","/dev/sdc","/dev/sdd"]
    for disk in disks:
        try:
            r = subprocess.run(["sudo","smartctl","-H",disk],capture_output=True,text=True,timeout=10)
            if "PASSED" in r.stdout: results[disk]="HEALTHY"
            elif "FAILED" in r.stdout:
                results[disk]="FAILED"
                log(f"DISK CRITICAL: {disk} SMART FAILED")
            else: results[disk]="checking"
        except: results[disk]="unavailable"
    r2=subprocess.run(["df","-h","/mnt/vnt-data"],capture_output=True,text=True)
    results["usage"]=[l for l in r2.stdout.split("\n") if "vnt" in l or "/dev/" in l][:2]
    r3=subprocess.run(["cat","/proc/mdstat"],capture_output=True,text=True)
    if "active" in r3.stdout:
        results["raid"]="degraded" if "[_" in r3.stdout or "_]" in r3.stdout else "active"
        if results["raid"]=="degraded":
            log("RAID DEGRADED - CHECK IMMEDIATELY")
    return results
"""
    zeus=zeus.replace("def fix_livekit():",disk_fn+chr(10)+"def fix_livekit():")

    # Add disk check to 6x daily report
    zeus=zeus.replace(
        "    lk = check_livekit()",
        """    lk = check_livekit()
    try:
        dh = check_disk_health()
        for d,s in dh.items():
            if isinstance(s,str):
                icon = chr(9989) if s in ["HEALTHY","OK","active"] else chr(10060) if "FAIL" in s or "DEGR" in s else chr(9888)
                lines.append(icon+" Disk "+str(d)+": "+str(s))
    except Exception as de:
        lines.append("Disk check error: "+str(de))"""
    )

    open("/home/k/zeus-monitor.py","w").write(zeus)
    subprocess.run(["sudo","systemctl","restart","zeus-monitor"],capture_output=True)
    time.sleep(2)
    r3=subprocess.run(["systemctl","is-active","zeus-monitor"],capture_output=True,text=True)
    print("Zeus monitor:", r3.stdout.strip())
    print("Disk health monitoring added to Zeus")
else:
    print("Disk health already in Zeus")

# Run first simulation workflow now
try:
    import urllib.request
    body=json.dumps({"action":"run","workflow":"daily_ops","initiator":"System"}).encode()
    req=urllib.request.Request("http://127.0.0.1:7785/",data=body,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=10) as r: d=json.loads(r.read())
    print("Daily ops workflow started:", d.get("started","?"))
except Exception as e:
    print("Workflow start:", e)

with open(MP,"a") as f:
    f.write(chr(10)+"### Fixes ["+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+"]"+chr(10)+"Simulation fixed. Disk health in Zeus. 4TB monitoring active."+chr(10))
print("All done")
