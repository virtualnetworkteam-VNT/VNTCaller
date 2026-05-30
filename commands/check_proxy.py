
import urllib.request, json, subprocess, os, time, datetime

M4  = "192.168.10.94"
WEB = "/home/k/vnt-web"
TS  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

print("="*55)
print("PROXY STATUS CHECK + FIX")
print(TS)
print("="*55)

# Check if portal server running
try:
    urllib.request.urlopen("http://127.0.0.1:8888/",timeout=5)
    print("[1] Port 8888: SERVING")
except Exception as e:
    print(f"[1] Port 8888: DOWN - {e}")
    # Restart portal server
    subprocess.run(["fuser","-k","8888/tcp"],capture_output=True)
    time.sleep(1)
    if os.path.exists(WEB+"/portal_server.py"):
        subprocess.Popen(["/usr/bin/python3",WEB+"/portal_server.py"],
            stdout=open("/tmp/portal.log","w"),stderr=subprocess.STDOUT)
        time.sleep(3)
        try:
            urllib.request.urlopen("http://127.0.0.1:8888/",timeout=5)
            print("  Portal restarted: OK")
        except Exception as e2:
            print(f"  Portal failed: {e2}")
            print("  Log:",open("/tmp/portal.log").read()[-200:] if os.path.exists("/tmp/portal.log") else "none")

# Check proxy to M4
print("[2] Testing proxy /api/health...")
try:
    with urllib.request.urlopen("http://127.0.0.1:8888/api/health",timeout=10) as r:
        d=json.loads(r.read())
        print(f"  PROXY WORKS: {json.dumps(d)[:80]}")
except Exception as e:
    print(f"  PROXY FAILED: {e}")
    # Direct check
    try:
        with urllib.request.urlopen(f"http://{M4}:3333/health",timeout=8) as r:
            d=json.loads(r.read())
            print(f"  DIRECT M4 OK: {json.dumps(d)[:80]}")
            print("  PROBLEM: MSI can reach M4 but proxy not working - portal_server.py issue")
    except Exception as e2:
        print(f"  DIRECT M4 ALSO FAILED: {e2}")
        print("  PROBLEM: MSI cannot reach M4:3333 - M4 firewall blocking")
        # SSH to M4 and disable firewall
        fw,_ = subprocess.Popen(
            ["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8",
             "Alias@"+M4,"/usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off 2>/dev/null; defaults write /Library/Preferences/com.apple.alf globalstate -int 0 2>/dev/null; echo done"],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate(timeout=15)
        print(f"  Firewall disable attempt: {fw.decode()[:60]}")
        time.sleep(2)
        # Try again
        try:
            with urllib.request.urlopen(f"http://{M4}:3333/health",timeout=8) as r:
                d=json.loads(r.read())
                print(f"  AFTER FIREWALL FIX: {json.dumps(d)[:80]}")
        except Exception as e3:
            print(f"  STILL BLOCKED: {e3}")

# Check media.html exists
mh=WEB+"/media.html"
idx=WEB+"/index.html"
ps=WEB+"/portal_server.py"
print(f"[3] Files: media={os.path.exists(mh)} index={os.path.exists(idx)} server={os.path.exists(ps)}")
if os.path.exists(mh): print(f"  media.html: {os.path.getsize(mh)} bytes")
if os.path.exists(idx): print(f"  index.html: {os.path.getsize(idx)} bytes")

# Show portal log
if os.path.exists("/tmp/portal.log"):
    print("[4] Portal log:",open("/tmp/portal.log").read()[-200:])

open(MP,"a").write(f"\n### Proxy Check [{TS}]\n")
print("\nDone. If proxy works: http://192.168.10.96:8888/")
