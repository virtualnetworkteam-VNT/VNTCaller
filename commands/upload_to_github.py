
import subprocess, os, shutil, base64, json, datetime
import urllib.request

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
WEB = "/home/k/vnt-web"
APP = "/home/k/hannahbird-app/android"
KEYSTORE = "/home/k/VNTCaller/vnt-release-key.keystore"
KEY_PASS = "VNT@keystore2025"
KEY_ALIAS = "vntworld"
GH_TOKEN = open("/home/k/github-relay.py").read().split('GH = "')[1].split('"')[0]
GH_REPO = "virtualnetworkteam-VNT/VNTCaller"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### GitHub Upload ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

# Check what we have built
aab = APP+"/app/build/outputs/bundle/release/app-release.aab"
apk = APP+"/app/build/outputs/apk/debug/app-debug.apk"

print("AAB exists:", os.path.exists(aab))
print("APK exists:", os.path.exists(apk))

# If neither exists, build now
if not os.path.exists(aab) and not os.path.exists(apk):
    print("Nothing built yet - building APK first...")
    subprocess.run("export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 && cd /home/k/hannahbird-app/android && ./gradlew assembleDebug --no-daemon 2>&1 | tail -5",
        shell=True,capture_output=True,text=True,timeout=600)

# Pick best available file
upload_file = aab if os.path.exists(aab) else apk if os.path.exists(apk) else None

if not upload_file:
    print("No build output - something wrong with build")
    exit()

sz = os.path.getsize(upload_file)
fname = "hannahbird-release.aab" if upload_file.endswith(".aab") else "hannahbird-debug.apk"
print(f"Uploading {fname} ({sz//1024}KB) to GitHub releases...")

# Copy to web too
shutil.copy(upload_file, WEB+"/"+fname)
os.chmod(WEB+"/"+fname, 0o644)
print("Available at: http://192.168.10.96:8888/"+fname)

# Upload to GitHub releases
# First create a release
rel_data = json.dumps({
    "tag_name": "hannahbird-v1.0",
    "name": "HannahBird.io v1.0",
    "body": "HannahBird.io Game\n\nFeatures:\n- 7 birds including Pigeon\n- Unlimited levels\n- Powerups: Fire, Speed, Area Blast, Supercharge\n- Music and sound effects\n- Day/Evening/Night themes\n- Fullscreen mobile\n\nInstall: download and open on Android",
    "draft": False,
    "prerelease": True
}).encode()

req = urllib.request.Request(
    f"https://api.github.com/repos/{GH_REPO}/releases",
    data=rel_data,
    headers={"Authorization":"Bearer "+GH_TOKEN,"Content-Type":"application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req,timeout=15) as r:
        rel = json.loads(r.read())
    rel_id = rel.get("id")
    upload_url = rel.get("upload_url","").replace("{?name,label}","")
    print("Release created, ID:", rel_id)
except Exception as e:
    # Release may already exist - get existing
    print("Release create:", e)
    req2 = urllib.request.Request(
        f"https://api.github.com/repos/{GH_REPO}/releases/tags/hannahbird-v1.0",
        headers={"Authorization":"Bearer "+GH_TOKEN}
    )
    try:
        with urllib.request.urlopen(req2,timeout=10) as r2:
            rel = json.loads(r2.read())
        rel_id = rel.get("id")
        upload_url = rel.get("upload_url","").replace("{?name,label}","")
        print("Using existing release:", rel_id)
    except Exception as e2:
        print("Could not get release:", e2)
        rel_id = None
        upload_url = None

# Upload asset to release
if upload_url and rel_id:
    print("Uploading file to release...")
    file_data = open(upload_file,"rb").read()
    content_type = "application/octet-stream"
    req3 = urllib.request.Request(
        upload_url+"?name="+fname,
        data=file_data,
        headers={"Authorization":"Bearer "+GH_TOKEN,"Content-Type":content_type,"Content-Length":str(len(file_data))},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req3,timeout=120) as r3:
            asset = json.loads(r3.read())
        dl_url = asset.get("browser_download_url","")
        print("UPLOADED!")
        print("Download URL:", dl_url)
        save("HannahBird uploaded to GitHub Releases"+chr(10)+
            "Download: "+dl_url+chr(10)+
            "Also at: http://192.168.10.96:8888/"+fname+chr(10)+
            "Play Console: upload AAB to play.google.com/console (virtual.network.team@gmail.com)")
        print("Share this link with friends:")
        print(dl_url)
    except Exception as e3:
        print("Upload error:", e3)
        print("File available at: http://192.168.10.96:8888/"+fname)
else:
    # Fallback: push to GitHub repo contents
    print("Pushing to repo contents as fallback...")
    file_data = open(upload_file,"rb").read()
    if len(file_data) < 50*1024*1024:  # under 50MB
        payload = {"message":"HannahBird v1.0 game file","content":base64.b64encode(file_data).decode()}
        req4 = urllib.request.Request(
            f"https://api.github.com/repos/{GH_REPO}/contents/releases/{fname}",
            data=json.dumps(payload).encode(),
            headers={"Authorization":"Bearer "+GH_TOKEN,"Content-Type":"application/json"},
            method="PUT"
        )
        try:
            with urllib.request.urlopen(req4,timeout=120) as r4:
                result = json.loads(r4.read())
            dl_url = result.get("content",{}).get("html_url","")
            print("Pushed to repo:", dl_url)
            save("HannahBird in GitHub repo: "+dl_url)
        except Exception as e4:
            print("Repo push error:", e4)
    print("Direct download: http://192.168.10.96:8888/"+fname)
