
import subprocess, time, os, json, datetime, re, urllib.request

MP  = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

def run(cmd, shell=False, timeout=20):
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def save(e):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try: open(MP,"a").write("\n### Verify ["+ts+"]\n"+e+"\n")
    except: pass

def ssh7(cmd, timeout=20):
    return run("sshpass -p '116899' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 Alias@192.168.10.114 \""+cmd+"\"", shell=True, timeout=timeout)

print("="*55)
print("REAL VERIFICATION - NO GUESSING")
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*55)

# ── 1. WHAT IS ACTUALLY LISTENING ON MSI ────────────────
print("\n[1] What is actually listening on MSI...")
ports,_ = run("ss -tlnp | grep -E '8080|8888|8443|8444|3333|7900'", shell=True)
print(ports if ports else "  NOTHING on any of those ports")

# ── 2. IS PORTAL ACTUALLY RUNNING? ──────────────────────
print("\n[2] Portal actual test...")
local,_ = run("curl -s --connect-timeout 3 http://127.0.0.1:8080/ | head -c 50", shell=True, timeout=6)
print("  127.0.0.1:8080:", local if local else "NO RESPONSE - portal not working")

local2,_ = run("curl -s --connect-timeout 3 http://127.0.0.1:8888/ | head -c 50", shell=True, timeout=6)
print("  127.0.0.1:8888:", local2 if local2 else "NO RESPONSE")

# ── 3. IS VOICE AGENT ACTUALLY WORKING? ─────────────────
print("\n[3] Voice agent real test...")
va_st,_ = run(["systemctl","is-active","alias-voice-agent"])
print("  Service:", va_st)
va_test,_ = run("curl -s --connect-timeout 3 http://127.0.0.1:8443/", shell=True, timeout=6)
print("  HTTP test:", va_test[:80] if va_test else "NO RESPONSE on :8443")

# ── 4. IS EDGE-TTS INSTALLED? ───────────────────────────
print("\n[4] Audio dependencies...")
edgetts,_ = run(["python3","-c","import edge_tts; print('edge_tts OK')"])
print("  edge_tts:", edgetts if edgetts else "NOT INSTALLED")

# Test actually generating audio
if "OK" in edgetts:
    audio_test,_ = run("python3 -c \"import asyncio,edge_tts; asyncio.run(edge_tts.Communicate('test','en-US-JennyNeural').save('/tmp/test.mp3'))\" 2>&1", shell=True, timeout=15)
    audio_exists = os.path.exists("/tmp/test.mp3")
    print("  Generate audio:", "OK" if audio_exists else "FAILED: "+audio_test[:60])
else:
    print("  Installing edge_tts...")
    run("pip install edge-tts --break-system-packages -q", shell=True, timeout=60)
    edgetts2,_ = run(["python3","-c","import edge_tts; print('OK')"])
    print("  After install:", edgetts2)

# ── 5. IS WHATSAPP RUNNING? ─────────────────────────────
print("\n[5] WhatsApp real test...")
wa_st,_ = run(["systemctl","--user","is-active","alias-whatsapp"])
print("  Service:", wa_st)
wa_log,_ = run("journalctl --user -u alias-whatsapp -n 5 --no-pager --quiet", shell=True)
print("  Last log:", wa_log[-150:] if wa_log else "no logs")

# ── 6. CLOUDFLARE TUNNEL REAL URL ───────────────────────
print("\n[6] Cloudflare tunnel real check...")
cf_st,_ = run(["systemctl","is-active","cf-tunnel"])
print("  Service:", cf_st)
if cf_st == "active":
    cf_log,_ = run("journalctl -u cf-tunnel -n 40 --no-pager --quiet", shell=True)
    m = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', cf_log or "")
    cf_url = m.group(0) if m else ""
    print("  URL:", cf_url if cf_url else "NOT FOUND in logs")
    print("  Log:", cf_log[-200:] if cf_log else "none")
else:
    print("  CF tunnel not active - starting...")
    run(["sudo","systemctl","restart","cf-tunnel"], timeout=15)

# ── 7. PUBLIC IP ─────────────────────────────────────────
print("\n[7] Real public IP...")
pub_ip,_ = run("curl -s --connect-timeout 5 ifconfig.me", shell=True, timeout=8)
print("  Current public IP:", pub_ip)
print("  94.49.29.97 is", "SAME" if pub_ip=="94.49.29.97" else "DIFFERENT from current IP")

# ── 8. ASUSI7 BROWSER TEST ───────────────────────────────
print("\n[8] Asusi7 browser test...")
conn,_ = ssh7("echo OK")
if "OK" in conn:
    # Open local portal in browser
    ssh7("powershell -Command \"Start-Process 'chrome' 'http://192.168.10.96:8080/' -ErrorAction SilentlyContinue\"")
    ssh7("powershell -Command \"Start-Process 'msedge' 'http://192.168.10.96:8080/' -ErrorAction SilentlyContinue\"")
    print("  Browser opened on Asusi7 with http://192.168.10.96:8080/")
    # Test if portal is reachable from Asusi7
    reach,_ = ssh7("powershell -Command \"try{$r=(New-Object Net.WebClient).DownloadString('http://192.168.10.96:8080/');Write-Output 'REACHED'}catch{Write-Output $_.Exception.Message}\"")
    print("  Portal from Asusi7:", reach[:60])
else:
    print("  Asusi7 SSH:", conn[:40])

# ── 9. SHOW EXACTLY WHAT NEEDS FIXING ───────────────────
print("\n"+"="*55)
print("REAL STATUS - HONEST:")
print("="*55)

issues = []
if not local: issues.append("Portal :8080 not running")
if va_st != "active": issues.append("Voice agent not active")
if not va_test: issues.append("Voice agent :8443 not responding")
if "NOT" in edgetts: issues.append("edge_tts not installed")
if wa_st != "active": issues.append("WhatsApp not active")
if pub_ip != "94.49.29.97": issues.append("94.49.29.97 is old IP, current is "+pub_ip)

if issues:
    print("ISSUES FOUND:")
    for i in issues: print("  - "+i)
else:
    print("All systems responding")

save("Verification: "+str(issues))
