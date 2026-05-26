
import subprocess, time, datetime, json, os

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GROQ = open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### Zeus Security ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

# Known trusted devices
TRUSTED = {
    "192.168.10.96": "MSI AI Server (BRAIN)",
    "192.168.10.114": "Asusi7 Windows (Alias)",
    "192.168.10.98": "Acer Windows (Ryan SSH)",
    "192.168.10.94": "M4 MacBook Pro (Media)",
    "192.168.10.19": "Proxmox1",
    "192.168.10.18": "Proxmox2",
    "192.168.10.10": "Nextcloud",
    "192.168.10.13": "Website CT108",
    "192.168.10.20": "LiveKit CT109",
    "192.168.10.21": "TURN CT110",
    "192.168.10.191": "Redmi Note 15 Pro+ (AI Phone)",
    "192.168.10.5": "Omada Controller",
    "192.168.10.1": "Router/Gateway",
}

KNOWN_FILE = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/known_devices.json"

def load_known():
    try: return json.load(open(KNOWN_FILE))
    except: return {}

def save_known(d):
    try: json.dump(d,open(KNOWN_FILE,"w"),indent=2)
    except: pass

def scan_network():
    r=subprocess.run(["arp","-a"],capture_output=True,text=True)
    devices={}
    for line in r.stdout.split(chr(10)):
        import re
        m=re.search(r"\(([0-9.]+)\).*?([0-9a-f:]{17})",line,re.I)
        if m:
            ip=m.group(1); mac=m.group(2).lower()
            devices[ip]={"mac":mac,"trusted":ip in TRUSTED,"name":TRUSTED.get(ip,"UNKNOWN")}
    return devices

def check_adb_devices():
    r=subprocess.run(["adb","devices"],capture_output=True,text=True)
    devices=[]
    for line in r.stdout.split(chr(10))[1:]:
        if "device" in line and not "List" in line:
            did=line.split()[0]
            devices.append(did)
    return devices

# Scan now
print("=== Zeus Security Scan ===")
current=scan_network()
known=load_known()
alerts=[]

for ip,info in current.items():
    if ip not in known:
        msg=f"NEW DEVICE: {ip} MAC:{info['mac']} Name:{info['name']}"
        alerts.append(msg)
        print("NEW:",msg)
        known[ip]=info
        known[ip]["first_seen"]=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    elif not info["trusted"] and known[ip].get("name","UNKNOWN")=="UNKNOWN":
        msg=f"UNTRUSTED: {ip} MAC:{info['mac']}"
        alerts.append(msg)

# Check ADB devices
adb_devs=check_adb_devices()
print("ADB connected devices:",adb_devs)

# Check Redmi specifically
redmi_wifi=subprocess.run(["adb","connect","192.168.10.191:5555"],capture_output=True,text=True)
print("Redmi WiFi ADB:",redmi_wifi.stdout.strip())

save_known(known)

# Update Zeus monitor to include security checks
zeus_mon=open("/home/k/zeus-monitor.py").read()
if "scan_network" not in zeus_mon:
    security_fn="""
def security_check():
    import re
    r=subprocess.run(["arp","-a"],capture_output=True,text=True)
    TRUSTED_IPS=["192.168.10.96","192.168.10.114","192.168.10.98","192.168.10.94",
        "192.168.10.19","192.168.10.18","192.168.10.10","192.168.10.13","192.168.10.20",
        "192.168.10.21","192.168.10.191","192.168.10.5","192.168.10.1"]
    KNOWN_FILE="/mnt/vnt-data/FileServer/VNT_World_AI_Division/known_devices.json"
    try: known=json.load(open(KNOWN_FILE))
    except: known={}
    new_devices=[]
    for line in r.stdout.split("\n"):
        m=re.search(r"\(([0-9.]+)\).*?([0-9a-f:]{17})",line,re.I)
        if m:
            ip=m.group(1)
            if ip not in known:
                trusted="TRUSTED" if ip in TRUSTED_IPS else "UNKNOWN"
                new_devices.append(f"{ip} ({trusted})")
                known[ip]={"mac":m.group(2),"status":trusted,"seen":datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
                if trusted=="UNKNOWN":
                    log(f"SECURITY ALERT: New unknown device {ip}")
                    save_to_mempalace(f"SECURITY: New unknown device on network: {ip}")
    if new_devices:
        try: json.dump(known,open(KNOWN_FILE,"w"),indent=2)
        except: pass
    # Keep Redmi ADB alive
    subprocess.run(["adb","connect","192.168.10.191:5555"],capture_output=True,timeout=5)
    return new_devices
"""
    zeus_mon=zeus_mon.replace("def fix_livekit():",security_fn+chr(10)+"def fix_livekit():")
    # Add to main loop
    zeus_mon=zeus_mon.replace(
        "        # Check disk health",
        """        # Security scan every 5 minutes
        if not hasattr(run_report, '_sec_last') or time.time()-getattr(run_report,'_sec_last',0)>300:
            new=security_check()
            run_report._sec_last=time.time()

        # Check disk health"""
    )
    # Need json import
    if "import json" not in zeus_mon:
        zeus_mon="import json"+chr(10)+zeus_mon
    open("/home/k/zeus-monitor.py","w").write(zeus_mon)
    subprocess.run(["sudo","systemctl","restart","zeus-monitor"],capture_output=True)
    print("Zeus security monitoring added")

summary = f"Security scan: {len(current)} devices on network. {len(alerts)} alerts. ADB: {adb_devs}"
save(summary)
print(summary)
print("Known devices:", len(known))
for ip,info in list(current.items())[:5]:
    print(f"  {ip}: {info['name']} ({'TRUSTED' if info['trusted'] else 'CHECK'})")
