
import subprocess,json,base64,datetime,time,urllib.request,os

MSI='/home/k/vnt-web'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')

print(TSF,'FIX MSI PORTAL')

def chk(url,t=6):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'VNT/1.0'})
        with urllib.request.urlopen(req,timeout=t) as r: return r.status,len(r.read())
    except Exception as e: return 0,str(e)[:40]

# Read portal_server.py log
if os.path.exists('/tmp/portal.log'):
    print('Portal log:',open('/tmp/portal.log').read()[-200:])

# Kill and restart
subprocess.run(['fuser','-k','8888/tcp'],capture_output=True)
time.sleep(2)

ps=MSI+'/portal_server.py'
if os.path.exists(ps):
    p=subprocess.Popen(['/usr/bin/python3',ps],stdout=open('/tmp/portal.log','w'),stderr=subprocess.STDOUT)
    time.sleep(6)
    st,sz=chk('http://127.0.0.1:8888/',t=5)
    st2,sz2=chk('http://127.0.0.1:8888/api/health',t=6)
    print(f'8888: {st} {sz}b')
    print(f'api/health: {st2} {sz2}b')
    r1=f'{st}:{sz}'
    r2=f'{st2}:{sz2}'
    if st==0:
        print('Portal log:',open('/tmp/portal.log').read()[-300:])
else:
    r1='no portal_server.py'
    r2='skip'
    print('portal_server.py MISSING at',MSI)

# Test CT108 proxy (already working)
import urllib.request as ul
try:
    with ul.urlopen('http://192.168.10.13/api/health',timeout=6) as r: ct108_api=str(r.status)+':'+str(len(r.read()))
except Exception as e: ct108_api='FAIL:'+str(e)[:30]
try:
    with ul.urlopen('http://vntworld.com/api/health',timeout=8) as r: vnt_api=str(r.status)+':'+str(len(r.read()))
except Exception as e: vnt_api='FAIL:'+str(e)[:30]
print('CT108 api:',ct108_api)
print('vntworld api:',vnt_api)

result={'ts':TSF,'msi_8888':r1,'msi_api':r2,'ct108_api':ct108_api,'vntworld_api':vnt_api}
try:
    hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
    try:
        rr=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',headers=hdr)
        with urllib.request.urlopen(rr,timeout=6) as resp: sha=json.loads(resp.read()).get('sha','')
    except: sha=''
    data={'message':'msi fix result','content':base64.b64encode(json.dumps({'ts':TSF,'results':result}).encode()).decode()}
    if sha: data['sha']=sha
    req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
    with urllib.request.urlopen(req,timeout=10) as resp: print('GH:','OK' if 'content' in json.loads(resp.read()) else 'FAIL')
except Exception as e: print('GH error:',str(e)[:50])
print('DONE')
