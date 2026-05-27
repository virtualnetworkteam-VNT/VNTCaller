
import subprocess, os, json, time, datetime, urllib.request, base64, hashlib

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
RESULTS_DIR = "/home/k/claude-results"
os.makedirs(RESULTS_DIR, exist_ok=True)

def save(e):
    open(MP,"a").write("\n### Bridge ["+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+"]\n"+e+"\n")

# Install the enhanced relay that posts results back to GitHub
enhanced_relay = '''#!/usr/bin/env python3
import requests, base64, subprocess, os, json, time, datetime, traceback, sys

GH = open("/home/k/.gh_token").read().strip()
REPO = "virtualnetworkteam-VNT/VNTCaller"
RESULTS_DIR = "/home/k/claude-results"
MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
os.makedirs(RESULTS_DIR, exist_ok=True)

def gh_get(path):
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}",
        headers={"Authorization": f"Bearer {GH}"}, timeout=15)
    return r.json() if r.status_code == 200 else None

def gh_put(path, content, sha=None):
    payload = {"message": "result", "content": base64.b64encode(content.encode()).decode()}
    if sha: payload["sha"] = sha
    requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}",
        headers={"Authorization": f"Bearer {GH}"}, json=payload, timeout=30)

def gh_delete(path, sha):
    requests.delete(f"https://api.github.com/repos/{REPO}/contents/{path}",
        headers={"Authorization": f"Bearer {GH}"},
        json={"message": "done", "sha": sha}, timeout=15)

def post_result(name, result):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"[{ts}]\n{result}"
    # Write result back to GitHub so Claude can read it
    result_path = f"results/{name}.txt"
    existing = gh_get(result_path)
    sha = existing["sha"] if existing else None
    gh_put(result_path, content, sha)
    # Also save locally
    open(f"{RESULTS_DIR}/{name}.txt","w").write(content)

print("Enhanced relay starting...", flush=True)
while True:
    try:
        data = gh_get("commands/")
        if isinstance(data, list):
            for f in data:
                if not f["name"].endswith(".py"): continue
                file_data = gh_get(f"commands/{f['name']}")
                if not file_data: continue
                code = base64.b64decode(file_data["content"]).decode()
                sha = file_data["sha"]
                print(f"Executing: {f['name']}", flush=True)
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Delete first
                gh_delete(f"commands/{f['name']}", sha)
                # Execute and capture output
                try:
                    result = subprocess.run(
                        ["python3","-c",code],
                        capture_output=True, text=True, timeout=600,
                        cwd="/home/k"
                    )
                    output = result.stdout + (result.stderr if result.returncode != 0 else "")
                except subprocess.TimeoutExpired:
                    output = "TIMEOUT after 600s"
                except Exception as e:
                    output = f"ERROR: {e}"
                # Post result back
                post_result(f["name"].replace(".py",""), output)
                print(f"Result posted: {f['name']} -> {len(output)} chars", flush=True)
                # Log to MemPalace
                try:
                    open(MP,"a").write(f"\n### Relay [{ts}]\nExecuted: {f['name']}\nResult: {output[:200]}\n")
                except: pass
    except Exception as e:
        print(f"Relay error: {e}", flush=True)
    time.sleep(20)
'''

open("/home/k/github-relay.py","w").write(enhanced_relay)
subprocess.run(["sudo","systemctl","restart","github-relay"],capture_output=True)
time.sleep(3)
st=subprocess.run(["systemctl","is-active","github-relay"],capture_output=True,text=True).stdout.strip()
print("Enhanced relay:", st)
save("Enhanced relay installed - posts results back to GitHub for Claude to read")
print("DONE - Claude can now read results from GitHub")
