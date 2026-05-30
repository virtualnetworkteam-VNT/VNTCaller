
import subprocess, os, json, time, datetime

M4 = "192.168.10.94"
M4_USER = "Alias"
PYTHON = "/Users/alias/miniforge3/envs/vnt/bin/python"
MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\n### M4 Fix ["+ts+"]\n"+e+"\n")

def run(cmd, shell=False, timeout=30):
    r=subprocess.run(cmd,shell=shell,capture_output=True,text=True,timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def ssh(cmd, timeout=60):
    r=subprocess.run(
        ["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=10",
         "-o","BatchMode=yes",M4_USER+"@"+M4,cmd],
        capture_output=True,text=True,timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

print("="*55)
print("M4 STUDIO API DIAGNOSIS + FIX")
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*55)

# 1. Can we reach M4?
print("\n[1] M4 connectivity...")
ping,_ = run(["ping","-c","2","-W","3",M4])
reachable = "2 received" in ping or "2 packets" in ping
print(f"  M4 ping: {'OK' if reachable else 'UNREACHABLE'}")
if not reachable:
    print("  M4 is offline - cannot proceed")
    save("M4 UNREACHABLE at "+M4)
    exit(1)

# 2. Check what's on port 3333
print("\n[2] Port 3333 status...")
port_check,_ = run(["curl","-s","--connect-timeout","5","http://"+M4+":3333/health"])
print(f"  Port 3333: {port_check[:100] if port_check else 'NO RESPONSE'}")

# 3. SSH check - what's actually running
print("\n[3] What's running on M4...")
procs,_ = ssh("ps aux | grep -E 'python|studio|3333' | grep -v grep | head -10")
print(f"  Processes:\n{procs[:400]}")

port_pid,_ = ssh("lsof -ti:3333 2>/dev/null || echo 'nothing on 3333'")
print(f"  PID on 3333: {port_pid}")

studio_log,_ = ssh("tail -30 /tmp/studio.log 2>/dev/null || echo 'no log'")
print(f"  Studio log:\n{studio_log[:500]}")

# 4. Check Python and studio path
print("\n[4] Checking Python and files...")
py_check,_ = ssh(PYTHON+" --version 2>&1")
print(f"  Python: {py_check}")

studio_files,_ = ssh("ls -la /Users/alias/vnt-studio/ 2>/dev/null || echo 'no studio dir'")
print(f"  Studio files:\n{studio_files[:300]}")

# 5. Check if old API still exists
old_api,_ = ssh("ls -la /home/k/vnt-web/ 2>/dev/null; ls /Users/alias/*.py 2>/dev/null | head -10")
print(f"  Old API files: {old_api[:200]}")

# 6. Kill anything on 3333 and restart cleanly
print("\n[5] Killing old processes and restarting...")
ssh("pkill -f 'studio_api' 2>/dev/null; pkill -f '3333' 2>/dev/null; sleep 1")
ssh("lsof -ti:3333 | xargs kill -9 2>/dev/null; sleep 1")

# Write a clean minimal working API directly
minimal_api = '''#!/usr/bin/env python3
import http.server, json, os, subprocess, datetime, threading, urllib.request, sys

PYTHON = "/Users/alias/miniforge3/envs/vnt/bin/python"
GEN = "/Users/alias/vnt-studio/generated"
STUDIO = "/Users/alias/vnt-studio"
os.makedirs(GEN, exist_ok=True)

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def run_script(script_name, args_dict, timeout=300):
    script_path = STUDIO+"/"+script_name
    if not os.path.exists(script_path):
        return {"status":"error","error":f"Script not found: {script_path}"}
    cmd = [PYTHON, script_path]
    for k,v in args_dict.items():
        cmd += ["--"+k, str(v)]
    log(f"Running: {' '.join(cmd[:4])}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        log(f"stdout: {r.stdout[-200:]}")
        log(f"stderr: {r.stderr[-100:]}")
        for line in reversed(r.stdout.strip().split("\n")):
            line = line.strip()
            if line.startswith("{"):
                try: return json.loads(line)
                except: pass
        return {"status":"ok" if r.returncode==0 else "error",
                "output":r.stdout[-300:],"error":r.stderr[-200:]}
    except subprocess.TimeoutExpired:
        return {"status":"error","error":"timeout after "+str(timeout)+"s"}
    except Exception as e:
        return {"status":"error","error":str(e)}

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.cors()
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/health":
            self.send_json({"status":"online","api":"VNT Studio v3.0",
                "python":PYTHON,"gen_dir":GEN})
        elif path == "/list":
            files=[]
            for f in sorted(os.listdir(GEN)):
                fp=GEN+"/"+f
                if os.path.isfile(fp):
                    files.append({"name":f,"size":os.path.getsize(fp),
                        "url":"http://192.168.10.94:3333/file/"+f})
            self.send_json({"files":files,"count":len(files)})
        elif path.startswith("/file/"):
            fname = path[6:]
            fpath = GEN+"/"+fname
            if os.path.exists(fpath) and os.path.isfile(fpath):
                ext=fname.split(".")[-1].lower()
                ct={"png":"image/png","jpg":"image/jpeg","mp4":"video/mp4",
                    "gif":"image/gif","obj":"text/plain","wav":"audio/wav",
                    "mp3":"audio/mpeg","glb":"model/gltf-binary"}.get(ext,"application/octet-stream")
                data=open(fpath,"rb").read()
                self.send_response(200)
                self.send_header("Content-Type",ct)
                self.send_header("Content-Length",str(len(data)))
                self.cors()
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_json({"error":"file not found: "+fname},404)
        else:
            self.send_json({"status":"online","endpoints":[
                "POST /generate - image","POST /generate-video - video",
                "POST /generate-3d - 3D model","POST /generate-audio - speech/music",
                "GET /health","GET /list","GET /file/<name>"]})

    def do_POST(self):
        n = int(self.headers.get("Content-Length",0))
        try: body = json.loads(self.rfile.read(n)) if n>0 else {}
        except: body = {}
        path = self.path
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log(f"POST {path}: {str(body)[:80]}")

        if path in ["/generate","/generate-image"]:
            prompt = body.get("prompt","a beautiful landscape, photorealistic")
            enhanced = prompt+", 8k uhd, photorealistic, sharp focus, professional photography"
            w = body.get("width",1024); h = body.get("height",1024)
            steps = body.get("steps",4)
            out = GEN+"/img_"+ts+".png"
            result = run_script("generate_hq.py",{"prompt":enhanced,"width":w,"height":h,"steps":steps,"output":out},300)
            if os.path.exists(out):
                result["path"]=out
                result["url"]="http://192.168.10.94:3333/file/img_"+ts+".png"
                result["status"]="ok"
            self.send_json(result)

        elif path == "/generate-video":
            prompt = body.get("prompt","cinematic landscape")
            frames = body.get("frames",16); fps = body.get("fps",8)
            steps = body.get("steps",20)
            out = GEN+"/video_"+ts+".mp4"
            result = run_script("generate_video_hq.py",{"prompt":prompt,"frames":str(frames),"fps":str(fps),"steps":str(steps),"output":out},600)
            if os.path.exists(out):
                result["path"]=out
                result["url"]="http://192.168.10.94:3333/file/video_"+ts+".mp4"
                result["status"]="ok"
            self.send_json(result)

        elif path == "/generate-3d":
            prompt = body.get("prompt","a detailed 3D object")
            out_dir = GEN+"/3d_"+ts
            result = run_script("generate_3d_hq.py",{"prompt":prompt,"output-dir":out_dir},300)
            if os.path.exists(out_dir):
                for f in os.listdir(out_dir):
                    if f.endswith(".obj"):
                        result["url"]="http://192.168.10.94:3333/file/3d_"+ts
                    if f=="preview.png":
                        result["preview"]="http://192.168.10.94:3333/file/3d_"+ts+"/preview.png"
                result["status"]="ok"
            self.send_json(result)

        elif path == "/generate-audio":
            text = body.get("text",body.get("prompt","Hello from VNT"))
            atype = body.get("type","speech")
            out = GEN+"/audio_"+ts+".wav"
            result = run_script("generate_audio_hq.py",{"type":atype,"text":text,"output":out},120)
            if os.path.exists(out):
                result["url"]="http://192.168.10.94:3333/file/audio_"+ts+".wav"
                result["status"]="ok"
            self.send_json(result)

        else:
            self.send_json({"error":"unknown endpoint: "+path},404)

log("VNT Studio API v3.0 starting on :3333")
log(f"Python: {PYTHON}")
log(f"Generated dir: {GEN}")
try:
    server = http.server.HTTPServer(("0.0.0.0",3333), Handler)
    log("API ONLINE - http://192.168.10.94:3333")
    server.serve_forever()
except Exception as e:
    log(f"FATAL: {e}")
    sys.exit(1)
'''

# Write minimal API to M4
tmp_api = "/tmp/studio_api_fix.py"
open(tmp_api,"w").write(minimal_api)
scp_r = subprocess.run(
    ["scp","-o","StrictHostKeyChecking=no",tmp_api,
     M4_USER+"@"+M4+":/Users/alias/vnt-studio/studio_api.py"],
    capture_output=True,text=True,timeout=30)
print(f"  SCP API: {'OK' if scp_r.returncode==0 else scp_r.stderr[:80]}")

# Start it
ssh("mkdir -p /Users/alias/vnt-studio/generated")
ssh(f"nohup {PYTHON} /Users/alias/vnt-studio/studio_api.py > /tmp/studio.log 2>&1 &")
time.sleep(5)

# Verify
health,_ = run(["curl","-s","--connect-timeout","8","http://"+M4+":3333/health"],timeout=10)
print(f"\n[6] Health check: {health[:150]}")

if '"status":"online"' in health or '"status": "online"' in health:
    print("  API ONLINE")
    save("M4 Studio API fixed and online: http://"+M4+":3333")
else:
    # Check log for error
    log_out,_ = ssh("tail -20 /tmp/studio.log")
    print(f"  API still down. Log:\n{log_out[:400]}")
    
    # Try with system python as fallback
    sys_py,_ = ssh("which python3 || which python")
    print(f"  System Python: {sys_py}")
    ssh("pkill -f studio_api 2>/dev/null; sleep 1")
    ssh(f"nohup {sys_py} /Users/alias/vnt-studio/studio_api.py > /tmp/studio.log 2>&1 &")
    time.sleep(4)
    health2,_ = run(["curl","-s","--connect-timeout","8","http://"+M4+":3333/health"],timeout=10)
    print(f"  Retry health: {health2[:100]}")
    save("M4 Studio API retry: "+health2[:100])

print("\nFINAL:", health[:200] if health else "check M4 manually")
