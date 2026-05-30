import subprocess, datetime, os

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
P1  = "192.168.10.19"
P2  = "192.168.10.18"
TS  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def save(e):
    open(MP,"a").write("\n### Prox Study ["+TS+"]\n"+e+"\n")

def rx(host, cmd, t=30):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+host,cmd],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def pct(host, ctid, cmd, t=30):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no",
        "-o","ConnectTimeout=8","root@"+host,
        "pct exec "+str(ctid)+" -- bash -c '"+cmd+"'"],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

print("="*60)
print("STUDYING ALL PROXMOX + CT108 WEB")
print(TS)
print("="*60)

# PROX1 - full container list
print("\n[PROX1] Containers and VMs...")
ct_list = rx(P1,"pct list")
vm_list = rx(P1,"qm list")
print("  CTs:\n"+ct_list)
print("  VMs:\n"+vm_list)

# PROX1 - resource usage
print("\n[PROX1] Resources...")
res = rx(P1,"free -h | head -2; df -h / | tail -1")
print("  "+res[:200])

# CT108 deep study
print("\n[CT108] Studying web container...")
ct108_status = rx(P1,"pct status 108")
print("  Status: "+ct108_status)

ct108_os = pct(P1,"108","cat /etc/os-release | grep PRETTY")
print("  OS: "+ct108_os[:100])

ct108_proc = pct(P1,"108","ps aux | grep -E 'nginx|apache|node|python|caddy|php-fpm' | grep -v grep")
print("  Processes:\n  "+ct108_proc[:400])

ct108_ports = pct(P1,"108","ss -tlnp 2>/dev/null | head -15")
print("  Ports:\n  "+ct108_ports[:300])

ct108_web_root = pct(P1,"108","find / -name 'dashboard.html' -o -name 'index.html' -o -name 'media.html' 2>/dev/null | grep -v proc | head -20")
print("  HTML files:\n  "+ct108_web_root[:400])

ct108_ls_html = pct(P1,"108","ls -la /var/www/html/ 2>/dev/null || ls -la /var/www/ 2>/dev/null || ls -la /usr/share/nginx/html/ 2>/dev/null")
print("  Web dir:\n  "+ct108_ls_html[:400])

ct108_nginx = pct(P1,"108","cat /etc/nginx/sites-enabled/default 2>/dev/null || cat /etc/nginx/sites-available/default 2>/dev/null || cat /etc/nginx/conf.d/default.conf 2>/dev/null")
print("  Nginx config:\n  "+ct108_nginx[:400])

ct108_head = pct(P1,"108","head -50 /var/www/html/index.html 2>/dev/null || head -50 /var/www/html/dashboard.html 2>/dev/null || head -50 /usr/share/nginx/html/index.html 2>/dev/null")
print("  HTML head:\n  "+ct108_head[:600])

# Get ALL html files content
ct108_files_full = pct(P1,"108","find /var/www -name '*.html' 2>/dev/null | head -10")
print("  All HTML: "+ct108_files_full[:300])

# PROX2
print("\n[PROX2] Containers and VMs...")
p2_ct = rx(P2,"pct list")
p2_vm = rx(P2,"qm list")
print("  CTs:\n"+p2_ct)
print("  VMs:\n"+p2_vm)

p2_omada = rx(P2,"pct list 2>/dev/null | grep -i omada; qm list 2>/dev/null | grep -i omada")
print("  Omada: "+p2_omada[:200])

full = "\n".join([
    "PROXMOX STUDY "+TS,
    "PROX1 CTs:", ct_list,
    "PROX1 VMs:", vm_list,
    "CT108 status: "+ct108_status,
    "CT108 OS: "+ct108_os,
    "CT108 processes: "+ct108_proc[:300],
    "CT108 ports: "+ct108_ports[:200],
    "CT108 html files: "+ct108_web_root[:300],
    "CT108 web dir: "+ct108_ls_html[:300],
    "CT108 nginx: "+ct108_nginx[:300],
    "CT108 html preview: "+ct108_head[:400],
    "PROX2 CTs:", p2_ct,
    "PROX2 VMs:", p2_vm,
    "PROX2 Omada: "+p2_omada,
])
save(full)
print("\n"+"="*60)
print("Study complete - saved to MemPalace")
print("="*60)
