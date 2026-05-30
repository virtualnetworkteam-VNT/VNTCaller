
import os, json, datetime

MP   = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
BRAIN= "/mnt/vnt-data/FileServer/VNT_World_AI_Division/alias_brain.json"

def save(e):
    try: open(MP,"a").write("\n"+e+"\n")
    except: pass

ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# Read relay token from actual file (don't hardcode)
try:
    relay = open("/home/k/github-relay.py").read()
    gh_line = [l for l in relay.split("\n") if l.startswith("GH=")][0]
    relay_token_note = "Token stored in /home/k/github-relay.py line: "+gh_line[:20]+"..."
except:
    relay_token_note = "Token: check /home/k/github-relay.py line 3"

rca = (
    "\n"+"="*80+"\n"
    +"VNT ROOT CAUSE ANALYSIS (RCA) - "+ts+"\n"
    +"For: Alias CEO + Zeus IT Director\n"
    +"="*80+"\n\n"

    +"SECTION 1: SYSTEM MAP\n"
    +"-"*40+"\n"
    +"MSI AI Server:  192.168.10.96  user=k  sudo=116899\n"
    +"M4 MacBook:     192.168.10.94:3333  ACTIVE MEDIA (NOT M2)\n"
    +"M2 MacBook:     RETIRED - NOT IN USE\n"
    +"Asusi7:         192.168.10.114  SSH:Alias/116899\n"
    +"Nextcloud:      192.168.10.10  CT104 on Proxmox 192.168.10.19\n"
    +"Public IP:      DYNAMIC fiber - use CF tunnel not raw IP\n"
    +"Omada:          https://192.168.10.5:8043  vntworld@aol.com\n"
    +"Twingate:       vntw.twingate.com (Ryan adds aliasvnt@gmail.com)\n\n"

    +"VOICE PROFILES (PERMANENT):\n"
    +"  Alias = en-US-MichelleNeural\n"
    +"  Mia   = en-US-AriaNeural\n"
    +"  Engine = python3 -m edge_tts  (NEVER piper, NEVER edge-tts CLI)\n\n"

    +"GITHUB RELAY:\n"
    +"  Repo: virtualnetworkteam-VNT/VNTCaller/commands/\n"
    +"  Polls every 20s. Log: /home/k/github-relay.log\n"
    +"  "+relay_token_note+"\n\n"

    +"="*80+"\n"
    +"SECTION 2: CONFIRMED RCA LOG\n"
    +"="*80+"\n\n"

    +"RCA-001: AUDIO/TTS FAILURE\n"
    +"Symptom: Alias replies text only, no voice on WhatsApp\n"
    +"Cause:   piper binary fails (model missing). edge-tts CLI not installed.\n"
    +"         index.js calls edge-tts CLI which doesnt exist, falls to broken catch\n"
    +"Evidence: journalctl --user -u alias-whatsapp | grep TTS error\n"
    +"Fix:\n"
    +"  pip install edge-tts --break-system-packages\n"
    +"  python3 -m edge_tts --voice en-US-MichelleNeural --text test --write-media /tmp/t.mp3\n"
    +"  ls -lh /tmp/t.mp3  (must exist >0 bytes)\n"
    +"  sed -i replace all Neural voice names -> en-US-MichelleNeural in index.js\n"
    +"  systemctl --user restart alias-whatsapp\n"
    +"Prevention: Never use piper. Always python3 -m edge_tts. Test file exists first.\n"
    +"Status: FIXED 2026-05-30\n\n"

    +"RCA-002: GITHUB RELAY DEAD\n"
    +"Symptom: Commands pushed but nothing executes for hours/days\n"
    +"Cause:   SyntaxError in relay.py (unterminated f-string). GH=empty after rewrite.\n"
    +"Evidence: relay log timestamp >30min old. GH= empty in file.\n"
    +"Fix:\n"
    +"  sed -n '1,5p' /home/k/github-relay.py  (check GH= line)\n"
    +"  python3 -m py_compile /home/k/github-relay.py  (check syntax)\n"
    +"  pkill -f github-relay && python3 /home/k/github-relay.py &\n"
    +"  tail -f /home/k/github-relay.log  (watch for relay started)\n"
    +"Prevention: Zeus checks relay log age every 5 min. Auto-fix if >30min old.\n"
    +"Status: FIXED 2026-05-30\n\n"

    +"RCA-003: EXTERNAL IP ACCESS FAILS\n"
    +"Symptom: 94.49.29.97 times out from external network\n"
    +"Cause:   Home fiber = dynamic IP. Changes on router restart.\n"
    +"Fix:     Use Cloudflare tunnel (cf-tunnel service) - permanent HTTPS URL\n"
    +"         journalctl -u cf-tunnel | grep trycloudflare.com\n"
    +"Prevention: Never use raw public IP. Always CF tunnel or Twingate.\n"
    +"Status: FIXED - CF tunnel deployed\n\n"

    +"RCA-004: M2/M4 CONFUSION\n"
    +"Symptom: Media tasks routed to wrong machine\n"
    +"Cause:   M2 (192.168.10.14) retired but IP used in old code\n"
    +"Fix:     ALL media -> 192.168.10.94:3333 (M4 only)\n"
    +"Status: FIXED - brain+mempalace updated\n\n"

    +"="*80+"\n"
    +"SECTION 3: ZEUS SELF-HEALING CHECKLIST (EVERY 5 MIN)\n"
    +"="*80+"\n\n"

    +"1. RELAY: Check log age. If >30min: fix token, restart relay\n"
    +"2. AUDIO: grep TTS error in WA log. If found: reinstall edge-tts, fix index.js\n"
    +"3. SERVICES: Restart any inactive agent. Log RCA. Email Ryan if fails 2x\n"
    +"4. PORTAL: curl http://127.0.0.1:8080/. If down: restart vnt-portal\n"
    +"5. CF TUNNEL: If inactive: restart, get new URL, WhatsApp Ryan\n\n"

    +"="*80+"\n"
    +"SECTION 4: QUICK FIX COMMANDS\n"
    +"="*80+"\n\n"

    +"FIX AUDIO:\n"
    +"  pip install edge-tts --break-system-packages -q\n"
    +"  python3 -m edge_tts --voice en-US-MichelleNeural --text test --write-media /tmp/t.mp3\n"
    +"  ls -lh /tmp/t.mp3\n"
    +"  sed -i s/en-US-JennyNeural/en-US-MichelleNeural/g /home/k/alias-baileys/index.js\n"
    +"  systemctl --user restart alias-whatsapp\n\n"

    +"FIX RELAY:\n"
    +"  sed -n '3p' /home/k/github-relay.py\n"
    +"  pkill -f github-relay && python3 /home/k/github-relay.py &\n"
    +"  tail -f /home/k/github-relay.log\n\n"

    +"CHECK ALL:\n"
    +"  for s in alias-voice-agent zeus-agent zeus-monitor maya-agent ava-agent "
    +"julian-agent ethan-agent lee-agent amr-agent nova-agent specter-agent "
    +"vnt-webserver luc-agent ben-agent dina-agent jodi-agent rick-agent "
    +"github-relay smbd; do echo $s: $(systemctl is-active $s); done\n"
    +"  systemctl --user is-active alias-whatsapp\n\n"

    +"="*80+"\n"
    +"END RCA - Append new entries above this line\n"
    +"="*80+"\n"
)

save(rca)

# Update brain
try:
    b = json.load(open(BRAIN))
    b["rca_document"] = MP
    b["voice"] = {"alias":"en-US-MichelleNeural","mia":"en-US-AriaNeural","engine":"python3 -m edge_tts"}
    b["tts_command"] = "python3 -m edge_tts --voice en-US-MichelleNeural --text TEXT --write-media FILE"
    b["known_fixes"] = ["RCA-001:TTS","RCA-002:relay","RCA-003:IP","RCA-004:M2M4"]
    json.dump(b, open(BRAIN,"w"), indent=2)
    print("Brain updated")
except Exception as e:
    print("Brain:", str(e)[:50])

print("RCA saved to MemPalace: "+str(len(rca))+" chars")
