import subprocess, datetime, json, urllib.request, os, time, base64

CT  = "192.168.10.13"
MSI = "/home/k/vnt-web"
P1  = "192.168.10.19"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GH  = open("/home/k/vnt-config-gh.txt").read().strip()
REPO= "virtualnetworkteam-VNT/VNTCaller"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx_ct(c,t=15):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8","root@"+CT,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def rx_p1(c,t=15):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8","root@"+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def chk(url,t=6):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"VNT/1.0"})
        with urllib.request.urlopen(req,timeout=t) as r: return r.status,len(r.read())
    except Exception as e: return 0,str(e)[:40]
def gh_push(path,content,msg):
    hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
    try:
        r=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",headers=hdr)
        with urllib.request.urlopen(r,timeout=8) as rr: sha=json.loads(rr.read()).get("sha","")
    except: sha=""
    data={"message":msg,"content":base64.b64encode(content if isinstance(content,bytes) else content.encode()).decode()}
    if sha: data["sha"]=sha
    req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",data=json.dumps(data).encode(),headers=hdr,method="PUT")
    with urllib.request.urlopen(req,timeout=12) as r: return "content" in json.loads(r.read())
def save(e):
    try: open(MP,"a").write("\n### Emergency ["+TSF+"]\n"+e+"\n")
    except: pass

R={}
print("="*55)
print("EMERGENCY RESTART - CT108 + MSI")
print(TSF)
print("="*55)

# ── RESTART CT108 WEB SERVER ──
print("\n[1] Restarting CT108 web server...")
# Kill everything
rx_ct("pkill -9 -f python3 2>/dev/null; fuser -k 80/tcp 2>/dev/null; sleep 2")
time.sleep(3)

# Check what python3 is available
python_ver=rx_ct("python3 --version 2>/dev/null || echo NONE")
print(f"  Python: {python_ver}")

# Check if ThreadingHTTPServer available
threading_ok=rx_ct("python3 -c 'from http.server import ThreadingHTTPServer; print(\"OK\")' 2>/dev/null || echo FAIL")
print(f"  ThreadingHTTPServer: {threading_ok}")

# Start web server - use disown to properly detach
if "OK" in threading_ok:
    # Use threaded server
    start_cmd="cd /var/www/html && python3 /tmp/ct108v2.py > /tmp/ct108.log 2>&1 & disown"
else:
    # Fallback to simple server
    start_cmd="cd /var/www/html && python3 -m http.server 80 --bind 0.0.0.0 > /tmp/web.log 2>&1 & disown"

rx_ct(start_cmd)
time.sleep(5)

# Verify
ps=rx_ct("ps aux | grep -E 'python3' | grep -v grep | head -3")
port=rx_ct("ss -tlnp | grep :80 | head -3")
print(f"  Process:\n  {ps[:200]}")
print(f"  Port 80: {port[:100]}")

st,sz=chk(f"http://{CT}/",t=8)
R["ct108_web"]=f"PASS {sz}b" if st==200 else f"FAIL {st}"
print(f"  CT108 web: {st} {sz}b")

if st!=200:
    # Try pct exec as backup
    log_out=rx_ct("tail -10 /tmp/ct108.log 2>/dev/null || tail -10 /tmp/web.log 2>/dev/null")
    print(f"  Log: {log_out[:200]}")
    # Try alternative: use pct exec from Prox1
    pct_start=rx_p1(f"pct exec 108 -- bash -c 'cd /var/www/html && python3 -m http.server 80 --bind 0.0.0.0 > /tmp/web.log 2>&1 &'")
    print(f"  pct exec start: {pct_start[:80]}")
    time.sleep(5)
    st,sz=chk(f"http://{CT}/",t=8)
    R["ct108_web"]=f"PASS {sz}b" if st==200 else f"FAIL {st}"
    print(f"  CT108 web after pct: {st} {sz}b")

# ── RESTART MSI PORTAL ──
print("\n[2] Restarting MSI portal...")
subprocess.run(["fuser","-k","8888/tcp"],capture_output=True)
time.sleep(1)
if os.path.exists(MSI+"/portal_server.py"):
    subprocess.Popen(["/usr/bin/python3",MSI+"/portal_server.py"],
        stdout=open("/tmp/portal.log","w"),stderr=subprocess.STDOUT)
    time.sleep(5)
    st2,sz2=chk("http://127.0.0.1:8888/",t=6)
    R["msi_8888"]=f"PASS {sz2}b" if st2==200 else f"FAIL {st2}"
    print(f"  MSI 8888: {st2} {sz2}b")
    st3,sz3=chk("http://127.0.0.1:8888/api/health",t=6)
    R["msi_api"]=f"PASS {sz3}b" if st3==200 else f"FAIL {st3}"
    print(f"  MSI api: {st3} {sz3}b")
else:
    print("  portal_server.py missing!")
    R["msi_8888"]="FAIL:missing"

# ── TEST ALL ──
print("\n[3] Testing all...")
tests=[
    ("vntworld","http://vntworld.com/dashboard.html",200,60000),
    ("vntworld_app","http://vntworld.com/app.html",200,5000),
    ("vntworld_api","http://vntworld.com/api/health",200,50),
    ("ct108_internal",f"http://{CT}/dashboard.html",200,60000),
    ("ct108_api",f"http://{CT}/api/health",200,50),
    ("nextcloud","http://192.168.10.10/",200,1000),
]
for name,url,code,min_sz in tests:
    st4,sz4=chk(url,t=10)
    ok=(st4==code and sz4>=min_sz)
    R[name]=f"PASS {sz4}b" if ok else f"FAIL {st4} {sz4}b"
    print(f"  {'PASS' if ok else 'FAIL'} {name}: {st4} {sz4}b")

# M4
m4r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5","-o","BatchMode=yes",
    "Alias@192.168.10.94","curl -s http://localhost:3333/health"],capture_output=True,text=True,timeout=10)
R["m4"]="PASS" if "\"online\"" in m4r.stdout else "FAIL"
print(f"  M4: {m4r.stdout.strip()[:60]}")

result=json.dumps({"ts":TSF,"results":R},indent=2)
try: gh_push("relay_result.json",result,"emergency restart results")
except Exception as e: print(f"GH: {e}")
save(result)

passed=sum(1 for v in R.values() if "PASS" in str(v))
print("\n"+"="*55)
print(f"SCORE: {passed}/{len(R)}")
for k,v in R.items(): print(f"  {'PASS' if 'PASS' in str(v) else 'FAIL'} {k}: {str(v)[:60]}")
print("="*55)
