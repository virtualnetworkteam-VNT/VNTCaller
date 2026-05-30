
import subprocess, time, os, urllib.request, json, base64

WEB = '/home/k/vnt-web'
MP  = '/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'

def save(e):
    open(MP,'a').write('\n### Zeus Emergency ['+__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')+'\n'+e+'\n')

print('EMERGENCY: Restarting web server...')

# Kill and restart portal server
subprocess.run(['fuser','-k','8888/tcp'],capture_output=True)
time.sleep(1)

# Check portal_server.py exists
if not os.path.exists(WEB+'/portal_server.py'):
    print('portal_server.py MISSING - writing fallback...')
    fallback=[
        'import http.server,mimetypes,os,json,urllib.request,urllib.error,subprocess,time',
        'WEB="/home/k/vnt-web"',
        'M4="http://192.168.10.94:3333"',
        'class H(http.server.BaseHTTPRequestHandler):',
        '    def log_message(self,*a): pass',
        '    def cors(self):',
        '        self.send_header("Access-Control-Allow-Origin","*")',
        '        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")',
        '        self.send_header("Access-Control-Allow-Headers","Content-Type")',
        '    def do_OPTIONS(self):',
        '        self.send_response(200);self.cors();self.end_headers()',
        '    def proxy(self,p,body=None):',
        '        try:',
        '            req=urllib.request.Request(M4+p,data=body,headers={"Content-Type":"application/json"},method="POST" if body else "GET")',
        '            with urllib.request.urlopen(req,timeout=360) as r:',
        '                d=r.read();ct=r.headers.get("Content-Type","application/json")',
        '                self.send_response(200);self.send_header("Content-Type",ct);self.cors();self.send_header("Content-Length",str(len(d)));self.end_headers();self.wfile.write(d)',
        '        except Exception as e:',
        '            err=json.dumps({"status":"error","error":str(e)}).encode()',
        '            self.send_response(503);self.send_header("Content-Type","application/json");self.cors();self.send_header("Content-Length",str(len(err)));self.end_headers();self.wfile.write(err)',
        '    def do_GET(self):',
        '        p=self.path.split("?")[0]',
        '        if p.startswith("/api/"): self.proxy(p[4:]); return',
        '        if p=="/" or p=="": p="/index.html"',
        '        fp=WEB+p',
        '        if os.path.isdir(fp): fp=fp.rstrip("/")+"/index.html"',
        '        if os.path.exists(fp) and os.path.isfile(fp):',
        '            ct,_=mimetypes.guess_type(fp);ct=ct or "application/octet-stream"',
        '            d=open(fp,"rb").read()',
        '            self.send_response(200);self.send_header("Content-Type",ct);self.send_header("Content-Length",str(len(d)));self.cors();self.end_headers();self.wfile.write(d)',
        '        else: self.send_response(404);self.end_headers();self.wfile.write(b"Not found")',
        '    def do_POST(self):',
        '        n=int(self.headers.get("Content-Length",0))',
        '        body=self.rfile.read(n) if n else None',
        '        if self.path.startswith("/api/"): self.proxy(self.path[4:],body); return',
        '        self.send_response(404);self.end_headers();self.wfile.write(b"Not found")',
        'subprocess.run(["fuser","-k","8888/tcp"],capture_output=True)',
        'time.sleep(1)',
        'print("VNT Portal serving on :8888")',
        'http.server.HTTPServer(("0.0.0.0",8888),H).serve_forever()',
    ]
    open(WEB+'/portal_server.py','w').write('\n'.join(fallback))
    os.chmod(WEB+'/portal_server.py',0o755)

# Start server
lf=open('/tmp/portal.log','w')
subprocess.Popen(['/usr/bin/python3',WEB+'/portal_server.py'],stdout=lf,stderr=lf)
time.sleep(4)

# Verify
try:
    urllib.request.urlopen('http://127.0.0.1:8888/',timeout=5)
    print('Port 8888: ONLINE')
    save('Web server restarted by emergency relay')
except Exception as e:
    print('Port 8888 FAILED:',e)
    print('Log:',open('/tmp/portal.log').read()[-300:])
    save('Web server restart FAILED: '+str(e))

print('Done')
