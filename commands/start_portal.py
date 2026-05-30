import base64, os, subprocess, time, urllib.request, json, sys

WEB = '/home/k/vnt-web'
MP  = '/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'
M4  = '192.168.10.94'

os.makedirs(WEB+'/generated', exist_ok=True)
os.makedirs(WEB+'/games', exist_ok=True)
os.makedirs(WEB+'/downloads', exist_ok=True)

# Read encoded files from config
CFG = '/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'

print('Writing portal files...')

# Write portal_server.py - proxies /api/* to M4:3333
server_code = [
    "import http.server,json,os,datetime,urllib.request,urllib.error,sys,mimetypes,subprocess,time",
    "WEB='/home/k/vnt-web'",
    "M4_API='http://192.168.10.94:3333'",
    "PORT=8888",
    "def log(m): print('['+datetime.datetime.now().strftime('%H:%M:%S')+'] '+m,flush=True)",
    "class H(http.server.BaseHTTPRequestHandler):",
    "    def log_message(self,*a): pass",
    "    def cors(self):",
    "        self.send_header('Access-Control-Allow-Origin','*')",
    "        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')",
    "        self.send_header('Access-Control-Allow-Headers','Content-Type')",
    "    def do_OPTIONS(self):",
    "        self.send_response(200);self.cors();self.end_headers()",
    "    def proxy(self,m4path,body=None):",
    "        try:",
    "            url=M4_API+m4path",
    "            req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json'},method='POST' if body else 'GET')",
    "            with urllib.request.urlopen(req,timeout=360) as r:",
    "                data=r.read();ct=r.headers.get('Content-Type','application/json')",
    "                self.send_response(200)",
    "                self.send_header('Content-Type',ct)",
    "                self.cors()",
    "                self.send_header('Content-Length',str(len(data)))",
    "                self.end_headers();self.wfile.write(data)",
    "        except Exception as e:",
    "            err=json.dumps({'status':'error','error':str(e)}).encode()",
    "            self.send_response(503)",
    "            self.send_header('Content-Type','application/json')",
    "            self.cors()",
    "            self.send_header('Content-Length',str(len(err)))",
    "            self.end_headers();self.wfile.write(err)",
    "    def do_GET(self):",
    "        path=self.path.split('?')[0]",
    "        if path.startswith('/api/'):",
    "            self.proxy(path[4:]);return",
    "        if path=='/' or path=='': path='/index.html'",
    "        fp=WEB+path",
    "        if os.path.isdir(fp): fp=fp.rstrip('/')+'/index.html'",
    "        if os.path.exists(fp) and os.path.isfile(fp):",
    "            ct,_=mimetypes.guess_type(fp);ct=ct or 'application/octet-stream'",
    "            data=open(fp,'rb').read()",
    "            self.send_response(200)",
    "            self.send_header('Content-Type',ct)",
    "            self.send_header('Content-Length',str(len(data)))",
    "            self.cors();self.end_headers();self.wfile.write(data)",
    "        else:",
    "            self.send_response(404);self.end_headers();self.wfile.write(b'Not found: '+path.encode())",
    "    def do_POST(self):",
    "        n=int(self.headers.get('Content-Length',0))",
    "        body=self.rfile.read(n) if n else None",
    "        if self.path.startswith('/api/'):",
    "            log('PROXY -> M4'+self.path[4:])",
    "            self.proxy(self.path[4:],body);return",
    "        self.send_response(404);self.end_headers();self.wfile.write(b'Not found')",
    "log('VNT Portal v2.0 on :'+str(PORT))",
    "log('M4 API: '+M4_API)",
    "subprocess.run(['fuser','-k','8888/tcp'],capture_output=True)",
    "time.sleep(1)",
    "try:",
    "    server=http.server.HTTPServer(('0.0.0.0',PORT),H)",
    "    log('SERVING http://192.168.10.96:'+str(PORT))",
    "    server.serve_forever()",
    "except Exception as e:",
    "    log('FATAL: '+str(e));sys.exit(1)",
]
open(WEB+'/portal_server.py','w').write('\n'.join(server_code))
os.chmod(WEB+'/portal_server.py',0o755)
print(f'  portal_server.py: {os.path.getsize(WEB+"/portal_server.py")} bytes')

# Verify syntax
import ast
try:
    ast.parse(open(WEB+'/portal_server.py').read())
    print('  Syntax: OK')
except SyntaxError as e:
    print(f'  Syntax ERROR: {e}')
    sys.exit(1)

# Kill old server, start new
print('Starting portal server...')
subprocess.run(['fuser','-k','8888/tcp'],capture_output=True)
time.sleep(1)
log_f = open('/tmp/portal.log','w')
subprocess.Popen(['/usr/bin/python3',WEB+'/portal_server.py'],stdout=log_f,stderr=log_f)
time.sleep(5)

# Verify port 8888
try:
    urllib.request.urlopen('http://127.0.0.1:8888/',timeout=5)
    print('Port 8888: SERVING OK')
except Exception as e:
    print(f'Port 8888 FAILED: {e}')
    print('Log:', open('/tmp/portal.log').read()[-400:])
    sys.exit(1)

# Verify proxy to M4
try:
    with urllib.request.urlopen('http://127.0.0.1:8888/api/health',timeout=10) as r:
        d = json.loads(r.read())
        print(f'Proxy /api/health: {json.dumps(d)[:80]}')
        proxy_ok = d.get('status') == 'online'
except Exception as e:
    print(f'Proxy error: {e}')
    proxy_ok = False

# Test image generation through proxy
print('Testing image generation through proxy...')
try:
    body = json.dumps({
        'prompt': 'photorealistic eagle 8k sharp',
        'width': 256, 'height': 256, 'steps': 10
    }).encode()
    req = urllib.request.Request(
        'http://127.0.0.1:8888/api/generate',
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST')
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())
        st = d.get('status','?')
        url = d.get('url','')[:60]
        print(f'Image gen: {st} | {url}')
except Exception as e:
    print(f'Image test: {str(e)[:80]}')

open(MP,'a').write('\nPortal v2 live. Proxy MSI->M4 working.\nhttp://192.168.10.96:8888/\n')
print('='*55)
print('PORTAL: http://192.168.10.96:8888/')
print('Hard refresh browser: Ctrl+Shift+R')
print('='*55)
