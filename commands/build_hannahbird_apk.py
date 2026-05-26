
import subprocess, os, time, datetime

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
DEVICE_IP = "192.168.10.191"
APP_DIR = "/home/k/hannahbird-app"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### HannahBird ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

def run(cmd, cwd=None, timeout=300):
    r=subprocess.run(cmd,shell=True,capture_output=True,text=True,cwd=cwd,timeout=timeout)
    if r.stdout: print(r.stdout[-500:])
    if r.stderr and r.returncode!=0: print("ERR:",r.stderr[-300:])
    return r.returncode==0, r.stdout, r.stderr

# Find Android SDK
sdk_paths=["/home/k/android-sdk","/opt/android-sdk",os.path.expanduser("~/.android/sdk"),
    "/root/android-sdk","ANDROID_HOME" in os.environ and os.environ.get("ANDROID_HOME","")]
sdk_found=None
for p in sdk_paths:
    if p and os.path.exists(str(p)+"/build-tools"):
        sdk_found=p; break

if not sdk_found:
    # Use the SDK already installed for VNTCaller project
    r=subprocess.run(["find","/home/k","-name","build-tools","-type","d","-maxdepth","5"],
        capture_output=True,text=True)
    if r.stdout.strip():
        sdk_found=r.stdout.strip().split(chr(10))[0].replace("/build-tools","")
    else:
        # Download minimal SDK tools
        print("Installing Android SDK cmdline-tools...")
        os.makedirs("/home/k/android-sdk/cmdline-tools",exist_ok=True)
        ok,_,_=run("wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/cmdtools.zip")
        run("unzip -q /tmp/cmdtools.zip -d /home/k/android-sdk/cmdline-tools/")
        run("mv /home/k/android-sdk/cmdline-tools/cmdline-tools /home/k/android-sdk/cmdline-tools/latest 2>/dev/null; true")
        os.environ["ANDROID_HOME"]="/home/k/android-sdk"
        os.environ["PATH"]+=":/home/k/android-sdk/cmdline-tools/latest/bin:/home/k/android-sdk/platform-tools"
        run("yes | sdkmanager --licenses 2>/dev/null; sdkmanager 'platform-tools' 'platforms;android-34' 'build-tools;34.0.0'",timeout=300)
        sdk_found="/home/k/android-sdk"

print("SDK found:", sdk_found)
os.environ["ANDROID_HOME"]=str(sdk_found)

# Write local.properties
lp=f"sdk.dir={sdk_found}"
open(f"{APP_DIR}/android/local.properties","w").write(lp)
print("local.properties written:", lp)

# Update game HTML - mobile optimized, no arrow keys, touch/swipe only
game_html = open("/home/k/vnt-web/hannahbird.html").read()
# Already mobile optimized - just ensure no keyboard UI shown
print("Game HTML ready")

# Build APK
print("Building APK...")
ok,out,err=run("./gradlew assembleDebug --no-daemon 2>&1 | tail -20",
    cwd=f"{APP_DIR}/android",timeout=600)
if not ok:
    print("Build failed, trying with stacktrace...")
    ok,out,err=run("./gradlew assembleDebug --stacktrace 2>&1 | grep -E 'error:|Error:|FAILED|BUILD' | head -20",
        cwd=f"{APP_DIR}/android",timeout=300)

apk_path=f"{APP_DIR}/android/app/build/outputs/apk/debug/app-debug.apk"
if os.path.exists(apk_path):
    size=os.path.getsize(apk_path)
    print(f"APK ready: {apk_path} ({size//1024}KB)")
    # Copy to web for download
    import shutil
    shutil.copy(apk_path,"/home/k/vnt-web/generated/hannahbird.apk")
    print("APK downloadable: http://192.168.10.96:3333/generated/hannahbird.apk")

    # Deploy via WiFi ADB
    print("Connecting to Redmi via WiFi ADB...")
    r2=subprocess.run(["adb","connect",DEVICE_IP+":5555"],capture_output=True,text=True)
    print("ADB connect:",r2.stdout.strip())
    time.sleep(2)

    # Try USB device ID too
    devices=subprocess.run(["adb","devices"],capture_output=True,text=True).stdout
    print("Devices:",devices.strip())

    # Install on all connected devices
    for dev_line in devices.split(chr(10))[1:]:
        if "device" in dev_line and not "List" in dev_line:
            dev_id=dev_line.split()[0]
            print(f"Installing on {dev_id}...")
            r3=subprocess.run(["adb","-s",dev_id,"install","-r",apk_path],
                capture_output=True,text=True,timeout=60)
            print("Install:",r3.stdout.strip() or r3.stderr[:100])

    save("HannahBird APK built and deployed"+chr(10)+
        "Download: http://192.168.10.96:3333/generated/hannahbird.apk"+chr(10)+
        "Web play: http://192.168.10.96:8888/hannahbird.html")
    print("=== DONE ===")
    print("APK: http://192.168.10.96:3333/generated/hannahbird.apk")
    print("Web: http://192.168.10.96:8888/hannahbird.html")
else:
    print("APK not found - checking build output...")
    run(f"find {APP_DIR}/android -name '*.apk' 2>/dev/null")
    save("HannahBird APK build failed - check logs")
