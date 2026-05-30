import subprocess,json,base64,datetime,time,urllib.request,os
M4='192.168.10.94'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
P1='192.168.10.19'

def m4_get(path,t=8):
    req=urllib.request.Request('http://'+M4+':3333'+path,headers={'User-Agent':'VNT/1.0'})
    with urllib.request.urlopen(req,timeout=t) as r: return r.status,json.loads(r.read())
def m4_post(path,body,t=90):
    req=urllib.request.Request('http://'+M4+':3333'+path,data=body,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=t) as r: return json.loads(r.read())
def rx1(c,t=10):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','root@'+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def gh_save(R):
    try:
        hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
        try:
            rr=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get('sha','')
        except: sha=''
        data={'message':'audio diag','content':base64.b64encode(json.dumps({'ts':TSF,'results':R}).encode()).decode()}
        if sha: data['sha']=sha
        req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
        with urllib.request.urlopen(req,timeout=8) as resp: return 'content' in json.loads(resp.read())
    except Exception as e: print('GH:',str(e)[:30]); return False

print(TSF,'AUDIO DIAG + VIDEO + 3D')
R={}

# 1. Check M4 studio API routes
print('[1] M4 API routes...')
try:
    st,h=m4_get('/health',t=6)
    print(f'  Health: {json.dumps(h)[:120]}')
    R['m4']='PASS'
except Exception as e: print(f'  Health: {e}'); R['m4']='FAIL'

# Check the studio_api.py content on M4
print('[2] Reading M4 API source...')
api_src=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','BatchMode=yes','-o','ConnectTimeout=5','Alias@'+M4,
    'grep -n "@app.route\|def generate" /Users/alias/vnt-studio/studio_api.py 2>/dev/null | head -30'],
    capture_output=True,text=True,timeout=12).stdout.strip()
print(f'  Routes:\n{api_src[:400]}')
R['api_routes']=api_src[:200]

# 3. Try audio with correct endpoint based on routes found
print('[3] Audio test...')
for ep,body in [
    ('/generate-audio',json.dumps({'text':'VNT ready','type':'speech'}).encode()),
    ('/generate-audio',json.dumps({'text':'VNT ready','voice':'en-US-AriaNeural'}).encode()),
    ('/tts',json.dumps({'text':'VNT ready'}).encode()),
    ('/generate',json.dumps({'type':'audio','text':'VNT ready','prompt':'VNT ready'}).encode()),
]:
    try:
        d=m4_post(ep,body,t=60)
        ok=d.get('status')=='ok' or bool(d.get('url'))
        print(f'  {ep}: {"PASS" if ok else str(d)[:60]}')
        if ok: R['audio']='PASS via '+ep; break
    except Exception as e: print(f'  {ep}: {str(e)[:50]}')
if 'audio' not in R: R['audio']='FAIL all endpoints'

# 4. Video test
print('[4] Video...')
try:
    body=json.dumps({'prompt':'ocean waves cinematic','frames':8,'fps':8,'steps':8}).encode()
    dv=m4_post('/generate-video',body,t=120)
    okv=dv.get('status')=='ok'
    R['video']='PASS' if okv else 'FAIL:'+str(dv)[:40]
    print(f'  Video: {"PASS" if okv else str(dv)[:60]}')
except Exception as e: R['video']='FAIL:'+str(e)[:40]; print(f'  Video: {str(e)[:60]}')

# 5. 3D test
print('[5] 3D...')
try:
    body=json.dumps({'description':'sports car','mesh_resolution':64,'steps':10,'output_format':'obj'}).encode()
    d3=m4_post('/generate-3d',body,t=120)
    ok3=d3.get('status')=='ok'
    R['3d']='PASS' if ok3 else 'FAIL:'+str(d3)[:40]
    print(f'  3D: {"PASS" if ok3 else str(d3)[:60]}')
except Exception as e: R['3d']='FAIL:'+str(e)[:40]; print(f'  3D: {str(e)[:60]}')

# 6. Image (fast 256x256)
print('[6] Image...')
try:
    body=json.dumps({'prompt':'VNT futuristic logo neon','width':256,'height':256,'steps':10}).encode()
    di=m4_post('/generate',body,t=180)
    oki=di.get('status')=='ok'
    R['image']='PASS url='+di.get('url','?')[:40] if oki else 'FAIL:'+str(di)[:40]
    print(f'  Image: {"PASS" if oki else str(di)[:60]}')
except Exception as e: R['image']='FAIL:'+str(e)[:40]; print(f'  Image: {str(e)[:60]}')

# 7. Site status
ct108=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/ --connect-timeout 5')
vnt=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://vntworld.com/ --connect-timeout 6')
R['ct108']=ct108; R['vntworld']=vnt
print(f'CT108:{ct108} vntworld:{vnt}')

gh_save(R)
passed=sum(1 for v in R.values() if 'PASS' in str(v) or '200' in str(v))
print(f'\nSCORE: {passed}/{len(R)}')
for k,v in R.items(): print(f'  {"✓" if "PASS" in str(v) or "200" in str(v) else "✗"} {k}: {str(v)[:65]}')
print('DONE')