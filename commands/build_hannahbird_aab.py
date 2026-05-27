
import subprocess, os, shutil, datetime

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
APP = "/home/k/hannahbird-app/android"
WEB = "/home/k/vnt-web"
KEYSTORE = "/home/k/VNTCaller/vnt-release-key.keystore"
KEY_PASS = "VNT@keystore2025"
KEY_ALIAS = "vntworld"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### AAB ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

print("Keystore exists:", os.path.exists(KEYSTORE))

# Write local.properties with signing info
open(APP+"/local.properties","w").write(
    "sdk.dir=/home/k/android-sdk"+chr(10)+
    "storeFile="+KEYSTORE+chr(10)+
    "storePassword="+KEY_PASS+chr(10)+
    "keyAlias="+KEY_ALIAS+chr(10)+
    "keyPassword="+KEY_PASS+chr(10)
)

# Check if signing config already in app/build.gradle
bg_path = APP+"/app/build.gradle"
bg = open(bg_path).read()
print("Has signingConfigs:", "signingConfigs" in bg)

if "signingConfigs" not in bg:
    signing_config = """
    signingConfigs {
        release {
            storeFile file(project.hasProperty("storeFile") ? project.storeFile : "debug.keystore")
            storePassword project.hasProperty("storePassword") ? project.storePassword : "android"
            keyAlias project.hasProperty("keyAlias") ? project.keyAlias : "androiddebugkey"
            keyPassword project.hasProperty("keyPassword") ? project.keyPassword : "android"
        }
    }
"""
    bg = bg.replace("    buildTypes {", signing_config+"    buildTypes {")
    bg = bg.replace("        release {", "        release { signingConfig signingConfigs.release")
    open(bg_path,"w").write(bg)
    print("Signing config added")

# Build release AAB
print("Building signed AAB...")
cmd = (
    "export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 && "
    "cd /home/k/hannahbird-app/android && "
    "./gradlew bundleRelease --no-daemon "
    "-PstoreFile="+KEYSTORE+" "
    "-PstorePassword="+KEY_PASS+" "
    "-PkeyAlias="+KEY_ALIAS+" "
    "-PkeyPassword="+KEY_PASS+" 2>&1 | tail -8"
)
r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=600)
print(r.stdout.strip())

aab=APP+"/app/build/outputs/bundle/release/app-release.aab"
if os.path.exists(aab):
    shutil.copy(aab, WEB+"/hannahbird.aab")
    os.chmod(WEB+"/hannahbird.aab", 0o644)
    sz=os.path.getsize(aab)//1024
    print(f"AAB built: {sz}KB")
    print("Download: http://192.168.10.96:8888/hannahbird.aab")
    save("AAB signed with VNT keystore. Download: http://192.168.10.96:8888/hannahbird.aab"+chr(10)+"Upload to: play.google.com/console (Account: virtual.network.team@gmail.com)")
else:
    # Also build debug APK as fallback
    print("AAB failed, building debug APK...")
    r2=subprocess.run("export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 && cd /home/k/hannahbird-app/android && ./gradlew assembleDebug --no-daemon 2>&1 | tail -5",
        shell=True,capture_output=True,text=True,timeout=600)
    print(r2.stdout.strip())
    apk=APP+"/app/build/outputs/apk/debug/app-debug.apk"
    if os.path.exists(apk):
        shutil.copy(apk,WEB+"/hannahbird.apk")
        print("APK: http://192.168.10.96:8888/hannahbird.apk")
    print("Error:", r.stderr[-300:] if r.returncode!=0 else "check signing config")
