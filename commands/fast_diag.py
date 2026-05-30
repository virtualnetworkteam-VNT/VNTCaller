import subprocess,json,base64,datetime,time,urllib.request
M4='192.168.10.94'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
P1='192.168.10.19'

def m4_ssh(c,t=10):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','-o','BatchMode=yes','Alias@'+M4,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
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
        data={'message':'fast diag','content':base64.b64encode(json.dumps({'ts':TSF,'results':R}).encode()).decode()}
        if sha: data['sha']=sha
        req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
        with urllib.request.urlopen(req,timeout=8) as resp: return 'content' in json.loads(resp.read())
    except Exception as e: print('GH:',str(e)[:30]); return False

print(TSF,'FAST DIAG')
R={}

# Read M4 API routes
routes=m4_ssh('grep -n "route\|def gen" /Users/alias/vnt-studio/studio_api.py 2>/dev/null | head -40')
print('ROUTES:',routes[:500])
R['routes']=routes[:200]

# Check audio script
audio_check=m4_ssh('ls /Users/alias/vnt-studio/generate_audio.py 2>/dev/null && cat /Users/alias/vnt-studio/generate_audio.py 2>/dev/null | head -20 || echo NOT_FOUND')
print('Audio script:',audio_check[:200])
R['audio_script']=audio_check[:100]

# Check studio log
studio_log=m4_ssh('tail -20 /tmp/studio.log 2>/dev/null || echo NO_LOG')
print('Studio log:',studio_log[:300])
R['studio_log']=studio_log[:150]

# Quick audio test with short timeout to see error
try:
    body=json.dumps({'text':'test','type':'speech'}).encode()
    req=urllib.request.Request('http://'+M4+':3333/generate-audio',data=body,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=15) as r:
        d=json.loads(r.read())
        R['audio_test']=str(d)[:100]
        print('Audio result:',str(d)[:100])
except Exception as e:
    R['audio_test']='FAIL:'+str(e)[:60]
    print('Audio error:',str(e)[:80])

# Site status
ct108=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/ --connect-timeout 5')
vnt=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://vntworld.com/ --connect-timeout 6')
R['ct108']=ct108; R['vntworld']=vnt
print(f'CT108:{ct108} vntworld:{vnt}')

gh_save(R)
for k,v in R.items(): print(f'{k}: {str(v)[:65]}')
print('DONE')