
import subprocess, os, time, datetime, shutil

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
WEB_DIR = "/home/k/vnt-web"
APP_DIR = "/home/k/hannahbird-app"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### APK ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

# Check where webserver is serving from
print("=== Web server check ===")
r=subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}",
    "http://127.0.0.1:8888/hannahbird.html"],capture_output=True,text=True,timeout=5)
print("hannahbird.html via :8888:",r.stdout.strip())

r2=subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}",
    "http://127.0.0.1:3333/generated/hannahbird.apk"],capture_output=True,text=True,timeout=5)
print("APK via :3333:",r2.stdout.strip())

# Check if APK exists anywhere
apk_paths=[
    APP_DIR+"/android/app/build/outputs/apk/debug/app-debug.apk",
    WEB_DIR+"/generated/hannahbird.apk",
    "/mnt/vnt-data/FileServer/VNT_World_AI_Division/generated_media/hannahbird.apk",
]
apk=None
for p in apk_paths:
    if os.path.exists(p):
        size=os.path.getsize(p)
        print(f"APK found: {p} ({size//1024}KB)")
        apk=p
        break
    else:
        print(f"Not found: {p}")

if not apk:
    # Build it
    print("Building APK...")
    sdk=None
    r3=subprocess.run(["find","/home/k","-name","local.properties","-maxdepth","7"],
        capture_output=True,text=True)
    for lp in r3.stdout.strip().split(chr(10)):
        if lp and os.path.exists(lp) and "sdk.dir" in open(lp).read():
            for line in open(lp).read().split(chr(10)):
                if line.startswith("sdk.dir="):
                    p=line.split("=",1)[1].strip()
                    if os.path.exists(p+"/build-tools"): sdk=p; break
        if sdk: break

    if not sdk:
        r4=subprocess.run("find /home /opt -name aapt 2>/dev/null | head -1",
            shell=True,capture_output=True,text=True)
        if r4.stdout.strip():
            sdk="/".join(r4.stdout.strip().split("/")[:-3])
            print("SDK via aapt:",sdk)

    if sdk:
        open(APP_DIR+"/android/local.properties","w").write("sdk.dir="+sdk+chr(10))
        os.makedirs(APP_DIR+"/www",exist_ok=True)
        shutil.copy(WEB_DIR+"/hannahbird.html",APP_DIR+"/www/index.html")
        subprocess.run("cd "+APP_DIR+" && npx cap sync android 2>&1 | tail -3",
            shell=True,capture_output=True,timeout=60)
        build=subprocess.run(["./gradlew","assembleDebug","--no-daemon","--stacktrace"],
            cwd=APP_DIR+"/android",capture_output=True,text=True,timeout=600)
        built_apk=APP_DIR+"/android/app/build/outputs/apk/debug/app-debug.apk"
        if os.path.exists(built_apk):
            apk=built_apk
            print("APK built:",os.path.getsize(apk)//1024,"KB")
        else:
            print("Build failed:",build.stdout[-400:])
            print(build.stderr[-200:])
    else:
        print("SDK not found")

# Copy APK to webserver with correct permissions
if apk:
    dst=WEB_DIR+"/hannahbird.apk"
    shutil.copy(apk,dst)
    os.chmod(dst,0o644)
    print(f"APK at: {dst}")

    # Also copy to generated
    gen_dst=WEB_DIR+"/generated/hannahbird.apk"
    os.makedirs(os.path.dirname(gen_dst),exist_ok=True)
    shutil.copy(apk,gen_dst)
    os.chmod(gen_dst,0o644)
    print(f"APK at: {gen_dst}")

    # Verify webserver can serve it
    r5=subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}",
        "http://127.0.0.1:8888/hannahbird.apk"],capture_output=True,text=True,timeout=5)
    print("APK via :8888:",r5.stdout.strip())

    # Try ADB install
    print("Installing on Redmi...")
    subprocess.run(["adb","connect","192.168.10.191:5555"],capture_output=True,timeout=10)
    time.sleep(2)
    for dev in ["192.168.10.191:5555","6db1f3a0"]:
        ri=subprocess.run(["adb","-s",dev,"install","-r","-t",apk],
            capture_output=True,text=True,timeout=120)
        out=(ri.stdout+ri.stderr).strip()
        print(f"ADB {dev}:",out[:100])
        if "Success" in out:
            print("INSTALLED on Redmi!")
            break

    save("APK ready"+chr(10)+"Download: http://192.168.10.96:8888/hannahbird.apk")
    print("=========================")
    print("APK DOWNLOAD URL:")
    print("http://192.168.10.96:8888/hannahbird.apk")
    print("=========================")
else:
    print("Could not build APK")
    print("Redmi can play web version: http://192.168.10.96:8888/hannahbird.html")
