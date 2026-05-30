import subprocess,json,base64,datetime,time,urllib.request,os
P1='192.168.10.19'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
def pct(ctid,c,t=12):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','root@'+P1,'pct exec '+str(ctid)+' -- bash -c '+json.dumps(c)],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def rx1(c,t=12):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','root@'+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
print(TSF,'RESTART HTTP.SERVER + SAVE RESULT')
# Kill and restart simple http.server
pct(108,'pkill -9 -f python3 2>/dev/null; fuser -k 80/tcp 2>/dev/null; sleep 2; cd /var/www/html && nohup python3 -m http.server 80 --bind 0.0.0.0 > /tmp/web.log 2>&1 & echo STARTED')
time.sleep(5)
r1=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/dashboard.html --connect-timeout 6')
r2=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://vntworld.com/dashboard.html --connect-timeout 8')
print('CT108:',r1)
print('vntworld:',r2)
# MSI portal
MSI='/home/k/vnt-web'
subprocess.run(['fuser','-k','8888/tcp'],capture_output=True);time.sleep(1)
if os.path.exists(MSI+'/portal_server.py'):
    subprocess.Popen(['/usr/bin/python3',MSI+'/portal_server.py'],stdout=open('/tmp/portal.log','w'),stderr=subprocess.STDOUT)
    time.sleep(4)
    try:
        with urllib.request.urlopen('http://127.0.0.1:8888/',timeout=4) as r: msi=str(r.status)+':'+str(len(r.read()))
    except Exception as e: msi='FAIL:'+str(e)[:20]
else: msi='FAIL:missing'
print('MSI:',msi)
R={'ct108':r1,'vntworld':r2,'msi':msi}
try:
    hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
    try:
        rr=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',headers=hdr)
        with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get('sha','')
    except: sha=''
    data={'message':'site status','content':base64.b64encode(json.dumps({'ts':TSF,'results':R}).encode()).decode()}
    if sha: data['sha']=sha
    req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
    with urllib.request.urlopen(req,timeout=8) as resp: print('GH:','OK' if 'content' in json.loads(resp.read()) else 'FAIL')
except Exception as e: print('GH error:',str(e)[:40])
print('DONE')