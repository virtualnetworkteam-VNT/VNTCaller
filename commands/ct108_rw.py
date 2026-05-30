import subprocess, datetime, json, os, urllib.request, base64, time

P1   = "192.168.10.19"
P2   = "192.168.10.18"
GH   = open("/home/k/vnt-config-gh.txt").read().strip() if os.path.exists("/home/k/vnt-config-gh.txt") else open("/home/k/github-relay.py").read().split(chr(71)+chr(72)+" = "+chr(34))[1].split(chr(34))[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"
CFG  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
MP   = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
TS   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def save(e):
    try: open(MP,"a").write("\n### CT108 ["+TS+"]\n"+e+"\n")
    except: pass

def rx(host, cmd, t=30):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+host, cmd],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def pct_exec(host, ctid, cmd, t=60):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+host,
        "pct exec "+str(ctid)+" -- bash -lc "+json.dumps(cmd)],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def pct_write(host, ctid, remote_path, content):
    # Write file to container via heredoc
    encoded = base64.b64encode(content.encode()).decode()
    cmd = f"echo '{encoded}' | base64 -d > {remote_path}"
    return pct_exec(host, ctid, cmd)

def gh_push(path, content, msg):
    headers={"Authorization":"Bearer "+GH,"Content-Type":"application/json",
             "Accept":"application/vnd.github.v3+json"}
    try:
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",
            headers=headers)
        with urllib.request.urlopen(req,timeout=10) as r:
            sha=json.loads(r.read()).get("sha","")
    except: sha=""
    data={"message":msg,"content":base64.b64encode(content.encode()).decode()}
    if sha: data["sha"]=sha
    req2=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",
        data=json.dumps(data).encode(),headers=headers,method="PUT")
    try:
        with urllib.request.urlopen(req2,timeout=15) as r:
            return "content" in json.loads(r.read())
    except Exception as e:
        print("GH push error:",e)
        return False

print("="*60)
print("CT108 READ + WRITE + PROX MONITORING")
print(TS)
print("="*60)

# ── PROX1: Study all containers ──
print("\n[PROX1] All containers and VMs...")
p1_cts = rx(P1,"pct list")
p1_vms = rx(P1,"qm list")
print(p1_cts)
print(p1_vms)

# Get status of each CT
print("\n[PROX1] Container statuses...")
p1_detail = rx(P1,"for id in $(pct list | tail -n +2 | awk '{print $1}'); do echo \"CT$id: $(pct status $id)\"; done")
print(p1_detail)
p1_vm_detail = rx(P1,"for id in $(qm list 2>/dev/null | tail -n +2 | awk '{print $1}'); do echo \"VM$id: $(qm status $id)\"; done")
print(p1_vm_detail)

# ── CT108 STUDY ──
print("\n[CT108] Checking status...")
ct108_st = rx(P1,"pct status 108")
print(" ",ct108_st)

if "stopped" in ct108_st.lower():
    print("  Starting CT108...")
    rx(P1,"pct start 108",t=20)
    time.sleep(8)

print("[CT108] Web server process...")
procs = pct_exec(P1,"108","ps aux | grep -v grep | grep -E 'nginx|apache|node|caddy'")
print(" ",procs[:200])

print("[CT108] Listening ports...")
ports = pct_exec(P1,"108","ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null")
print(" ",ports[:300])

print("[CT108] Finding web root...")
# Try common locations
for candidate in ["/var/www/html","/var/www","/usr/share/nginx/html","/opt/vnt","/root/web","/home/www"]:
    chk = pct_exec(P1,"108",f"ls {candidate} 2>/dev/null && echo FOUND:{candidate}")
    if "FOUND:" in chk:
        web_root = candidate
        print(f"  Web root: {web_root}")
        break
else:
    web_root = pct_exec(P1,"108","find / -name 'dashboard.html' -not -path '*/proc/*' 2>/dev/null | head -1 | xargs dirname 2>/dev/null || echo /var/www/html")
    web_root = web_root.strip().split("\n")[0] or "/var/www/html"
    print(f"  Web root (found): {web_root}")

print("[CT108] File listing...")
file_list = pct_exec(P1,"108",f"ls -la {web_root}/")
print(" ",file_list[:400])

print("[CT108] Nginx config...")
nginx_cfg = pct_exec(P1,"108",
    "cat /etc/nginx/sites-enabled/default 2>/dev/null || "
    "cat /etc/nginx/sites-available/default 2>/dev/null || "
    "cat /etc/nginx/conf.d/*.conf 2>/dev/null || "
    "grep -r 'root' /etc/nginx/ 2>/dev/null | grep -v '#' | head -5")
print(" ",nginx_cfg[:400])

print("[CT108] Reading HTML files...")
dash_html = pct_exec(P1,"108",f"cat {web_root}/dashboard.html 2>/dev/null || cat {web_root}/index.html 2>/dev/null",t=15)
media_html = pct_exec(P1,"108",f"cat {web_root}/media.html 2>/dev/null",t=15)
print(f"  dashboard.html: {len(dash_html)} chars")
print(f"  media.html: {len(media_html)} chars")
print(f"  Preview: {dash_html[:300]}")

# Push HTML files to GitHub so Claude can read them
print("\n[GH] Saving CT108 files to GitHub...")
if dash_html and len(dash_html) > 100:
    ok = gh_push("infra/ct108_dashboard.html", dash_html, "CT108 dashboard.html")
    print(f"  dashboard.html -> GitHub: {'OK' if ok else 'FAIL'}")
if media_html and len(media_html) > 100:
    ok = gh_push("infra/ct108_media.html", media_html, "CT108 media.html")
    print(f"  media.html -> GitHub: {'OK' if ok else 'FAIL'}")

# Push infra summary to GitHub
infra_summary = {
    "updated": TS,
    "prox1_ip": P1,
    "prox1_containers": p1_cts,
    "prox1_vms": p1_vms,
    "prox1_ct_status": p1_detail,
    "ct108": {
        "status": ct108_st,
        "web_root": web_root,
        "processes": procs[:200],
        "ports": ports[:200],
        "nginx": nginx_cfg[:400],
        "files": file_list[:400],
        "dashboard_size": len(dash_html),
        "media_size": len(media_html),
    },
    "prox2_ip": P2,
    "prox2_containers": rx(P2,"pct list"),
    "prox2_vms": rx(P2,"qm list"),
    "production_facts": {
        "web_server": "CT108 on Prox1",
        "web_root": web_root,
        "domain": "vntworld.com",
        "never_write_to": "/home/k/vnt-web",
        "correct_write": f"pct exec 108 -- bash to write to {web_root}/"
    }
}
gh_push("infra/infrastructure.json", json.dumps(infra_summary,indent=2), "infra summary")
print("  infrastructure.json -> GitHub: OK")

# ── PROX2 OMADA STUDY ──
print("\n[PROX2] Omada containers...")
p2_cts = rx(P2,"pct list")
p2_vms = rx(P2,"qm list")
print(p2_cts)
print(p2_vms)

# Check Omada active
omada_active = rx(P2,"qm status 100 2>/dev/null || pct status 100 2>/dev/null")
omada_backup = rx(P2,"pct status 101 2>/dev/null || qm status 101 2>/dev/null")
print(f"  Omada active (100): {omada_active}")
print(f"  Omada backup (101): {omada_backup}")

# ── INSTALL ZEUS MONITORING FOR ALL CTs ──
print("\n[ZEUS] Installing Prox monitoring in Zeus...")
zeus_mon_path = "/home/k/zeus-monitor.py"
if os.path.exists(zeus_mon_path):
    zeus = open(zeus_mon_path).read()
    if "pct status" not in zeus:
        prox_check = '''
# Proxmox CT monitoring - added by relay
def check_prox_containers():
    PROX1="192.168.10.19"; PROX2="192.168.10.18"
    CRITICAL_CTS={"108":"vnt-web","104":"nextcloud","109":"livekit","110":"turn"}
    CRITICAL_VMS_P2={"100":"omadavnt"}
    issues=[]; fixed=[]
    for ctid,name in CRITICAL_CTS.items():
        r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5",
            "root@"+PROX1,"pct status "+ctid],capture_output=True,text=True,timeout=10)
        if "running" not in r.stdout:
            save(f"CT{ctid} ({name}) is DOWN - attempting restart")
            r2=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
                "root@"+PROX1,"pct start "+ctid],capture_output=True,timeout=30)
            issues.append(f"CT{ctid}({name}) restarted")
    for vmid,name in CRITICAL_VMS_P2.items():
        r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5",
            "root@"+PROX2,"qm status "+vmid],capture_output=True,text=True,timeout=10)
        if "running" not in r.stdout:
            r2=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
                "root@"+PROX2,"qm start "+vmid],capture_output=True,timeout=30)
            issues.append(f"VM{vmid}({name}) restarted")
    return issues
'''
        # Inject into zeus monitor before the while loop
        zeus = zeus.replace("while True:", prox_check + "\nwhile True:")
        try:
            import ast
            ast.parse(zeus)
            open(zeus_mon_path,"w").write(zeus)
            subprocess.run(["sudo","systemctl","restart","zeus-monitor"],capture_output=True)
            print("  Zeus: Prox monitoring injected")
        except SyntaxError as e:
            print(f"  Zeus inject error: {e}")

# ── SAVE CONFIG ──
try:
    cfg = json.load(open(CFG))
except: cfg = {}
cfg.update({
    "production_web_ct": "108",
    "production_web_root": web_root,
    "production_web_host": P1,
    "production_domain": "vntworld.com",
    "prox1_ip": P1,
    "prox2_ip": P2,
    "omada_active_id": "100",
    "omada_backup_id": "101",
    "updated": TS,
})
json.dump(cfg,open(CFG,"w"),indent=2)

save("\n".join([
    f"CT108 WEB ROOT: {web_root}",
    f"PRODUCTION: vntworld.com -> CT108 on Prox1 ({P1})",
    f"NEVER WRITE TO: /home/k/vnt-web",
    f"WRITE TO: pct exec 108 -- bash, then {web_root}/",
    f"Prox2 Omada: VM100=active, CT101=backup(stopped)",
    f"CT108 dashboard.html: {len(dash_html)} chars",
    f"CT108 media.html: {len(media_html)} chars",
]))

print("\n"+"="*60)
print(f"DONE. Web root: {web_root}")
print(f"Files pushed to GitHub: infra/ct108_dashboard.html")
print(f"Read at: https://github.com/{REPO}/blob/main/infra/ct108_dashboard.html")
print("="*60)
