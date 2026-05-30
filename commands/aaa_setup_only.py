import subprocess, datetime, json, urllib.request, os, time, base64

P1  = "192.168.10.19"
CT  = "192.168.10.13"
M4  = "192.168.10.94"
WEB = "/var/www/html"
MSI = "/home/k/vnt-web"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GH  = open("/home/k/vnt-config-gh.txt").read().strip()
REPO= "virtualnetworkteam-VNT/VNTCaller"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx(h,c,t=20):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8","root@"+h,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def chk(url,t=6):
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
    req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",data=json.dumps(data).encode(),headers=headers,method="PUT")
    with urllib.request.urlopen(req,timeout=12) as r: return "content" in json.loads(r.read())
def save(e):
    try: open(MP,"a").write("\n### Setup ["+TSF+"]\n"+e+"\n")
    except: pass

R={}
print("="*55)
print("SETUP: PORTAL SERVER + DASHBOARD DEPLOY")
print(TSF)
print("="*55)

# 1. Write portal server with proper proxy
print("[1] Writing portal_server.py with proxy...")
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
    def proxy_m4(self,m4path,body=None,method="GET"):
        try:
            req=urllib.request.Request(M4API+m4path,data=body,headers={"Content-Type":"application/json"},method=method)
            with urllib.request.urlopen(req,timeout=360) as r:
                data=r.read();ct=r.headers.get("Content-Type","application/json")
                self.send_response(200);self.send_header("Content-Type",ct)
                self.cors();self.send_header("Content-Length",str(len(data)))
                self.end_headers();self.wfile.write(data)
        except Exception as e:
            err=json.dumps({"status":"error","error":str(e)}).encode()
            self.send_response(503);self.send_header("Content-Type","application/json")
            self.cors();self.send_header("Content-Length",str(len(err)))
            self.end_headers();self.wfile.write(err)
    def do_OPTIONS(self): self.send_response(200);self.cors();self.end_headers()
    def do_GET(self):
        path=self.path.split("?")[0]
        if path.startswith("/api/"): self.proxy_m4(path[4:]); return
        if path=="/" or path=="": path="/index.html"
        fp=WEB+path
        if os.path.isdir(fp): fp=fp.rstrip("/")+"/index.html"
        if os.path.exists(fp) and os.path.isfile(fp):
            ct,_=mimetypes.guess_type(fp);ct=ct or "application/octet-stream"
            data=open(fp,"rb").read()
            self.send_response(200);self.send_header("Content-Type",ct)
            self.send_header("Content-Length",str(len(data)));self.cors()
            self.end_headers();self.wfile.write(data)
        else: self.send_response(404);self.end_headers();self.wfile.write(b"Not found: "+path.encode())
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0))
        body=self.rfile.read(n) if n else None
        if self.path.startswith("/api/"):
            log("POST M4"+self.path[4:])
            self.proxy_m4(self.path[4:],body,"POST"); return
        self.send_response(404);self.end_headers();self.wfile.write(b"Not found")
subprocess.run(["fuser","-k","8888/tcp"],capture_output=True)
time.sleep(1)
log("VNT Portal :8888 proxying M4="+M4API)
http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
'''
open(MSI+"/portal_server.py","w").write(portal)
print(f"  Written: {len(portal)}b")

# 2. Start portal server
print("[2] Starting portal...")
subprocess.run(["fuser","-k","8888/tcp"],capture_output=True)
time.sleep(1)
subprocess.Popen(["/usr/bin/python3",MSI+"/portal_server.py"],
    stdout=open("/tmp/portal.log","w"),stderr=subprocess.STDOUT)
time.sleep(5)
st,sz=chk("http://127.0.0.1:8888/")
R["msi_8888"]=f"PASS {sz}b" if st==200 else f"FAIL {st}"
print(f"  8888: {st} {sz}b")
st2,sz2=chk("http://127.0.0.1:8888/api/health",t=8)
R["api_proxy"]=f"PASS" if st2==200 else f"FAIL {st2} {sz2}"
print(f"  /api/health: {st2} {sz2}b")

# 3. Deploy v5 HTML - SCP to Prox1 then pct push
print("[3] Deploying v5 dashboard to CT108...")
v5=MSI+"/dashboard_v5.html"
if not os.path.exists(v5): v5=MSI+"/index.html"
vsz=os.path.getsize(v5) if os.path.exists(v5) else 0
print(f"  Source: {v5} ({vsz}b)")
# SCP to Prox1
scp=subprocess.run(["scp","-o","StrictHostKeyChecking=no",v5,"root@"+P1+":/tmp/vv5.html"],
    capture_output=True,text=True,timeout=20)
print(f"  SCP to Prox1: {'OK' if scp.returncode==0 else scp.stderr[:60]}")
# pct push from Prox1 to CT108
push_r=rx(P1,"pct push 108 /tmp/vv5.html /var/www/html/dashboard.html",t=20)
print(f"  pct push: {push_r or 'OK'}")
# Verify
sz_r=rx(P1,"pct exec 108 -- bash -c 'stat -c %s /var/www/html/dashboard.html 2>/dev/null'")
try: ct_sz=int(sz_r.strip())
except: ct_sz=0
R["ct108_dash"]=f"PASS {ct_sz}b" if ct_sz>30000 else f"FAIL {ct_sz}b"
print(f"  CT108 dashboard: {ct_sz}b")

# 4. Deploy app.html to CT108
print("[4] Deploying app.html...")
app_src=MSI+"/app.html"
if os.path.exists(app_src):
    subprocess.run(["scp","-o","StrictHostKeyChecking=no",app_src,"root@"+P1+":/tmp/app.html"],capture_output=True,timeout=15)
    rx(P1,"pct push 108 /tmp/app.html /var/www/html/app.html",t=15)
    app_sz=rx(P1,"pct exec 108 -- bash -c 'stat -c %s /var/www/html/app.html 2>/dev/null'")
    R["ct108_app"]=f"PASS {app_sz}b" if int(app_sz or 0)>5000 else f"FAIL {app_sz}b"
    print(f"  app.html: {app_sz}b")
else: R["ct108_app"]="SKIP"

# 5. Quick tests - NO generation (too slow for relay)
print("[5] Quick tests...")
tests=[
    ("vntworld.com",    "http://vntworld.com/dashboard.html",   200,30000),
    ("vnt_app",         "http://vntworld.com/app.html",         200,5000),
    ("MSI_portal",      "http://127.0.0.1:8888/",              200,1000),
    ("MSI_api",         "http://127.0.0.1:8888/api/health",    200,10),
    ("nextcloud",       "http://192.168.10.10/",               200,1000),
    ("ct108_internal",  f"http://{CT}/",                       200,1000),
]
for name,url,exp_code,exp_size in tests:
    st3,sz3=chk(url,t=8)
    ok=st3==exp_code and sz3>=exp_size
    R[name]=f"PASS {sz3}b" if ok else f"FAIL {st3} {sz3}"
    print(f"  {'✓' if ok else '✗'} {name}: {st3} {sz3}b")

# M4 API direct
m4=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5",
    "-o","BatchMode=yes","Alias@"+M4,"curl -s http://localhost:3333/health"],
    capture_output=True,text=True,timeout=10)
online="\"online\"" in m4.stdout
R["m4_api"]="PASS" if online else f"FAIL {m4.stdout[:40]}"
print(f"  {'✓' if online else '✗'} M4 API: {m4.stdout.strip()[:60]}")

# Save result
result=json.dumps({"ts":TSF,"results":R},indent=2)
try: gh_push("relay_result.json",result,"setup results")
except Exception as e: print(f"GH: {e}")
save(result)

passed=sum(1 for v in R.values() if "PASS" in str(v))
print("\n"+"="*55)
print(f"SCORE: {passed}/{len(R)}")
for k,v in R.items(): print(f"  {'✓' if 'PASS' in str(v) else '✗'} {k}: {str(v)[:60]}")
print("="*55)
