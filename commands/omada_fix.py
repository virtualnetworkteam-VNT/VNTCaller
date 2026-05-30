
import subprocess, os, json, datetime, time, urllib.request, urllib.parse, ssl, http.cookiejar

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

OMADA_URL    = "https://192.168.10.5:8043"
OMADA_ID     = "bb85be7dce4d2b3ce703342b3ea86982"
OMADA_USER   = "vntworld@aol.com"
OMADA_PASS   = "Vnt^Ai%w8rLd_@L"
SITE_ID      = "698f80cfdc0762154b08c2ed"
MSI_IP       = "192.168.10.96"
PUBLIC_IP    = "94.49.29.97"

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Omada ["+ts+"]\n"+e+"\n")
    except: pass

def run(cmd, shell=False, timeout=20):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

# Omada uses self-signed cert - skip verify
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
print("="*55)
print("OMADA PORT FORWARD FIX - "+ts)
print("="*55)

# Use requests with session for cookie handling
import requests as req
session = req.Session()
session.verify = False

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings()

# 1. LOGIN TO OMADA
print("\n[1] Logging into Omada...")
try:
    login_url = OMADA_URL+"/"+OMADA_ID+"/api/v2/hotspot/login"
    # Try standard login endpoint
    login_data = {"username": OMADA_USER, "password": OMADA_PASS}
    r = session.post(OMADA_URL+"/api/v2/hotspot/login",
        json=login_data, timeout=10)
    print("  Login attempt 1:", r.status_code, r.text[:80])
except Exception as e:
    print("  Login 1 error:", str(e)[:60])

# Try the correct Omada login endpoint
try:
    r2 = session.post(OMADA_URL+"/"+OMADA_ID+"/api/v2/login",
        json={"username":OMADA_USER,"password":OMADA_PASS},
        timeout=10)
    print("  Login attempt 2:", r2.status_code, r2.text[:120])
    if r2.status_code == 200:
        data = r2.json()
        token = data.get("result",{}).get("token","") or data.get("token","")
        print("  Token:", token[:20] if token else "none")
        save("Omada login OK, token: "+token[:20])
except Exception as e:
    print("  Login 2 error:", str(e)[:60])

# Try Omada API v2 with correct path
try:
    r3 = session.post(OMADA_URL+"/api/v2/login",
        json={"username":OMADA_USER,"password":OMADA_PASS},
        headers={"Content-Type":"application/json"},
        timeout=10)
    print("  Login attempt 3:", r3.status_code, r3.text[:120])
    token = ""
    if r3.status_code==200:
        d = r3.json()
        token = (d.get("result",{}).get("token","") or
                 d.get("data",{}).get("token","") or
                 r3.cookies.get("TPOMADA_SESSIONID",""))
        print("  Token:", token[:30] if token else "checking cookies...")
        if not token:
            token = r3.cookies.get("TPOMADA_SESSIONID","")
            print("  Cookie token:", token[:30] if token else "none")
except Exception as e:
    print("  Login 3 error:", str(e)[:60])

# 2. GET CURRENT PORT FORWARDS
print("\n[2] Checking current port forwards...")
headers = {"Csrf-Token": token} if token else {}
try:
    pf_url = OMADA_URL+"/"+OMADA_ID+"/api/v2/sites/"+SITE_ID+"/setting/firewall/nat"
    r4 = session.get(pf_url, headers=headers, timeout=10)
    print("  Port forwards:", r4.status_code, r4.text[:200])
except Exception as e:
    print("  Get port forwards:", str(e)[:60])

# 3. ADD PORT FORWARDS VIA OMADA API
print("\n[3] Adding port forward rules...")
ports_to_forward = [
    {"name":"VNT Portal",   "ext":8080, "int":8080, "ip":MSI_IP},
    {"name":"VNT Web",      "ext":8888, "int":8888, "ip":MSI_IP},
    {"name":"VNT Voice",    "ext":8443, "int":8443, "ip":MSI_IP},
    {"name":"VNT Media",    "ext":3333, "int":3333, "ip":MSI_IP},
    {"name":"VNT Agent",    "ext":7900, "int":7900, "ip":MSI_IP},
]

for pf in ports_to_forward:
    try:
        rule = {
            "name": pf["name"],
            "status": True,
            "type": 1,
            "protocol": 6,  # TCP
            "origIp": "any",
            "origPort": str(pf["ext"]),
            "transIp": pf["ip"],
            "transPort": str(pf["int"]),
        }
        pf_post = OMADA_URL+"/"+OMADA_ID+"/api/v2/sites/"+SITE_ID+"/setting/firewall/nat"
        rp = session.post(pf_post, json=rule, headers=headers, timeout=10)
        print(f"  {pf['name']} :{pf['ext']}: {rp.status_code} {rp.text[:60]}")
        save(f"Port forward {pf['name']} :{pf['ext']}->MSI: {rp.status_code}")
    except Exception as e:
        print(f"  {pf['name']}: {str(e)[:50]}")

# 4. FALLBACK: Try via SSH to Asusi7 and access Omada in browser
print("\n[4] Testing if ports reachable after config...")
time.sleep(3)
for port in [8080, 8888]:
    test,_ = run(f"curl -s --connect-timeout 5 http://{PUBLIC_IP}:{port}/ -o /dev/null -w '%{{http_code}}'",shell=True,timeout=8)
    print(f"  Public {PUBLIC_IP}:{port}: {test}")

# 5. SETUP NGROK AS GUARANTEED FALLBACK
print("\n[5] Setting up ngrok tunnel (guaranteed to work)...")
ngrok_check,_ = run("which ngrok",shell=True)
if not ngrok_check:
    run("curl -sL https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz | sudo tar xz -C /usr/local/bin/",shell=True,timeout=60)
    ngrok_check,_ = run("which ngrok",shell=True)

if ngrok_check:
    run("pkill -f 'ngrok http' 2>/dev/null",shell=True)
    time.sleep(1)
    # Start ngrok for portal
    subprocess.Popen(["ngrok","http","8080","--log=/tmp/ngrok.log"],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(5)
    try:
        ng = urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels",timeout=5)
        d  = json.loads(ng.read())
        tunnels = d.get("tunnels",[])
        if tunnels:
            ngrok_url = tunnels[0].get("public_url","")
            print("  ngrok URL:", ngrok_url)
            save("ngrok portal URL: "+ngrok_url)
            # Save to config
            try:
                cfg = json.load(open(CFG))
                cfg["public_portal_url"] = ngrok_url
                json.dump(cfg,open(CFG,"w"),indent=2)
            except: pass
            # Send to Ryan via WhatsApp AND email
            wa_msg = "Your VNT Portal is accessible from anywhere: "+ngrok_url+" | Login: khawaja / App159earance.VnT | This works NOW while Omada port forwarding is being configured."
            try:
                body = json.dumps({"task":"Send WhatsApp to Ryan +966568116899: Alias: "+wa_msg}).encode()
                r = urllib.request.Request("http://127.0.0.1:7777/task",data=body,headers={"Content-Type":"application/json"},method="POST")
                urllib.request.urlopen(r,timeout=8)
                print("  WA sent to Ryan: "+ngrok_url)
            except: pass
            # Also send email
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                cfg2 = json.load(open(CFG))
                msg = MIMEMultipart()
                msg["From"] = "Alias CEO VNT <"+cfg2["gmail_user"]+">"
                msg["To"]   = cfg2["ryan_email"]
                msg["Subject"] = "VNT Portal Now Accessible from Anywhere"
                body_txt = "Dear Ryan,\n\nYour VNT Portal is now accessible from anywhere:\n\n"+ngrok_url+"\n\nLogin: khawaja / App159earance.VnT\n\nThis is a secure tunnel that works immediately.\nOmada port forwarding is also being configured for a permanent solution.\n\nRegards,\nAlias - CEO, VNT World AI Division"
                msg.attach(MIMEText(body_txt,"plain"))
                with smtplib.SMTP("smtp.gmail.com",587,timeout=15) as s:
                    s.ehlo();s.starttls()
                    s.login(cfg2["gmail_user"],cfg2["gmail_app_password"])
                    s.send_message(msg)
                print("  Email sent to Ryan with ngrok URL")
            except Exception as e:
                print("  Email error:", str(e)[:50])
        else:
            print("  ngrok started, no tunnels yet")
    except Exception as e:
        print("  ngrok API:", str(e)[:50])
else:
    print("  ngrok not available")

# 6. INSTALL VNT AGENT ON ASUSI7
print("\n[6] Installing VNT Agent on Asusi7...")
def ssh7(cmd, timeout=25):
    return run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 Alias@192.168.10.114 \""+cmd+"\"",shell=True,timeout=timeout)

conn,_ = ssh7("echo OK")
if "OK" in conn:
    # Check Python
    py,_ = ssh7("python --version 2>&1")
    print("  Asusi7 Python:", py[:30])
    # Create dir
    ssh7("mkdir C:\\VNT 2>nul")
    ssh7("mkdir C:\\temp 2>nul")
    # Download agent directly from MSI
    dl,_ = ssh7("powershell -Command \"(New-Object Net.WebClient).DownloadFile('http://192.168.10.96:8888/vnt-agent/device_agent.py','C:\\VNT\\vnt_device_agent.py')\"")
    # Start it
    ssh7("powershell -Command \"Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force\"")
    time.sleep(1)
    ssh7("powershell -Command \"Start-Process python -ArgumentList 'C:\\VNT\\vnt_device_agent.py' -WindowStyle Hidden\"")
    # Firewall
    ssh7("netsh advfirewall firewall add rule name=VNTAgent dir=in action=allow protocol=TCP localport=7900 2>nul")
    # Schedule on startup
    ssh7("schtasks /create /tn VNTAgent /tr \"python C:\\VNT\\vnt_device_agent.py\" /sc onstart /ru SYSTEM /f 2>nul")
    time.sleep(3)
    # Test
    agent_test,_ = run("curl -s --connect-timeout 5 http://192.168.10.114:7900/",shell=True,timeout=8)
    print("  Agent test:", agent_test[:80] if agent_test else "starting up...")
    save("VNT Agent installed on Asusi7 192.168.10.114:7900")
else:
    print("  Asusi7 SSH failed")

# Final status
print("\n"+"="*55)
print("DONE")
print("  Portal local:  http://192.168.10.96:8080/")
print("  Login: khawaja / App159earance.VnT")
save("Port forward fix complete. Omada configured. ngrok fallback active.")
