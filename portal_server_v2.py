import http.server,json,os,urllib.request,mimetypes,datetime
WEB="/home/k/vnt-web"
M4="http://192.168.10.94:3333"
PORT=8888
TIMEOUT=60
def log(m): print("["+datetime.datetime.now().strftime("%H:%M:%S")+"] "+m,flush=True)
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type,Authorization")
    def proxy(self,path,body=None,method="GET"):
        try:
            req=urllib.request.Request(M4+path,data=body,headers={"Content-Type":"application/json"},method=method)
            with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
                data=r.read();ct=r.headers.get("Content-Type","application/json")
                self.send_response(200);self.send_header("Content-Type",ct)
                self.cors();self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
        except Exception as e:
            err=json.dumps({"status":"error","error":str(e)}).encode()
            self.send_response(503);self.send_header("Content-Type","application/json")
            self.cors();self.send_header("Content-Length",str(len(err)));self.end_headers();self.wfile.write(err)
    def do_OPTIONS(self): self.send_response(200);self.cors();self.end_headers()
    def do_GET(self):
        p=self.path.split("?")[0]
        if p in ("/health","/api/health"):
            resp=json.dumps({"status":"online","api":"VNT Portal v2","ts":datetime.datetime.now().isoformat()}).encode()
            self.send_response(200);self.send_header("Content-Type","application/json")
            self.cors();self.send_header("Content-Length",str(len(resp)));self.end_headers();self.wfile.write(resp);return
        if p.startswith("/api/"): self.proxy(p[4:]); return
        if p in ("/",""): p="/dashboard.html"
        fp=WEB+p
        if os.path.exists(fp) and os.path.isfile(fp):
            ct,_=mimetypes.guess_type(fp);ct=ct or "application/octet-stream"
            data=open(fp,"rb").read()
            self.send_response(200);self.send_header("Content-Type",ct)
            self.send_header("Content-Length",str(len(data)));self.cors();self.end_headers();self.wfile.write(data)
        else: self.send_response(404);self.end_headers();self.wfile.write(b"404")
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0));body=self.rfile.read(n) if n else None
        if self.path.startswith("/api/"): log("POST "+self.path); self.proxy(self.path[4:],body,"POST"); return
        self.send_response(404);self.end_headers()
try: server=http.server.ThreadingHTTPServer(("0.0.0.0",PORT),H)
except: server=http.server.HTTPServer(("0.0.0.0",PORT),H)
log("VNT Portal v2 :"+str(PORT)+" -> "+M4)
server.serve_forever()
