
import subprocess, time, datetime, json, os, re

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
KNOWN_FILE = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/known_devices.json"
GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]

TRUSTED = {
    "192.168.10.96":"MSI AI Server (BRAIN)",
    "192.168.10.114":"Asusi7 Windows (Alias)",
    "192.168.10.98":"Acer (Ryan SSH machine)",
    "192.168.10.94":"M4 MacBook Pro (Media)",
    "192.168.10.19":"Proxmox1",
    "192.168.10.18":"Proxmox2",
    "192.168.10.10":"Nextcloud",
    "192.168.10.13":"Website CT108",
    "192.168.10.20":"LiveKit CT109",
    "192.168.10.21":"TURN CT110",
    "192.168.10.191":"Redmi Note 15 Pro+ (AI Phone)",
    "192.168.10.5":"Omada Network Controller",
    "192.168.10.1":"Main Router/Gateway",
    "192.168.10.14":"M2 MacBook (retired media)",
}

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### Zeus Security ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

def load_known():
    try: return json.load(open(KNOWN_FILE))
    except: return {}

def save_known(d):
    try: json.dump(d,open(KNOWN_FILE,"w"),indent=2)
    except: pass

def scan_arp():
    r=subprocess.run(["arp","-a"],capture_output=True,text=True)
    devs={}
    for line in r.stdout.split(chr(10)):
        m=re.search(r"\(([0-9.]+)\).*?([0-9a-f:]{17})",line,re.I)
        if m:
            ip=m.group(1); mac=m.group(2).lower()
            devs[ip]={"ip":ip,"mac":mac,
                "trusted":ip in TRUSTED,
                "name":TRUSTED.get(ip,"UNKNOWN DEVICE"),
                "last_seen":datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    return devs

def check_redmi():
    results={}
    # WiFi ADB
    r=subprocess.run(["adb","connect","192.168.10.191:5555"],capture_output=True,text=True,timeout=8)
    results["wifi_adb"]=r.stdout.strip()
    # Check all ADB devices
    r2=subprocess.run(["adb","devices"],capture_output=True,text=True)
    results["adb_devices"]=r2.stdout.strip()
    # Ping
    r3=subprocess.run(["ping","-c","1","-W","2","192.168.10.191"],capture_output=True,text=True)
    results["ping"]="online" if r3.returncode==0 else "offline"
    return results

# Run full scan
print("=== Zeus Security Scan ===")
ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
current=scan_arp()
known=load_known()

new_devices=[]
unknown_devices=[]
reconnected=[]

for ip,info in current.items():
    if ip not in known:
        new_devices.append(ip)
        known[ip]=info
        known[ip]["first_seen"]=ts
        if not info["trusted"]:
            unknown_devices.append(ip)
            print(f"ALERT: Unknown device: {ip} MAC:{info['mac']}")
        else:
            print(f"New trusted device: {ip} - {info['name']}")
    else:
        # Check if was offline
        if known[ip].get("status")=="offline":
            reconnected.append(ip)
        known[ip]["last_seen"]=ts
        known[ip]["status"]="online"
        known[ip]["trusted"]=ip in TRUSTED
        known[ip]["name"]=TRUSTED.get(ip,known[ip].get("name","UNKNOWN"))

# Mark previously seen devices that are now offline
for ip in list(known.keys()):
    if ip not in current:
        if known[ip].get("status")!="offline":
            print(f"Device went offline: {ip} - {known[ip].get('name','?')}")
        known[ip]["status"]="offline"

save_known(known)

# Redmi status
redmi=check_redmi()
print("Redmi status:",redmi)

# Report
trusted_count=sum(1 for ip in current if ip in TRUSTED)
unknown_count=len(unknown_devices)
total=len(current)

report=f"""SECURITY SCAN COMPLETE [{ts}]
Total devices on network: {total}
Trusted: {trusted_count}
Unknown: {unknown_count}
New devices: {len(new_devices)}
Redmi: {redmi.get('ping','?')} | WiFi ADB: {redmi.get('wifi_adb','?')[:50]}
"""

if unknown_devices:
    report+="ALERTS - Unknown devices:"+chr(10)
    for ip in unknown_devices:
        report+=f"  {ip} MAC:{current[ip]['mac']}"+chr(10)

print(report)
save(report)

# Update Zeus monitor with security
zeus=open("/home/k/zeus-monitor.py").read()
if "TRUSTED_IPS" not in zeus:
    sec_code="""
import re as _re
TRUSTED_IPS=["192.168.10.96","192.168.10.114","192.168.10.98","192.168.10.94",
    "192.168.10.19","192.168.10.18","192.168.10.10","192.168.10.13","192.168.10.20",
    "192.168.10.21","192.168.10.191","192.168.10.5","192.168.10.1","192.168.10.14"]
KNOWN_DEVS="/mnt/vnt-data/FileServer/VNT_World_AI_Division/known_devices.json"

def security_scan():
    r=subprocess.run(["arp","-a"],capture_output=True,text=True)
    try: known=json.load(open(KNOWN_DEVS))
    except: known={}
    alerts=[]
    for line in r.stdout.split("\n"):
        m=_re.search(r"\(([0-9.]+)\).*?([0-9a-f:]{17})",line,_re.I)
        if m:
            ip=m.group(1)
            if ip not in known:
                status="TRUSTED" if ip in TRUSTED_IPS else "UNKNOWN"
                known[ip]={"mac":m.group(2),"status":status,"first_seen":str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))}
                if status=="UNKNOWN":
                    alerts.append(f"NEW UNKNOWN DEVICE: {ip}")
                    log(f"SECURITY ALERT: Unknown device {ip} on network")
                    save_to_mempalace(f"SECURITY ALERT: Unknown device {ip} joined network")
    try: json.dump(known,open(KNOWN_DEVS,"w"),indent=2)
    except: pass
    # Keep Redmi connected via WiFi ADB
    subprocess.run(["adb","connect","192.168.10.191:5555"],capture_output=True,timeout=5)
    return alerts

def check_redmi_status():
    r=subprocess.run(["ping","-c","1","-W","2","192.168.10.191"],capture_output=True)
    online=r.returncode==0
    if online:
        subprocess.run(["adb","connect","192.168.10.191:5555"],capture_output=True,timeout=5)
    return online
"""
    zeus="import json"+chr(10)+sec_code+chr(10)+zeus
    # Add to daily report
    zeus=zeus.replace(
        "    lk = check_livekit()",
        """    lk = check_livekit()
    try:
        sec_alerts=security_scan()
        for a in sec_alerts: lines.append("⚠️ "+a)
        redmi_ok=check_redmi_status()
        lines.append(("✅" if redmi_ok else "🔴")+" Redmi :191 WiFi")
    except Exception as se: lines.append("Security check error: "+str(se))"""
    )
    open("/home/k/zeus-monitor.py","w").write(zeus)
    subprocess.run(["sudo","systemctl","restart","zeus-monitor"],capture_output=True)
    print("Zeus security + Redmi monitoring active")
else:
    print("Zeus security already configured")

print("Zeus security upgrade complete")
print("Known devices saved to:",KNOWN_FILE)
