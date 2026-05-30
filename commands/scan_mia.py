import subprocess,os,json,datetime,urllib.request,base64

GH=open("/home/k/vnt-config-gh.txt").read().strip()
REPO="virtualnetworkteam-VNT/VNTCaller"
TSF=datetime.datetime.now().strftime("%Y%m%d_%H%M")
R={"ts":TSF}

def gh_save(R):
    try:
        hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
        try:
            rr=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp:sha=json.loads(resp.read()).get("sha","")
        except:sha=""
        data={"message":"mia scan","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha:data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp:return "content" in json.loads(resp.read())
    except Exception as e:print("GH:",str(e)[:30]);return False

# Find agent files
out=[]
for path in ["/home/k","/home/k/vnt-web","/home/k/.openclaw","/opt/vnt","/home/k/agents"]:
    if os.path.isdir(path):
        r=subprocess.run(["find",path,"-maxdepth",3,"-type","f","-name","*.py","-o","-name","*.json","-o","-name","*.js"],
            capture_output=True,text=True,timeout=10)
        for f in r.stdout.strip().split("\n"):
            if f and any(x in f.lower() for x in ["mia","agent","bot","openclaw","9999","whatsapp"]):
                sz=os.path.getsize(f) if os.path.exists(f) else 0
                out.append(f"{f} ({sz}b)")
R["agent_files"]=out[:20]

# Read OpenClaw config
oc="/home/k/.openclaw/openclaw.json"
if os.path.exists(oc):
    try:
        cfg=json.load(open(oc))
        R["openclaw_keys"]=list(cfg.keys())[:10]
        # Find Mia
        for section in ["agents","bots","personas"]:
            if section in cfg:
                agents=cfg[section]
                if isinstance(agents,list):
                    mia=[a for a in agents if "mia" in str(a).lower()]
                    R["mia_config"]=str(mia[0])[:300] if mia else "not found in list"
                elif isinstance(agents,dict):
                    mia={k:v for k,v in agents.items() if "mia" in k.lower()}
                    R["mia_config"]=str(list(mia.values())[0])[:300] if mia else "not found in dict"
    except Exception as e:
        R["openclaw_err"]=str(e)
        R["openclaw_raw"]=open(oc).read()[:500]
else:
    R["openclaw"]="not found"

# Check running processes
ps=subprocess.run(["ps","aux"],capture_output=True,text=True)
agent_procs=[l for l in ps.stdout.split("\n") if any(x in l.lower() for x in ["mia","9999","openclaw","agent"])]
R["running"]=agent_procs[:5]

# List home dir
ls=subprocess.run(["ls","-la","/home/k/"],capture_output=True,text=True)
R["home_k"]=ls.stdout[:400]

gh_save(R)
print(json.dumps(R,indent=2)[:800])
print("DONE")
