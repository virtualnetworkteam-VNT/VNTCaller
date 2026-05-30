import subprocess,json,base64,datetime,time,urllib.request,os
P1='192.168.10.19'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
PROXY_PARTS=[
    b'aW1wb3J0IGh0dHAuc2VydmVyLGpzb24sb3MsdXJsbGliLnJlcXVlc3QsdXJsbGliLmVycm9yLG1pbWV0eXBlcyxkYXRldGltZSx0aW1lCldFQj0iL3Zhci93d3cvaHRtbCIKTTQ9Imh0dHA6Ly8xOTIuMTY4LjEwLjk0OjMzMzMiClBPUlQ9ODAKZGVmIGxvZyhtKTogcHJpbnQoIlsiK2RhdGV0aW1lLmRhdGV0aW1lLm5vdygpLnN0cmZ0aW1lKCIlSDolTTolUyIpKyJdICIrbSxmbHVzaD1UcnVlKQpjbGFzcyBIKGh0dHAuc2VydmVyLkJhc2VIVFRQUmVxdWVzdEhhbmRsZXIpOgogICAgZGVmIGxvZ19tZXNzYWdlKHNlbGYsKmEpOiBwYXNzCiAgICBkZWYgY29ycyhzZWxmKToKICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJBY2Nlc3MtQ29udHJvbC1BbGxvdy1PcmlnaW4iLCIqIikKICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJBY2Nlc3MtQ29udHJvbC1BbGxvdy1NZXRob2RzIiwiR0VULFBPU1QsT1BUSU9OUyIpCiAgICAgICAgc2VsZi5zZW5kX2hlYWRlcigiQWNjZXNzLUNvbnRyb2wtQWxsb3ctSGVhZGVycyIsIkNvbnRlbnQtVHlwZSIpCiAgICBkZWYgcHJveHkoc2VsZixwYXRoLGJvZHk9Tm9uZSxtZXRob2Q9IkdFVCIpOgogICAgICAgIHRyeToKICAgICAgICAgICAgcmVxPXVybGxpYi5yZXF1ZXN0LlJlcXVlc3QoTTQrcGF0aCxkYXRhPWJvZHksaGVhZGVycz17IkNvbnRlbnQtVHlwZSI6ImFwcGxpY2F0aW9uL2pzb24ifSxtZXRob2Q9bWV0aG9kKQogICAgICAgICAgICB3aXRoIHVybGxpYi5yZXF1ZXN0LnVybG9wZW4ocmVxLHRpbWVvdXQ9MzYwKSBhcyByOgogICAgICAgICAgICAgICAgZGF0YT1yLnJlYWQoKTtjdD1yLmhlYWRlcnMuZ2V0KCJDb250ZW50LVR5cGUiLCJhcHBsaWNhdGlvbi9qc29uIikKICAgICAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSgyMDApO3NlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtVHlwZSIsY3QpO3NlbGYuY29ycygpCiAgICAgICAgICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJDb250ZW50LUxlbmd0aCIsc3RyKGxlbihkYXRhKSkpO3NlbGYuZW5kX2hlYWRlcnMoKTtzZWxmLndmaWxlLndyaXRlKGRhdGEpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgICAgICBlcnI9anNvbi5kdW1wcyh7InN0YXR1cyI6ImVycm9yIiwiZXJyb3IiOnN0cihlKX0pLmVuY29kZSgpCiAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSg1MDMpO3NlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtVHlwZSIsImFwcGxpY2F0aW9uL2pzb24iKTtzZWxmLmNvcnMoKQogICAgICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJDb250ZW50LUxlbmd0aCIsc3RyKGxlbihlcnIpKSk7c2VsZi5lbmRfaGVhZGVycygpO3NlbGYud2ZpbGUud3JpdGUoZXJyKQogICAgZGVmIGRvX09QVElPTlMoc2VsZik6IHNlbGYuc2VuZF9yZXNwb25zZSgyMDApO3NlbGYuY29ycygpO3NlbGYuZW5kX2hlYWRlcnMoKQogICAgZGVmIGRvX0dFVChzZWxmKToKICAgICAgICBwPXNlbGYucGF0aC5zcGxpdCgiPyIpWzBdCiAgICAgICAgaWYgcC5zdGFydHN3aXRoKCIvYXBpLyIpOiBzZWxmLnByb3h5KHBbNDpdKTsgcmV0dXJuCiAgICAgICAgaWYgcD09Ii8iIG9yIHA9PSIiOiBwPSIvZGFzaGJvYXJkLmh0bWwiCiAgICAgICAgZnA9V0VCK3AKICAgICAgICBpZiBvcy5wYXRoLmlzZGlyKGZwKTogZnA9ZnAucnN0cmlwKCIvIikrIi9pbmRleC5odG1sIgogICAgICAgIGlmIG9zLnBhdGguZXhpc3RzKGZwKSBhbmQgb3MucGF0aC5pc2ZpbGUoZnApOgogICAgICAgICAgICBjdCxfPW1pbWV0eXBlcy5ndWVzc190eXBlKGZwKTtjdD1jdCBvciAiYXBwbGljYXRpb24vb2N0ZXQtc3RyZWFtIgogICAgICAgICAgICBkYXRhPW9wZW4oZnAsInJiIikucmVhZCgpCiAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSgyMDApO3NlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtVHlwZSIsY3QpCiAgICAgICAgICAgIHNlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtTGVuZ3RoIixzdHIobGVuKGRhdGEpKSk7c2VsZi5jb3JzKCk7c2VsZi5lbmRfaGVhZGVycygpO3NlbGYud2ZpbGUud3JpdGUoZGF0YSkKICAgICAgICBlbHNlOiBzZWxmLnNlbmRfcmVzcG9uc2UoNDA0KTtzZWxmLmVuZF9oZWFkZXJzKCk7c2VsZi53ZmlsZS53cml0ZShiIjQwNCIpCiAgICBkZWYgZG9fUE9TVChzZWxmKToKICAgICAgICBuPWludChzZWxmLmhlYWRlcnMuZ2V0KCJDb250ZW50LUxlbmd0aCIsMCkpCiAgICAgICAgYm9keT1zZWxmLnJmaWxlLnJlYWQobikgaWYgbiBlbHNlIE5vbmUKICAgICAgICBpZiBzZWxmLnBhdGguc3RhcnRzd2l0aCgiL2FwaS8iKTogbG9nKCJQT1NUICIrc2VsZi5wYXRoWzQ6XSk7IHNlbGYucHJveHkoc2VsZi5wYXRoWzQ6XSxib2R5LCJQT1NUIik7IHJldHVybgogICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSg0MDQpO3NlbGYuZW5kX2hlYWRlcnMoKTtzZWxmLndmaWxlLndyaXRlKGIiNDA0IikKdHJ5OiBzZXJ2ZXI9aHR0cC5zZXJ2ZXIuVGhyZWFkaW5nSFRUUFNlcnZlcigoIjAuMC4wLjAiLFBPUlQpLEgpCmV4Y2VwdCBBdHRyaWJ1dGVFcnJvcjogc2VydmVyPWh0dHAuc2VydmVyLkhUVFBTZXJ2ZXIoKCIwLjAuMC4wIixQT1JUKSxIKQpsb2coIlZOVCBDVDEwOCA6IitzdHIoUE9SVCkrIiAtPiAiK000KQpzZXJ2ZXIuc2VydmVfZm9yZXZlcigpCg==',
]
PROXY=base64.b64decode(b''.join(PROXY_PARTS))
print(f'Proxy: {len(PROXY)}b')
def scp2p(local,remote,t=15):
    r=subprocess.run(['scp','-o','StrictHostKeyChecking=no',local,'root@'+P1+':'+remote],capture_output=True,text=True,timeout=t)
    return r.returncode==0,r.stderr[:40]
def rx1(c,t=12):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','root@'+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def pct(ctid,c,t=12):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','root@'+P1,'pct exec '+str(ctid)+' -- bash -c '+json.dumps(c)],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
print(TSF,'INSTALL PROXY')

# Write proxy to MSI temp
open('/tmp/vnt_proxy.py','wb').write(PROXY)

# SCP MSI -> Prox1
ok,err=scp2p('/tmp/vnt_proxy.py','/tmp/vnt_proxy.py')
print('SCP to Prox1:','OK' if ok else 'FAIL:'+err)

# pct push Prox1 -> CT108
push_r=rx1('pct push 108 /tmp/vnt_proxy.py /tmp/vnt_proxy.py',t=12)
print('pct push:',push_r or 'OK')

# Kill old, start proxy
pct(108,'pkill -9 -f http.server 2>/dev/null; pkill -9 -f vnt_proxy 2>/dev/null; fuser -k 80/tcp 2>/dev/null; sleep 2; nohup python3 /tmp/vnt_proxy.py > /tmp/proxy.log 2>&1 & echo STARTED')
time.sleep(5)

# Verify
r1=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/ --connect-timeout 6')
r2=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/api/health --connect-timeout 6')
print('CT108 root:',r1)
print('CT108 api/health:',r2)

# Also restart MSI portal
MSI='/home/k/vnt-web'
if os.path.exists(MSI+'/portal_server.py'):
    subprocess.run(['fuser','-k','8888/tcp'],capture_output=True)
    time.sleep(1)
    subprocess.Popen(['/usr/bin/python3',MSI+'/portal_server.py'],stdout=open('/tmp/portal.log','w'),stderr=subprocess.STDOUT)
    time.sleep(4)
    import urllib.request as ul
    try:
        with ul.urlopen('http://127.0.0.1:8888/api/health',timeout=5) as rr: r3=str(rr.status)+':'+str(len(rr.read()))
    except Exception as e: r3='FAIL:'+str(e)[:30]
    print('MSI api/health:',r3)
else:
    r3='no portal_server'
    print('MSI portal: missing')

result={'ts':TSF,'ct108_root':r1,'ct108_api':r2,'msi_api':r3}
try:
    hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
    try:
        rr=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',headers=hdr)
        with urllib.request.urlopen(rr,timeout=6) as resp: sha=json.loads(resp.read()).get('sha','')
    except: sha=''
    data={'message':'proxy ok','content':base64.b64encode(json.dumps({'ts':TSF,'results':result}).encode()).decode()}
    if sha: data['sha']=sha
    req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
    with urllib.request.urlopen(req,timeout=10) as resp: print('GH:','OK' if 'content' in json.loads(resp.read()) else 'FAIL')
except Exception as e: print('GH error:',str(e)[:50])
print('DONE')
