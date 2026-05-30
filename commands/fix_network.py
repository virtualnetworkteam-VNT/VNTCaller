
import subprocess, os, json, datetime, time, urllib.request

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

def run(cmd, shell=False, timeout=20):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Net Fix ["+ts+"]\n"+e+"\n")
    except: pass

def ssh7(cmd, timeout=25):
    return run(
        "sshpass -p '116899' ssh -o StrictHostKeyChecking=no "
        "-o ConnectTimeout=5 Alias@192.168.10.114 \""+cmd+"\"",
        shell=True, timeout=timeout)

ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
print("="*55)
print("NETWORK DIAGNOSIS + PORT FORWARD FIX")
print(ts)
print("="*55)

# 1. Check MSI services are actually listening
print("\n[1] MSI - what ports are listening...")
listening,_ = run("ss -tlnp | grep -E ':8080|:8888|:8443|:80 '", shell=True)
print("  Listening:", listening if listening else "nothing on those ports")

# Check portal service
portal_st,_ = run(["systemctl","is-active","vnt-portal"])
web_st,_    = run(["systemctl","is-active","vnt-webserver"])
print("  Portal :8080:", portal_st)
print("  Webserver :8888:", web_st)

# Restart if not running
if portal_st != "active":
    run(["sudo","systemctl","restart","vnt-portal"], timeout=10)
    time.sleep(2)
    portal_st,_ = run(["systemctl","is-active","vnt-portal"])
    print("  Portal restarted:", portal_st)

# Test locally on MSI
local_test,_ = run("curl -s --connect-timeout 3 http://127.0.0.1:8080/ | grep -o 'VNT\|Login'", shell=True, timeout=8)
print("  Local 8080 test:", local_test if local_test else "not responding locally")

# 2. Check if Asusi7 SSH works
print("\n[2] Asusi7 SSH test...")
ssh_out,ssh_err = ssh7("echo SSH_OK && ipconfig | findstr /i 'IPv4' | head -3")
if "SSH_OK" in ssh_out:
    print("  Asusi7 SSH: CONNECTED")
    print("  IPs:", ssh_out.replace("SSH_OK","").strip()[:100])
else:
    print("  Asusi7 SSH FAILED:", ssh_err[:60])
    save("Asusi7 SSH failed")
    import sys; sys.exit(1)

# 3. Test from Asusi7 - can it reach MSI portal?
print("\n[3] Testing from Asusi7 -> MSI portal...")
asusi7_test,_ = ssh7("powershell -Command \"(New-Object Net.WebClient).DownloadString('http://192.168.10.96:8080/') | Select-Object -First 1\" 2>&1 | head -3")
print("  Asusi7->MSI:8080:", asusi7_test[:80] if asusi7_test else "failed")

# 4. Test from Asusi7 - can it reach public IP?
print("\n[4] Testing public IP from Asusi7...")
pub_test,_ = ssh7("powershell -Command \"try{(New-Object Net.WebClient).DownloadString('http://94.49.29.97:8080/')}catch{$_.Exception.Message}\" 2>&1")
print("  Asusi7->public:8080:", pub_test[:80])

# Also test ping to public
ping_test,_ = ssh7("ping 94.49.29.97 -n 2 -w 2000 2>&1 | findstr 'TTL\|Request\|timeout'")
print("  Ping public:", ping_test[:60] if ping_test else "no response")

# 5. Get router IP from Asusi7
print("\n[5] Getting network info from Asusi7...")
gw_info,_ = ssh7("powershell -Command \"Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -ExpandProperty NextHop\"")
print("  Default gateway:", gw_info[:30] if gw_info else "unknown")

# Try Linksys router - Omada controller at 192.168.10.5
print("\n[6] Checking Omada controller (192.168.10.5)...")
omada_test,_ = run("curl -s --connect-timeout 5 http://192.168.10.5:8043/ -o /dev/null -w '%{http_code}'", shell=True, timeout=8)
print("  Omada :8043:", omada_test)

# Check if UPnP is available for auto port forward
upnp_check,_ = run("python3 -c "import miniupnpc" 2>&1", shell=True)
if "No module" in upnp_check:
    run("pip install miniupnpc --break-system-packages -q", shell=True, timeout=60)

# Try UPnP auto port forward
print("\n[7] Attempting UPnP auto port forward...")
upnp_script = """
import miniupnpc
u = miniupnpc.UPnP()
u.discoverdelay = 2000
n = u.discover()
print('UPnP devices:', n)
if n > 0:
    u.selectigd()
    ext_ip = u.externalipaddress()
    print('External IP:', ext_ip)
    for port, ext_port, desc in [(8080,8080,'VNT Portal'),(8888,8888,'VNT Web'),(8443,8443,'VNT Voice')]:
        try:
            result = u.addportmapping(ext_port,'TCP','192.168.10.96',port,desc,'')
            print(f'Forwarded {ext_port} -> 192.168.10.96:{port}: {result}')
        except Exception as e:
            print(f'Port {ext_port}: {e}')
else:
    print('No UPnP devices found - manual router config needed')
"""
try:
    r2 = subprocess.run(["python3","-c",upnp_script], capture_output=True, text=True, timeout=30)
    print("  UPnP result:", r2.stdout[:200] if r2.stdout else r2.stderr[:100])
    save("UPnP attempt: "+r2.stdout[:100])
except Exception as e:
    print("  UPnP error:", str(e)[:60])

# 8. Try Linksys SmartWifi via Asusi7 browser
print("\n[8] Router access instructions for Ryan...")
router_info = """
ROUTER PORT FORWARDING - 2 OPTIONS:

OPTION A - Omada Controller (if accessible):
  URL: http://192.168.10.5:8043
  Add port forward rules:
    8080 TCP -> 192.168.10.96 (VNT Portal)
    8888 TCP -> 192.168.10.96 (VNT Web)
    8443 TCP -> 192.168.10.96 (VNT Voice)

OPTION B - Linksys Router:
  URL: http://linksyssmartwifi.com or http://192.168.10.1
  Settings -> Security -> Apps and Gaming -> Port Forwarding
  Add: 8080 TCP -> 192.168.10.96

OPTION C - Use ngrok (instant, no router config):
  Runs on MSI, creates secure tunnel automatically
  Access via: https://[random].ngrok.io
"""
print(router_info)

# 9. Install and start ngrok as fallback
print("\n[9] Setting up ngrok as instant public access...")
ngrok_check,_ = run("which ngrok 2>/dev/null", shell=True)
if not ngrok_check:
    # Download ngrok
    run("wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -O /tmp/ngrok.tgz", shell=True, timeout=60)
    run("tar -xzf /tmp/ngrok.tgz -C /usr/local/bin/", shell=True)
    ngrok_check,_ = run("which ngrok", shell=True)

if ngrok_check:
    print("  ngrok: available at", ngrok_check)
    # Start ngrok tunnel for portal
    run("pkill -f ngrok 2>/dev/null", shell=True)
    subprocess.Popen(["ngrok","http","8080","--log=/tmp/ngrok.log"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    # Get tunnel URL
    try:
        ng_req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels")
        with urllib.request.urlopen(ng_req, timeout=5) as r:
            ng_data = json.loads(r.read())
            tunnels = ng_data.get("tunnels",[])
            if tunnels:
                url = tunnels[0].get("public_url","")
                print("  ngrok tunnel: "+url)
                save("ngrok tunnel created: "+url)
                # Update config with ngrok URL
                try:
                    cfg = json.load(open(CFG))
                    cfg["public_portal_url"] = url
                    cfg["ngrok_tunnel"] = url
                    json.dump(cfg, open(CFG,"w"), indent=2)
                except: pass
                # Send WhatsApp notification
                try:
                    body = json.dumps({"task":"Send WhatsApp to Ryan +966568116899: Alias: Your VNT Portal is now accessible from anywhere at: "+url+" | Login: khawaja / App159earance.VnT"}).encode()
                    req3 = urllib.request.Request("http://127.0.0.1:7777/task",
                        data=body,headers={"Content-Type":"application/json"},method="POST")
                    urllib.request.urlopen(req3, timeout=8)
                    print("  WhatsApp sent to Ryan with portal URL")
                except: pass
            else:
                print("  ngrok started, tunnel not ready yet")
    except Exception as e:
        print("  ngrok API:", str(e)[:50])
else:
    print("  ngrok not available - use router option above")

# Final summary
print("\n"+"="*55)
print("SUMMARY:")
print("  Local portal:  http://192.168.10.96:8080/")
print("  Portal status:", portal_st)
print("  Asusi7 SSH:   ", "OK" if "SSH_OK" in ssh_out else "FAIL")
print("  Public access: router port forward needed OR ngrok")
save("Network diagnosis complete. Portal:"+portal_st+" Asusi7:"+("OK" if "SSH_OK" in ssh_out else "FAIL"))
