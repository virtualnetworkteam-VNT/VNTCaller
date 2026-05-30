import subprocess,json,base64,datetime,time,urllib.request,os
M4='192.168.10.94'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
P1='192.168.10.19'

# Helper
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
        data={'message':'studio test','content':base64.b64encode(json.dumps({'ts':TSF,'results':R}).encode()).decode()}
        if sha: data['sha']=sha
        req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
        with urllib.request.urlopen(req,timeout=8) as resp: return 'content' in json.loads(resp.read())
    except: return False

print(TSF,'FULL STUDIO TEST')
R={}

# Check M4 endpoints
print('[1] M4 health + endpoints...')
try:
    with urllib.request.urlopen('http://'+M4+':3333/health',timeout=8) as r:
        h=json.loads(r.read())
        print('  Health:',json.dumps(h)[:100])
        R['m4_health']='PASS'
except Exception as e:
    print('  Health: FAIL',str(e)[:40])
    R['m4_health']='FAIL'

# Try audio endpoints
print('[2] Audio generation...')
audio_ok=False
for endpoint in ['/generate-audio','/tts','/audio','/generate_audio']:
    try:
        body=json.dumps({'text':'VNT AI Division online','type':'speech'}).encode()
        d=m4_post(endpoint,body,t=60)
        if d.get('status')=='ok' or d.get('url'):
            print(f'  Audio via {endpoint}: PASS url={d.get("url","?")[:40]}')
            R['audio']='PASS via '+endpoint
            audio_ok=True
            break
        else:
            print(f'  {endpoint}: {str(d)[:60]}')
    except Exception as e:
        print(f'  {endpoint}: {str(e)[:50]}')
if not audio_ok: R['audio']='FAIL - no working endpoint'

# 3D test
print('[3] 3D generation...')
try:
    body=json.dumps({'description':'sports car red metallic','mesh_resolution':64,'steps':10,'output_format':'obj'}).encode()
    d3=m4_post('/generate-3d',body,t=120)
    ok3=d3.get('status')=='ok'
    R['3d']='PASS' if ok3 else 'FAIL:'+str(d3)[:40]
    print(f'  3D: {"PASS" if ok3 else "FAIL"} {str(d3)[:60]}')
except Exception as e:
    R['3d']='FAIL:'+str(e)[:40]
    print(f'  3D: FAIL {str(e)[:50]}')

# Video test (short)
print('[4] Video generation...')
try:
    body=json.dumps({'prompt':'aerial ocean waves cinematic','frames':8,'fps':8,'steps':10}).encode()
    dv=m4_post('/generate-video',body,t=120)
    okv=dv.get('status')=='ok'
    R['video']='PASS' if okv else 'FAIL:'+str(dv)[:40]
    print(f'  Video: {"PASS" if okv else "FAIL"} {str(dv)[:60]}')
except Exception as e:
    R['video']='FAIL:'+str(e)[:40]
    print(f'  Video: FAIL {str(e)[:50]}')

# 2D drawing test
print('[5] 2D Drawing...')
try:
    body=json.dumps({'prompt':'floor plan 3 bedroom modern house','style':'architectural blueprint'}).encode()
    d2=m4_post('/generate-2d',body,t=90)
    ok2=d2.get('status')=='ok'
    R['2d']='PASS' if ok2 else 'FAIL:'+str(d2)[:40]
    print(f'  2D: {"PASS" if ok2 else "FAIL"} {str(d2)[:60]}')
except Exception as e:
    R['2d']='FAIL:'+str(e)[:40]
    print(f'  2D: FAIL {str(e)[:50]}')

# Image test (confirm)
print('[6] Image generation...')
try:
    body=json.dumps({'prompt':'VNT logo futuristic neon blue','width':512,'height':512,'steps':20}).encode()
    di=m4_post('/generate',body,t=180)
    oki=di.get('status')=='ok'
    R['image']='PASS url='+di.get('url','?')[:40] if oki else 'FAIL:'+str(di)[:40]
    print(f'  Image: {"PASS" if oki else "FAIL"} {di.get("url","")[:50]}')
except Exception as e:
    R['image']='FAIL:'+str(e)[:40]
    print(f'  Image: FAIL {str(e)[:50]}')

# Site status
ct108=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/ --connect-timeout 5')
vnt=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://vntworld.com/ --connect-timeout 6')
R['ct108']=ct108
R['vntworld']=vnt
print(f'CT108: {ct108}  vntworld: {vnt}')

gh_save(R)
passed=sum(1 for v in R.values() if 'PASS' in str(v) or '200' in str(v))
print(f'\nFINAL SCORE: {passed}/{len(R)}')
for k,v in R.items(): print(f'  {"PASS" if "PASS" in str(v) or "200" in str(v) else "FAIL"} {k}: {str(v)[:60]}')
print('DONE')