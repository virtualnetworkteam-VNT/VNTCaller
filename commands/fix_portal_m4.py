import subprocess,datetime,json,urllib.request,time,os
MSI='/home/k/vnt-web'
M4='192.168.10.94'
PY='/Users/alias/miniforge3/envs/vnt/bin/python'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
def chk(url,t=6):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'VNT/1.0'})
        with urllib.request.urlopen(req,timeout=t) as r: return r.status,len(r.read())
    except Exception as e: return 0,str(e)[:40]
def gh_save(R):
    try:
        hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
        try:
            rr=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get('sha','')
        except: sha=''
        data={'message':'fix portal m4','content':__import__('base64').b64encode(json.dumps({'ts':TSF,'results':R}).encode()).decode()}
        if sha: data['sha']=sha
        req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
        with urllib.request.urlopen(req,timeout=8) as resp: return 'content' in json.loads(resp.read())
    except Exception as e: print('GH:',str(e)[:30]); return False
print(TSF,'DIAG + FIX PORTAL + M4')
R={}
# Check portal log
if os.path.exists('/tmp/portal.log'):
    log=open('/tmp/portal.log').read()[-400:]
    print('Portal log:',log)
    R['portal_log']=log[:150]
# Check portal_server.py exists and its content
ps_exists=os.path.exists(MSI+'/portal_server.py')
print(f'portal_server.py exists: {ps_exists}')
if ps_exists:
    size=os.path.getsize(MSI+'/portal_server.py')
    print(f'Size: {size} bytes')
    # Check for syntax errors
    result=subprocess.run(['/usr/bin/python3','-m','py_compile',MSI+'/portal_server.py'],capture_output=True,text=True)
    print(f'Syntax check: {result.returncode} {result.stderr[:100]}')
    R['portal_syntax']='OK' if result.returncode==0 else result.stderr[:50]
# Kill and restart portal
subprocess.run(['fuser','-k','8888/tcp'],capture_output=True)
time.sleep(2)
proc=subprocess.Popen(['/usr/bin/python3',MSI+'/portal_server.py'],stdout=open('/tmp/portal.log','w'),stderr=subprocess.STDOUT)
time.sleep(6)
st,sz=chk('http://127.0.0.1:8888/',t=5)
R['msi_8888']=f'PASS {sz}b' if st==200 else f'FAIL {st}'
print(f'MSI 8888: {st} {sz}b')
st2,sz2=chk('http://127.0.0.1:8888/api/health',t=8)
R['msi_api']=f'PASS {sz2}b' if st2==200 else f'FAIL {st2}'
print(f'MSI api: {st2} {sz2}b')
# If still failing check log
if st==0:
    if os.path.exists('/tmp/portal.log'):
        print('Error log:',open('/tmp/portal.log').read()[-300:])
# Restart M4 API
print('Checking M4...')
m4r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','-o','BatchMode=yes','Alias@'+M4,'curl -s http://localhost:3333/health 2>/dev/null || echo OFFLINE'],capture_output=True,text=True,timeout=12)
m4_health=m4r.stdout.strip()
print(f'M4 health: {m4_health[:80]}')
R['m4_health']=m4_health[:60]
if 'online' not in m4_health:
    print('Restarting M4 API...')
    subprocess.Popen(['ssh','-o','StrictHostKeyChecking=no','-o','BatchMode=yes','Alias@'+M4,f'pkill -f studio_api 2>/dev/null; sleep 2; nohup {PY} /Users/alias/vnt-studio/studio_api.py > /tmp/studio.log 2>&1 &'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(8)
    m4r2=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','-o','BatchMode=yes','Alias@'+M4,'curl -s http://localhost:3333/health 2>/dev/null'],capture_output=True,text=True,timeout=12)
    R['m4_after_restart']=m4r2.stdout.strip()[:60]
    print(f'M4 after restart: {m4r2.stdout.strip()[:60]}')
gh_save(R)
for k,v in R.items(): print(f'  {k}: {str(v)[:60]}')
print('DONE')