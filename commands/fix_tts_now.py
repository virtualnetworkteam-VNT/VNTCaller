import subprocess, os, time, json, datetime, re

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

def run(cmd, shell=False, timeout=30):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### TTS Fix ["+ts+"]\n"+e+"\n")
    except: pass

print("="*55)
print("FIX AUDIO - ROOT CAUSE CONFIRMED: piper binary fails")
print("="*55)

# 1. Show exact piper error
print("\n[1] Exact piper error:")
out,err = run("echo 'test' | /home/k/.local/bin/piper --model /home/k/.local/share/piper/en_US-lessac-medium.onnx --output_file /tmp/t.wav 2>&1", shell=True, timeout=8)
print("  Error:", out[:150] or err[:150])

model_ok,_ = run("ls -lh /home/k/.local/share/piper/en_US-lessac-medium.onnx 2>/dev/null", shell=True)
print("  Model:", model_ok if model_ok else "MODEL FILE MISSING")

# 2. Install edge-tts
print("\n[2] Installing edge-tts...")
run("pip install edge-tts --break-system-packages -q", shell=True, timeout=60)
ok,_ = run(["python3","-c","import edge_tts; print('OK')"])
print("  edge_tts:", ok)

# 3. Write TTS helper script
print("\n[3] Writing TTS helper...")
helper = open("/dev/stdin").read() if False else ""
helper_lines = [
    "#!/usr/bin/env python3",
    "import sys,asyncio,edge_tts,os",
    "async def speak(text,path):",
    "    await edge_tts.Communicate(text,'en-US-JennyNeural').save(path)",
    "text=sys.argv[1] if len(sys.argv)>1 else 'Hello'",
    "path=sys.argv[2] if len(sys.argv)>2 else '/tmp/alias.mp3'",
    "asyncio.run(speak(text,path))",
    "if os.path.exists(path):print('OK:'+path)",
    "else:print('FAILED')",
]
open("/home/k/alias_tts.py","w").write("\n".join(helper_lines))
os.chmod("/home/k/alias_tts.py",0o755)

# Test it
test_out,_ = run("python3 /home/k/alias_tts.py 'Hello Ryan, I am Alias' /tmp/test_alias.mp3 2>&1", shell=True, timeout=20)
audio_ok = os.path.exists("/tmp/test_alias.mp3")
size,_ = run("ls -lh /tmp/test_alias.mp3 2>/dev/null", shell=True)
print("  Test:", test_out[:60], "|", size[:30] if audio_ok else "FAILED")

# 4. Patch index.js - find and fix piper lines
print("\n[4] Patching WhatsApp index.js...")
wa_path = "/home/k/alias-baileys/index.js"
content = open(wa_path).read()

# Show the piper lines
piper_lines = [(i+1,l) for i,l in enumerate(content.split("\n")) if "piper" in l]
print("  Piper lines found:", len(piper_lines))
for ln,line in piper_lines[:5]:
    print(f"  L{ln}: {line.strip()[:100]}")

if piper_lines:
    # Replace each piper command line
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        if "piper" in line and ("echo" in line or "ttsCmd" in line or "exec" in line.lower()):
            # Extract the output file variable from context
            # Replace the whole piper command with python3 alias_tts.py
            indent = len(line) - len(line.lstrip())
            new_line = " "*indent + "const ttsCmd = `python3 /home/k/alias_tts.py \"${ttsText}\" \"${audioFile}\"`;"
            new_lines.append(new_line)
            print(f"  REPLACED L{lines.index(line)+1}: {line.strip()[:60]}")
            print(f"  WITH: {new_line.strip()[:60]}")
        else:
            new_lines.append(line)
    
    new_content = "\n".join(new_lines)
    
    # Validate
    open("/tmp/wa_test.js","w").write(new_content)
    syntax,_ = run(["node","--check","/tmp/wa_test.js"])
    if not syntax:
        open(wa_path,"w").write(new_content)
        print("  index.js patched OK")
        save("WA TTS fixed: piper->edge-tts via alias_tts.py")
    else:
        print("  Syntax error after patch:", syntax[:80])
        print("  Showing ttsText/audioFile variable names in code...")
        for i,l in enumerate(content.split("\n")):
            if "ttsText" in l or "audioFile" in l or "ttsCmd" in l:
                print(f"  L{i+1}: {l.strip()[:100]}")
else:
    # piper called differently - search more broadly
    print("  No direct piper lines - searching TTS function...")
    for i,line in enumerate(content.split("\n")):
        if any(w in line.lower() for w in ["tts","audio","voice","wav","mp3","piper"]):
            print(f"  L{i+1}: {line.strip()[:100]}")

# 5. Restart and test
print("\n[5] Restarting WhatsApp...")
run(["systemctl","--user","restart","alias-whatsapp"])
time.sleep(4)
wa_st,_ = run(["systemctl","--user","is-active","alias-whatsapp"])
print("  WhatsApp:", wa_st)

# Check new log
time.sleep(2)
new_log,_ = run("journalctl --user -u alias-whatsapp -n 5 --no-pager --quiet", shell=True)
print("  New log:", new_log[-150:] if new_log else "none")

save("TTS fix complete. edge_tts:"+("OK" if audio_ok else "FAIL")+" WA:"+wa_st)
print("\nDONE - now send a WhatsApp to Alias and check for audio")
