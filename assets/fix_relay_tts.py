import subprocess, os, json, datetime, re, time, ast

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"

def run(cmd, shell=False, timeout=20):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Fix ["+ts+"]\n"+e+"\n")
    except: pass

print("="*55)
print("FIX RELAY + TTS")
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*55)

# 1. Fix relay
print("\n[1] Fixing relay...")
relay_path = "/home/k/github-relay.py"
relay_content = open(relay_path).read()
try:
    ast.parse(relay_content)
    print("  Relay syntax: OK")
    subprocess.run(["sudo","systemctl","restart","github-relay"],capture_output=True,timeout=15)
except SyntaxError as e:
    print(f"  Relay broken L{e.lineno}: {e.msg}")
    # Rewrite reading token from file itself
    GH_LINE = [l for l in relay_content.split("\n") if "GH" in l and "ghp_" in l]
    GH_TOKEN = GH_LINE[0].split('"')[1] if GH_LINE and '"' in GH_LINE[0] else GH_LINE[0].split("'")[1] if GH_LINE else ""
    relay_new = "\n".join([
        "#!/usr/bin/env python3",
        "import requests,base64,os,time,subprocess,logging",
        f'GH="{GH_TOKEN}"',
        "REPO='virtualnetworkteam-VNT/VNTCaller'",
        "LOG='/home/k/github-relay.log'",
        "logging.basicConfig(filename=LOG,level=logging.INFO,format='%(asctime)s %(message)s')",
        "def log(m):logging.info(m);print(m)",
        "def get_cmds():",
        "    try:",
        "        r=requests.get('https://api.github.com/repos/'+REPO+'/contents/commands/',headers={'Authorization':'Bearer '+GH},timeout=10)",
        "        return [f for f in r.json() if isinstance(f,dict) and f.get('name','').endswith('.py')] if r.status_code==200 else []",
        "    except:return []",
        "def get_code(i):",
        "    try:r=requests.get(i['download_url'],timeout=15);return r.text if r.status_code==200 else ''",
        "    except:return ''",
        "def del_cmd(i):",
        "    try:requests.delete('https://api.github.com/repos/'+REPO+'/contents/commands/'+i['name'],headers={'Authorization':'Bearer '+GH},json={'message':'done','sha':i['sha']},timeout=10)",
        "    except:pass",
        "log('relay started')",
        "while True:",
        "    try:",
        "        for cmd in get_cmds():",
        "            log('Executing: '+cmd.get('name',''))",
        "            code=get_code(cmd)",
        "            if code:",
        "                try:r=subprocess.run(['python3','-c',code],capture_output=True,text=True,timeout=600);log('Result: '+(r.stdout+r.stderr)[-300:])",
        "                except Exception as e:log('Error: '+str(e))",
        "                del_cmd(cmd);log('Completed: '+cmd.get('name',''))",
        "    except Exception as e:log('Relay error: '+str(e))",
        "    time.sleep(20)",
    ])
    open(relay_path,"w").write(relay_new)
    print("  Relay rewritten")
    subprocess.run(["sudo","systemctl","restart","github-relay"],capture_output=True,timeout=15)

time.sleep(2)
st,_ = run(["systemctl","is-active","github-relay"])
print("  Relay:", st)

# 2. Install edge-tts
print("\n[2] edge-tts...")
run("pip install edge-tts --break-system-packages -q",shell=True,timeout=60)
ok,_ = run(["python3","-c","import edge_tts;print('OK')"])
print("  edge_tts:",ok)

# Write helper
helper = "\n".join([
    "#!/usr/bin/env python3",
    "import sys,asyncio,edge_tts,os",
    "async def go(t,p):",
    "    await edge_tts.Communicate(t,'en-US-JennyNeural').save(p)",
    "t=sys.argv[1] if len(sys.argv)>1 else 'Hello'",
    "p=sys.argv[2] if len(sys.argv)>2 else '/tmp/alias.mp3'",
    "asyncio.run(go(t,p))",
    "sys.exit(0 if os.path.exists(p) else 1)",
])
open("/home/k/alias_tts.py","w").write(helper)
os.chmod("/home/k/alias_tts.py",0o755)
test,_ = run("python3 /home/k/alias_tts.py 'Alias is working' /tmp/alias_test.mp3 2>&1",shell=True,timeout=20)
audio_ok = os.path.exists("/tmp/alias_test.mp3")
print("  Audio test:", "OK" if audio_ok else "FAIL: "+test[:60])

# 3. Read actual piper lines
print("\n[3] Reading index.js piper lines...")
wa = "/home/k/alias-baileys/index.js"
lines = open(wa).read().split("\n")
piper_idxs = [i for i,l in enumerate(lines) if "piper" in l]
print(f"  Found {len(piper_idxs)} piper lines:")
for i in piper_idxs:
    print(f"  L{i+1}: {lines[i].strip()[:120]}")

# 4. Patch
print("\n[4] Patching...")
if piper_idxs:
    new_lines = list(lines)
    for i in piper_idxs:
        orig = lines[i]
        indent = " "*(len(orig)-len(orig.lstrip()))
        # Find what variable names are used for text and file
        # Look in surrounding lines for ttsText, audioFile etc
        ctx = " ".join(lines[max(0,i-5):i+5])
        text_var = "ttsText"
        file_var = "audioFile"
        if "voiceText" in ctx: text_var="voiceText"
        if "textToSpeak" in ctx: text_var="textToSpeak"
        if "outputPath" in ctx: file_var="outputPath"
        if "wavFile" in ctx: file_var="wavFile"
        if "outputFile" in ctx: file_var="outputFile"
        
        if "const ttsCmd" in orig or "ttsCmd=" in orig:
            new_lines[i] = indent+"const ttsCmd = `python3 /home/k/alias_tts.py \"${"+text_var+"}\" \"${"+file_var+"}\" 2>&1`;"
        elif "execSync" in orig:
            new_lines[i] = indent+"execSync(`python3 /home/k/alias_tts.py \"${"+text_var+"}\" \"${"+file_var+"}\" 2>&1`);"
        else:
            new_lines[i] = orig  # skip unknown pattern
            print(f"  L{i+1}: SKIPPED (unknown pattern)")
            continue
        print(f"  L{i+1}: PATCHED -> {new_lines[i].strip()[:80]}")

    new_content = "\n".join(new_lines)
    open("/tmp/wa_p.js","w").write(new_content)
    syn,_ = run(["node","--check","/tmp/wa_p.js"])
    if not syn:
        open(wa,"w").write(new_content)
        print("  index.js saved OK")
        save("TTS patched: piper->edge-tts")
    else:
        print("  JS syntax error:", syn[:80])
        print("  Showing all audio-related lines for manual check:")
        for i,l in enumerate(lines):
            if any(w in l for w in ["ttsText","audioFile","piper","wav","sendAudio","VoiceMessage"]):
                print(f"  L{i+1}: {l.strip()[:100]}")

# 5. Restart
print("\n[5] Restarting WhatsApp...")
run(["systemctl","--user","restart","alias-whatsapp"])
time.sleep(4)
wa_st,_ = run(["systemctl","--user","is-active","alias-whatsapp"])
log,_ = run("journalctl --user -u alias-whatsapp -n 5 --no-pager --quiet",shell=True)
print("  WA:", wa_st)
print("  Log:", log[-200:] if log else "none")

save(f"Fix done: relay={st} audio={audio_ok} wa={wa_st}")
print("\n"+"="*55)
print(f"relay={st} | audio={'OK' if audio_ok else 'FAIL'} | WA={wa_st}")
print("Send WhatsApp to Alias now - should get voice reply")
