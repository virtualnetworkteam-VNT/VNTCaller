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
        data={"message":"read alias md","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
            data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp: return "content" in json.loads(resp.read())
    except Exception as e: print("GH:",str(e)[:30]); return False

print(TSF,"READ ALIAS MD + MAIN JSON")
R={}
AGENTS="/home/k/.openclaw/agents"

for fname in ["alias.md","main.json","main"]:
    fpath=AGENTS+"/"+fname
    if os.path.exists(fpath):
        content=open(fpath).read() if os.path.isfile(fpath) else "IS_DIR"
        R[fname]=content[:600]
        print(f"\n=== {fname} ===")
        print(content[:400])

gh_save(R)
print("DONE")
