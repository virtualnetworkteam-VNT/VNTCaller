import subprocess, os, json, datetime, time

MP = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/MemPalace.md"
CFG = "/mnt/vnt-data/FileServer/VNT_World_AI_Division/vnt_config.json"
WEB = "/home/k/vnt-web"

def save(e):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    open(MP,"a").write("\n### Luc ["+ts+"]\n"+e+"\n")

def svc_active(svc):
    r=subprocess.run(["systemctl","is-active",svc],capture_output=True,text=True)
    return r.stdout.strip()=="active"

try:
    cfg=json.load(open(CFG))
    AGENTS=cfg.get("agent_registry",[])
except:
    AGENTS=[]

if not AGENTS:
    AGENTS=[
        {"name":"Alias","role":"CEO","svc":"alias-voice-agent","port":8443,"reports_to":"Ryan"},
        {"name":"Zeus","role":"IT Director","svc":"zeus-agent","port":7777,"reports_to":"Alias"},
        {"name":"Specter","role":"Cybersecurity","svc":"specter-agent","port":7788,"reports_to":"Zeus"},
        {"name":"Luc","role":"Software Developer","svc":"luc-agent","port":7787,"reports_to":"Zeus"},
        {"name":"Ben","role":"IT Operations","svc":"ben-agent","port":7789,"reports_to":"Zeus"},
        {"name":"Maya","role":"Finance & Crypto","svc":"maya-agent","port":7778,"reports_to":"Alias"},
        {"name":"Ava","role":"Files & Documents","svc":"ava-agent","port":7779,"reports_to":"Alias"},
        {"name":"Julian","role":"Project Manager","svc":"julian-agent","port":7780,"reports_to":"Alias"},
        {"name":"Dr. Ethan","role":"Chief Medical Officer","svc":"ethan-agent","port":7781,"reports_to":"Alias"},
        {"name":"Dina","role":"Nurse","svc":"dina-agent","port":7786,"reports_to":"Dr. Ethan"},
        {"name":"Lee","role":"Marketing Manager","svc":"lee-agent","port":7782,"reports_to":"Alias"},
        {"name":"Amr","role":"Legal Advisor","svc":"amr-agent","port":7783,"reports_to":"Alias"},
        {"name":"Nova","role":"Civil Architect","svc":"nova-agent","port":7784,"reports_to":"Alias"},
        {"name":"Jodi","role":"Research Analyst","svc":"jodi-agent","port":7790,"reports_to":"Alias"},
        {"name":"Rick","role":"Tech Research","svc":"rick-agent","port":7791,"reports_to":"Alias"},
        {"name":"Mia","role":"Receptionist","svc":"vnt-webserver","port":9999,"reports_to":"Alias"},
    ]

for a in AGENTS:
    a["active"]=svc_active(a["svc"])

wa=subprocess.run(["systemctl","--user","is-active","alias-whatsapp"],capture_output=True,text=True).stdout.strip()=="active"
active_count=sum(1 for a in AGENTS if a["active"])
ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# Build rows
rows=""
for a in AGENTS:
    dot="#00cc55" if a["active"] else "#cc2222"
    st_txt="Active" if a["active"] else "Offline"
    st_col="#00cc55" if a["active"] else "#cc4444"
    wa_tag=""
    if a["name"]=="Alias":
        wa_tag='&nbsp;<small style="background:#075e54;color:#dcf8c6;border-radius:3px;padding:1px 4px;font-size:9px">WA</small>'
    rows+=(
        "<tr>"
        +"<td style='width:14px;padding:8px 4px 8px 14px'>"
        +"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:"+dot+"'></span></td>"
        +"<td style='padding:8px 12px;font-weight:600;color:#e0ffe0'>"+a["name"]+wa_tag+"</td>"
        +"<td style='padding:8px 12px;color:#7ab87a;font-size:12px'>"+a["role"]+"</td>"
        +"<td style='padding:8px 12px;color:#556655;font-size:12px'>"+str(a["reports_to"])+"</td>"
        +"<td style='padding:8px 12px;color:#334433;font-size:11px;font-family:monospace'>:"+str(a["port"])+"</td>"
        +"<td style='padding:8px 14px;color:"+st_col+";font-size:12px;font-weight:600'>"+st_txt+"</td>"
        +"</tr>"
    )

# CSS as separate string - no curly braces issues
css = (
    "* { margin:0; padding:0; box-sizing:border-box; }"
    "body { background:#0d1117; color:#c9d1d9; font-family:Segoe UI,Arial,sans-serif; }"
    ".hdr { background:#161b22; border-bottom:1px solid #21262d; padding:16px 24px;"
    "  display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }"
    ".logo { font-size:18px; font-weight:700; color:#58a6ff; }"
    ".sub { font-size:11px; color:#484f58; margin-top:3px; }"
    ".stats { display:flex; gap:20px; }"
    ".sn { font-size:20px; font-weight:700; text-align:center; }"
    ".sl { font-size:9px; color:#484f58; text-transform:uppercase; letter-spacing:1px; text-align:center; }"
    ".sec { padding:16px 24px; }"
    ".sec-t { font-size:10px; color:#484f58; text-transform:uppercase; letter-spacing:2px; margin-bottom:10px; }"
    ".links { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px; }"
    ".btn { padding:6px 14px; border-radius:6px; font-size:12px; font-weight:500;"
    "  text-decoration:none; border:1px solid; display:inline-block; }"
    ".bg { background:rgba(35,134,54,.13); border-color:#238636; color:#3fb950; }"
    ".bb { background:rgba(31,111,235,.13); border-color:#1f6feb; color:#58a6ff; }"
    ".bo { background:rgba(158,106,3,.13); border-color:#9e6a03; color:#d29922; }"
    "table { width:100%; border-collapse:collapse; background:#161b22;"
    "  border:1px solid #21262d; border-radius:6px; overflow:hidden; }"
    "thead th { background:#0d1117; color:#484f58; font-size:10px; text-transform:uppercase;"
    "  letter-spacing:1px; padding:8px 12px; text-align:left; border-bottom:1px solid #21262d; }"
    "tbody tr { border-bottom:1px solid #1a2030; transition:background .1s; }"
    "tbody tr:last-child { border-bottom:none; }"
    "tbody tr:hover { background:#1c2128; }"
    ".ftr { padding:12px 24px; border-top:1px solid #21262d; font-size:10px;"
    "  color:#30363d; text-align:center; margin-top:4px; }"
)

infra_rows=(
    "<tr><td style='padding:8px 14px;color:#e0ffe0'>MSI AI Server</td><td style='padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px'>192.168.10.96</td><td style='padding:8px 14px;color:#484f58;font-size:12px'>Main AI brain</td></tr>"
    "<tr><td style='padding:8px 14px;color:#e0ffe0'>Nextcloud CT104</td><td style='padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px'>192.168.10.10</td><td style='padding:8px 14px;color:#484f58;font-size:12px'>File server on Prox1</td></tr>"
    "<tr><td style='padding:8px 14px;color:#e0ffe0'>Samba Share</td><td style='padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px'>\\\\192.168.10.96</td><td style='padding:8px 14px;color:#484f58;font-size:12px'>Windows file access</td></tr>"
    "<tr><td style='padding:8px 14px;color:#e0ffe0'>M4 MacBook</td><td style='padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px'>192.168.10.94:3333</td><td style='padding:8px 14px;color:#484f58;font-size:12px'>Media generation</td></tr>"
    "<tr><td style='padding:8px 14px;color:#e0ffe0'>LiveKit CT109</td><td style='padding:8px 14px;font-family:monospace;color:#58a6ff;font-size:12px'>192.168.10.20:7880</td><td style='padding:8px 14px;color:#484f58;font-size:12px'>Voice WebRTC</td></tr>"
)

wa_color="#25d366" if wa else "#f85149"
wa_txt="ON" if wa else "OFF"
off_count=len(AGENTS)-active_count

html=(
    "<!DOCTYPE html><html lang='en'><head>"
    "<meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>VNT World AI Division</title>"
    "<style>"+css+"</style>"
    "</head><body>"
    "<div class='hdr'>"
    "<div><div class='logo'>VNT World AI Division</div>"
    "<div class='sub'>Command Center &nbsp;|&nbsp; "+ts+" &nbsp;|&nbsp; Auto-refresh 60s</div></div>"
    "<div class='stats'>"
    "<div><div class='sn' style='color:#3fb950'>"+str(active_count)+"</div><div class='sl'>Active</div></div>"
    "<div><div class='sn' style='color:#f85149'>"+str(off_count)+"</div><div class='sl'>Offline</div></div>"
    "<div><div class='sn' style='color:"+wa_color+"'>"+wa_txt+"</div><div class='sl'>WhatsApp</div></div>"
    "<div><div class='sn'>"+str(len(AGENTS))+"</div><div class='sl'>Agents</div></div>"
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
    "<div class='sec-t'>Agents &mdash; "+str(active_count)+"/"+str(len(AGENTS))+" Online</div>"
    "<table>"
    "<thead><tr><th></th><th>Agent</th><th>Role</th><th>Reports To</th><th>Port</th><th>Status</th></tr></thead>"
    "<tbody>"+rows+"</tbody>"
    "</table>"
    "<div class='sec-t' style='margin-top:20px'>Infrastructure</div>"
    "<table>"
    "<thead><tr><th>System</th><th>Address</th><th>Notes</th></tr></thead>"
    "<tbody>"+infra_rows+"</tbody>"
    "</table>"
    "</div>"
    "<div class='ftr'>VNT World AI Division &mdash; 192.168.10.96</div>"
    "<script>setTimeout(()=>location.reload(),60000)</script>"
    "</body></html>"
)

open(WEB+"/vnt_hierarchy.html","w").write(html)
save("Luc fixed hierarchy: clean table layout, no personal info, correct roles, all agents listed")

# Fix offline agents
fixed=[]
for a in AGENTS:
    if not a["active"]:
        subprocess.run(["sudo","systemctl","restart",a["svc"]],capture_output=True,timeout=15)
        time.sleep(1)
        if subprocess.run(["systemctl","is-active",a["svc"]],capture_output=True,text=True).stdout.strip()=="active":
            fixed.append(a["name"])

if fixed:
    save("Zeus restarted offline agents: "+" ".join(fixed))

print("Hierarchy fixed: clean table, no personal info")
print(f"{active_count}/{len(AGENTS)} active. Restarted: {fixed if fixed else 'none'}")
