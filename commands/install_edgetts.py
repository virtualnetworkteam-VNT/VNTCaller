import subprocess, json, base64, datetime, time, urllib.request

M4  = "192.168.10.94"
GH  = open("/home/k/vnt-config-gh.txt").read().strip()
REPO= "virtualnetworkteam-VNT/VNTCaller"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")
P1  = "192.168.10.19"
PY  = "/Users/alias/miniforge3/envs/vnt/bin/python"
PIP = "/Users/alias/miniforge3/envs/vnt/bin/pip"

def m4(c,t=60):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5",
        "-o","BatchMode=yes","Alias@"+M4,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def rx1(c,t=10):
    r=subprocess.run(["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=5",
        "root@"+P1,c],capture_output=True,text=True,timeout=t)
    return (r.stdout+r.stderr).strip()

def gh_save(R):
    try:
        hdr={"Authorization":"Bearer "+GH,"Content-Type":"application/json","Accept":"application/vnd.github.v3+json"}
        try:
            rr=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",headers=hdr)
            with urllib.request.urlopen(rr,timeout=5) as resp: sha=json.loads(resp.read()).get("sha","")
        except: sha=""
        data={"message":"edge-tts result","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
            data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp: return "content" in json.loads(resp.read())
    except Exception as e: print("GH:",str(e)[:30]); return False

print(TSF,"INSTALL EDGE-TTS + FIX AUDIO")
R={}

# Install edge-tts
print("[1] Installing edge-tts...")
install=m4(PIP+" install edge-tts 2>&1 | tail -3",t=60)
print("  Install:",install[:100])
R["install"]=install[:80]

# Verify
verify=m4(PY+" -c \"import edge_tts; print(edge_tts.__version__)\" 2>/dev/null || echo FAIL",t=10)
print("  edge-tts:",verify)
R["edge_tts"]=verify

# Write and test audio script
audio_py="""import asyncio,sys,os,json,datetime
async def main():
    text=sys.argv[1] if len(sys.argv)>1 else "VNT ready"
    voice="en-US-AriaNeural"
    od="/Users/alias/vnt-studio/generated"
    os.makedirs(od,exist_ok=True)
    fname="audio_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".mp3"
    out=os.path.join(od,fname)
    try:
        import edge_tts
        await edge_tts.Communicate(text,voice).save(out)
        print(json.dumps({"status":"ok","url":"/generated/"+fname,"path":out}))
    except Exception as e:
        print(json.dumps({"status":"error","error":str(e)}))
asyncio.run(main())
"""

audio_b64=base64.b64encode(audio_py.encode()).decode()
m4("echo "+audio_b64+" | base64 -d > /Users/alias/vnt-studio/generate_audio.py",t=10)
print("[2] Audio script written")

# Test directly
audio_result=m4(PY+" /Users/alias/vnt-studio/generate_audio.py 'VNT AI Division is online'",t=30)
print("  Direct test:",audio_result[:100])
R["audio_direct"]=audio_result[:100]

# Restart studio API
print("[3] Restart studio API...")
m4("pkill -f studio_api 2>/dev/null; sleep 2; nohup "+PY+" /Users/alias/vnt-studio/studio_api.py > /tmp/studio.log 2>&1 &",t=10)
time.sleep(6)

# Test audio via API
print("[4] Audio via API...")
try:
    body=json.dumps({"text":"VNT World AI Division is operational","type":"speech"}).encode()
    req=urllib.request.Request("http://"+M4+":3333/generate-audio",
        data=body,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=30) as r:
        d=json.loads(r.read())
        ok=d.get("status")=="ok"
        R["audio_api"]="PASS url="+str(d.get("url","?"))[:40] if ok else "FAIL:"+str(d)[:60]
        print("  API:",str(d)[:80])
except Exception as e:
    R["audio_api"]="FAIL:"+str(e)[:50]
    log=m4("tail -8 /tmp/studio.log 2>/dev/null",t=8)
    print("  FAIL:",str(e)[:60])
    print("  Log:",log[:200])
    R["studio_log"]=log[:100]

# Image confirm
print("[5] Image confirm...")
try:
    body=json.dumps({"prompt":"VNT AI futuristic city neon blue","width":256,"height":256,"steps":8}).encode()
    req=urllib.request.Request("http://"+M4+":3333/generate",
        data=body,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=120) as r:
        d2=json.loads(r.read())
        oki=d2.get("status")=="ok"
        R["image"]="PASS url="+str(d2.get("url","?"))[:40] if oki else "FAIL:"+str(d2)[:40]
        print("  Image:","PASS" if oki else str(d2)[:60])
except Exception as e:
    R["image"]="FAIL:"+str(e)[:40]
    print("  Image FAIL:",str(e)[:50])

# Sites
ct108=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' http://192.168.10.13/ --connect-timeout 5")
vnt=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' http://vntworld.com/ --connect-timeout 6")
R["ct108"]=ct108; R["vntworld"]=vnt
print(f"CT108:{ct108} vntworld:{vnt}")

gh_save(R)
passed=sum(1 for v in R.values() if "PASS" in str(v) or "200" in str(v))
print(f"\nSCORE: {passed}/{len(R)}")
for k,v in R.items(): print(f"  {'OK' if 'PASS' in str(v) or '200' in str(v) else 'FAIL'} {k}: {str(v)[:65]}")
print("DONE")
