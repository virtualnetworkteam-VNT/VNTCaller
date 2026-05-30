import subprocess, datetime, json, urllib.request, time, re, base64, os

P1  = "192.168.10.19"
WEB = "/var/www/html"
MSI = "/home/k/vnt-web"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
GH  = open("/home/k/vnt-config-gh.txt").read().strip()
REPO= "virtualnetworkteam-VNT/VNTCaller"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx1(c,t=20):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=6","root@"+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def scp_p1(l,r,t=20):
    return subprocess.run(["scp","-o","StrictHostKeyChecking=no",l,"root@"+P1+":"+r],capture_output=True,timeout=t).returncode==0
def gh_api(path):
    hdr={"Authorization":"Bearer "+GH,"Accept":"application/vnd.github.v3+json"}
    req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",headers=hdr)
    return json.loads(urllib.request.urlopen(req,timeout=30).read())
def gh_save(R):
    try:
        hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
        try:
            rr=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get("sha","")
        except: sha=""
        data={"message":"login+proxy","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp: return "content" in json.loads(resp.read())
    except Exception as e: print("GH:",str(e)[:30]); return False

print(TSF,"DEPLOY LOGIN + API PROXY")
R={}

# 1. Get login.html and restore passwords
print("[1] Deploying login.html...")
fd=gh_api("login_v2.html")
raw=base64.b64decode(fd["content"].replace("\n","")).decode()
raw=raw.replace("USER_PASS2","App159earance.VnT")
raw=raw.replace("USER_PASS3","0568116899")
raw=raw.replace("USER_PASS","116899")
open("/tmp/login_v2.html","wb").write(raw.encode())
ok=scp_p1("/tmp/login_v2.html","/tmp/login_v2.html")
push=rx1("pct push 108 /tmp/login_v2.html "+WEB+"/login.html",t=15)
sz=rx1("pct exec 108 -- stat -c %s "+WEB+"/login.html 2>/dev/null")
print(f"  login.html: {sz}b")
R["login"]=f"PASS {sz}b" if int(sz or 0)>5000 else f"FAIL {sz}b"

# 2. Install CT108 proxy server
print("[2] Installing CT108 proxy server...")
proxy_code=b"""import http.server,json,os,urllib.request,urllib.error,mimetypes,datetime
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
                self.send_response(200);self.send_header("Content-Type",ct);self.cors()
                self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
        except Exception as e:
            err=json.dumps({"status":"error","error":str(e)}).encode()
            self.send_response(503);self.send_header("Content-Type","application/json");self.cors()
            self.send_header("Content-Length",str(len(err)));self.end_headers();self.wfile.write(err)
    def do_OPTIONS(self): self.send_response(200);self.cors();self.end_headers()
    def do_GET(self):
        p=self.path.split("?")[0]
        if p.startswith("/api/"): self.proxy(p[4:]); return
        if p=="/" or p=="": p="/dashboard.html"
        fp=WEB+p
        if os.path.isdir(fp): fp=fp.rstrip("/")+"/index.html"
        if os.path.exists(fp) and os.path.isfile(fp):
            ct,_=mimetypes.guess_type(fp);ct=ct or "application/octet-stream"
            data=open(fp,"rb").read()
            self.send_response(200);self.send_header("Content-Type",ct)
            self.send_header("Content-Length",str(len(data)));self.cors();self.end_headers();self.wfile.write(data)
        else: self.send_response(404);self.end_headers();self.wfile.write(b"404")
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0))
        body=self.rfile.read(n) if n else None
        if self.path.startswith("/api/"): log("POST "+self.path[4:]); self.proxy(self.path[4:],body,"POST"); return
        self.send_response(404);self.end_headers();self.wfile.write(b"404")
try: server=http.server.ThreadingHTTPServer(("0.0.0.0",PORT),H)
except: server=http.server.HTTPServer(("0.0.0.0",PORT),H)
log("VNT CT108 :"+str(PORT)+" -> "+M4)
server.serve_forever()
"""
open("/tmp/ct108proxy.py","wb").write(proxy_code)
ok2=scp_p1("/tmp/ct108proxy.py","/tmp/ct108proxy.py")
push2=rx1("pct push 108 /tmp/ct108proxy.py /tmp/ct108proxy.py",t=12)
rx1("pct exec 108 -- bash -c 'pkill -9 -f http.server 2>/dev/null; pkill -9 -f ct108proxy 2>/dev/null; fuser -k 80/tcp 2>/dev/null; sleep 2; nohup python3 /tmp/ct108proxy.py > /tmp/proxy.log 2>&1 &'")
import time; time.sleep(5)
api_test=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' http://192.168.10.13/api/health --connect-timeout 6")
ct_test=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' http://192.168.10.13/ --connect-timeout 6")
print(f"  CT108 root:{ct_test}  api:{api_test}")
R["ct108_web"]=ct_test; R["ct108_api"]=api_test

vnt=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' https://vntworld.com/ --connect-timeout 8")
vnt_api=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' https://vntworld.com/api/health --connect-timeout 8")
print(f"  vntworld:{vnt}  api:{vnt_api}")
R["vntworld"]=vnt; R["vntworld_api"]=vnt_api

try: open(MP,"a").write("\n### LoginProxy ["+TSF+"]\nlogin.html: local auth\nCT108 proxy: /api/* -> M4\n")
except: pass
gh_save(R)
for k,v in R.items(): print(f"  {'OK' if '200' in str(v) or 'PASS' in str(v) else 'FL'} {k}: {str(v)[:60]}")
print("DONE")
