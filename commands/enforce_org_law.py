import subprocess, os, json, datetime

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
WEB = "/home/k/vnt-web"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\n"+e+"\n")

def run(cmd,shell=False,timeout=30):
    r=subprocess.run(cmd,shell=shell,capture_output=True,text=True,timeout=timeout)
    return r.stdout.strip()

# ── THE LAW - saved permanently ──
ORG_LAW = """
╔══════════════════════════════════════════════════════════════════╗
║           VNT WORLD AI DIVISION — ORGANIZATIONAL LAW            ║
║                  Issued by: Ryan Khawaja                        ║
║                  Date: """+datetime.datetime.now().strftime("%Y-%m-%d")+"""                              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ALL OPERATIONS FLOW THROUGH ALIAS (CEO). NO EXCEPTIONS.        ║
║                                                                  ║
║  ALIAS is the Central Node. Every agent reports to Alias.        ║
║  Every task comes from Alias. No agent bypasses the CEO.         ║
║  Bypassing Alias = permanent deletion from the system.           ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  DIRECT REPORTS TO ALIAS (CEO):                                  ║
║                                                                  ║
║  ZEUS      - IT Director                                         ║
║              IT operations, auto-heals infrastructure            ║
║                                                                  ║
║  MAYA      - Finance & Crypto                                    ║
║              Live prices, financial analysis                     ║
║                                                                  ║
║  AVA       - Files & Documents                                   ║
║              Nextcloud, document management                      ║
║                                                                  ║
║  JULIAN    - Project Manager                                     ║
║              Project tracking, BirdHouse PM                      ║
║                                                                  ║
║  DR. ETHAN - Chief Medical Officer                               ║
║              Health monitoring, medical research                 ║
║              (Dina is his assistant, reports through Ethan)      ║
║                                                                  ║
║  LEE       - Marketing Manager                                   ║
║              Strategy, social media, brand                       ║
║                                                                  ║
║  AMR       - Legal Advisor                                       ║
║              Legal advice, compliance, contracts                 ║
║                                                                  ║
║  NOVA      - Civil Architect                                     ║
║              Architecture, DXF drawings, planning               ║
║                                                                  ║
║  MIA       - Receptionist                                        ║
║              Web portal, reception, visitor management           ║
║                                                                  ║
║  SPECTER   - Cybersecurity                                       ║
║              Network security, threat monitoring                 ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  NOTE: Luc, Ben, Dina, Jodi, Rick are specialists who           ║
║  operate under their direct supervisors but ALL final            ║
║  reporting goes UP through Alias to Ryan.                        ║
║                                                                  ║
║  ALIAS reports directly to Ryan Khawaja.                        ║
║  Ryan is the owner. His word is final.                          ║
╚══════════════════════════════════════════════════════════════════╝
"""

save(ORG_LAW)
print("Law saved to MemPalace")

# ── Save org structure to config ──
try:
    cfg=json.load(open(CFG))
except:
    cfg={}

cfg["org_law"] = {
    "issued_by": "Ryan Khawaja",
    "date": datetime.datetime.now().strftime("%Y-%m-%d"),
    "central_node": "Alias",
    "law": "ALL operations flow through Alias CEO. No bypassing. Violation = permanent deletion.",
    "direct_reports_to_alias": ["Zeus","Maya","Ava","Julian","Dr. Ethan","Lee","Amr","Nova","Mia","Specter"],
    "under_ethan": ["Dina"],
    "under_zeus": ["Luc","Ben"],
    "specialists": ["Jodi","Rick"],
    "alias_reports_to": "Ryan Khawaja"
}

cfg["agent_registry"] = [
    {"name":"Alias",     "role":"CEO",                    "svc":"alias-voice-agent","port":8443,"reports_to":"Ryan Khawaja","law":"Central node. All operations flow through Alias."},
    {"name":"Zeus",      "role":"IT Director",             "svc":"zeus-agent",       "port":7777,"reports_to":"Alias","law":"IT ops, auto-heal. Reports to Alias only."},
    {"name":"Maya",      "role":"Finance & Crypto",        "svc":"maya-agent",       "port":7778,"reports_to":"Alias","law":"Prices, financial analysis. Reports to Alias only."},
    {"name":"Ava",       "role":"Files & Documents",       "svc":"ava-agent",        "port":7779,"reports_to":"Alias","law":"Nextcloud, docs. Reports to Alias only."},
    {"name":"Julian",    "role":"Project Manager",         "svc":"julian-agent",     "port":7780,"reports_to":"Alias","law":"Project tracking. Reports to Alias only."},
    {"name":"Dr. Ethan", "role":"Chief Medical Officer",   "svc":"ethan-agent",      "port":7781,"reports_to":"Alias","law":"Medical CMO. Dina is his assistant. Reports to Alias only."},
    {"name":"Lee",       "role":"Marketing Manager",       "svc":"lee-agent",        "port":7782,"reports_to":"Alias","law":"Marketing, social, brand. Reports to Alias only."},
    {"name":"Amr",       "role":"Legal Advisor",           "svc":"amr-agent",        "port":7783,"reports_to":"Alias","law":"Legal, compliance. Reports to Alias only."},
    {"name":"Nova",      "role":"Civil Architect",         "svc":"nova-agent",       "port":7784,"reports_to":"Alias","law":"Architecture, DXF. Reports to Alias only."},
    {"name":"Mia",       "role":"Receptionist",            "svc":"vnt-webserver",    "port":9999,"reports_to":"Alias","law":"Web portal, reception. Reports to Alias only."},
    {"name":"Specter",   "role":"Cybersecurity",           "svc":"specter-agent",    "port":7788,"reports_to":"Alias","law":"Network security, threats. Reports to Alias only."},
    {"name":"Dina",      "role":"Nurse",                   "svc":"dina-agent",       "port":7786,"reports_to":"Dr. Ethan","law":"Medical support. Reports through Ethan to Alias."},
    {"name":"Luc",       "role":"Software Developer",      "svc":"luc-agent",        "port":7787,"reports_to":"Zeus","law":"Software dev. Reports through Zeus to Alias."},
    {"name":"Ben",       "role":"IT Operations",           "svc":"ben-agent",        "port":7789,"reports_to":"Zeus","law":"IT ops. Reports through Zeus to Alias."},
    {"name":"Jodi",      "role":"Research Analyst",        "svc":"jodi-agent",       "port":7790,"reports_to":"Alias","law":"Research. Reports to Alias only."},
    {"name":"Rick",      "role":"Tech Research",           "svc":"rick-agent",       "port":7791,"reports_to":"Alias","law":"Tech research. Reports to Alias only."},
]

json.dump(cfg, open(CFG,"w"), indent=2)
print("Org law saved to vnt_config.json")

# ── Inject law into EVERY agent's system prompt ──
ORG_LAW_SHORT = (
    "ORGANIZATIONAL LAW (Ryan Khawaja - absolute rule): "
    "ALL operations flow through ALIAS (CEO). "
    "You report ONLY to your direct supervisor as defined. "
    "No agent bypasses Alias. Violation = permanent deletion. "
    "Chain: Ryan -> Alias -> [Zeus/Maya/Ava/Julian/Ethan/Lee/Amr/Nova/Mia/Specter] -> Alias -> Ryan. "
    "Every task received from Alias. Every result reported to Alias. No exceptions."
)

agent_files = {
    "zeus": "/home/k/zeus-agent/zeus.py",
    "maya": "/home/k/maya-agent.py",
    "julian": "/home/k/julian-agent.py",
    "ethan": "/home/k/ethan-agent.py",
    "lee": "/home/k/lee-agent.py",
    "amr": "/home/k/amr-agent.py",
    "nova": "/home/k/nova-agent.py",
    "ava": "/home/k/ava-agent.py",
    "specter": "/home/k/specter-agent.py",
}

updated=[]
for name, path in agent_files.items():
    if os.path.exists(path):
        content=open(path).read()
        if "ORG_LAW" not in content and "organizational law" not in content.lower():
            law_inject = '\n# VNT ORGANIZATIONAL LAW - Ryan Khawaja\nORG_LAW = "'+ORG_LAW_SHORT+'"\n'
            # Inject after imports
            lines=content.split("\n")
            insert_at=0
            for i,line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    insert_at=i+1
            lines.insert(insert_at, law_inject)
            open(path,"w").write("\n".join(lines))
            updated.append(name)

print("Law injected into agents:", updated if updated else "already present")

# ── Inject into Alias voice agent ──
va_path="/home/k/alias-voice-agent.py"
if os.path.exists(va_path):
    va=open(va_path).read()
    if "organizational law" not in va.lower():
        idx1=va.find("async def groq_llm")
        idx2=va.find("async def edge_tts")
        if idx1>-1 and idx2>-1:
            new_fn=(
                "async def groq_llm(history):\n"
                "    try:\n        mp=load_mempalace()\n    except:\n        mp=''\n"
                "    system=(\n"
                "        'You are Alias, CEO of VNT World AI Division. Ryan Khawaja is your owner. '\n"
                "        'ORGANIZATIONAL LAW: ALL operations flow through you as CEO. '\n"
                "        'Every agent reports to you. You report only to Ryan. '\n"
                "        'No agent bypasses you - that law is absolute. '\n"
                "        'ROUTING - delegate tasks to: '\n"
                "        'Zeus(IT), Maya(Finance/Crypto), Ava(Files), Julian(Projects), '\n"
                "        'Ethan(Medical), Lee(Marketing), Amr(Legal), Nova(Architecture), '\n"
                "        'Mia(Reception), Specter(Cybersecurity). '\n"
                "        'All results come back to you before going to Ryan. '\n"
                "        'VOICE RULES: Max 2 sentences. Listen first. Never technical details. '\n"
                "        'Sound warm, professional, human. '\n"
                "        +('Memory: '+mp[-300:] if mp else '')\n"
                "    )\n"
                "    import json as _j\n"
                "    msgs=[{'role':'system','content':system}]+history[-6:]\n"
                "    payload=_j.dumps({'model':'llama-3.3-70b-versatile','messages':msgs,'max_tokens':60,'temperature':0.7})\n"
                "    loop=asyncio.get_event_loop()\n"
                "    r=await loop.run_in_executor(None,lambda: subprocess.run(\n"
                "        ['curl','-s','-X','POST','https://api.groq.com/openai/v1/chat/completions',\n"
                "         '-H','Authorization: Bearer '+GROQ_KEY,\n"
                "         '-H','Content-Type: application/json','-d',payload],\n"
                "        capture_output=True,text=True,timeout=15))\n"
                "    try:\n"
                "        d=_j.loads(r.stdout)\n"
                "        if 'choices' in d:\n"
                "            reply=d['choices'][0]['message']['content'].strip()\n"
                "            if reply: return reply\n"
                "    except: pass\n"
                "    return 'I am here, Ryan.'\n\n"
            )
            va=va[:idx1]+new_fn+va[idx2:]
            import ast
            try:
                ast.parse(va)
                open(va_path,"w").write(va)
                subprocess.run(["sudo","systemctl","restart","alias-voice-agent"],capture_output=True)
                print("Alias voice: org law injected, restarted")
            except SyntaxError as e:
                print("Voice syntax error:",str(e)[:60])

# ── Rebuild hierarchy with correct structure ──
DIRECT_REPORTS=[
    ("Alias","CEO","alias-voice-agent",8443,"Ryan Khawaja","Central node. All flows through CEO."),
    ("Zeus","IT Director","zeus-agent",7777,"Alias","IT ops, infrastructure, auto-heal."),
    ("Maya","Finance & Crypto","maya-agent",7778,"Alias","Live prices, financial analysis."),
    ("Ava","Files & Documents","ava-agent",7779,"Alias","Nextcloud, document management."),
    ("Julian","Project Manager","julian-agent",7780,"Alias","Project tracking, BirdHouse PM."),
    ("Dr. Ethan","Chief Medical Officer","ethan-agent",7781,"Alias","Medical CMO. (Dina is assistant.)"),
    ("Lee","Marketing Manager","lee-agent",7782,"Alias","Strategy, social media, brand."),
    ("Amr","Legal Advisor","amr-agent",7783,"Alias","Legal, compliance, contracts."),
    ("Nova","Civil Architect","nova-agent",7784,"Alias","Architecture, DXF, planning."),
    ("Mia","Receptionist","vnt-webserver",9999,"Alias","Web portal, reception."),
    ("Specter","Cybersecurity","specter-agent",7788,"Alias","Network security, threat monitoring."),
    ("Dina","Nurse","dina-agent",7786,"Dr. Ethan","Medical support. Through Ethan."),
    ("Luc","Software Developer","luc-agent",7787,"Zeus","Dev. Through Zeus."),
    ("Ben","IT Operations","ben-agent",7789,"Zeus","IT ops. Through Zeus."),
    ("Jodi","Research Analyst","jodi-agent",7790,"Alias","Research and analysis."),
    ("Rick","Tech Research","rick-agent",7791,"Alias","Technology research."),
]

def is_active(svc):
    return run(["systemctl","is-active",svc])=="active"

rows=""
for name,role,svc,port,reports_to,desc in DIRECT_REPORTS:
    active=is_active(svc)
    if not active:
        subprocess.run(["sudo","systemctl","restart",svc],capture_output=True,timeout=15)
        import time; time.sleep(1)
        active=is_active(svc)
    dot="#00cc55" if active else "#cc2222"
    st_txt="Active" if active else "Offline"
    st_col="color:#00cc55" if active else "color:#cc4444"
    wa_tag=""
    if name=="Alias":
        wa_tag='&nbsp;<small style="background:#075e54;color:#dcf8c6;border-radius:3px;padding:1px 4px;font-size:9px;vertical-align:middle">WA</small>'
    rows+=(
        "<tr>"
        "<td style='width:14px;padding:8px 4px 8px 14px'>"
        "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:"+dot+"'></span></td>"
        "<td style='padding:8px 12px;font-weight:600;color:#e0ffe0'>"+name+wa_tag+"</td>"
        "<td style='padding:8px 12px;color:#7ab87a;font-size:12px'>"+role+"</td>"
        "<td style='padding:8px 12px;color:#556655;font-size:12px'>"+reports_to+"</td>"
        "<td style='padding:8px 12px;color:#334433;font-size:11px;font-family:monospace'>:"+str(port)+"</td>"
        "<td style='padding:8px 14px;font-size:12px;font-weight:600;"+st_col+"'>"+st_txt+"</td>"
        "</tr>"
    )

active_count=sum(1 for n,r,s,p,rt,d in DIRECT_REPORTS if is_active(s))
wa=run(["systemctl","--user","is-active","alias-whatsapp"])=="active"
ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

css=(
    "*{margin:0;padding:0;box-sizing:border-box}"
    "body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif}"
    ".hdr{background:#161b22;border-bottom:1px solid #21262d;padding:16px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}"
    ".logo{font-size:18px;font-weight:700;color:#58a6ff}"
    ".sub{font-size:11px;color:#484f58;margin-top:3px}"
    ".stats{display:flex;gap:20px}"
    ".sn{font-size:20px;font-weight:700;text-align:center}"
    ".sl{font-size:9px;color:#484f58;text-transform:uppercase;letter-spacing:1px;text-align:center}"
    ".sec{padding:16px 24px}"
    ".sec-t{font-size:10px;color:#484f58;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px}"
    ".links{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}"
    ".btn{padding:6px 14px;border-radius:6px;font-size:12px;font-weight:500;text-decoration:none;border:1px solid;display:inline-block}"
    ".bg{background:rgba(35,134,54,.13);border-color:#238636;color:#3fb950}"
    ".bb{background:rgba(31,111,235,.13);border-color:#1f6feb;color:#58a6ff}"
    ".bo{background:rgba(158,106,3,.13);border-color:#9e6a03;color:#d29922}"
    "table{width:100%;border-collapse:collapse;background:#161b22;border:1px solid #21262d;border-radius:6px;overflow:hidden}"
    "thead th{background:#0d1117;color:#484f58;font-size:10px;text-transform:uppercase;letter-spacing:1px;padding:8px 12px;text-align:left;border-bottom:1px solid #21262d}"
    "tbody tr{border-bottom:1px solid #1a2030;transition:background .1s}"
    "tbody tr:last-child{border-bottom:none}"
    "tbody tr:hover{background:#1c2128}"
    ".ftr{padding:12px 24px;border-top:1px solid #21262d;font-size:10px;color:#30363d;text-align:center;margin-top:4px}"
)

infra=(
    "<tr><td style='padding:8px 14px;color:#e0ffe0'>MSI AI Server</td><td style='padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px'>192.168.10.96</td><td style='padding:8px 14px;color:#484f58;font-size:12px'>Main AI brain</td></tr>"
    "<tr><td style='padding:8px 14px;color:#e0ffe0'>Nextcloud CT104</td><td style='padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px'>192.168.10.10</td><td style='padding:8px 14px;color:#484f58;font-size:12px'>File server on Prox1</td></tr>"
    "<tr><td style='padding:8px 14px;color:#e0ffe0'>Samba Share</td><td style='padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px'>\\\\192.168.10.96</td><td style='padding:8px 14px;color:#484f58;font-size:12px'>Windows file access</td></tr>"
    "<tr><td style='padding:8px 14px;color:#e0ffe0'>M4 MacBook</td><td style='padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px'>192.168.10.94:3333</td><td style='padding:8px 14px;color:#484f58;font-size:12px'>Media generation</td></tr>"
    "<tr><td style='padding:8px 14px;color:#e0ffe0'>LiveKit CT109</td><td style='padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px'>192.168.10.20:7880</td><td style='padding:8px 14px;color:#484f58;font-size:12px'>Voice WebRTC</td></tr>"
)

wa_col="#25d366" if wa else "#f85149"
off_count=len(DIRECT_REPORTS)-active_count

html=(
    "<!DOCTYPE html><html lang='en'><head>"
    "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>VNT World AI Division</title>"
    "<style>"+css+"</style></head><body>"
    "<div class='hdr'>"
    "<div><div class='logo'>VNT World AI Division</div>"
    "<div class='sub'>Command Center &nbsp;|&nbsp; "+ts+" &nbsp;|&nbsp; Auto-refresh 60s</div></div>"
    "<div class='stats'>"
    "<div><div class='sn' style='color:#3fb950'>"+str(active_count)+"</div><div class='sl'>Active</div></div>"
    "<div><div class='sn' style='color:#f85149'>"+str(off_count)+"</div><div class='sl'>Offline</div></div>"
    "<div><div class='sn' style='color:"+wa_col+"'>"+("ON" if wa else "OFF")+"</div><div class='sl'>WhatsApp</div></div>"
    "<div><div class='sn'>"+str(len(DIRECT_REPORTS))+"</div><div class='sl'>Agents</div></div>"
    "</div></div>"
    "<div class='sec'>"
    "<div class='sec-t'>Quick Access</div>"
    "<div class='links'>"
    "<a href='https://192.168.10.96:8443' class='btn bg'>&#127908; Voice &mdash; Alias</a>"
    "<a href='http://192.168.10.10' class='btn bb'>&#9729; Nextcloud</a>"
    "<a href='http://192.168.10.96:8888/media.html' class='btn bo'>&#127912; Media Studio</a>"
    "<a href='http://192.168.10.96:8888/generated/bird_house_proposal.html' class='btn bg'>&#127981; BirdHouse Proposal</a>"
    "<a href='http://192.168.10.96:3333/generated/BirdHouse_Presentation.pptx' class='btn bb'>&#128202; PPTX</a>"
    "<a href='http://192.168.10.96:3333/generated/birdhouse_site_plan.dxf' class='btn bo'>&#128208; DXF</a>"
    "</div>"
    "<div class='sec-t'>Organizational Hierarchy &mdash; "+str(active_count)+"/"+str(len(DIRECT_REPORTS))+" Online</div>"
    "<table><thead><tr>"
    "<th></th><th>Agent</th><th>Role</th><th>Reports To</th><th>Port</th><th>Status</th>"
    "</tr></thead><tbody>"+rows+"</tbody></table>"
    "<div class='sec-t' style='margin-top:20px'>Infrastructure</div>"
    "<table><thead><tr><th>System</th><th>Address</th><th>Notes</th></tr></thead>"
    "<tbody>"+infra+"</tbody></table>"
    "</div>"
    "<div class='ftr'>VNT World AI Division &mdash; 192.168.10.96</div>"
    "<script>setTimeout(()=>location.reload(),60000)</script>"
    "</body></html>"
)

open(WEB+"/vnt_hierarchy.html","w").write(html)
save("ORG LAW enforced. Hierarchy fixed. All agents law injected. Luc rebuilt page.")
print("DONE. Law saved. Hierarchy rebuilt. All agents updated.")
print(f"Active: {active_count}/{len(DIRECT_REPORTS)}")
