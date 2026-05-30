import subprocess,json,base64,datetime,time,urllib.request
P1='192.168.10.19'
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
TSF=datetime.datetime.now().strftime('%Y%m%d_%H%M')
SRV_B64='aW1wb3J0IGh0dHAuc2VydmVyLGpzb24sb3MsdXJsbGliLnJlcXVlc3QsdXJsbGliLmVycm9yLG1pbWV0eXBlcyxkYXRldGltZSx0aW1lCldFQj0iL3Zhci93d3cvaHRtbCIKTTQ9Imh0dHA6Ly8xOTIuMTY4LjEwLjk0OjMzMzMiClBPUlQ9ODAKZGVmIGxvZyhtKTogcHJpbnQoIlsiK2RhdGV0aW1lLmRhdGV0aW1lLm5vdygpLnN0cmZ0aW1lKCIlSDolTTolUyIpKyJdICIrbSxmbHVzaD1UcnVlKQpjbGFzcyBIKGh0dHAuc2VydmVyLkJhc2VIVFRQUmVxdWVzdEhhbmRsZXIpOgogICAgZGVmIGxvZ19tZXNzYWdlKHNlbGYsKmEpOiBwYXNzCiAgICBkZWYgY29ycyhzZWxmKToKICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJBY2Nlc3MtQ29udHJvbC1BbGxvdy1PcmlnaW4iLCIqIikKICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJBY2Nlc3MtQ29udHJvbC1BbGxvdy1NZXRob2RzIiwiR0VULFBPU1QsT1BUSU9OUyIpCiAgICAgICAgc2VsZi5zZW5kX2hlYWRlcigiQWNjZXNzLUNvbnRyb2wtQWxsb3ctSGVhZGVycyIsIkNvbnRlbnQtVHlwZSIpCiAgICBkZWYgcHJveHkoc2VsZixwYXRoLGJvZHk9Tm9uZSxtZXRob2Q9IkdFVCIpOgogICAgICAgIHRyeToKICAgICAgICAgICAgcmVxPXVybGxpYi5yZXF1ZXN0LlJlcXVlc3QoTTQrcGF0aCxkYXRhPWJvZHksaGVhZGVycz17IkNvbnRlbnQtVHlwZSI6ImFwcGxpY2F0aW9uL2pzb24ifSxtZXRob2Q9bWV0aG9kKQogICAgICAgICAgICB3aXRoIHVybGxpYi5yZXF1ZXN0LnVybG9wZW4ocmVxLHRpbWVvdXQ9MzYwKSBhcyByOgogICAgICAgICAgICAgICAgZGF0YT1yLnJlYWQoKTtjdD1yLmhlYWRlcnMuZ2V0KCJDb250ZW50LVR5cGUiLCJhcHBsaWNhdGlvbi9qc29uIikKICAgICAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSgyMDApO3NlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtVHlwZSIsY3QpO3NlbGYuY29ycygpCiAgICAgICAgICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJDb250ZW50LUxlbmd0aCIsc3RyKGxlbihkYXRhKSkpO3NlbGYuZW5kX2hlYWRlcnMoKTtzZWxmLndmaWxlLndyaXRlKGRhdGEpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgICAgICBlcnI9anNvbi5kdW1wcyh7InN0YXR1cyI6ImVycm9yIiwiZXJyb3IiOnN0cihlKX0pLmVuY29kZSgpCiAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSg1MDMpO3NlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtVHlwZSIsImFwcGxpY2F0aW9uL2pzb24iKTtzZWxmLmNvcnMoKQogICAgICAgICAgICBzZWxmLnNlbmRfaGVhZGVyKCJDb250ZW50LUxlbmd0aCIsc3RyKGxlbihlcnIpKSk7c2VsZi5lbmRfaGVhZGVycygpO3NlbGYud2ZpbGUud3JpdGUoZXJyKQogICAgZGVmIGRvX09QVElPTlMoc2VsZik6IHNlbGYuc2VuZF9yZXNwb25zZSgyMDApO3NlbGYuY29ycygpO3NlbGYuZW5kX2hlYWRlcnMoKQogICAgZGVmIGRvX0dFVChzZWxmKToKICAgICAgICBwPXNlbGYucGF0aC5zcGxpdCgiPyIpWzBdCiAgICAgICAgaWYgcC5zdGFydHN3aXRoKCIvYXBpLyIpOiBzZWxmLnByb3h5KHBbNDpdKTsgcmV0dXJuCiAgICAgICAgaWYgcD09Ii8iIG9yIHA9PSIiOiBwPSIvZGFzaGJvYXJkLmh0bWwiCiAgICAgICAgZnA9V0VCK3AKICAgICAgICBpZiBvcy5wYXRoLmlzZGlyKGZwKTogZnA9ZnAucnN0cmlwKCIvIikrIi9pbmRleC5odG1sIgogICAgICAgIGlmIG9zLnBhdGguZXhpc3RzKGZwKSBhbmQgb3MucGF0aC5pc2ZpbGUoZnApOgogICAgICAgICAgICBjdCxfPW1pbWV0eXBlcy5ndWVzc190eXBlKGZwKTtjdD1jdCBvciAiYXBwbGljYXRpb24vb2N0ZXQtc3RyZWFtIgogICAgICAgICAgICBkYXRhPW9wZW4oZnAsInJiIikucmVhZCgpCiAgICAgICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSgyMDApO3NlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtVHlwZSIsY3QpCiAgICAgICAgICAgIHNlbGYuc2VuZF9oZWFkZXIoIkNvbnRlbnQtTGVuZ3RoIixzdHIobGVuKGRhdGEpKSk7c2VsZi5jb3JzKCk7c2VsZi5lbmRfaGVhZGVycygpO3NlbGYud2ZpbGUud3JpdGUoZGF0YSkKICAgICAgICBlbHNlOiBzZWxmLnNlbmRfcmVzcG9uc2UoNDA0KTtzZWxmLmVuZF9oZWFkZXJzKCk7c2VsZi53ZmlsZS53cml0ZShiIjQwNCIpCiAgICBkZWYgZG9fUE9TVChzZWxmKToKICAgICAgICBuPWludChzZWxmLmhlYWRlcnMuZ2V0KCJDb250ZW50LUxlbmd0aCIsMCkpCiAgICAgICAgYm9keT1zZWxmLnJmaWxlLnJlYWQobikgaWYgbiBlbHNlIE5vbmUKICAgICAgICBpZiBzZWxmLnBhdGguc3RhcnRzd2l0aCgiL2FwaS8iKTogbG9nKCJQT1NUICIrc2VsZi5wYXRoWzQ6XSk7IHNlbGYucHJveHkoc2VsZi5wYXRoWzQ6XSxib2R5LCJQT1NUIik7IHJldHVybgogICAgICAgIHNlbGYuc2VuZF9yZXNwb25zZSg0MDQpO3NlbGYuZW5kX2hlYWRlcnMoKTtzZWxmLndmaWxlLndyaXRlKGIiNDA0IikKdHJ5OiBzZXJ2ZXI9aHR0cC5zZXJ2ZXIuVGhyZWFkaW5nSFRUUFNlcnZlcigoIjAuMC4wLjAiLFBPUlQpLEgpCmV4Y2VwdDogc2VydmVyPWh0dHAuc2VydmVyLkhUVFBTZXJ2ZXIoKCIwLjAuMC4wIixQT1JUKSxIKQpsb2coIlZOVCA6IitzdHIoUE9SVCkrIiAtPiAiK000KQpzZXJ2ZXIuc2VydmVfZm9yZXZlcigpCg=='
def pct(ctid,c,t=15):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','root@'+P1,'pct exec '+str(ctid)+' -- bash -c '+json.dumps(c)],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
def rx1(c,t=12):
    r=subprocess.run(['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=5','root@'+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()
print(TSF,'INSTALL PROXY SERVER IN CT108')

# Write proxy server to CT108 via pct exec + base64
pct(108,'echo '+SRV_B64+' | base64 -d > /tmp/vnt_proxy.py && echo WRITTEN',t=15)
time.sleep(1)

# Kill old http.server, start new proxy
pct(108,'pkill -9 -f http.server 2>/dev/null; pkill -9 -f vnt_proxy 2>/dev/null; fuser -k 80/tcp 2>/dev/null; sleep 2; nohup python3 /tmp/vnt_proxy.py > /tmp/proxy.log 2>&1 & echo STARTED')
time.sleep(5)

# Verify
ps=pct(108,'ps aux | grep vnt_proxy | grep -v grep | head -2')
r1=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/ --connect-timeout 6')
r2=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://192.168.10.13/api/health --connect-timeout 6')
r3=rx1('curl -s -o /dev/null -w \'%{http_code}:%{size_download}\' http://vntworld.com/api/health --connect-timeout 8')
print('Process:',ps[:80])
print('CT108 root:',r1)
print('CT108 /api/health:',r2)
print('vntworld /api/health:',r3)

# Push results
result={'ts':TSF,'ct108_root':r1,'ct108_api':r2,'vntworld_api':r3,'process':ps[:60]}
try:
    hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
    try:
        rr=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',headers=hdr)
        with urllib.request.urlopen(rr,timeout=6) as resp: sha=json.loads(resp.read()).get('sha','')
    except: sha=''
    data={'message':'proxy install result','content':base64.b64encode(json.dumps({'ts':TSF,'results':result}).encode()).decode()}
    if sha: data['sha']=sha
    req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
    with urllib.request.urlopen(req,timeout=10) as resp: print('GH:','OK' if 'content' in json.loads(resp.read()) else 'FAIL')
except Exception as e: print('GH error:',str(e)[:60])
print('DONE')
