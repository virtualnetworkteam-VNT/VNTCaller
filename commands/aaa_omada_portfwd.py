import subprocess, datetime, json, time, urllib.request, urllib.parse, ssl

P1      = "192.168.10.19"
CT108_IP= "192.168.10.13"
OMADA   = "https://192.168.10.5:8043"
OMADA_ID= "bb85be7dce4d2b3ce703342b3ea86982"
SITE_ID = "698f80cfdc0762154b08c2ed"
USER    = "vntworld@aol.com"
PASSWD  = "Vnt^Ai%w8rLd_@L"
MP      = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
P1_PASS = "68116899"
TSF     = datetime.datetime.now().strftime("%Y%m%d_%H%M")

# SSL context - ignore cert for internal controller
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def save(e):
    try: open(MP,"a").write("\n### PortFwd ["+TSF+"]\n"+e+"\n")
    except: pass

def rx(h,c,t=30):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+h,c],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def pct_bg(ctid,c):
    """Run command in background - don't wait"""
    subprocess.Popen(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+P1,
        f"pct exec {ctid} -- bash -c "+json.dumps(c)],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def omada_post(path, data, token=None, cookies=None):
    body = json.dumps(data).encode()
    url  = f"{OMADA}/{OMADA_ID}/api/v2/{path}"
    headers = {"Content-Type":"application/json"}
    if token:   headers["Csrf-Token"] = token
    if cookies: headers["Cookie"]     = cookies
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read()), r.headers.get("Set-Cookie","")

def omada_get(path, token=None, cookies=None):
    url = f"{OMADA}/{OMADA_ID}/api/v2/{path}"
    headers = {}
    if token:   headers["Csrf-Token"] = token
    if cookies: headers["Cookie"]     = cookies
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read()), r.headers.get("Set-Cookie","")

print("="*55)
print("OMADA PORT FORWARDING + CT108 FIX")
print(TSF)
print("="*55)

# ── Step 1: Fix CT108 web server (background, no timeout) ──
print("\n[1] Starting Python HTTP server in CT108 (background)...")
# Kill everything first
pct_bg(108, "systemctl stop nginx 2>/dev/null; pkill -9 nginx 2>/dev/null; pkill -9 'http.server' 2>/dev/null; fuser -k 80/tcp 2>/dev/null; sleep 2")
time.sleep(4)
# Start Python server - background, no wait
pct_bg(108, f"cd /var/www/html && nohup python3 -m http.server 80 --bind 0.0.0.0 >> /tmp/web.log 2>&1 &")
print("  Started (background)")
time.sleep(4)

# Test internal
internal = rx(P1, f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}b' http://{CT108_IP}/ --connect-timeout 6")
print(f"  Internal ({CT108_IP}): {internal}")

# ── Step 2: Restore dashboard.html ──
print("\n[2] Restoring dashboard.html...")
best = rx(P1,"ls -S /root/ct108_backups/*.html 2>/dev/null | head -1").strip()
if best:
    bs_out=rx(P1,f"stat -c %s {best} 2>/dev/null || wc -c < {best} 2>/dev/null")
    try: bs=int(bs_out.strip().split('\n')[-1].split()[0])
    except: bs=0
    print(f"  Best backup: {best} ({bs} bytes)")
    if bs > 50000:
        rx(P1,f"pct push 108 {best} /var/www/html/dashboard.html",t=20)
        sz2=rx(P1,f"pct exec 108 -- wc -c /var/www/html/dashboard.html 2>/dev/null")
        print(f"  Restored: {sz2[:60]}")
    else:
        print(f"  Backup too small ({bs}b) - all backups corrupted")

# ── Step 3: Omada login ──
print("\n[3] Logging into Omada controller...")
token = ""
cookies = ""
try:
    login_data = {"username": USER, "password": PASSWD}
    resp, ck = omada_post("login", login_data)
    print(f"  Login: {resp.get('errorCode',resp.get('msg','?'))}")
    if resp.get("errorCode") == 0:
        token   = resp["result"]["token"]
        cookies = ck
        print(f"  Token: {token[:20]}...")
    else:
        print(f"  Login failed: {resp}")
except Exception as e:
    print(f"  Omada error: {str(e)[:100]}")

# ── Step 4: Check existing port forwarding ──
if token:
    print("\n[4] Checking existing port forwarding rules...")
    try:
        fwd_resp, _ = omada_get(
            f"sites/{SITE_ID}/setting/firewall/natRules?pageSize=50&currentPage=1",
            token=token, cookies=cookies)
        rules = fwd_resp.get("result",{}).get("data",[])
        print(f"  Existing rules: {len(rules)}")
        for r in rules:
            print(f"  - {r.get('name','?')}: {r.get('protocol','?')} ext:{r.get('exPort','?')} -> {r.get('inIp','?')}:{r.get('inPort','?')}")
    except Exception as e:
        print(f"  Error getting rules: {str(e)[:100]}")
        rules = []

    # ── Step 5: Add port forwarding rules ──
    print("\n[5] Adding port forwarding rules...")

    new_rules = [
        {
            "name": "VNT-Web-HTTP",
            "protocol": "TCP",
            "exPortType": "port",
            "exPort": "80",
            "inIp": CT108_IP,
            "inPort": "80",
            "enable": True,
            "status": True,
        },
        {
            "name": "VNT-Web-HTTPS",
            "protocol": "TCP",
            "exPortType": "port",
            "exPort": "443",
            "inIp": CT108_IP,
            "inPort": "80",
            "enable": True,
            "status": True,
        },
    ]

    for rule in new_rules:
        # Check if already exists
        exists = any(r.get("name")==rule["name"] for r in rules)
        if exists:
            print(f"  Rule {rule['name']}: already exists")
            continue
        try:
            add_resp, _ = omada_post(
                f"sites/{SITE_ID}/setting/firewall/natRules",
                rule, token=token, cookies=cookies)
            ec = add_resp.get("errorCode", -1)
            print(f"  Add {rule['name']}: {'OK' if ec==0 else 'FAIL: '+str(add_resp)[:80]}")
        except Exception as e:
            print(f"  Add {rule['name']} error: {str(e)[:100]}")
    
    time.sleep(3)

# ── Step 6: Test public access ──
print("\n[6] Testing public access...")
time.sleep(5)
pub = rx(P1, "curl -s -o /dev/null -w '%{http_code} %{size_download}b' http://94.49.29.97/ -H 'Host: vntworld.com' --connect-timeout 10")
print(f"  Public IP: {pub}")

vnt = rx(P1, "curl -s -o /dev/null -w '%{http_code} %{size_download}b' http://vntworld.com/ --connect-timeout 10 2>&1")
print(f"  vntworld.com: {vnt}")

dashboard = rx(P1, f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}b' http://vntworld.com/dashboard.html --connect-timeout 10")
print(f"  dashboard.html: {dashboard}")

app_test = rx(P1, f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}b' http://vntworld.com/app.html --connect-timeout 10")
print(f"  app.html: {app_test}")

ok = "200" in vnt or "200" in pub
save(f"Port fwd {TSF}\nomada: port 80+443 -> {CT108_IP}:80\nresult: {ok}\nvntworld: {vnt}\ndashboard: {dashboard}")

print("\n"+"="*55)
if ok:
    print("SITE IS UP: vntworld.com is responding")
    print("Visit: http://vntworld.com/dashboard.html")
    print("App:   http://vntworld.com/app.html")
else:
    print("Still not responding externally")
    print(f"Internal CT108 ({CT108_IP}): {internal}")
    print("Check: Omada port forwarding in router settings")
    print(f"  Add: TCP 80 -> {CT108_IP}:80")
    print(f"  Add: TCP 443 -> {CT108_IP}:80")
print("="*55)
