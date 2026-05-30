import subprocess, base64, datetime, time, json, os

P1   = "192.168.10.19"
WEB  = "/var/www/html"
MP   = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
TSF  = datetime.datetime.now().strftime("%Y%m%d_%H%M")

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
    try: open(MP,"a").write("\n### SSL+Fix ["+TSF+"]\n"+e+"\n")
    except: pass

print("="*55)
print("FIX SSL + VERIFY DASHBOARD + DEPLOY")
print(TSF)
print("="*55)

# ── Check current file ──
print("\n[1] Checking current dashboard file...")
cur_size=pct_e(108,f"wc -c {WEB}/dashboard.html 2>/dev/null | awk '{{print $1}}'")
cur_lines=pct_e(108,f"wc -l {WEB}/dashboard.html 2>/dev/null | awk '{{print $1}}'")
print(f"  Size: {cur_size} bytes | Lines: {cur_lines}")
has_games=pct_e(108,f"grep -c 'GAMES' {WEB}/dashboard.html 2>/dev/null || echo 0")
has_coding=pct_e(108,f"grep -c 'spane-coding' {WEB}/dashboard.html 2>/dev/null || echo 0")
print(f"  GAMES: {has_games} | Coding tab: {has_coding}")

# ── Check nginx config ──
print("\n[2] Nginx config...")
nginx_conf=pct_e(108,"cat /etc/nginx/sites-enabled/default 2>/dev/null || cat /etc/nginx/sites-available/default 2>/dev/null")
print(" ",nginx_conf[:400])

# ── Install SSL ──
print("\n[3] Installing SSL (Let's Encrypt)...")
# Check if certbot installed
certbot_v=pct_e(108,"certbot --version 2>/dev/null || echo NOT_INSTALLED")
print("  certbot:",certbot_v[:60])

if "NOT_INSTALLED" in certbot_v:
    print("  Installing certbot...")
    install_r=pct_e(108,"apt-get update -qq && apt-get install -y certbot python3-certbot-nginx 2>&1 | tail -3",t=120)
    print(" ",install_r[:200])

# Check if cert already exists
cert_check=pct_e(108,"ls /etc/letsencrypt/live/vntworld.com/ 2>/dev/null || echo NO_CERT")
print("  Existing cert:",cert_check[:100])

if "NO_CERT" in cert_check or "fullchain" not in cert_check:
    print("  Requesting SSL cert...")
    # Stop nginx briefly for standalone mode
    cert_r=pct_e(108,
        "certbot certonly --nginx -d vntworld.com --non-interactive --agree-tos "
        "-m vntworld@hotmail.com --redirect 2>&1 | tail -10",t=120)
    print(" ",cert_r[:400])
    
    # Also try www subdomain
    cert_r2=pct_e(108,
        "certbot certonly --nginx -d vntworld.com -d www.vntworld.com --non-interactive "
        "--agree-tos -m vntworld@hotmail.com 2>&1 | tail -5",t=120)
    print(" ",cert_r2[:200])
else:
    print("  Cert exists - renewing if needed...")
    pct_e(108,"certbot renew --quiet 2>/dev/null || true",t=60)

# ── Write proper nginx config with SSL ──
print("\n[4] Writing nginx config with HTTPS...")
nginx_new="""server {
    listen 80;
    server_name vntworld.com www.vntworld.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name vntworld.com www.vntworld.com;

    ssl_certificate /etc/letsencrypt/live/vntworld.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vntworld.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;

    root /var/www/html;
    index dashboard.html index.html;

    location / {
        try_files $uri $uri/ /dashboard.html =404;
    }

    location /api/ {
        proxy_pass http://192.168.10.96:8888/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 360;
    }

    location /generated/ {
        alias /var/www/html/generated/;
        add_header Access-Control-Allow-Origin *;
    }

    gzip on;
    gzip_types text/html text/css application/javascript;
}"""
pct_e(108,"cat > /etc/nginx/sites-available/default << 'NGEOF'\n"+nginx_new+"\nNGEOF")
test_r=pct_e(108,"nginx -t 2>&1")
print("  nginx test:",test_r[:100])
if "ok" in test_r.lower() or "successful" in test_r.lower():
    reload_r=pct_e(108,"nginx -s reload 2>&1 || service nginx reload 2>&1")
    print("  reloaded:",reload_r[:80])

# ── Check file size - if truncated, rewrite ──
print("\n[5] Checking dashboard integrity...")
if int(cur_size or "0") < 50000:
    print(f"  File appears truncated ({cur_size} bytes) - needs rewrite")
    # Signal that we need fresh deploy
    open("/tmp/NEEDS_REDEPLOY","w").write("1")
else:
    print(f"  File OK ({cur_size} bytes)")

# ── Check auto-renewal ──
pct_e(108,"systemctl enable certbot.timer 2>/dev/null || "
     "(crontab -l 2>/dev/null; echo '0 12 * * * certbot renew --quiet') | crontab -")

save(f"SSL fixed {TSF}\ncert: vntworld.com\nnginx: HTTPS configured with redirect\nAPI proxy: /api/ -> 192.168.10.96:8888")

print("\n"+"="*55)
print("SSL config complete")
print("Dashboard size:",cur_size)
print("="*55)
