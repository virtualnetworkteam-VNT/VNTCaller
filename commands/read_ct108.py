import subprocess, datetime, json, os, urllib.request

P1  = "192.168.10.19"
P2  = "192.168.10.18"
GH  = open("/home/k/github-relay.py").read().split('GH = "')[1].split('"')[0]
REPO= "virtualnetworkteam-VNT/VNTCaller"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
TS  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def rx(host, cmd, t=30):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+host,cmd],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def pct_exec(host, ctid, cmd, t=30):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+host,
        "pct exec "+str(ctid)+" -- bash -c "+json.dumps(cmd)],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def gh_push(path, content, msg):
    import base64, urllib.request, json as _j
    headers={"Authorization":"Bearer "+GH,"Content-Type":"application/json",
             "Accept":"application/vnd.github.v3+json"}
    # Get existing SHA
    try:
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",
            headers=headers)
        with urllib.request.urlopen(req,timeout=10) as r:
            sha=_j.loads(r.read()).get("sha","")
    except: sha=""
    data={"message":msg,"content":base64.b64encode(content.encode()).decode()}
    if sha: data["sha"]=sha
    req2=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",
        data=_j.dumps(data).encode(),headers=headers,method="PUT")
    with urllib.request.urlopen(req2,timeout=15) as r:
        return "content" in _j.loads(r.read())

print("="*60)
print("READING CT108 + ALL PROXMOX INFRA")
print(TS)
print("="*60)

# ── PROX1: All containers ──
print("\n[PROX1] Containers...")
p1_ct = rx(P1,"pct list")
p1_vm = rx(P1,"qm list")
print(p1_ct)
print(p1_vm)

# ── CT108: Full web study ──
print("\n[CT108] Status...")
ct108_status = rx(P1,"pct status 108")
print(" ",ct108_status)

if "stopped" in ct108_status:
    print("  CT108 stopped - starting...")
    rx(P1,"pct start 108")
    import time; time.sleep(5)

print("[CT108] Processes...")
procs = pct_exec(P1,"108","ps aux | grep -v grep | grep -E 'nginx|apache|node|caddy|php'")
print(" ",procs[:300])

print("[CT108] Ports...")
ports = pct_exec(P1,"108","ss -tlnp")
print(" ",ports[:300])

print("[CT108] Web root...")
webroot_candidates = pct_exec(P1,"108",
    "ls /var/www/html/ 2>/dev/null && echo FOUND:/var/www/html || "
    "ls /var/www/ 2>/dev/null && echo FOUND:/var/www || "
    "ls /usr/share/nginx/html/ 2>/dev/null && echo FOUND:/usr/share/nginx/html || "
    "ls /opt/ 2>/dev/null | head -5")
print(" ",webroot_candidates[:400])

# Determine web root
web_root = "/var/www/html"
if "FOUND:/var/www" in webroot_candidates and "FOUND:/var/www/html" not in webroot_candidates:
    web_root = "/var/www"
print(f"  Using web root: {web_root}")

print("[CT108] File list...")
files = pct_exec(P1,"108",f"ls -la {web_root}/")
print(" ",files[:500])

print("[CT108] Reading HTML files...")
html_files = pct_exec(P1,"108",f"find {web_root} -name '*.html' -o -name '*.js' -o -name '*.css' 2>/dev/null | head -20")
print(" ",html_files[:400])

print("[CT108] Reading main HTML...")
main_html = pct_exec(P1,"108",f"cat {web_root}/index.html 2>/dev/null || cat {web_root}/dashboard.html 2>/dev/null")
print(" PREVIEW:", main_html[:300])

print("[CT108] Nginx config...")
nginx_conf = pct_exec(P1,"108",
    "cat /etc/nginx/sites-enabled/default 2>/dev/null || "
    "cat /etc/nginx/sites-available/default 2>/dev/null || "
    "cat /etc/nginx/conf.d/default.conf 2>/dev/null || "
    "cat /etc/nginx/nginx.conf 2>/dev/null | head -40")
print(" ",nginx_conf[:400])

print("[CT108] All HTML files sizes...")
html_sizes = pct_exec(P1,"108",f"find {web_root} -name '*.html' | xargs ls -la 2>/dev/null")
print(" ",html_sizes[:400])

# Read FULL content of dashboard/media html
print("[CT108] Full dashboard.html...")
dash_html = pct_exec(P1,"108",f"cat {web_root}/dashboard.html 2>/dev/null")
media_html = pct_exec(P1,"108",f"cat {web_root}/media.html 2>/dev/null")
print(f"  dashboard.html: {len(dash_html)} chars")
print(f"  media.html: {len(media_html)} chars")

# ── PROX2: Omada ──
print("\n[PROX2] Containers...")
p2_ct = rx(P2,"pct list")
p2_vm = rx(P2,"qm list")
print(p2_ct)
print(p2_vm)

p2_ct100 = rx(P2,"pct status 100 2>/dev/null || qm status 100 2>/dev/null")
p2_ct101 = rx(P2,"pct status 101 2>/dev/null || qm status 101 2>/dev/null")
print(f"  ID 100: {p2_ct100}")
print(f"  ID 101: {p2_ct101}")

# ── BUILD INFRASTRUCTURE REPORT ──
infra = {
    "updated": TS,
    "prox1": {
        "ip": P1,
        "containers": p1_ct,
        "vms": p1_vm,
    },
    "ct108": {
        "id": 108,
        "name": "vnt-web",
        "host": P1,
        "web_root": web_root,
        "processes": procs[:200],
        "ports": ports[:200],
        "nginx_config": nginx_conf[:500],
        "files": html_files[:400],
        "dashboard_html_size": len(dash_html),
        "media_html_size": len(media_html),
        "dashboard_html_preview": dash_html[:2000],
    },
    "prox2": {
        "ip": P2,
        "containers": p2_ct,
        "vms": p2_vm,
        "omada_active": "100",
        "omada_backup": "101 (stopped)",
    },
    "key_facts": [
        "CT108 is the PRODUCTION web server - vntworld.com",
        f"CT108 web root: {web_root}",
        "DO NOT write to /home/k/vnt-web - that is NOT the production web",
        "To update website: pct exec 108 -- bash -c 'cat > /var/www/html/file.html'",
        "Prox2 Omada: VM100 running (active), CT101 stopped (backup)",
    ]
}

# Save to GitHub so Claude can read it
gh_push("infra/ct108_study.json",
    json.dumps(infra, indent=2),
    "CT108 study results")

# Save to vnt_config
try:
    cfg = json.load(open(CFG))
except: cfg = {}
cfg["infra"] = infra
cfg["ct108_web_root"] = web_root
cfg["production_web"] = "CT108 on Prox1 192.168.10.19"
json.dump(cfg, open(CFG,"w"), indent=2)

# Also save full HTML to GitHub for Claude to read
if dash_html:
    gh_push("infra/ct108_dashboard.html", dash_html, "CT108 dashboard HTML")
if media_html:
    gh_push("infra/ct108_media.html", media_html, "CT108 media HTML")

print("\n"+"="*60)
print("CT108 study saved to GitHub: infra/ct108_study.json")
print("Dashboard HTML saved: infra/ct108_dashboard.html")
print(f"Web root: {web_root}")
print("="*60)
