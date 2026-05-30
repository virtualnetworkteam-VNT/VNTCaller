import subprocess,os,json,datetime,urllib.request,base64

GH=open("/home/k/vnt-config-gh.txt").read().strip()
REPO="virtualnetworkteam-VNT/VNTCaller"
TSF=datetime.datetime.now().strftime("%Y%m%d_%H%M")
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
AGENTS="/home/k/.openclaw/agents"

def gh_api(path):
    hdr={"Authorization":"Bearer "+GH,"Accept":"application/vnd.github.v3+json"}
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/contents/{path}",headers=hdr),timeout=30).read())

def gh_save(R):
    try:
        hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
        try:
            rr=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get("sha","")
        except: sha=""
        data={"message":"mia install","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
            data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp: return "content" in json.loads(resp.read())
    except Exception as e: print("GH:",str(e)[:30]); return False

print(TSF,"INSTALL MIA FILES")
R={}

for fname,dest in [("mia.md",AGENTS+"/mia.md"),("mia.json",AGENTS+"/mia.json"),("mia_v2.py","/home/k/vnt-agents/mia_v2.py")]:
    try:
        fd=gh_api(fname)
        raw=base64.b64decode(fd["content"].replace("\n",""))
        open(dest,"wb").write(raw)
        R[fname]="INSTALLED "+dest
        print(f"  {fname} -> {dest}")
    except Exception as e:
        R[fname]="FAIL:"+str(e)[:40]

# Verify
for f2 in [AGENTS+"/mia.md",AGENTS+"/mia.json","/home/k/vnt-agents/mia_v2.py"]:
    exists=os.path.exists(f2)
    sz=os.path.getsize(f2) if exists else 0
    print(f"  {f2}: {'OK '+str(sz)+'b' if exists else 'MISSING'}")

# Verify portal still up
try:
    with urllib.request.urlopen("http://127.0.0.1:8888/api/health",timeout=5) as r2:
        R["portal"]="PASS "+json.loads(r2.read()).get("status","?")
except Exception as e: R["portal"]="FAIL:"+str(e)[:20]

# Update MemPalace
try:
    open(MP,"a").write("\n### Mia v2 Installed ["+TSF+"]\nFiles: mia.md, mia.json, mia_v2.py\nMultilingual: EN/AR/UR/FR/HI. Audio-in=Audio-out. Human personality.\n")
    R["mempalace"]="WRITTEN"
except Exception as e: R["mempalace"]="FAIL:"+str(e)[:20]

gh_save(R)
for k,v in R.items(): print(f"  {k}: {str(v)[:80]}")
print("DONE")
