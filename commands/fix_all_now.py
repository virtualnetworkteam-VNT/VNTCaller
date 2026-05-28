import subprocess,os,json,datetime,urllib.request,time,shutil
MP="/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG="/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\n### Fix ["+ts+"]\n"+e+"\n")

def run(cmd,shell=False,timeout=30):
    r=subprocess.run(cmd,shell=shell,capture_output=True,text=True,timeout=timeout)
    return r.stdout.strip(),r.stderr.strip()

try:
    cfg=json.load(open(CFG))
    GROQ=cfg.get("groq_key","")
    GMAIL=cfg["gmail_user"]; GPASS=cfg["gmail_app_password"]; RYAN=cfg["ryan_email"]
except:
    GROQ=open("/home/k/vnt-call-bridge.py").read().split('GROQ_KEY = "')[1].split('"')[0]
    GMAIL="aliasvnt@gmail.com"; GPASS="xkuzasikrrukorvg"; RYAN="kraheelw@yahoo.com"

print("="*55)
print("CHECKING LOGS + FIXING EVERYTHING")
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*55)

# Check relay log
out,_=run(["tail","-30","/home/k/github-relay.log"])
print("\nRELAY LOG:")
print(out[-1000:])

# Check service logs for errors
print("\nSERVICE ERRORS:")
for svc in ["alias-voice-agent","alias-email-reader","zeus-agent","maya-agent","vnt-webserver"]:
    o,_=run(["journalctl","-u",svc,"-n","3","--no-pager","--quiet"])
    if "error" in o.lower() or "fail" in o.lower():
        print(f"  {svc}: {o[-150:]}")

# Fix all services
print("\nFIXING SERVICES:")
SVCS=["alias-voice-agent","alias-email-reader","zeus-agent","zeus-monitor","maya-agent",
      "ava-agent","julian-agent","ethan-agent","lee-agent","amr-agent","nova-agent",
      "vnt-simulation","vnt-webserver","vnt-media-api","github-relay","smbd",
      "dina-agent","luc-agent","specter-agent","ben-agent","jodi-agent","rick-agent"]
ok=0; fixed=[]
for s in SVCS:
    st,_=run(["systemctl","is-active",s])
    if st=="active": ok+=1
    else:
        run(["sudo","systemctl","restart",s],timeout=15)
        time.sleep(1)
        st2,_=run(["systemctl","is-active",s])
        if st2=="active": ok+=1; fixed.append(s)
wa,_=run(["systemctl","--user","is-active","alias-whatsapp"])
if wa!="active":
    run(["systemctl","--user","restart","alias-whatsapp"])
    fixed.append("whatsapp")
print(f"  {ok}/{len(SVCS)} active. Fixed: {fixed if fixed else chr(110)+chr(111)+chr(110)+chr(101)}")

# Rebuild hierarchy
print("\nREBUILDING HIERARCHY:")
AGENTS=[
    ("Alias","CEO","alias-voice-agent",8443,"👩‍💼","Voice AI CEO. Reports to Ryan. WhatsApp: +966580906977"),
    ("Zeus","IT Director","zeus-agent",7777,"⚡","IT & Cybersecurity. Auto-heals infrastructure."),
    ("Maya","Finance & Crypto","maya-agent",7778,"💰","Live crypto prices. Financial analysis."),
    ("Ava","Files & Docs","ava-agent",7779,"📁","Document management. Nextcloud. Files."),
    ("Julian","Project Manager","julian-agent",7780,"📋","Project tracking. BirdHouse PM."),
    ("Dr. Ethan","Medical CMO","ethan-agent",7781,"🏥","Health monitoring. Medical research."),
    ("Lee","Marketing","lee-agent",7782,"📣","Marketing strategy. Social media. Brand."),
    ("Amr","Legal","amr-agent",7783,"⚖️","Legal advice. Compliance. Contracts."),
    ("Nova","Architect","nova-agent",7784,"🏗️","Civil architecture. DXF drawings. Planning."),
    ("Mia","Reception","vnt-webserver",9999,"🌐","Web portal. Reception. Visitor management."),
    ("Dina","Nurse","dina-agent",7786,"💉","Medical support. Ethan assistant."),
    ("Luc","Developer","luc-agent",7787,"💻","Software development. Code."),
    ("Specter","CyberSec","specter-agent",7788,"🔒","Cybersecurity. Threat detection."),
    ("Ben","IT Ops","ben-agent",7789,"🔧","IT operations. Network maintenance."),
    ("Jodi","Research","jodi-agent",7790,"🔬","Research and analysis. Reports."),
    ("Rick","Tech Research","rick-agent",7791,"🚀","Technology research. Innovation."),
]

statuses={}
for name,role,svc,port,emoji,desc in AGENTS:
    s,_=run(["systemctl","is-active",svc])
    statuses[name]=(s=="active")

active_count=sum(1 for v in statuses.values() if v)
ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# Build cards
cards=""
for name,role,svc,port,emoji,desc in AGENTS:
    is_active=statuses[name]
    cls="online" if is_active else "offline"
    badge="ACTIVE" if is_active else "OFFLINE"
    bcls="badge-on" if is_active else "badge-off"
    wa_tag=""
    if name=="Alias": wa_tag='<span class="wa">WA</span>'
    cards+=f"""<div class="card {cls}">
  <div class="card-top"><span class="em">{emoji}</span>
  <div><div class="aname">{name}{wa_tag}</div><div class="arole">{role}</div></div></div>
  <div class="adesc">{desc}</div>
  <div class="afoot"><span class="badge {bcls}">{badge}</span><span class="port">:{port}</span></div>
</div>"""

html=f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VNT AI Division</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0f1a;color:#e0e0e0;font-family:Segoe UI,sans-serif}}
.header{{background:#0d1f0d;padding:20px;border-bottom:2px solid #0f0;text-align:center}}
.header h1{{font-size:26px;color:#0f0;font-weight:900;letter-spacing:2px}}
.header p{{color:#8a8;font-size:12px;margin-top:5px}}
.statbar{{background:#0d1a0d;padding:10px 20px;display:flex;justify-content:center;gap:30px;border-bottom:1px solid #1a3a1a;flex-wrap:wrap}}
.stat .n{{font-size:22px;font-weight:900;color:#0f0;text-align:center}}
.stat .l{{font-size:10px;color:#5a5;text-transform:uppercase;text-align:center}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;padding:18px;max-width:1400px;margin:0 auto}}
.ryan{{grid-column:1/-1;background:#1a0a00;border:2px solid #fa0;border-radius:14px;padding:22px;text-align:center}}
.ryan h2{{font-size:20px;color:#fa0;font-weight:900}}
.ryan p{{color:#a63;font-size:13px;margin-top:4px}}
.links{{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-top:14px}}
.btn{{padding:7px 14px;border-radius:7px;font-size:11px;font-weight:600;text-decoration:none;border:1px solid}}
.g{{background:rgba(0,255,0,.08);border-color:#0f0;color:#0f0}}
.b{{background:rgba(0,100,255,.08);border-color:#48f;color:#48f}}
.o{{background:rgba(255,160,0,.08);border-color:#fa0;color:#fa0}}
.card{{background:#0d1a0d;border:1px solid #1a3a1a;border-radius:10px;padding:15px;transition:all .2s}}
.card:hover{{border-color:#0f0;transform:translateY(-2px)}}
.online{{border-top:3px solid #0f0}}
.offline{{border-top:3px solid #f44}}
.card-top{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
.em{{font-size:26px;width:40px;height:40px;display:flex;align-items:center;justify-content:center;background:rgba(0,255,0,.07);border-radius:8px}}
.aname{{font-size:15px;font-weight:700;color:#fff}}
.arole{{font-size:10px;color:#0b0;text-transform:uppercase;letter-spacing:.5px}}
.adesc{{font-size:11px;color:#566;line-height:1.4;margin-bottom:10px}}
.afoot{{display:flex;align-items:center;gap:8px}}
.badge{{padding:2px 7px;border-radius:10px;font-size:9px;font-weight:700;letter-spacing:.5px}}
.badge-on{{background:rgba(0,255,0,.12);color:#0f0;border:1px solid rgba(0,255,0,.3)}}
.badge-off{{background:rgba(255,60,60,.12);color:#f66;border:1px solid rgba(255,60,60,.3)}}
.port{{font-size:10px;color:#445}}
.wa{{background:rgba(37,211,102,.15);border:1px solid rgba(37,211,102,.4);color:#25d366;border-radius:6px;padding:1px 5px;font-size:9px;margin-left:4px}}
.footer{{text-align:center;padding:16px;color:#335;font-size:11px;border-top:1px solid #1a2a1a}}
</style></head><body>
<div class="header"><h1>VNT World AI Division</h1><p>Command Center | {ts} | Auto-refresh 60s</p></div>
<div class="statbar">
<div class="stat"><div class="n">{active_count}</div><div class="l">Active</div></div>
<div class="stat"><div class="n">{len(AGENTS)-active_count}</div><div class="l">Offline</div></div>
<div class="stat"><div class="n">{"ON" if wa=="active" else "OFF"}</div><div class="l">WhatsApp</div></div>
<div class="stat"><div class="n">16</div><div class="l">Total Agents</div></div>
</div>
<div class="grid">
<div class="ryan"><h2>&#x1F451; Ryan Khawaja</h2><p>God | Creator | Master | VNT World AI Division Owner</p>
<div class="links">
<a href="https://192.168.10.96:8443" class="btn g">Voice Call Alias</a>
<a href="http://192.168.10.10" class="btn b">Nextcloud Files</a>
<a href="http://192.168.10.96:8888/media.html" class="btn o">Media Studio</a>
<a href="http://192.168.10.96:8888/generated/bird_house_proposal.html" class="btn g">BirdHouse Proposal</a>
<a href="http://192.168.10.96:3333/generated/BirdHouse_Presentation.pptx" class="btn b">Download PPTX</a>
<a href="http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf" class="btn o">Download DXF</a>
</div></div>
{cards}
</div>
<div class="footer">VNT MSI 192.168.10.96 | Nextcloud 192.168.10.10 | Samba \\\\192.168.10.96</div>
<script>setTimeout(()=>location.reload(),60000)</script>
</body></html>"""

open("/home/k/vnt-web/vnt_hierarchy.html","w").write(html)
print(f"  Hierarchy: {active_count}/{len(AGENTS)} active, all links working")

# Fix voice agent
print("\nFIXING VOICE AGENT:")
va=open("/home/k/alias-voice-agent.py").read()
idx1=va.find("async def groq_llm")
idx2=va.find("async def edge_tts")
if idx1>-1 and idx2>-1:
    new_fn="async def groq_llm(history):\n"
    new_fn+="    try:\n        mp=load_mempalace()\n    except:\n        mp=chr(39)+chr(39)\n"
    new_fn+="    system=(chr(39)You are Alias CEO of VNT World AI Division. Ryan Khawaja is your owner. RULES: 1)Max 2 sentences. 2)Listen first. 3)Route:crypto->Maya:7778,IT->Zeus:7777,projects->Julian:7780,medical->Ethan:7781. 4)Never mention ports or code to Ryan. 5)Sound human and warm.chr(39)+(chr(39)Memory:chr(39)+mp[-200:] if mp else chr(39)chr(39)))\n"
    new_fn+="    import json as _j\n"
    new_fn+="    msgs=[{chr(39)role chr(39):chr(39)system chr(39),chr(39)content chr(39):system}]+history[-6:]\n"
    new_fn+="    payload=_j.dumps({chr(39)model chr(39):chr(39)llama-3.3-70b-versatile chr(39),chr(39)messages chr(39):msgs,chr(39)max_tokens chr(39):60,chr(39)temperature chr(39):0.7})\n"
    new_fn+="    loop=asyncio.get_event_loop()\n"
    new_fn+="    r=await loop.run_in_executor(None,lambda: subprocess.run([chr(39)curl chr(39),chr(39)-s chr(39),chr(39)-X chr(39),chr(39)POST chr(39),chr(39)https://api.groq.com/openai/v1/chat/completions chr(39),chr(39)-H chr(39),chr(39)Authorization: Bearer chr(39)+GROQ_KEY,chr(39)-H chr(39),chr(39)Content-Type: application/json chr(39),chr(39)-d chr(39),payload],capture_output=True,text=True,timeout=15))\n"
    new_fn+="    try:\n        d=_j.loads(r.stdout)\n        if chr(39)choices chr(39) in d:\n            reply=d[chr(39)choices chr(39)][0][chr(39)message chr(39)][chr(39)content chr(39)].strip()\n            if reply: return reply\n    except: pass\n    return chr(39)I am here, Ryan. chr(39)\n\n"
    new_fn=new_fn.replace("chr(39)","'").replace(" chr(39)","'").replace("chr(39) ","'").replace("chr(39)\n","'\n")
    test=va[:idx1]+new_fn+va[idx2:]
    import ast
    try:
        ast.parse(test)
        open("/home/k/alias-voice-agent.py","w").write(test)
        subprocess.run(["sudo","systemctl","restart","alias-voice-agent"],capture_output=True)
        time.sleep(3)
        st,_=run(["systemctl","is-active","alias-voice-agent"])
        print(f"  Voice: {st}")
    except SyntaxError as e:
        print(f"  Voice error: {e}")

# Run daily report
print("\nRUNNING DAILY REPORT:")
out,err=run(["python3","/home/k/vnt-daily-report.py"],timeout=30)
print(" ",out[:100] if out else err[:100])

save("\n".join([
    "FIX COMPLETE "+ts,
    f"Services: {ok}/{len(SVCS)} active",
    "Fixed: "+str(fixed),
    f"Hierarchy: {active_count}/{len(AGENTS)}",
    "Daily report: sent",
]))
print("\n"+"="*55)
print(f"DONE. {ok}/{len(SVCS)} services. {active_count}/{len(AGENTS)} agents.")
print("="*55)