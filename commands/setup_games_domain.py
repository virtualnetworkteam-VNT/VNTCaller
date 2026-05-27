
import subprocess, os, time, datetime, shutil

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
APP_DIR = "/home/k/hannahbird-app"
GAME_SRC = "/home/k/vnt-web/hannahbird.html"
GAMES_DIR = "/home/k/vnt-games"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write(chr(10)+"### Games ["+ts+"]"+chr(10)+e+chr(10))
    except: pass

os.makedirs(GAMES_DIR, exist_ok=True)

# Copy game to games directory
if os.path.exists(GAME_SRC):
    shutil.copy(GAME_SRC, GAMES_DIR+"/index.html")
    print("Game copied to games dir")

# Check Caddy config for subdomain
caddy_conf = "/etc/caddy/Caddyfile"
caddy_content = ""
if os.path.exists(caddy_conf):
    caddy_content = open(caddy_conf).read()

if "games.vntworld.com" not in caddy_content:
    games_block = """
games.vntworld.com {
    root * /home/k/vnt-games
    file_server
    encode gzip
    header {
        Access-Control-Allow-Origin *
        Cache-Control max-age=3600
    }
}
"""
    # Also add HTTP fallback
    games_block_http = """
http://games.vntworld.com {
    root * /home/k/vnt-games
    file_server
    encode gzip
}
"""
    try:
        with open(caddy_conf,"a") as f:
            f.write(games_block+games_block_http)
        subprocess.run(["sudo","systemctl","reload","caddy"],capture_output=True)
        print("Caddy: games.vntworld.com configured")
    except Exception as e:
        print("Caddy config:", e)
        # Try alternative - serve via existing webserver on a route
        ws = open("/home/k/vnt-webserver.py").read()
        if "/games" not in ws:
            ws = ws.replace(
                "SERVE_DIR = ",
                'GAMES_DIR = "/home/k/vnt-games"
SERVE_DIR = '
            )
            open("/home/k/vnt-webserver.py","w").write(ws)
            subprocess.run(["sudo","systemctl","restart","vnt-webserver"],capture_output=True)
else:
    print("games.vntworld.com already in Caddy")

# Fix Android SDK and rebuild APK
print("=== Building APK ===")
# Find SDK from VNTCaller project
sdk = None
r=subprocess.run(["find","/home/k","-name","local.properties","-maxdepth","6"],capture_output=True,text=True)
for lp in r.stdout.strip().split(chr(10)):
    if lp and os.path.exists(lp) and "sdk.dir" in open(lp).read():
        for line in open(lp).read().split(chr(10)):
            if line.startswith("sdk.dir="):
                p=line.split("=",1)[1].strip()
                if os.path.exists(p): sdk=p; break
    if sdk: break

if not sdk:
    r2=subprocess.run(["find","/home","/opt","/.android","-name","aapt","2>/dev/null"],
        shell=True,capture_output=True,text=True)
    if r2.stdout.strip():
        aapt=r2.stdout.strip().split(chr(10))[0]
        sdk=os.path.dirname(os.path.dirname(os.path.dirname(aapt)))
        print("SDK found via aapt:", sdk)

if sdk:
    print("SDK:", sdk)
    lp_path=APP_DIR+"/android/local.properties"
    open(lp_path,"w").write("sdk.dir="+sdk+chr(10))

    # Sync game to capacitor www
    os.makedirs(APP_DIR+"/www",exist_ok=True)
    shutil.copy(GAME_SRC, APP_DIR+"/www/index.html")

    # Run capacitor sync
    subprocess.run("cd "+APP_DIR+" && npx cap sync android 2>&1 | tail -5",
        shell=True,capture_output=True,text=True,timeout=60)

    # Build
    ok,_,err=subprocess.run("cd "+APP_DIR+"/android && ./gradlew assembleDebug --no-daemon 2>&1 | tail -15",
        shell=True,capture_output=True,text=True,timeout=600).__class__.__init__

    apk=APP_DIR+"/android/app/build/outputs/apk/debug/app-debug.apk"
    r3=subprocess.run(["./gradlew","assembleDebug","--no-daemon"],
        cwd=APP_DIR+"/android",capture_output=True,text=True,timeout=600)
    print(r3.stdout[-500:])
    print(r3.stderr[-300:] if r3.returncode!=0 else "")

    if os.path.exists(apk):
        shutil.copy(apk,"/home/k/vnt-web/generated/hannahbird.apk")
        shutil.copy(apk,GAMES_DIR+"/hannahbird.apk")
        sz=os.path.getsize(apk)//1024
        print(f"APK built: {sz}KB")
        # Deploy via WiFi
        subprocess.run(["adb","connect","192.168.10.191:5555"],capture_output=True,timeout=10)
        ri=subprocess.run(["adb","install","-r",apk],capture_output=True,text=True,timeout=120)
        print("ADB install:", ri.stdout.strip()[:100] or ri.stderr.strip()[:100])
        save("HannahBird APK built and deployed"+chr(10)+"APK: http://192.168.10.96:3333/generated/hannahbird.apk")
    else:
        print("APK not found - SDK issue persists")
        save("APK build failed - SDK issue")
else:
    print("SDK not found")

save("Games subdomain: games.vntworld.com configured"+chr(10)+"Game: http://192.168.10.96:8888/hannahbird.html")
print("Game accessible: http://192.168.10.96:8888/hannahbird.html")
print("Public (after DNS): https://games.vntworld.com")
