import subprocess, datetime, json, urllib.request, os, time, base64

P1  = "192.168.10.19"
CT  = "192.168.10.13"
MSI = "/home/k/vnt-web"
WEB = "/var/www/html"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GH  = open("/home/k/vnt-config-gh.txt").read().strip()
REPO= "virtualnetworkteam-VNT/VNTCaller"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx1(c,t=25):
    "Run on Prox1"
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8","root@"+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def pct_bg(ctid,c):
    "Run in CT bg - no wait"
    subprocess.Popen(["ssh","-o","StrictHostKeyChecking=no","root@"+P1,
        f"pct exec {ctid} -- bash -c "+json.dumps(c)],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def pct_e(ctid,c,t=20):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=8","root@"+P1,
        f"pct exec {ctid} -- bash -c "+json.dumps(c)],
        capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def scp_to_prox(local,remote):
    r=subprocess.run(["scp","-o","StrictHostKeyChecking=no",local,"root@"+P1+":"+remote],
        capture_output=True,text=True,timeout=20)
    return r.returncode==0

def chk(url,t=8):
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
    try: open(MP,"a").write("\n### ProxFix ["+TSF+"]\n"+e+"\n")
    except: pass

R={}
print("="*55)
print("FIX CT108 VIA PROX1 - NO DIRECT SSH TO CT108")
print(TSF)
print("="*55)

# ── Step 1: Kill old web server in CT108 via pct exec ──
print("\n[1] Killing old web server via pct exec...")
pct_bg(108,"pkill -9 -f python3 2>/dev/null; pkill -9 -f http.server 2>/dev/null; fuser -k 80/tcp 2>/dev/null; echo KILLED")
time.sleep(4)

# ── Step 2: Write threaded server to Prox1, then push to CT108 ──
print("[2] Writing threaded proxy server to CT108...")
srv_code = """
import http.server,json,os,urllib.request,urllib.error,mimetypes,sys,datetime
WEB="/var/www/html"
M4="http://192.168.10.94:3333"
PORT=80
def log(m): print("["+datetime.datetime.now().strftime("%H:%M:%S")+"] "+m,flush=True)
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
    def proxy(self,path,body=None,method="GET"):
        try:
            req=urllib.request.Request(M4+path,data=body,headers={"Content-Type":"application/json"},method=method)
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
        if path.startswith("/api/"): self.proxy(path[4:]); return
        if path=="/" or path=="": path="/dashboard.html"
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
        if self.path.startswith("/api/"): log("POST "+self.path[4:]); self.proxy(self.path[4:],body,"POST"); return
        self.send_response(404);self.end_headers();self.wfile.write(b"404")
log("VNT CT108 :"+str(PORT)+" -> "+M4)
try:
    server=http.server.ThreadingHTTPServer(("0.0.0.0",PORT),H)
    log("READY threaded")
    server.serve_forever()
except AttributeError:
    log("Fallback to HTTPServer")
    http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
""".strip()

open("/tmp/vnt_ct108_srv.py","w").write(srv_code)
ok_scp=scp_to_prox("/tmp/vnt_ct108_srv.py","/tmp/vnt_ct108_srv.py")
print(f"  SCP to Prox1: {'OK' if ok_scp else 'FAIL'}")
push_r=rx1("pct push 108 /tmp/vnt_ct108_srv.py /tmp/vnt_ct108_srv.py",t=15)
print(f"  pct push: {push_r or 'OK'}")

# ── Step 3: Write systemd service for auto-restart ──
print("[3] Installing systemd service in CT108...")
svc = "[Unit]\nDescription=VNT Web\nAfter=network.target\n\n[Service]\nExecStart=/usr/bin/python3 /tmp/vnt_ct108_srv.py\nRestart=always\nRestartSec=3\n\n[Install]\nWantedBy=multi-user.target"
open("/tmp/vnt-web.service","w").write(svc)
scp_to_prox("/tmp/vnt-web.service","/tmp/vnt-web.service")
rx1("pct push 108 /tmp/vnt-web.service /etc/systemd/system/vnt-web.service",t=10)
pct_e(108,"systemctl daemon-reload && systemctl enable vnt-web && systemctl restart vnt-web 2>&1",t=15)
time.sleep(4)

svc_status=pct_e(108,"systemctl status vnt-web 2>/dev/null | head -6",t=10)
print(f"  Systemd: {svc_status[:200]}")

# ── Step 4: Verify from Prox1 curl ──
print("[4] Verifying from Prox1...")
curl_root=rx1(f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}' http://{CT}/ --connect-timeout 8",t=15)
curl_api=rx1(f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}' http://{CT}/api/health --connect-timeout 8",t=15)
curl_dash=rx1(f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}' http://{CT}/dashboard.html --connect-timeout 8",t=15)
print(f"  root: {curl_root}")
print(f"  api/health: {curl_api}")
print(f"  dashboard: {curl_dash}")
R["ct108_root"]=f"PASS" if curl_root.startswith("200") else f"FAIL:{curl_root}"
R["ct108_api"]=f"PASS" if curl_api.startswith("200") else f"FAIL:{curl_api}"
R["ct108_dash"]=f"PASS {curl_dash.split()[1]}b" if curl_dash.startswith("200") else f"FAIL:{curl_dash}"

# ── Step 5: Test vntworld.com from Prox1 ──
print("[5] Testing vntworld.com from Prox1...")
vnt=rx1("curl -s -o /dev/null -w '%{http_code} %{size_download}' http://vntworld.com/dashboard.html --connect-timeout 10",t=15)
vnt_api=rx1("curl -s -o /dev/null -w '%{http_code} %{size_download}' http://vntworld.com/api/health --connect-timeout 8",t=15)
print(f"  dashboard: {vnt}")
print(f"  api/health: {vnt_api}")
R["vntworld"]=f"PASS {vnt}" if vnt.startswith("200") else f"FAIL:{vnt}"
R["vntworld_api"]=f"PASS" if vnt_api.startswith("200") else f"FAIL:{vnt_api}"

# ── Step 6: MSI Portal ──
print("[6] MSI portal...")
subprocess.run(["fuser","-k","8888/tcp"],capture_output=True);time.sleep(1)
if os.path.exists(MSI+"/portal_server.py"):
    subprocess.Popen(["/usr/bin/python3",MSI+"/portal_server.py"],
        stdout=open("/tmp/portal.log","w"),stderr=subprocess.STDOUT)
    time.sleep(5)
    st,sz=chk("http://127.0.0.1:8888/api/health",t=6)
    R["msi_api"]=f"PASS {sz}b" if st==200 else f"FAIL {st}"
    print(f"  MSI api: {st} {sz}b")
else:
    R["msi_api"]="FAIL:no portal_server"

# ── Step 7: M4 + Nextcloud ──
m4r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5","-o","BatchMode=yes",
    "Alias@192.168.10.94","curl -s http://localhost:3333/health"],capture_output=True,text=True,timeout=10)
R["m4"]="PASS" if "\"online\"" in m4r.stdout else "FAIL"
st_nc,_=chk("http://192.168.10.10/",t=5)
R["nextcloud"]=f"PASS" if st_nc in [200,301,302] else f"FAIL {st_nc}"

result=json.dumps({"ts":TSF,"results":R},indent=2)
try: gh_push("relay_result.json",result,"prox1 fix results")
except Exception as e: print(f"GH: {e}")
save(result)

passed=sum(1 for v in R.values() if "PASS" in str(v))
print("\n"+"="*55)
print(f"SCORE: {passed}/{len(R)}")
for k,v in R.items(): print(f"  {'PASS' if 'PASS' in str(v) else 'FAIL'} {k}: {str(v)[:60]}")
print("="*55)
