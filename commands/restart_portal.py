import subprocess,datetime,json,urllib.request,time,os
MSI='/home/k/vnt-web'
MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'
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
        data={'message':'portal restart','content':__import__('base64').b64encode(json.dumps({'ts':TSF,'results':R}).encode()).decode()}
        if sha: data['sha']=sha
        req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
        with urllib.request.urlopen(req,timeout=8) as resp: return 'content' in json.loads(resp.read())
    except Exception as e: print('GH:',str(e)[:30]); return False
print(TSF,'RESTART MSI PORTAL + VERIFY ALL')
R={}
# Restart portal
subprocess.run(['fuser','-k','8888/tcp'],capture_output=True)
time.sleep(1)
if os.path.exists(MSI+'/portal_server.py'):
    subprocess.Popen(['/usr/bin/python3',MSI+'/portal_server.py'],stdout=open('/tmp/portal.log','w'),stderr=subprocess.STDOUT)
    time.sleep(5)
    st,sz=chk('http://127.0.0.1:8888/api/health',t=8)
    R['msi_api']=f'PASS {sz}b' if st==200 else f'FAIL {st}'
    print(f'MSI /api/health: {st} {sz}b')
else:
    R['msi_api']='FAIL:no portal_server.py'
    print('portal_server.py MISSING')
# Check all services
for name,url in [('vntworld','https://vntworld.com/dashboard.html'),('m4_api','http://192.168.10.94:3333/health'),('nextcloud','http://192.168.10.10/')]:
    st2,sz2=chk(url,t=8)
    ok=st2 in [200,301,302]
    R[name]=f'PASS {sz2}b' if ok else f'FAIL {st2}'
    print(f'{name}: {st2} {sz2}b')
try: open(MP,'a').write('\n### Portal restart ['+TSF+']\n'+json.dumps(R)+'\n')
except: pass
gh_save(R)
for k,v in R.items(): print(f'  {"OK" if "PASS" in str(v) else "FL"} {k}: {str(v)[:60]}')
print('DONE')