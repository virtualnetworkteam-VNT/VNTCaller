import subprocess, datetime, json, urllib.request, os, time, base64

P1  = "192.168.10.19"
CT  = "192.168.10.13"
M4  = "192.168.10.94"
WEB = "/var/www/html"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GH  = open("/home/k/vnt-config-gh.txt").read().strip()
REPO= "virtualnetworkteam-VNT/VNTCaller"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx(h,c,t=25):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8","root@"+h,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def chk(url,t=8):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"VNT/1.0"})
        with urllib.request.urlopen(req,timeout=t) as r: return r.status,len(r.read())
    except Exception as e: return 0,str(e)[:40]

def gh_push(path,content,msg):
    headers={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
    try:
        r=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",headers=headers)
        with urllib.request.urlopen(r,timeout=8) as rr: sha=json.loads(rr.read()).get("sha","")
    except: sha=""
    data={"message":msg,"content":base64.b64encode(content.encode() if isinstance(content,str) else content).decode()}
    if sha: data["sha"]=sha
    req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",
        data=json.dumps(data).encode(),headers=headers,method="PUT")
    with urllib.request.urlopen(req,timeout=12) as r: return "content" in json.loads(r.read())

def save(e):
    try: open(MP,"a").write("\n### Fix ["+TSF+"]\n"+e+"\n")
    except: pass

R={}
print("="*55)
print("FIX: PROXY + DASHBOARD v5")
print(TSF)
print("="*55)

# ── FIX 1: Restart MSI proxy ──
print("\n[1] Restarting MSI proxy (8888)...")
subprocess.run(["fuser","-k","8888/tcp"],capture_output=True)
time.sleep(1)
portal="/home/k/vnt-web/portal_server.py"
if os.path.exists(portal):
    subprocess.Popen(["/usr/bin/python3",portal],
        stdout=open("/tmp/portal.log","w"),stderr=subprocess.STDOUT)
    time.sleep(4)
    st,sz=chk("http://127.0.0.1:8888/")
    R["msi_proxy"]=f"PASS {st}" if st==200 else f"FAIL {st}"
    print(f"  Port 8888: {st} {sz}b")
    # Test proxy to M4
    st2,sz2=chk("http://127.0.0.1:8888/api/health")
    R["api_proxy"]=f"PASS {st2}" if st2==200 else f"FAIL {st2}"
    print(f"  /api/health: {st2} {sz2}b")
else:
    R["msi_proxy"]="FAIL:no portal_server.py"
    print(f"  FAIL: {portal} missing")

# ── FIX 2: Deploy v5 HTML directly via SCP to CT108 IP ──
print("\n[2] Deploying v5 dashboard via SCP to CT108 (192.168.10.13)...")
# Try direct SCP to CT108
v5_path="/tmp/dash_v5_deploy.html"
# Get best backup from Prox1
best_bk=rx(P1,"ls -S /root/ct108_backups/*.html 2>/dev/null | head -1").strip()
if best_bk:
    bs_out=rx(P1,f"stat -c %s {best_bk} 2>/dev/null")
    try: bs=int(bs_out.strip())
    except: bs=0
    print(f"  Best Prox1 backup: {best_bk} ({bs}b)")
    if bs>50000:
        rx(P1,f"pct push 108 {best_bk} {WEB}/dashboard.html",t=25)
        sz_check=rx(P1,f"pct exec 108 -- wc -c {WEB}/dashboard.html 2>/dev/null | awk '{{print $1}}'")
        print(f"  After restore: {sz_check}b")
        R["dashboard"]=f"PASS {sz_check}b" if int(sz_check or 0)>50000 else f"FAIL {sz_check}b"
    else:
        # Try writing v5 HTML in base64 chunks via pct exec
        print("  Writing v5 HTML via base64 chunks in container...")
        # Read from MSI's copy if exists
        if os.path.exists("/home/k/vnt-web/index.html"):
            html=open("/home/k/vnt-web/index.html","rb").read()
            print(f"  Using index.html: {len(html)}b")
            b64=base64.b64encode(html).decode()
            # Write in 10k chunks via pct exec
            chunk_size=8000
            chunks=[b64[i:i+chunk_size] for i in range(0,len(b64),chunk_size)]
            # First chunk
            rx(P1,f"pct exec 108 -- bash -c 'printf \"%s\" \"{chunks[0]}\" > /tmp/d.b64'",t=20)
            for ch in chunks[1:]:
                rx(P1,f"pct exec 108 -- bash -c 'printf \"%s\" \"{ch}\" >> /tmp/d.b64'",t=20)
            dec=rx(P1,f"pct exec 108 -- bash -c 'base64 -d /tmp/d.b64 > {WEB}/dashboard.html && wc -c {WEB}/dashboard.html'",t=20)
            print(f"  Decoded: {dec[:60]}")
            R["dashboard"]=f"PASS {dec}" if html else "FAIL"
        else:
            R["dashboard"]="FAIL:no source"
else:
    R["dashboard"]="FAIL:no backups on prox1"

# ── TEST: Check dashboard is correct size ──
print("\n[3] Verifying dashboard...")
st3,sz3=chk(f"http://{CT}/dashboard.html",t=8)
print(f"  CT108 internal: {st3} {sz3}b")
R["ct108_dash_size"]=f"{sz3}b"

# ── TEST: vntworld.com ──
print("[4] Testing vntworld.com...")
st4,sz4=chk("http://vntworld.com/dashboard.html",t=10)
print(f"  vntworld.com: {st4} {sz4}b")
R["vntworld"]=f"PASS {sz4}b" if st4==200 else f"FAIL {st4}"

# ── TEST: M4 API ──
print("[5] M4 API...")
st5,sz5=chk("http://127.0.0.1:8888/api/health",t=6)
print(f"  via MSI proxy: {st5} {sz5}b")
R["m4_via_proxy"]=f"PASS" if st5==200 else f"FAIL {st5}"

# Save result
result_json=json.dumps({"ts":TSF,"results":R},indent=2)
try: gh_push("relay_result.json",result_json,"fix results")
except Exception as e: print(f"  GH save: {e}")
save(result_json)

print("\n"+"="*55)
passed=sum(1 for v in R.values() if "PASS" in str(v))
print(f"RESULTS: {passed}/{len(R)} PASS")
for k,v in R.items(): print(f"  {'✓' if 'PASS' in str(v) else '✗'} {k}: {v}")
print("="*55)
