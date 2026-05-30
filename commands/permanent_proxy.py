import subprocess,json,base64,datetime,time,urllib.request,os
P1='192.168.10.19'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
PROXY_PARTS=[
    b'aW1wb3J0IGh0dHAuc2VydmVyLGpzb24sb3MsdXJsbGliLnJlcXVlc3QsdXJsbGliLmVycm9yLG1pbWV0eXBlcyxkYXRldGltZSx0aW1lCldFQj0iL3Zhci93d3cvaHRtbCIKTTQ9Imh0dHA6Ly8xOTIuMTY4LjEwLjk0OjMzMzMiClBPUlQ9ODAKZGVmIGxvZyhtKTogcHJpbnQoIlsiK2RhdGV0aW1lLmRhdGV0aW1lLm5vdygpLnN0cmZ0aW1lKCIlSDolTTolUyIpKyJdICIrbSxmbHVzaD1UcnVlKQpjbGFzcyBIKGh0dHAuc2VydmVyLkJhc2VIVFRQUmVxdWVzdEhhbmRsZXIpOgogICAgZGVmIGxvZ19tZXNzYWdlKHNlbGYsKmEpOiBwYXNzCiAgICBkZWYgY29ycyhzZWxmKToKICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJBY2Nlc3MtQ29udHJvbC1BbGxvdy1PcmlnaW4iLCIqIikKICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJBY2Nlc3MtQ29udHJvbC1BbGxvdy1NZXRob2RzIiwiR0VULFBPU1QsT1BUSU9OUyIpCiAgICAgICAgc2VsZi5zZW5kX2hlYWRlcigiQWNjZXNzLUNvbnRyb2wtQWxsb3ctSGVhZGVycyIsIkNvbnRlbnQtVHlwZSIpCiAgICBkZWYgcHJveHkoc2VsZixwYXRoLGJvZHk9Tm9uZSxtZXRob2Q9IkdFVCIpOgogICAgICAgIHRyeToKICAgICAgICAgICAgcmVxPXVybGxpYi5yZXF1ZXN0LlJlcXVlc3QoTTQrcGF0aCxkYXRhPWJvZHksaGVhZGVycz17IkNvbnRlbnQtVHlwZSI6ImFwcGxpY2F0aW9uL2pzb24ifSxtZXRob2Q9bWV0aG9kKQogICAgICAgICAgICB3aXRoIHVybGxpYi5yZXF1ZXN0LnVybG9wZW4ocmVxLHRpbWVvdXQ9MzYwKSBhcyByOgogICAgICAgICAgICAgICAgZGF0YT1yLnJlYWQoKTtjdD1yLmhlYWRlcnMuZ2V0KCJDb250ZW50LVR5cGUiLCJhcHBsaWNhdGlvbi9qc29uIikKICAgICAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSgyMDApO3NlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtVHlwZSIsY3QpO3NlbGYuY29ycygpCiAgICAgICAgICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJDb250ZW50LUxlbmd0aCIsc3RyKGxlbihkYXRhKSkpO3NlbGYuZW5kX2hlYWRlcnMoKTtzZWxmLndmaWxlLndyaXRlKGRhdGEpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgICAgICBlcnI9anNvbi5kdW1wcyh7InN0YXR1cyI6ImVycm9yIiwiZXJyb3IiOnN0cihlKX0pLmVuY29kZSgpCiAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSg1MDMpO3NlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtVHlwZSIsImFwcGxpY2F0aW9uL2pzb24iKTtzZWxmLmNvcnMoKQogICAgICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJDb250ZW50LUxlbmd0aCIsc3RyKGxlbihlcnIpKSk7c2VsZi5lbmRfaGVhZGVycygpO3NlbGYud2ZpbGUud3JpdGUoZXJyKQogICAgZGVmIGRvX09QVElPTlMoc2VsZik6IHNlbGYuc2VuZF9yZXNwb25zZSgyMDApO3NlbGYuY29ycygpO3NlbGYuZW5kX2hlYWRlcnMoKQogICAgZGVmIGRvX0dFVChzZWxmKToKICAgICAgICBwPXNlbGYucGF0aC5zcGxpdCgiPyIpWzBdCiAgICAgICAgaWYgcC5zdGFydHN3aXRoKCIvYXBpLyIpOiBzZWxmLnByb3h5KHBbNDpdKTsgcmV0dXJuCiAgICAgICAgaWYgcD09Ii8iIG9yIHA9PSIiOiBwPSIvZGFzaGJvYXJkLmh0bWwiCiAgICAgICAgZnA9V0VCK3AKICAgICAgICBpZiBvcy5wYXRoLmlzZGlyKGZwKTogZnA9ZnAucnN0cmlwKCIvIikrIi9pbmRleC5odG1sIgogICAgICAgIGlmIG9zLnBhdGguZXhpc3RzKGZwKSBhbmQgb3MucGF0aC5pc2ZpbGUoZnApOgogICAgICAgICAgICBjdCxfPW1pbWV0eXBlcy5ndWVzc190eXBlKGZwKTtjdD1jdCBvciAiYXBwbGljYXRpb24vb2N0ZXQtc3RyZWFtIgogICAgICAgICAgICBkYXRhPW9wZW4oZnAsInJiIikucmVhZCgpCiAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSgyMDApO3NlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtVHlwZSIsY3QpCiAgICAgICAgICAgIHNlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtTGVuZ3RoIixzdHIobGVuKGRhdGEpKSk7c2VsZi5jb3JzKCk7c2VsZi4=',
    b'ZW5kX2hlYWRlcnMoKTtzZWxmLndmaWxlLndyaXRlKGRhdGEpCiAgICAgICAgZWxzZTogc2VsZi5zZW5kX3Jlc3BvbnNlKDQwNCk7c2VsZi5lbmRfaGVhZGVycygpO3NlbGYud2ZpbGUud3JpdGUoYiI0MDQiKQogICAgZGVmIGRvX1BPU1Qoc2VsZik6CiAgICAgICAgbj1pbnQoc2VsZi5oZWFkZXJzLmdldCgiQ29udGVudC1MZW5ndGgiLDApKQogICAgICAgIGJvZHk9c2VsZi5yZmlsZS5yZWFkKG4pIGlmIG4gZWxzZSBOb25lCiAgICAgICAgaWYgc2VsZi5wYXRoLnN0YXJ0c3dpdGgoIi9hcGkvIik6IGxvZygiUE9TVCAiK3NlbGYucGF0aFs0Ol0pOyBzZWxmLnByb3h5KHNlbGYucGF0aFs0Ol0sYm9keSwiUE9TVCIpOyByZXR1cm4KICAgICAgICBzZWxmLnNlbmRfcmVzcG9uc2UoNDA0KTtzZWxmLmVuZF9oZWFkZXJzKCk7c2VsZi53ZmlsZS53cml0ZShiIjQwNCIpCnRyeTogc2VydmVyPWh0dHAuc2VydmVyLlRocmVhZGluZ0hUVFBTZXJ2ZXIoKCIwLjAuMC4wIixQT1JUKSxIKQpleGNlcHQgQXR0cmlidXRlRXJyb3I6IHNlcnZlcj1odHRwLnNlcnZlci5IVFRQU2VydmVyKCgiMC4wLjAuMCIsUE9SVCksSCkKbG9nKCJWTlQgQ1QxMDggOiIrc3RyKFBPUlQpKyIgLT4gIitNNCkKc2VydmVyLnNlcnZlX2ZvcmV2ZXIoKQo=',
]
PROXY=base64.b64decode(b''.join(PROXY_PARTS))
def rx1(c,t=12):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','root@'+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def scp2p(local,remote,t=12):
    r=subprocess.run(['scp','-o','StrictHostKeyChecking=no',local,'root@'+P1+':'+remote],capture_output=True,text=True,timeout=t)
    return r.returncode==0
def pct(ctid,c,t=12):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','root@'+P1,'pct exec '+str(ctid)+' -- bash -c '+json.dumps(c)],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def chk(url,t=8):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'VNT/1.0'})
        with urllib.request.urlopen(req,timeout=t) as r: return str(r.status)+':'+str(len(r.read()))
    except Exception as e: return 'FAIL:'+str(e)[:30]
def gh_save(result):
    try:
        hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
        try:
            rr=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',headers=hdr)
            with urllib.request.urlopen(rr,timeout=6) as resp: sha=json.loads(resp.read()).get('sha','')
        except: sha=''
        data={'message':'final result','content':base64.b64encode(json.dumps({'ts':TSF,'results':result}).encode()).decode()}
        if sha: data['sha']=sha
        req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
        with urllib.request.urlopen(req,timeout=10) as resp: return 'content' in json.loads(resp.read())
    except Exception as e: print('GH:',str(e)[:50]); return False
print(TSF,'PERMANENT PROXY + MSI FIX')
R={}

# Deploy proxy server to CT108
print('[1] Deploy proxy...')
open('/tmp/vnt_proxy.py','wb').write(PROXY)
scp2p('/tmp/vnt_proxy.py','/tmp/vnt_proxy.py')
rx1('pct push 108 /tmp/vnt_proxy.py /tmp/vnt_proxy.py',t=12)

# Create systemd service
print('[2] Systemd...')
svc_content='[Unit]\nDescription=VNT Web\nAfter=network.target\n\n[Service]\nExecStart=/usr/bin/python3 /tmp/vnt_proxy.py\nRestart=always\nRestartSec=3\n\n[Install]\nWantedBy=multi-user.target'
pct(108,'cat > /etc/systemd/system/vnt-web.service << SEOF\n'+svc_content+'\nSEOF && systemctl daemon-reload && systemctl enable vnt-web && systemctl restart vnt-web && echo SYSTEMD_OK',t=15)
time.sleep(5)
svc_st=pct(108,'systemctl is-active vnt-web 2>/dev/null')
R['ct108_systemd']=svc_st
print(f'  Systemd: {svc_st}')

# Verify CT108
print('[3] Verify CT108...')
r1=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/ --connect-timeout 6')
r2=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/api/health --connect-timeout 6')
print(f'  root: {r1}  api: {r2}')
R['ct108_root']=r1
R['ct108_api']=r2

# MSI portal
print('[4] MSI portal...')
MSI='/home/k/vnt-web'
subprocess.run(['fuser','-k','8888/tcp'],capture_output=True);time.sleep(1)
if os.path.exists(MSI+'/portal_server.py'):
    subprocess.Popen(['/usr/bin/python3',MSI+'/portal_server.py'],stdout=open('/tmp/portal.log','w'),stderr=subprocess.STDOUT)
    time.sleep(5)
    R['msi_8888']=chk('http://127.0.0.1:8888/',t=5)
    R['msi_api']=chk('http://127.0.0.1:8888/api/health',t=8)
    print(f'  8888: {R["msi_8888"]}  api: {R["msi_api"]}')
else:
    R['msi_8888']='FAIL:missing'
    R['msi_api']='FAIL:missing'

# vntworld.com test via Prox1
vnt_root=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://vntworld.com/ --connect-timeout 8')
R['vntworld']=vnt_root
print(f'  vntworld.com: {vnt_root}')

# M4 API
m4r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','-o','BatchMode=yes','Alias@192.168.10.94','curl -s http://localhost:3333/health'],capture_output=True,text=True,timeout=10)
R['m4']='PASS' if '"online"' in m4r.stdout else 'FAIL'
print(f'  M4: {m4r.stdout.strip()[:40]}')

ok=gh_save(R)
print('GH save:',ok)
passed=sum(1 for v in R.values() if '200' in str(v) or 'active' in str(v) or 'PASS' in str(v))
print(f'\nSCORE: {passed}/{len(R)}')
for k,v in R.items(): print(f'  {"OK" if "200" in str(v) or "active" in str(v) or "PASS" in str(v) else "FAIL"} {k}: {str(v)[:60]}')
print('DONE')