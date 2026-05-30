import subprocess,os,json,datetime,urllib.request,base64

GH=open("/home/k/vnt-config-gh.txt").read().strip()
REPO="virtualnetworkteam-VNT/VNTCaller"
TSF=datetime.datetime.now().strftime("%Y%m%d_%H%M")
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def run(c,t=10):
    r=subprocess.run(c,shell=True,capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def gh_save(R):
    try:
        hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
        try:
            rr=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get("sha","")
        except: sha=""
        data={"message":"mia oc","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
            data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp: return "content" in json.loads(resp.read())
    except Exception as e: print("GH:",str(e)[:30]); return False

MIA_PROMPT = (
    "You are Mia, receptionist at VNT World AI Division. "
    "Be warm, friendly, and completely natural. Never use robotic phrases. "
    "Reply in the SAME language as the person writes. "
    "Arabic in -> Arabic out. Urdu in -> Urdu out. French in -> French out. English in -> English out. "
    "If they send audio, reply with audio. Keep replies short and natural. "
    "NEVER say things like I am functioning normally or I am processing your request. "
    "Just talk like a normal friendly human. Say Im good thanks! not I am operating optimally."
)

print(TSF,"MIA OPENCLAW INTEGRATION")
R={}

oc_path="/home/k/.openclaw/openclaw.json"
if os.path.exists(oc_path):
    try:
        oc=json.load(open(oc_path))
        R["keys"]=str(list(oc.keys()))

        agents=oc.get("agents",[])
        R["agents_type"]=type(agents).__name__
        R["agents_count"]=len(agents) if isinstance(agents,(list,dict)) else "?"

        if isinstance(agents,list):
            for i,a in enumerate(agents[:6]):
                nm=a.get("name",a.get("id","?"))
                R[f"a{i}"]=f"{nm}:port={a.get('port','?')}"
            mia_idx=None
            for i,a in enumerate(agents):
                n=str(a.get("name","")).lower()
                p=str(a.get("port",""))
                if "mia" in n or p=="9999":
                    mia_idx=i
                    break
            if mia_idx is not None:
                oc["agents"][mia_idx]["system_prompt"]=MIA_PROMPT
                oc["agents"][mia_idx]["multilingual"]=True
                oc["agents"][mia_idx]["audio_reply"]=True
                open(oc_path,"w").write(json.dumps(oc,indent=2))
                R["mia_updated"]="YES agents["+str(mia_idx)+"]"
            else:
                names=[(a.get("name","?"),a.get("port","?")) for a in agents]
                R["all_agents"]=str(names[:15])
                R["mia_found"]="not found"

        elif isinstance(agents,dict):
            R["agent_keys"]=str(list(agents.keys())[:12])
            mia_key=next((k for k in agents if "mia" in k.lower()),None)
            if mia_key:
                oc["agents"][mia_key]["system_prompt"]=MIA_PROMPT
                open(oc_path,"w").write(json.dumps(oc,indent=2))
                R["mia_updated"]="YES key:"+mia_key
            else:
                R["mia_found"]="not in dict"

        for d2 in ["/home/k/.openclaw/agents","/home/k/.openclaw/personas"]:
            if os.path.isdir(d2):
                R["dir_"+d2.split("/")[-1]]=run("ls "+d2)[:100]

    except Exception as e:
        R["oc_err"]=str(e)[:60]
        R["oc_raw"]=open(oc_path).read()[:500]
else:
    R["oc"]="not found"
    R["home_k"]=run("ls /home/k/")[:300]

try:
    with urllib.request.urlopen("http://127.0.0.1:8888/api/health",timeout=5) as r2:
        R["portal"]="PASS "+json.loads(r2.read()).get("status","?")
except Exception as e:
    R["portal"]="FAIL:"+str(e)[:30]

gh_save(R)
for k,v in R.items(): print(f"  {k}: {str(v)[:80]}")
print("DONE")
