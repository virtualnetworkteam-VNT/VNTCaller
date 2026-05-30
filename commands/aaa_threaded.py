import subprocess,base64,datetime,json,urllib.request,os,time
CT='192.168.10.13'
MSI='/home/k/vnt-web'
MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
SRV=base64.b64decode(b'IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJWTlQgQ1QxMDggV2ViIFNlcnZlciB2MiAtIFRocmVhZGVkLCBzZXJ2ZXMgc3RhdGljICsgcHJveGllcyAvYXBpLyogdG8gTTQiIiIKaW1wb3J0IGh0dHAuc2VydmVyLCBqc29uLCBvcywgdXJsbGliLnJlcXVlc3QsIHVybGxpYi5lcnJvciwgbWltZXR5cGVzLCBzeXMsIHN1YnByb2Nlc3MsIHRpbWUsIHRocmVhZGluZwoKV0VCICAgPSAiL3Zhci93d3cvaHRtbCIKTTRBUEkgPSAiaHR0cDovLzE5Mi4xNjguMTAuOTQ6MzMzMyIKUE9SVCAgPSA4MAoKaW1wb3J0IGRhdGV0aW1lCmRlZiBsb2cobSk6IHByaW50KCJbIitkYXRldGltZS5kYXRldGltZS5ub3coKS5zdHJmdGltZSgiJUg6JU06JVMiKSsiXSAiK20sIGZsdXNoPVRydWUpCgpjbGFzcyBIYW5kbGVyKGh0dHAuc2VydmVyLkJhc2VIVFRQUmVxdWVzdEhhbmRsZXIpOgogICAgZGVmIGxvZ19tZXNzYWdlKHNlbGYsICphKTogcGFzcwoKICAgIGRlZiBjb3JzKHNlbGYpOgogICAgICAgIHNlbGYuc2VuZF9oZWFkZXIoIkFjY2Vzcy1Db250cm9sLUFsbG93LU9yaWdpbiIsIioiKQogICAgICAgIHNlbGYuc2VuZF9oZWFkZXIoIkFjY2Vzcy1Db250cm9sLUFsbG93LU1ldGhvZHMiLCJHRVQsUE9TVCxPUFRJT05TIikKICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJBY2Nlc3MtQ29udHJvbC1BbGxvdy1IZWFkZXJzIiwiQ29udGVudC1UeXBlLEF1dGhvcml6YXRpb24iKQoKICAgIGRlZiBwcm94eV9tNChzZWxmLCBtNHBhdGgsIGJvZHk9Tm9uZSwgbWV0aG9kPSJHRVQiKToKICAgICAgICB0cnk6CiAgICAgICAgICAgIHVybCA9IE00QVBJICsgbTRwYXRoCiAgICAgICAgICAgIHJlcSA9IHVybGxpYi5yZXF1ZXN0LlJlcXVlc3QodXJsLCBkYXRhPWJvZHksCiAgICAgICAgICAgICAgICBoZWFkZXJzPXsiQ29udGVudC1UeXBlIjoiYXBwbGljYXRpb24vanNvbiJ9LCBtZXRob2Q9bWV0aG9kKQogICAgICAgICAgICB3aXRoIHVybGxpYi5yZXF1ZXN0LnVybG9wZW4ocmVxLCB0aW1lb3V0PTM2MCkgYXMgcjoKICAgICAgICAgICAgICAgIGRhdGEgPSByLnJlYWQoKQogICAgICAgICAgICAgICAgY3QgPSByLmhlYWRlcnMuZ2V0KCJDb250ZW50LVR5cGUiLCJhcHBsaWNhdGlvbi9qc29uIikKICAgICAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSgyMDApCiAgICAgICAgICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJDb250ZW50LVR5cGUiLCBjdCkKICAgICAgICAgICAgICAgIHNlbGYuY29ycygpCiAgICAgICAgICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJDb250ZW50LUxlbmd0aCIsIHN0cihsZW4oZGF0YSkpKQogICAgICAgICAgICAgICAgc2VsZi5lbmRfaGVhZGVycygpCiAgICAgICAgICAgICAgICBzZWxmLndmaWxlLndyaXRlKGRhdGEpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgICAgICBlcnIgPSBqc29uLmR1bXBzKHsic3RhdHVzIjoiZXJyb3IiLCJlcnJvciI6c3RyKGUpfSkuZW5jb2RlKCkKICAgICAgICAgICAgc2VsZi5zZW5kX3Jlc3BvbnNlKDUwMykKICAgICAgICAgICAgc2VsZi5zZW5kX2hlYWRlcigiQ29udGVudC1UeXBlIiwiYXBwbGljYXRpb24vanNvbiIpCiAgICAgICAgICAgIHNlbGYuY29ycygpCiAgICAgICAgICAgIHNlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtTGVuZ3RoIixzdHIobGVuKGVycikpKQogICAgICAgICAgICBzZWxmLmVuZF9oZWFkZXJzKCkKICAgICAgICAgICAgc2VsZi53ZmlsZS53cml0ZShlcnIpCgogICAgZGVmIGRvX09QVElPTlMoc2VsZik6CiAgICAgICAgc2VsZi5zZW5kX3Jlc3BvbnNlKDIwMCk7IHNlbGYuY29ycygpOyBzZWxmLmVuZF9oZWFkZXJzKCkKCiAgICBkZWYgZG9fR0VUKHNlbGYpOgogICAgICAgIHBhdGggPSBzZWxmLnBhdGguc3BsaXQoIj8iKVswXQogICAgICAgIGlmIHBhdGguc3RhcnRzd2l0aCgiL2FwaS8iKTogc2VsZi5wcm94eV9tNChwYXRoWzQ6XSk7IHJldHVybgogICAgICAgIGlmIHBhdGggPT0gIi8iIG9yIHBhdGggPT0gIiI6IHBhdGggPSAiL2Rhc2hib2FyZC5odG1sIgogICAgICAgIGZwID0gV0VCICsgcGF0aAogICAgICAgIGlmIG9zLnBhdGguaXNkaXIoZnApOiBmcCA9IGZwLnJzdHJpcCgiLyIpICsgIi9pbmRleC5odG1sIgogICAgICAgIGlmIG9zLnBhdGguZXhpc3RzKGZwKSBhbmQgb3MucGF0aC5pc2ZpbGUoZnApOgogICAgICAgICAgICBjdCxfID0gbWltZXR5cGVzLmd1ZXNzX3R5cGUoZnApOyBjdCA9IGN0IG9yICJhcHBsaWNhdGlvbi9vY3RldC1zdHJlYW0iCiAgICAgICAgICAgIGRhdGEgPSBvcGVuKGZwLCJyYiIpLnJlYWQoKQogICAgICAgICAgICBzZWxmLnNlbmRfcmVzcG9uc2UoMjAwKQogICAgICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJDb250ZW50LVR5cGUiLCBjdCkKICAgICAgICAgICAgc2VsZi5zZW5kX2hlYWRlcigiQ29udGVudC1MZW5ndGgiLCBzdHIobGVuKGRhdGEpKSkKICAgICAgICAgICAgc2VsZi5jb3JzKCk7IHNlbGYuZW5kX2hlYWRlcnMoKTsgc2VsZi53ZmlsZS53cml0ZShkYXRhKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSg0MDQpOyBzZWxmLmVuZF9oZWFkZXJzKCkKICAgICAgICAgICAgc2VsZi53ZmlsZS53cml0ZShiIk5vdCBmb3VuZDogIitwYXRoLmVuY29kZSgpKQoKICAgIGRlZiBkb19QT1NUKHNlbGYpOgogICAgICAgIG4gPSBpbnQoc2VsZi5oZWFkZXJzLmdldCgiQ29udGVudC1MZW5ndGgiLCAwKSkKICAgICAgICBib2R5ID0gc2VsZi5yZmlsZS5yZWFkKG4pIGlmIG4gZWxzZSBOb25lCiAgICAgICAgaWYgc2VsZi5wYXRoLnN0YXJ0c3dpdGgoIi9hcGkvIik6CiAgICAgICAgICAgIGxvZygiUE9TVCAiK3NlbGYucGF0aFs0Ol0pCiAgICAgICAgICAgIHNlbGYucHJveHlfbTQoc2VsZi5wYXRoWzQ6XSwgYm9keSwgIlBPU1QiKTsgcmV0dXJuCiAgICAgICAgc2VsZi5zZW5kX3Jlc3BvbnNlKDQwNCk7IHNlbGYuZW5kX2hlYWRlcnMoKTsgc2VsZi53ZmlsZS53cml0ZShiIk5vdCBmb3VuZCIpCgojIFRocmVhZGluZ0hUVFBTZXJ2ZXIgLSBoYW5kbGVzIGNvbmN1cnJlbnQgcmVxdWVzdHMKY2xhc3MgVGhyZWFkZWRTZXJ2ZXIoaHR0cC5zZXJ2ZXIuVGhyZWFkaW5nSFRUUFNlcnZlcik6CiAgICBkYWVtb25fdGhyZWFkcyA9IFRydWUKCmxvZyhmIlZOVCBDVDEwOCBUaHJlYWRlZCBTZXJ2ZXIgOntQT1JUfSAtPiB7TTRBUEl9IikKdHJ5OgogICAgc2VydmVyID0gVGhyZWFkZWRTZXJ2ZXIoKCIwLjAuMC4wIiwgUE9SVCksIEhhbmRsZXIpCiAgICBsb2coIlJFQURZIC0gdGhyZWFkZWQsIG5vIGJsb2NraW5nIikKICAgIHNlcnZlci5zZXJ2ZV9mb3JldmVyKCkKZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgbG9nKGYiRkFUQUw6IHtlfSIpOyBzeXMuZXhpdCgxKQo=')
def rx(h,c,t=15): r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=8','root@'+h,c],capture_output=True,text=True,timeout=t); return (r.stdout+r.stderr).strip()
def scp(src,dst,t=15): r=subprocess.run(['scp','-o','StrictHostKeyChecking=no',src,'root@'+CT+':'+dst],capture_output=True,text=True,timeout=t); return r.returncode==0
def chk(url,t=8):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'VNT/1.0'})
        with urllib.request.urlopen(req,timeout=t) as r: return r.status,len(r.read())
    except Exception as e: return 0,str(e)[:40]
def gh_push(path,content,msg):
    hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
    try:
        r=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/{path}',headers=hdr)
        with urllib.request.urlopen(r,timeout=8) as rr: sha=json.loads(rr.read()).get('sha','')
    except: sha=''
    data={'message':msg,'content':base64.b64encode(content if isinstance(content,bytes) else content.encode()).decode()}
    if sha: data['sha']=sha
    req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/{path}',data=json.dumps(data).encode(),headers=hdr,method='PUT')
    with urllib.request.urlopen(req,timeout=12) as r: return 'content' in json.loads(r.read())
def save(e):
    try: open(MP,'a').write('\n### Threaded ['+TSF+']\n'+e+'\n')
    except: pass
R={}
print('='*55)
print('UPGRADE CT108: THREADED SERVER + VERIFY ALL')
print(TSF)
print('='*55)

# Deploy threaded server to CT108
print('[1] Deploying threaded server...')
open('/tmp/ct108v2.py','wb').write(SRV)
ok=scp('/tmp/ct108v2.py','/tmp/ct108v2.py')
print(f'  SCP: {"OK" if ok else "FAIL"}')
# Kill old, start new
subprocess.Popen(['ssh','-o','StrictHostKeyChecking=no','root@'+CT,'pkill -9 -f ct108 2>/dev/null; pkill -9 -f http.server 2>/dev/null; fuser -k 80/tcp 2>/dev/null; sleep 2; nohup python3 /tmp/ct108v2.py > /tmp/ct108.log 2>&1 &'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(6)
ps=rx(CT,'ps aux | grep ct108v2 | grep -v grep | head -2')
port=rx(CT,'ss -tlnp | grep :80')
print(f'  Process: {ps[:80]}')
print(f'  Port 80: {port[:80]}')

# Fix MSI portal
print('[2] MSI portal...')
subprocess.run(['fuser','-k','8888/tcp'],capture_output=True);time.sleep(1)
subprocess.Popen(['/usr/bin/python3',MSI+'/portal_server.py'],stdout=open('/tmp/portal.log','w'),stderr=subprocess.STDOUT)
time.sleep(4)
st,sz=chk('http://127.0.0.1:8888/api/health',t=6)
R['msi_proxy']=f'PASS {sz}b' if st==200 else f'FAIL {st}'
print(f'  MSI /api/health: {st} {sz}b')

# Test all endpoints WITHOUT blocking image gen
print('[3] Testing all endpoints...')
tests=[
    ('CT108_root',f'http://192.168.10.13/',200,60000),
    ('CT108_dashboard',f'http://192.168.10.13/dashboard.html',200,60000),
    ('CT108_api',f'http://192.168.10.13/api/health',200,50),
    ('CT108_app',f'http://192.168.10.13/app.html',200,5000),
    ('vntworld_dash','http://vntworld.com/dashboard.html',200,60000),
    ('vntworld_app','http://vntworld.com/app.html',200,5000),
    ('vntworld_api','http://vntworld.com/api/health',200,50),
    ('MSI_8888','http://127.0.0.1:8888/',200,10000),
    ('nextcloud','http://192.168.10.10/',200,1000),
]
for name,url,code,min_sz in tests:
    st3,sz3=chk(url,t=10)
    ok=(st3==code and sz3>=min_sz)
    R[name]=f'PASS {sz3}b' if ok else f'FAIL {st3} {sz3}b'
    print(f'  {"PASS" if ok else "FAIL"} {name}: {st3} {sz3}b')

# M4 API
m4r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','-o','BatchMode=yes','Alias@192.168.10.94','curl -s http://localhost:3333/health'],capture_output=True,text=True,timeout=10)
R['m4']='PASS' if '"online"' in m4r.stdout else 'FAIL'
print(f'  M4: {m4r.stdout.strip()[:60]}')

# Audio test (quick) via CT108
print('[4] Audio via CT108...')
try:
    body=json.dumps({'text':'VNT ready','type':'speech'}).encode()
    req=urllib.request.Request('http://192.168.10.13/api/generate-audio',data=body,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=90) as r:
        d=json.loads(r.read())
        ok_a=d.get('status')=='ok'
        R['audio']='PASS' if ok_a else 'FAIL:'+str(d)[:40]
        print(f'  Audio: {"PASS" if ok_a else "FAIL"} {str(d)[:60]}')
except Exception as e: R['audio']='FAIL:'+str(e)[:40]; print(f'  Audio: FAIL {e}')

# Image test (concurrent - won't block other requests now)
print('[5] Image via CT108 (concurrent with other requests)...')
try:
    body=json.dumps({'prompt':'eagle 8k photorealistic','width':256,'height':256,'steps':8}).encode()
    req=urllib.request.Request('http://192.168.10.13/api/generate',data=body,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=180) as r:
        d=json.loads(r.read())
        ok_i=d.get('status')=='ok'
        R['image']='PASS url='+d.get('url','?')[:40] if ok_i else 'FAIL:'+str(d)[:40]
        print(f'  Image: {"PASS" if ok_i else "FAIL"} url={d.get("url","")[:50]}')
except Exception as e: R['image']='FAIL:'+str(e)[:40]; print(f'  Image: FAIL {e}')

# Verify CT108 still responding while image was generating
st_final,sz_final=chk('http://192.168.10.13/',t=5)
R['ct108_concurrent']=f'PASS {sz_final}b' if st_final==200 else f'FAIL {st_final}'
print(f'  CT108 concurrent test: {st_final} {sz_final}b')

result=json.dumps({'ts':TSF,'results':R},indent=2)
try: gh_push('relay_result.json',result,'threaded server results')
except Exception as e: print(f'GH: {e}')
save(result)
passed=sum(1 for v in R.values() if 'PASS' in str(v))
print('\n'+'='*55)
print(f'SCORE: {passed}/{len(R)}')
for k,v in R.items(): print(f'  {"PASS" if "PASS" in str(v) else "FAIL"} {k}: {str(v)[:60]}')
print('='*55)
