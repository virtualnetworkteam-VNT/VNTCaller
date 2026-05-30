import subprocess,datetime,json,urllib.request,time,re,base64,os
P1='192.168.10.19';WEB='/var/www/html';MSI='/home/k/vnt-web'
CFG='/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json'
MP='/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller';TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
def rx1(c,t=20):r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=6','root@'+P1,c],capture_output=True,text=True,timeout=t);return (r.stdout+r.stderr).strip()
def scp_p1(l,r,t=20):return subprocess.run(['scp','-o','StrictHostKeyChecking=no',l,'root@'+P1+':'+r],capture_output=True,timeout=t).returncode==0
def gh_api(path):
    hdr={'Authorization':'Bearer '+GH,'Accept':'application/vnd.github.v3+json'}
    return json.loads(urllib.request.urlopen(urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/{path}',headers=hdr),timeout=30).read())
def gh_save(R):
    try:
        hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
        try:
            rr=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get('sha','')
        except: sha=''
        data={'message':'v8d result','content':base64.b64encode(json.dumps({'ts':TSF,'results':R}).encode()).decode()}
        if sha: data['sha']=sha
        req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
        with urllib.request.urlopen(req,timeout=8) as resp: return 'content' in json.loads(resp.read())
    except Exception as e: print('GH:',str(e)[:30]); return False
print(TSF,'DEPLOY v8d');R={}
fd=gh_api('dashboard_v8d.html')
raw=base64.b64decode(fd['content'].replace('\n','')).decode()
groq_key=''
try:cfg=json.load(open(CFG));groq_key=cfg.get('groq_key','')
except:pass
if not groq_key:
    try:mp=open(MP).read();m=re.search(r'gsk_[A-Za-z0-9]{40,}',mp)
    except:m=None
    if m:groq_key=m.group(0)
if groq_key:raw=raw.replace('GROQ_PH',groq_key)
for old,new in [('U_PW2','App159earance.VnT'),('U_PW3','0568116899'),('U_PW1','116899')]:raw=raw.replace(old,new)
html=raw.encode()
print(f'HTML: {len(html)}b')
open('/tmp/dash_v8d.html','wb').write(html)
open(MSI+'/dashboard.html','wb').write(html)
ok=scp_p1('/tmp/dash_v8d.html','/tmp/dash_v8d.html')
push=rx1('pct push 108 /tmp/dash_v8d.html '+WEB+'/dashboard.html',t=20)
sz=rx1('pct exec 108 -- stat -c %s '+WEB+'/dashboard.html 2>/dev/null')
print(f'CT108: {sz}b push={push or "OK"}')
R['dashboard']=f'PASS {sz}b' if int(sz or 0)>90000 else f'FAIL {sz}b'
ps=rx1('pct exec 108 -- ps aux 2>/dev/null | grep -E "ct108proxy|http.server" | grep -v grep | wc -l',t=8)
if ps.strip()=='0':
    subprocess.Popen(['ssh','-o','StrictHostKeyChecking=no','root@'+P1,'pct exec 108 -- bash -c \'cd /var/www/html && nohup python3 -m http.server 80 --bind 0.0.0.0 >> /tmp/web.log 2>&1 &\''],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(3)
ct108=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/ --connect-timeout 5')
vnt=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' https://vntworld.com/dashboard.html --connect-timeout 8')
print(f'CT108:{ct108} vnt:{vnt}');R['ct108']=ct108;R['vntworld']=vnt
try:open(MP,'a').write('\n### v8d ['+TSF+']\nSAPI: MSI proxy + M4 fallback\n')
except:pass
gh_save(R)
for k,v in R.items():print(f'  {"OK" if "200" in str(v) or "PASS" in str(v) else "FL"} {k}: {str(v)[:60]}')
print('DONE')