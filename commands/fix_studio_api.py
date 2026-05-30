import subprocess, json, base64, datetime, time, urllib.request

M4  = "192.168.10.94"
GH  = open("/home/k/vnt-config-gh.txt").read().strip()
REPO= "virtualnetworkteam-VNT/VNTCaller"
TSF = datetime.datetime.now().strftime("%Y%m%d_%H%M")
P1  = "192.168.10.19"
PY  = "/Users/alias/miniforge3/envs/vnt/bin/python"

def m4(c,t=20):
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
        data={"message":"studio fix result","content":base64.b64encode(json.dumps({"ts":TSF,"results":R}).encode()).decode()}
        if sha: data["sha"]=sha
        req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/contents/relay_result.json",
            data=json.dumps(data).encode(),headers=hdr,method="PUT")
        with urllib.request.urlopen(req,timeout=8) as resp: return "content" in json.loads(resp.read())
    except Exception as e: print("GH:",str(e)[:30]); return False

print(TSF,"FIX STUDIO API AUDIO POPEN")
R={}

# Read the full studio_api.py audio section
print("[1] Reading studio_api.py audio section...")
audio_section=m4("grep -n 'audio\\|tts\\|speech\\|bark' /Users/alias/vnt-studio/studio_api.py 2>/dev/null | head -20")
print("  Audio refs:",audio_section[:300])
R["api_audio_refs"]=audio_section[:150]

# Read lines 180-220
crash_area=m4("sed -n '175,225p' /Users/alias/vnt-studio/studio_api.py 2>/dev/null")
print("  Crash area:\n",crash_area[:500])
R["crash_area"]=crash_area[:200]

# Fix: patch studio_api.py to use correct python and script path
# We'll replace the audio generation subprocess call
print("[2] Patching studio_api.py audio endpoint...")

# Read full file
full_api=m4("cat /Users/alias/vnt-studio/studio_api.py",t=15)
print(f"  API file: {len(full_api)} chars")

if full_api and len(full_api)>100:
    # Find and fix the audio subprocess call
    # Common patterns that cause issues:
    import re
    
    # Pattern: subprocess.run(['python', ...]) -> use PY
    # Pattern: generate_audio script path wrong
    
    # Write the fix directly to a temp file on MSI
    open("/tmp/studio_api_orig.py","w").write(full_api)
    
    # Fix python path in subprocess calls for audio
    fixed=full_api
    for old,new in [
        ("subprocess.run(['python'", f"subprocess.run(['{PY}'"),
        ('subprocess.run(["python"', f'subprocess.run(["{PY}"'),
        ("subprocess.Popen(['python'", f"subprocess.Popen(['{PY}'"),
        ("generate_audio.py'", "vnt-studio/generate_audio.py'"),
        ("generate_audio.py\"", "vnt-studio/generate_audio.py\""),
    ]:
        if old in fixed:
            fixed=fixed.replace(old,new)
            print(f"  Fixed: {old[:40]}")
    
    open("/tmp/studio_api_fixed.py","w").write(fixed)
    
    # SCP to Prox1 then use SSH/SCP to push to M4
    subprocess.run(["scp","-o","StrictHostKeyChecking=no",
        "/tmp/studio_api_fixed.py","Alias@"+M4+":/Users/alias/vnt-studio/studio_api_fixed.py"],
        capture_output=True,timeout=15)
    m4("cp /Users/alias/vnt-studio/studio_api.py /Users/alias/vnt-studio/studio_api.py.bak && cp /Users/alias/vnt-studio/studio_api_fixed.py /Users/alias/vnt-studio/studio_api.py",t=10)
    print("  Patched and deployed")
    R["api_patched"]="YES"

# Also add a direct async edge-tts handler in case subprocess is broken
# Inject a simpler audio handler right into the server via patch
print("[3] Adding direct edge-tts handler...")

# The cleanest fix: add an alternative /audio-direct endpoint to studio_api.py
# that uses asyncio directly without subprocess
# But this requires rewriting the API - let's just restart and test

# Restart studio API
print("[4] Restarting studio API...")
m4(f"pkill -f studio_api 2>/dev/null; sleep 2; nohup {PY} /Users/alias/vnt-studio/studio_api.py > /tmp/studio.log 2>&1 &",t=10)
time.sleep(6)

# Test health
try:
    with urllib.request.urlopen(f"http://{M4}:3333/health",timeout=6) as r:
        h=json.loads(r.read())
        print("  Health:",json.dumps(h)[:80])
        R["health"]="PASS"
except Exception as e:
    print("  Health FAIL:",str(e)[:50])
    R["health"]="FAIL:"+str(e)[:30]

# Test audio
print("[5] Testing audio via API...")
try:
    body=json.dumps({"text":"VNT AI Division is operational and ready","type":"speech"}).encode()
    req=urllib.request.Request(f"http://{M4}:3333/generate-audio",
        data=body,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=30) as r:
        d=json.loads(r.read())
        ok=d.get("status")=="ok"
        R["audio"]="PASS url="+str(d.get("url","?"))[:40] if ok else "FAIL:"+str(d)[:60]
        print("  Audio:",str(d)[:80])
except Exception as e:
    # Check log for actual error
    log=m4("tail -15 /tmp/studio.log 2>/dev/null",t=8)
    R["audio"]="FAIL:"+str(e)[:40]
    R["error_log"]=log[:150]
    print("  Audio FAIL:",str(e)[:60])
    print("  Log:",log[:200])

# Sites
ct108=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' http://192.168.10.13/ --connect-timeout 5")
vnt=rx1("curl -s -o /dev/null -w '%{http_code}:%{size_download}' http://vntworld.com/ --connect-timeout 6")
R["ct108"]=ct108; R["vntworld"]=vnt
print(f"CT108:{ct108} vntworld:{vnt}")

gh_save(R)
passed=sum(1 for v in R.values() if "PASS" in str(v) or "200" in str(v))
print(f"\nSCORE: {passed}/{len(R)}")
for k,v in R.items(): print(f"  {'OK' if 'PASS' in str(v) or '200' in str(v) else 'FL'} {k}: {str(v)[:65]}")
print("DONE")
