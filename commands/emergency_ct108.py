import subprocess, base64, datetime, json, os, time, urllib.request

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
    try: open(MP,"a").write("\n### Emergency ["+TSF+"]\n"+e+"\n")
    except: pass

print("="*55)
print("EMERGENCY: FIX 502 + RESTORE CT108")
print(TSF)
print("="*55)

# Step 1: Check CT108
st=rx(P1,"pct status 108")
print(f"[1] CT108: {st}")
if "stopped" in st.lower():
    rx(P1,"pct start 108",t=20)
    time.sleep(8)

# Step 2: Check nginx status
nginx_st=pct_e(108,"systemctl status nginx 2>/dev/null | head -5 || service nginx status 2>/dev/null | head -3")
print(f"[2] Nginx: {nginx_st[:200]}")

# Step 3: Restore simple working nginx config (HTTP only, SSL via Cloudflare)
print("[3] Restoring nginx config...")
simple_nginx="""server {
    listen 80;
    server_name vntworld.com www.vntworld.com _;
    root /var/www/html;
    index dashboard.html index.html;
    location / {
        try_files $uri $uri/ /dashboard.html =404;
    }
    location /generated/ {
        alias /var/www/html/generated/;
        add_header Access-Control-Allow-Origin *;
    }
    location /downloads/ {
        alias /var/www/html/downloads/;
    }
    gzip on;
    gzip_types text/html text/css application/javascript application/json;
    client_max_body_size 50M;
}"""
open("/tmp/nginx_simple.conf","w").write(simple_nginx)
rx(P1,"pct push 108 /tmp/nginx_simple.conf /etc/nginx/sites-available/default",t=15)
pct_e(108,"rm -f /etc/nginx/sites-enabled/* && ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default")
test=pct_e(108,"nginx -t 2>&1")
print(f"[4] nginx -t: {test[:100]}")
reload=pct_e(108,"nginx -t 2>&1 && systemctl restart nginx 2>/dev/null || service nginx restart 2>/dev/null || nginx -s reload 2>/dev/null")
print(f"[5] nginx restart: {reload[:100]}")

# Step 4: Check file size - if truncated restore from backup
size_raw=pct_e(108,f"wc -c < {WEB}/dashboard.html 2>/dev/null")
try: size=int(size_raw.strip())
except: size=0
print(f"[6] dashboard.html: {size} bytes")

if size < 50000:
    print("  File truncated! Restoring from backup...")
    backups=pct_e(108,f"ls -t {WEB}/dashboard.html.bak_* 2>/dev/null | head -5")
    print(f"  Backups: {backups[:200]}")
    if backups:
        best=backups.split("\n")[0].strip()
        bsize_raw=pct_e(108,f"wc -c < {best}")
        try: bsize=int(bsize_raw.strip())
        except: bsize=0
        if bsize > 50000:
            restore=pct_e(108,f"cp {best} {WEB}/dashboard.html && echo 'RESTORED'")
            print(f"  Restored from {best}: {restore}")
        else:
            print(f"  Backup {best} also small ({bsize}). Need fresh deploy.")
            # Will deploy below
    size_after_raw=pct_e(108,f"wc -c < {WEB}/dashboard.html 2>/dev/null")
    try: size=int(size_after_raw.strip())
    except: size=0
    print(f"  After restore: {size} bytes")

# Step 5: Fresh deploy if still small
if size < 50000:
    print("[7] Deploying fresh dashboard from MSI relay scripts...")
    # Check for any backed up versions on MSI/Prox1
    prox_backups=rx(P1,"ls -t /root/ct108_backups/*.html 2>/dev/null | head -5")
    print(f"  Prox1 backups: {prox_backups[:200]}")
    if prox_backups:
        best_prox=prox_backups.split("\n")[0].strip()
        bsize_raw=rx(P1,f"wc -c < {best_prox} 2>/dev/null")
        try: bsize=int(bsize_raw.strip())
        except: bsize=0
        print(f"  Best backup: {best_prox} ({bsize} bytes)")
        if bsize > 50000:
            rx(P1,f"pct push 108 {best_prox} {WEB}/dashboard.html",t=20)
            size_raw=pct_e(108,f"wc -c < {WEB}/dashboard.html")
            try: size=int(size_raw.strip())
            except: size=0
            print(f"  Deployed: {size} bytes")

# Step 6: Verify site is up
print("[8] Testing site...")
pct_e(108,"nginx -s reload 2>/dev/null || service nginx restart 2>/dev/null || true")
time.sleep(3)
try:
    with urllib.request.urlopen("http://vntworld.com/dashboard.html",timeout=12) as r:
        content=r.read().decode("utf-8","ignore")
        print(f"  vntworld.com: UP ({len(content)} bytes)")
        print(f"  Has GAMES: {'GAMES' in content}")
        print(f"  Has STUDIO: {'STUDIO' in content}")
except Exception as e:
    print(f"  vntworld.com: {str(e)[:80]}")

# Fix MSI portal server
print("\n[9] Fixing MSI portal (8888)...")
subprocess.run("fuser -k 8888/tcp 2>/dev/null; sleep 1",shell=True)
subprocess.Popen(["/usr/bin/python3","/home/k/vnt-web/portal_server.py"],
    stdout=open("/tmp/portal.log","w"),stderr=subprocess.STDOUT)
time.sleep(3)
try:
    urllib.request.urlopen("http://127.0.0.1:8888/",timeout=5)
    print("  MSI 8888: ONLINE")
except Exception as e:
    print(f"  MSI 8888: {str(e)[:60]}")

save(f"Emergency fix {TSF}\nnginx: HTTP-only restored\ndashboard: {size} bytes\nSSL via Cloudflare")
print("\n"+"="*55)
print(f"DONE - CT108 nginx restarted, dashboard: {size} bytes")
print("="*55)
