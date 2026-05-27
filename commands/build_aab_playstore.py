
import subprocess, os, shutil, datetime

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
APP = "/home/k/hannahbird-app/android"
WEB = "/home/k/vnt-web"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### AAB Build ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

# Create keystore for signing if not exists
KEYSTORE = "/home/k/vnt-hannahbird.keystore"
if not os.path.exists(KEYSTORE):
    print("Creating signing keystore...")
    r=subprocess.run([
        "keytool","-genkey","-v","-keystore",KEYSTORE,
        "-alias","hannahbird","-keyalg","RSA","-keysize","2048","-validity","10000",
        "-storepass","vntbird2026","-keypass","vntbird2026",
        "-dname","CN=VNT World AI,OU=VNT,O=VNT World,L=Riyadh,S=Riyadh,C=SA"
    ],capture_output=True,text=True,timeout=30)
    print("Keystore:", "created" if os.path.exists(KEYSTORE) else "failed: "+r.stderr[:100])

# Write signing config to gradle
local_props = APP+"/../android/local.properties"
open(local_props,"w").write(
    "sdk.dir=/home/k/android-sdk"+chr(10)+
    "storeFile="+KEYSTORE+chr(10)+
    "storePassword=vntbird2026"+chr(10)+
    "keyAlias=hannahbird"+chr(10)+
    "keyPassword=vntbird2026"+chr(10)
)

# Add signing config to app/build.gradle if not there
build_gradle = APP+"/app/build.gradle"
bg = open(build_gradle).read()
if "signingConfigs" not in bg:
    signing = """
    signingConfigs {
        release {
            storeFile file(project.property("storeFile") ?: "debug.keystore")
            storePassword project.property("storePassword") ?: "android"
            keyAlias project.property("keyAlias") ?: "androiddebugkey"
            keyPassword project.property("keyPassword") ?: "android"
        }
    }
"""
    bg = bg.replace("buildTypes {", signing+"    buildTypes {")
    bg = bg.replace("release {", "release { signingConfig signingConfigs.release")
    open(build_gradle,"w").write(bg)
    print("Signing config added to build.gradle")

# Build release AAB
print("Building release AAB...")
r2=subprocess.run(
    "export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 && "
    "cd /home/k/hannahbird-app/android && "
    "./gradlew bundleRelease --no-daemon "
    "-PstoreFile="+KEYSTORE+" "
    "-PstorePassword=vntbird2026 "
    "-PkeyAlias=hannahbird "
    "-PkeyPassword=vntbird2026 2>&1 | tail -8",
    shell=True,capture_output=True,text=True,timeout=600
)
print(r2.stdout.strip())

aab="/home/k/hannahbird-app/android/app/build/outputs/bundle/release/app-release.aab"
if os.path.exists(aab):
    shutil.copy(aab, WEB+"/hannahbird.aab")
    os.chmod(WEB+"/hannahbird.aab", 0o644)
    sz=os.path.getsize(aab)//1024
    print(f"AAB ready: {sz}KB")
    print("Upload this to Google Play Console:")
    print("http://192.168.10.96:8888/hannahbird.aab")
    save("AAB built for Google Play. Download: http://192.168.10.96:8888/hannahbird.aab"+chr(10)+"Keystore: "+KEYSTORE+" / pass: vntbird2026")
else:
    # Fallback: try debug APK for now
    print("AAB failed, checking APK...")
    apk="/home/k/hannahbird-app/android/app/build/outputs/apk/debug/app-debug.apk"
    if os.path.exists(apk):
        shutil.copy(apk,WEB+"/hannahbird.apk")
        print("APK available: http://192.168.10.96:8888/hannahbird.apk")
    print("Error:", r2.stderr[-200:] if r2.returncode!=0 else "unknown")
    save("AAB build failed - check gradle signing config")
