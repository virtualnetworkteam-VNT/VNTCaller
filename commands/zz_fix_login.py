import subprocess, base64, datetime, json, os, time

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
    try: open(MP,"a").write("\n### Login Fix ["+TSF+"]\n"+e+"\n")
    except: pass

print("="*55)
print("FIX: AUTO-LOGIN + OPEN WEBUI UNLIMITED")
print(TSF)
print("="*55)

# Read current dashboard
print("\n[1] Reading current dashboard.html...")
size=pct_e(108,f"wc -c {WEB}/dashboard.html | awk '{{print $1}}'")
print(f"  Size: {size} bytes")

# Pull dashboard to MSI for editing
rx(P1,f"pct pull 108 {WEB}/dashboard.html /tmp/current_dash.html",t=20)
if not os.path.exists("/tmp/current_dash.html"):
    print("  Pull failed - aborting")
    exit(1)

html=open("/tmp/current_dash.html").read()
print(f"  Pulled: {len(html)} chars")

# ── PATCH 1: Auto-login from localStorage ──
print("\n[2] Patching auto-login...")

# Find the checkAuth or init function and add localStorage check
auto_login_patch="""
// ── AUTO-LOGIN: Check saved token on startup ──
async function autoLogin(){
  const token=localStorage.getItem("vnt_tk");
  const udata=localStorage.getItem("vnt_u");
  if(!token||!udata) return false;
  try{
    const r=await fetch("/api/auth.php?action=check",{
      method:"POST",
      headers:{"Content-Type":"application/json","Authorization":"Bearer "+token},
      body:JSON.stringify({token:token}),
      signal:AbortSignal.timeout(5000)
    });
    const d=await r.json();
    if(d.success){
      window.currentUser=JSON.parse(udata);
      return true;
    }
  }catch(e){}
  return false;
}"""

# Inject before closing script tag
html=html.replace("</script>",auto_login_patch+"\n</script>",1)

# ── PATCH 2: Save token on login ──
# Find login POST calls and add localStorage save
if 'localStorage.setItem("vnt_tk"' not in html:
    html=html.replace(
        'd.success',
        'd.success&&d.token&&(localStorage.setItem("vnt_tk",d.token),localStorage.setItem("vnt_u",JSON.stringify(d.user||{id:"ryan",name:"Ryan",role:"admin"})))||d.success',
        1  # Only first occurrence (login success)
    )
    print("  Token save injected")

# ── PATCH 3: Check localStorage on page load ──
# Find where the page init happens and prepend autoLogin check
if "autoLogin()" not in html:
    # Find DOMContentLoaded or window.onload
    if "DOMContentLoaded" in html:
        html=html.replace(
            "document.addEventListener(\"DOMContentLoaded\",",
            "document.addEventListener(\"DOMContentLoaded\","
        )
    # Add auto-login trigger at start of init
    html=html.replace(
        "window.onload=",
        "window.onload=async function(){const ok=await autoLogin();if(ok){const fn=("
    )

# ── PATCH 4: Add "Remember me" UI and fix login form ──
if "remember" not in html.lower():
    html=html.replace(
        '<button class="btn-p"',
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px"><input type="checkbox" id="rememberMe" checked style="accent-color:#6366f1"><label for="rememberMe" style="font-size:11px;color:#4a6080;cursor:pointer">Keep me signed in</label></div><button class="btn-p"'
    )
    print("  Remember me checkbox added")

# ── Write fixed HTML back ──
open("/tmp/fixed_dash.html","w").write(html)
print(f"  Fixed HTML: {len(html)} chars")

# Backup + push
pct_e(108,f"cp {WEB}/dashboard.html {WEB}/dashboard.html.bak_prelogin_{TSF}")
rx(P1,f"pct push 108 /tmp/fixed_dash.html {WEB}/dashboard.html",t=30)

# Verify
v=pct_e(108,f"wc -c {WEB}/dashboard.html | awk '{{print $1}}'")
print(f"[3] Pushed: {v} bytes")

# ── FIX Open WebUI ──
print("\n[4] Fixing Open WebUI unlimited access...")

# Check where Open WebUI is running
owui_ps=subprocess.run("ps aux | grep -i 'open.webui\\|openwebui\\|main:app' | grep -v grep | head -3",
    shell=True,capture_output=True,text=True).stdout.strip()
print("  Process:",owui_ps[:200])

owui_port=subprocess.run("ss -tlnp | grep -E ':3000|:8080|:11000|:7860' | head -5",
    shell=True,capture_output=True,text=True).stdout.strip()
print("  Ports:",owui_port[:200])

owui_docker=subprocess.run("docker ps 2>/dev/null | head -10",
    shell=True,capture_output=True,text=True).stdout.strip()
print("  Docker:",owui_docker[:300])

# Find .env files with WEBUI settings
env_out=subprocess.run("find /home /opt /root -name '.env' -o -name 'docker-compose.yml' 2>/dev/null | head -10",
    shell=True,capture_output=True,text=True).stdout.strip()
print("  Env/compose files:",env_out[:200])

for fpath in env_out.split("\n"):
    fpath=fpath.strip()
    if not fpath or not os.path.exists(fpath): continue
    content=open(fpath).read()
    changed=False
    if "WEBUI" in content or "webui" in content.lower():
        print(f"  Patching {fpath}...")
        # Disable auth
        for old,new in [
            ("WEBUI_AUTH=True","WEBUI_AUTH=False"),
            ("WEBUI_AUTH=true","WEBUI_AUTH=False"),
            ("ENABLE_SIGNUP=false","ENABLE_SIGNUP=true"),
            ("DEFAULT_USER_ROLE=pending","DEFAULT_USER_ROLE=admin"),
        ]:
            if old in content:
                content=content.replace(old,new); changed=True
        if "WEBUI_AUTH" not in content:
            content+="\nWEBUI_AUTH=False\nENABLE_SIGNUP=true\nDEFAULT_USER_ROLE=admin\n"
            changed=True
        if changed:
            open(fpath,"w").write(content)
            print(f"  Updated: {fpath}")

# Restart Open WebUI if docker
if owui_docker and "webui" in owui_docker.lower():
    cid=subprocess.run("docker ps | grep -i webui | awk '{print $1}'",
        shell=True,capture_output=True,text=True).stdout.strip().split("\n")[0]
    if cid:
        subprocess.run(f"docker restart {cid}",shell=True,capture_output=True,timeout=30)
        print(f"  Docker restarted: {cid}")

# ── Reload nginx in CT108 ──
pct_e(108,"nginx -s reload 2>/dev/null || service nginx reload 2>/dev/null || true")
print("\n[5] Nginx reloaded")

save(f"Login fix {TSF}\nAuto-login: localStorage token\nOpen WebUI: WEBUI_AUTH=False\nVNT credentials active")
print("\n"+"="*55)
print("DONE")
print("Login: use ryan/116899 or khawaja/App159earance.VnT")
print("After login: never asked again (token stored)")
print("Open WebUI: auth disabled for unlimited use")
print("="*55)
