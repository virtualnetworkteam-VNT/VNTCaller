
import subprocess, time, urllib.request, json, os, datetime

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

def run(cmd, shell=False, timeout=20):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Test ["+ts+"]\n"+e+"\n")
    except: pass

def ssh7(cmd, timeout=20):
    return run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 Alias@192.168.10.114 \""+cmd+"\"", shell=True, timeout=timeout)

print("="*55)
print("LIVE TEST - OPENING BROWSER ON ASUSI7")
print("="*55)

# 1. Confirm Asusi7 connected
out,_ = ssh7("echo CONNECTED && hostname")
print("Asusi7:", out[:40])

# 2. Check what MSI portal service is actually doing
print("\n[Portal] MSI portal status...")
portal_st,_ = run(["systemctl","is-active","vnt-portal"])
print("  vnt-portal service:", portal_st)

# Check if anything listening on 8080
listening,_ = run("ss -tlnp | grep 8080", shell=True)
print("  Port 8080 listening:", listening if listening else "NOTHING - portal not running")

# Check webserver on 8888
web_st,_ = run(["systemctl","is-active","vnt-webserver"])
listening2,_ = run("ss -tlnp | grep 8888", shell=True)
print("  Port 8888 listening:", listening2 if listening2 else "nothing on 8888")

# Start portal if not running
if not listening:
    print("  Starting portal...")
    run(["sudo","systemctl","restart","vnt-portal"], timeout=15)
    time.sleep(3)
    listening,_ = run("ss -tlnp | grep 8080", shell=True)
    print("  After restart:", listening if listening else "still not listening")
    
    # Check why it failed
    if not listening:
        log,_ = run("journalctl -u vnt-portal -n 20 --no-pager --quiet", shell=True)
        print("  Portal log:", log[-200:] if log else "no logs")

# 3. Get current public IP
pub_ip,_ = run("curl -s --connect-timeout 5 ifconfig.me", shell=True, timeout=8)
print("\n[IP] Current public IP:", pub_ip)

# Also get IP from Asusi7
asusi7_ip,_ = ssh7("powershell -Command \"(Invoke-WebRequest -Uri 'https://api.ipify.org' -UseBasicParsing).Content\" 2>&1")
print("  Asusi7 public IP:", asusi7_ip[:20])

# 4. OPEN BROWSER ON ASUSI7 - test local first
print("\n[BROWSER] Opening browser on Asusi7...")
# Open local portal
ssh7("start http://192.168.10.96:8080/")
time.sleep(2)
print("  Opened: http://192.168.10.96:8080/")

# Test if local works from Asusi7
local_test,_ = ssh7("powershell -Command \"try{(New-Object Net.WebClient).DownloadString('http://192.168.10.96:8080/')}catch{$_.Exception.Message}\" 2>&1")
print("  Local portal from Asusi7:", local_test[:80] if local_test else "no response")

# 5. Test public IP from Asusi7
print("\n[PUBLIC] Testing 94.49.29.97 from Asusi7...")
pub_test,_ = ssh7("powershell -Command \"try{(New-Object Net.WebClient).DownloadString('http://94.49.29.97:8080/')}catch{$_.Exception.Message}\" 2>&1")
print("  94.49.29.97:8080 from Asusi7:", pub_test[:80])

# Open public in browser too
ssh7("start http://94.49.29.97:8080/")
time.sleep(1)
print("  Opened 94.49.29.97:8080 in Asusi7 browser")

# 6. GET CLOUDFLARE TUNNEL URL
print("\n[CF] Getting Cloudflare tunnel URL...")
cf_st,_ = run(["systemctl","is-active","cf-tunnel"])
print("  cf-tunnel service:", cf_st)

if cf_st != "active":
    run(["sudo","systemctl","restart","cf-tunnel"], timeout=15)
    time.sleep(6)

cf_url = ""
for i in range(8):
    cf_log,_ = run("journalctl -u cf-tunnel -n 30 --no-pager --quiet 2>/dev/null", shell=True)
    import re
    m = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', cf_log or "")
    if m:
        cf_url = m.group(0)
        print("  CF URL:", cf_url)
        break
    time.sleep(2)

if cf_url:
    # Open in Asusi7 browser
    ssh7("start "+cf_url)
    print("  Opened CF URL in Asusi7 browser")
    
    # Save and notify
    save("Cloudflare tunnel: "+cf_url)
    try:
        cfg = json.load(open(CFG))
        cfg["cloudflare_tunnel_url"] = cf_url
        json.dump(cfg, open(CFG,"w"), indent=2)
    except: pass
    
    # Send WhatsApp
    try:
        wa_msg = "Portal now accessible: "+cf_url+" | Login: khawaja / App159earance.VnT | Opened in Asusi7 browser now."
        body = json.dumps({"task":"Send WhatsApp to Ryan +966568116899: Alias: "+wa_msg}).encode()
        req = urllib.request.Request("http://127.0.0.1:7777/task",data=body,headers={"Content-Type":"application/json"},method="POST")
        urllib.request.urlopen(req,timeout=8)
        print("  WhatsApp sent to Ryan with CF URL")
    except: pass
else:
    cf_log2,_ = run("journalctl -u cf-tunnel -n 30 --no-pager --quiet", shell=True)
    print("  CF log:", cf_log2[-300:] if cf_log2 else "no logs")

# 7. DIAGNOSE WHY 94.49.29.97 FAILS - check Omada/router
print("\n[OMADA] Checking port forward via Omada API...")
import ssl, requests as req_lib
session = req_lib.Session()
session.verify = False
import urllib3; urllib3.disable_warnings()

OMADA_URL = "https://192.168.10.5:8043"
OMADA_ID  = "bb85be7dce4d2b3ce703342b3ea86982"
SITE_ID   = "698f80cfdc0762154b08c2ed"

# Login
try:
    r = session.post(OMADA_URL+"/"+OMADA_ID+"/api/v2/login",
        json={"username":"vntworld@aol.com","password":"Vnt^Ai%w8rLd_@L"},
        timeout=10)
    print("  Omada login:", r.status_code)
    if r.status_code == 200:
        d = r.json()
        token = d.get("result",{}).get("token","") or d.get("data",{}).get("token","")
        # Try cookie too
        if not token:
            token = r.cookies.get("TPOMADA_SESSIONID","") or r.cookies.get("sessionId","")
        print("  Token:", token[:20] if token else "none, checking cookies: "+str(dict(r.cookies))[:80])
        
        headers = {"Csrf-Token":token} if token else {}
        
        # Get existing NAT rules
        nat,_ = session.get(OMADA_URL+"/"+OMADA_ID+"/api/v2/sites/"+SITE_ID+"/setting/firewall/nat",
            headers=headers, timeout=10), None
        nat = nat if hasattr(nat,'status_code') else None
        if nat:
            print("  NAT rules:", nat.status_code, nat.text[:200])
except Exception as e:
    print("  Omada error:", str(e)[:80])

print("\n"+"="*55)
print("RESULT:")
print("  Current public IP:", pub_ip)
print("  CF Tunnel:", cf_url or "check cf-tunnel service")
print("  94.49.29.97:", "different IP from current" if pub_ip and pub_ip != "94.49.29.97" else "same")
save("Live test done. CF:"+cf_url+" pub_ip:"+pub_ip)
