import subprocess, datetime, json, urllib.request, os

P1  = "192.168.10.19"
CT  = "192.168.10.13"
M4  = "192.168.10.94"
GH  = open("/home/k/vnt-config-gh.txt").read().strip()
REPO= "virtualnetworkteam-VNT/VNTCaller"
MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")

def rx(h,c,t=20):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=6","root@"+h,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def chk(url,t=8):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"VNT/1.0"})
        with urllib.request.urlopen(req,timeout=t) as r: return r.status,len(r.read())
    except Exception as e: return 0,str(e)[:40]

def gh_push(path,content,msg):
    import base64
    headers={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
    try:
        r=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",headers=headers)
        with urllib.request.urlopen(r,timeout=8) as rr: sha=json.loads(rr.read()).get("sha","")
    except: sha=""
    data={"message":msg,"content":base64.b64encode(content.encode()).decode()}
    if sha: data["sha"]=sha
    req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/{path}",
        data=json.dumps(data).encode(),headers=headers,method="PUT")
    with urllib.request.urlopen(req,timeout=10) as r: return "content" in json.loads(r.read())

R={}
print("QUICK STATUS CHECK",TSF)

# CT108 web server
st,sz=chk(f"http://{CT}/dashboard.html")
R["ct108_web"]=f"{st} {sz}b"

# CT108 dashboard size
dash_sz=rx(P1,"pct exec 108 -- wc -c /var/www/html/dashboard.html 2>/dev/null")
R["dash_size"]=dash_sz[:50]

# Python http.server running?
ps=rx(P1,"pct exec 108 -- ps aux 2>/dev/null | grep 'http.server' | grep -v grep")
R["web_process"]=ps[:80] if ps else "NOT RUNNING"

# M4 API
m4=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5","-o","BatchMode=yes","Alias@"+M4,"curl -s http://localhost:3333/health 2>/dev/null"],capture_output=True,text=True,timeout=10)
R["m4_api"]=m4.stdout.strip()[:80] if m4.stdout else "offline"

# MSI proxy
st2,sz2=chk("http://127.0.0.1:8888/api/health")
R["msi_proxy"]=f"{st2} {sz2}b"

# vntworld.com
st3,sz3=chk("http://vntworld.com/dashboard.html",t=10)
R["vntworld"]=f"{st3} {sz3}b"

print(json.dumps(R,indent=2))

# Save result to GitHub so Claude can read it
gh_push("relay_result.json",json.dumps({"ts":TSF,"results":R},indent=2),"self-test results")
open(MP,"a").write("\n### QuickStatus ["+TSF+"]\n"+json.dumps(R)+"\n")
print("DONE")
