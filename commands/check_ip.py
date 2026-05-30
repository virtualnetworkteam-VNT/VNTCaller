
import subprocess, os, json, datetime, urllib.request

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

def run(cmd, shell=False, timeout=15):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### IP Check ["+ts+"]\n"+e+"\n")
    except: pass

print("="*55)
print("INVESTIGATING PUBLIC IP SITUATION")
print("="*55)

# Check current actual public IP of MSI
print("\n[1] What is MSI current public IP?")
ips = []
for svc in ["ifconfig.me","api.ipify.org","icanhazip.com","checkip.amazonaws.com"]:
    o,_ = run(f"curl -s --connect-timeout 5 {svc}",shell=True,timeout=8)
    if o and len(o)<20:
        ips.append(svc+": "+o.strip())
        print("  "+svc+": "+o.strip())

# Check MemPalace for how 94.49.29.97 was set
print("\n[2] Searching MemPalace for 94.49.29.97 origin...")
mp_content = open(MP).read() if os.path.exists(MP) else ""
lines_with_ip = [l for l in mp_content.split("\n") if "94.49.29.97" in l]
print("  Found in MemPalace:", len(lines_with_ip), "references")
for l in lines_with_ip[:5]:
    print("  - "+l.strip()[:80])

# Check config
print("\n[3] Config entries...")
try:
    cfg = json.load(open(CFG))
    print("  public_ip in config:", cfg.get("public_ip","not set"))
    print("  ngrok_url:", cfg.get("ngrok_tunnel","not set"))
    print("  public_portal:", cfg.get("public_portal_url","not set"))
except: pass

# Check if 94.49.29.97 responds to anything
print("\n[4] Testing 94.49.29.97...")
for port in [22, 80, 443, 2222, 8080, 8888]:
    o,_ = run(f"timeout 3 bash -c 'echo > /dev/tcp/94.49.29.97/{port}' 2>&1 && echo OPEN || echo closed",shell=True,timeout=5)
    if "OPEN" in o:
        print(f"  Port {port}: OPEN")

# Check Proxmox - 94.49.29.97 might be a VPS or Proxmox external IP
print("\n[5] Checking if this is Proxmox external IP...")
prox_check,_ = run("curl -s --connect-timeout 5 https://94.49.29.97:8006/ -k -o /dev/null -w '%{http_code}'",shell=True,timeout=8)
print("  Proxmox :8006:", prox_check)

# Check SSH on port 2222 (was configured before)
ssh_check,_ = run("timeout 5 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=4 -p 2222 k@94.49.29.97 'echo SSH_OK && hostname && ip route get 8.8.8.8 | grep src' 2>&1",shell=True,timeout=10)
print("  SSH :2222 to 94.49.29.97:", ssh_check[:100])

# Check coturn (was installed in CT110)
coturn_check,_ = run("curl -s --connect-timeout 5 http://94.49.29.97:3478/ 2>&1 | head -c 50",shell=True,timeout=5)
print("  TURN :3478:", coturn_check[:50] if coturn_check else "no response")

# Get actual current public IP
print("\n[6] CONCLUSION:")
current_ip = ips[0].split(": ")[1] if ips else "unknown"
print("  MSI current public IP:", current_ip)
print("  94.49.29.97: could be old/different IP or Proxmox node")

save("IP investigation: current="+current_ip+" | 94.49.29.97 tested")
print("DONE")
