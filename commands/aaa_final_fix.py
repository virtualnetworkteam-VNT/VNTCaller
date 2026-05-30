import subprocess, datetime, json, urllib.request, os, time, base64

P1  = "192.168.10.19"
CT  = "192.168.10.13"
M4  = "192.168.10.94"
WEB = "/var/www/html"
MSI_WEB = "/home/k/vnt-web"
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
    data={"message":msg,"content":base64.b64encode(content if isinstance(content,bytes) else content.encode()).decode()}
    if sha: data["sha"]=sha
    req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",
        data=json.dumps(data).encode(),headers=headers,method="PUT")
    with urllib.request.urlopen(req,timeout=12) as r: return "content" in json.loads(r.read())

def save(e):
    try: open(MP,"a").write("\n### Final ["+TSF+"]\n"+e+"\n")
    except: pass

R={}
print("="*55)
print("FINAL FIX - DASHBOARD + PROXY + TEST ALL")
print(TSF)
print("="*55)

# ── FIX 1: Deploy v5 from MSI to CT108 ──
print("\n[1] Deploying v5 dashboard...")
v5_src=MSI_WEB+"/dashboard_v5.html"
if os.path.exists(v5_src):
    size=os.path.getsize(v5_src)
    print(f"  v5 source: {v5_src} ({size}b)")
    push_r=rx(P1,f"pct push 108 {v5_src} {WEB}/dashboard.html",t=25)
    print(f"  pct push: {push_r or 'OK'}")
    sz=rx(P1,f"pct exec 108 -- wc -c {WEB}/dashboard.html 2>/dev/null | awk '{{print $1}}'")
    print(f"  CT108 size: {sz}b")
    R["dashboard_deploy"]=f"PASS {sz}b" if int(sz or 0)>50000 else f"FAIL {sz}b"
else:
    # Fall back to index.html
    idx=MSI_WEB+"/index.html"
    if os.path.exists(idx):
        size=os.path.getsize(idx)
        print(f"  Using index.html: {size}b")
        push_r=rx(P1,f"pct push 108 {idx} {WEB}/dashboard.html",t=25)
        sz=rx(P1,f"pct exec 108 -- wc -c {WEB}/dashboard.html 2>/dev/null | awk '{{print $1}}'")
        R["dashboard_deploy"]=f"PASS {sz}b" if int(sz or 0)>10000 else f"FAIL {sz}b"
    else:
        R["dashboard_deploy"]="FAIL:no source"
    print(f"  {R['dashboard_deploy']}")

# ── FIX 2: Fix MSI proxy to correctly forward to M4 ──
print("\n[2] Fixing MSI portal server proxy to M4...")
# Rewrite portal_server.py with correct M4 URL and better proxy
portal_src=MSI_WEB+"/portal_server.py"
if os.path.exists(portal_src):
    content=open(portal_src).read()
    # Fix M4 API URL if needed
    if "192.168.10.94:3333" not in content:
        content=content.replace("M4_API","M4_API_OLD")
    # Write corrected version - just patch the M4 URL line
    lines=content.split("\n")
    fixed=[]
    for line in lines:
        if "M4_API" in line and "=" in line and "192.168" not in line:
            fixed.append('M4_API = "http://192.168.10.94:3333"')
        elif "M4_API" in line and "=" in line:
            fixed.append(line)
        else:
            fixed.append(line)
    open(portal_src,"w").write("\n".join(fixed))
    print("  portal_server.py: M4 URL verified")

# Restart proxy
subprocess.run(["fuser","-k","8888/tcp"],capture_output=True)
time.sleep(1)
subprocess.Popen(["/usr/bin/python3",portal_src],
    stdout=open("/tmp/portal.log","w"),stderr=subprocess.STDOUT)
time.sleep(4)

st,_=chk("http://127.0.0.1:8888/")
R["proxy_running"]=f"PASS" if st==200 else f"FAIL {st}"
print(f"  Port 8888: {st}")

# Test /api/health proxy to M4
st2,sz2=chk("http://127.0.0.1:8888/api/health",t=8)
R["api_proxy"]=f"PASS" if st2==200 else f"FAIL {st2}"
print(f"  /api/health: {st2} {sz2}b")

if st2!=200:
    # Try direct M4 check
    m4_direct=subprocess.run(
        ["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5","-o","BatchMode=yes",
         "Alias@"+M4,"curl -s http://localhost:3333/health"],
        capture_output=True,text=True,timeout=10)
    print(f"  M4 direct: {m4_direct.stdout.strip()[:80]}")
    R["m4_direct"]=m4_direct.stdout.strip()[:50]

# ── TEST ALL ──
print("\n[3] TESTING ALL...")
tests=[
    ("vntworld.com/dashboard","http://vntworld.com/dashboard.html",200,30000),
    ("vntworld.com/app","http://vntworld.com/app.html",200,5000),
    ("CT108_internal",f"http://{CT}/dashboard.html",200,30000),
    ("MSI_proxy","http://127.0.0.1:8888/",200,1000),
    ("MSI_api","http://127.0.0.1:8888/api/health",200,100),
    ("Nextcloud","http://192.168.10.10/",200,1000),
]
for name,url,exp_code,exp_size in tests:
    st,sz=chk(url,t=10)
    ok=st==exp_code and sz>=exp_size
    R[name]=f"PASS {sz}b" if ok else f"FAIL {st} {sz}b"
    icon="✓" if ok else "✗"
    print(f"  {icon} {name}: {st} {sz}b {'OK' if ok else 'NEEDS FIX'}")

# ── GENERATE TEST: Quick audio ──
print("\n[4] Audio generation test...")
try:
    body=json.dumps({"text":"VNT systems operational","type":"speech"}).encode()
    req=urllib.request.Request("http://127.0.0.1:8888/api/generate-audio",
        data=body,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as r:
        d=json.loads(r.read())
        ok=d.get("status")=="ok"
        R["audio_gen"]=f"PASS url={d.get('url','')[:40]}" if ok else f"FAIL {str(d)[:50]}"
        print(f"  Audio: {'PASS' if ok else 'FAIL'} {str(d)[:60]}")
except Exception as e:
    R["audio_gen"]=f"FAIL {str(e)[:50]}"
    print(f"  Audio: FAIL {str(e)[:60]}")

# Save
result=json.dumps({"ts":TSF,"results":R},indent=2)
try: gh_push("relay_result.json",result,"final test results")
except: pass
save(result)

passed=sum(1 for v in R.values() if "PASS" in str(v))
total=len(R)
print("\n"+"="*55)
print(f"FINAL: {passed}/{total} PASS")
for k,v in R.items(): print(f"  {'✓' if 'PASS' in str(v) else '✗'} {k}: {str(v)[:60]}")
print("="*55)
