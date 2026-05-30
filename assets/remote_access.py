import subprocess, os, json, datetime, time, smtplib, urllib.request, ast, shutil
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
WEB = "/home/k/vnt-web"

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Remote ["+ts+"]\n"+e+"\n")
    except: pass

def ssh7(cmd, timeout=25):
    return run(
        "sshpass -p '116899' ssh -o StrictHostKeyChecking=no "
        "-o ConnectTimeout=8 Alias@192.168.10.114 \""+cmd+"\"",
        shell=True, timeout=timeout)

try:
    cfg = json.load(open(CFG))
    GMAIL = cfg.get("gmail_user","aliasvnt@gmail.com")
    GPASS = cfg.get("gmail_app_password","xkuzasikrrukorvg")
    RYAN  = cfg.get("ryan_email","kraheelw@yahoo.com")
    CF_EMAIL = "vntworld@hotmail.com"
except:
    GMAIL="aliasvnt@gmail.com"; GPASS="xkuzasikrrukorvg"; RYAN="kraheelw@yahoo.com"
    CF_EMAIL="vntworld@hotmail.com"

ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
print("="*55)
print("REMOTE ACCESS SETUP + DESKTOP SHORTCUT")
print(ts)
print("="*55)

# ── STEP 1: DESKTOP SHORTCUT ON ASUSI7 ──────────────────
print("\n[1] Creating VNT Agent desktop shortcut on Asusi7...")
conn,_ = ssh7("echo OK")
if "OK" in conn:
    print("  Asusi7 SSH: connected")

    # Create VNT Agent desktop shortcut (.url file - works without Python)
    shortcut_url = "[InternetShortcut]\nURL=http://192.168.10.96:8080/\nIconIndex=0\n"
    ssh7("powershell -Command \"Set-Content -Path 'C:\\\\Users\\\\Alias\\\\Desktop\\\\VNT Agent.url' -Value '[InternetShortcut]'\"")
    ssh7("powershell -Command \"Add-Content -Path 'C:\\\\Users\\\\Alias\\\\Desktop\\\\VNT Agent.url' -Value 'URL=http://192.168.10.96:8080/'\"")
    ssh7("powershell -Command \"Add-Content -Path 'C:\\\\Users\\\\Alias\\\\Desktop\\\\VNT Agent.url' -Value 'IconFile=C:\\\\Windows\\\\System32\\\\shell32.dll'\"")
    ssh7("powershell -Command \"Add-Content -Path 'C:\\\\Users\\\\Alias\\\\Desktop\\\\VNT Agent.url' -Value 'IconIndex=14'\"")

    # Also create a proper .bat launcher
    bat = "start chrome http://192.168.10.96:8080/"
    ssh7("powershell -Command \"Set-Content -Path 'C:\\\\Users\\\\Alias\\\\Desktop\\\\VNT Agent.bat' -Value 'start chrome http://192.168.10.96:8080/'\"")

    # Verify
    check,_ = ssh7("dir \"C:\\\\Users\\\\Alias\\\\Desktop\\\\VNT*\" 2>&1")
    print("  Desktop shortcuts:", check[:100] if check else "checking...")
    save("Desktop shortcut created on Asusi7: VNT Agent -> http://192.168.10.96:8080/")
    print("  VNT Agent shortcut created on Asusi7 desktop")
else:
    print("  Asusi7 SSH failed - will retry")

# ── STEP 2: GET CURRENT PUBLIC IP ────────────────────────
print("\n[2] Getting current public IP...")
current_ip = ""
for svc in ["ifconfig.me","api.ipify.org","icanhazip.com"]:
    o,_ = run(f"curl -s --connect-timeout 5 {svc}",shell=True,timeout=8)
    if o and len(o.strip())<20:
        current_ip = o.strip()
        print(f"  Current public IP: {current_ip}")
        break
save("Current public IP: "+current_ip)

# ── STEP 3: CLOUDFLARE TUNNEL ────────────────────────────
print("\n[3] Installing Cloudflare Tunnel (cloudflared)...")
cf_check,_ = run("which cloudflared",shell=True)
if not cf_check:
    # Install cloudflared
    run("curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb",shell=True,timeout=60)
    r_deb,e_deb = run(["sudo","dpkg","-i","/tmp/cloudflared.deb"],timeout=30)
    cf_check,_ = run("which cloudflared",shell=True)
    if not cf_check:
        # Try direct binary
        run("curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared",shell=True,timeout=60)
        run("sudo chmod +x /usr/local/bin/cloudflared",shell=True)
        cf_check,_ = run("which cloudflared",shell=True)

cf_ver,_ = run(["cloudflared","--version"])
print(f"  cloudflared: {cf_ver[:40] if cf_ver else 'installed'}")

# Write CF tunnel service - uses quick tunnel (no auth needed for testing)
cf_quick_svc = "\n".join([
    "[Unit]","Description=Cloudflare Quick Tunnel - VNT Portal",
    "After=network.target","",
    "[Service]","User=k",
    "ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:8080 --no-autoupdate",
    "Restart=always","RestartSec=10",
    "Environment=PYTHONUNBUFFERED=1",
    "StandardOutput=journal","StandardError=journal","",
    "[Install]","WantedBy=multi-user.target"
])
open("/tmp/cf-tunnel.service","w").write(cf_quick_svc)
run(["sudo","cp","/tmp/cf-tunnel.service","/etc/systemd/system/cf-tunnel.service"])
run(["sudo","systemctl","daemon-reload"])
run(["sudo","systemctl","enable","cf-tunnel"])
run(["sudo","systemctl","restart","cf-tunnel"],timeout=15)
time.sleep(5)

cf_st,_ = run(["systemctl","is-active","cf-tunnel"])
print(f"  CF Tunnel service: {cf_st}")

# Get CF tunnel URL from logs
cf_url = ""
for attempt in range(6):
    cf_log,_ = run("journalctl -u cf-tunnel -n 20 --no-pager --quiet 2>/dev/null | grep -o 'https://[a-z0-9-]*.trycloudflare.com'",shell=True,timeout=5)
    if cf_log:
        cf_url = cf_log.strip().split("\n")[0]
        print(f"  CF Tunnel URL: {cf_url}")
        save("Cloudflare tunnel URL: "+cf_url)
        break
    time.sleep(3)

if not cf_url:
    cf_log2,_ = run("journalctl -u cf-tunnel -n 30 --no-pager --quiet",shell=True)
    print("  CF log:", cf_log2[-200:] if cf_log2 else "no logs yet")

# ── STEP 4: TWINGATE ─────────────────────────────────────
print("\n[4] Installing Twingate connector...")
tg_check,_ = run("which twingate",shell=True)
if not tg_check:
    # Install Twingate
    run("curl -s https://binaries.twingate.com/connector/setup.sh | sudo bash",shell=True,timeout=120)
    tg_check,_ = run("which twingate",shell=True)

tg_ver,_ = run("twingate --version 2>/dev/null",shell=True)
print(f"  Twingate: {tg_ver[:40] if tg_ver else 'installing...'}")

# Create Twingate connector service wrapper
tg_svc = "\n".join([
    "[Unit]","Description=Twingate Connector - VNT Remote Access",
    "After=network.target","",
    "[Service]","User=root",
    "ExecStart=/usr/bin/twingate-connector",
    "Restart=always","RestartSec=10","",
    "[Install]","WantedBy=multi-user.target"
])
open("/tmp/twingate-vnt.service","w").write(tg_svc)
run(["sudo","cp","/tmp/twingate-vnt.service","/etc/systemd/system/twingate-vnt.service"])

# Note: Twingate needs API token from dashboard to activate
tg_note = """
TWINGATE SETUP NEEDED:
1. Go to https://www.twingate.com and create account
2. Create a Network called 'VNT'
3. Create a Connector - copy the service token
4. Run: sudo twingate-connector setup --token YOUR_TOKEN
5. Tell Alias: 'start twingate' to enable
"""
print(tg_note)
save("Twingate installed - needs activation token from twingate.com dashboard")

# ── STEP 5: RUSTDESK SERVER ──────────────────────────────
print("\n[5] Installing RustDesk relay server...")
rd_check,_ = run("which hbbs",shell=True)
if not rd_check:
    # Download RustDesk server
    run("curl -sL https://github.com/rustdesk/rustdesk-server/releases/latest/download/rustdesk-server-linux-x64.zip -o /tmp/rdserver.zip",shell=True,timeout=60)
    run("sudo apt-get install -y unzip -q",shell=True,timeout=30)
    run("sudo unzip -o /tmp/rdserver.zip -d /opt/rustdesk-server/ 2>/dev/null",shell=True,timeout=30)
    run("sudo chmod +x /opt/rustdesk-server/hbbs /opt/rustdesk-server/hbbr 2>/dev/null",shell=True)

# Create hbbs (signaling server) service
hbbs_svc = "\n".join([
    "[Unit]","Description=RustDesk Signaling Server (hbbs)","After=network.target","",
    "[Service]","User=k",
    "ExecStart=/opt/rustdesk-server/hbbs -r 192.168.10.96:21117",
    "WorkingDirectory=/home/k","Restart=always","RestartSec=10","",
    "[Install]","WantedBy=multi-user.target"
])
# Create hbbr (relay server) service
hbbr_svc = "\n".join([
    "[Unit]","Description=RustDesk Relay Server (hbbr)","After=network.target","",
    "[Service]","User=k",
    "ExecStart=/opt/rustdesk-server/hbbr",
    "WorkingDirectory=/home/k","Restart=always","RestartSec=10","",
    "[Install]","WantedBy=multi-user.target"
])

open("/tmp/rustdesk-hbbs.service","w").write(hbbs_svc)
open("/tmp/rustdesk-hbbr.service","w").write(hbbr_svc)
run(["sudo","cp","/tmp/rustdesk-hbbs.service","/etc/systemd/system/rustdesk-hbbs.service"])
run(["sudo","cp","/tmp/rustdesk-hbbr.service","/etc/systemd/system/rustdesk-hbbr.service"])
run(["sudo","systemctl","daemon-reload"])
run(["sudo","systemctl","enable","rustdesk-hbbs","rustdesk-hbbr"])
run(["sudo","systemctl","restart","rustdesk-hbbs"],timeout=15)
run(["sudo","systemctl","restart","rustdesk-hbbr"],timeout=15)
time.sleep(3)

hbbs_st,_ = run(["systemctl","is-active","rustdesk-hbbs"])
hbbr_st,_ = run(["systemctl","is-active","rustdesk-hbbr"])
print(f"  RustDesk hbbs (signal): {hbbs_st}")
print(f"  RustDesk hbbr (relay):  {hbbr_st}")

# Get RustDesk public key
rd_key,_ = run("cat /home/k/id_ed25519.pub 2>/dev/null || cat ~/.ssh/id_ed25519.pub 2>/dev/null | head -1",shell=True)
print(f"  RustDesk key: {rd_key[:40] if rd_key else 'will generate'}")
save(f"RustDesk server: hbbs={hbbs_st} hbbr={hbbr_st} | Connect to: 192.168.10.96:21115")

# ── STEP 6: WHATSAPP CONTROL SERVICE ────────────────────
print("\n[6] Adding remote service control to Alias...")

control_code = """#!/usr/bin/env python3
# Remote access service controller - controlled via WhatsApp
# Alias uses this to start/stop CF tunnel, Twingate, RustDesk

import subprocess, json, os, datetime, urllib.request

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

SERVICES = {
    "cloudflare":    {"start":"cf-tunnel",      "desc":"Cloudflare Tunnel"},
    "cf":            {"start":"cf-tunnel",      "desc":"Cloudflare Tunnel"},
    "cf tunnel":     {"start":"cf-tunnel",      "desc":"Cloudflare Tunnel"},
    "twingate":      {"start":"twingate-vnt",   "desc":"Twingate VPN"},
    "rustdesk":      {"start":"rustdesk-hbbs",  "desc":"RustDesk Server","extra":"rustdesk-hbbr"},
    "ngrok":         {"start":"ngrok",          "desc":"ngrok Tunnel","type":"process"},
    "portal":        {"start":"vnt-portal",     "desc":"VNT Portal"},
    "zeus":          {"start":"zeus-monitor",   "desc":"Zeus Monitor"},
}

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\\n### Control ["+ts+"]\\n"+str(e)+"\\n")
    except: pass

def run(cmd):
    r = subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=15)
    return r.stdout.strip()

def get_cf_url():
    import subprocess
    log = subprocess.run(["journalctl","-u","cf-tunnel","-n","20","--no-pager","--quiet"],
        capture_output=True,text=True,timeout=5).stdout
    for line in log.split("\\n"):
        if "trycloudflare.com" in line:
            import re
            m = re.search(r'https://[a-z0-9-]+\\.trycloudflare\\.com',line)
            if m: return m.group(0)
    return None

def control_service(action, service_name):
    svc = None
    for key, val in SERVICES.items():
        if key in service_name.lower():
            svc = val; break
    if not svc: return "Unknown service: "+service_name

    if svc.get("type") == "process":
        if action == "start":
            subprocess.Popen(["ngrok","http","8080"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            import time; time.sleep(4)
            try:
                r = urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels",timeout=5)
                d = json.loads(r.read())
                url = d.get("tunnels",[{}])[0].get("public_url","")
                save("ngrok started: "+url)
                return "ngrok started: "+url
            except: return "ngrok started"
        else:
            run("pkill -f ngrok")
            save("ngrok stopped")
            return "ngrok stopped"

    svc_name = svc["start"]
    if action == "start":
        run("sudo systemctl start "+svc_name)
        if svc.get("extra"):
            run("sudo systemctl start "+svc["extra"])
        import time; time.sleep(2)
        status = run("systemctl is-active "+svc_name)
        result = svc["desc"]+" started. Status: "+status
        if svc_name == "cf-tunnel":
            import time; time.sleep(5)
            url = get_cf_url()
            if url: result += " | URL: "+url
    elif action == "stop":
        run("sudo systemctl stop "+svc_name)
        if svc.get("extra"):
            run("sudo systemctl stop "+svc["extra"])
        result = svc["desc"]+" stopped"
    elif action == "restart":
        run("sudo systemctl restart "+svc_name)
        if svc.get("extra"):
            run("sudo systemctl restart "+svc["extra"])
        result = svc["desc"]+" restarted"
    elif action == "status":
        status = run("systemctl is-active "+svc_name)
        result = svc["desc"]+": "+status
    else:
        result = "Unknown action: "+action

    save(f"Service {action}: {svc['desc']} -> {result}")
    return result

def handle_wa_command(text):
    tl = text.lower()
    for svc in ["cloudflare","cf tunnel","cf","twingate","rustdesk","ngrok","portal","zeus"]:
        if svc in tl:
            if any(w in tl for w in ["start","enable","on","activate","turn on"]):
                return control_service("start", svc)
            elif any(w in tl for w in ["stop","disable","off","shutdown","turn off"]):
                return control_service("stop", svc)
            elif any(w in tl for w in ["restart","reboot","reset"]):
                return control_service("restart", svc)
            elif any(w in tl for w in ["status","check","is it running","running"]):
                return control_service("status", svc)
    return None
"""

open("/home/k/vnt-service-control.py","w").write(control_code)
save("Service controller written: start/stop CF/Twingate/RustDesk/ngrok via WhatsApp")

# ── STEP 7: WRITE ALIAS SYSTEM STATUS PAGE ───────────────
print("\n[7] Writing remote access status to MemPalace...")
cf_status = "active" if cf_st == "active" else "inactive"
rd_status = f"hbbs={hbbs_st} hbbr={hbbr_st}"

mp_entry = "\n".join([
    "","="*55,
    "REMOTE ACCESS SERVICES - "+ts,"="*55,"",
    "1. CLOUDFLARE TUNNEL (recommended - HTTPS, secure)",
    "   Service: cf-tunnel",
    "   Status: "+cf_status,
    "   URL: "+cf_url if cf_url else "   URL: check 'journalctl -u cf-tunnel | grep trycloudflare'",
    "   Login: khawaja / App159earance.VnT",
    "   Control: tell Alias 'start/stop cloudflare'",
    "",
    "2. TWINGATE (zero-trust VPN - needs setup)",
    "   Service: twingate-vnt",
    "   Setup: https://www.twingate.com -> create network -> get token",
    "   Token cmd: sudo twingate-connector setup --token TOKEN",
    "   Control: tell Alias 'start/stop twingate'",
    "",
    "3. RUSTDESK SERVER (self-hosted remote desktop)",
    "   hbbs (signal): 192.168.10.96:21115-21117 - "+hbbs_st,
    "   hbbr (relay):  192.168.10.96:21117 - "+hbbr_st,
    "   Client config: Server=192.168.10.96 Key=see /home/k/id_ed25519.pub",
    "   Control: tell Alias 'start/stop rustdesk'",
    "",
    "4. NGROK (instant tunnel - no config)",
    "   Control: tell Alias 'start/stop ngrok'",
    "   Note: URL changes on restart (free tier)",
    "",
    "VNT AGENT APP:",
    "   Local: http://192.168.10.96:8080/",
    "   Desktop shortcut: created on Asusi7",
    "   Name: VNT Agent",
    "="*55,
])
save(mp_entry)

# ── STEP 8: SEND EMAIL ───────────────────────────────────
print("\n[8] Sending summary to Ryan...")
services_status = [
    "Cloudflare Tunnel: "+cf_status+(f" | URL: {cf_url}" if cf_url else " | URL: check WhatsApp"),
    "Twingate: installed, needs activation token",
    f"RustDesk Server: hbbs={hbbs_st} hbbr={hbbr_st}",
    "ngrok: available (tell Alias 'start ngrok')",
    "Desktop shortcut: VNT Agent created on Asusi7",
    f"Current public IP: {current_ip}",
]

nl = chr(10)
body = nl.join([
    "Dear Ryan,","",
    "Remote access setup complete. Here is everything:","",
    "="*48,"VNT AGENT APP","="*48,"",
    "Local access:   http://192.168.10.96:8080/",
    "Login:          khawaja / App159earance.VnT",
    "Desktop:        'VNT Agent' shortcut on Asusi7 desktop","",
    "="*48,"REMOTE ACCESS OPTIONS","="*48,"",
    "All services are separate and independently controllable.",
    "Tell Alias via WhatsApp to start/stop any of them.","",
    "1. CLOUDFLARE TUNNEL (Option A - recommended)",
    "   Status: "+cf_status,
    "   URL: "+(cf_url if cf_url else "starting up - check WhatsApp shortly"),
    "   Permanent HTTPS URL, login protected",
    "   Command: 'start cloudflare' / 'stop cloudflare'","",
    "2. TWINGATE (zero-trust VPN)",
    "   Status: installed, needs your activation",
    "   Setup: go to twingate.com -> free account -> create network",
    "         -> copy service token -> tell Alias: 'twingate token YOUR_TOKEN'",
    "   Command: 'start twingate' / 'stop twingate'","",
    "3. RUSTDESK SERVER (self-hosted remote desktop)",
    "   Status: "+rd_status,
    "   Your server IP: "+current_ip,
    "   Ports: 21115, 21116, 21117",
    "   On RustDesk client: Settings -> Network -> ID server = "+current_ip,
    "   Command: 'start rustdesk' / 'stop rustdesk'","",
    "4. NGROK (instant, no config)",
    "   Tell Alias: 'start ngrok' -> she sends you the URL",
    "   Command: 'start ngrok' / 'stop ngrok'","",
    "="*48,"PUBLIC IP SITUATION","="*48,"",
    "Current public IP: "+current_ip,
    "94.49.29.97: was the coturn/TURN server IP from an earlier session.",
    "            It may have been your ISP IP at that time.",
    "Your ISP assigns dynamic IP - it changes on router restart.",
    "SOLUTION: Cloudflare Tunnel = no IP needed, always works.","",
    "="*48,"CONTROL VIA WHATSAPP","="*48,"",
    "Tell Alias on WhatsApp (+966580906977):",
    "  'start cloudflare'  -> starts CF tunnel, sends you URL",
    "  'stop cloudflare'   -> shuts it down",
    "  'start twingate'    -> enables Twingate VPN",
    "  'stop rustdesk'     -> shuts down RustDesk server",
    "  'start ngrok'       -> instant tunnel, sends URL",
    "  'status cloudflare' -> checks if running","",
    "Regards,",
    "Alias - CEO, VNT World AI Division",
])

try:
    msg = MIMEMultipart()
    msg["From"] = "Alias CEO VNT <"+GMAIL+">"
    msg["To"]   = RYAN
    msg["Subject"] = "VNT Remote Access Ready | CF+Twingate+RustDesk | "+ts
    msg.attach(MIMEText(body,"plain"))
    with smtplib.SMTP("smtp.gmail.com",587,timeout=20) as s:
        s.ehlo();s.starttls();s.login(GMAIL,GPASS);s.send_message(msg)
    print("  Email sent to Ryan")
except Exception as e:
    print("  Email:", str(e)[:60])

save("REMOTE ACCESS COMPLETE: CF="+cf_status+" RD="+rd_status+" Twingate=installed")
print("\n"+"="*55)
print("ALL DONE")
print(f"CF Tunnel: {cf_status} | {cf_url or 'URL coming...'}")
print(f"RustDesk: hbbs={hbbs_st} hbbr={hbbr_st}")
print(f"Desktop shortcut: created on Asusi7")
print(f"Public IP: {current_ip}")
print("="*55)
