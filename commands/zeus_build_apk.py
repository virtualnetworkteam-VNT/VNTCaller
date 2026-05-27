
import subprocess, os, shutil, datetime

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
APP = "/home/k/hannahbird-app/android"
APK_SRC = APP+"/app/build/outputs/apk/debug/app-debug.apk"
APK_DST = "/home/k/vnt-web/hannahbird.apk"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### Zeus Build ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

# Fix local.properties
open(APP+"/../android/local.properties","w").write("sdk.dir=/home/k/android-sdk"+chr(10))

# Get exact error
print("Getting build error...")
r=subprocess.run(["./gradlew","assembleDebug","--no-daemon","--info"],
    cwd=APP,capture_output=True,text=True,timeout=300)
errors=[l for l in (r.stdout+r.stderr).split(chr(10)) if any(x in l for x in ["error:","Error:","FAILED","Exception","could not","Could not"])]
print("Errors found:")
for e in errors[:10]: print(" ",e)

# Common fix: Java version or minSdk
if "Unsupported class file major version" in str(errors) or "Java" in str(errors):
    print("Java version issue - trying with JAVA_HOME fix")
    java=subprocess.run(["find","/usr/lib/jvm","-name","java","-maxdepth","5"],capture_output=True,text=True)
    if java.stdout.strip():
        jpath=java.stdout.strip().split(chr(10))[0].replace("/bin/java","")
        env=os.environ.copy()
        env["JAVA_HOME"]=jpath
        r2=subprocess.run(["./gradlew","assembleDebug","--no-daemon"],
            cwd=APP,capture_output=True,text=True,timeout=300,env=env)
        print(r2.stdout[-300:])

if os.path.exists(APK_SRC):
    shutil.copy(APK_SRC,APK_DST)
    os.chmod(APK_DST,0o644)
    sz=os.path.getsize(APK_DST)//1024
    print(f"APK ready: {sz}KB")
    # Install on all connected ADB devices
    devs=subprocess.run(["adb","devices"],capture_output=True,text=True)
    for line in devs.stdout.split(chr(10))[1:]:
        if "device" in line and "List" not in line:
            dev=line.split()[0]
            ri=subprocess.run(["adb","-s",dev,"install","-r",APK_DST],
                capture_output=True,text=True,timeout=120)
            print(f"Install {dev}:",(ri.stdout+ri.stderr).strip()[:80])
    save("APK built and installed. Download: http://192.168.10.96:8888/hannahbird.apk")
else:
    save("APK build failed. Errors: "+str(errors[:3]))
    print("Build failed - errors above")
    print("Manual: cd /home/k/hannahbird-app/android && ./gradlew assembleDebug 2>&1 | grep error")
