
import subprocess, os, time, datetime, shutil

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
REDMI_IP = "192.168.10.191"
APP_DIR = "/home/k/hannahbird-app"
APK_PATH = APP_DIR+"/android/app/build/outputs/apk/debug/app-debug.apk"
WEB_APK = "/home/k/vnt-web/generated/hannahbird.apk"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### HannahBird APK ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

# Step 1: Connect Redmi via WiFi ADB
print("Connecting Redmi via WiFi...")
subprocess.run(["adb","connect",REDMI_IP+":5555"],capture_output=True,timeout=10)
time.sleep(2)

# Check all connected devices
r=subprocess.run(["adb","devices"],capture_output=True,text=True)
print("Devices:",r.stdout.strip())

# Step 2: Check if APK exists
apk = None
for path in [APK_PATH, WEB_APK, "/home/k/vnt-web/generated/hannahbird.apk"]:
    if os.path.exists(path):
        apk = path
        print(f"APK found: {path} ({os.path.getsize(path)//1024}KB)")
        break

if not apk:
    print("APK not built yet - building now...")
    # Find SDK
    sdk = None
    r2=subprocess.run(["find","/home/k","-name","local.properties","-maxdepth","6"],
        capture_output=True,text=True)
    for lp in r2.stdout.strip().split(chr(10)):
        if lp and os.path.exists(lp):
            content=open(lp).read()
            if "sdk.dir" in content:
                for line in content.split(chr(10)):
                    if line.startswith("sdk.dir="):
                        p=line.split("=",1)[1].strip()
                        if os.path.exists(p): sdk=p; break
        if sdk: break

    if not sdk:
        r3=subprocess.run("find /home /opt -name aapt 2>/dev/null | head -1",
            shell=True,capture_output=True,text=True)
        if r3.stdout.strip():
            sdk=os.path.dirname(os.path.dirname(os.path.dirname(r3.stdout.strip())))

    if sdk:
        print("SDK:",sdk)
        lp=APP_DIR+"/android/local.properties"
        open(lp,"w").write("sdk.dir="+sdk+chr(10))
        # Sync game HTML
        os.makedirs(APP_DIR+"/www",exist_ok=True)
        if os.path.exists("/home/k/vnt-web/hannahbird.html"):
            shutil.copy("/home/k/vnt-web/hannahbird.html",APP_DIR+"/www/index.html")
        # Build
        subprocess.run("cd "+APP_DIR+" && npx cap sync android 2>&1 | tail -3",
            shell=True,capture_output=True,timeout=60)
        build=subprocess.run(["./gradlew","assembleDebug","--no-daemon"],
            cwd=APP_DIR+"/android",capture_output=True,text=True,timeout=600)
        print(build.stdout[-300:])
        if os.path.exists(APK_PATH):
            shutil.copy(APK_PATH,WEB_APK)
            apk=WEB_APK
            print("APK built successfully")
        else:
            print("Build output:",build.stderr[-200:])
    else:
        print("SDK not found - need Android SDK installed")

# Step 3: Install on Redmi
if apk and os.path.exists(apk):
    print(f"Installing {apk} on Redmi...")
    # Try WiFi ADB first
    for dev in [REDMI_IP+":5555","6db1f3a0"]:
        ri=subprocess.run(["adb","-s",dev,"install","-r","-t",apk],
            capture_output=True,text=True,timeout=120)
        out=(ri.stdout+ri.stderr).strip()
        print(f"Install on {dev}:",out[:150])
        if "Success" in out:
            print("INSTALLED SUCCESSFULLY")
            # Launch game
            subprocess.run(["adb","-s",dev,"shell","monkey","-p","io.vnt.hannahbird",
                "-c","android.intent.category.LAUNCHER","1"],capture_output=True,timeout=10)
            save("HannahBird installed on Redmi via WiFi ADB"+chr(10)+
                "APK: "+apk+chr(10)+"Download: http://192.168.10.96:3333/generated/hannahbird.apk")
            print("Game launched on Redmi!")
            break
    else:
        # Manual install via download link
        print("ADB install failed - use manual download:")
        print("On Redmi browser: http://192.168.10.96:3333/generated/hannahbird.apk")
        save("APK install failed via ADB - manual download needed"+chr(10)+
            "URL: http://192.168.10.96:3333/generated/hannahbird.apk")
else:
    print("No APK available")
    print("Manual install: http://192.168.10.96:3333/generated/hannahbird.apk")

# Set native dialer as default on Redmi
print("Setting native dialer as default...")
for dev in [REDMI_IP+":5555","6db1f3a0"]:
    subprocess.run(["adb","-s",dev,"shell","cmd","telecom",
        "set-default-dialer","com.android.dialer"],
        capture_output=True,timeout=10)
print("Native dialer set")

print("DONE")
print("If ADB failed, open this on Redmi browser:")
print("http://192.168.10.96:3333/generated/hannahbird.apk")
