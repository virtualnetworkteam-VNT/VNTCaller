import subprocess,json,base64,datetime,time,urllib.request,os
P1='192.168.10.19'
M4='192.168.10.94'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')

# Check M4 directly from MSI
print('[1] M4 direct test from MSI...')
try:
    with urllib.request.urlopen('http://'+M4+':3333/health',timeout=10) as r:
        d=json.loads(r.read())
        print(f'  M4 direct: {json.dumps(d)[:80]}')
        m4_ok=d.get('status')=='online'
except Exception as e:
    print(f'  M4 direct: FAIL {str(e)[:60]}')
    m4_ok=False

# Check portal log
print('[2] Portal log...')
if os.path.exists('/tmp/portal.log'):
    print(open('/tmp/portal.log').read()[-200:])

# Check what's on port 8888
ps8888=subprocess.run('ps aux | grep -E "portal_server|http.server" | grep -v grep | head -3',shell=True,capture_output=True,text=True).stdout.strip()
print('[3] Port 8888 process:',ps8888[:200])

# Test MSI api with longer timeout
print('[4] MSI /api/health test...')
try:
    with urllib.request.urlopen('http://127.0.0.1:8888/api/health',timeout=15) as r:
        d2=json.loads(r.read())
        print(f'  MSI /api/health: {json.dumps(d2)[:80]}')
        msi_api='PASS'
except Exception as e:
    print(f'  MSI /api/health: FAIL {str(e)[:60]}')
    msi_api='FAIL:'+str(e)[:40]

# Run audio test if M4 ok
print('[5] Audio generation test...')
if m4_ok:
    try:
        body=json.dumps({'text':'VNT World AI Division is online and ready.','type':'speech'}).encode()
        req=urllib.request.Request('http://'+M4+':3333/generate-audio',data=body,headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=90) as r:
            d3=json.loads(r.read())
            audio_ok=d3.get('status')=='ok'
            print(f'  Audio M4 direct: {"PASS" if audio_ok else "FAIL"} {str(d3)[:60]}')
    except Exception as e:
        print(f'  Audio: FAIL {str(e)[:60]}')
        audio_ok=False
else:
    audio_ok=False
    print('  Skipped (M4 offline)')

# Run image test if M4 ok
print('[6] Image generation test...')
if m4_ok:
    try:
        body=json.dumps({'prompt':'eagle 8k photorealistic sharp','width':256,'height':256,'steps':8}).encode()
        req=urllib.request.Request('http://'+M4+':3333/generate',data=body,headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=180) as r:
            d4=json.loads(r.read())
            img_ok=d4.get('status')=='ok'
            url=d4.get('url','?')[:50]
            print(f'  Image M4 direct: {"PASS" if img_ok else "FAIL"} {url}')
    except Exception as e:
        print(f'  Image: FAIL {str(e)[:60]}')
        img_ok=False
else:
    img_ok=False

# Check CT108 still up
print('[7] CT108 check...')
def rx1(c,t=10):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','root@'+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
ct108=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/dashboard.html --connect-timeout 6')
vnt=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://vntworld.com/dashboard.html --connect-timeout 8')
print(f'  CT108: {ct108}  vntworld: {vnt}')

R={'ts':TSF,'m4_direct':'PASS' if m4_ok else 'FAIL','msi_api':msi_api,'audio':'PASS' if audio_ok else 'FAIL','image':'PASS' if img_ok else 'FAIL','ct108':ct108,'vntworld':vnt}
try:
    hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
    try:
        rr=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',headers=hdr)
        with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get('sha','')
    except: sha=''
    data={'message':'gen test results','content':base64.b64encode(json.dumps({'ts':TSF,'results':R}).encode()).decode()}
    if sha: data['sha']=sha
    req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
    with urllib.request.urlopen(req,timeout=8) as resp: print('GH:','OK' if 'content' in json.loads(resp.read()) else 'FAIL')
except Exception as e: print('GH:',str(e)[:40])
print('SCORE:',sum(1 for v in R.values() if v not in ['ts'] and ('PASS' in str(v) or '200' in str(v))),'/',len([k for k in R if k!='ts']))
print('DONE')