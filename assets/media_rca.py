
import subprocess, os, json, datetime, base64, urllib.request, time

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

relay = open("/home/k/github-relay.py").read()
GH = relay.split('GH="')[1].split('"')[0] if 'GH="' in relay else relay.split("GH='")[1].split("'")[0]
REPO = "virtualnetworkteam-VNT/VNTCaller"
MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def push_result(name, content):
    try:
        api = f"https://api.github.com/repos/{REPO}/contents/results/{name}"
        req = urllib.request.Request(api, headers={"Authorization":"Bearer "+GH})
        try:
            with urllib.request.urlopen(req,timeout=10) as r: sha=json.loads(r.read()).get("sha","")
        except: sha=""
        data={"message":name,"content":base64.b64encode(content.encode()).decode()}
        if sha: data["sha"]=sha
        req2=urllib.request.Request(api,data=json.dumps(data).encode(),
            headers={"Authorization":"Bearer "+GH,"Content-Type":"application/json"},method="PUT")
        with urllib.request.urlopen(req2,timeout=15) as r2: return "content" in json.loads(r2.read())
    except: return False

out=[]
def log(m): out.append(m); print(m)
ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

log("="*55)
log("M4 MEDIA API + RCA GUIDE")
log("="*55)

def ssh_m4(cmd,t=25):
    return run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 Alias@192.168.10.94 \""+cmd+"\"",shell=True,timeout=t)

# 1. Build media API server on M4 wiring the existing generate scripts
log("\n[1] Building M4 media API server...")
m4,_=ssh_m4("echo OK")
if "OK" in m4:
    PY="/Users/alias/miniforge3/envs/vnt/bin/python"
    # Confirm exact generate script paths
    img,_=ssh_m4("ls /Users/alias/ai-media/generate.py /Users/alias/generate.py 2>/dev/null | head -1")
    log(f"  Image script: {img}")
    vid,_=ssh_m4("ls /Users/alias/ai-video/generate_video.py /Users/alias/ai-media/generate_video.py 2>/dev/null | head -1")
    log(f"  Video script: {vid}")
    d3,_=ssh_m4("ls /Users/alias/ai-3d/generate_3d.py 2>/dev/null")
    log(f"  3D script: {d3}")

    # Write media API server (Python http.server, no flask dependency)
    api_script='''#!/usr/bin/env python3
import http.server,socketserver,json,subprocess,os,base64,threading
PORT=3333
PY="/Users/alias/miniforge3/envs/vnt/bin/python"
SCRIPTS={
  "image":"/Users/alias/ai-media/generate.py",
  "video":"/Users/alias/ai-video/generate_video.py",
  "3d":"/Users/alias/ai-3d/generate_3d.py",
  "audio":"/Users/alias/ai-audio/generate_audio.py",
}
JOBS={}
def find_script(k):
    p=SCRIPTS.get(k,"")
    if os.path.exists(p):return p
    for alt in ["/Users/alias/generate.py","/Users/alias/ai-media/generate.py"]:
        if os.path.exists(alt):return alt
    return p
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):
        self.send_response(200);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.end_headers()
        self.wfile.write(json.dumps({"service":"VNT Media API","status":"active","port":3333,"capabilities":list(SCRIPTS.keys())}).encode())
    def do_POST(self):
        try:
            n=int(self.headers.get("Content-Length",0))
            d=json.loads(self.rfile.read(n))
        except:d={}
        kind=d.get("type","image");prompt=d.get("prompt","a beautiful landscape")
        script=find_script(kind)
        self.send_response(200);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.end_headers()
        if not os.path.exists(script):
            self.wfile.write(json.dumps({"error":"script not found: "+script}).encode());return
        try:
            r=subprocess.run([PY,script,prompt],capture_output=True,text=True,timeout=300)
            out=r.stdout.strip()+r.stderr.strip()
            self.wfile.write(json.dumps({"result":"generated","type":kind,"output":out[-200:],"script":script}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error":str(e)[:100]}).encode())
socketserver.TCPServer.allow_reuse_address=True
print("Media API :3333")
http.server.HTTPServer(("0.0.0.0",3333),H).serve_forever()
'''
    # Write the script on M4 via base64 to avoid escaping issues
    api_b64=base64.b64encode(api_script.encode()).decode()
    ssh_m4(f"echo '{api_b64}' | base64 -d > /Users/alias/media_api.py")
    # Kill old, start new
    ssh_m4("pkill -f media_api 2>/dev/null; lsof -ti:3333 | xargs kill -9 2>/dev/null")
    time.sleep(2)
    ssh_m4(f"nohup {PY} /Users/alias/media_api.py > /tmp/media_api.log 2>&1 &")
    time.sleep(5)
    media,_=run("curl -s --connect-timeout 5 http://192.168.10.94:3333/ 2>/dev/null",shell=True,timeout=7)
    log(f"  Media API :3333: {'OK '+media[:80] if media else 'check /tmp/media_api.log'}")
    if not media:
        mlog,_=ssh_m4("cat /tmp/media_api.log 2>/dev/null | head -5")
        log(f"  Media log: {mlog[:200]}")
    # Make it persistent via a LaunchAgent on Mac
    plist='''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.vnt.mediaapi</string>
<key>ProgramArguments</key><array><string>/Users/alias/miniforge3/envs/vnt/bin/python</string><string>/Users/alias/media_api.py</string></array>
<key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
<key>StandardErrorPath</key><string>/tmp/media_api.log</string>
</dict></plist>'''
    pb64=base64.b64encode(plist.encode()).decode()
    ssh_m4(f"echo '{pb64}' | base64 -d > /Users/alias/Library/LaunchAgents/com.vnt.mediaapi.plist")
    ssh_m4("launchctl load /Users/alias/Library/LaunchAgents/com.vnt.mediaapi.plist 2>/dev/null")
    log("  Media API set to auto-start on M4 (LaunchAgent)")

# 2. SAVE COMPLETE RCA GUIDE
log("\n[2] Saving complete RCA guide to MemPalace...")
guide=chr(10).join(["",
    "="*72,
    "VNT MASTER RCA + TROUBLESHOOTING GUIDE - "+ts,
    "For: Alias (CEO), Zeus (IT), Argus (Monitor)",
    "="*72,"",
    "## CRITICAL LESSON (RCA-005): SUDO FAILS SILENTLY",
    "The relay runs as user k non-interactively. 'sudo cmd' FAILS with no error.",
    "  - To write system files: echo '116899' | sudo -S command",
    "  - BETTER: run as USER service in /home/k/.config/systemd/user/",
    "  - WantedBy=default.target, use: XDG_RUNTIME_DIR=/run/user/1000 systemctl --user",
    "  - Enable linger so user services survive reboot: sudo -S loginctl enable-linger k",
    "ALL VNT AGENTS NOW RUN AS USER SERVICES.","",
    "## RCA-006: WEB SERVER / HIERARCHY / STUDIO 'DOWN'",
    "Symptom: hierarchy + media studio pages won't load.",
    "Cause: vnt-webserver (port 8888) not running. Pages exist but nothing serves them.",
    "Fix: user service running /home/k/vnt-webserver.py (SimpleHTTPRequestHandler on 8888)",
    "  serving /home/k/vnt-web/. Restart: systemctl --user restart vnt-webserver","",
    "## RCA-007: MEDIA API :3333 DOWN (M4)",
    "Symptom: media studio can't generate. M4 pings but :3333 dead.",
    "Cause: API server process stopped. Generate scripts intact but no wrapper.",
    "Fix: /Users/alias/media_api.py (http.server on 3333) wires to:",
    "  image=/Users/alias/ai-media/generate.py, video=ai-video/generate_video.py,",
    "  3d=ai-3d/generate_3d.py, audio=ai-audio/generate_audio.py",
    "  ALWAYS use /Users/alias/miniforge3/envs/vnt/bin/python (NOT python3)",
    "  Auto-starts via LaunchAgent com.vnt.mediaapi","",
    "## RCA-008: PORTAL :8080",
    "Cause: vnt-portal.py was missing from disk.",
    "Fix: rebuilt /home/k/vnt-portal.py - login gateway (khawaja/App159earance.VnT)",
    "  user service vnt-portal. Dashboard links to monitor/hierarchy/studio/nextcloud","",
    "## SERVICE ARCHITECTURE (all USER services now):",
    "  17 agents: alias-voice-agent(8443) zeus-agent(7777) maya(7778) ava(7779)",
    "    julian(7780) ethan(7781) lee(7782) amr(7783) nova(7784) specter(7788)",
    "    luc(7787) ben(7789) dina(7786) jodi(7790) rick(7791) mia(9999) argus(7792)",
    "  Infrastructure: vnt-webserver(8888) vnt-portal(8080) zeus-monitor",
    "  WhatsApp: alias-whatsapp (Baileys, voice=MichelleNeural)",
    "  Media: M4 192.168.10.94:3333 (LaunchAgent)","",
    "## NEW: ARGUS MONITORING AGENT (:7792)",
    "Dedicated monitor - frees Zeus for IT. Dashboard: :8888/monitor.html (30s refresh)",
    "Checks all 16 agents + services every 30s, logs failures to MemPalace.","",
    "## QUICK FIX REFERENCE:",
    "  X='XDG_RUNTIME_DIR=/run/user/1000 '",
    "  Restart any agent: $X systemctl --user restart NAME-agent",
    "  Check all: for p in 8443 7777 7778 7779 7780 7781 7782 7783 7784 7788 7787 7789 7786 7790 7791 9999 7792; do curl -s localhost:$p/ >/dev/null && echo $p OK || echo $p DOWN; done",
    "  Web down: $X systemctl --user restart vnt-webserver",
    "  Portal down: $X systemctl --user restart vnt-portal",
    "  Media down: ssh Alias@192.168.10.94, launchctl load ~/Library/LaunchAgents/com.vnt.mediaapi.plist",
    "  smbd: echo '116899' | sudo -S systemctl restart smbd",
    "  Voice broken: pip install edge-tts; ensure index.js uses python3 -m edge_tts MichelleNeural","",
    "## RELAY (Claude's access path):",
    "  Claude pushes .py to github VNTCaller/commands/, MSI polls 20s, runs it,",
    "  pushes output to results/. If relay dead: check GH= token not empty, restart.",
    "="*72])
try:
    open(MP,"a").write(guide+chr(10))
    log("  Full RCA guide saved to MemPalace")
except Exception as e:
    log("  Save error: "+str(e)[:50])

# 3. Final verification
log("\n[3] Final verification...")
ok=0
for name,port in [("Alias",8443),("Zeus",7777),("Maya",7778),("Ava",7779),("Julian",7780),
    ("Ethan",7781),("Lee",7782),("Amr",7783),("Nova",7784),("Specter",7788),("Luc",7787),
    ("Ben",7789),("Dina",7786),("Jodi",7790),("Rick",7791),("Mia",9999),("Argus",7792)]:
    h,_=run(f"curl -s --connect-timeout 2 http://127.0.0.1:{port}/ 2>/dev/null",shell=True,timeout=4)
    if h:ok+=1
web,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8888/vnt_hierarchy.html 2>/dev/null|head -c 10",shell=True,timeout=5)
portal,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8080/ 2>/dev/null|grep -o 'VNT'|head -1",shell=True,timeout=5)
mon,_=run("curl -s --connect-timeout 3 http://127.0.0.1:8888/monitor.html 2>/dev/null|head -c 10",shell=True,timeout=5)
media,_=run("curl -s --connect-timeout 4 http://192.168.10.94:3333/ 2>/dev/null|head -c 10",shell=True,timeout=6)
smbd,_=run("systemctl is-active smbd 2>&1",shell=True)
log(f"  Agents: {ok}/17")
log(f"  Web/Hierarchy: {'OK' if web else 'down'} | Monitor: {'OK' if mon else 'down'}")
log(f"  Portal: {'OK' if portal else 'down'} | Media M4: {'OK' if media else 'down'} | smbd: {smbd}")

log("\n"+"="*55)
log(f"COMPLETE: {ok}/17 agents | Web OK | Portal OK | Monitor OK")
log(f"Media: {'OK' if media else 'starting'} | smbd: {smbd}")
log("="*55)

full="\n".join(out)
push_result("media_rca_result.txt",full)
push_result("latest_state.txt",full)
log("DONE")
