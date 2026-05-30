import subprocess, datetime, json, os, urllib.request, base64, time

P1   = "192.168.10.19"
P2   = "192.168.10.18"
GH   = open("/home/k/vnt-config-gh.txt").read().strip()
REPO = "virtualnetworkteam-VNT/VNTCaller"
CFG  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
MP   = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
TS   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
TSF  = datetime.datetime.now().strftime("%Y%m%d_%H%M")

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
        "pct exec "+str(ctid)+" -- bash -c "+json.dumps(cmd)],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def gh_push(path, content, msg):
    headers={"Authorization":"Bearer "+GH,"Content-Type":"application/json",
             "Accept":"application/vnd.github.v3+json"}
    try:
        req=urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/contents/{path}",
            headers=headers)
        with urllib.request.urlopen(req,timeout=10) as r:
            sha=json.loads(r.read()).get("sha","")
    except: sha=""
    if isinstance(content,str): content=content.encode()
    data={"message":msg,"content":base64.b64encode(content).decode()}
    if sha: data["sha"]=sha
    req2=urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/contents/{path}",
        data=json.dumps(data).encode(),headers=headers,method="PUT")
    try:
        with urllib.request.urlopen(req2,timeout=15) as r:
            ok="content" in json.loads(r.read())
            return ok
    except Exception as e:
        print(f"  GH push error {path}: {e}")
        return False

print("="*60)
print("CT108 READ + BACKUP + STUDY")
print(TS)
print("="*60)

# ── PROX1: Full inventory ──
print("\n[PROX1] Inventory...")
p1_cts = rx(P1,"pct list")
p1_vms = rx(P1,"qm list 2>/dev/null || echo 'no VMs'")
p1_ct_status = rx(P1,
    "for id in $(pct list | awk 'NR>1{print $1}'); do "
    "echo \"CT$id: $(pct status $id | awk '{print $2}') - $(pct config $id | grep hostname | head -1)\"; "
    "done")
print(p1_cts)
print(p1_vms)
print(p1_ct_status)

# ── CT108: Status ──
print("\n[CT108] Status...")
ct108_st = rx(P1,"pct status 108")
print(" ",ct108_st)
if "stopped" in ct108_st.lower():
    print("  Starting CT108...")
    rx(P1,"pct start 108",t=20)
    time.sleep(8)
    ct108_st = rx(P1,"pct status 108")
    print("  After start:",ct108_st)

# ── CT108: Find web root ──
print("\n[CT108] Finding web root...")
for candidate in ["/var/www/html","/var/www","/usr/share/nginx/html","/opt/vnt","/root"]:
    chk = pct_exec(P1,"108",f"test -d {candidate} && ls {candidate} | head -3 && echo FOUND:{candidate}")
    if "FOUND:" in chk and ("html" in chk or "js" in chk or "dashboard" in chk):
        web_root = candidate
        print(f"  Web root: {web_root}")
        break
else:
    found = pct_exec(P1,"108",
        "find / -name 'dashboard.html' -not -path '*/proc/*' 2>/dev/null | head -1")
    web_root = os.path.dirname(found.strip()) if found.strip() else "/var/www/html"
    print(f"  Web root (searched): {web_root}")

# ── CT108: Read ALL files ──
print("\n[CT108] Reading web files...")
all_files = pct_exec(P1,"108",f"ls -la {web_root}/")
print(" ",all_files[:500])

dashboard_html = pct_exec(P1,"108",f"cat {web_root}/dashboard.html 2>/dev/null",t=15)
media_html     = pct_exec(P1,"108",f"cat {web_root}/media.html 2>/dev/null",t=15)
index_html     = pct_exec(P1,"108",f"cat {web_root}/index.html 2>/dev/null",t=15)
nginx_conf     = pct_exec(P1,"108",
    "cat /etc/nginx/sites-enabled/default 2>/dev/null || "
    "cat /etc/nginx/sites-available/default 2>/dev/null || "
    "cat /etc/nginx/conf.d/default.conf 2>/dev/null")

print(f"  dashboard.html: {len(dashboard_html)} chars")
print(f"  media.html: {len(media_html)} chars")
print(f"  index.html: {len(index_html)} chars")
print(f"  nginx: {len(nginx_conf)} chars")
print(f"\n  === DASHBOARD PREVIEW (first 500 chars) ===")
print(dashboard_html[:500])

# ── STEP 1: BACKUP BEFORE ANYTHING ──
print("\n[BACKUP] Creating rollback point...")
backup_dir = f"/root/backup_ct108_{TSF}"
backup_result = rx(P1,
    f"mkdir -p {backup_dir} && "
    f"pct exec 108 -- bash -c 'tar czf /tmp/web_backup_{TSF}.tar.gz {web_root}/' && "
    f"pct pull 108 /tmp/web_backup_{TSF}.tar.gz {backup_dir}/web_backup_{TSF}.tar.gz && "
    f"echo BACKUP_OK:{backup_dir}/web_backup_{TSF}.tar.gz")
print(" ",backup_result[:200])

# Push backup manifest to GitHub
backup_manifest = {
    "timestamp": TS,
    "backup_path": f"{backup_dir}/web_backup_{TSF}.tar.gz",
    "web_root": web_root,
    "dashboard_size": len(dashboard_html),
    "media_size": len(media_html),
    "restore_command": f"pct push 108 {backup_dir}/web_backup_{TSF}.tar.gz /tmp/restore.tar.gz && pct exec 108 -- bash -c 'cd / && tar xzf /tmp/restore.tar.gz'",
}
gh_push(f"infra/backups/ct108_{TSF}.json",
    json.dumps(backup_manifest,indent=2),
    f"CT108 backup manifest {TSF}")
print(f"  Backup manifest saved to GitHub")

# ── Push actual web files to GitHub for Claude to read ──
print("\n[GH] Pushing CT108 files to GitHub...")
results={}
if dashboard_html:
    results["dashboard"] = gh_push("infra/ct108_dashboard.html",dashboard_html,f"CT108 dashboard.html {TS}")
if media_html:
    results["media"] = gh_push("infra/ct108_media.html",media_html,f"CT108 media.html {TS}")
if index_html:
    results["index"] = gh_push("infra/ct108_index.html",index_html,f"CT108 index.html {TS}")
if nginx_conf:
    results["nginx"] = gh_push("infra/ct108_nginx.conf",nginx_conf,f"CT108 nginx {TS}")
print(" ",{k:"OK" if v else "FAIL" for k,v in results.items()})

# ── PROX2: Study Omada ──
print("\n[PROX2] Omada study...")
p2_cts = rx(P2,"pct list")
p2_vms = rx(P2,"qm list 2>/dev/null || echo 'no VMs'")
print(p2_cts); print(p2_vms)
omada_100 = rx(P2,"qm status 100 2>/dev/null || pct status 100 2>/dev/null")
omada_101 = rx(P2,"pct status 101 2>/dev/null || qm status 101 2>/dev/null")
print(f"  VM100 (active Omada): {omada_100}")
print(f"  CT101 (backup Omada): {omada_101}")

# ── Save infra to GitHub ──
infra = {
    "updated": TS,
    "CRITICAL": {
        "production_web": "CT108 on Prox1 192.168.10.19",
        "web_root": web_root,
        "domain": "vntworld.com",
        "NEVER_WRITE_TO": "/home/k/vnt-web (this is MSI, NOT production)",
        "write_command": f"pct exec 108 -- bash to write to {web_root}/",
        "rollback": backup_manifest["restore_command"]
    },
    "prox1": {
        "ip": P1,
        "containers": p1_cts,
        "vms": p1_vms,
        "ct_status": p1_ct_status,
    },
    "ct108": {
        "web_root": web_root,
        "dashboard_html_size": len(dashboard_html),
        "media_html_size": len(media_html),
        "nginx_config": nginx_conf[:400],
        "backup": backup_manifest,
    },
    "prox2": {
        "ip": P2,
        "omada_active": "VM100 running",
        "omada_backup": "CT101 stopped",
        "containers": p2_cts,
        "vms": p2_vms,
    }
}
gh_push("infra/infrastructure.json",
    json.dumps(infra,indent=2),"infrastructure summary")

# ── Update vnt_config.json ──
try: cfg=json.load(open(CFG))
except: cfg={}
cfg.update({
    "production_web_ct":"108","production_web_root":web_root,
    "production_web_host":P1,"production_domain":"vntworld.com",
    "prox1_ip":P1,"prox2_ip":P2,
    "omada_active_id":"100","omada_backup_id":"101",
    "ct108_backup":backup_manifest,"updated":TS,
})
json.dump(cfg,open(CFG,"w"),indent=2)

save("\n".join([
    f"CT108 STUDIED {TS}",
    f"Web root: {web_root}",
    f"Backup: {backup_manifest['backup_path']}",
    f"Files pushed to GitHub infra/",
    f"NEVER write to /home/k/vnt-web",
    f"Prox2 Omada: VM100=active, CT101=backup",
]))

print("\n"+"="*60)
print(f"DONE. Web root: {web_root}")
print(f"Backup: {backup_manifest['backup_path']}")
print(f"GitHub: https://github.com/{REPO}/blob/main/infra/ct108_dashboard.html")
print("="*60)
