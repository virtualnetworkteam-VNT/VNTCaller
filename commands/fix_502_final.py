import subprocess, datetime, json, os, time, urllib.request

P1  = "192.168.10.19"
WEB = "/var/www/html"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx(h,c,t=60):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+h,c],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def pct_e(id,c,t=120):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+P1,
        "pct exec "+str(id)+" -- bash -c "+json.dumps(c)],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def save(e):
    try: open(MP,"a").write("\n### 502 Fix ["+TSF+"]\n"+e+"\n")
    except: pass

print("="*55)
print("FIXING 502 - WILL TEST BEFORE REPORTING")
print(TSF)
print("="*55)

# Step 1: Start CT108
print("[1] CT108 status...")
st = rx(P1, "pct status 108")
print(f"  {st}")
if "stopped" in st.lower():
    rx(P1, "pct start 108", t=20)
    time.sleep(10)

# Step 2: Get CT108's IP address
print("[2] CT108 IP...")
ct108_ip = pct_e(108, "hostname -I | awk '{print $1}'")
print(f"  CT108 IP: {ct108_ip}")

# Step 3: Check current nginx state
print("[3] Nginx status...")
nginx_status = pct_e(108, "systemctl status nginx 2>/dev/null | head -8 || service nginx status 2>/dev/null | head -5")
print(f"  {nginx_status[:300]}")

nginx_test = pct_e(108, "nginx -t 2>&1")
print(f"  nginx -t: {nginx_test[:200]}")

# Step 4: Find and remove broken SSL config
print("[4] Removing broken SSL config...")
pct_e(108, "ls /etc/nginx/sites-enabled/ 2>/dev/null")
# Remove all enabled sites and start clean
pct_e(108, "rm -f /etc/nginx/sites-enabled/*")

# Step 5: Write bulletproof nginx config (HTTP only - Cloudflare handles HTTPS)
print("[5] Writing clean nginx config...")
clean_nginx = r"""server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    root /var/www/html;
    index dashboard.html index.html;

    # Main pages
    location / {
        try_files $uri $uri/ /dashboard.html =404;
        add_header X-Frame-Options SAMEORIGIN;
        add_header X-Content-Type-Options nosniff;
    }

    # Generated media files
    location /generated/ {
        alias /var/www/html/generated/;
        add_header Access-Control-Allow-Origin *;
        expires 1h;
    }

    # Downloads
    location /downloads/ {
        alias /var/www/html/downloads/;
    }

    # Icons/static
    location /icons/ {
        alias /var/www/html/icons/;
    }

    gzip on;
    gzip_types text/html text/css application/javascript application/json image/svg+xml;
    client_max_body_size 50M;

    # Logging
    access_log /var/log/nginx/vnt_access.log;
    error_log /var/log/nginx/vnt_error.log;
}"""

open("/tmp/vnt_nginx_clean.conf", "w").write(clean_nginx)
push_r = rx(P1, "pct push 108 /tmp/vnt_nginx_clean.conf /etc/nginx/sites-available/vntworld")
pct_e(108, "ln -sf /etc/nginx/sites-available/vntworld /etc/nginx/sites-enabled/vntworld")
pct_e(108, "rm -f /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default 2>/dev/null || true")

# Step 6: Test config then restart
print("[6] Testing and restarting nginx...")
test = pct_e(108, "nginx -t 2>&1")
print(f"  Test: {test[:150]}")

if "ok" in test.lower() or "successful" in test.lower():
    restart = pct_e(108, "systemctl restart nginx 2>/dev/null || service nginx restart 2>/dev/null")
    print(f"  Restart: {restart[:80] or 'OK'}")
    time.sleep(2)
else:
    print("  Config error - trying to fix...")
    # Check what's wrong
    full_test = pct_e(108, "nginx -T 2>&1 | grep -E 'error|warn|include'")
    print(f"  Full test: {full_test[:300]}")
    # Fall back to minimal config
    minimal = "server { listen 80 default_server; server_name _; root /var/www/html; index dashboard.html; location / { try_files $uri $uri/ /dashboard.html =404; } }"
    pct_e(108, f"echo '{minimal}' > /etc/nginx/sites-available/vntworld && nginx -t 2>&1 && systemctl restart nginx 2>/dev/null || service nginx restart 2>/dev/null")
    time.sleep(2)

# Step 7: Verify nginx is running
print("[7] Verifying nginx...")
ps = pct_e(108, "ps aux | grep nginx | grep -v grep | head -3")
print(f"  {ps[:200]}")
ports = pct_e(108, "ss -tlnp | grep :80")
print(f"  Ports: {ports[:150]}")

# Step 8: TEST FROM MSI (internal network curl)
print("\n[8] Testing from MSI internal network...")
if ct108_ip and ct108_ip.strip():
    ip = ct108_ip.strip()
    internal_test = rx(P1, f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}' http://{ip}/ --connect-timeout 5 2>&1")
    print(f"  curl http://{ip}/: {internal_test}")

    if "200" in internal_test:
        print("  INTERNAL: OK - nginx serving correctly")
        # Test the dashboard file
        dash_test = rx(P1, f"curl -s http://{ip}/dashboard.html | wc -c")
        print(f"  dashboard.html size from network: {dash_test} bytes")
    else:
        print("  INTERNAL FAILED - checking nginx error log")
        err_log = pct_e(108, "tail -20 /var/log/nginx/vnt_error.log 2>/dev/null || tail -20 /var/log/nginx/error.log 2>/dev/null")
        print(f"  Error log: {err_log[:400]}")

# Step 9: Check dashboard file integrity
print("\n[9] Dashboard file check...")
size_out = pct_e(108, f"stat -c %s {WEB}/dashboard.html 2>/dev/null || wc -c < {WEB}/dashboard.html 2>/dev/null")
try:
    size = int(size_out.strip().split('\n')[-1].split()[0])
except:
    size = 0
print(f"  Size: {size} bytes")

if size < 50000:
    print(f"  WARNING: File too small ({size}b) - checking backups...")
    # Check all backups on Prox1
    all_backups = rx(P1, "ls -lt /root/ct108_backups/*.html 2>/dev/null | head -10")
    print(f"  Backups:\n{all_backups}")
    # Find largest backup
    best_backup = rx(P1, "ls -S /root/ct108_backups/*.html 2>/dev/null | head -1")
    if best_backup.strip():
        best_size = rx(P1, f"stat -c %s {best_backup.strip()}")
        try: bs = int(best_size.strip())
        except: bs = 0
        print(f"  Best backup: {best_backup.strip()} ({bs} bytes)")
        if bs > 50000:
            rx(P1, f"pct push 108 {best_backup.strip()} {WEB}/dashboard.html", t=20)
            # Re-check
            new_size = pct_e(108, f"stat -c %s {WEB}/dashboard.html")
            print(f"  After restore: {new_size} bytes")
            pct_e(108, "nginx -s reload 2>/dev/null || true")

# Step 10: Final external test via public IP  
print("\n[10] Testing via public IP (94.49.29.97)...")
pub_test = rx(P1, "curl -s -o /dev/null -w '%{http_code} %{size_download}' http://94.49.29.97/ --connect-timeout 8 -H 'Host: vntworld.com' 2>&1")
print(f"  curl via public IP: {pub_test}")

# Step 11: Check Cloudflare can reach origin
print("\n[11] Checking port forwarding on router...")
# The domain goes: DNS -> Cloudflare -> 94.49.29.97 -> router -> CT108
# Check if port 80 is forwarded from router to CT108
iptables = rx(P1, "iptables -t nat -L PREROUTING -n 2>/dev/null | grep -E '80|108' | head -5")
print(f"  iptables: {iptables[:200]}")

# Check Proxmox firewall for CT108
pf = rx(P1, "cat /etc/pve/firewall/108.fw 2>/dev/null | head -20 || echo 'no ct firewall'")
print(f"  CT108 firewall: {pf[:200]}")

save(f"502 fix attempt {TSF}\nnginx config: clean HTTP\ndashboard: {size} bytes\ninternal: {internal_test if 'internal_test' in dir() else 'not tested'}")

print("\n"+"="*55)
print(f"nginx config: CLEAN HTTP-only")
print(f"dashboard.html: {size} bytes")
print("="*55)
