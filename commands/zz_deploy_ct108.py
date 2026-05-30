import subprocess, os, base64, datetime, urllib.request, json, time

P1  = "192.168.10.19"
WEB = "/var/www/html"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx(host, cmd, t=30):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+host, cmd],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def pct_e(ctid, cmd, t=60):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+P1,
        "pct exec "+str(ctid)+" -- bash -c "+json.dumps(cmd)],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def save(e):
    try: open(MP,"a").write("\n### CT108 Deploy ["+TSF+"]\n"+e+"\n")
    except: pass

print("="*55)
print("DEPLOY CT108 DASHBOARD v2")
print(TSF)
print("="*55)

# Check CT108
print("\n[1] CT108 status...")
st = rx(P1,"pct status 108")
print(" ",st)
if "stopped" in st.lower():
    print("  Starting CT108...")
    rx(P1,"pct start 108",t=20)
    time.sleep(8)

# Read new HTML from vnt_config
cfg_path = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
try:
    cfg = json.load(open(cfg_path))
    html_b64 = cfg.get("ct108_pending_html","")
except: html_b64 = ""

if not html_b64:
    print("ERROR: No pending HTML in config - aborting")
    exit(1)

html_data = base64.b64decode(html_b64)
print(f"\n[2] HTML ready: {len(html_data)} bytes")

# BACKUP FIRST
print("\n[3] Backing up current dashboard.html...")
bk = pct_e(108, f"cp {WEB}/dashboard.html {WEB}/dashboard.html.bak_{TSF} && echo OK")
print(" ",bk)
# Also backup to Prox1
rx(P1, f"mkdir -p /root/ct108_backups")
rx(P1, f"pct pull 108 {WEB}/dashboard.html /root/ct108_backups/dashboard_{TSF}.html",t=20)
print("  Prox1 backup: /root/ct108_backups/dashboard_"+TSF+".html")

# Write new file
print("\n[4] Writing new dashboard.html...")
# Write to temp file on MSI, then push to CT108
open("/tmp/new_dashboard.html","wb").write(html_data)
# Use pct push
push_r = rx(P1, f"pct push 108 /tmp/new_dashboard.html {WEB}/dashboard.html",t=30)
print("  pct push:",push_r or "OK")

# If pct push not available, use base64 method
if "error" in push_r.lower() or "unknown" in push_r.lower():
    print("  pct push failed, using base64 method...")
    encoded = base64.b64encode(html_data).decode()
    # Write in chunks
    chunk=8000
    chunks=[encoded[i:i+chunk] for i in range(0,len(encoded),chunk)]
    pct_e(108,f"echo '' > /tmp/d_b64.txt")
    for c in chunks:
        pct_e(108,f"printf '%s' '{c}' >> /tmp/d_b64.txt")
    decode_r = pct_e(108,
        f"base64 -d /tmp/d_b64.txt > {WEB}/dashboard.html && "
        f"echo 'OK:$(wc -c < {WEB}/dashboard.html)bytes'")
    print("  base64 decode:",decode_r)

# Verify
verify = pct_e(108,f"wc -c {WEB}/dashboard.html && head -3 {WEB}/dashboard.html")
print("\n[5] Verify:",verify[:200])

# Check live site
print("\n[6] Checking vntworld.com...")
try:
    req=urllib.request.Request("https://vntworld.com/dashboard.html",
        headers={"User-Agent":"VNT/1.0"})
    with urllib.request.urlopen(req,timeout=12) as r:
        content=r.read().decode("utf-8","ignore")
        has_games="GAMES" in content
        has_apps="APPS" in content
        has_desk="DESKTOP" in content
        print(f"  Site accessible: YES")
        print(f"  Has GAMES: {has_games}")
        print(f"  Has APPS: {has_apps}")
        print(f"  Has DESKTOP: {has_desk}")
        if has_games and has_apps:
            print("  DEPLOYMENT SUCCESSFUL")
        else:
            print("  Content check failed - may need reload")
except Exception as e:
    print(f"  Site check: {str(e)[:80]}")

save("\n".join([
    "CT108 dashboard v2 deployed",
    "Backup: "+WEB+"/dashboard.html.bak_"+TSF,
    "Prox1 backup: /root/ct108_backups/dashboard_"+TSF+".html",
    "ROLLBACK: pct exec 108 -- bash -c 'cp "+WEB+"/dashboard.html.bak_"+TSF+" "+WEB+"/dashboard.html'",
]))

print("\n"+"="*55)
print("DONE")
print(f"Rollback: pct exec 108 -- bash -c 'cp {WEB}/dashboard.html.bak_{TSF} {WEB}/dashboard.html'")
print("="*55)
