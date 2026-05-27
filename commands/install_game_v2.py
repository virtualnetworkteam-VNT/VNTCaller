
import subprocess, os, shutil, datetime, urllib.request, base64, json

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
WEB = "/home/k/vnt-web"
APP_WWW = "/home/k/hannahbird-app/www"
os.makedirs(APP_WWW, exist_ok=True)

# Get token from local relay config
relay = open("/home/k/github-relay.py").read()
GH_TOKEN = relay.split('GH = "')[1].split('"')[0]

# Download game HTML from GitHub
print("Downloading new game from GitHub...")
req = urllib.request.Request(
    "https://api.github.com/repos/virtualnetworkteam-VNT/VNTCaller/contents/game/hannahbird.html",
    headers={"Authorization": "Bearer "+GH_TOKEN, "Accept": "application/vnd.github.v3+json"}
)
with urllib.request.urlopen(req, timeout=15) as r:
    content = json.loads(r.read())["content"]

html = base64.b64decode(content)
print("Downloaded:", len(html), "bytes")

for path in [WEB+"/hannahbird.html", APP_WWW+"/index.html"]:
    open(path, "wb").write(html)
print("Written to web and app www")

# Sync + Build + Install
print("Syncing Capacitor...")
subprocess.run("export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 && cd /home/k/hannahbird-app && npx cap sync android 2>&1 | tail -3",
    shell=True, capture_output=True, text=True, timeout=60)

print("Building APK...")
r2=subprocess.run("export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 && cd /home/k/hannahbird-app/android && ./gradlew assembleDebug --no-daemon 2>&1 | tail -5",
    shell=True, capture_output=True, text=True, timeout=600)
print(r2.stdout.strip())

apk="/home/k/hannahbird-app/android/app/build/outputs/apk/debug/app-debug.apk"
if os.path.exists(apk):
    shutil.copy(apk, WEB+"/hannahbird.apk")
    os.chmod(WEB+"/hannahbird.apk", 0o644)
    print("APK:", os.path.getsize(apk)//1024, "KB")
    devs=subprocess.run(["adb","devices"],capture_output=True,text=True).stdout
    installed=False
    for line in devs.split(chr(10))[1:]:
        if "device" in line and "List" not in line:
            dev=line.split()[0]
            ri=subprocess.run(["adb","-s",dev,"install","-r","-t",apk],capture_output=True,text=True,timeout=120)
            out=(ri.stdout+ri.stderr).strip()
            print("Install",dev,":",out[:80])
            if "Success" in out:
                installed=True
                print("INSTALLED ON REDMI!")
                subprocess.run(["adb","-s",dev,"shell","monkey","-p","io.vnt.hannahbird","-c","android.intent.category.LAUNCHER","1"],capture_output=True,timeout=10)
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write(chr(10)+"### HannahBird v2 ["+ts+"]"+chr(10)+"Pigeon+fullscreen+music. Installed:"+str(installed)+chr(10))
    print("Done. APK: http://192.168.10.96:8888/hannahbird.apk")
else:
    print("Build failed:", r2.stderr[-200:])
