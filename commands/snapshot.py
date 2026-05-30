import subprocess,os,json,datetime,urllib.request,base64

GH=open("/home/k/vnt-config-gh.txt").read().strip()
REPO="virtualnetworkteam-VNT/VNTCaller"
TSF=datetime.datetime.now().strftime("%Y%m%d_%H%M")
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def gh_save(R):
    try:
        hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
        try:
            rr=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get("sha","")
        except: sha=""
        data={"message":"handover snap","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
            data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp: return "content" in json.loads(resp.read())
    except Exception as e: print("GH:",str(e)[:30]); return False

import urllib.request as ur
def chk(url,t=5):
    try:
        with ur.urlopen(ur.Request(url,headers={"User-Agent":"VNT"}),timeout=t) as r:
            return r.status,len(r.read())
    except Exception as e: return 0,str(e)[:30]

R={"ts":TSF}
for name,url in [
    ("portal_8888","http://127.0.0.1:8888/api/health"),
    ("vntworld","https://vntworld.com/dashboard.html"),
    ("nextcloud","http://192.168.10.10/"),
]:
    st,sz=chk(url)
    R[name]=f"{'PASS' if st in [200,301,302] else 'FAIL'} {st} {sz}b"

r_ss=subprocess.run(["systemctl","--user","is-active","vnt-portal"],capture_output=True,text=True)
r_sys=subprocess.run(["systemctl","is-active","vnt-portal"],capture_output=True,text=True)
R["systemd_user"]=(r_ss.stdout+r_ss.stderr).strip()
R["systemd_sys"]=(r_sys.stdout+r_sys.stderr).strip()
R["crontab"]=subprocess.run(["crontab","-l"],capture_output=True,text=True).stdout.strip()[:200]
R["portal_py_size"]=os.path.getsize("/home/k/vnt-web/portal_server.py") if os.path.exists("/home/k/vnt-web/portal_server.py") else 0
R["mia_md_exists"]=os.path.exists("/home/k/.openclaw/agents/mia.md")
R["mia_v2_exists"]=os.path.exists("/home/k/vnt-agents/mia_v2.py")
R["dashboard_size"]=subprocess.run(["bash","-c","stat -c %s /var/www/html/dashboard.html 2>/dev/null || echo 0"],capture_output=True,text=True).stdout.strip()

gh_save(R)
for k,v in R.items(): print(f"  {k}: {str(v)[:80]}")
print("DONE")
