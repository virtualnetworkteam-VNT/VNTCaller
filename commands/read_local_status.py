import json,base64,urllib.request,os
GH=open('/home/k/vnt-config-gh.txt').read().strip()
REPO='virtualnetworkteam-VNT/VNTCaller'
f='/home/k/vnt-status.json'
if os.path.exists(f):
    content=open(f).read()
    print('STATUS FILE:',content[:500])
    hdr={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github.v3+json'}
    try:
        r=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',headers=hdr)
        with urllib.request.urlopen(r,timeout=8) as rr: sha=json.loads(rr.read()).get('sha','')
    except: sha=''
    data={'message':'status from local file','content':base64.b64encode(content.encode()).decode()}
    if sha: data['sha']=sha
    req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/relay_result.json',data=json.dumps(data).encode(),headers=hdr,method='PUT')
    with urllib.request.urlopen(req,timeout=12) as r:
        result=json.loads(r.read())
        print('GH push:','OK' if 'content' in result else 'FAIL')
else:
    print('STATUS FILE NOT FOUND - status_check.py did not run yet')
