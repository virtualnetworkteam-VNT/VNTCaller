import subprocess,datetime,json,urllib.request,time,os
MSI='/home/k/vnt-web'
M4='192.168.10.94'
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
        data={'message':'portal diag fix','content':__import__('base64').b64encode(json.dumps({'ts':TSF,'results':R}).encode()).decode()}
        if sha: data['sha']=sha
        req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
        with urllib.request.urlopen(req,timeout=8) as resp: return 'content' in json.loads(resp.read())
    except Exception as e: print('GH:',str(e)[:30]); return False
print(TSF,'PORTAL DIAG + HARD FIX')
R={}
# What's on port 8888?
ss=subprocess.run(['ss','-tlnp'],capture_output=True,text=True)
port_info=[l for l in ss.stdout.split('\n') if '8888' in l]
print('Port 8888:',port_info)
R['port_8888']=str(port_info)[:80]
# Kill everything on 8888
subprocess.run(['fuser','-k','-9','8888/tcp'],capture_output=True)
time.sleep(2)
# Also kill by name
subprocess.run(['pkill','-9','-f','portal_server'],capture_output=True)
time.sleep(2)
# Read portal_server.py first 30 lines to see what's happening
ps_head=open(MSI+'/portal_server.py').read()[:800] if os.path.exists(MSI+'/portal_server.py') else 'not found'
print('portal_server.py head:',ps_head[:200])
R['portal_head']=ps_head[:150]
# Try to start it and wait longer
env={'PATH':'/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'}
proc=subprocess.Popen(['/usr/bin/python3',MSI+'/portal_server.py'],stdout=open('/tmp/portal.log','w'),stderr=subprocess.STDOUT,env=env)
time.sleep(10)
# Check log
log_content=open('/tmp/portal.log').read() if os.path.exists('/tmp/portal.log') else ''
print('Log (last 400):')
print(log_content[-400:])
R['portal_log2']=log_content[-200:]
# Check if port is now open
ss2=subprocess.run(['ss','-tlnp'],capture_output=True,text=True)
port_now=[l for l in ss2.stdout.split('\n') if '8888' in l]
print('Port 8888 now:',port_now)
R['port_now']=str(port_now)[:80]
# Test API
st,sz=chk('http://127.0.0.1:8888/api/health',t=8)
R['msi_api']=f'PASS {sz}b' if st==200 else f'FAIL {st}'
print(f'API health: {st} {sz}b')
# If still failing, check if port 8888 is firewall blocked
if st==0:
    fw=subprocess.run(['iptables','-L','-n'],capture_output=True,text=True)
    fw_8888=[l for l in fw.stdout.split('\n') if '8888' in l]
    print('Firewall 8888:',fw_8888)
    R['firewall']=str(fw_8888)[:60]
gh_save(R)
for k,v in R.items(): print(f'  {k}: {str(v)[:80]}')
print('DONE')