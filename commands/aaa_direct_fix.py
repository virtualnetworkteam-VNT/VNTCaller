import subprocess, datetime, json, urllib.request, os, time, base64

CT  = "192.168.10.13"   # Direct CT108 IP
M4  = "192.168.10.94"
MSI = "/home/k/vnt-web"
WEB = "/var/www/html"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def scp_to_ct(local,remote,t=20):
    r=subprocess.run(["scp","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8",
        local,"root@"+CT+":"+remote],capture_output=True,text=True,timeout=t)
    return r.returncode==0,r.stderr.strip()

def ssh_ct(c,t=20):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8",
        "root@"+CT,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def chk(url,t=8):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"VNT/1.0"})
        with urllib.request.urlopen(req,timeout=t) as r: return r.status,len(r.read())
    except Exception as e: return 0,str(e)[:40]

def save(e):
    try: open(MP,"a").write("\n### Direct ["+TSF+"]\n"+e+"\n")
    except: pass

# Write result to a local MSI file (accessible via relay next run)
def save_result(R):
    try:
        open("/home/k/vnt-result.json","w").write(json.dumps({"ts":TSF,"results":R},indent=2))
    except Exception as e: print(f"save_result: {e}")

R={}
print("="*55)
print("DIRECT FIX: SCP TO CT108 + PORTAL")
print(TSF)
print("="*55)

# 1. SCP v5 dashboard directly to CT108
print("\n[1] SCPing v5 dashboard directly to CT108 (192.168.10.13)...")
v5=MSI+"/dashboard_v5.html"
if not os.path.exists(v5):
    v5=MSI+"/index.html"
    print(f"  Fallback to index.html")
if os.path.exists(v5):
    vsz=os.path.getsize(v5)
    print(f"  Source: {v5} ({vsz}b)")
    ok,err=scp_to_ct(v5,WEB+"/dashboard.html")
    print(f"  SCP: {'OK' if ok else 'FAIL: '+err[:60]}")
    if ok:
        ct_sz=ssh_ct(f"wc -c {WEB}/dashboard.html 2>/dev/null | awk '{{print $1}}'")
        print(f"  CT108 size: {ct_sz}b")
        R["dashboard"]=f"PASS {ct_sz}b" if int(ct_sz or 0)>30000 else f"FAIL {ct_sz}b"
    else:
        R["dashboard"]="FAIL:scp error"
else:
    R["dashboard"]="FAIL:no source"

# 2. SCP app.html to CT108
print("\n[2] SCPing app.html to CT108...")
app=MSI+"/app.html"
if os.path.exists(app):
    ok2,err2=scp_to_ct(app,WEB+"/app.html")
    app_sz=ssh_ct(f"stat -c %s {WEB}/app.html 2>/dev/null || echo 0")
    R["app"]= f"PASS {app_sz}b" if ok2 else f"FAIL {err2[:40]}"
    print(f"  app.html: {'OK' if ok2 else 'FAIL'} {app_sz}b")
else:
    R["app"]="SKIP"

# 3. SCP manifest and icons to CT108
print("\n[3] SCPing PWA files...")
for src,dst in [(MSI+"/manifest.json",WEB+"/manifest.json"),(MSI+"/sw.js",WEB+"/sw.js")]:
    if os.path.exists(src):
        ok3,_=scp_to_ct(src,dst)
        print(f"  {os.path.basename(src)}: {'OK' if ok3 else 'FAIL'}")
ssh_ct("mkdir -p "+WEB+"/icons")
for sz_n in [192,512]:
    icon=MSI+f"/icons/icon-{sz_n}.png"
    if os.path.exists(icon):
        scp_to_ct(icon,WEB+f"/icons/icon-{sz_n}.png")

# 4. Verify CT108 web server running
print("\n[4] CT108 web server check...")
ps=ssh_ct("ps aux | grep 'http.server' | grep -v grep | head -2")
print(f"  Process: {ps[:100]}")
if not ps.strip():
    print("  Restarting web server...")
    subprocess.Popen(["ssh","-o","StrictHostKeyChecking=no","root@"+CT,
        f"cd {WEB} && nohup python3 -m http.server 80 --bind 0.0.0.0 >> /tmp/web.log 2>&1 &"],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(4)
    ps2=ssh_ct("ps aux | grep 'http.server' | grep -v grep | head -2")
    print(f"  After restart: {ps2[:80]}")

# 5. Write and start portal server
print("\n[5] Portal server (MSI 8888)...")
portal='''import http.server,json,os,urllib.request,datetime,mimetypes,subprocess,time,sys
WEB="/home/k/vnt-web"
M4API="http://192.168.10.94:3333"
PORT=8888
def log(m): print("["+datetime.datetime.now().strftime("%H:%M:%S")+"] "+m,flush=True)
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
    def proxy_m4(self,path,body=None,method="GET"):
        try:
            req=urllib.request.Request(M4API+path,data=body,headers={"Content-Type":"application/json"},method=method)
            with urllib.request.urlopen(req,timeout=360) as r:
                data=r.read();ct=r.headers.get("Content-Type","application/json")
                self.send_response(200);self.send_header("Content-Type",ct)
                self.cors();self.send_header("Content-Length",str(len(data)))
                self.end_headers();self.wfile.write(data)
        except Exception as e:
            err=json.dumps({"error":str(e)}).encode()
            self.send_response(503);self.send_header("Content-Type","application/json")
            self.cors();self.send_header("Content-Length",str(len(err)))
            self.end_headers();self.wfile.write(err)
    def do_OPTIONS(self): self.send_response(200);self.cors();self.end_headers()
    def do_GET(self):
        path=self.path.split("?")[0]
        if path.startswith("/api/"): self.proxy_m4(path[4:]); return
        if path=="/": path="/index.html"
        fp=WEB+path
        if os.path.isdir(fp): fp=fp.rstrip("/")+"/index.html"
        if os.path.exists(fp) and os.path.isfile(fp):
            ct,_=mimetypes.guess_type(fp);ct=ct or "application/octet-stream"
            data=open(fp,"rb").read()
            self.send_response(200);self.send_header("Content-Type",ct)
            self.send_header("Content-Length",str(len(data)));self.cors()
            self.end_headers();self.wfile.write(data)
        else: self.send_response(404);self.end_headers();self.wfile.write(b"404")
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0))
        body=self.rfile.read(n) if n else None
        if self.path.startswith("/api/"):
            log("POST M4"+self.path[4:])
            self.proxy_m4(self.path[4:],body,"POST"); return
        self.send_response(404);self.end_headers();self.wfile.write(b"404")
subprocess.run(["fuser","-k","8888/tcp"],capture_output=True)
time.sleep(1)
log("VNT Portal :8888 -> "+M4API)
http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
'''
open(MSI+"/portal_server.py","w").write(portal)
subprocess.run(["fuser","-k","8888/tcp"],capture_output=True)
time.sleep(1)
subprocess.Popen(["/usr/bin/python3",MSI+"/portal_server.py"],
    stdout=open("/tmp/portal.log","w"),stderr=subprocess.STDOUT)
time.sleep(5)
st,sz=chk("http://127.0.0.1:8888/",t=5)
R["msi_8888"]=f"PASS {sz}b" if st==200 else f"FAIL {st}"
print(f"  8888: {st} {sz}b")
st2,sz2=chk("http://127.0.0.1:8888/api/health",t=8)
R["api_proxy"]=f"PASS {sz2}b" if st2==200 else f"FAIL {st2}"
print(f"  /api/health: {st2} {sz2}b")

# 6. Tests
print("\n[6] Tests...")
tests=[("CT108",f"http://{CT}/dashboard.html",200,30000),
       ("vntworld",   "http://vntworld.com/dashboard.html",200,30000),
       ("vnt_app",    "http://vntworld.com/app.html",200,5000),
       ("nextcloud",  "http://192.168.10.10/",200,1000)]
for name,url,code,min_sz in tests:
    st3,sz3=chk(url,t=10)
    ok=(st3==code and sz3>=min_sz)
    R[name]=f"PASS {sz3}b" if ok else f"FAIL {st3} {sz3}"
    print(f"  {'✓' if ok else '✗'} {name}: {st3} {sz3}b")

# M4 API
m4_r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5",
    "-o","BatchMode=yes","Alias@"+M4,"curl -s http://localhost:3333/health"],
    capture_output=True,text=True,timeout=10)
R["m4"]=f"PASS" if "\"online\"" in m4_r.stdout else f"FAIL {m4_r.stdout[:30]}"
print(f"  {'✓' if 'PASS' in R['m4'] else '✗'} M4: {m4_r.stdout.strip()[:60]}")

save_result(R)
save(json.dumps(R))
passed=sum(1 for v in R.values() if "PASS" in str(v))
print("\n"+"="*55)
print(f"SCORE: {passed}/{len(R)}")
for k,v in R.items(): print(f"  {'PASS' if 'PASS' in str(v) else 'FAIL'} {k}: {str(v)[:60]}")
print("="*55)
