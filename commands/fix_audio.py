import subprocess,json,base64,datetime,time,urllib.request
M4='192.168.10.94'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
P1='192.168.10.19'

def m4_ssh(c,t=12):
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
        data={'message':'audio fix','content':base64.b64encode(json.dumps({'ts':TSF,'results':R}).encode()).decode()}
        if sha: data['sha']=sha
        req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
        with urllib.request.urlopen(req,timeout=8) as resp: return 'content' in json.loads(resp.read())
    except Exception as e: print('GH:',str(e)[:30]); return False

print(TSF,'FIND AND FIX AUDIO')
R={}

# Find audio scripts on M4
find_audio=m4_ssh('find /Users/alias -name "*audio*" -o -name "*tts*" -o -name "*speech*" 2>/dev/null | head -10')
print('Audio files:',find_audio[:200])
R['audio_files']=find_audio[:100]

# Read studio_api.py lines around 185-200 to see the crash
api_crash=m4_ssh('sed -n "180,210p" /Users/alias/vnt-studio/studio_api.py 2>/dev/null')
print('API crash area:',api_crash[:400])
R['crash_area']=api_crash[:200]

# Check edge-tts installation
edge_tts=m4_ssh('/Users/alias/miniforge3/envs/vnt/bin/python -c "import edge_tts; print(edge_tts.__version__)" 2>/dev/null || echo NOT_INSTALLED')
print('edge-tts:',edge_tts)
R['edge_tts']=edge_tts

# Write a simple generate_audio.py that uses edge-tts
audio_script='''import asyncio,sys,os,json,datetime
async def main():
    text=sys.argv[1] if len(sys.argv)>1 else "Hello from VNT"
    voice=sys.argv[2] if len(sys.argv)>2 else "en-US-AriaNeural"
    out_dir="/Users/alias/vnt-studio/generated"
    os.makedirs(out_dir,exist_ok=True)
    fname=f"audio_{datetime.datetime.now().strftime(chr(37)+\'Y%m%d_%H%M%S\')}.mp3"
    out_path=os.path.join(out_dir,fname)
    try:
        import edge_tts
        comm=edge_tts.Communicate(text,voice)
        await comm.save(out_path)
        print(json.dumps({"status":"ok","url":"/generated/"+fname,"path":out_path}))
    except Exception as e:
        print(json.dumps({"status":"error","error":str(e)}))
asyncio.run(main())
'''
# Write the audio script to M4
audio_b64=base64.b64encode(audio_script.encode()).decode()
m4_ssh(f'echo {audio_b64} | base64 -d > /Users/alias/vnt-studio/generate_audio.py && echo WRITTEN',t=10)
print('Audio script written')

# Test edge-tts directly
audio_test=m4_ssh('/Users/alias/miniforge3/envs/vnt/bin/python /Users/alias/vnt-studio/generate_audio.py "VNT AI Division ready" 2>/dev/null',t=30)
print('Audio test:',audio_test[:150])
R['audio_direct']=audio_test[:100]

# Restart studio API on M4
print('Restarting studio API...')
m4_ssh('pkill -f studio_api 2>/dev/null; sleep 2; nohup /Users/alias/miniforge3/envs/vnt/bin/python /Users/alias/vnt-studio/studio_api.py > /tmp/studio.log 2>&1 & echo STARTED')
time.sleep(5)

# Test audio via API
try:
    body=json.dumps({'text':'VNT World AI Division systems online','type':'speech'}).encode()
    req=urllib.request.Request('http://'+M4+':3333/generate-audio',data=body,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=30) as r:
        d=json.loads(r.read())
        ok=d.get('status')=='ok'
        R['audio_api']='PASS url='+d.get('url','?')[:40] if ok else 'FAIL:'+str(d)[:60]
        print('Audio via API:',str(d)[:80])
except Exception as e:
    R['audio_api']='FAIL:'+str(e)[:50]
    print('Audio API error:',str(e)[:60])

# Site check
ct108=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/ --connect-timeout 5')
vnt=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://vntworld.com/ --connect-timeout 6')
R['ct108']=ct108; R['vntworld']=vnt
print(f'CT108:{ct108} vntworld:{vnt}')

gh_save(R)
for k,v in R.items(): print(f'{k}: {str(v)[:65]}')
print('DONE')