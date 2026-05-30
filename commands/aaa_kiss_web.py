import subprocess, datetime, json, time, urllib.request, os

P1   = "192.168.10.19"
CT   = "192.168.10.13"   # CT108 IP confirmed
WEB  = "/var/www/html"
MP   = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
TSF  = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx(h, c, t=60):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+h, c],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def pct_e(ctid, c, t=60):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+P1,
        f"pct exec {ctid} -- bash -c "+json.dumps(c)],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def save(e):
    try: open(MP,"a").write("\n### KISS ["+TSF+"]\n"+e+"\n")
    except: pass

def test_site(label):
    """Test from Prox1 to CT108 internal, then external"""
    # Internal test via Prox1 -> CT108
    internal = rx(P1, f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}b' http://{CT}/ --connect-timeout 5")
    # External test via public IP
    external = rx(P1, f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}b' http://vntworld.com/ --connect-timeout 8 -H 'Host: vntworld.com'")
    print(f"  [{label}] CT108 internal: {internal} | vntworld.com: {external}")
    return "200" in internal, "200" in external

print("="*55)
print("KISS: KILL NGINX, USE PYTHON HTTP SERVER")
print(TSF)
print("="*55)

# ── Step 1: Kill EVERYTHING on port 80 in CT108 ──
print("\n[1] Killing nginx and anything on port 80...")
pct_e(108, "systemctl stop nginx 2>/dev/null; service nginx stop 2>/dev/null; pkill -9 nginx 2>/dev/null; pkill -9 python3 2>/dev/null; fuser -k 80/tcp 2>/dev/null; sleep 2; echo KILLED")
time.sleep(2)

# Verify nothing running on port 80
check = pct_e(108, "ss -tlnp | grep :80 || echo 'port 80 clear'")
print(f"  Port 80: {check}")

# ── Step 2: Confirm web files exist ──
print("\n[2] Checking web files...")
files = pct_e(108, f"ls -la {WEB}/ | head -20")
print(f"  {files[:400]}")

size_out = pct_e(108, f"stat -c %s {WEB}/dashboard.html 2>/dev/null || echo 0")
try: size = int(size_out.strip().split('\n')[-1].split()[0])
except: size = 0
print(f"  dashboard.html: {size} bytes")

# Restore from backup if needed
if size < 50000:
    print(f"  File truncated ({size}b) - restoring from Prox1 backup...")
    best = rx(P1, "ls -S /root/ct108_backups/*.html 2>/dev/null | head -1").strip()
    if best:
        bs_out = rx(P1, f"stat -c %s {best} 2>/dev/null || echo 0")
        try: bs = int(bs_out.strip().split()[0])
        except: bs = 0
        print(f"  Best backup: {best} ({bs}b)")
        if bs > 50000:
            rx(P1, f"pct push 108 {best} {WEB}/dashboard.html", t=20)
            time.sleep(1)

# ── Step 3: Start Python HTTP server on port 80 (KISS) ──
print("\n[3] Starting Python HTTP server on port 80...")
pct_e(108,
    f"cd {WEB} && nohup python3 -m http.server 80 "
    f"--bind 0.0.0.0 > /tmp/webserver.log 2>&1 & "
    f"echo STARTED", t=10)
time.sleep(3)

# Verify it's running
ps = pct_e(108, "ps aux | grep 'http.server' | grep -v grep")
port = pct_e(108, "ss -tlnp | grep :80")
print(f"  Process: {ps[:150]}")
print(f"  Port 80: {port[:100]}")

# ── Step 4: Test immediately ──
print("\n[4] Testing from Prox1 → CT108...")
ok_internal, ok_external = test_site("POST-START")

if not ok_internal:
    print("  Internal failed - checking log...")
    log = pct_e(108, "tail -10 /tmp/webserver.log")
    print(f"  Log: {log[:200]}")
    # Try port 8080 then proxy
    print("  Trying port 8080...")
    pct_e(108, f"fuser -k 80/tcp 2>/dev/null; cd {WEB} && nohup python3 -m http.server 8080 --bind 0.0.0.0 > /tmp/webserver.log 2>&1 &", t=10)
    time.sleep(2)
    internal8080 = rx(P1, f"curl -s -o /dev/null -w '%{{http_code}}' http://{CT}:8080/ --connect-timeout 5")
    print(f"  Port 8080: {internal8080}")

# ── Step 5: Install as systemd service so it never dies ──
print("\n[5] Installing auto-restart service...")
service = f"""[Unit]
Description=VNT Web Server
After=network.target

[Service]
Type=simple
WorkingDirectory={WEB}
ExecStart=/usr/bin/python3 -m http.server 80 --bind 0.0.0.0
Restart=always
RestartSec=3
StandardOutput=append:/tmp/webserver.log
StandardError=append:/tmp/webserver.log

[Install]
WantedBy=multi-user.target"""

open("/tmp/vnt-web.service","w").write(service)
rx(P1, "pct push 108 /tmp/vnt-web.service /etc/systemd/system/vnt-web.service", t=10)
pct_e(108, "systemctl daemon-reload && systemctl enable vnt-web && systemctl restart vnt-web 2>/dev/null", t=15)
time.sleep(3)

svc_status = pct_e(108, "systemctl status vnt-web 2>/dev/null | head -8")
print(f"  Service: {svc_status[:200]}")

# ── Step 6: Final comprehensive test ──
print("\n[6] FINAL TEST...")
ok_internal, ok_external = test_site("FINAL")

# Also test specific pages
pages = ["dashboard.html","app.html"]
for page in pages:
    result = rx(P1, f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}b' http://{CT}/{page} --connect-timeout 5")
    print(f"  {page}: {result}")

# Test app.html exists
app_exists = pct_e(108, "test -f /var/www/html/app.html && echo EXISTS || echo MISSING")
print(f"  app.html: {app_exists}")

# Deploy app.html if missing
if "MISSING" in app_exists:
    if os.path.exists("/home/k/vnt-web/app.html"):
        rx(P1, "pct push 108 /home/k/vnt-web/app.html /var/www/html/app.html", t=10)
        print("  app.html: deployed from MSI")

save(f"KISS web server {TSF}\npython3 -m http.server 80\nCT108: {CT}\ninternal: {ok_internal}\nexternal: {ok_external}")

print("\n"+"="*55)
if ok_internal:
    print("CT108 web server: RUNNING (Python HTTP)")
    if ok_external:
        print("vntworld.com: UP - visit to confirm")
    else:
        print("vntworld.com: check Cloudflare/router port forward to 192.168.10.13:80")
else:
    print("CT108: still not responding - check CT108 network config")
print(f"CT108 IP: {CT}")
print(f"Dashboard: {size} bytes")
print("="*55)
